# Installation

[简体中文](../zh-CN/installation.md) · [Back to README](../../README.md)

## Contents

- [1. Prerequisites](#1-prerequisites)
- [2. Get the code](#2-get-the-code)
- [3. Option A: `install.py` (Claude Code and/or Codex)](#3-option-a-installpy-claude-code-andor-codex)
- [4. Option B: Claude Code plugin marketplace](#4-option-b-claude-code-plugin-marketplace)
- [5. Option C: manual copy](#5-option-c-manual-copy)
- [6. Verify the installation](#6-verify-the-installation)
- [7. Updating](#7-updating)
- [8. Uninstalling](#8-uninstalling)
- [9. Python discovery](#python-discovery)
- [10. Per-OS notes](#10-per-os-notes)

---

## 1. Prerequisites

| Component | Version | Needed for | Installed by the skill? |
|---|---|---|---|
| Python | ≥ 3.9 (standard library only) | everything | **no, install it yourself** |
| Zotero Desktop | 7 or newer (verified with 10.0.2), running, local communication allowed | matching, importing | **no** |
| Microsoft Word + Zotero Word add-in | Word 2016 / Microsoft 365 (verified with Word 16) | Refresh (manual); PDF rendering on Windows | **no** |
| Claude Code or OpenAI Codex | current | running the skill as an agent | no |
| Internet | | literature search only | |

> [!IMPORTANT]
> **The skill never installs anything**: no Python, no pip packages, no Zotero plugins, no Word add-ins. The one-time setup of Python, Zotero and the Word add-in is described step by step in [manual-steps.md § Before first use](manual-steps.md#before-first-use).

## 2. Get the code

```bash
git clone https://github.com/<owner>/zotero-word-live-citations.git
```

```bash
cd zotero-word-live-citations
```

No git? Download the ZIP from the GitHub page (**Code → Download ZIP**) and unpack it.

## 3. Option A: `install.py` (Claude Code and/or Codex)

`install.py` copies `skills/zotero-word-live-citations/` (without `tests/` and caches) into the agent's skills folder. It uses only the standard library.

| Command | Installs to |
|---|---|
| `python install.py --target claude` | `~/.claude/skills/zotero-word-live-citations` |
| `python install.py --target codex` | `$CODEX_HOME/skills/zotero-word-live-citations` (default `~/.codex/skills/…`) |
| `python install.py --target both` | both of the above |
| `python install.py --target claude --project <dir>` | `<dir>/.claude/skills/zotero-word-live-citations` (only for that project) |
| `python install.py --target codex --project <dir>` | `<dir>/.codex/skills/zotero-word-live-citations` |

Flags:

| Flag | Meaning |
|---|---|
| `--target {claude,codex,both}` | required |
| `--project DIR` | install into a project folder instead of your home directory |
| `--dry-run` | print what would happen, change nothing |
| `--force` | replace an existing installation that differs |
| `--uninstall` | remove the installed skill directory (only if it contains `SKILL.md`) |

Examples:

```bash
python install.py --target claude
```

```bash
python install.py --target both --dry-run
```

On Windows, `~` means `%USERPROFILE%`, e.g. `C:\Users\you\.claude\skills\zotero-word-live-citations`.

> [!NOTE]
> If an existing installation differs from the repository, `install.py` lists every `added` / `changed` / `removed` file and **stops** (exit 1). Re-run with `--force` to replace it. Identical installations are reported as "already up to date".

> [!NOTE]
> **Codex home.** If you set the `CODEX_HOME` environment variable, the Codex target uses `$CODEX_HOME/skills`. Otherwise it uses `~/.codex/skills`. `--project` installs to `<dir>/.codex/skills`, which is useful for Codex versions that discover repository-scoped skills.

When it finishes, `install.py` reminds you to **start a new Claude Code / Codex session** (skills are discovered at session start) and to run the self-test.

## 4. Option B: Claude Code plugin marketplace

This repository is also a Claude Code plugin marketplace (`.claude-plugin/marketplace.json`). Inside Claude Code:

```text
/plugin marketplace add <owner>/zotero-word-live-citations
```

```text
/plugin install zotero-word-live-citations@zotero-word-live-citations
```

The first command registers the marketplace from GitHub. The second installs the plugin named `zotero-word-live-citations` from the marketplace named `zotero-word-live-citations`. Restart Claude Code or start a new session afterwards.

With a local clone you can also add the marketplace from a path:

```text
/plugin marketplace add ./zotero-word-live-citations
```

> [!TIP]
> Plugin installs live inside Claude Code's plugin cache, not in `~/.claude/skills`. To run the self-test by hand, use the copy in your clone: `python skills/zotero-word-live-citations/scripts/selftest.py`.

**Codex plugin manifest.** The repository also contains `.codex-plugin/plugin.json` (with `"skills": "./skills/"`) and `skills/zotero-word-live-citations/agents/openai.yaml` for Codex plugin tooling. The supported, tested path for Codex is still Option A or C.

## 5. Option C: manual copy

Copy the folder `skills/zotero-word-live-citations/` so that `SKILL.md` ends up at one of:

| Agent | Path |
|---|---|
| Claude Code (personal) | `~/.claude/skills/zotero-word-live-citations/SKILL.md` |
| Claude Code (one project) | `<project>/.claude/skills/zotero-word-live-citations/SKILL.md` |
| Codex | `~/.codex/skills/zotero-word-live-citations/SKILL.md` (or `$CODEX_HOME/skills/…`) |

bash / zsh:

```bash
mkdir -p ~/.claude/skills
```

```bash
cp -R skills/zotero-word-live-citations ~/.claude/skills/
```

PowerShell:

```powershell
New-Item -ItemType Directory -Force "$HOME\.claude\skills"
```

```powershell
Copy-Item -Recurse skills\zotero-word-live-citations "$HOME\.claude\skills\"
```

The `tests/` folder is not needed at runtime. You may delete it from the copy.

## 6. Verify the installation

1. **Files exist:**

   ```bash
   ls ~/.claude/skills/zotero-word-live-citations
   ```

   You should see `SKILL.md`, `agents/`, `references/`, `scripts/`.

2. **Self-test.** Start Zotero first:

   ```bash
   python ~/.claude/skills/zotero-word-live-citations/scripts/selftest.py
   ```

   PowerShell:

   ```powershell
   python "$HOME\.claude\skills\zotero-word-live-citations\scripts\selftest.py"
   ```

   Expected: `[OK ]` for `python`, `zotero-running`, `zotero-local-api`, `zotero-read-items`, `docx-pipeline`, and `microsoft-word` on Windows with Office. Add `--json` for machine-readable output, or `--strict` to exit 1 unless Zotero is readable.

3. **New agent session.** Open a new Claude Code / Codex session and ask: *"Do you have the zotero-word-live-citations skill? What does it do?"* In Codex you can also reference it as `$zotero-word-live-citations`.

## 7. Updating

**`install.py` installs:**

```bash
git pull
```

```bash
python install.py --target claude --force
```

Use `--target codex` or `--target both` as appropriate. Without `--force`, `install.py` lists what changed and stops. Start a new session afterwards.

**Marketplace installs** (inside Claude Code):

```text
/plugin marketplace update zotero-word-live-citations
```

Then update or reinstall the plugin from the `/plugin` menu, and restart.

**Manual copies:** delete the old folder and copy the new one.

## 8. Uninstalling

```bash
python install.py --target claude --uninstall
```

```bash
python install.py --target both --uninstall --dry-run
```

`--uninstall` refuses to delete a directory that does not contain `SKILL.md`, as a safety check.

Marketplace installs (inside Claude Code):

```text
/plugin uninstall zotero-word-live-citations@zotero-word-live-citations
```

```text
/plugin marketplace remove zotero-word-live-citations
```

Uninstalling the skill does **not** touch your Zotero library, your documents, or items imported earlier (those carry the `zwlc-import` tag if you used it).

<a id="python-discovery"></a>
## 9. Python discovery

The agent chooses `PY` once per task: the **first** of `python3`, `python`, `py -3` whose `--version` prints ≥ 3.9. On Windows it skips the Microsoft Store stub. Codex users may also use the Codex-bundled runtime:

```text
~/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python      (macOS/Linux)
%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe   (Windows)
```

If none is found, the agent asks you to install Python and does nothing else.

Check what you have:

```bash
python3 --version
```

```bash
python --version
```

```bash
py -3 --version
```

## 10. Per-OS notes

### Windows

- Use real Python from python.org. `py -3` is the most reliable command. Disable the Store alias if `python` opens the Store (Settings → Apps → Advanced app settings → App execution aliases).
- PowerShell vs bash: environment variables are `$env:NAME = "value"` in PowerShell and `export NAME="value"` in bash. Paths may use `\` or `/`.
- Chinese paths and file names are fine. The scripts force UTF-8 console output. If a legacy console shows garbled Chinese, see [troubleshooting.md § Windows encoding](troubleshooting.md#windows-encoding-and-chinese-paths).
- `word_render.py` (PDF rendering) needs Microsoft Word and PowerShell. Word is found in the standard `Program Files` / `Program Files (x86)` folders `Microsoft Office\…\Office16` (or `Office15`) first. If it is not there, the script uses the path Word registers under the Windows registry key `App Paths\Winword.exe` (HKLM, then HKCU), which covers other install locations.

### macOS

- Use `python3`. Everything except `word_render.py` works. PDF rendering is Windows-only and reported as "not available".
- Zotero and Word may ask for automation/accessibility permissions the first time the Word add-in runs. Allow them.
- Field-code toggle in Word: **Option+F9** (may need **fn**).

### Linux

- Use `python3`. Zotero Desktop runs on Linux. Microsoft Word does not, so run Refresh on a Windows or macOS machine with Word and the Zotero add-in. Do **not** use LibreOffice to refresh or re-save the output (see [manual-steps.md § A1](manual-steps.md#a1-open-the-output-in-microsoft-word)).
- `word_render.py` is not available.
