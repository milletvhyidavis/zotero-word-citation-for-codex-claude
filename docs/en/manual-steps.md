# Manual steps: what only you can do

[简体中文](../zh-CN/manual-steps.md) · [Back to README](../../README.md)

The agent automates searching, matching, file building, field insertion and validation. A few actions are **deliberately left to you**. Some need software the skill will not install. Some change your Zotero library. Some are scientific judgements. And Zotero Refresh only runs inside Word. This page lists every one of them in the order you will meet them, with why each matters and exactly how to do it.

> [!IMPORTANT]
> If you skip a step marked **Required**, the workflow either stops with an error or produces a document that is not what you expect. Steps marked *Recommended* or *Optional* are safety nets.

## Contents

- [Quick checklist](#quick-checklist)
- [Before first use](#before-first-use)
  - [B1. Install Python ≥ 3.9](#b1-install-python--39)
  - [B2. Run Zotero Desktop and allow local communication](#b2-run-zotero-desktop-and-allow-local-communication)
  - [B3. Install the Zotero Word add-in](#b3-install-the-zotero-word-add-in)
  - [B4. Citation styles (optional)](#b4-citation-styles-optional)
  - [B5. Sign in to Zotero (usually already done; fix only when asked)](#b5-sign-in-to-zotero-usually-already-done-fix-only-when-asked)
  - [B6. Optional environment variables](#b6-optional-environment-variables)
  - [B7. Install the skill, start a new session, run the self-test](#b7-install-the-skill-start-a-new-session-run-the-self-test)
- [For every task](#for-every-task)
  - [T1. Protect your original document](#t1-protect-your-original-document)
  - [T2. Review the chosen literature](#t2-review-the-chosen-literature)
  - [T3. Resolve ambiguous matches and duplicates](#t3-resolve-ambiguous-matches-and-duplicates)
  - [T4. Before any import: select the target collection, then approve](#t4-before-any-import-select-the-target-collection-then-approve)
  - [T5. Review uncertain citation placements](#t5-review-uncertain-citation-placements)
- [After the output is generated](#after-the-output-is-generated)
  - [A1. Open the output in Microsoft Word](#a1-open-the-output-in-microsoft-word)
  - [A2. Click Zotero → Refresh](#a2-click-zotero--refresh)
  - [A3. Check, and change the style if needed](#a3-check-and-change-the-style-if-needed)
  - [A4. Undo an import (if needed)](#a4-undo-an-import-if-needed)
  - [A5. Before you share or submit](#a5-before-you-share-or-submit)
- [Menu names: English ↔ Chinese UI](#menu-names-english--chinese-ui)

---

## Quick checklist

Copy this into your notes and tick it off.

**Before first use (once per computer)**

- [ ] **B1** Python ≥ 3.9 installed (if not, the agent guides you to python.org), and `python --version` (or `py -3 --version`) works. *Required*
- [ ] **B2** Zotero Desktop 7+ running; *Allow other applications on this computer to communicate with Zotero* enabled, and a **screenshot of the ticked setting sent to the agent**. *Required*
- [ ] **B3** Zotero Word add-in installed in Microsoft Word; Word restarted. *Required for Refresh*
- [ ] **B4** No style needs to be prepared; change it later in Word's Document Preferences. *Optional*
- [ ] **B5** Zotero is signed in to a zotero.org account (most users already are; the agent tells you if not). *Required only when the agent reports a problem*
- [ ] **B6** `ZWLC_MAILTO` / `NCBI_API_KEY` set. *Optional*
- [ ] **B7** Skill installed, new agent session started, `selftest.py` all OK. *Required*

**For every task**

- [ ] **T1** Original document backed up, not open for editing by others. *Recommended*
- [ ] **T2** Claim → paper list reviewed. *Required (your responsibility)*
- [ ] **T3** Ambiguous matches resolved (pin `zoteroKey`); duplicates noted. *Required when reported*
- [ ] **T4** Target collection **selected in the Zotero window**, count + target confirmed with an explicit "yes". *Required before any import*
- [ ] **T5** Low-confidence placements reviewed (placements mode). *Required when reported*

**After the output**

- [ ] **A1** Output opened in **Microsoft Word** (not WPS/LibreOffice/Pages). *Required*
- [ ] **A2** **Zotero → Refresh** clicked; dialogs handled. *Required*
- [ ] **A3** Style, numbering and bibliography checked; style changed via Document Preferences if needed. *Required*
- [ ] **A4** Unwanted imports removed via the `zwlc-import` tag. *Optional*
- [ ] **A5** Final/sharing copy handled (backups; unlink citations only on a submission copy). *Recommended*

---

## Before first use

### B1. Install Python ≥ 3.9

**Why.** Every script is Python 3.9+ standard library. **The skill never installs anything**, including Python and packages.

**How.**

| OS | Recommended |
|---|---|
| Windows | Install from [python.org](https://www.python.org/downloads/) and tick *Add python.exe to PATH*. The installer also provides the `py` launcher. |
| macOS | `python3` from python.org or Homebrew (`brew install python`). |
| Linux | Your distribution's `python3` (3.9 or newer). |

Check:

```bash
python --version
```

```bash
py -3 --version
```

> [!WARNING]
> **Windows: the Microsoft Store "python" alias.** On a fresh Windows, typing `python` may open the Microsoft Store or print *"Python was not found; run without arguments to install from the Microsoft Store…"*. That is a stub, not Python. Either install real Python (above) and use `py -3`, or turn the alias off: **Settings → Apps → Advanced app settings → App execution aliases** → switch off `python.exe` and `python3.exe`.

> [!TIP]
> **Codex users** may already have a bundled Python at `~/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python` (`python.exe` on Windows). The skill's instructions allow the agent to use it when no system Python is available.

The agent picks the first of `python3`, `python`, `py -3` that reports version ≥ 3.9. If none works, the agent **walks you through the install**: it gives you the python.org download link, reminds Windows users to tick *Add python.exe to PATH*, and asks you to reopen the terminal / agent session and confirm the version. It will not install anything itself.

### B2. Run Zotero Desktop and allow local communication

**Why.** Matching and importing talk to Zotero Desktop on your own computer at `http://127.0.0.1:23119` (local API: `http://127.0.0.1:23119/api/`). This interface is off unless you enable it, and it only works while Zotero is running.

**How.**

1. Install **Zotero 7 or newer** from [zotero.org](https://www.zotero.org/download/). The verified test used Zotero 10.0.2.
2. Start Zotero and keep it running while the agent works.
3. Open settings:
   - Windows / Linux: **Edit → Settings** (编辑 → 设置)
   - macOS: **Zotero → Settings…**
4. Go to **Advanced** (高级). Under **Miscellaneous** (杂项), tick
   **"Allow other applications on this computer to communicate with Zotero"**
   (**"允许此计算机上的其他应用程序与 Zotero 通讯"**).
5. **Send the agent a screenshot of the settings page with the box ticked.** The local API is required by this skill: the agent checks the screenshot, then confirms with the check below, and will not start matching or importing before that.
6. Close settings. No restart is usually needed. If the check below still fails, restart Zotero.

**Check.** `$S` is the skill's `scripts/` folder, e.g. `~/.claude/skills/zotero-word-live-citations/scripts` (see [usage.md § Conventions](usage.md#3-conventions-used-below)):

```bash
python "$S/zotero_local.py" status
```

You want `"apiReachable": true` and `"itemsReadable": true`. If `connectorReachable` is true but `apiReachable` is false, the checkbox is off, or Zotero is older than 7. `selftest.py` performs the same checks (`zotero-running`, `zotero-local-api`, `zotero-read-items`).

> [!NOTE]
> The local API only listens on `127.0.0.1`. It is not reachable from other computers, and it needs no API key or password. The skill never changes Zotero settings. You tick this box yourself.

### B3. Install the Zotero Word add-in

**Why.** The live fields are only useful when the Zotero add-in in Word can refresh them. Without it, there is no Zotero tab and no Refresh.

**How.**

1. In Zotero: **Settings → Cite → Word Processors** (设置 → 引用 → 文字处理软件).
2. Click **Install Microsoft Word Add-in** (安装 Microsoft Word 加载项), or **Reinstall** if it already exists.
3. **Quit and restart Word.** A **Zotero** tab should now appear in the ribbon.

On macOS, grant any permission prompts Word or Zotero shows. If the tab does not appear, see [troubleshooting.md § Word add-in](troubleshooting.md#zotero-refresh-in-word).

### B4. Citation styles (optional)

**Nothing to prepare.** Change the style anytime after generation in Word → Zotero → **Document Preferences**. The style ID the skill writes is only a starting value; if it is not installed, Zotero tries to download it on Refresh or asks you to pick another.

**If you want to install a style anyway:** Zotero → **Settings → Cite → Styles** (设置 → 引用 → 样式) → **+** / **Get additional styles…** → search, e.g. "GB/T 7714" or your journal's name → install. Check that the style appears in the list.

### B5. Sign in to Zotero (usually already done; fix only when asked)

**Most users need to do nothing.** The agent checks automatically via `zotero_local.py status` (`"loggedIn"`) or `selftest.py` (`zotero-logged-in`). Only if you are not signed in, or resolving reports *"cannot verify library namespace … local-only/unsynced"*, will it ask you to follow the steps below.

**How (only when the agent asks).**

1. If you have no account, create a free one at [zotero.org](https://www.zotero.org/user/register).
2. Zotero → **Settings → Sync**: sign in with your username and password (type the password only in Zotero, **never send it to the agent**).
3. Click the sync button at the top right of the Zotero window once.
4. **Send the agent a screenshot of the Sync page showing the signed-in account**; the agent re-checks and continues resolving.

Why this matters, and notes on group libraries:

**Why.** A Zotero citation stores a URI such as `http://zotero.org/users/<id>/items/<KEY>` or `http://zotero.org/groups/<id>/items/<KEY>`. The skill builds this URI from the item's own library, and **only when the library has a real numeric ID**, which comes from syncing with zotero.org.

| Library | What happens |
|---|---|
| Personal library, synced at least once | works (`users/<id>`) |
| **Personal library never synced (local-only)** | resolving **refuses**: the item goes to `missing` with *"cannot verify library namespace … local-only/unsynced"* |
| Group library | works (`groups/<id>`) when you resolve with `--library group:<id>` |

**How to fix a local-only library.** Sign in and sync once as described above, then run resolving again. (If an existing Zotero-generated field in a document already carries a URI for that item, that URI is valid too. The skill just won't invent one.)

**Group libraries.** List them with `zotero_local.py groups`, then resolve with `resolve_references.py --library group:<id> …`. Keep in mind:

- A collection you want to import into must be **editable** by you. The import refuses read-only targets.
- `[@zotero:KEY]` markers for keys *not* in the map are looked up in your **personal** library only. For group items, resolve them into the map first.
- One `insert_zotero_fields.py` run takes one map. Citing personal and group items in the same run means combining the `resolved` sections of two maps into one file yourself.

### B6. Optional environment variables

| Variable | Used by | Purpose |
|---|---|---|
| `ZWLC_MAILTO` | `search_literature.py` | your e-mail, sent as `mailto` to Crossref and OpenAlex (their "polite pool": more reliable, fewer rate-limit errors) |
| `NCBI_API_KEY` | `search_literature.py` | NCBI E-utilities key; raises PubMed limits (without it, stay around 3 requests/second) |
| `ZOTERO_LOCAL_BASE_URL` | all Zotero scripts | a non-default Zotero address (default `http://127.0.0.1:23119`) |

bash / zsh (add to `~/.bashrc` / `~/.zshrc` to keep):

```bash
export ZWLC_MAILTO="you@example.org"
```

```bash
export NCBI_API_KEY="your-ncbi-key"
```

PowerShell (current session):

```powershell
$env:ZWLC_MAILTO = "you@example.org"
```

PowerShell (persist for your user):

```powershell
[Environment]::SetEnvironmentVariable("ZWLC_MAILTO", "you@example.org", "User")
```

Restart the terminal and the agent session afterwards. **Network access is only needed for literature search.** Matching, importing, inserting and validating are local.

### B7. Install the skill, start a new session, run the self-test

See [installation.md](installation.md). After installing, **start a new Claude Code / Codex session**, because skills are discovered at session start. Then run:

```bash
python ~/.claude/skills/zotero-word-live-citations/scripts/selftest.py
```

All lines should say `[OK ]`. `microsoft-word` may say `NO` on macOS/Linux, which only disables PDF rendering.

---

## For every task

### T1. Protect your original document

**Why.** The skill always writes a **copy** (`<stem>-zotero-cited.docx`) and refuses to overwrite the input. Your own habits still matter, though.

**How.**

- Keep a backup or version history of important manuscripts.
- **Never ask the agent to overwrite the original**, and don't rename the output over it.
- **Shared documents** (OneDrive/SharePoint/Teams co-authoring, a thesis shared with a supervisor): coordinate first. Work on a copy, and do not refresh or re-save a colleague's document without agreement.
- **Close the output file in Word** before asking the agent to regenerate it. A file locked by Word cannot be replaced, and the script refuses an existing output unless `--force` is used.

### T2. Review the chosen literature

**Why.** The agent may only cite papers that a search or lookup tool actually returned, and it never invents DOIs. **Whether a paper really supports your claim is a scientific judgement, and it is yours.**

**How.** When the agent shows the *claim → paper* list:

- Read at least the title and abstract of each paper. Open the full text for key claims.
- Check the paper type: primary study for specific findings, review for broad statements.
- Watch out for retractions, preprints you would not cite, and outdated work on fast-moving topics.
- Ask for replacements freely, e.g. *"use the original 2010 trial, not the review"*.

### T3. Resolve ambiguous matches and duplicates

**Why.** When a reference could be more than one item in your library, the skill **never picks one for you**.

**How.** The agent shows the `ambiguous` candidates (key, title, year, first author, score). Tell it which one is right. It then pins that item by adding `"zoteroKey": "ABCD1234"` to the reference record and resolves again. You can also look the item up in Zotero yourself: select it, and the key appears in the item URI.

`duplicates` means several of your own library items share a DOI/PMID. The skill never merges or deletes them. If you want to clean up, use **Duplicate Items** (重复条目) in Zotero's left pane.

### T4. Before any import: select the target collection, then approve

> [!CAUTION]
> **The Zotero connector imports into whatever collection is currently selected in the Zotero window.** There is no collection parameter. If you have *Unfiled Items* or a random project folder selected, that is where the new items go.

**How.**

1. In Zotero, **create a dedicated collection** for the import (right-click *My Library* → *New Collection…* / 新建分类…), e.g. `Imported by agent` or, as in the verified test, `肿瘤免疫测试`.
2. **Click it** so it is selected.
3. The agent runs `zotero_local.py selected-target` and tells you something like: *"18 records → collection 肿瘤免疫测试 in library My Library. Import?"*
4. **Check the count and the target, then answer with a clear "yes".** "Go ahead and add citations" is *not* approval to import. The agent will ask explicitly.
5. The agent imports with `--expect-target "<name>"`. If you clicked another collection in the meantime, the import **refuses** (exit 2). Re-select and confirm again.

> [!TIP]
> All imported records carry the tag **`zwlc-import`** when the agent builds the RIS with `--tag zwlc-import`, which is the recommended default. That makes them easy to find, review or undo (see [A4](#a4-undo-an-import-if-needed)).

Want to review the records first? Open the generated `missing.ris` in any text editor. It is plain text.

### T5. Review uncertain citation placements

**Why.** When citations are added to an existing text without markers (`placements.json` mode), or migrated from an old draft to a new one, some locations are uncertain.

**How.** The agent runs a dry run and shows each placement's context (`...text <<CITE>> text...`). Placements with low similarity (below about 0.8), split or merged sentences, or claims that vanished from the new text are listed for you. Confirm, move or drop them. The agent never edits your text to make an anchor fit.

---

## After the output is generated

### A1. Open the output in Microsoft Word

> [!WARNING]
> **WPS is not supported.** Use **Microsoft Word** with the Zotero add-in. **Do not open and save the output in WPS, LibreOffice, Pages or online converters.** If WPS is the default app for `.docx`, right-click the file → Open with → Word. They can turn Zotero fields into plain text, and then the citations are no longer live. If that happens, go back to the last good copy.

### A2. Click Zotero → Refresh

> [!IMPORTANT]
> **Refresh is never run automatically.** Before Refresh, the visible citation and bibliography text is **provisional**: simple `[1]`/`(Author, Year)` labels and a plain, Vancouver-like list. Refresh makes Zotero format everything in your chosen style.

**How.**

1. Open `<stem>-zotero-cited.docx` in Word.
2. Ribbon: **Zotero** tab → **Refresh** (刷新).
3. Wait until it finishes. Large documents can take a while.

**Dialogs you may see:**

| Dialog | What to do |
|---|---|
| *"You have modified this citation since Zotero generated it…"* | Someone edited the visible text of a field. Usually choose **No** to keep Zotero's version, or undo your edit. If many appear, stop and report it. Don't click through blindly. |
| *"… item not found in your library / could not be found"* | The citation refers to an item from another library, e.g. a co-author's. Its embedded `itemData` keeps it working. Don't relink unless you mean to. |
| Style chooser (Document Preferences) | Pick your style and confirm. |

If Refresh reports **modified or missing items** for citations the agent just created, stop, note which citation, and report it (see [troubleshooting.md](troubleshooting.md#zotero-refresh-in-word)).

### A3. Check, and change the style if needed

Check citation style, numbering order, and completeness and order of the bibliography.

To **change the style** at any time: **Zotero tab → Document Preferences** (文档首选项) → choose a style (and language) → OK. Zotero reformats the whole document. The style chosen at generation time is just a starting point.

> [!TIP]
> Seeing `{ ADDIN ZOTERO_ITEM CSL_CITATION {...} }` instead of citations? That is Word's field-code view. Press **Alt+F9** (macOS: **Option+F9** / **fn+Option+F9**) to toggle back.

### A4. Undo an import (if needed)

The skill **never deletes** anything from Zotero. To remove imported items:

1. In Zotero, select the library (or the target collection).
2. In the **tag selector** (bottom of the left pane), click **`zwlc-import`**.
3. Check the listed items. Remove any that you already cite elsewhere from the selection.
4. Select the items → **Move Item to Trash…** (移到回收站) / press Delete.
5. Optionally empty the trash later.

Items that are still cited in a document keep working there, because the fields contain embedded `itemData`. Refresh will then report them as not in your library.

> [!WARNING]
> **Never import the same RIS file twice.** The Zotero connector does not deduplicate. A second `import-ris` run creates a second copy of every item, and `resolve_references.py` then reports those references as `ambiguous` / `duplicates`. Always re-run `resolve_references.py` before importing again, and import only what is still `missing`.
>
> **If it already happened:** click the tag `zwlc-import`, sort by **Date Added**, and delete the extra copies or merge them via **Duplicate Items** (重复条目). **Keep the copies already cited in your document.** Their keys are in `report.json` (`placements[].keys`) and `reference-map.json` (`resolved.<refId>.key`). Then run `resolve_references.py` again. See also [troubleshooting.md § Importing](troubleshooting.md#importing).

### A5. Before you share or submit

- Keep the live-citation version as your working copy.
- Some journals want plain text: in Word, **Zotero → Unlink Citations** (取消链接引用) converts fields to static text. **Do this only on a separate submission copy**, because it cannot be undone into live fields.
- When passing the document to co-authors, tell them to use Word with the Zotero add-in, not WPS/LibreOffice/Pages.

---

## Menu names: English ↔ Chinese UI

UI labels vary a little between Zotero and Word versions. Look for the closest match.

| English | 简体中文 |
|---|---|
| Zotero: Edit → Settings | 编辑 → 设置 |
| Settings → Advanced → Miscellaneous | 设置 → 高级 → 杂项 |
| Allow other applications on this computer to communicate with Zotero | 允许此计算机上的其他应用程序与 Zotero 通讯 |
| Settings → Cite → Word Processors → Install/Reinstall Microsoft Word Add-in | 设置 → 引用 → 文字处理软件 → 安装/重新安装 Microsoft Word 加载项 |
| Settings → Cite → Styles | 设置 → 引用 → 样式 |
| Settings → Sync | 设置 → 同步 |
| New Collection… | 新建分类… |
| Duplicate Items | 重复条目 |
| Move Item to Trash… | 移到回收站… |
| Word: Zotero → Refresh | Zotero → 刷新 |
| Word: Zotero → Document Preferences | Zotero → 文档首选项 |
| Word: Zotero → Unlink Citations | Zotero → 取消链接引用 |
