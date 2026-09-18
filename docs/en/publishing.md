# Publishing guide (for maintainers)

[简体中文](../zh-CN/publishing.md) · [Back to README](../../README.en.md)

This page is for whoever publishes the repository on GitHub. Users of the skill don't need it.

> [!IMPORTANT]
> **About `<owner>`.** Every GitHub URL and marketplace command in the documentation uses the placeholder **`<owner>`** for the GitHub user or organisation that will own the repository, e.g. `https://github.com/<owner>/zotero-word-citation-for-codex-claude`. It is used on purpose so that it can be replaced in one pass once the owner is known ([step 4](#4-replace-owner)). This guide itself keeps `<owner>` as a placeholder and is excluded from that replacement.

## Contents

- [1. Pre-publish checks](#1-pre-publish-checks)
- [2. Create an empty repository on GitHub](#2-create-an-empty-repository-on-github)
- [3. Push the code](#3-push-the-code)
- [4. Replace `<owner>`](#4-replace-owner)
- [5. Description, topics and settings](#5-description-topics-and-settings)
- [6. Tag and release v1.0.0](#6-tag-and-release-v100)
- [7. Test the install from GitHub](#7-test-the-install-from-github)
- [8. Optional: submit to skill directories](#8-optional-submit-to-skill-directories)
- [9. Later releases](#9-later-releases)

---

## 1. Pre-publish checks

Work through this list in the repository root before the first push.

1. **Tests pass.**

   ```bash
   cd skills/zotero-word-live-citations/tests
   ```

   ```bash
   python -m unittest discover
   ```

   Expect `Ran 38 tests … OK`. Go back to the repository root afterwards.

2. **No personal data.** Search for your Zotero user ID, your e-mail address, private collection names and local paths:

   ```bash
   grep -rn "your-zotero-user-id\|you@your-domain\|C:/Users/" --exclude-dir=.git .
   ```

   PowerShell:

   ```powershell
   Get-ChildItem -Recurse -File | Where-Object { $_.FullName -notmatch "\\.git\\" } | Select-String -Pattern "your-zotero-user-id","you@your-domain"
   ```

   > [!TIP]
   > Run this scan again whenever you add examples, fixtures or screenshots. The shipped examples use neutral values (e.g. the user ID `123456` in `references/zotero-local-api.md`), and your own should too.

3. **No generated or test files.** The `.gitignore` already excludes `__pycache__/`, `*.pyc`, `.pytest_cache/`, `*-zotero-cited.docx`, Word lock files (`~$*.docx`) and `e2e-tumor-immunology/`. Check that no manuscripts, reference maps, RIS files or PDFs from your own tests are in the tree:

   ```bash
   git status --short
   ```

4. **Optional personalisation** (these are code/metadata files, so review any change yourself):
   - `LICENSE`, `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` and `.codex-plugin/plugin.json` name the author as `zotero-word-live-citations contributors`. You may put your own name or organisation there instead.
   - `skills/zotero-word-live-citations/scripts/_common.py` sets `USER_AGENT = "zotero-word-live-citations/1.0"`. OpenAlex and Crossref recommend a user agent that points to the project, so you may append the repository URL once it exists, e.g. `"zotero-word-live-citations/1.0 (+https://github.com/<owner>/zotero-word-citation-for-codex-claude)"`. This is a code change, so the `<owner>` replacement in [step 4](#4-replace-owner) does not cover it. Type the real owner name directly.

5. **Docs are consistent.** Both languages exist for every page in `docs/`, and `CHANGELOG.md` has the release date you want.

## 2. Create an empty repository on GitHub

1. Go to **github.com → New repository**.
2. Owner: your user or organisation (this is `<owner>`). Name: **`zotero-word-citation-for-codex-claude`**.
3. Visibility: **Public**.
4. **Do not** add a README, `.gitignore` or license. The repository already has them, and an initial commit on GitHub would make the first push fail.
5. Click **Create repository**.

With the GitHub CLI you can do the same from the terminal instead (it creates the repository, adds the remote and pushes in one go):

```bash
gh repo create <owner>/zotero-word-citation-for-codex-claude --public --source . --remote origin --push
```

If you use it, skip to [step 4](#4-replace-owner).

## 3. Push the code

If the folder is not a git repository yet, initialise it and make the first commit:

```bash
git init
```

```bash
git add .
```

```bash
git commit -m "Initial public release v1.0.0"
```

Then connect it to GitHub and push:

```bash
git remote add origin https://github.com/<owner>/zotero-word-citation-for-codex-claude.git
```

```bash
git branch -M main
```

```bash
git push -u origin main
```

Replace `<owner>` in these commands with your GitHub name. If `origin` already exists, use `git remote set-url origin …` instead of `git remote add`.

## 4. Replace `<owner>`

The placeholder `<owner>` appears in these files and lines (excluding this guide and its Chinese counterpart):

| File | Line | Content |
|---|---|---|
| `README.en.md` | 102 | `git clone https://github.com/<owner>/zotero-word-citation-for-codex-claude.git` |
| `README.en.md` | 120 | `/plugin marketplace add <owner>/zotero-word-citation-for-codex-claude` |
| `README.md` | 102 | `git clone https://github.com/<owner>/zotero-word-citation-for-codex-claude.git` |
| `README.md` | 120 | `/plugin marketplace add <owner>/zotero-word-citation-for-codex-claude` |
| `CHANGELOG.md` | 53 | `[1.0.0]: https://github.com/<owner>/zotero-word-citation-for-codex-claude/releases/tag/v1.0.0` |
| `CONTRIBUTING.md` | 15 | `git clone https://github.com/<owner>/zotero-word-citation-for-codex-claude.git` (English) |
| `CONTRIBUTING.md` | 89 | `git clone https://github.com/<owner>/zotero-word-citation-for-codex-claude.git` (Chinese) |
| `SECURITY.md` | 26 | `https://github.com/<owner>/zotero-word-citation-for-codex-claude/security/advisories/new` (English) |
| `SECURITY.md` | 52 | `https://github.com/<owner>/zotero-word-citation-for-codex-claude/security/advisories/new` (Chinese) |
| `docs/en/installation.md` | 36 | `git clone https://github.com/<owner>/zotero-word-citation-for-codex-claude.git` |
| `docs/en/installation.md` | 92 | `/plugin marketplace add <owner>/zotero-word-citation-for-codex-claude` |
| `docs/en/troubleshooting.md` | 164 | `https://github.com/<owner>/zotero-word-citation-for-codex-claude/issues` |
| `docs/zh-CN/installation.md` | 38 | `git clone https://github.com/<owner>/zotero-word-citation-for-codex-claude.git` |
| `docs/zh-CN/installation.md` | 96 | `/plugin marketplace add <owner>/zotero-word-citation-for-codex-claude` |
| `docs/zh-CN/troubleshooting.md` | 175 | `https://github.com/<owner>/zotero-word-citation-for-codex-claude/issues` |

No code, JSON or YAML file contains `<owner>`. Line numbers may shift if you edit the files first. The grep below always gives the current list.

List current occurrences:

```bash
grep -rn "<owner>" --include="*.md" --exclude-dir=.git .
```

**Replace them (bash, GNU sed on Linux or Git Bash):**

```bash
OWNER=your-github-name
```

```bash
grep -rl "<owner>" --include="*.md" --exclude-dir=.git . | grep -v "/publishing.md$" | xargs sed -i "s/<owner>/$OWNER/g"
```

On macOS (BSD sed), use `sed -i ''` instead of `sed -i`:

```bash
grep -rl "<owner>" --include="*.md" --exclude-dir=.git . | grep -v "/publishing.md$" | xargs sed -i '' "s/<owner>/$OWNER/g"
```

**Replace them (PowerShell).** This writes UTF-8 without BOM, which keeps the Chinese text intact:

```powershell
$Owner = "your-github-name"
```

```powershell
Get-ChildItem -Recurse -Filter *.md | Where-Object { $_.Name -ne "publishing.md" -and $_.FullName -notmatch "\\.git\\" } | ForEach-Object { $t = [IO.File]::ReadAllText($_.FullName); if ($t.Contains("<owner>")) { [IO.File]::WriteAllText($_.FullName, $t.Replace("<owner>", $Owner), (New-Object Text.UTF8Encoding($false))) } }
```

> [!NOTE]
> Don't use `Set-Content` in Windows PowerShell 5.1 for this. It writes the system ANSI code page by default and would corrupt the Chinese files.

Check that only the two publishing guides still contain the placeholder, then commit and push:

```bash
grep -rn "<owner>" --include="*.md" --exclude-dir=.git .
```

```bash
git commit -am "docs: set repository owner"
```

```bash
git push
```

## 5. Description, topics and settings

On the repository page, click the gear icon next to **About**:

- **Description:** e.g. *Agent skill for Claude Code and Codex: find papers, match them to Zotero, and write live, refreshable Zotero citations into Word DOCX.*
- **Topics:** `zotero`, `microsoft-word`, `docx`, `citations`, `bibliography`, `csl`, `claude-code`, `claude-skills`, `agent-skills`, `codex`, `literature-search`, `pubmed`, `openalex`, `crossref`

Or with the GitHub CLI:

```bash
gh repo edit <owner>/zotero-word-citation-for-codex-claude --description "Agent skill for Claude Code and Codex: live, refreshable Zotero citations in Word DOCX"
```

```bash
gh repo edit <owner>/zotero-word-citation-for-codex-claude --add-topic zotero,microsoft-word,docx,citations,bibliography,csl,claude-code,claude-skills,agent-skills,codex,literature-search,pubmed,openalex,crossref
```

Recommended settings:

- **Settings → Security → Private vulnerability reporting → Enable.** `SECURITY.md` points reporters to it. (Depending on the GitHub UI version, it is under *Code security* or *Code security and analysis*.)
- **Settings → General → Features:** keep **Issues** on. `docs/*/troubleshooting.md` sends users there.
- Optionally protect `main` (**Settings → Branches**) so changes arrive via pull requests.

## 6. Tag and release v1.0.0

Create an annotated tag and push it:

```bash
git tag -a v1.0.0 -m "zotero-word-live-citations v1.0.0"
```

```bash
git push origin v1.0.0
```

Create the release. The simplest way is to copy the `## [1.0.0]` section of `CHANGELOG.md` into a temporary file outside the repository, e.g. `../release-notes-1.0.0.md`, and use it as the release notes:

```bash
gh release create v1.0.0 --title "v1.0.0" --notes-file ../release-notes-1.0.0.md
```

Without the CLI: repository → **Releases → Draft a new release** → choose tag `v1.0.0` → title `v1.0.0` → paste the changelog section → **Publish release**.

The version must match `"version": "1.0.0"` in `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` and `.codex-plugin/plugin.json`.

## 7. Test the install from GitHub

Test as a new user would, on a clean machine or account if possible.

**Claude Code marketplace:** in a new Claude Code session:

```text
/plugin marketplace add <owner>/zotero-word-citation-for-codex-claude
```

```text
/plugin install zotero-word-live-citations@zotero-word-live-citations
```

Restart Claude Code, then ask *"Do you have the zotero-word-live-citations skill?"* and try a small task (e.g. "check whether this DOCX contains valid Zotero fields").

**`install.py` from a fresh clone:**

```bash
git clone https://github.com/<owner>/zotero-word-citation-for-codex-claude.git
```

```bash
cd zotero-word-citation-for-codex-claude
```

```bash
python install.py --target both --dry-run
```

```bash
python install.py --target claude
```

```bash
python ~/.claude/skills/zotero-word-live-citations/scripts/selftest.py
```

**Codex:** `python install.py --target codex`, start a new Codex session and call `$zotero-word-live-citations`.

Also check that all links in the README and `docs/` work on GitHub (in both languages), and that the mermaid diagram and alert blocks render.

## 8. Optional: submit to skill directories

Several community-run lists and directories collect Claude Code plugins, agent skills and Codex skills (for example "awesome" lists on GitHub and marketplace aggregators). If you want more users to find the skill:

1. Find directories that are active and accept submissions. Read their contribution guidelines.
2. Submit the repository URL `https://github.com/<owner>/zotero-word-citation-for-codex-claude` with a one-line description, e.g. *Live, refreshable Zotero citations in Word DOCX: literature search, Zotero matching, approved imports, field insertion and validation.*
3. Mention the requirements honestly: Zotero Desktop 7+, Microsoft Word with the Zotero add-in for Refresh, Python ≥ 3.9.
4. Don't imply any affiliation with Zotero, Microsoft, Anthropic or OpenAI.

## 9. Later releases

1. Add entries under an `## [Unreleased]` heading in `CHANGELOG.md` (English and Chinese) as changes land.
2. At release time, rename it to `## [x.y.z] — YYYY-MM-DD` and add the link line at the bottom.
3. Bump `"version"` in `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` and `.codex-plugin/plugin.json`. Also update `USER_AGENT` in `_common.py` if it contains the version.
4. Run the tests, commit, then tag and release as in [step 6](#6-tag-and-release-v100).
5. Users update with `git pull` + `python install.py --target … --force`, or `/plugin marketplace update zotero-word-live-citations` in Claude Code.
