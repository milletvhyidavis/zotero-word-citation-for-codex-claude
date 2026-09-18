"""Shared helpers for the zotero-word-live-citations scripts (stdlib only).

HTTP plumbing for the Zotero Desktop local API / connector is adapted from the
MIT-licensed OpenAI Zotero plugin helper (openai/plugins, plugins/zotero).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_BASE_URL = os.environ.get("ZOTERO_LOCAL_BASE_URL", "http://127.0.0.1:23119")
API_VERSION_HEADERS = {"Zotero-API-Version": "3"}
CONNECTOR_HEADERS = {"X-Zotero-Connector-API-Version": "3"}
USER_AGENT = "zotero-word-live-citations/1.0"

EXIT_OK = 0
EXIT_FAIL = 1
EXIT_USAGE = 2

ZOTERO_ITEM_URI = re.compile(
    r"^https?://(?:www\.)?zotero\.org/"
    r"(?P<namespace>users/(?:local/[^/]+|\d+)|groups/\d+)/"
    r"items/(?P<key>[A-Z0-9]{8})$"
)
NON_CITABLE_TYPES = {"attachment", "note", "annotation"}


def utf8_stdio() -> None:
    """Make stdout/stderr UTF-8 so Chinese paths and titles print on Windows."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
        except (AttributeError, ValueError):
            pass


def dump_json(value: Any, out: str | Path | None = None) -> None:
    text = json.dumps(value, indent=2, ensure_ascii=False)
    if out:
        path = Path(out).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)


def load_json(path: str | Path) -> Any:
    return json.loads(Path(path).expanduser().read_text(encoding="utf-8-sig"))


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


class UsageError(Exception):
    """Bad arguments or unusable environment (exit code 2)."""


# ---------------------------------------------------------------- HTTP ----


@dataclass(frozen=True)
class Response:
    status: int | None
    headers: dict[str, str]
    text: str
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.status is not None and 200 <= self.status < 300

    def json(self) -> Any:
        return json.loads(self.text or "null")


def http(
    url: str,
    *,
    method: str = "GET",
    data: Any = None,
    headers: dict[str, str] | None = None,
    timeout: float = 10.0,
) -> Response:
    req_headers = {"User-Agent": USER_AGENT}
    req_headers.update(headers or {})
    body: bytes | None = None
    if data is not None:
        if isinstance(data, (dict, list)):
            body = json.dumps(data).encode("utf-8")
            req_headers.setdefault("Content-Type", "application/json")
        elif isinstance(data, bytes):
            body = data
        else:
            body = str(data).encode("utf-8")
    try:
        req = urllib.request.Request(url, data=body, method=method, headers=req_headers)
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return Response(
                status=response.status,
                headers=dict(response.headers.items()),
                text=response.read().decode("utf-8", errors="replace"),
            )
    except urllib.error.HTTPError as exc:
        return Response(
            status=exc.code,
            headers=dict(exc.headers.items()),
            text=exc.read().decode("utf-8", errors="replace"),
            error=str(exc),
        )
    except Exception as exc:  # server down, DNS failure, timeout ...
        return Response(status=None, headers={}, text="", error=str(exc))


