---
name: zotero-word-live-citations
description: Find relevant papers, match them to the user's local Zotero Desktop library, import missing ones (with approval), and write real live Zotero citation and bibliography fields (ADDIN ZOTERO_ITEM CSL_CITATION / ZOTERO_BIBL) into Word DOCX files, then validate them. Use when the user wants Zotero-linked, refreshable citations in a Word/DOCX manuscript, to add references to a draft from Zotero or from a literature search, to convert citation markers into Zotero fields, or to check whether a DOCX really contains valid Zotero fields. Not for plain-text-only reference lists.
---

# Zotero → Word live citations

End-to-end chain: **literature search → Zotero item (key + URI + CSL itemData) → DOCX Zotero field → user runs Zotero Refresh in Word.**
Every script is Python 3.9+ standard library only and has `--help`.

## 0. Setup (every task)

- `SKILL_DIR` = the directory containing this `SKILL.md`. Call scripts as `"$PY" "$SKILL_DIR/scripts/<name>.py"`; quote paths (spaces/Chinese are fine).
- Pick `PY` once: the first of `python3`, `python`, `py -3` whose `--version` prints ≥ 3.9 (on Windows skip the Microsoft Store stub that prints "Python was not found"). Codex users may also use the Codex-bundled `~/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python(.exe)`. If none exists, **guide the user to install it** — never install anything yourself: give them https://www.python.org/downloads/ , tell Windows users to tick **"Add python.exe to PATH"** in the installer (macOS: the python.org installer or `brew install python`), then to reopen the terminal/agent session and confirm with `python --version` / `py -3 --version`.
- Run `"$PY" "$SKILL_DIR/scripts/selftest.py"` and read the capabilities line. No Zotero → only validation/DOCX work is possible; no Word → skip visual rendering only.
- **Zotero onboarding (mandatory before steps 3–4; the local API is required).** Unless `selftest.py` already shows `zotero-local-api` as OK, stop and ask the user to:
  1. start Zotero Desktop (7+) and keep it running;
  2. open Settings → Advanced → Miscellaneous (Windows/Linux: Edit → Settings; macOS: Zotero → Settings…), tick **"Allow other applications on this computer to communicate with Zotero" / “允许此计算机上的其他应用程序与 Zotero 通讯”**, and **send you a screenshot of that settings page with the box ticked**;
  Check the screenshot (box ticked), then re-run `zotero_local.py status` and require `apiReachable` and `itemsReadable`.
- **Zotero sign-in (only when needed).** Most users are already signed in, so do not ask up front. Only if `status` shows `loggedIn: false`, or resolving reports *"cannot verify library namespace … local-only/unsynced"*, explain that citations need a signed-in library and ask the user to sign in to zotero.org in Zotero Settings → Sync (free account), sync once, and send a screenshot of the Sync page; then re-run `status` / resolving. Never change Zotero settings yourself and never ask for the user's password.
- **WPS is not supported.** Output must be opened, refreshed and saved only in Microsoft Word with the Zotero add-in; say so in the hand-off.
- Keep work files (candidates, maps, placements, reports) in a work folder next to the document or in the agent scratch dir, never inside `SKILL_DIR`.

## 1. Route the request

| User wants | Do |
|---|---|
| "Check whether this DOCX has valid Zotero fields" | step 6 only |
| Cite items already in Zotero | steps 3 → 5 → 6 |
| Find literature for a text and cite it | steps 2 → 3 → 4 → 5 → 6 |
| Write a manuscript and cite it | draft Markdown with `[@ref:ID]` markers → `md_to_docx.py` → steps 2–6 |

Full decision tree and command lines: [references/workflow.md](references/workflow.md).

## 2. Find papers (read-only)

`search_literature.py search "<topic query>" --source openalex,pubmed[,crossref] --limit 10 [--from-year Y] --out candidates.json`; confirm exact records with `search_literature.py lookup --doi … --pmid …`.
Read titles/abstracts and keep only papers that actually support the claim; show the user the chosen list (claim → paper). Never cite a paper that no tool returned; never invent DOIs. Host literature tools (PubMed/web search) may be used for discovery, but pass the final DOIs/PMIDs through `lookup`. Details: [references/literature-search.md](references/literature-search.md).

