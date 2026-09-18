#!/usr/bin/env python3
"""Map reference records to Zotero parent items (read-only).

Input (--references) may be:
  * JSON: a list of reference records (e.g. from search_literature.py) or
    {"references": [...]}; a record may pin an item with "zoteroKey";
  * RIS (.ris);
  * plain text / Markdown (.txt/.md): one reference per line, optionally
    numbered ("1.", "[1]", "1)") - DOI/PMID/year/title are extracted.

Matching order: pinned key > DOI exact > PMID exact > normalized-title exact >
title similarity + first author + year. Several plausible candidates -> the
reference goes to "ambiguous" (never silently chosen). Attachments/notes are
never matched. Several library items sharing one DOI/PMID are reported under
"duplicates" and not merged.

Output (--out reference-map.json):
  {"totalReferences", "resolved": {refId: {key, uri, itemData, title, year,
   matchMethod, score}}, "missing": [...], "ambiguous": [...],
   "duplicates": [...], "references": [...], "libraryNamespaces": [...]}

Exit code 0 when every reference resolved, 1 when some are missing/ambiguous
(the map is still written), 2 on usage/connection errors.
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (  # noqa: E402
    DEFAULT_BASE_URL, EXIT_FAIL, EXIT_OK, EXIT_USAGE, NON_CITABLE_TYPES, ZoteroLocal,
    dump_json, extract_pmid, item_uri, load_json, normalize_doi, normalize_name,
    normalize_title, title_similarity, utf8_stdio, year_of, zotero_item_summary,
)

# ------------------------------------------------------------ parsing ----

RIS_TAGS = {"TI": "title", "T1": "title", "JO": "journal", "JF": "journal", "T2": "journal",
            "VL": "volume", "IS": "issue", "DO": "doi", "UR": "url", "AB": "abstract",
            "ID": "refId"}


def parse_ris(text: str) -> list[dict[str, Any]]:
    records, cur = [], None
    sp = ep = None
    for line in text.splitlines():
        m = re.match(r"^([A-Z][A-Z0-9])  - ?(.*)$", line)
        if not m:
            continue
        tag, value = m.group(1), m.group(2).strip()
        if tag == "TY":
            cur, sp, ep = {"authors": [], "sourceFormat": "ris"}, None, None
            continue
        if cur is None:
            continue
        if tag == "ER":
            if sp:
                cur["pages"] = sp + (f"-{ep}" if ep else "")
            records.append(cur)
            cur = None
        elif tag in ("AU", "A1"):
            fam, _, giv = value.partition(",")
            cur["authors"].append({"family": fam.strip(), "given": giv.strip()})
        elif tag in ("PY", "Y1", "DA"):
            cur.setdefault("year", year_of(value))
        elif tag == "SP":
            sp = value
        elif tag == "EP":
            ep = value
        elif tag == "AN" or (tag in ("N1", "M1") and "PMID" in value.upper()):
            cur.setdefault("pmid", extract_pmid(value) or (value if value.isdigit() else None))
        elif tag in RIS_TAGS:
            cur.setdefault(RIS_TAGS[tag], value)
    return records


_NUM = re.compile(r"^\s*(?:\[(\d+)\]|(\d+)[.)]|(\d+)\s)\s*")


def guess_title(line: str) -> str | None:
    """Best-effort title from a formatted reference string (Vancouver / APA)."""
    text = re.sub(r"\s*(?:https?://\S+|doi:\s*\S+|PMID:?\s*\d+)\s*", " ", line, flags=re.I).strip()
    apa = re.search(r"\((?:19|20)\d\d[a-z]?\)\.\s*(.+?)[.?!](?:\s|$)", text)
    if apa:
        return apa.group(1).strip()
    parts = [p.strip() for p in re.split(r"\.\s+", text) if p.strip()]
    if len(parts) >= 2:
        return parts[1]
    return None


def parse_text(text: str) -> list[dict[str, Any]]:
    records = []
    for n, raw in enumerate(l for l in text.splitlines() if l.strip()):
        line = raw.strip().lstrip("-*").strip()
        if not line or line.startswith("#"):
            continue
        m = _NUM.match(line)
        ref_id = next((g for g in m.groups() if g), None) if m else None
        body = line[m.end():] if m else line
        first = re.match(r"\s*([^\s,.;]+)", body)
        records.append({
            "refId": ref_id or str(len(records) + 1),
            "raw": body,
            "title": guess_title(body),
            "doi": normalize_doi(body),
            "pmid": extract_pmid(body),
            "year": year_of(body),
            "authors": [{"family": first.group(1)}] if first else [],
            "sourceFormat": "text",
        })
    return records


def load_references(path: Path) -> list[dict[str, Any]]:
    suffix = path.suffix.lower()
    if suffix == ".json":
        data = load_json(path)
        refs = data.get("references", data) if isinstance(data, dict) else data
        if not isinstance(refs, list):
            raise ValueError("JSON references must be a list or {'references': [...]} ")
        records = [dict(r) for r in refs]
    elif suffix == ".ris":
        records = parse_ris(path.read_text(encoding="utf-8-sig"))
    else:
        records = parse_text(path.read_text(encoding="utf-8-sig"))
    seen: set[str] = set()
    for n, rec in enumerate(records, 1):
        rid = str(rec.get("refId") or n)
        if rid in seen:
            rid = f"{rid}-{n}"
        seen.add(rid)
        rec["refId"] = rid
        rec["doi"] = normalize_doi(rec.get("doi"))
        rec["pmid"] = str(rec["pmid"]) if rec.get("pmid") else None
        rec["year"] = year_of(rec.get("year"))
    return records


# ------------------------------------------------------------ matching ----

def first_author(rec: dict[str, Any]) -> str:
    authors = rec.get("authors") or []
    if not authors:
        return ""
    a = authors[0]
    return a.get("family") or a.get("literal") or ""


def author_matches(ref_author: str, item_author: str) -> bool:
    ra, ia = normalize_name(ref_author), normalize_name(item_author)
    return bool(ra and ia) and (ra == ia or ia.startswith(ra) or ra.startswith(ia))


def score_candidate(ref: dict[str, Any], cand: dict[str, Any]) -> dict[str, Any]:
    title = ref.get("title")
    if title:
        sim = title_similarity(title, cand["title"])
    elif ref.get("raw"):  # free text without a parsable title: token containment
        ct = set(normalize_title(cand["title"]).split())
        rt = set(normalize_title(ref["raw"]).split())
        sim = round(len(ct & rt) / len(ct), 4) if ct else 0.0
    else:
        sim = 0.0
    year_ok = bool(ref.get("year") and cand.get("year") and ref["year"] == cand["year"])
    year_conflict = bool(ref.get("year") and cand.get("year") and ref["year"] != cand["year"])
    auth_ok = author_matches(first_author(ref), cand.get("firstAuthor") or "")
    accept = (sim >= 0.97 and not year_conflict) or \
             (sim >= 0.90 and (year_ok or auth_ok) and not year_conflict) or \
             (sim >= 0.80 and year_ok and auth_ok)
    score = round(sim + 0.05 * year_ok + 0.05 * auth_ok - 0.1 * year_conflict, 4)
    return {"key": cand["key"], "title": cand["title"], "year": cand.get("year"),
            "firstAuthor": cand.get("firstAuthor"), "similarity": sim, "score": score,
            "yearMatch": year_ok, "authorMatch": auth_ok, "accept": accept}


def citable(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for it in items:
        s = zotero_item_summary(it)
        if s["itemType"] in NON_CITABLE_TYPES or s["parentItem"]:
            continue
        s["_raw"] = it
        out.append(s)
    return out


SearchFn = Callable[[str, bool], list[dict[str, Any]]]


def resolve_one(ref: dict[str, Any], search: SearchFn, fetch: Callable[[str], dict[str, Any]]
                ) -> tuple[str, dict[str, Any]]:
    """Return (status, payload) with status in resolved|missing|ambiguous."""
    if ref.get("zoteroKey"):
        item = fetch(ref["zoteroKey"])
        s = citable([item])
        if not s:
            return "missing", {"reason": f"pinned key {ref['zoteroKey']} is not a citable parent item"}
        return "resolved", {"item": s[0], "matchMethod": "manual", "score": 1.0}

    for field, method in (("doi", "doi"), ("pmid", "pmid")):
        value = ref.get(field)
        if not value:
            continue
        hits = [c for c in citable(search(value, True))
                if (c["doi"] == value if field == "doi" else c["pmid"] == value)]
        unique = {c["key"]: c for c in hits}
        if len(unique) == 1:
            return "resolved", {"item": next(iter(unique.values())), "matchMethod": method, "score": 1.0}
        if len(unique) > 1:
            return "ambiguous", {"reason": f"{len(unique)} library items share this {method.upper()}",
                                 "duplicateKeys": sorted(unique),
                                 "candidates": [score_candidate(ref, c) for c in unique.values()]}

    title = ref.get("title") or ref.get("raw")
    if not title:
        return "missing", {"reason": "no DOI, PMID or title to search"}
    words = normalize_title(ref.get("title") or "").split()
    queries = [" ".join(words[:8])] if words else []
    if ref.get("raw") and not ref.get("title"):
        queries.append(" ".join(normalize_title(ref["raw"]).split()[:6]))
    pool: dict[str, dict[str, Any]] = {}
    for q in queries:
        if q:
            for c in citable(search(q, False)):
                pool[c["key"]] = c
    if not pool:
        return "missing", {"reason": "no library item matched the title"}
    scored = sorted((score_candidate(ref, c) for c in pool.values()),
                    key=lambda s: s["score"], reverse=True)
    exact = [s for s in scored if normalize_title(s["title"]) == normalize_title(ref.get("title"))
             and not (ref.get("year") and s["year"] and s["year"] != ref["year"])]
    accepted = [s for s in scored if s["accept"]]
    if len(exact) == 1:
        return "resolved", {"item": pool[exact[0]["key"]], "matchMethod": "title", "score": exact[0]["score"]}
    if len(exact) > 1:
        return "ambiguous", {"reason": "several items with identical title",
                             "duplicateKeys": [s["key"] for s in exact], "candidates": exact}
    if len(accepted) == 1 or (len(accepted) > 1 and accepted[0]["score"] - accepted[1]["score"] >= 0.1):
        return "resolved", {"item": pool[accepted[0]["key"]], "matchMethod": "title-fuzzy",
                            "score": accepted[0]["score"]}
    if accepted:
        return "ambiguous", {"reason": "several plausible title matches", "candidates": accepted[:5]}
    return "missing", {"reason": "no candidate passed the title/author/year threshold",
                       "nearest": scored[:3]}


def resolve_all(refs: list[dict[str, Any]], z: ZoteroLocal, library: str) -> dict[str, Any]:
    cache: dict[tuple[str, bool], list[dict[str, Any]]] = {}

    def search(q: str, everything: bool) -> list[dict[str, Any]]:
        if (q, everything) not in cache:
            cache[(q, everything)] = z.search(q, library=library, limit=50, everything=everything)
        return cache[(q, everything)]

    report: dict[str, Any] = {
        "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "zoteroBaseUrl": z.base_url, "library": library,
        "totalReferences": len(refs), "resolved": {}, "missing": [], "ambiguous": [],
        "duplicates": [], "libraryNamespaces": [], "references": refs,
    }
    namespaces: set[str] = set()
    for ref in refs:
        status, payload = resolve_one(ref, search, lambda k: z.item(k, library=library))
        rid = ref["refId"]
        if payload.get("duplicateKeys"):
            report["duplicates"].append({"refId": rid, "keys": payload["duplicateKeys"]})
        if status == "resolved":
            s = payload["item"]
            try:
                uri = item_uri(s["_raw"])
            except ValueError as exc:
                report["missing"].append({"refId": rid, "title": ref.get("title"), "reason": str(exc)})
                continue
            item_data = z.csljson(s["key"], library=library)
            namespaces.add(uri.split("/items/")[0].split("zotero.org/", 1)[1])
            report["resolved"][rid] = {
                "key": s["key"], "uri": uri, "itemData": item_data, "title": s["title"],
                "year": s["year"], "doi": s["doi"], "matchMethod": payload["matchMethod"],
                "score": payload["score"],
            }
        elif status == "ambiguous":
            report["ambiguous"].append({"refId": rid, "title": ref.get("title") or ref.get("raw"),
                                        "reason": payload["reason"],
                                        "candidates": payload.get("candidates", [])})
        else:
            entry = {"refId": rid, "title": ref.get("title") or ref.get("raw"),
                     "doi": ref.get("doi"), "reason": payload["reason"]}
            if payload.get("nearest"):
                entry["nearest"] = payload["nearest"]
            report["missing"].append(entry)
    report["libraryNamespaces"] = sorted(namespaces)
    return report


def main(argv: list[str] | None = None) -> int:
    utf8_stdio()
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--references", required=True, type=Path,
                        help="references file (.json/.ris/.txt/.md)")
    parser.add_argument("--out", required=True, type=Path, help="reference-map JSON to write")
    parser.add_argument("--library", default="user", help="'user' (default) or 'group:<id>'")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    args = parser.parse_args(argv)
    try:
        refs = load_references(args.references.expanduser())
    except (OSError, ValueError) as exc:
        print(f"ERROR: cannot read references: {exc}", file=sys.stderr)
        return EXIT_USAGE
    if not refs:
        print("ERROR: no references found in input", file=sys.stderr)
        return EXIT_USAGE
    z = ZoteroLocal(args.base_url)
    try:
        report = resolve_all(refs, z, args.library)
    except ConnectionError as exc:
        print(f"ERROR: Zotero not reachable: {exc}", file=sys.stderr)
        return EXIT_USAGE
    dump_json(report, args.out)
    print(f"references={report['totalReferences']} resolved={len(report['resolved'])} "
          f"missing={len(report['missing'])} ambiguous={len(report['ambiguous'])} "
          f"duplicates={len(report['duplicates'])} -> {args.out}", file=sys.stderr)
    return EXIT_OK if not report["missing"] and not report["ambiguous"] else EXIT_FAIL


if __name__ == "__main__":
    raise SystemExit(main())