class ZoteroLocal:
    """Read access to Zotero Desktop's local API plus the connector import route."""

    def __init__(self, base_url: str = DEFAULT_BASE_URL, timeout: float = 10.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def request(self, path: str, *, method: str = "GET", data: Any = None,
                content_type: str | None = None, timeout: float | None = None) -> Response:
        headers: dict[str, str] = {}
        if path.startswith("/api"):
            headers.update(API_VERSION_HEADERS)
        if path.startswith("/connector"):
            headers.update(CONNECTOR_HEADERS)
        if content_type:
            headers["Content-Type"] = content_type
        return http(self.base_url + path, method=method, data=data, headers=headers,
                    timeout=timeout or self.timeout)

    def get_json(self, path: str) -> Any:
        response = self.request(path)
        if not response.ok:
            detail = response.error or response.text[:300]
            raise ConnectionError(f"GET {path} failed: status={response.status} {detail}")
        return response.json()

    @staticmethod
    def library_prefix(library: str) -> str:
        """'user' -> /api/users/0 ; 'group:<id>' -> /api/groups/<id>."""
        if library in ("", "user", "users/0"):
            return "/api/users/0"
        if library.startswith("group:"):
            group_id = library.split(":", 1)[1]
            if not group_id.isdigit():
                raise UsageError(f"invalid group library id: {library}")
            return f"/api/groups/{group_id}"
        raise UsageError(f"unknown library selector: {library} (use 'user' or 'group:<id>')")

    def search(self, text: str, *, library: str = "user", limit: int = 25,
               everything: bool = False) -> list[dict[str, Any]]:
        params = {"q": text, "limit": limit, "format": "json"}
        if everything:
            params["qmode"] = "everything"
        prefix = self.library_prefix(library)
        return self.get_json(f"{prefix}/items/top?{urllib.parse.urlencode(params)}") or []

    def item(self, key: str, *, library: str = "user") -> dict[str, Any]:
        prefix = self.library_prefix(library)
        return self.get_json(f"{prefix}/items/{urllib.parse.quote(key)}")

    def csljson(self, key: str, *, library: str = "user") -> dict[str, Any]:
        prefix = self.library_prefix(library)
        data = self.get_json(f"{prefix}/items/{urllib.parse.quote(key)}?format=csljson")
        if isinstance(data, dict) and "items" in data:
            data = data["items"]
        if not isinstance(data, list) or len(data) != 1:
            raise ValueError(f"unexpected CSL-JSON payload for {key}")
        return data[0]


def item_uri(item: dict[str, Any]) -> str:
    """Build the canonical Zotero item URI from the *item's own* library object.

    Raises ValueError when the library identity cannot be verified (e.g. an
    unsynced local library whose local user key the local API does not expose).
    """
    key = item.get("key") or (item.get("data") or {}).get("key")
    library = item.get("library") or {}
    lib_type, lib_id = library.get("type"), library.get("id")
    if not key or not re.fullmatch(r"[A-Z0-9]{8}", str(key)):
        raise ValueError(f"invalid Zotero item key: {key!r}")
    if lib_type == "user" and isinstance(lib_id, int) and lib_id > 0:
        return f"http://zotero.org/users/{lib_id}/items/{key}"
    if lib_type == "group" and isinstance(lib_id, int) and lib_id > 0:
        return f"http://zotero.org/groups/{lib_id}/items/{key}"
    raise ValueError(
        f"cannot verify library namespace for item {key} (library={library}); "
        "the library may be local-only/unsynced — take the URI from an existing "
        "Zotero-generated field or sync the library first"
    )


# -------------------------------------------------------- normalization ----

_DOI_PREFIX = re.compile(r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)", re.I)
_DOI_FIND = re.compile(r"10\.\d{4,9}/[^\s\"<>]+", re.I)


def normalize_doi(value: str | None) -> str | None:
    if not value:
        return None
    text = urllib.parse.unquote(str(value).strip())
    text = _DOI_PREFIX.sub("", text)
    match = _DOI_FIND.search(text)
    if not match:
        return None
    doi = match.group(0).rstrip(".,;:)]}'\"").lower()
    return doi or None


def normalize_title(value: str | None) -> str:
    if not value:
        return ""
    text = unicodedata.normalize("NFKC", str(value))
    text = re.sub(r"<[^>]+>", " ", text)  # strip inline HTML such as <i>
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch)).casefold()
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def title_similarity(a: str | None, b: str | None) -> float:
    """Character sequence ratio (robust to plurals/typos) blended with token Dice, in [0, 1]."""
    from difflib import SequenceMatcher

    na, nb = normalize_title(a), normalize_title(b)
    if not na or not nb:
        return 0.0
    if na == nb:
        return 1.0
    ta, tb = set(na.split()), set(nb.split())
    dice = 2 * len(ta & tb) / (len(ta) + len(tb))
    ratio = SequenceMatcher(None, na, nb).ratio()
    return round(0.7 * ratio + 0.3 * dice, 4)


def normalize_name(value: str | None) -> str:
    return normalize_title(value).replace(" ", "")


def extract_pmid(value: str | None) -> str | None:
    if not value:
        return None
    match = re.search(r"PMID:?\s*(\d{5,9})", str(value), re.I)
    return match.group(1) if match else None


def year_of(value: Any) -> str | None:
    match = re.search(r"(1[5-9]\d\d|20\d\d)", str(value or ""))
    return match.group(1) if match else None


def zotero_item_summary(item: dict[str, Any]) -> dict[str, Any]:
    """Flatten a local-API JSON item into the fields used for matching."""
    data = item.get("data", item)
    creators = data.get("creators") or []
    first = creators[0] if creators else {}
    first_author = first.get("lastName") or first.get("name") or ""
    extra = data.get("extra") or ""
    return {
        "key": data.get("key") or item.get("key"),
        "itemType": data.get("itemType"),
        "title": data.get("title") or "",
        "doi": normalize_doi(data.get("DOI") or data.get("url") or extra),
        "pmid": extract_pmid(extra) or extract_pmid(data.get("archiveLocation")),
        "year": year_of(data.get("date") or (item.get("meta") or {}).get("parsedDate")),
        "firstAuthor": first_author,
        "library": {k: (item.get("library") or {}).get(k) for k in ("type", "id", "name")},
        "parentItem": data.get("parentItem"),
    }