## 3. Resolve to Zotero items (read-only)

`resolve_references.py --references <candidates.json|refs.ris|refs.txt> --out reference-map.json` → `resolved` / `missing` / `ambiguous` / `duplicates`.
Order: pinned `zoteroKey` > DOI > PMID > exact title > title+author+year. Ambiguous entries are **never** auto-picked: show the candidates and let the user choose (pin with `"zoteroKey"` in the input JSON and rerun). Duplicates are reported, never merged or deleted.

## 4. Import missing items (WRITE — needs explicit approval)

1. `build_import_file.py --map reference-map.json --format ris --out missing.ris [--tag zwlc-import]`
2. `zotero_local.py selected-target` → tell the user: *N records → collection X in library Y* (imports land in whatever is selected in the Zotero window). Ask them to confirm or to select another collection first.
3. Only after a clear "yes": `zotero_local.py import-ris --file missing.ris --expect-target "<name>" --yes`
4. Re-run step 3 and use the new map. Items still missing are failures — never fabricate a key or URI.
Rules: [references/import-policy.md](references/import-policy.md).

## 5. Insert live fields into a copy of the DOCX

- Decide locations. Preferred: `[@ref:C3; @ref:C7]`, `[@zotero:KEY]` or `[@doi:…]` markers in the text + `--placeholders`. For an existing manuscript whose text must not change, write `placements.json` with exact anchors (use `--list-paragraphs` first). Place the citation right after the supported claim, one field per location, several items in one field. Low-confidence locations go to the user for review. See [references/citation-placement.md](references/citation-placement.md).
- `insert_zotero_fields.py --input in.docx --items reference-map.json (--placeholders | --placements p.json) --style <vancouver|apa|nature|gb-t-7714-numeric|…|CSL URL> [--locale zh-CN] --bibliography-heading "References" --report report.json`
- Output defaults to `<stem>-zotero-cited.docx`; the input is never overwritten. The script validates its own output against the input (baseline citations must survive).
Field format: [references/word-field-schema.md](references/word-field-schema.md).

## 6. Validate and hand off

- `validate_zotero_docx.py out.docx --baseline in.docx [--preserve-baseline-citations] --expected-increase N --require-item-data --expect-bibliography --json`
- Optional, if Word exists and the user agrees: `word_render.py out.docx --pdf out.pdf`, then look at the PDF pages. Rendering ≠ Zotero Refresh.
- Tell the user: open the output in Microsoft Word with the Zotero add-in (**not WPS** — on machines where WPS owns `.docx`, use right-click → Open with → Word) → Zotero tab → **Refresh**; then check style, numbering and bibliography. If Refresh reports modified/missing items, stop and report the field.

## Hard rules

- Never overwrite the input DOCX unless the user explicitly asks; never open/re-save a Zotero DOCX in WPS/Pages/LibreOffice (WPS is not supported at all).
- Never import, edit, move, merge or delete Zotero items without explicit approval of the exact count and target.
- Cite parent items only (never attachment/note keys); use the URI of the item's own library; never mix a key with another library's URI prefix.
- Never present plain `[1]` text, author–year text or ordinary Word fields as Zotero citations; never synthesize `formattedCitation`/`plainCitation`.
- Never change the scientific meaning of the user's text to fit a citation. Do not run Zotero Refresh automatically, especially on shared documents.
- Troubleshooting: [references/troubleshooting.md](references/troubleshooting.md). Local API routes: [references/zotero-local-api.md](references/zotero-local-api.md).

## Final report (always)

```text
Input document / Output document (absolute paths) + SHA-256 of both; input unchanged: yes/no
References: total N | matched N | missing N | ambiguous N | suspected duplicates N | imported N
Zotero fields inserted N | citation item occurrences N | unique items N | embedded itemData N/N
Library namespaces … | Bibliography field yes/no | Style …
Structural validation passed/failed | Word rendering passed/not run/failed | Zotero Refresh: left to user / passed / failed
```
