# Workflow and decision tree

`$PY` = chosen Python, `$S` = `"$SKILL_DIR/scripts"`, `$W` = a work folder (e.g. `<document dir>/zotero-work/`).

## A. New manuscript written by the agent

1. Draft the text in Markdown. After each claim that needs support, put a marker with a temporary id: `...is required for T-cell priming [@ref:PD1a]`. Several sources: `[@ref:A; @ref:B]`. Headings with `#`/`##`; end with `## References` (or `## 参考文献`).
2. For each claim run a search (step B) and pick real papers. Then rewrite the markers to the chosen candidate refIds, or build one `refs.json` list whose `refId` values equal the marker ids.
3. `"$PY" $S/resolve_references.py --references $W/refs.json --out $W/reference-map.json`
4. Missing → import (section D) → rerun 3.
5. `"$PY" $S/md_to_docx.py --input $W/review.md --output $W/review.docx`
6. `"$PY" $S/insert_zotero_fields.py --input $W/review.docx --items $W/reference-map.json --placeholders --style vancouver --bibliography-heading "References" --report $W/insert-report.json`
7. Validate / render / report (section E).

## B. Literature search

```bash
"$PY" $S/search_literature.py search "PD-1 blockade melanoma overall survival" --source openalex,pubmed --limit 8 --from-year 2010 --out $W/cand-pd1.json
"$PY" $S/search_literature.py lookup --doi 10.1056/NEJMoa1003466 --out $W/lookup.json
```

- Candidates carry `refId` `C1..Cn` per file. When combining several searches into one `refs.json`, give every chosen record a unique `refId` (e.g. the marker id) — keep the rest of the record unchanged.
- Choose by reading title + abstract; prefer landmark primary studies and authoritative reviews; record which claim each supports.

## C. Existing DOCX, citations to add, text must stay unchanged

1. `"$PY" $S/validate_zotero_docx.py in.docx --json` — baseline (existing fields, namespaces, itemData coverage). If the sender claims live citations but none are found, stop.
2. `"$PY" $S/insert_zotero_fields.py --input in.docx --list-paragraphs > $W/paragraphs.json`
3. Write `$W/placements.json` (see citation-placement.md). Dry run: add `--dry-run` and review the `context` of every placement.
4. Insert with `--placements $W/placements.json`; baseline preservation is checked automatically when the input already has Zotero fields.

## D. Import missing items (write, approval required)

```bash
"$PY" $S/build_import_file.py --map $W/reference-map.json --format ris --out $W/missing.ris --tag zwlc-import
"$PY" $S/zotero_local.py selected-target
# show the user: count, titles, target collection/library -> wait for "yes"
"$PY" $S/zotero_local.py import-ris --file $W/missing.ris --expect-target "<collection name>" --yes
"$PY" $S/resolve_references.py --references $W/refs.json --out $W/reference-map.json
```

Zotero may need a few seconds to index new items; if an imported DOI is still missing, wait and resolve again before reporting failure.

## E. Validation and delivery

```bash
"$PY" $S/validate_zotero_docx.py out.docx --baseline in.docx --expected-increase N --require-item-data --expect-bibliography --expect-style vancouver
"$PY" $S/word_render.py out.docx --pdf $W/out.pdf     # optional, Windows + Word
```

Look at every PDF page when rendering (headings, citations, bibliography, tables, page breaks). Report structural validation, Word rendering and Zotero Refresh as three separate results.

## Exit codes (all scripts)

0 success · 1 validation failure, or unresolved references in `resolve_references.py` (the map is still written) · 2 usage or environment error — including a `[@…]` marker in `insert_zotero_fields.py` that names an unknown ref (nothing is written).
