# zotero-word-live-citations

[中文说明](README.zh-CN.md)

This is an agent skill for **Claude Code** and **OpenAI Codex**. It turns a draft into a Word document that contains **live Zotero citations**. These are real `ADDIN ZOTERO_ITEM CSL_CITATION` and `ZOTERO_BIBL` fields, so the Zotero Word add-in can refresh, restyle and edit them later. The output is not plain `[1]` text.

The workflow has five steps:

1. **Find papers.** Search OpenAlex, PubMed and Crossref, then pick the papers that support each claim.
2. **Resolve against your library.** Match references to your local Zotero Desktop library by DOI, then PMID, then title, author and year. Ambiguous matches are never auto-picked.
3. **Import missing items (with approval only).** Missing references become an RIS file. The file is imported into the collection currently selected in Zotero, and only after you confirm the count and the target.
4. **Insert live fields.** Citation fields, a bibliography field and document preferences are written into a **copy** of your DOCX. The original file is never modified.
5. **Validate.** Structural validation always runs. On Windows, Word can also render the document to PDF. Zotero **Refresh** is left to you in Word.

All scripts use only the Python 3.9+ standard library. Nothing is installed automatically.

## Requirements

| | Needed for |
|---|---|
| Python ≥ 3.9 | everything |
| Zotero 7+ desktop, running, with *Settings → Advanced → Allow other applications on this computer to communicate with Zotero* enabled (local API at `http://127.0.0.1:23119/api/`) | resolving and importing |
| Microsoft Word + Zotero Word add-in | Refresh (manual) and optional PDF rendering (Windows) |
| Internet | literature search only |

## Install

```bash
git clone https://github.com/<owner>/codex-zotero-wordcitation.git
```

```bash
cd codex-zotero-wordcitation
```

For **Claude Code** (installs to `~/.claude/skills/`):

```bash
python install.py --target claude
```

For **Codex** (installs to `$CODEX_HOME/skills/`, by default `~/.codex/skills/`):

```bash
python install.py --target codex
```

Other install options:
- Use `--target both` to install for both agents.
- Use `--project <dir>` to install into `<dir>/.claude/skills` instead of your home directory.
- Use `--dry-run` to preview the changes.
- Use `--uninstall` to remove the skill.
- If an existing installation differs, the installer lists the differences and asks you to pass `--force`.

**Claude Code plugin marketplace (alternative).** Run these inside Claude Code:

```text
/plugin marketplace add <owner>/codex-zotero-wordcitation
/plugin install zotero-word-live-citations@zotero-word-live-citations
```

After installing, start a new session and check your environment. Run the command from the skill's install directory:

```bash
python scripts/selftest.py
```

## Usage

Ask the agent in plain language, for example:

- "Find supporting literature for each claim in `draft.md` and give me a Word file with live Zotero citations in Vancouver style."
- "Add Zotero citations for the references in `refs.ris` to `manuscript.docx` at the marked places."
- "Check whether `thesis.docx` contains valid Zotero citation fields."

The agent follows [`SKILL.md`](skills/zotero-word-live-citations/SKILL.md). Before importing anything into Zotero, it tells you how many records it will import and into which collection, then waits for your "yes".

### Minimal manual run

```bash
S=skills/zotero-word-live-citations/scripts
python $S/search_literature.py search "PD-1 blockade melanoma" --source openalex,pubmed --limit 5 --out candidates.json
python $S/resolve_references.py --references candidates.json --out map.json
python $S/md_to_docx.py --input draft.md --output draft.docx          # draft.md contains markers like [@ref:C1; @ref:C3]
python $S/insert_zotero_fields.py --input draft.docx --items map.json --placeholders --style vancouver --report report.json
python $S/validate_zotero_docx.py draft-zotero-cited.docx --baseline draft.docx --require-item-data --expect-bibliography --json
```

Then open `draft-zotero-cited.docx` in Word and click **Zotero → Refresh**.

## Safety guarantees

- The input DOCX is never overwritten. The output is `<stem>-zotero-cited.docx`, and the report includes SHA-256 hashes of both files.
- Zotero items are never created, edited, merged or deleted without explicit approval.
- Only parent items are cited, never attachments or notes. Each item gets its own library URI, and namespaces are never mixed.
- `formattedCitation`/`plainCitation` are never synthesized. Zotero produces them on Refresh.
- The final report keeps three results separate: structural validation, Word rendering and Zotero Refresh.

## Development

```bash
cd skills/zotero-word-live-citations/tests
```

```bash
python -m unittest discover
```

## License

This project is released under the MIT License; see [LICENSE](LICENSE). Parts of the code are adapted from [drguptavivek/zotero-use](https://github.com/drguptavivek/zotero-use) and [openai/plugins](https://github.com/openai/plugins) (both MIT). [NOTICE](NOTICE) lists what was adapted from each.
