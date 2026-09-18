# Troubleshooting

[简体中文](../zh-CN/troubleshooting.md) · [Back to README](../../README.md)

Each table lists **symptom → cause → fix**. Start with the self-test. It usually points straight at the problem:

```bash
python "$S/selftest.py"
```

`$S` is the skill's `scripts/` folder (see [usage.md § Conventions](usage.md#3-conventions-used-below)).

## Contents

- [Python](#python)
- [Zotero connection](#zotero-connection)
- [Matching references](#matching-references)
- [Importing](#importing)
- [Literature search and network](#literature-search-and-network)
- [Inserting fields](#inserting-fields)
- [Validation and Word rendering](#validation-and-word-rendering)
- [Zotero Refresh in Word](#zotero-refresh-in-word)
- [Windows encoding and Chinese paths](#windows-encoding-and-chinese-paths)
- [Installation](#installation)
- [Still stuck?](#still-stuck)

---

## Python

| Symptom | Cause | Fix |
|---|---|---|
| `Python was not found; run without arguments to install from the Microsoft Store…` | Windows **Microsoft Store alias stub**, not a real Python | Install Python 3.9+ from python.org and use `py -3`, or disable the alias: Settings → Apps → Advanced app settings → **App execution aliases** → off for `python.exe`/`python3.exe`. Codex users can use the bundled Python (see [installation.md](installation.md#python-discovery)). |
| `SyntaxError` or `TypeError` mentioning `list[str]` / `str \| None` | Python older than 3.9 | Install Python ≥ 3.9 and make sure that is the one being called (`python --version`). |
| `ModuleNotFoundError: _common` | Script copied out of its folder | Run scripts from the installed `scripts/` folder. They import each other. |
| The agent says it cannot find Python | None of `python3`, `python`, `py -3` works | Install Python yourself. The skill never installs anything. |

## Zotero connection

| Symptom | Cause | Fix |
|---|---|---|
| `selftest`: `[NO ] zotero-running … not reachable at http://127.0.0.1:23119` | Zotero Desktop not running | Start Zotero and keep it open. |
| Still not reachable while Zotero runs | Firewall, VPN or proxy tool blocking `127.0.0.1:23119`; Zotero configured on another port | Allow local connections for Zotero; exclude `127.0.0.1` from proxies; if you changed the port, set `ZOTERO_LOCAL_BASE_URL` or pass `--base-url`. |
| `zotero-running` OK but `zotero-local-api` NO; `status` shows `connectorReachable: true`, `apiReachable: false` (often HTTP **403**) | Local API disabled | Zotero → **Settings → Advanced → Miscellaneous** → tick **"Allow other applications on this computer to communicate with Zotero"** (设置 → 高级 → 杂项 → 允许此计算机上的其他应用程序与 Zotero 通讯). Restart Zotero if it still fails. |
| `/api/` returns 404 | Zotero 6 or older | Upgrade to Zotero 7+. |
| `zotero-read-items` NO while the API is up | Library still loading, or database locked | Wait for Zotero to finish starting; close dialogs; retry. |
| `ERROR: Zotero not reachable: …` from `resolve_references.py` (exit 2) | Zotero closed during a run | Start Zotero and re-run. The step is read-only and safe to repeat. |

## Matching references

| Symptom | Cause | Fix |
|---|---|---|
| `cannot verify library namespace for item … local-only/unsynced` | Your personal library has never been synced, so it has no numeric user ID for the URI | Sync once with a zotero.org account (Zotero → Settings → Sync), then resolve again. Or cite from a group library. |
| A DOI you know is in Zotero comes back `missing` | DOI stored only in *Extra*/URL in a different form, or the item is in a **group** library | Put the DOI in the item's DOI field; for groups use `--library group:<id>` (`zotero_local.py groups` lists IDs). Or pin the item: add `"zoteroKey": "KEY"` to the record. |
| A reference is `ambiguous` with *"N library items share this DOI"* | Duplicate items in your library | Choose one and pin it with `"zoteroKey"`. Merge the duplicates in Zotero (*Duplicate Items*) if you like. The skill never merges. |
| `ambiguous` with *"several plausible title matches"* | Similar titles, no DOI/PMID | Pin the correct item with `"zoteroKey"`, or add the DOI to the record. |
| `missing` with *"no candidate passed the title/author/year threshold"* plus `nearest` | Title differs too much, or year conflict | Check `nearest`; if one is right, pin it. Otherwise the item really is missing, so import it. |
| `pinned key … is not a citable parent item` | Key of an attachment or note | Use the parent item's key. |
| Plain-text reference list resolves poorly | Titles are guessed from formatted strings | Prefer JSON from `search_literature.py`/`lookup`, or RIS. Include DOIs where possible. |

## Importing

| Symptom | Cause | Fix |
|---|---|---|
| `Refusing to write: this would import N record(s) into '…'` (exit 2) | `--yes` missing. This is intentional. | The agent must get your explicit approval first. Then it re-runs with `--yes`. |
| `selected Zotero target is 'X', expected 'Y'. Select the right collection in Zotero.` | The selection in the Zotero window differs from the approved target | Click the intended collection in Zotero and approve again. |
| `selected Zotero target '…' is not editable` | Read-only group/collection selected | Select a collection you can edit. |
| Imported items landed in the wrong collection | Another collection was selected at import time, perhaps without `--expect-target` | In Zotero, click tag `zwlc-import`, select the items, and drag them to the right collection (or remove them from the wrong one). Next time select the collection first. See [manual-steps.md § T4](manual-steps.md#t4-before-any-import-select-the-target-collection-then-approve). |
| Newly imported items still `missing` after re-resolving | Zotero still indexing | Wait a few seconds and resolve again. Check that the target was editable and the import reported records. |
| Import created duplicates of existing items | The item was already present but not matched (e.g. no DOI) | The skill reports duplicates and never deletes. Merge them in Zotero via *Duplicate Items*. |
| `no RIS records found in …` | Empty or non-RIS file | Rebuild with `build_import_file.py`. |
| `build_import_file.py`: `SKIPPED … no structured title` | Record has no title (e.g. from a plain-text list) | Look it up first: `search_literature.py lookup --doi …`. |
| After a second import, `resolve_references.py` reports the same references as `ambiguous` (*"N library items share this DOI"*) or lists them under `duplicates` | `import-ris` was run twice for the same RIS file. The connector does not deduplicate, so every run creates new copies. | See the warning below. |
| Want to undo an import | | Tag selector → `zwlc-import` → select → Move to Trash. See [manual-steps.md § A4](manual-steps.md#a4-undo-an-import-if-needed). |

> [!WARNING]
> **Importing the same RIS twice creates duplicate items.** The Zotero connector does not deduplicate. Every `import-ris` run adds a full new set of copies, and `resolve_references.py` then reports those references as `ambiguous` / `duplicates`.
>
> **To fix it, in Zotero:**
> 1. Click the tag **`zwlc-import`** in the tag selector and sort the list by **Date Added**.
> 2. Find out which copies are already cited in your document. Their keys are in `report.json` (`placements[].keys`) and in `reference-map.json` (`resolved.<refId>.key`). **Keep those copies.**
> 3. Delete the extra copies (Move Item to Trash), or merge them via **Duplicate Items** (重复条目), keeping the cited copy as the master item.
> 4. Run `resolve_references.py` again and check that the references resolve cleanly.
>
> **To prevent it:** always re-run `resolve_references.py` after an import, and before any new import. Never re-import the same file "to be sure". Only references that are still `missing` should go into a new RIS file.

## Literature search and network

| Symptom | Cause | Fix |
|---|---|---|
| `WARNING: openalex failed: …` but results still written | One source failed; the others still returned | Nothing to do, or retry later. |
| Exit 1, every source failed | No internet, proxy, firewall, or all APIs down | Check the connection or proxy settings (the scripts use the system/`HTTPS_PROXY` settings honoured by Python's `urllib`). |
| HTTP **429** / rate limits | Too many requests | The script retries once after 2 s. Set `ZWLC_MAILTO` (Crossref/OpenAlex polite pool) and `NCBI_API_KEY` (PubMed); slow down; reduce `--limit`. |
| Few or irrelevant results | Query too long or too specific | Use 3–7 concept words in English; try `--source crossref`; use `--from-year` for recent topics. |
| `lookup` fails for a DOI | DOI wrong or not registered with Crossref | Don't use that reference. Search by title instead. |

Network access is only needed for literature search. Matching, importing, inserting and validating are local.

## Inserting fields

| Symptom | Cause | Fix |
|---|---|---|
| `refId X is not resolved in --items map (missing/ambiguous refs cannot be cited)` | Marker points to an unresolved reference | Import or pin it, re-resolve, then insert. Nothing was written. |
| `DOI … is not resolved in --items map` | `[@doi:…]` marker for a DOI not in `resolved` | Add the reference to `refs.json` and resolve it. |
| `bad placeholder token` | Typo in a marker | Use `[@ref:ID]`, `[@zotero:KEY]`, `[@key:KEY]`, `[@doi:10.x/y]`, separated by `;`. |
| `output exists: … (use --force to replace it)` | Earlier output still there. | Delete or rename the old output, or add `--force`. Close it in Word first. |
| `output must differ from input` | `--output` equals `--input` | Choose another name. The original is never overwritten. |
| `anchor not found` | Text differs (hyphen vs dash, non-breaking space, tracked changes), or anchor spans an existing field | Check `--list-paragraphs`; copy the exact text; accept or reject tracked changes first; shorten the anchor. |
| `anchor matches N places` | Anchor not unique | Add `occurrence`, `paragraph` or `paragraphContains`. |
| `two citations target the same location` | Two placements at the same point | Merge them into one placement with several `refs`. |
| `footnote/endnote citations are not supported yet` | `noteIndex` ≠ 0 | This version inserts in-text citations only. |
| `input DOCX fails validation; fix it first` | The input is already broken (e.g. damaged field) | Validate it with `validate_zotero_docx.py --json`; go back to a good copy. |
| Citation appears inside a text box in the wrong place, or not at all | Paragraphs containing text boxes are skipped as containers | Put the anchor in the text box's inner paragraph. |
| Bibliography added at the end instead of under your heading | Heading text not exactly equal to `--bibliography-heading` | Match the heading text exactly (e.g. `参考文献` vs `参考文献：`). |
| Existing bibliography not replaced | By design: an existing `ZOTERO_BIBL` is kept | Nothing to do. Refresh updates it. |
| Style in the document isn't the one you passed | The document already had Zotero prefs, which are kept | Change the style in Word via Zotero → Document Preferences. |

## Validation and Word rendering

| Symptom | Cause | Fix |
|---|---|---|
| `expected Zotero field count to increase by N, observed M` | Wrong `N` (it counts **fields**, not items), or insertion failed | Use `fieldsInserted` from `report.json`. |
| `N citation item(s) lack embedded itemData` | Citations from another tool or old document | Only fatal with `--require-item-data`. Such citations need the item in the reader's library. |
| `expected document style gb-t-7714-numeric, found …` | `--expect-style` needs the style ID's last segment, not the alias | Use `--expect-style china-national-standard-gb-t-7714-2015-numeric`. |
| `mixedLibraryNamespaces: true` in `--json` | Citations from several libraries | Fine in collaborative documents; just be aware. |
| `word_render.py`: `Microsoft Word (Windows) not available; visual check skipped` (exit 2) | macOS/Linux, or Word found neither in the standard `Program Files\Microsoft Office\…\Office16/15` folders nor via the registry key `App Paths\Winword.exe` (HKLM/HKCU) | Expected off Windows. On Windows, check that Word is installed and starts normally. A repair of Office restores its registry entries. Rendering is optional. |
| `word_render.py`: `Word did not finish within 180s` | Word stuck on a dialog (activation, safe mode, add-in prompt) or huge document | Open Word once manually and clear its dialogs; retry with `--timeout 600`. |
| `word_render.py` `ok: false` with a COM error | Word busy or a hidden Word process hanging | Close all Word windows (and stray `WINWORD.EXE` in Task Manager), retry. |

## Zotero Refresh in Word

| Symptom | Cause | Fix |
|---|---|---|
| No **Zotero** tab in Word | Add-in not installed or disabled | Zotero → Settings → Cite → Word Processors → **(Re)install Microsoft Word Add-in**; restart Word. On Windows, also check Word → File → Options → Add-ins → *COM/Templates* for a disabled Zotero add-in. |
| Word shows `{ ADDIN ZOTERO_ITEM CSL_CITATION {...} }` | Field-code view is on | Press **Alt+F9** (macOS **Option+F9**). |
| Refresh: *"You have modified this citation…"* | Someone edited a field's visible text | Choose **No** to keep Zotero's version, or undo the edit. If there are many, stop and report. |
| Refresh: item *"not found in your library"* | Citation from another library (e.g. co-author's) | Embedded `itemData` keeps it working. Don't relink unless you mean to. |
| Refresh runs but the style is not the expected one | Style not installed in Zotero | Zotero → Settings → Cite → Styles → install it, then Word → Zotero → **Document Preferences** → choose it. |
| Refresh asks you to choose a style | Prefs missing or unreadable | Pick the style in the dialog. |
| Numbers look odd before Refresh | Visible text is provisional | Run Refresh. |
| Citations became plain text after someone edited the file | Document opened and saved in WPS/Pages/LibreOffice/an online converter | Go back to the last good copy; use Microsoft Word only. |
| Refresh very slow | Large document, many citations | Be patient. In Document Preferences keep "Fields" as the storage format. |

## Windows encoding and Chinese paths

| Symptom | Cause | Fix |
|---|---|---|
| Chinese text appears garbled in the console | Legacy GBK (code page 936) console | The scripts write UTF-8. Use Windows Terminal, or run `chcp 65001` first, or in PowerShell `[Console]::OutputEncoding = [Text.Encoding]::UTF8`. Files on disk are always UTF-8 and correct. |
| JSON written with `>` can't be read back (`UnicodeDecodeError`, `JSONDecodeError`) | Windows PowerShell 5.1 `>` writes UTF-16 | Use the scripts' own `--out` / `--report` options instead of redirection. |
| `UnicodeDecodeError` reading your `refs.json`/`.md`/`.ris` | File saved as ANSI/GBK | Re-save as UTF-8 (with or without BOM both work). |
| Paths with spaces or Chinese characters fail | Unquoted paths | Quote them: `"D:\论文\综述 草稿.docx"`. |

## Installation

| Symptom | Cause | Fix |
|---|---|---|
| `install.py`: `existing installation differs … re-run with --force` (exit 1) | An older or modified copy is installed | Review the listed files, then `--force`. |
| `refusing to remove …: no SKILL.md` | `--uninstall` target isn't a skill folder | Safety check. Remove manually if you're sure. |
| Agent doesn't know the skill | Session started before installing, or wrong folder | Start a **new** session; check `SKILL.md` is at `~/.claude/skills/zotero-word-live-citations/SKILL.md` (or the Codex path). |
| Codex doesn't see it | `CODEX_HOME` points elsewhere | Install with `CODEX_HOME` set the same way Codex runs, or copy to `$CODEX_HOME/skills`. |

## Still stuck?

Open an issue at `https://github.com/<owner>/zotero-word-live-citations/issues` with:

- OS, Python, Zotero and Word versions
- `selftest.py --json` output (it contains no library contents)
- the exact command and error message
- for DOCX problems: `validate_zotero_docx.py file.docx --json`. **Do not attach confidential manuscripts.**
