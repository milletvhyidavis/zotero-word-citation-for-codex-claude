# 常见问题

[English](../en/faq.md) · [返回 README](../../README.md)

## 目录

- [总体](#general)
- [Zotero](#zotero)
- [Word 与文档](#word-and-documents)
- [文献与学术责任](#literature)
- [隐私与安全](#privacy-and-safety)

---

<a id="general"></a>
## 总体

### “活引用”到底是什么意思？

文档中包含真正的 Zotero Word 域：每处引用一个 `ADDIN ZOTERO_ITEM CSL_CITATION {...}`，参考文献表是 `ADDIN ZOTERO_BIBL … CSL_BIBLIOGRAPHY`，另外还有 `ZOTERO_PREF_n` 文档偏好。它们和你在 Word 中点击 Zotero 插件的 *Add/Edit Citation*（添加/编辑引文）时生成的东西完全一样。执行 **Zotero → Refresh** 之后，你可以像手动插入的引用一样，在 Word 中更换样式、编辑、重新编号、继续添加。纯文本的 `[1]` 做不到这些。

### 这是 Zotero、Microsoft、Anthropic 或 OpenAI 的官方产品吗？

不是。这是一个独立的开源项目。Zotero 是 Corporation for Digital Scholarship 的商标。见 [NOTICE](../../NOTICE)。

### 需要同时安装 Claude Code 和 Codex 吗？

不需要，任选其一即可。同一个技能文件夹在两者中都能用。

### 不用 AI agent，能直接用这些脚本吗？

可以。每个脚本都是普通的命令行工具，支持 `--help`。见 [usage.md](usage.md) 以及 README 中的最小手动命令示例。

### 为什么它不自动安装任何东西？

出于安全和透明的考虑。它只需要 Python 标准库，从不在你的电脑上运行 `pip`、安装程序或修改设置。装什么由你自己决定。

### 支持哪些操作系统？

凡是能运行 Python ≥ 3.9 的系统都能运行这些脚本。Zotero 桌面版支持 Windows、macOS 和 Linux。Refresh 需要装有 Zotero 插件的 Microsoft Word（Windows 或 macOS）。可选的 PDF 渲染步骤（`word_render.py`）仅支持 Windows。

<a id="zotero"></a>
## Zotero

### 为什么必须运行 Zotero 桌面版？

匹配和导入要用到 Zotero 桌面版的本地 API 和 connector，地址为 `http://127.0.0.1:23119`。只有 Zotero 在运行，并且勾选了“允许此计算机上的其他应用程序与 Zotero 通讯”时，它们才可用。

### 它会修改或删除我文库里的东西吗？

它只会**添加**条目，而且必须在你批准了确切的条数和目标集合之后。它从不编辑、移动、合并或删除条目，也不修改 Zotero 设置。要撤销导入，按 `zwlc-import` 标签筛选后自己删除即可（[manual-steps.md § A4](manual-steps.md#a4)）。

### 为什么我的导入进了错误的集合？

Zotero connector 会把条目导入 **Zotero 窗口中当前选中的集合**，没有可以指定集合的参数。请在批准**之前**选中集合。agent 会传入 `--expect-target` 以及文库和集合 ID，如果选中项变了，导入就会被拒绝。见 [manual-steps.md § T4](manual-steps.md#t4)。

<a id="group-library"></a>
### 可以引用群组文库中的条目吗？

可以。先用 `zotero_local.py groups` 列出群组，再用 `resolve_references.py --library group:<id> …` 匹配，引用中会使用 `groups/<id>` 形式的 URI。限制：对于 map 中*没有*的 key，`[@zotero:KEY]` 简写只会在你的个人文库中查找；另外每次写入只接受一个 map。见 [manual-steps.md § B5](manual-steps.md#b5)。

### 我的文库是纯本地的（从未同步过），会怎样？

匹配时会拒绝生成 URI（提示 *“cannot verify library namespace”*）。这是因为对于未同步的文库，本地 API 不提供数字用户 ID，而技能不会凭空编造。用免费的 zotero.org 账号同步一次文库，然后重新匹配即可。

### 需要哪个版本的 Zotero？

Zotero 7 或更高版本（本地 API 从 7 开始提供）。包括 Refresh 在内的端到端测试是在 Zotero 10.0.2 上验证的。

<a id="word-and-documents"></a>
## Word 与文档

### 我的原稿会被修改吗？

永远不会。输出是一个新文件 `<原名>-zotero-cited.docx`。脚本拒绝覆盖输入文件，报告中还会列出两个文件的 SHA-256 哈希值以及 `inputUnchanged: true/false`。

### 为什么点 Refresh 之前引用看起来不对？

显示的只是临时文字：`[1]`、`[2,3]` 或 `(作者, 年份)`，外加一份类似 Vancouver 格式的简易参考文献表。技能有意不去伪造 Zotero 的排版结果。在 Word 中执行 Refresh 才会生成正式格式。

### agent 能替我执行 Refresh 吗？

不能，这是有意的设计。Refresh 是在 Word 中通过 Zotero 插件运行的，它可能改写整篇文档，包括别人的文档。应当由你来执行并检查结果。

### 之后还能更换引文样式吗？

随时可以：Word → **Zotero → Document Preferences（文档首选项）** → 选择样式。该样式必须已安装在 Zotero 中。

### 支持哪些样式？

别名有：`vancouver`、`apa`、`nature`、`ieee`、`ama`、`chicago-author-date`、`harvard`、`gb-t-7714-numeric`、`gb-t-7714-author-date`。其他任何 CSL 样式都可以通过完整 ID 使用，例如 `http://www.zotero.org/styles/cell`。见 [usage.md § 13](usage.md#styles)。

### 可以用 WPS、LibreOffice 或 Pages 吗？

处理这类文件时不可以。它们可能把 Zotero Word 域转换成纯文本。输出文件请只用 Microsoft Word 打开和保存。

### 支持脚注引用吗？

暂不支持。引用都插入在正文中（`noteIndex` 为 0）。`--note-type` 只设置文档偏好。

### 能在不改动正文的情况下插入引用吗？

可以，使用 `placements.json` 模式，按精确的锚点文字定位。见 [usage.md § 模式 2](usage.md#mode-2)。

### 文档中已有的引用会保留吗？

会。已有的 Zotero 域、参考文献表和文档偏好都会保留，并自动验证是否完好。

### `md_to_docx.py` 支持哪些 Markdown 语法？

最多到 `###` 的标题、段落、无序列表、编号行（按普通文本处理）、`**粗体**`、`*斜体*`。表格、图片、链接和脚注不会被转换。版式复杂的文档，请直接在 Word 中编写，再用标记或 placements 插入引用。

<a id="literature"></a>
## 文献与学术责任

### agent 会编造参考文献吗？

技能明确禁止这样做。每篇被引论文都必须来自 `search_literature.py` 或 `lookup`，凭记忆给出的 DOI 必须通过 `lookup` 核实。尽管如此，**你**仍需确认每篇论文确实能支撑对应的论断（[manual-steps.md § T2](manual-steps.md#t2)）。

### 检索哪些数据库？

OpenAlex、PubMed（NCBI E-utilities）和 Crossref，都通过公开 API。宿主环境中的其他工具（例如 PubMed MCP 服务或网页搜索）也可以用来发现文献，但最终清单一定会经过 `lookup` 核实。

### 需要 API 密钥吗？

不需要。可选设置：`ZWLC_MAILTO`（进入 Crossref / OpenAlex 的 polite pool）和 `NCBI_API_KEY`（提高 PubMed 请求上限）。

<a id="privacy-and-safety"></a>
## 隐私与安全

### 哪些数据会离开我的电脑？

只有文献检索的检索词，以及你设置了的 `ZWLC_MAILTO` / `NCBI_API_KEY`，会发送给 OpenAlex、PubMed 和 Crossref。与 Zotero 的通信只在 `127.0.0.1` 上进行。没有任何遥测。请不要把保密内容写进检索词。见 [SECURITY.md](../../SECURITY.md)。

### 需要我的 Zotero 密码或 API 密钥吗？

不需要。本地 API 不需要任何凭据，技能也从不索要。
