# Usage guide

[简体中文](../zh-CN/usage.md) · [Back to README](../../README.md)

This guide walks through the whole workflow, script by script: what each step does, which flags matter, what it writes, and what you have to check yourself. You normally never type these commands, because the agent runs them for you. It still helps to know them. You can then review what the agent did, re-run a step by hand, or use the scripts without an agent at all.

## Contents

- [1. The big picture](#1-the-big-picture)
- [2. Talking to the agent](#2-talking-to-the-agent)
- [3. Conventions used below](#3-conventions-used-below)
- [4. Step 0: check the environment (`selftest.py`)](#4-step-0-check-the-environment-selftestpy)
- [5. Step 1: find papers (`search_literature.py`)](#5-step-1-find-papers-search_literaturepy)
- [6. Step 2: resolve against Zotero (`resolve_references.py`)](#6-step-2-resolve-against-zotero-resolve_referencespy)
- [7. Step 3: import missing items (`build_import_file.py`, `zotero_local.py`)](#7-step-3-import-missing-items-build_import_filepy-zotero_localpy)
- [8. Step 4: prepare the DOCX (`md_to_docx.py`)](#8-step-4-prepare-the-docx-md_to_docxpy)
- [9. Step 5: insert live fields (`insert_zotero_fields.py`)](#9-step-5-insert-live-fields-insert_zotero_fieldspy)
- [10. Step 6: validate (`validate_zotero_docx.py`)](#10-step-6-validate-validate_zotero_docxpy)
- [11. Step 7: render with Word (`word_render.py`, Windows only)](#11-step-7-render-with-word-word_renderpy-windows-only)
- [12. Step 8: you run Zotero Refresh in Word](#12-step-8-you-run-zotero-refresh-in-word)
- [13. Citation styles and locales](#13-citation-styles-and-locales)
- [14. The final report](#14-the-final-report)
- [15. Exit codes](#15-exit-codes)
- [16. Worked example: a Chinese tumour-immunology review](#16-worked-example-a-chinese-tumour-immunology-review)
- [17. Other scenarios](#17-other-scenarios)

---

## 1. The big picture

```text
literature search ─► Zotero item (key + URI + CSL itemData) ─► DOCX Zotero field ─► you click Refresh in Word
```

| # | Step | Script | Writes to Zotero? | Who acts |
|---|---|---|---|---|
| 0 | Environment check | `selftest.py` | no | agent |
| 1 | Find papers | `search_literature.py` | no | agent. **You review the claim → paper list.** |
| 2 | Match to your library | `resolve_references.py` | no | agent. **You resolve ambiguous matches.** |
| 3 | Import missing items | `build_import_file.py`, `zotero_local.py import-ris` | **yes** | **You select the collection and say "yes".** |
| 4 | Markdown → DOCX (optional) | `md_to_docx.py` | no | agent |
| 5 | Insert live fields into a copy | `insert_zotero_fields.py` | no | agent |
| 6 | Structural validation | `validate_zotero_docx.py` | no | agent |
| 7 | PDF rendering (optional) | `word_render.py` | no | agent (Windows + Word only) |
| 8 | Zotero Refresh | none | no | **You, in Microsoft Word** |

> [!IMPORTANT]
> Steps 1–3 and 8 involve decisions only you can make. The agent stops and asks you at step 3, and it never runs step 8. See [manual-steps.md](manual-steps.md) for the full checklist.

## 2. Talking to the agent

Plain language is enough. Some prompts that work well:

- *"Write a 1,500-word review on X in Markdown with `[@ref:ID]` markers, find supporting literature for every claim, and give me a Word file with live Zotero citations in GB/T 7714 numeric style (zh-CN)."*
- *"Find supporting literature for each claim in `draft.md` and give me a Word file with live Zotero citations in Vancouver style."*
- *"Add Zotero citations for the references in `refs.ris` to `manuscript.docx` at the marked places."*
- *"My co-author sent `chapter3.docx`. Insert citations for these five DOIs after the sentences I list below. Don't change any text."*
- *"Check whether `thesis.docx` contains valid Zotero citation fields."*

In **Codex** you can name the skill explicitly with `$zotero-word-live-citations`. In **Claude Code** the skill is picked up automatically when your request matches its description. You can also ask for it by name.

What the agent will do on its own, and what it will ask you:

| The agent does by itself | The agent asks you first |
|---|---|
| search, read abstracts, propose a claim → paper list | whether the chosen papers are acceptable (you should review them) |
| resolve references against your library (read-only) | which candidate to use when a match is ambiguous |
| build the RIS file | **whether to import N records into collection X** (it waits for an explicit "yes") |
| write the output copy, validate it, render a PDF | whether to render with Word (optional) |
| write the final report | nothing. **Refresh is always left to you.** |

## 3. Conventions used below

- `S` is the `scripts/` folder of the installed skill, for example `~/.claude/skills/zotero-word-live-citations/scripts`, or `skills/zotero-word-live-citations/scripts` in a clone of this repository.
- Use `python` in the examples. Substitute `python3` or `py -3` if that is what works on your machine. See [installation.md § Python](installation.md#python-discovery).
- Keep work files (candidates, maps, reports) in a work folder next to your document, e.g. `zotero-work/`. Never put them inside the skill folder.
- Every script has `--help`.

bash / zsh:

```bash
S=~/.claude/skills/zotero-word-live-citations/scripts
```

```bash
python "$S/selftest.py"
```

Windows PowerShell:

```powershell
$S = "$HOME\.claude\skills\zotero-word-live-citations\scripts"
```

```powershell
python "$S\selftest.py"
```

Quote paths. Spaces and Chinese characters in paths are fine.

## 4. Step 0: check the environment (`selftest.py`)

```bash
python "$S/selftest.py"
```

Example output:

```text
[OK ] python: 3.12.4 at C:\...\python.exe
[OK ] zotero-running: Zotero 10.0.2
[OK ] zotero-local-api: local API enabled
[OK ] zotero-read-items: read one item key
[OK ] docx-pipeline: insert + validate OK
[OK ] microsoft-word: C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE
capabilities: literatureSearch=yes, zoteroSearchResolve=yes, zoteroImport=yes, docxInsertValidate=yes, markdownToDocx=yes, wordRendering=yes
```

| Flag | Meaning |
|---|---|
| `--json` | machine-readable output (`checks` + `capabilities`) |
| `--strict` | exit 1 unless Zotero items are readable **and** the offline DOCX pipeline passes |
| `--base-url URL` | Zotero local server (default `http://127.0.0.1:23119` or `$ZOTERO_LOCAL_BASE_URL`) |

The self-test is read-only. It installs nothing, changes no Zotero setting and prints no library contents. The offline pipeline check builds a throwaway DOCX in a temporary folder.

What a missing capability means:

| Check fails | You lose | You keep |
|---|---|---|
| `zotero-running` / `zotero-local-api` / `zotero-read-items` | resolving and importing | literature search, DOCX validation, Markdown → DOCX |
| `microsoft-word` | PDF rendering only | everything else, and the fields still work |
| `docx-pipeline` | insertion | investigate before continuing (usually a broken Python install) |

## 5. Step 1: find papers (`search_literature.py`)

Two subcommands. Both are read-only and use only public APIs.

### `search`: keyword search

```bash
python "$S/search_literature.py" search "cancer immunoediting elimination equilibrium escape" --source openalex,pubmed --limit 8 --out zotero-work/q1.json
```

| Flag | Default | Meaning |
|---|---|---|
| `query` (positional) | | 3–7 content words; English terms work best in international databases |
| `--source` | `openalex,pubmed` | comma list of `openalex`, `pubmed`, `crossref` |
| `--limit` | `10` | results **per source** |
| `--from-year` | | only works published in or after this year |
| `--out` | stdout | write JSON here |
| `--brief` | off | omit abstracts (smaller files) |
| `--mailto` (global, before the subcommand) | `$ZWLC_MAILTO` | contact e-mail sent to Crossref/OpenAlex ("polite pool") |
| `--timeout` (global) | `20` | seconds per HTTP request |

| Source | Best for |
|---|---|
| `openalex` | broad coverage, abstracts, citation counts |
| `pubmed` | biomedicine, PMIDs, high-quality metadata. `$NCBI_API_KEY` raises rate limits. |
| `crossref` | DOI registry, all disciplines, canonical metadata |

Records from several sources are merged by DOI/PMID and numbered `C1`, `C2`, … within each output file. If one source fails, you get a warning and the others still return results. The exit code is 1 only if every source failed and nothing was found.

Output record (shared by the resolve and build scripts):

```json
{"refId": "C1", "title": "...", "authors": [{"family": "Dunn", "given": "Gavin P."}],
 "year": "2004", "journal": "Annual Review of Immunology", "volume": "22", "issue": "1",
 "pages": "329-360", "doi": "10.1146/annurev.immunol.22.012703.104803", "pmid": "15032581",
 "abstract": "...", "url": "...", "type": "article-journal", "sources": ["openalex", "pubmed"]}
```

### `lookup`: canonical metadata for known identifiers

```bash
python "$S/search_literature.py" lookup --doi 10.1056/NEJMoa1003466 --pmid 15032581 --out zotero-work/lookup.json
```

`--doi` and `--pmid` can be repeated. Use `lookup` for any DOI that came from memory, a colleague or another tool. **If lookup fails, the reference is not used.**

> [!WARNING]
> **You are responsible for the scientific choice of papers.** The agent is not allowed to cite a paper that no tool returned, and it must not invent DOIs. Whether a paper actually supports your claim is still your judgement. Read the claim → paper list the agent shows you before anything is imported or inserted.

### Combining several searches into one `refs.json`

Each search file numbers its candidates from `C1`, so IDs collide between files. When you, or the agent, pick papers from several searches, copy each chosen record into one JSON list and give it a unique `refId`. The simplest choice is the marker ID used in the manuscript, e.g. `"refId": "editing"` for `[@ref:editing]`. Leave the rest of the record unchanged.

```json
[
  {"refId": "editing", "title": "The Three Es of Cancer Immunoediting", "doi": "10.1146/annurev.immunol.22.012703.104803", "...": "..."},
  {"refId": "ipi", "title": "Improved Survival with Ipilimumab in Patients with Metastatic Melanoma", "doi": "10.1056/NEJMoa1003466", "...": "..."}
]
```

## 6. Step 2: resolve against Zotero (`resolve_references.py`)

```bash
python "$S/resolve_references.py" --references zotero-work/refs.json --out zotero-work/reference-map.json
```

| Flag | Meaning |
|---|---|
| `--references` | input: `.json` (list of records or `{"references": [...]}`), `.ris`, or `.txt`/`.md` (one formatted reference per line; `1.`, `[1]`, `1)` numbering is recognised) |
| `--out` | reference map to write (required) |
| `--library` | `user` (default) or `group:<id>` (see `zotero_local.py groups`) |
| `--base-url` | Zotero local server |

Matching order, strongest first:

1. **pinned key**: a `"zoteroKey": "ABCD1234"` field in the input record (JSON input only)
2. **DOI** exact match
3. **PMID** exact match (read from the item's *Extra* field, e.g. `PMID: 12345678`)
4. **exact normalised title**
5. **fuzzy title** + first author + year (a year conflict blocks a fuzzy match)

Attachments, notes and annotations are never matched. Only top-level parent items are.

> [!IMPORTANT]
> **Ambiguous matches are never auto-picked.** Examples are two library items that share a DOI, several items with the same title, or two fuzzy candidates with close scores. They land in `ambiguous` and the agent shows you the candidates. To choose one, add `"zoteroKey"` to that record in your input JSON and run the script again:
>
> ```json
> {"refId": "ipi", "title": "...", "doi": "10.1056/NEJMoa1003466", "zoteroKey": "ABCD1234"}
> ```
>
> Suspected duplicates in your library are reported in `duplicates` and never merged or deleted. Merge them yourself in Zotero if you want to (*Duplicate Items* in the left pane).

The script prints a one-line summary to stderr:

```text
references=18 resolved=18 missing=0 ambiguous=0 duplicates=0 -> zotero-work/reference-map.json
```

### `reference-map.json` structure

```jsonc
{
  "generatedAt": "2026-09-18T06:55:00+00:00",
  "zoteroBaseUrl": "http://127.0.0.1:23119",
  "library": "user",
  "totalReferences": 18,
  "resolved": {
    "editing": {
      "key": "ABCD1234",                                   // Zotero item key (parent item)
      "uri": "http://zotero.org/users/<id>/items/ABCD1234", // built from the item's own library
      "itemData": { "id": "...", "type": "article-journal", "title": "..." }, // Zotero's CSL-JSON
      "title": "The Three Es of Cancer Immunoediting",
      "year": "2004",
      "doi": "10.1146/annurev.immunol.22.012703.104803",
      "matchMethod": "doi",                                // manual | doi | pmid | title | title-fuzzy
      "score": 1.0
    }
  },
  "missing":   [ {"refId": "...", "title": "...", "doi": "...", "reason": "...", "nearest": [ ... ]} ],
  "ambiguous": [ {"refId": "...", "title": "...", "reason": "...", "candidates": [
                   {"key": "...", "title": "...", "year": "...", "firstAuthor": "...",
                    "similarity": 0.93, "score": 0.98, "yearMatch": true, "authorMatch": true, "accept": true} ]} ],
  "duplicates": [ {"refId": "...", "keys": ["KEY1", "KEY2"]} ],
  "libraryNamespaces": ["users/<id>"],
  "references": [ /* your input records, normalised */ ]
}
```

Exit code: 0 when every reference resolved, 1 when some are missing or ambiguous (the map is still written), 2 on bad input or if Zotero is unreachable.

## 7. Step 3: import missing items (`build_import_file.py`, `zotero_local.py`)

This is the **only step that writes to Zotero**, and it needs your explicit approval every time.

### 7.1 Build the import file (no write)

```bash
python "$S/build_import_file.py" --map zotero-work/reference-map.json --format ris --out zotero-work/missing.ris --tag zwlc-import
```

| Flag | Meaning |
|---|---|
| `--map` | the reference map (required) |
| `--format` | `ris` (default) or `bibtex` |
| `--out` | file to write (required) |
| `--ref-id` | export only these refIds (repeatable). By default, everything under `missing` is exported. |
| `--tag` | add a Zotero tag to every record (repeatable). **Use `zwlc-import`** so you can find, review or undo the import later. |

Records without a title are skipped and reported. Nothing is invented. Open the `.ris` file and look at it if you like. It is plain text.

### 7.2 See where the import would land

```bash
python "$S/zotero_local.py" selected-target
```

```json
{
  "libraryID": 1,
  "libraryName": "My Library",
  "libraryEditable": true,
  "id": 168,
  "name": "肿瘤免疫测试"
}
```

> [!CAUTION]
> **The Zotero connector imports into whatever library/collection is currently selected in the Zotero window.** There is no "collection" parameter. **Before approving, click the collection you want in Zotero's left pane**, e.g. a dedicated test collection. If the root library is selected, `name` is the library name (e.g. *My Library* / *我的文库*).

The agent then tells you something like *"18 records → collection 肿瘤免疫测试 in library My Library. Import?"* and **waits for an explicit yes**. "Add citations" is **not** approval to import.

### 7.3 Import (write)

```bash
python "$S/zotero_local.py" import-ris --file zotero-work/missing.ris --expect-target "肿瘤免疫测试" --yes
```

| Flag | Meaning |
|---|---|
| `--file` | the RIS (or, for `import-bibtex`, BibTeX) file |
| `--expect-target NAME` | refuse (exit 2) if the selected collection/library is not named exactly `NAME`. This protects you if the selection changed after you approved. |
| `--yes` | confirms that you approved this import. Without it the script prints what it *would* do and refuses (exit 2). |

The script also refuses if the selected target is not editable. On success it prints `requestedRecords`, `target`, `session` and `connectorReportedItems`. **That response is not proof of success.** The next step is always to re-resolve.

### 7.4 Re-resolve

```bash
python "$S/resolve_references.py" --references zotero-work/refs.json --out zotero-work/reference-map.json
```

Newly imported items should now resolve, normally by DOI. If an imported item is still `missing`, wait a few seconds, because Zotero may still be indexing, and run the command again. Items that still fail are reported as failures. **No key or URI is ever guessed.**

> [!TIP]
> **Undoing an import:** in Zotero, click the tag `zwlc-import` in the tag selector (bottom-left), select the items, and move them to the trash. The skill itself never deletes anything. See [manual-steps.md § Undo an import](manual-steps.md#a4-undo-an-import-if-needed).

### Other `zotero_local.py` subcommands (read-only)

| Subcommand | Purpose |
|---|---|
| `status` | API and connector reachability, Zotero version, and a hint if something is off. Exit 0 only if items are readable. |
| `search "<text>" [--library user\|group:<id>] [--limit N] [--everything]` | search top-level items. `--everything` also searches full text and notes. |
| `item KEY [--library ...]` | one item's metadata + verified URI + CSL `itemData`. Refuses attachments and notes. |
| `collections` | list collections of your personal library (key, name, parent) |
| `groups` | list group libraries visible locally |
| `selected-target` | the library/collection currently selected in Zotero |
| `import-ris` / `import-bibtex` | the write commands above |

The global `--base-url` goes before the subcommand: `zotero_local.py --base-url http://127.0.0.1:23119 status`.

## 8. Step 4: prepare the DOCX (`md_to_docx.py`)

Skip this if you already have a DOCX. For a manuscript drafted in Markdown:

```bash
python "$S/md_to_docx.py" --input zotero-work/review.md --output zotero-work/review.docx
```

| Flag | Default | Meaning |
|---|---|---|
| `--input` / `--output` | | required |
| `--latin-font` | `Times New Roman` | Latin font |
| `--east-asia-font` | `SimSun` | CJK font (e.g. `SimSun` / 宋体, `Microsoft YaHei`) |
| `--force` | off | overwrite an existing output |

Supported Markdown: `#`–`###` headings (the first `#` becomes the document Title), paragraphs, `-`/`*` bullets, `1.` numbered lines (kept as plain text), `**bold**`, `*italic*`. Tables, images, links and footnotes are **not** converted. Citation markers are kept verbatim for the next step.

### Placeholder syntax

| Marker | Meaning |
|---|---|
| `[@ref:C4]` | a refId from `reference-map.json` |
| `[@ref:C4; @ref:C9]` | **one** field citing two items |
| `[@zotero:ABCD1234]` or `[@key:ABCD1234]` | a Zotero item key (fetched read-only from your personal library if it is not in the map) |
| `[@doi:10.1000/xyz]` | a DOI that is resolved in the map |

Kinds can be mixed inside one marker: `[@ref:A; @zotero:ABCD1234; @doi:10.1000/xyz]`.

Put the marker right after the claim. For numeric styles, place it before the sentence punctuation: `...is required for T-cell priming[@ref:C4].` The marker text is replaced exactly. If you want a space before the citation, type one before the marker. Markers may be split across Word runs, since they are found on the paragraph's visible text.

> [!NOTE]
> An unresolved marker, such as a refId that is `missing` or `ambiguous` in the map, **aborts the whole insertion with exit code 2 (usage error). Nothing is written.** Fix the map first.

## 9. Step 5: insert live fields (`insert_zotero_fields.py`)

```bash
python "$S/insert_zotero_fields.py" --input zotero-work/review.docx --items zotero-work/reference-map.json --placeholders --style vancouver --bibliography-heading "References" --report zotero-work/report.json
```

### Flags

| Flag | Default | Meaning |
|---|---|---|
| `--input` | | source DOCX (required, never modified) |
| `--output` | `<stem>-zotero-cited.docx` next to the input | must differ from the input |
| `--items` | | `reference-map.json` |
| `--placeholders` | | replace `[@...]` markers (mode 1) |
| `--placements FILE` | | anchor-based placements (mode 2, text unchanged) |
| `--style` | `vancouver` | alias or any CSL style URL. See [§13](#13-citation-styles-and-locales). |
| `--locale` | `en-US` | citation locale, e.g. `zh-CN`, `de-DE` |
| `--note-type` | `0` | document preference only: `0` in-text, `1` footnotes, `2` endnotes. (This version inserts in-text fields only.) |
| `--visible` | `auto` | provisional text: `auto`, `numeric`, `author-date` |
| `--bibliography-heading TEXT` | | insert a `ZOTERO_BIBL` field after the paragraph whose text is exactly `TEXT`; the heading is created at the end if absent |
| `--no-bibliography` | | do not insert a bibliography |
| `--zotero-version` | detected from Zotero, else `7.0` | value of the `zotero-version` attribute in the document prefs |
| `--base-url` | | Zotero local server |
| `--list-paragraphs` | | print `{"paragraphs": [{"index", "text"}]}` and exit |
| `--dry-run` | | plan and audit only; write nothing |
| `--force` | | replace an existing **output** file |
| `--report FILE` | | also write the JSON report here |

### What gets written

- One Word complex field per citation location: ` ADDIN ZOTERO_ITEM CSL_CITATION {json} `, with a unique 8-character `citationID`. Several items at one location share one field. The same item cited at two places gets two fields.
- Each citation item carries `id` (the item key), `uris` (the item's own library URI) and `itemData` (Zotero's own CSL-JSON). The citation therefore keeps working for co-authors who do not have the item.
- A `ZOTERO_BIBL` bibliography field, if requested. If the document already has one, it is kept and not duplicated.
- Document preferences `ZOTERO_PREF_1..n` in `docProps/custom.xml` (style, locale, field type). If the document already has Zotero prefs, they are left untouched and the existing style wins.
- **Provisional visible text:** numeric styles get `[1]`, `[2,3]`, `[4–6]` numbered by first appearance. Author–date styles get `(Author, Year)`. The bibliography gets simple provisional entries. **Zotero Refresh replaces all of this** with properly formatted text. `formattedCitation`/`plainCitation` are never synthesized.
- Only `word/document.xml`, `docProps/custom.xml`, `[Content_Types].xml` and `_rels/.rels` change. Every other part of the package is copied byte-for-byte. Text inside existing fields is never split.

After writing, the script validates its own output against the input. If the input already contained Zotero citations, all of them must survive unchanged.

### `report.json`

| Field | Meaning |
|---|---|
| `inputDocument`, `outputDocument` | absolute paths |
| `inputSHA256`, `outputSHA256` | file hashes |
| `inputUnchanged` | `true` if the input hash is identical after the run |
| `fieldsInserted` | new citation fields |
| `zoteroFieldsTotal` | all citation fields in the output (existing + new) |
| `citationItemOccurrences` | total cited items across fields |
| `uniqueItems` | distinct item URIs |
| `embeddedItemData` | e.g. `18/18` |
| `libraryNamespaces` | e.g. `["users/<id>"]` or `["groups/<id>"]` |
| `bibliography` | `none`, `kept-existing`, `added after heading '…'`, `added at end [with new heading '…']` |
| `documentPreferences` | `added` or `kept-existing` |
| `style` | full CSL style ID written to the prefs |
| `structuralValidation` | `passed` / `failed` |
| `validationErrors`, `validationWarnings` | lists |
| `placements` | per field: `placement`, `paragraph`, `citationID`, `keys`, `visibleText`, `context` |

With `--dry-run` the report is just `{"dryRun": true, "placements": [...], "bibliography": "..."}`.

### Mode 2: `placements.json` (existing manuscript, text must not change)

Use this for a received or finished manuscript where you cannot add markers. Every citation is placed next to an exact **anchor** text.

**1. List paragraphs** (index + visible text):

```bash
python "$S/insert_zotero_fields.py" --input manuscript.docx --list-paragraphs --report zotero-work/paragraphs.json
```

**2. Write `placements.json`:**

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

| Key | Required | Meaning |
|---|---|---|
| `anchor` | yes | text the citation follows (or precedes). Matched on the paragraph's visible text outside existing fields; whitespace and straight/curly quotes match loosely. |
| `refs` / `keys` | at least one | refIds from the map and/or Zotero keys. All go into **one** field. |
| `id` | no | label for the audit (default `P1`, `P2`, …) |
| `paragraph` | no | 0-based paragraph index from `--list-paragraphs` |
| `paragraphContains` | no | only consider paragraphs containing this text |
| `occurrence` | if ambiguous | which match to use (1-based). Required when the anchor matches more than once. |
| `position` | no | `after` (default) or `before` |
| `spaceBefore` | no | insert a space before the field. The default is on for author–date styles and off for numeric. |
| `noteIndex` | no | must be `0`. Footnote citations are not supported yet. |
| `bibliography.heading` | no | same as `--bibliography-heading`. The command-line flag wins. |

Rules: an anchor that matches several places is an **error** unless `occurrence`, `paragraph` or `paragraphContains` makes it unique. Two placements at the same point are rejected, so merge them into one with several refs.

**3. Dry run and read every `context`** (`...text <<CITE>> text...`):

```bash
python "$S/insert_zotero_fields.py" --input manuscript.docx --items zotero-work/reference-map.json --placements zotero-work/placements.json --style apa --dry-run
```

**4. Insert for real** by running the same command without `--dry-run`, adding `--report`.

> [!IMPORTANT]
> When the agent migrates citations from an old draft to a new one, it aligns sentences by similarity. Placements with low similarity (below about 0.8), split or merged sentences, or claims that disappeared are **listed for you to review, not inserted silently**. It never edits your text to make an anchor fit.

## 10. Step 6: validate (`validate_zotero_docx.py`)

```bash
python "$S/validate_zotero_docx.py" zotero-work/review-zotero-cited.docx --baseline zotero-work/review.docx --expected-increase 17 --require-item-data --expect-bibliography
```

The validator is read-only. It checks ZIP integrity and unsafe part names, XML well-formedness, complete `begin/separate/end` fields, citation JSON (`citationID` uniqueness, `noteIndex`, `citationItems`, URIs, schema), key ↔ URI consistency, embedded `itemData` coverage, library namespaces, `ZOTERO_BIBL` fields and document preferences.

| Flag | Meaning |
|---|---|
| `docx` (positional) | file to validate |
| `--baseline FILE` | the original, for comparison |
| `--expected-increase N` | citation-field count must grow by exactly N (needs `--baseline`) |
| `--expected-field-count N` / `--minimum-fields N` | absolute counts |
| `--preserve-baseline-citations` | every baseline `citationID` and its URIs must survive unchanged |
| `--require-item-data` | fail if any citation item lacks embedded `itemData` |
| `--expect-bibliography` | fail without a `ZOTERO_BIBL` field |
| `--expect-style ID` | full style ID, or its last path segment (e.g. `vancouver`, `china-national-standard-gb-t-7714-2015-numeric`) |
| `--expect-citation-id`, `--expect-item-key`, `--expect-visible-text` | repeatable spot checks |
| `--json` | full machine-readable result |

> [!NOTE]
> `--expected-increase` counts **citation fields**, not cited items. In the worked example below, 18 items sit in 17 fields because one field cites two items, so the value is 17.

> [!NOTE]
> `--expect-style` compares against the style ID written in the document, not against the short aliases of `insert_zotero_fields.py`. `vancouver`, `apa`, `nature`, `ieee` and `chicago-author-date` happen to equal their ID's last segment. For `gb-t-7714-numeric`, `ama` or `harvard`, pass the full ID or its last segment instead.

To check a document someone sent you, just run `validate_zotero_docx.py their.docx --json`. The result shows existing fields, namespaces and `itemData` coverage.

## 11. Step 7: render with Word (`word_render.py`, Windows only)

```bash
python "$S/word_render.py" zotero-work/review-zotero-cited.docx --pdf zotero-work/review-zotero-cited.pdf
```

| Flag | Default | Meaning |
|---|---|---|
| `docx` (positional) | | document to render |
| `--pdf FILE` | | also export a PDF |
| `--timeout` | `180` | seconds before giving up |

The script copies the DOCX to a temporary folder and opens that copy **read-only** in a hidden Word instance via PowerShell COM. It counts the fields Word itself parses (`fields`, `zoteroItemFields`, `zoteroBibliographyFields`) and the `pages`, optionally exports a PDF, and closes without saving. Output is always JSON.

> [!NOTE]
> Rendering proves that Word opens the file and sees the fields. **It does not run Zotero Refresh and is not proof that Refresh will succeed.** On macOS and Linux this step is skipped (exit 2, "not available"). That is expected, not an error in your document.

## 12. Step 8: you run Zotero Refresh in Word

> [!IMPORTANT]
> **This step is always manual.**
> 1. Open `<stem>-zotero-cited.docx` in **Microsoft Word** (not WPS, LibreOffice or Pages).
> 2. Go to the **Zotero** tab → **Refresh** (Chinese UI: **Zotero → 刷新**).
> 3. Check the citation style, the numbering and the bibliography.
>
> Before Refresh, the visible text is **provisional**. After Refresh, Zotero owns the formatting.

To change the style later, use **Zotero → Document Preferences** (文档首选项) in Word. Details, dialogs and what to do if Refresh complains: [manual-steps.md § After the output](manual-steps.md#after-the-output-is-generated) and [troubleshooting.md](troubleshooting.md#zotero-refresh-in-word).

## 13. Citation styles and locales

`--style` accepts these aliases:

| Alias | CSL style ID | Visible provisional text |
|---|---|---|
| `vancouver` (default) | `http://www.zotero.org/styles/vancouver` | numeric |
| `apa` | `http://www.zotero.org/styles/apa` | author–date |
| `nature` | `http://www.zotero.org/styles/nature` | numeric |
| `ieee` | `http://www.zotero.org/styles/ieee` | numeric |
| `ama` | `http://www.zotero.org/styles/american-medical-association` | numeric |
| `chicago-author-date` | `http://www.zotero.org/styles/chicago-author-date` | author–date |
| `harvard` | `http://www.zotero.org/styles/harvard-cite-them-right` | author–date |
| `gb-t-7714-numeric` | `http://www.zotero.org/styles/china-national-standard-gb-t-7714-2015-numeric` | numeric |
| `gb-t-7714-author-date` | `http://www.zotero.org/styles/china-national-standard-gb-t-7714-2015-author-date` | author–date |

**Any other CSL style works too.** Pass its full ID, e.g. `--style http://www.zotero.org/styles/cell`. The provisional format is guessed from the ID (IDs containing `apa`, `author-date`, `harvard` or `chicago-author` count as author–date). Override it with `--visible numeric|author-date`.

> [!IMPORTANT]
> The style must be **installed in your Zotero** for Refresh to apply it. Install it under Zotero → Settings → Cite → Styles (设置 → 引用 → 样式), using the "+" button or "Get additional styles…". This matters especially for GB/T 7714 and journal-specific styles.

`--locale` sets the citation language, e.g. `en-US` (default), `en-GB`, `zh-CN`, `de-DE`. For Chinese GB/T output use `--style gb-t-7714-numeric --locale zh-CN --bibliography-heading "参考文献"`.

## 14. The final report

At the end of every task the agent gives you a report in this shape. The three verification results are kept separate on purpose:

```text
Input document / Output document (absolute paths) + SHA-256 of both; input unchanged: yes/no
References: total N | matched N | missing N | ambiguous N | suspected duplicates N | imported N
Zotero fields inserted N | citation item occurrences N | unique items N | embedded itemData N/N
Library namespaces … | Bibliography field yes/no | Style …
Structural validation passed/failed | Word rendering passed/not run/failed | Zotero Refresh: left to user / passed / failed
```

"Zotero Refresh: left to user" is the normal state when the agent finishes. Only you can change it to passed, by running Refresh in Word.

## 15. Exit codes

The convention for all scripts: **0** success · **1** validation failure, or unresolved references in `resolve_references.py` (the map is still written) · **2** usage or environment error, including a `[@…]` marker in `insert_zotero_fields.py` that names an unknown or unresolved reference (nothing is written).

| Script | 0 | 1 | 2 |
|---|---|---|---|
| `selftest.py` | Python + DOCX pipeline OK (with `--strict`: also Zotero readable) | an essential check failed | bad arguments |
| `search_literature.py` | results written | every source failed / lookup failed | bad arguments / unexpected error |
| `resolve_references.py` | everything resolved | some missing or ambiguous (map written) | bad input, Zotero unreachable |
| `build_import_file.py` | file written (or nothing to export) | some records skipped / none exportable | map unreadable |
| `zotero_local.py` | success | connection error, import failed, `status` not OK | refused (no `--yes`, `--expect-target` mismatch, target not editable, empty file) |
| `md_to_docx.py` | written | | input missing, output exists |
| `insert_zotero_fields.py` | written and structurally valid | written, but validation failed | refused (unresolved marker, ambiguous anchor, output exists, input invalid …). Nothing written. |
| `validate_zotero_docx.py` | valid | invalid | bad arguments |
| `word_render.py` | rendered | Word failed / timeout | Word or PowerShell unavailable (non-Windows) |
| `install.py` | done | existing install differs (needs `--force`), refused uninstall | skill source not found |

## 16. Worked example: a Chinese tumour-immunology review

This is a real end-to-end run, verified on **Windows 11, Zotero 10.0.2, Word 16 (Microsoft 365) with the Zotero Word add-in**.

**Task.** A Chinese review (about 1,575 characters) on tumour immunology, drafted in Markdown with 18 `[@ref:ID]` markers such as `[@ref:editing]`, `[@ref:ipi]` and `[@ref:car]`. One sentence cites two papers: `[@ref:microbiome; @ref:microbiome2]`. Output style: GB/T 7714-2015 numeric, Chinese locale.

**1. Search.** 15 searches, e.g.:

```bash
python "$S/search_literature.py" search "cancer immunoediting three Es" --source openalex,pubmed --limit 4 --out q1.json
```

**2. Choose.** 18 papers were chosen from the results by reading titles and abstracts, among them Dunn 2004 *The Three Es of Cancer Immunoediting* (Annu Rev Immunol), Hodi 2010 ipilimumab in metastatic melanoma (NEJM), Rizvi 2015 mutational landscape and PD-1 blockade in NSCLC (Science), and Maude 2014 CAR T cells in ALL (NEJM). The chosen records were copied into `refs.json` with `refId` = marker ID and abstracts removed.

**3. Resolve.** All 18 were missing from the library:

```bash
python "$S/resolve_references.py" --references refs.json --out reference-map.json
```

**4. Build the RIS** (18 records, tagged `zwlc-import`):

```bash
python "$S/build_import_file.py" --map reference-map.json --format ris --out missing.ris --tag zwlc-import
```

**5. Manual step.** In the Zotero window, the user created a dedicated collection **肿瘤免疫测试** and selected it. The agent checked the selection:

```bash
python "$S/zotero_local.py" selected-target
```

It then asked *"18 records → collection 肿瘤免疫测试 in My Library. Import?"* and the user approved.

**6. Import:**

```bash
python "$S/zotero_local.py" import-ris --file missing.ris --expect-target "肿瘤免疫测试" --yes
```

**7. Re-resolve.** 18/18 matched by DOI:

```bash
python "$S/resolve_references.py" --references refs.json --out reference-map.json
```

**8. Markdown → DOCX:**

```bash
python "$S/md_to_docx.py" --input review.md --output review.docx
```

**9. Insert fields:**

```bash
python "$S/insert_zotero_fields.py" --input review.docx --items reference-map.json --placeholders --style gb-t-7714-numeric --locale zh-CN --bibliography-heading "参考文献" --report report.json
```

Key lines of `report.json`:

```json
{
  "inputUnchanged": true,
  "fieldsInserted": 17,
  "zoteroFieldsTotal": 17,
  "citationItemOccurrences": 18,
  "uniqueItems": 18,
  "embeddedItemData": "18/18",
  "bibliography": "added at end with new heading '参考文献'",
  "documentPreferences": "added",
  "style": "http://www.zotero.org/styles/china-national-standard-gb-t-7714-2015-numeric",
  "structuralValidation": "passed"
}
```

17 fields for 18 items, because the microbiome sentence got one field with provisional text `[11,12]`. The Markdown had no "参考文献" heading, so the heading was created at the end followed by the bibliography field.

**10. Validate:**

```bash
python "$S/validate_zotero_docx.py" review-zotero-cited.docx --baseline review.docx --expected-increase 17 --require-item-data --expect-bibliography
```

Result: passed.

**11. Render.** Word opened the file and exported 4 pages:

```bash
python "$S/word_render.py" review-zotero-cited.docx --pdf review-zotero-cited.pdf
```

**12. Manual step.** The user opened `review-zotero-cited.docx` in Word and clicked **Zotero → Refresh**. **Refresh succeeded.** Zotero replaced the provisional, Vancouver-like bibliography text with GB/T 7714-2015 formatting.

Final report:

```text
References: total 18 | matched 18 | missing 0 | ambiguous 0 | suspected duplicates 0 | imported 18
Zotero fields inserted 17 | citation item occurrences 18 | unique items 18 | embedded itemData 18/18
Library namespaces users/<id> | Bibliography field yes | Style china-national-standard-gb-t-7714-2015-numeric
Structural validation passed | Word rendering passed (4 pages) | Zotero Refresh: passed (run by the user)
```

## 17. Other scenarios

| You have | Steps |
|---|---|
| A DOCX to check | `validate_zotero_docx.py doc.docx --json` |
| Items already in Zotero, markers in the text | resolve (or cite `[@zotero:KEY]` directly) → insert → validate |
| A reference list (`refs.ris`, `refs.txt`) + a DOCX with markers | `resolve_references.py --references refs.ris …` → import missing (with approval) → insert → validate |
| A received manuscript with existing Zotero citations | validate baseline → `--list-paragraphs` → `placements.json` → `--dry-run` → insert. Existing citations are preserved and checked automatically. |
| A group library | `zotero_local.py groups` → `resolve_references.py --library group:<id> …`. See [faq.md](faq.md#can-i-cite-items-from-a-group-library). |

In received or collaborative documents, citations from other people's libraries (other `users/<id>` or `groups/<id>`) are valid and are left as they are. The agent will not run Refresh on someone else's document for you, and it warns about citations that have no embedded `itemData`.
