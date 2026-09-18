# Zotero write policy

Read-only operations need no confirmation: status, search, item, collections, selected-target, resolve, building RIS/BibTeX files, validating/rendering DOCX.

## Needs explicit user approval each time

| Action | Supported here | How |
|---|---|---|
| Import RIS/BibTeX | yes | `zotero_local.py import-ris|import-bibtex --yes` |
| Edit item metadata | no | tell the user what to change in Zotero |
| Merge/delete duplicates | no | report `duplicates`; the user merges in Zotero |
| Move items between collections | no | user does it in Zotero |

Before asking, show: number of records, their titles (or the RIS file), and the destination from `selected-target` (library + collection). Suggest a dedicated collection (e.g. "Imported by agent") and the `--tag zwlc-import` tag so the user can review or undo the import in Zotero. "Add citations" is **not** approval to import.

## After importing

- Never trust the connector response; re-run `resolve_references.py` and use the keys it returns.
- Items still missing → list as failures with the reason. Never write a guessed key or URI.
- If the import created duplicates of existing items, report them; do not delete.

## Received / collaborative documents

- Keep existing citations exactly (validator `--preserve-baseline-citations`).
- Citations from other libraries (other `users/<id>` or `groups/<id>`) are valid; do not re-link them to the user's items unless asked.
- Do not run Zotero Refresh on someone else's document on your own; warn about citations without embedded `itemData`.
