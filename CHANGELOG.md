# Changelog · 更新日志

All notable changes to this project are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses [Semantic Versioning](https://semver.org/).

本文件记录项目的所有重要变更，格式参照 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，版本号遵循[语义化版本](https://semver.org/lang/zh-CN/)。

## [Unreleased]

### Changed (English)

- First-use setup: enabling Zotero's local API is now a **required** step, confirmed by a screenshot the user sends the agent. Zotero sign-in is checked automatically; the user is asked to sign in (with a screenshot) only when it is missing. The agent guides Python installation from python.org when none is found. **WPS is explicitly unsupported.** Citation styles no longer need to be installed in advance.
- `zotero_local.py status` reports `loggedIn` / `userLibraryId`; `selftest.py` adds a `zotero-logged-in` check.

### Fixed (English)

- Requests to the local Zotero server no longer go through `HTTP(S)_PROXY` (previously failed when a proxy was set without `NO_PROXY`).
- `[@doi:…]` with an unparsable DOI no longer silently cites an unrelated item that has no DOI.
- A pinned `zoteroKey` that does not exist now lands in `missing` instead of aborting the whole run with "Zotero not reachable".
- `build_import_file.py` no longer exports references that are already in the library but not citable (e.g. unsynced library), which would have created duplicates.
- Author–date provisional text shows `n.d.` for items without a year; the report shows the document's real style when existing Zotero preferences are kept.

### 变更（中文）

- 首次使用：开启 Zotero 本地 API 改为**必需**步骤，用户需把设置截图发给 agent；Zotero 登录状态由 agent 自动检查，仅在未登录时才请用户登录并截图；找不到 Python 时由 agent 引导用户从 python.org 安装；明确**不支持 WPS**；引文样式无需提前安装。
- `zotero_local.py status` 新增 `loggedIn` / `userLibraryId`；`selftest.py` 新增 `zotero-logged-in` 检查。

### 修复（中文）

- 访问本地 Zotero 不再经过 `HTTP(S)_PROXY`（此前设置了代理但未设置 `NO_PROXY` 时会连接失败）。
- `[@doi:…]` 中的 DOI 无法解析时，不再静默引用一篇没有 DOI 的无关文献。
- 锁定的 `zoteroKey` 不存在时，归入 `missing`，而不是以“Zotero not reachable”中止整个匹配。
- `build_import_file.py` 不再导出“已在文库中但无法引用”的条目（例如未同步文库），避免重复导入。
- 作者–年份临时文字在缺少年份时显示 `n.d.`；保留原有 Zotero 首选项时，报告中显示文档实际使用的样式。

## [1.0.0] — 2026-09-18

Initial public release. · 首个公开版本。

### Added (English)

- Agent skill `zotero-word-live-citations` for **Claude Code** and **OpenAI Codex** (`SKILL.md`, reference docs, `agents/openai.yaml`).
- `search_literature.py`: `search` across OpenAlex, PubMed and Crossref, with records merged by DOI/PMID, and `lookup` for canonical metadata by DOI/PMID. Supports `ZWLC_MAILTO` and `NCBI_API_KEY`.
- `resolve_references.py`: read-only matching of JSON/RIS/plain-text references to Zotero parent items (pinned `zoteroKey` > DOI > PMID > exact title > title + author + year). Ambiguous matches are never auto-picked, and duplicates are reported. Group libraries are supported via `--library group:<id>`.
- `build_import_file.py`: RIS/BibTeX for missing references, with optional tags (e.g. `zwlc-import`).
- `zotero_local.py`: `status`, `search`, `item`, `collections`, `groups`, `selected-target`, and approval-gated `import-ris` / `import-bibtex` (`--yes`, `--expect-target`).
- `md_to_docx.py`: minimal Markdown → DOCX with CJK font support, keeping citation markers.
- `insert_zotero_fields.py`: real `ADDIN ZOTERO_ITEM CSL_CITATION` fields with embedded `itemData`, a `ZOTERO_BIBL` bibliography field and `ZOTERO_PREF_n` document preferences, written into a copy (`<stem>-zotero-cited.docx`). Supports placeholder mode, `placements.json` mode, `--list-paragraphs`, `--dry-run`, style aliases (incl. GB/T 7714-2015) and any CSL style URL, self-validation and a JSON report.
- `validate_zotero_docx.py`: structural validation of DOCX packages and Zotero fields, including baseline preservation, `itemData` coverage, namespace, bibliography and style checks.
- `word_render.py`: optional Word COM rendering to PDF on Windows (read-only copy, no Refresh).
- `selftest.py`: environment and capability check.
- `install.py`: installer for Claude Code (`~/.claude/skills`), Codex (`$CODEX_HOME/skills`) or a project folder, with `--dry-run`, `--force` and `--uninstall`.
- Claude Code plugin/marketplace manifests (`.claude-plugin/`) and a Codex plugin manifest (`.codex-plugin/`).
- Bilingual documentation (English / Simplified Chinese): README, installation, usage, manual-steps checklist, troubleshooting, FAQ, publishing guide, contributing and security policy.
- Unit test suite (38 tests, standard library `unittest`).

### Verified

- End-to-end on Windows 11 + Zotero 10.0.2 + Word 16 (Microsoft 365) with the Zotero Word add-in: 18 references imported with approval and matched by DOI, 17 citation fields + bibliography in GB/T 7714-2015 numeric (zh-CN), structural validation passed, Word rendering passed, and **Zotero Refresh in Word succeeded**.

### 新增（中文）

- 同时适用于 **Claude Code** 和 **OpenAI Codex** 的技能 `zotero-word-live-citations`（`SKILL.md`、参考文档、`agents/openai.yaml`）。
- `search_literature.py`：`search` 可同时检索 OpenAlex、PubMed、Crossref，结果按 DOI/PMID 合并；`lookup` 按 DOI/PMID 获取权威元数据。支持 `ZWLC_MAILTO` 和 `NCBI_API_KEY`。
- `resolve_references.py`：只读地把 JSON / RIS / 纯文本参考文献匹配到 Zotero 父条目，优先级为指定 `zoteroKey` > DOI > PMID > 题名精确匹配 > 题名 + 作者 + 年份。有歧义时绝不自动选择，重复条目只报告不处理。可用 `--library group:<id>` 匹配群组文库。
- `build_import_file.py`：为缺失文献生成 RIS/BibTeX，可附加标签（如 `zwlc-import`）。
- `zotero_local.py`：提供 `status`、`search`、`item`、`collections`、`groups`、`selected-target`，以及须经批准才执行的 `import-ris` / `import-bibtex`（`--yes`、`--expect-target`）。
- `md_to_docx.py`：简易 Markdown → DOCX，支持中文字体，保留引用标记。
- `insert_zotero_fields.py`：在文档副本（`<原名>-zotero-cited.docx`）中写入真正的 `ADDIN ZOTERO_ITEM CSL_CITATION` 域（内嵌 `itemData`）、`ZOTERO_BIBL` 参考文献表域和 `ZOTERO_PREF_n` 文档偏好。支持标记模式、`placements.json` 模式、`--list-paragraphs`、`--dry-run`、样式别名（含 GB/T 7714-2015）及任意 CSL 样式 URL，写入后自动校验并输出 JSON 报告。
- `validate_zotero_docx.py`：检查 DOCX 结构和 Zotero 域，包括原有引用是否保留、`itemData` 覆盖率、文库命名空间、参考文献表和样式。
- `word_render.py`：Windows 上可选的 Word COM 渲染，导出 PDF（只读副本，不执行 Refresh）。
- `selftest.py`：检查运行环境和可用功能。
- `install.py`：可安装到 Claude Code（`~/.claude/skills`）、Codex（`$CODEX_HOME/skills`）或项目目录，支持 `--dry-run`、`--force`、`--uninstall`。
- Claude Code 插件 / 插件市场清单（`.claude-plugin/`）和 Codex 插件清单（`.codex-plugin/`）。
- 中英双语文档：README、安装、使用、手动步骤清单、故障排查、FAQ、发布指南、贡献指南和安全策略。
- 单元测试 38 个（标准库 `unittest`）。

### 实测验证

- 在 Windows 11 + Zotero 10.0.2 + Word 16（Microsoft 365）+ Zotero Word 插件环境下完成端到端测试：18 篇文献经用户批准后导入并全部按 DOI 匹配成功，生成 17 个引用域和参考文献表，样式为 GB/T 7714-2015 顺序编码制（zh-CN）。结构验证通过，Word 渲染通过，**用户在 Word 中执行 Zotero Refresh 成功**。

[1.0.0]: https://github.com/milletvhyidavis/zotero-word-live-citations/releases/tag/v1.0.0
