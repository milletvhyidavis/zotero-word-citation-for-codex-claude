# 使用指南

[English](../en/usage.md) · [返回 README](../../README.md)

本指南按脚本逐一讲解整个流程：每一步做什么、哪些参数要紧、会写出什么文件、哪些地方需要你亲自检查。这些命令通常不需要你手动输入，agent 会替你运行，但了解它们仍然有用：你可以核查 agent 做了什么，手动重跑某一步，或者完全不借助 agent 直接使用这些脚本。

## 目录

- [1. 全局概览](#big-picture)
- [2. 如何向 agent 提需求](#talking-to-the-agent)
- [3. 本文约定](#conventions)
- [4. 第 0 步：检查环境（`selftest.py`）](#step-0)
- [5. 第 1 步：检索文献（`search_literature.py`）](#step-1)
- [6. 第 2 步：与 Zotero 文库匹配（`resolve_references.py`）](#step-2)
- [7. 第 3 步：导入缺失条目（`build_import_file.py`、`zotero_local.py`）](#step-3)
- [8. 第 4 步：准备 DOCX（`md_to_docx.py`）](#step-4)
- [9. 第 5 步：写入活引用域（`insert_zotero_fields.py`）](#step-5)
- [10. 第 6 步：验证（`validate_zotero_docx.py`）](#step-6)
- [11. 第 7 步：用 Word 渲染（`word_render.py`，仅 Windows）](#step-7)
- [12. 第 8 步：你在 Word 中执行 Zotero Refresh](#step-8)
- [13. 引文样式与语言](#styles)
- [14. 最终报告](#final-report)
- [15. 退出码](#exit-codes)
- [16. 实例：肿瘤免疫学中文综述](#worked-example)
- [17. 其他使用场景](#other-scenarios)

---

<a id="big-picture"></a>
## 1. 全局概览

```text
文献检索 ─► Zotero 条目（key + URI + CSL itemData）─► DOCX 中的 Zotero 域 ─► 你在 Word 中点击 Refresh
```

| # | 步骤 | 脚本 | 是否写入 Zotero | 由谁操作 |
|---|---|---|---|---|
| 0 | 环境检查 | `selftest.py` | 否 | agent |
| 1 | 检索文献 | `search_literature.py` | 否 | agent。**你审阅“论断 → 文献”清单。** |
| 2 | 与文库匹配 | `resolve_references.py` | 否 | agent。**你处理有歧义的匹配。** |
| 3 | 导入缺失条目 | `build_import_file.py`、`zotero_local.py import-ris` | **是** | **你选中集合并回复“同意”。** |
| 4 | Markdown → DOCX（可选） | `md_to_docx.py` | 否 | agent |
| 5 | 在副本中写入活引用域 | `insert_zotero_fields.py` | 否 | agent |
| 6 | 结构验证 | `validate_zotero_docx.py` | 否 | agent |
| 7 | 渲染 PDF（可选） | `word_render.py` | 否 | agent（仅限 Windows + Word） |
| 8 | Zotero Refresh | 无 | 否 | **你，在 Microsoft Word 中** |

> [!IMPORTANT]
> 第 1–3 步和第 8 步涉及只有你才能做的决定。agent 会在第 3 步停下来询问你，并且从不执行第 8 步。完整清单见 [manual-steps.md](manual-steps.md)。

<a id="talking-to-the-agent"></a>
## 2. 如何向 agent 提需求

用平常的话说就行。下面是一些效果不错的说法：

- *“用 Markdown 写一篇约 1500 字的 X 主题综述，用 `[@ref:ID]` 标记引用位置，为每个论断查找支撑文献，最后给我一份带 Zotero 活引用、GB/T 7714 顺序编码制（zh-CN）的 Word 文档。”*
- *“为 `draft.md` 中的每个论断查找支撑文献，生成带 Zotero 活引用（Vancouver 格式）的 Word。”*
- *“把 `refs.ris` 里的文献按标记位置插入 `manuscript.docx`，要 Zotero 引用。”*
- *“合作者发来了 `chapter3.docx`。请在我下面列出的几句话后面插入这五个 DOI 的引用，正文一个字都不要改。”*
- *“检查 `thesis.docx` 里的 Zotero 引用域是否有效。”*

在 **Codex** 中，可以用 `$zotero-word-live-citations` 显式指定本技能。在 **Claude Code** 中，只要你的请求符合技能描述，就会自动调用；你也可以直接点名要求使用它。

哪些事 agent 会自己做，哪些会先问你：

| agent 自己完成 | agent 先征求你的意见 |
|---|---|
| 检索、阅读摘要、提出“论断 → 文献”清单 | 所选文献是否合适（你应当审阅） |
| 把参考文献与你的文库匹配（只读） | 匹配有歧义时用哪个候选条目 |
| 生成 RIS 文件 | **是否把 N 条记录导入集合 X**（等你明确回复“同意”） |
| 写出输出副本、验证、渲染 PDF | 是否用 Word 渲染（可选） |
| 撰写最终报告 | 无。**Refresh 永远留给你来做。** |

<a id="conventions"></a>
## 3. 本文约定

- `S` 表示已安装技能的 `scripts/` 目录，例如 `~/.claude/skills/zotero-word-live-citations/scripts`；如果在本仓库的克隆中使用，则为 `skills/zotero-word-live-citations/scripts`。
- 示例中统一写 `python`。如果你的电脑上可用的是 `python3` 或 `py -3`，请自行替换。见 [installation.md § Python](installation.md#python-discovery)。
- 中间文件（候选文献、map、报告）请放在文档旁边的工作目录中，例如 `zotero-work/`，不要放进技能目录。
- 每个脚本都支持 `--help`。

bash / zsh：

```bash
S=~/.claude/skills/zotero-word-live-citations/scripts
```

```bash
python "$S/selftest.py"
```

Windows PowerShell：

```powershell
$S = "$HOME\.claude\skills\zotero-word-live-citations\scripts"
```

```powershell
python "$S\selftest.py"
```

路径请加引号。路径中含空格或中文都没问题。

<a id="step-0"></a>
## 4. 第 0 步：检查环境（`selftest.py`）

```bash
python "$S/selftest.py"
```

输出示例：

```text
[OK ] python: 3.12.4 at C:\...\python.exe
[OK ] zotero-running: Zotero 10.0.2
[OK ] zotero-local-api: local API enabled
[OK ] zotero-read-items: read one item key
[OK ] docx-pipeline: insert + validate OK
[OK ] microsoft-word: C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE
capabilities: literatureSearch=yes, zoteroSearchResolve=yes, zoteroImport=yes, docxInsertValidate=yes, markdownToDocx=yes, wordRendering=yes
```

| 参数 | 含义 |
|---|---|
| `--json` | 机器可读输出（`checks` + `capabilities`） |
| `--strict` | 只有 Zotero 条目可读**且**离线 DOCX 流程通过时才返回 0，否则返回 1 |
| `--base-url URL` | Zotero 本地服务地址（默认 `http://127.0.0.1:23119` 或 `$ZOTERO_LOCAL_BASE_URL`） |

自检是只读的：不安装任何东西，不修改任何 Zotero 设置，也不输出文库内容。离线流程检查会在临时目录里生成一个用完即删的 DOCX。

某项检查失败意味着什么：

| 失败的检查 | 失去的功能 | 仍可使用的功能 |
|---|---|---|
| `zotero-running` / `zotero-local-api` / `zotero-read-items` | 匹配和导入 | 文献检索、DOCX 验证、Markdown → DOCX |
| `microsoft-word` | 仅 PDF 渲染 | 其他全部功能，引用域照常可用 |
| `docx-pipeline` | 写入引用域 | 请先排查再继续（通常是 Python 安装损坏） |

<a id="step-1"></a>
## 5. 第 1 步：检索文献（`search_literature.py`）

有两个子命令，都是只读的，只使用公开 API。

### `search`：关键词检索

```bash
python "$S/search_literature.py" search "cancer immunoediting elimination equilibrium escape" --source openalex,pubmed --limit 8 --out zotero-work/q1.json
```

| 参数 | 默认值 | 含义 |
|---|---|---|
| `query`（位置参数） | | 3–7 个实义词；在国际数据库中用英文检索效果最好 |
| `--source` | `openalex,pubmed` | 逗号分隔，可选 `openalex`、`pubmed`、`crossref` |
| `--limit` | `10` | **每个来源**返回的结果数 |
| `--from-year` | | 只要该年份及以后发表的文献 |
| `--out` | 标准输出 | 写入的 JSON 文件 |
| `--brief` | 关 | 不含摘要（文件更小） |
| `--mailto`（全局参数，写在子命令之前） | `$ZWLC_MAILTO` | 发给 Crossref / OpenAlex 的联系邮箱（“polite pool”） |
| `--timeout`（全局参数） | `20` | 每个 HTTP 请求的超时秒数 |

| 来源 | 适用场景 |
|---|---|
| `openalex` | 覆盖面广，有摘要和被引次数 |
| `pubmed` | 生物医学，有 PMID，元数据质量高。设置 `$NCBI_API_KEY` 可提高请求上限。 |
| `crossref` | DOI 注册机构，覆盖所有学科，元数据权威 |

多个来源的结果会按 DOI/PMID 合并，并在每个输出文件内编号为 `C1`、`C2`……。某个来源失败时只会给出警告，其他来源照常返回结果。只有所有来源都失败且一条结果都没有时，退出码才为 1。

输出记录格式（匹配脚本和生成导入文件的脚本都使用这种格式）：

```json
{"refId": "C1", "title": "...", "authors": [{"family": "Dunn", "given": "Gavin P."}],
 "year": "2004", "journal": "Annual Review of Immunology", "volume": "22", "issue": "1",
 "pages": "329-360", "doi": "10.1146/annurev.immunol.22.012703.104803", "pmid": "15032581",
 "abstract": "...", "url": "...", "type": "article-journal", "sources": ["openalex", "pubmed"]}
```

### `lookup`：按已知标识符获取权威元数据

```bash
python "$S/search_literature.py" lookup --doi 10.1056/NEJMoa1003466 --pmid 15032581 --out zotero-work/lookup.json
```

`--doi` 和 `--pmid` 都可以重复使用。凡是来自记忆、同事或其他工具的 DOI，都要先用 `lookup` 核实。**lookup 失败的文献一律不用。**

> [!WARNING]
> **文献的学术选择由你负责。** agent 不得引用任何工具都没有返回过的论文，也不得编造 DOI。但一篇论文是否真能支撑你的论断，仍需你来判断。在导入或写入之前，请认真阅读 agent 给出的“论断 → 文献”清单。

### 把多次检索的结果合并成一个 `refs.json`

每个检索结果文件都从 `C1` 开始编号，所以不同文件之间的 ID 会重复。当你（或 agent）从多次检索中挑选文献时，要把选中的记录复制到同一个 JSON 列表里，并给每条记录一个唯一的 `refId`。最简单的做法是直接用稿件中的标记 ID，例如 `[@ref:editing]` 对应 `"refId": "editing"`。记录的其余部分保持不变。

```json
[
  {"refId": "editing", "title": "The Three Es of Cancer Immunoediting", "doi": "10.1146/annurev.immunol.22.012703.104803", "...": "..."},
  {"refId": "ipi", "title": "Improved Survival with Ipilimumab in Patients with Metastatic Melanoma", "doi": "10.1056/NEJMoa1003466", "...": "..."}
]
```

<a id="step-2"></a>
## 6. 第 2 步：与 Zotero 文库匹配（`resolve_references.py`）

```bash
python "$S/resolve_references.py" --references zotero-work/refs.json --out zotero-work/reference-map.json
```

| 参数 | 含义 |
|---|---|
| `--references` | 输入文件：`.json`（记录列表或 `{"references": [...]}`）、`.ris`，或 `.txt`/`.md`（每行一条已排版的参考文献；能识别 `1.`、`[1]`、`1)` 这类编号） |
| `--out` | 要写出的 reference map（必填） |
| `--library` | `user`（默认）或 `group:<id>`（群组 ID 可用 `zotero_local.py groups` 查看） |
| `--base-url` | Zotero 本地服务地址 |

匹配顺序（由强到弱）：

1. **指定 key**：输入记录中的 `"zoteroKey": "ABCD1234"` 字段（仅 JSON 输入支持）
2. **DOI** 精确匹配
3. **PMID** 精确匹配（从条目的 *Extra*（其他）字段读取，例如 `PMID: 12345678`）
4. **规范化后的题名**精确匹配
5. **模糊题名** + 第一作者 + 年份（年份冲突时不做模糊匹配）

附件、笔记和批注永远不会被匹配，只匹配顶层的父条目。

> [!IMPORTANT]
> **有歧义的匹配绝不自动选择。** 例如：文库中两个条目共用一个 DOI、多个条目题名相同，或者两个模糊候选的得分很接近。这些都会归入 `ambiguous`，agent 会把候选条目展示给你。要选定其中一条，就在输入 JSON 的对应记录中加上 `"zoteroKey"`，然后重新运行：
>
> ```json
> {"refId": "ipi", "title": "...", "doi": "10.1056/NEJMoa1003466", "zoteroKey": "ABCD1234"}
> ```
>
> 疑似重复的条目会报告在 `duplicates` 中，但绝不会被合并或删除。如需合并，请自己在 Zotero 中处理（左侧栏的*重复条目*）。

脚本会在标准错误输出一行摘要：

```text
references=18 resolved=18 missing=0 ambiguous=0 duplicates=0 -> zotero-work/reference-map.json
```

### `reference-map.json` 的结构

```jsonc
{
  "generatedAt": "2026-09-18T06:55:00+00:00",
  "zoteroBaseUrl": "http://127.0.0.1:23119",
  "library": "user",
  "totalReferences": 18,
  "resolved": {
    "editing": {
      "key": "ABCD1234",                                   // Zotero 条目 key（父条目）
      "uri": "http://zotero.org/users/<id>/items/ABCD1234", // 根据条目所在文库生成
      "itemData": { "id": "...", "type": "article-journal", "title": "..." }, // Zotero 输出的 CSL-JSON
      "title": "The Three Es of Cancer Immunoediting",
      "year": "2004",
      "doi": "10.1146/annurev.immunol.22.012703.104803",
      "matchMethod": "doi",                                // manual | doi | pmid | title | title-fuzzy
      "score": 1.0
    }
  },
  "missing":   [ {"refId": "...", "title": "...", "doi": "...", "reason": "...", "nearest": [ ... ]} ],
  "ambiguous": [ {"refId": "...", "title": "...", "reason": "...", "candidates": [
                   {"key": "...", "title": "...", "year": "...", "firstAuthor": "...",
                    "similarity": 0.93, "score": 0.98, "yearMatch": true, "authorMatch": true, "accept": true} ]} ],
  "duplicates": [ {"refId": "...", "keys": ["KEY1", "KEY2"]} ],
  "libraryNamespaces": ["users/<id>"],
  "references": [ /* 你的输入记录（已规范化） */ ]
}
```

退出码：全部匹配成功为 0；有缺失或歧义时为 1（map 照常写出）；输入有误或无法连接 Zotero 时为 2。

<a id="step-3"></a>
## 7. 第 3 步：导入缺失条目（`build_import_file.py`、`zotero_local.py`）

这是**唯一会写入 Zotero 的步骤**，每次都需要你明确批准。

### 7.1 生成导入文件（不写入）

```bash
python "$S/build_import_file.py" --map zotero-work/reference-map.json --format ris --out zotero-work/missing.ris --tag zwlc-import
```

| 参数 | 含义 |
|---|---|
| `--map` | reference map（必填） |
| `--format` | `ris`（默认）或 `bibtex` |
| `--out` | 要写出的文件（必填） |
| `--ref-id` | 只导出这些 refId（可重复）。默认导出 `missing` 中的全部条目。 |
| `--tag` | 给每条记录加一个 Zotero 标签（可重复）。**请使用 `zwlc-import`**，方便日后查找、检查或撤销导入。 |

没有题名的记录会被跳过并报告，不会凭空补全任何内容。你可以打开 `.ris` 文件看看，它是纯文本。

### 7.2 查看条目会导入到哪里

```bash
python "$S/zotero_local.py" selected-target
```

```json
{
  "libraryID": 1,
  "libraryName": "My Library",
  "libraryEditable": true,
  "id": 168,
  "name": "肿瘤免疫测试"
}
```

> [!CAUTION]
> **Zotero connector 会把条目导入 Zotero 窗口中当前选中的文库或集合。** 没有“集合”参数。**批准之前，请先在 Zotero 左侧栏中点击你想要的集合**，例如一个专用的测试集合。如果选中的是文库根目录，`name` 就是文库名称（例如 *My Library* / *我的文库*）。

接着 agent 会告诉你类似 *“18 条记录 → 文库 My Library 中的集合 肿瘤免疫测试，是否导入？”* 的信息，并**等待你明确回复同意**。“加上引用”**不等于**批准导入。

### 7.3 导入（写入）

```bash
python "$S/zotero_local.py" import-ris --file zotero-work/missing.ris --expect-target "肿瘤免疫测试" --yes
```

| 参数 | 含义 |
|---|---|
| `--file` | RIS 文件（`import-bibtex` 则为 BibTeX 文件） |
| `--expect-target NAME` | 如果当前选中的集合或文库名称不完全等于 `NAME`，就拒绝导入（退出码 2）。这样即使你批准后选中项变了，也不会导错地方。 |
| `--yes` | 表示你已批准这次导入。不加时脚本只显示*将要*执行的操作并拒绝执行（退出码 2）。 |

如果选中的目标不可编辑，脚本同样会拒绝。成功时输出 `requestedRecords`、`target`、`session` 和 `connectorReportedItems`。**这个返回结果并不能证明导入成功**，下一步必须重新匹配。

### 7.4 重新匹配

```bash
python "$S/resolve_references.py" --references zotero-work/refs.json --out zotero-work/reference-map.json
```

新导入的条目现在应当能匹配上，通常是按 DOI。如果某个导入的条目仍在 `missing` 中，可能是 Zotero 还在建立索引，请等几秒钟再运行一次。仍然失败的会如实报告为失败。**绝不会猜测 key 或 URI。**

> [!TIP]
> **撤销导入：** 在 Zotero 左下角的标签选择器中点击 `zwlc-import` 标签，选中这些条目，移到回收站。技能本身从不删除任何东西。见 [manual-steps.md § 撤销导入](manual-steps.md#a4)。

### `zotero_local.py` 的其他子命令（只读）

| 子命令 | 作用 |
|---|---|
| `status` | API 和 connector 是否可连接、Zotero 版本，出问题时给出提示。仅当条目可读时退出码为 0。 |
| `search "<文本>" [--library user\|group:<id>] [--limit N] [--everything]` | 检索顶层条目。`--everything` 还会检索全文和笔记。 |
| `item KEY [--library ...]` | 单个条目的元数据 + 经过核实的 URI + CSL `itemData`。附件和笔记会被拒绝。 |
| `collections` | 列出个人文库中的集合（key、名称、上级集合） |
| `groups` | 列出本机可见的群组文库 |
| `selected-target` | Zotero 中当前选中的文库或集合 |
| `import-ris` / `import-bibtex` | 上面介绍的写入命令 |

全局参数 `--base-url` 要写在子命令之前：`zotero_local.py --base-url http://127.0.0.1:23119 status`。

<a id="step-4"></a>
## 8. 第 4 步：准备 DOCX（`md_to_docx.py`）

如果你已经有 DOCX，可以跳过这一步。如果稿件是用 Markdown 起草的：

```bash
python "$S/md_to_docx.py" --input zotero-work/review.md --output zotero-work/review.docx
```

| 参数 | 默认值 | 含义 |
|---|---|---|
| `--input` / `--output` | | 必填 |
| `--latin-font` | `Times New Roman` | 西文字体 |
| `--east-asia-font` | `SimSun` | 中文字体（例如 `SimSun` / 宋体、`Microsoft YaHei` / 微软雅黑） |
| `--force` | 关 | 覆盖已存在的输出文件 |

支持的 Markdown：`#`–`###` 标题（第一个 `#` 会成为文档标题），段落，`-`/`*` 无序列表，`1.` 编号行（按普通文本保留），`**粗体**`，`*斜体*`。表格、图片、链接和脚注**不会**被转换。引用标记会原样保留，留给下一步处理。

<a id="placeholder-syntax"></a>
### 引用标记语法

| 标记 | 含义 |
|---|---|
| `[@ref:C4]` | reference map 中的某个 refId |
| `[@ref:C4; @ref:C9]` | **一个**域同时引用两篇文献 |
| `[@zotero:ABCD1234]` 或 `[@key:ABCD1234]` | Zotero 条目 key（如果 map 中没有，会以只读方式从你的个人文库中获取） |
| `[@doi:10.1000/xyz]` | map 中已匹配的某个 DOI |

同一个标记内可以混用多种写法：`[@ref:A; @zotero:ABCD1234; @doi:10.1000/xyz]`。

标记应紧跟在论断之后。对于顺序编码制，请放在句末标点之前：`...是 T 细胞活化所必需的[@ref:C4]。` 标记文字会被原样替换；如果希望引文前有空格，请在标记前自己打一个空格。标记即使被拆分在 Word 的多个 run 中也没关系，因为查找是在段落的可见文本上进行的。

> [!NOTE]
> 只要有一个标记无法解析，比如某个 refId 在 map 中属于 `missing` 或 `ambiguous`，**整个写入过程就会中止（退出码 2，用法错误），什么都不会写出。** 请先修正 map。

<a id="step-5"></a>
## 9. 第 5 步：写入活引用域（`insert_zotero_fields.py`）

```bash
python "$S/insert_zotero_fields.py" --input zotero-work/review.docx --items zotero-work/reference-map.json --placeholders --style vancouver --bibliography-heading "References" --report zotero-work/report.json
```

### 参数

| 参数 | 默认值 | 含义 |
|---|---|---|
| `--input` | | 源 DOCX（必填，永远不会被修改） |
| `--output` | 输入文件旁的 `<原名>-zotero-cited.docx` | 必须与输入文件不同 |
| `--items` | | `reference-map.json` |
| `--placeholders` | | 替换 `[@...]` 标记（模式 1） |
| `--placements FILE` | | 按锚点文字定位（模式 2，正文不变） |
| `--style` | `vancouver` | 样式别名或任意 CSL 样式 URL，见 [§13](#styles) |
| `--locale` | `en-US` | 引文语言，例如 `zh-CN`、`de-DE` |
| `--note-type` | `0` | 仅设置文档偏好：`0` 文中引用，`1` 脚注，`2` 尾注。（本版本只插入文中引用域。） |
| `--visible` | `auto` | 临时显示文字的格式：`auto`、`numeric`、`author-date` |
| `--bibliography-heading TEXT` | | 在文字恰好等于 `TEXT` 的段落之后插入 `ZOTERO_BIBL` 域；如果没有这个标题，会在文末新建 |
| `--no-bibliography` | | 不插入参考文献表 |
| `--zotero-version` | 从 Zotero 检测，检测不到时为 `7.0` | 写入文档偏好的 `zotero-version` 属性值 |
| `--base-url` | | Zotero 本地服务地址 |
| `--list-paragraphs` | | 输出 `{"paragraphs": [{"index", "text"}]}` 后退出 |
| `--dry-run` | | 只做规划和审计，不写入任何文件 |
| `--force` | | 替换已存在的**输出**文件 |
| `--report FILE` | | 同时把 JSON 报告写到这里 |

### 会写入哪些内容

- 每个引用位置写入一个 Word 复合域：` ADDIN ZOTERO_ITEM CSL_CITATION {json} `，带一个唯一的 8 位 `citationID`。同一位置的多篇文献共用一个域；同一篇文献在两处被引用，则写入两个域。
- 每个引用条目都带有 `id`（条目 key）、`uris`（条目所在文库的 URI）和 `itemData`（Zotero 自己的 CSL-JSON）。因此即使合作者的文库里没有这个条目，引用依然可用。
- 如有需要，写入一个 `ZOTERO_BIBL` 参考文献表域。如果文档中已经有了，就保留原有的，不会重复添加。
- 在 `docProps/custom.xml` 中写入文档偏好 `ZOTERO_PREF_1..n`（样式、语言、域类型）。如果文档中已有 Zotero 偏好，则原样保留，以原有样式为准。
- **临时显示文字：** 顺序编码制样式按首次出现的顺序显示 `[1]`、`[2,3]`、`[4–6]`；著者-出版年制样式显示 `(作者, 年份)`；参考文献表显示简易的临时条目。**Zotero Refresh 会把这些全部替换**为正式格式。技能从不自行生成 `formattedCitation` / `plainCitation`。
- 只改动 `word/document.xml`、`docProps/custom.xml`、`[Content_Types].xml` 和 `_rels/.rels`，文件包中的其他部分逐字节复制。已有域内部的文字永远不会被拆开。

写入后，脚本会对照输入文件验证自己的输出。如果输入中已有 Zotero 引用，这些引用必须全部原样保留。

### `report.json`

| 字段 | 含义 |
|---|---|
| `inputDocument`、`outputDocument` | 绝对路径 |
| `inputSHA256`、`outputSHA256` | 文件哈希值 |
| `inputUnchanged` | 运行后输入文件的哈希值未变时为 `true` |
| `fieldsInserted` | 新增的引用域数量 |
| `zoteroFieldsTotal` | 输出文件中的全部引用域（原有 + 新增） |
| `citationItemOccurrences` | 所有域中被引条目的总次数 |
| `uniqueItems` | 不重复的条目 URI 数 |
| `embeddedItemData` | 例如 `18/18` |
| `libraryNamespaces` | 例如 `["users/<id>"]` 或 `["groups/<id>"]` |
| `bibliography` | `none`、`kept-existing`、`added after heading '…'`、`added at end [with new heading '…']` |
| `documentPreferences` | `added` 或 `kept-existing` |
| `style` | 写入偏好的完整 CSL 样式 ID |
| `structuralValidation` | `passed` / `failed` |
| `validationErrors`、`validationWarnings` | 列表 |
| `placements` | 每个域的 `placement`、`paragraph`、`citationID`、`keys`、`visibleText`、`context` |

使用 `--dry-run` 时，报告只有 `{"dryRun": true, "placements": [...], "bibliography": "..."}`。

<a id="mode-2"></a>
### 模式 2：`placements.json`（现成稿件，正文不能改）

适用于收到的稿件或已定稿、无法添加标记的文档。每个引用都放在一段精确的**锚点**文字旁边。

**1. 列出段落**（序号 + 可见文字）：

```bash
python "$S/insert_zotero_fields.py" --input manuscript.docx --list-paragraphs --report zotero-work/paragraphs.json
```

**2. 编写 `placements.json`：**

```json
{"placements": [
  {"id": "P1", "anchor": "is required for T-cell priming", "refs": ["C4"]},
  {"id": "P2", "anchor": "tumour mutational burden", "paragraphContains": "Biomarkers", "occurrence": 2,
   "refs": ["C7", "C9"]},
  {"id": "P3", "anchor": "Checkpoint inhibitors", "position": "before", "keys": ["ABCD1234"],
   "spaceBefore": false}
 ],
 "bibliography": {"heading": "References"}}
```

| 键 | 是否必填 | 含义 |
|---|---|---|
| `anchor` | 是 | 引文跟在这段文字之后（或之前）。在段落中已有域之外的可见文字上匹配；空白字符以及直引号与弯引号都做宽松匹配。 |
| `refs` / `keys` | 至少填一个 | map 中的 refId 和/或 Zotero key，全部放进**同一个**域 |
| `id` | 否 | 审计用的标签（默认 `P1`、`P2`……） |
| `paragraph` | 否 | 段落序号（从 0 开始），来自 `--list-paragraphs` |
| `paragraphContains` | 否 | 只在包含这段文字的段落中查找 |
| `occurrence` | 有歧义时必填 | 使用第几处匹配（从 1 开始）。锚点匹配到多处时必须填写。 |
| `position` | 否 | `after`（默认）或 `before` |
| `spaceBefore` | 否 | 是否在域前加空格。著者-出版年制默认加，顺序编码制默认不加。 |
| `noteIndex` | 否 | 必须为 `0`，暂不支持脚注引用 |
| `bibliography.heading` | 否 | 与 `--bibliography-heading` 相同；两者都有时以命令行参数为准 |

规则：锚点匹配到多处时会**报错**，除非用 `occurrence`、`paragraph` 或 `paragraphContains` 使其唯一。两个引用落在同一位置也会被拒绝，请把它们合并成一个带多个 refs 的引用。

**3. 试运行，逐条阅读 `context`**（`...前文 <<CITE>> 后文...`）：

```bash
python "$S/insert_zotero_fields.py" --input manuscript.docx --items zotero-work/reference-map.json --placements zotero-work/placements.json --style apa --dry-run
```

**4. 正式写入：** 去掉 `--dry-run`，加上 `--report`，再运行同一条命令。

> [!IMPORTANT]
> 当 agent 把旧稿中的引用迁移到新稿时，会按相似度对齐句子。相似度较低（约低于 0.8）、句子被拆分或合并，以及论断已消失的位置，都会**列出来请你审阅，而不是悄悄写入**。agent 绝不会为了让锚点对上而改动你的正文。

<a id="step-6"></a>
## 10. 第 6 步：验证（`validate_zotero_docx.py`）

```bash
python "$S/validate_zotero_docx.py" zotero-work/review-zotero-cited.docx --baseline zotero-work/review.docx --expected-increase 17 --require-item-data --expect-bibliography
```

验证器是只读的。它检查：ZIP 完整性和不安全的内部路径、XML 是否格式正确、`begin/separate/end` 域结构是否完整、引用 JSON（`citationID` 是否唯一、`noteIndex`、`citationItems`、URI、schema）、key 与 URI 是否一致、内嵌 `itemData` 的覆盖率、文库命名空间、`ZOTERO_BIBL` 域和文档偏好。

| 参数 | 含义 |
|---|---|
| `docx`（位置参数） | 要验证的文件 |
| `--baseline FILE` | 用于对比的原始文件 |
| `--expected-increase N` | 引用域数量必须恰好增加 N 个（需要 `--baseline`） |
| `--expected-field-count N` / `--minimum-fields N` | 引用域的绝对数量 |
| `--preserve-baseline-citations` | 原文件中的每个 `citationID` 及其 URI 都必须原样保留 |
| `--require-item-data` | 有任何引用条目缺少内嵌 `itemData` 即判定失败 |
| `--expect-bibliography` | 没有 `ZOTERO_BIBL` 域即判定失败 |
| `--expect-style ID` | 完整样式 ID，或其路径的最后一段（例如 `vancouver`、`china-national-standard-gb-t-7714-2015-numeric`） |
| `--expect-citation-id`、`--expect-item-key`、`--expect-visible-text` | 可重复使用的抽查项 |
| `--json` | 完整的机器可读结果 |

> [!NOTE]
> `--expected-increase` 统计的是**引用域**的数量，而不是被引文献的数量。在下面的实例中，18 篇文献分布在 17 个域里（其中一个域引用了两篇），所以这里填 17。

> [!NOTE]
> `--expect-style` 比对的是写入文档的样式 ID，而不是 `insert_zotero_fields.py` 的简短别名。`vancouver`、`apa`、`nature`、`ieee` 和 `chicago-author-date` 恰好与其 ID 的最后一段相同；而 `gb-t-7714-numeric`、`ama` 和 `harvard` 则需要传完整 ID 或 ID 的最后一段。

要检查别人发来的文档，直接运行 `validate_zotero_docx.py 对方的文档.docx --json` 即可。结果中会列出已有的域、命名空间和 `itemData` 覆盖率。

<a id="step-7"></a>
## 11. 第 7 步：用 Word 渲染（`word_render.py`，仅 Windows）

```bash
python "$S/word_render.py" zotero-work/review-zotero-cited.docx --pdf zotero-work/review-zotero-cited.pdf
```

| 参数 | 默认值 | 含义 |
|---|---|---|
| `docx`（位置参数） | | 要渲染的文档 |
| `--pdf FILE` | | 同时导出 PDF |
| `--timeout` | `180` | 超时秒数 |

脚本会把 DOCX 复制到临时目录，再通过 PowerShell COM 在隐藏的 Word 实例中以**只读**方式打开这个副本。它统计 Word 自己解析出的域（`fields`、`zoteroItemFields`、`zoteroBibliographyFields`）和页数（`pages`），可选导出 PDF，最后不保存直接关闭。输出始终为 JSON。

> [!NOTE]
> 渲染只能证明 Word 能打开这个文件并识别出其中的域。**它不会执行 Zotero Refresh，也不能证明 Refresh 一定成功。** 在 macOS 和 Linux 上会跳过这一步（退出码 2，“not available”），这是正常现象，并不说明文档有问题。

<a id="step-8"></a>
## 12. 第 8 步：你在 Word 中执行 Zotero Refresh

> [!IMPORTANT]
> **这一步永远需要手动完成。**
> 1. 用 **Microsoft Word** 打开 `<原名>-zotero-cited.docx`（不要用 WPS、LibreOffice 或 Pages）。
> 2. 点击 **Zotero** 选项卡 → **Refresh**（中文界面：**Zotero → 刷新**）。
> 3. 检查引文样式、编号和参考文献表。
>
> 刷新之前，显示的文字都是**临时的**；刷新之后，格式就完全由 Zotero 负责了。

之后想换样式，在 Word 中使用 **Zotero → Document Preferences（文档首选项）**。更多细节、各种对话框以及 Refresh 报错时的处理办法，见 [manual-steps.md § 生成文档之后](manual-steps.md#after-the-output) 和 [troubleshooting.md](troubleshooting.md#zotero-refresh-in-word)。

<a id="styles"></a>
## 13. 引文样式与语言

`--style` 支持以下别名：

| 别名 | CSL 样式 ID | 临时显示格式 |
|---|---|---|
| `vancouver`（默认） | `http://www.zotero.org/styles/vancouver` | 顺序编码 |
| `apa` | `http://www.zotero.org/styles/apa` | 著者-出版年 |
| `nature` | `http://www.zotero.org/styles/nature` | 顺序编码 |
| `ieee` | `http://www.zotero.org/styles/ieee` | 顺序编码 |
| `ama` | `http://www.zotero.org/styles/american-medical-association` | 顺序编码 |
| `chicago-author-date` | `http://www.zotero.org/styles/chicago-author-date` | 著者-出版年 |
| `harvard` | `http://www.zotero.org/styles/harvard-cite-them-right` | 著者-出版年 |
| `gb-t-7714-numeric` | `http://www.zotero.org/styles/china-national-standard-gb-t-7714-2015-numeric` | 顺序编码 |
| `gb-t-7714-author-date` | `http://www.zotero.org/styles/china-national-standard-gb-t-7714-2015-author-date` | 著者-出版年 |

**其他任何 CSL 样式也都可以用**，传入完整 ID 即可，例如 `--style http://www.zotero.org/styles/cell`。临时显示格式根据 ID 推断（ID 中含 `apa`、`author-date`、`harvard` 或 `chicago-author` 的视为著者-出版年制），也可以用 `--visible numeric|author-date` 强制指定。

> [!IMPORTANT]
> 样式必须**已经安装在你的 Zotero 中**，Refresh 才能应用它。安装位置：Zotero → 设置 → 引用 → 样式（Settings → Cite → Styles），点击 “+” 或“获取更多样式…”。GB/T 7714 和各期刊的专用样式尤其要注意这一点。

`--locale` 设置引文语言，例如 `en-US`（默认）、`en-GB`、`zh-CN`、`de-DE`。中文 GB/T 输出请使用 `--style gb-t-7714-numeric --locale zh-CN --bibliography-heading "参考文献"`。

<a id="final-report"></a>
## 14. 最终报告

每个任务结束时，agent 都会给出如下格式的报告。三项验证结果有意分开列出：

```text
Input document / Output document (absolute paths) + SHA-256 of both; input unchanged: yes/no
References: total N | matched N | missing N | ambiguous N | suspected duplicates N | imported N
Zotero fields inserted N | citation item occurrences N | unique items N | embedded itemData N/N
Library namespaces … | Bibliography field yes/no | Style …
Structural validation passed/failed | Word rendering passed/not run/failed | Zotero Refresh: left to user / passed / failed
```

各项含义：输入/输出文档路径及两者的 SHA-256、输入是否未变；参考文献总数、已匹配、缺失、有歧义、疑似重复、已导入；写入的域数、被引条目总次数、不重复条目数、内嵌 itemData 覆盖率；文库命名空间、是否有参考文献表域、样式；结构验证、Word 渲染、Zotero Refresh 三项结果。

agent 完成时，“Zotero Refresh: left to user”（留给用户）是正常状态。只有你在 Word 中执行 Refresh 之后，它才会变成 passed。

<a id="exit-codes"></a>
## 15. 退出码

所有脚本的统一约定：**0** 成功；**1** 验证失败，或 `resolve_references.py` 中存在未解析的文献（map 照常写出）；**2** 用法或环境错误，包括 `insert_zotero_fields.py` 中某个 `[@…]` 标记指向未知或未解析的文献（不写出任何文件）。

| 脚本 | 0 | 1 | 2 |
|---|---|---|---|
| `selftest.py` | Python 和 DOCX 流程正常（`--strict` 时还要求 Zotero 可读） | 某项必要检查失败 | 参数错误 |
| `search_literature.py` | 结果已写出 | 所有来源都失败 / lookup 失败 | 参数错误 / 意外错误 |
| `resolve_references.py` | 全部匹配成功 | 有缺失或歧义（map 已写出） | 输入有误、无法连接 Zotero |
| `build_import_file.py` | 文件已写出（或没有要导出的内容） | 有记录被跳过 / 没有可导出的记录 | map 无法读取 |
| `zotero_local.py` | 成功 | 连接错误、导入失败、`status` 不正常 | 拒绝执行（没有 `--yes`、`--expect-target` 不符、目标不可编辑、文件为空） |
| `md_to_docx.py` | 已写出 | | 输入不存在、输出已存在 |
| `insert_zotero_fields.py` | 已写出且结构有效 | 已写出，但验证失败 | 拒绝执行（标记无法解析、锚点有歧义、输出已存在、输入无效等），不写出任何文件 |
| `validate_zotero_docx.py` | 有效 | 无效 | 参数错误 |
| `word_render.py` | 渲染成功 | Word 出错 / 超时 | 没有 Word 或 PowerShell（非 Windows） |
| `install.py` | 完成 | 已有安装内容不同（需 `--force`）、拒绝卸载 | 找不到技能源目录 |

<a id="worked-example"></a>
## 16. 实例：肿瘤免疫学中文综述

这是一次真实的端到端运行，测试环境为 **Windows 11、Zotero 10.0.2、Word 16（Microsoft 365）+ Zotero Word 插件**。

**任务。** 一篇约 1,575 字的肿瘤免疫学中文综述，用 Markdown 起草，含 18 个 `[@ref:ID]` 标记，例如 `[@ref:editing]`、`[@ref:ipi]`、`[@ref:car]`。其中一句同时引用两篇论文：`[@ref:microbiome; @ref:microbiome2]`。输出样式为 GB/T 7714-2015 顺序编码制，语言为中文。

**1. 检索。** 共检索 15 次，例如：

```bash
python "$S/search_literature.py" search "cancer immunoediting three Es" --source openalex,pubmed --limit 4 --out q1.json
```

**2. 挑选。** 通过阅读题名和摘要，从结果中选出 18 篇论文，包括 Dunn 2004 *The Three Es of Cancer Immunoediting*（Annu Rev Immunol）、Hodi 2010 伊匹木单抗治疗转移性黑色素瘤（NEJM）、Rizvi 2015 突变图谱与非小细胞肺癌 PD-1 阻断疗效（Science）、Maude 2014 CAR-T 细胞治疗急性淋巴细胞白血病（NEJM）。选中的记录被复制到 `refs.json` 中，`refId` 取标记 ID，并去掉了摘要。

**3. 匹配。** 18 篇在文库中全部缺失：

```bash
python "$S/resolve_references.py" --references refs.json --out reference-map.json
```

**4. 生成 RIS**（18 条记录，带 `zwlc-import` 标签）：

```bash
python "$S/build_import_file.py" --map reference-map.json --format ris --out missing.ris --tag zwlc-import
```

**5. 手动步骤。** 用户在 Zotero 窗口中新建了专用集合 **肿瘤免疫测试** 并选中它。agent 检查选中项：

```bash
python "$S/zotero_local.py" selected-target
```

然后询问 *“18 条记录 → My Library 中的集合 肿瘤免疫测试，是否导入？”*，用户回复同意。

**6. 导入：**

```bash
python "$S/zotero_local.py" import-ris --file missing.ris --expect-target "肿瘤免疫测试" --yes
```

**7. 重新匹配。** 18/18 全部按 DOI 匹配成功：

```bash
python "$S/resolve_references.py" --references refs.json --out reference-map.json
```

**8. Markdown → DOCX：**

```bash
python "$S/md_to_docx.py" --input review.md --output review.docx
```

**9. 写入引用域：**

```bash
python "$S/insert_zotero_fields.py" --input review.docx --items reference-map.json --placeholders --style gb-t-7714-numeric --locale zh-CN --bibliography-heading "参考文献" --report report.json
```

`report.json` 的关键字段：

```json
{
  "inputUnchanged": true,
  "fieldsInserted": 17,
  "zoteroFieldsTotal": 17,
  "citationItemOccurrences": 18,
  "uniqueItems": 18,
  "embeddedItemData": "18/18",
  "bibliography": "added at end with new heading '参考文献'",
  "documentPreferences": "added",
  "style": "http://www.zotero.org/styles/china-national-standard-gb-t-7714-2015-numeric",
  "structuralValidation": "passed"
}
```

18 篇文献对应 17 个域，因为肠道菌群那句话只用了一个域，临时显示为 `[11,12]`。Markdown 中没有“参考文献”标题，所以在文末新建了这个标题，其后是参考文献表域。

**10. 验证：**

```bash
python "$S/validate_zotero_docx.py" review-zotero-cited.docx --baseline review.docx --expected-increase 17 --require-item-data --expect-bibliography
```

结果：通过。

**11. 渲染。** Word 成功打开文件并导出 4 页 PDF：

```bash
python "$S/word_render.py" review-zotero-cited.docx --pdf review-zotero-cited.pdf
```

**12. 手动步骤。** 用户在 Word 中打开 `review-zotero-cited.docx`，点击 **Zotero → Refresh**。**刷新成功**，Zotero 把类似 Vancouver 的临时参考文献文字替换成了 GB/T 7714-2015 格式。

最终报告：

```text
References: total 18 | matched 18 | missing 0 | ambiguous 0 | suspected duplicates 0 | imported 18
Zotero fields inserted 17 | citation item occurrences 18 | unique items 18 | embedded itemData 18/18
Library namespaces users/<id> | Bibliography field yes | Style china-national-standard-gb-t-7714-2015-numeric
Structural validation passed | Word rendering passed (4 pages) | Zotero Refresh: passed (run by the user)
```

<a id="other-scenarios"></a>
## 17. 其他使用场景

| 你手上有 | 步骤 |
|---|---|
| 一份要检查的 DOCX | `validate_zotero_docx.py doc.docx --json` |
| 条目已在 Zotero 中，正文有标记 | 匹配（或直接用 `[@zotero:KEY]` 引用）→ 写入 → 验证 |
| 一份参考文献列表（`refs.ris`、`refs.txt`）+ 带标记的 DOCX | `resolve_references.py --references refs.ris …` → 导入缺失条目（经你批准）→ 写入 → 验证 |
| 收到的稿件中已有 Zotero 引用 | 先验证原稿 → `--list-paragraphs` → `placements.json` → `--dry-run` → 写入。原有引用会自动保留并接受检查。 |
| 群组文库 | `zotero_local.py groups` → `resolve_references.py --library group:<id> …`，见 [faq.md](faq.md#group-library)。 |

在收到的文档或多人协作的文档中，来自他人文库的引用（其他的 `users/<id>` 或 `groups/<id>`）都是有效的，会原样保留。agent 不会替你在别人的文档上执行 Refresh；对于没有内嵌 `itemData` 的引用，它会给出提醒。
