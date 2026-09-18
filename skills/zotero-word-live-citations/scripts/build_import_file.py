#!/usr/bin/env python3
"""Build a RIS or BibTeX file for references missing from Zotero (does NOT import).

Reads a reference-map.json (from resolve_references.py) and writes the records
listed under "missing" - or only the --ref-id values given - so the user can
review them before `zotero_local.py import-ris --file ... --yes`.

Records without a title are skipped and reported; nothing is invented.

  build_import_file.py --map reference-map.json --format ris --out missing.ris
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import EXIT_FAIL, EXIT_OK, EXIT_USAGE, load_json, utf8_stdio  # noqa: E402

RIS_TYPES = {"article-journal": "JOUR", "article": "JOUR", "paper-conference": "CONF",
             "chapter": "CHAP", "book": "BOOK", "thesis": "THES", "report": "RPRT"}
BIB_TYPES = {"article-journal": "article", "article": "article", "paper-conference": "inproceedings",
             "chapter": "incollection", "book": "book", "thesis": "phdthesis", "report": "techreport"}


def author_name(a: dict[str, Any]) -> str:
    if a.get("literal"):
        return a["literal"]
    return f"{a.get('family', '').strip()}, {a.get('given', '').strip()}".strip(", ")


def split_pages(pages: str | None) -> tuple[str | None, str | None]:
    if not pages:
        return None, None
    parts = re.split(r"\s*[-–—]\s*", str(pages), maxsplit=1)
    return parts[0] or None, (parts[1] if len(parts) > 1 and parts[1] else None)


def to_ris(rec: dict[str, Any], tags: list[str]) -> str:
    lines = [f"TY  - {RIS_TYPES.get(rec.get('type') or '', 'JOUR')}"]
    add = lambda tag, value: value and lines.append(f"{tag}  - {str(value).strip()}")  # noqa: E731
    add("TI", rec.get("title"))
    for a in rec.get("authors") or []:
        add("AU", author_name(a))
    add("PY", rec.get("year"))
    add("T2", rec.get("journal"))
    add("VL", rec.get("volume"))
    add("IS", rec.get("issue"))
    sp, ep = split_pages(rec.get("pages"))
    add("SP", sp)
    add("EP", ep)
    add("DO", rec.get("doi"))
    add("AN", rec.get("pmid") and f"PMID:{rec['pmid']}")
    add("UR", rec.get("url") or (rec.get("doi") and f"https://doi.org/{rec['doi']}"))
    add("AB", rec.get("abstract"))
    for tag in tags:
        add("KW", tag)
    lines.append("ER  - ")
    return "\n".join(lines)


def bib_escape(value: str) -> str:
    return str(value).replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")


def to_bibtex(rec: dict[str, Any], tags: list[str]) -> str:
    first = (rec.get("authors") or [{}])[0]
    base = re.sub(r"\W", "", (first.get("family") or first.get("literal") or "ref")).lower() or "ref"
    key = f"{base}{rec.get('year') or ''}_{re.sub(r'[^A-Za-z0-9]', '', str(rec['refId']))}"
    fields = {
        "title": rec.get("title"),
        "author": " and ".join(author_name(a) for a in rec.get("authors") or []) or None,
        "year": rec.get("year"), "journal": rec.get("journal"), "volume": rec.get("volume"),
        "number": rec.get("issue"), "pages": rec.get("pages"), "doi": rec.get("doi"),
        "pmid": rec.get("pmid"), "url": rec.get("url"), "abstract": rec.get("abstract"),
        "keywords": ", ".join(tags) or None,
    }
    body = ",\n".join(f"  {k} = {{{bib_escape(v)}}}" for k, v in fields.items() if v)
    return f"@{BIB_TYPES.get(rec.get('type') or '', 'article')}{{{key},\n{body}\n}}"


def main(argv: list[str] | None = None) -> int:
    utf8_stdio()
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--map", required=True, type=Path, help="reference-map.json")
    parser.add_argument("--format", choices=("ris", "bibtex"), default="ris")
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--ref-id", action="append", default=[],
                        help="export only these refIds (default: all 'missing')")
    parser.add_argument("--tag", action="append", default=[],
                        help="add a Zotero tag to every record (e.g. zwlc-import)")
    args = parser.parse_args(argv)

    try:
        data = load_json(args.map)
    except (OSError, ValueError) as exc:
        print(f"ERROR: cannot read map: {exc}", file=sys.stderr)
        return EXIT_USAGE
    by_id = {str(r["refId"]): r for r in data.get("references", [])}
    wanted = args.ref_id or [str(m["refId"]) for m in data.get("missing", [])]
    if not wanted:
        print("Nothing to export: no missing references.", file=sys.stderr)
        return EXIT_OK
    chunks, skipped = [], []
    for rid in wanted:
        rec = by_id.get(rid)
        if rid in data.get("resolved", {}):
            skipped.append(f"{rid}: already in Zotero ({data['resolved'][rid]['key']})")
        elif not rec or not rec.get("title"):
            skipped.append(f"{rid}: no structured title - look it up with search_literature.py first")
        else:
            chunks.append(to_ris(rec, args.tag) if args.format == "ris" else to_bibtex(rec, args.tag))
    for s in skipped:
        print(f"SKIPPED {s}", file=sys.stderr)
    if not chunks:
        print("ERROR: no exportable records", file=sys.stderr)
        return EXIT_FAIL
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n\n".join(chunks) + "\n", encoding="utf-8")
    print(f"{len(chunks)} record(s) -> {args.out} (review before importing)", file=sys.stderr)
    return EXIT_OK if not skipped else EXIT_FAIL


if __name__ == "__main__":
    raise SystemExit(main())
