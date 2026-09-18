# zotero-word-live-citations

[English](README.md)

这是一个同时适用于 **Claude Code** 和 **OpenAI Codex** 的技能（skill）。它能把草稿变成带 **Zotero 活引用** 的 Word 文档。文档里写入的是真正的 `ADDIN ZOTERO_ITEM CSL_CITATION` / `ZOTERO_BIBL` 域，Zotero 的 Word 插件之后可以对它们刷新、切换样式和编辑，而不是纯文本的 `[1]`。

整个流程分五步：

1. **查找文献**：检索 OpenAlex、PubMed 和 Crossref，为每个论断挑出能支撑它的论文。
2. **匹配 Zotero**：在本地 Zotero Desktop 文库中查找对应条目，依次按 DOI、PMID、题名+作者+年份匹配。有歧义的匹配不会自动选择。
3. **导入缺失条目（须经你批准）**：缺失的文献生成 RIS 文件，导入到 Zotero 中当前选中的集合。导入前会先告诉你条数和目标集合，你确认后才执行。
4. **写入活引用域**：把引用域、参考文献表域和文档偏好写入 DOCX 的**副本**，原文件不会被改动。
5. **验证**：每次都做结构验证。在 Windows 上还可以用 Word 渲染成 PDF 检查版面。Zotero **Refresh** 需要你在 Word 中手动点击。

所有脚本只使用 Python 3.9+ 标准库，不会自动安装任何依赖。

## 环境要求

| | 用途 |
|---|---|
| Python ≥ 3.9 | 全部功能 |
| Zotero 7+ 桌面版正在运行，且已开启「设置 → 高级 → 允许此计算机上的其他应用程序与 Zotero 通讯」（本地 API：`http://127.0.0.1:23119/api/`） | 条目匹配、导入 |
| Microsoft Word + Zotero Word 插件 | 手动 Refresh；可选的 PDF 渲染（仅 Windows） |
| 联网 | 仅文献检索需要 |

## 安装

```bash
git clone https://github.com/<owner>/codex-zotero-wordcitation.git
```

```bash
cd codex-zotero-wordcitation
```

安装到 **Claude Code**（`~/.claude/skills/`）：

```bash
python install.py --target claude
```

安装到 **Codex**（`$CODEX_HOME/skills/`，默认 `~/.codex/skills/`）：

```bash
python install.py --target codex
```

其他安装选项：
- `--target both`：同时安装到两个平台。
- `--project <目录>`：安装到指定项目的 `.claude/skills`，而不是用户主目录。
- `--dry-run`：只预览，不做改动。
- `--uninstall`：卸载。
- 如果目标位置已有不同版本，安装器会列出差异，需要加 `--force` 才会覆盖。

也可以用 **Claude Code 插件市场**安装，在 Claude Code 中执行：

```text
/plugin marketplace add <owner>/codex-zotero-wordcitation
/plugin install zotero-word-live-citations@zotero-word-live-citations
```

安装后请开启一个新会话。在技能的安装目录中运行下面的命令，检查环境是否就绪：

```bash
python scripts/selftest.py
```

## 使用

直接用自然语言向 agent 提出需求即可，例如：

- “为 `draft.md` 中的每个论断查找支撑文献，生成带 Zotero 活引用（Vancouver 格式）的 Word。”
- “把 `refs.ris` 里的文献按标记位置插入 `manuscript.docx`，要 Zotero 引用。”
- “检查 `thesis.docx` 里的 Zotero 引用域是否有效。”

agent 会按 [`SKILL.md`](skills/zotero-word-live-citations/SKILL.md) 的流程执行。向 Zotero 导入条目之前，它会先说明要导入几条、导入到哪个集合，等你回复“同意”后才会导入。

### 最小手动示例

```bash
S=skills/zotero-word-live-citations/scripts
python $S/search_literature.py search "PD-1 blockade melanoma" --source openalex,pubmed --limit 5 --out candidates.json
python $S/resolve_references.py --references candidates.json --out map.json
python $S/md_to_docx.py --input draft.md --output draft.docx          # draft.md 中含 [@ref:C1; @ref:C3] 这样的标记
python $S/insert_zotero_fields.py --input draft.docx --items map.json --placeholders --style gb-t-7714-numeric --locale zh-CN --bibliography-heading "参考文献" --report report.json
python $S/validate_zotero_docx.py draft-zotero-cited.docx --baseline draft.docx --require-item-data --expect-bibliography --json
```

最后在 Word 中打开 `draft-zotero-cited.docx`，点击 **Zotero → Refresh**。

## 安全保证

- 不会覆盖输入的 DOCX。输出文件名为 `<原名>-zotero-cited.docx`，报告中会给出输入和输出两个文件的 SHA-256。
- 未经你明确同意，不会新建、修改、合并或删除任何 Zotero 条目。
- 只引用父条目，不引用附件或笔记。URI 取自条目所在的文库，不会混用不同文库的命名空间。
- 不会伪造 `formattedCitation`/`plainCitation`，这两项由 Zotero 在 Refresh 时生成。
- 最终报告把“结构验证”“Word 渲染”“Zotero Refresh”三项结果分开列出。

## 开发

```bash
cd skills/zotero-word-live-citations/tests
```

```bash
python -m unittest discover
```

## 许可

本项目采用 MIT 许可，见 [LICENSE](LICENSE)。部分代码改编自 [drguptavivek/zotero-use](https://github.com/drguptavivek/zotero-use) 和 [openai/plugins](https://github.com/openai/plugins)（均为 MIT 许可），各自改编了哪些部分见 [NOTICE](NOTICE)。
