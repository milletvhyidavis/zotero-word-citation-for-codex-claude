#!/usr/bin/env python3
"""Talk to Zotero Desktop's local API (read) and connector (import, needs --yes).

Subcommands:
  status           API / connector reachability and Zotero version
  search           search top-level items (attachments/notes excluded)
  item             one item's metadata + verified URI + CSL itemData
  collections      list collections (key, name, parent)
  groups           list group libraries visible locally
  selected-target  the library/collection currently selected in Zotero
                   (this is where connector imports land)
  import-ris       import a RIS file into the selected target   (--yes required)
  import-bibtex    import a BibTeX file into the selected target (--yes required)

Stdlib only. Never changes Zotero preferences; only import-* writes, and only
with --yes after the user has approved the item count and target.
"""

from __future__ import annotations

import argparse
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (  # noqa: E402
    DEFAULT_BASE_URL, EXIT_FAIL, EXIT_OK, EXIT_USAGE, NON_CITABLE_TYPES,
    UsageError, ZoteroLocal, dump_json, item_uri, utf8_stdio, zotero_item_summary,
)


def status(z: ZoteroLocal) -> dict:
    api = z.request("/api/", timeout=3)
    connector = z.request("/connector/ping", timeout=3)
    items_ok = False
    logged_in, user_id = None, None
    if api.ok:
        probe = z.request("/api/users/0/items/top?limit=1&format=keys", timeout=5)
        items_ok = probe.ok
        logged_in, user_id = z.login_state()
    if not api.ok:
        hint = ("Start Zotero Desktop and enable Settings > Advanced > "
                "'Allow other applications on this computer to communicate with Zotero'."
                if not connector.ok else
                "Connector is up but /api/ is not: enable the local API in Zotero settings "
                "(same checkbox, Zotero 7+).")
    elif logged_in is False:
        hint = ("Zotero is not signed in: sign in to a zotero.org account in "
                "Settings > Sync and sync once, otherwise citation URIs cannot be built.")
    else:
        hint = None
    return {
        "baseUrl": z.base_url,
        "apiReachable": api.ok,
        "apiStatus": api.status,
        "apiError": api.error,
        "itemsReadable": items_ok,
        "loggedIn": logged_in,
        "userLibraryId": user_id,
        "connectorReachable": connector.ok,
        "zoteroVersion": api.headers.get("X-Zotero-Version")
        or connector.headers.get("X-Zotero-Version"),
        "hint": hint,
    }


def count_records(text: str, kind: str) -> int:
    if kind == "ris":
        return sum(1 for line in text.splitlines() if line.startswith("TY  -"))
    return sum(1 for line in text.splitlines() if line.lstrip().startswith("@")
               and not line.lstrip().lower().startswith(("@comment", "@string", "@preamble")))


