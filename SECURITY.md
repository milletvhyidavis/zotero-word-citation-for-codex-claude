# Security Policy · 安全策略

[English](#english) · [简体中文](#简体中文)

## English

### Security model

- **Zotero access is local only.** The scripts talk to Zotero Desktop at `http://127.0.0.1:23119` (override: `ZOTERO_LOCAL_BASE_URL` / `--base-url`). The local API and connector only listen on the loopback interface. No Zotero web API key, account password or other credential is used, requested or stored.
- **Reads by default, one approval-gated write.** The only operation that changes Zotero is `zotero_local.py import-ris|import-bibtex`. It refuses without `--yes`, refuses non-editable targets, and with `--expect-target` refuses if the selected collection differs. The skill never edits, moves, merges or deletes Zotero items and never changes Zotero preferences.
- **Documents.** The input DOCX is never overwritten. Output is written to a temporary file and then moved into place. ZIP part names are checked for unsafe paths during validation.
- **Network.** Only `search_literature.py` uses the internet, calling `api.openalex.org`, `eutils.ncbi.nlm.nih.gov` and `api.crossref.org` over HTTPS. Your search queries, plus `ZWLC_MAILTO` (Crossref/OpenAlex) and `NCBI_API_KEY` (NCBI) if you set them, are sent to these services. **Do not put confidential manuscript text into search queries.** There is no telemetry.
- **Word rendering** (`word_render.py`, Windows) runs a fixed PowerShell script that opens a temporary read-only copy of the document in Word via COM and closes it without saving.
- **No dependencies.** Python standard library only. Nothing is downloaded or installed.

### Supported versions

| Version | Supported |
|---|---|
| 1.0.x | yes |

### Reporting a vulnerability

Please **do not open a public issue** for security problems.

1. Preferably use GitHub's private vulnerability reporting: `https://github.com/<owner>/zotero-word-live-citations/security/advisories/new` (repository → **Security** → **Report a vulnerability**).
2. If that is unavailable, open a minimal public issue asking a maintainer for a private contact channel, without technical details.

Include the affected version, OS, a description, reproduction steps and the impact. Remove personal data and confidential documents. We aim to acknowledge reports within 7 days and to publish a fix or mitigation as soon as practical, crediting reporters who wish to be named.

## 简体中文

### 安全模型

- **只在本机访问 Zotero。** 脚本通过 `http://127.0.0.1:23119` 与 Zotero 桌面版通信（可用 `ZOTERO_LOCAL_BASE_URL` 或 `--base-url` 修改地址）。本地 API 和 connector 只监听回环地址。整个过程不使用、不索取、也不保存 Zotero Web API 密钥、账户密码或其他任何凭据。
- **默认只读，唯一的写操作须经批准。** 唯一会修改 Zotero 的操作是 `zotero_local.py import-ris|import-bibtex`：没有 `--yes` 时拒绝执行；目标不可写时拒绝执行；使用 `--expect-target` 时，如果 Zotero 中当前选中的集合与之不符也会拒绝。本技能不会编辑、移动、合并或删除 Zotero 条目，也不会修改 Zotero 设置。
- **文档。** 绝不覆盖输入的 DOCX。输出先写入临时文件，再移动到目标位置。验证时会检查 ZIP 内部路径是否存在不安全的写法。
- **网络。** 只有 `search_literature.py` 需要联网，通过 HTTPS 访问 `api.openalex.org`、`eutils.ncbi.nlm.nih.gov` 和 `api.crossref.org`。发送的内容包括你的检索词，以及你设置了的 `ZWLC_MAILTO`（发给 Crossref/OpenAlex）和 `NCBI_API_KEY`（发给 NCBI）。**请不要把未公开的稿件内容写进检索词。** 本项目没有任何遥测。
- **Word 渲染**（`word_render.py`，仅 Windows）运行一段固定的 PowerShell 脚本，通过 COM 在 Word 中以只读方式打开文档的临时副本，完成后不保存直接关闭。
- **零依赖。** 只使用 Python 标准库，不下载、不安装任何东西。

### 支持的版本

| 版本 | 是否支持 |
|---|---|
| 1.0.x | 是 |

### 报告漏洞

安全问题请**不要提交公开 issue**。

1. 首选 GitHub 的私密漏洞报告：`https://github.com/<owner>/zotero-word-live-citations/security/advisories/new`（仓库 → **Security** → **Report a vulnerability**）。
2. 如果该功能不可用，可以提交一个简短的公开 issue，请维护者提供私下联系方式，但不要写任何技术细节。

报告中请写明受影响的版本、操作系统、问题描述、复现步骤和影响范围，并删去个人信息和保密文档。我们会尽量在 7 天内确认收到，并尽快发布修复或缓解措施；如果你愿意署名，我们会在致谢中注明。
