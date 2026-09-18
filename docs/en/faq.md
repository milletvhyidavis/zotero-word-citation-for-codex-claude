# FAQ

[简体中文](../zh-CN/faq.md) · [Back to README](../../README.en.md)

## Contents

- [General](#general)
- [Zotero](#zotero)
- [Word and documents](#word-and-documents)
- [Literature and scientific responsibility](#literature-and-scientific-responsibility)
- [Privacy and safety](#privacy-and-safety)

---

## General

### What exactly does "live citation" mean?

The document contains real Zotero Word fields: `ADDIN ZOTERO_ITEM CSL_CITATION {...}` for each citation, `ADDIN ZOTERO_BIBL … CSL_BIBLIOGRAPHY` for the bibliography, and `ZOTERO_PREF_n` document preferences. They are the same things the Zotero Word add-in creates when you click *Add/Edit Citation*. After **Zotero → Refresh** you can restyle, edit, renumber and extend them in Word as if you had inserted them by hand. Plain `[1]` text cannot do any of that.

### Is this an official Zotero, Microsoft, Anthropic or OpenAI product?

No. It is an independent open-source project. Zotero is a trademark of the Corporation for Digital Scholarship. See [NOTICE](../../NOTICE).

### Do I need both Claude Code and Codex?

No. Either one. The same skill folder works in both.

### Can I use the scripts without an AI agent?

Yes. Every script is a normal command-line tool with `--help`. See [usage.md](usage.md) and the minimal run in the README.

### Why does it not install anything automatically?

Safety and transparency. It needs only the Python standard library, and it never runs `pip`, installers or setting changes on your machine. You stay in control of what is installed.

### Which operating systems are supported?

The scripts run anywhere Python ≥ 3.9 runs. Zotero Desktop runs on Windows, macOS and Linux. Refresh needs Microsoft Word with the Zotero add-in (Windows or macOS). The optional PDF rendering step (`word_render.py`) is Windows-only.

## Zotero

### Why must Zotero Desktop be running?

Matching and importing use Zotero Desktop's local API and connector at `http://127.0.0.1:23119`. They exist only while Zotero is running and *Allow other applications on this computer to communicate with Zotero* is enabled.

### Will it change or delete things in my library?

It only **adds** items, and only after you approve the exact count and target collection. It never edits, moves, merges or deletes items, and it never changes Zotero settings. To undo an import, filter by the `zwlc-import` tag and delete the items yourself ([manual-steps.md § A4](manual-steps.md#a4-undo-an-import-if-needed)).

### Why did my import go into the wrong collection?

The Zotero connector imports into **whatever collection is selected in the Zotero window**. There is no collection parameter. Select the collection **before** approving. The agent passes `--expect-target` so the import refuses if the selection changes. See [manual-steps.md § T4](manual-steps.md#t4-before-any-import-select-the-target-collection-then-approve).

### Can I cite items from a group library?

Yes. List groups with `zotero_local.py groups`, then resolve with `resolve_references.py --library group:<id> …`. The citations get `groups/<id>` URIs. Limitations: `[@zotero:KEY]` shortcuts for keys *not* in the map only look in your personal library, and one insert run takes one map. See [manual-steps.md § B5](manual-steps.md#b5-sign-in-to-zotero-usually-already-done-fix-only-when-asked).

### My library is local-only (never synced). What happens?

Resolving refuses to build a URI (*"cannot verify library namespace"*), because the local API does not expose a numeric user ID for unsynced libraries and the skill won't invent one. Sync your library once with a free zotero.org account, then resolve again.

### Which Zotero version is required?

Zotero 7 or newer (the local API arrived in 7). The end-to-end test, including Refresh, was verified with Zotero 10.0.2.

## Word and documents

### Is my original document modified?

Never. The output is a new file, `<stem>-zotero-cited.docx`. The script refuses to write over the input, and the report includes SHA-256 hashes of both files plus `inputUnchanged: true/false`.

### Why do the citations look wrong before I click Refresh?

The visible text is provisional: `[1]`, `[2,3]` or `(Author, Year)`, plus a simple Vancouver-like bibliography. The skill deliberately never fabricates Zotero's formatted output. Refresh in Word produces the real formatting.

### Can the agent run Refresh for me?

No, by design. Refresh runs inside Word through the Zotero add-in, and it can rewrite a whole document, including someone else's. You run it and review the result.

### Can I change the citation style afterwards?

Yes, anytime: Word → **Zotero → Document Preferences** (文档首选项) → pick a style. The style must be installed in Zotero.

### Which styles are supported?

Aliases: `vancouver`, `apa`, `nature`, `ieee`, `ama`, `chicago-author-date`, `harvard`, `gb-t-7714-numeric`, `gb-t-7714-author-date`. Any other CSL style works by its full ID, e.g. `http://www.zotero.org/styles/cell`. See [usage.md § 13](usage.md#13-citation-styles-and-locales).

### Can I use WPS, LibreOffice or Pages?

Not for these files. They can convert Zotero Word fields into plain text. Open and save the output only in Microsoft Word.

### Does it support footnote citations?

Not yet. Citations are inserted in the body text (`noteIndex` 0). `--note-type` only sets the document preference.

### Can it insert citations without changing my text?

Yes, in `placements.json` mode, which uses exact anchors. See [usage.md § Mode 2](usage.md#mode-2-placementsjson-existing-manuscript-text-must-not-change).

### Will it keep citations that are already in the document?

Yes. Existing Zotero fields, bibliography and document preferences are kept, and their preservation is validated automatically.

### What Markdown does `md_to_docx.py` support?

Headings up to `###`, paragraphs, bullets, numbered lines (as plain text), `**bold**`, `*italic*`. Tables, images, links and footnotes are not converted. For complex layouts, write the DOCX in Word and use markers or placements.

## Literature and scientific responsibility

### Can the agent make up references?

The skill forbids it. Every cited paper must come from `search_literature.py` or `lookup`, and DOIs from memory must pass `lookup`. Still, **you** must check that each paper actually supports its claim ([manual-steps.md § T2](manual-steps.md#t2-review-the-chosen-literature)).

### Which databases are searched?

OpenAlex, PubMed (NCBI E-utilities) and Crossref, using public APIs. Other host tools (e.g. a PubMed MCP server or web search) may be used for discovery, but the final list is always passed through `lookup`.

### Do I need API keys?

No. Optional: `ZWLC_MAILTO` (polite pool for Crossref/OpenAlex) and `NCBI_API_KEY` (higher PubMed limits).

## Privacy and safety

### What leaves my computer?

Only literature-search queries, and your `ZWLC_MAILTO`/`NCBI_API_KEY` if set, go to OpenAlex, PubMed and Crossref. Zotero communication stays on `127.0.0.1`. There is no telemetry. Don't put confidential text into search queries. See [SECURITY.md](../../SECURITY.md).

### Does it need my Zotero password or API key?

No. The local API needs no credentials, and the skill never asks for any.