def main(argv: list[str] | None = None) -> int:
    utf8_stdio()
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL,
                        help="Zotero local server (default %(default)s or $ZOTERO_LOCAL_BASE_URL)")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("status", help="check API/connector reachability")

    p = sub.add_parser("search", help="search top-level items")
    p.add_argument("query")
    p.add_argument("--library", default="user", help="'user' (default) or 'group:<id>'")
    p.add_argument("--limit", type=int, default=25)
    p.add_argument("--everything", action="store_true", help="also search full text/notes")

    p = sub.add_parser("item", help="item metadata + URI + CSL itemData")
    p.add_argument("key")
    p.add_argument("--library", default="user")

    sub.add_parser("collections", help="list collections")
    sub.add_parser("groups", help="list group libraries")
    sub.add_parser("selected-target", help="currently selected library/collection")

    for kind in ("ris", "bibtex"):
        p = sub.add_parser(f"import-{kind}", help=f"import {kind.upper()} (writes to Zotero)")
        p.add_argument("--file", required=True, type=Path)
        p.add_argument("--yes", action="store_true",
                       help="confirm the user approved this import")
        p.add_argument("--expect-target", metavar="NAME",
                       help="refuse unless the selected Zotero collection/library has this name")
        p.add_argument("--expect-library-id", metavar="ID",
                       help="refuse unless the selected libraryID (from selected-target) matches")
        p.add_argument("--expect-collection-id", metavar="ID",
                       help="refuse unless the selected collection id (from selected-target) "
                            "matches; use 'null' when the library root is selected")

    args = parser.parse_args(argv)
    z = ZoteroLocal(args.base_url)

    try:
        if args.command == "status":
            payload = status(z)
            dump_json(payload)
            return EXIT_OK if payload["apiReachable"] and payload["itemsReadable"] else EXIT_FAIL

        if args.command == "search":
            rows = []
            for item in z.search(args.query, library=args.library, limit=args.limit,
                                 everything=args.everything):
                summary = zotero_item_summary(item)
                if summary["itemType"] in NON_CITABLE_TYPES:
                    continue
                try:
                    summary["uri"] = item_uri(item)
                except ValueError as exc:
                    summary["uri"] = None
                    summary["uriError"] = str(exc)
                rows.append(summary)
            dump_json(rows)
            return EXIT_OK

        if args.command == "item":
            item = z.item(args.key, library=args.library)
            summary = zotero_item_summary(item)
            if summary["itemType"] in NON_CITABLE_TYPES:
                print(f"ERROR: {args.key} is a {summary['itemType']}, not a citable parent item"
                      + (f"; parent is {summary['parentItem']}" if summary["parentItem"] else ""),
                      file=sys.stderr)
                return EXIT_FAIL
            summary["uri"] = item_uri(item)
            summary["itemData"] = z.csljson(args.key, library=args.library)
            dump_json(summary)
            return EXIT_OK

        if args.command == "collections":
            rows = []
            start = 0
            while True:
                page = z.get_json(f"/api/users/0/collections?limit=100&start={start}")
                for c in page:
                    d = c.get("data", c)
                    rows.append({"key": d.get("key"), "name": d.get("name"),
                                 "parent": d.get("parentCollection") or None})
                if len(page) < 100:
                    break
                start += 100
            dump_json(rows)
            return EXIT_OK

        if args.command == "groups":
            dump_json([{"id": g.get("id"), "name": (g.get("data") or {}).get("name")}
                       for g in z.get_json("/api/users/0/groups")])
            return EXIT_OK

        if args.command == "selected-target":
            response = z.request("/connector/getSelectedCollection", method="POST", data={})
            if not response.ok:
                raise ConnectionError(f"getSelectedCollection failed: {response.status} {response.error}")
            data = response.json()
            dump_json({k: data.get(k) for k in
                       ("libraryID", "libraryName", "libraryEditable", "id", "name")})
            return EXIT_OK

        if args.command in ("import-ris", "import-bibtex"):
            kind = args.command.split("-", 1)[1]
            text = args.file.expanduser().read_text(encoding="utf-8-sig")
            n = count_records(text, kind)
            if n == 0:
                raise UsageError(f"no {kind.upper()} records found in {args.file}")
            target = z.request("/connector/getSelectedCollection", method="POST", data={})
            if not target.ok:
                raise ConnectionError("cannot read the selected Zotero target; is Zotero running?")
            t = target.json()
            target_name = t.get("name") or t.get("libraryName")
            if not t.get("editable", t.get("libraryEditable", True)):
                raise UsageError(f"selected Zotero target '{target_name}' is not editable")
            if args.expect_target and args.expect_target != target_name:
                raise UsageError(f"selected Zotero target is '{target_name}', expected "
                                 f"'{args.expect_target}'. Select the right collection in Zotero.")
            # a name alone is not unique: libraries can hold collections with the same name
            for flag, key, expected in (("--expect-library-id", "libraryID", args.expect_library_id),
                                        ("--expect-collection-id", "id", args.expect_collection_id)):
                actual = "null" if t.get(key) is None else str(t.get(key))
                if expected is not None and expected != actual:
                    raise UsageError(f"selected Zotero target has {key}={actual}, expected {expected} "
                                     f"({flag}). Select the right collection in Zotero.")
            if not args.yes:
                print(f"Refusing to write: this would import {n} {kind.upper()} record(s) into "
                      f"'{target_name}' (library '{t.get('libraryName')}', "
                      f"libraryID={t.get('libraryID')}, collection id={t.get('id')}). "
                      "Re-run with --yes only after the user approves.", file=sys.stderr)
                return EXIT_USAGE
            session = f"zwlc-{uuid.uuid4().hex}"
            response = z.request(f"/connector/import?session={session}", method="POST",
                                 data=text, content_type="text/plain", timeout=60)
            if not response.ok:
                print(f"ERROR: import failed: status={response.status} "
                      f"{response.error or response.text[:300]}", file=sys.stderr)
                return EXIT_FAIL
            try:
                imported = response.json()
            except ValueError:
                imported = None
            dump_json({
                "requestedRecords": n,
                "target": target_name,
                "session": session,
                "connectorReportedItems": len(imported) if isinstance(imported, list) else None,
                "next": "Re-run resolve_references.py to read back the real item keys; "
                        "do not trust this response as proof of success.",
            })
            return EXIT_OK
    except UsageError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return EXIT_USAGE
    except (ConnectionError, ValueError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return EXIT_FAIL
    return EXIT_USAGE


if __name__ == "__main__":
    raise SystemExit(main())
