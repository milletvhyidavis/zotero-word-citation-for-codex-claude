# Where citations go

## Mode 1 — markers in the text (`--placeholders`)

Markers are replaced by fields at the same position:

| Marker | Meaning |
|---|---|
| `[@ref:C4]` | refId from reference-map.json |
| `[@ref:C4; @ref:C9]` | one field, two items |
| `[@zotero:ABCD1234]` / `[@key:ABCD1234]` | Zotero key (fetched read-only if not in the map) |
| `[@doi:10.1000/xyz]` | DOI resolved in the map |

Put the marker directly after the claim, before the sentence punctuation for numeric styles (`...signalling[@ref:C4].`), or where the target journal wants it. Markers may be split across Word runs; they are found on the paragraph text. An unresolved marker aborts the insertion (nothing is written).

## Mode 2 — `placements.json` (text must not change)

```json
{"placements": [
  {"id": "P1", "anchor": "is required for T-cell priming", "refs": ["C4"]},
  {"id": "P2", "anchor": "tumour mutational burden", "paragraphContains": "Biomarkers", "occurrence": 2,
   "refs": ["C7", "C9"]},
  {"id": "P3", "anchor": "Checkpoint inhibitors", "position": "before", "keys": ["ABCD1234"],
   "spaceBefore": false}
 ],
 "bibliography": {"heading": "References"}}
```

- `anchor` is matched on the paragraph's visible text (outside existing fields); whitespace and straight/curly quotes are matched loosely.
- An anchor matching several places is an error unless `occurrence`, `paragraph` or `paragraphContains` makes it unique — reproducibility over convenience.
- Two placements at the same point are rejected: merge them into one with several refs.
- Always run with `--dry-run` first and read each `context` (`...text <<CITE>> text...`).

## Migrating citations from an old draft to a new one

1. Align sections by heading, then sentences by similarity; the citation belongs to the sentence making the claim, not to the end of the paragraph.
2. Merge numbers cited together into one placement.
3. Record for each placement: old sentence, new sentence, similarity, decision.
4. Similarity below ~0.8, split/merged sentences, or claims that vanished → list them for the user; do not insert them silently. A claim deleted from the new text loses its citation.
5. Never edit the new text to make an anchor fit.
