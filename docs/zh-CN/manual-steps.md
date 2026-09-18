# 手动步骤：只有你能完成的事

[English](../en/manual-steps.md) · [返回 README](../../README.zh-CN.md)

检索、匹配、生成文件、写入引用域和验证，都由 agent 自动完成。但有几件事是**有意留给你亲自做的**：有的需要安装软件，而本技能不会替你安装；有的会改动你的 Zotero 文库；有的属于学术判断；Zotero Refresh 则只能在 Word 里运行。本页按你遇到它们的先后顺序逐一列出，并说明每一步为什么重要、具体怎么做。

> [!IMPORTANT]
> 标为**必需**的步骤如果跳过，流程要么报错停止，要么产出不符合预期的文档。标为*建议*或*可选*的步骤是额外的安全保障。

## 目录

- [快速清单](#quick-checklist)
- [首次使用前](#before-first-use)
  - [B1. 安装 Python ≥ 3.9](#b1)
  - [B2. 运行 Zotero 桌面版并允许本地通讯](#b2)
  - [B3. 安装 Zotero Word 插件](#b3)
  - [B4. 引文样式（可选）](#b4)
  - [B5. 登录 Zotero 账号（通常已完成，出问题时再处理）](#b5)
  - [B6. 可选的环境变量](#b6)
  - [B7. 安装技能、新开会话、运行自检](#b7)
- [每次任务](#for-every-task)
  - [T1. 保护原稿](#t1)
  - [T2. 审阅所选文献](#t2)
  - [T3. 处理有歧义的匹配和重复条目](#t3)
  - [T4. 导入之前：先选中目标集合，再批准](#t4)
  - [T5. 审阅不确定的引用位置](#t5)
- [生成文档之后](#after-the-output)
  - [A1. 用 Microsoft Word 打开输出文件](#a1)
  - [A2. 点击 Zotero → Refresh（刷新）](#a2)
  - [A3. 检查格式，必要时更换样式](#a3)
  - [A4. 撤销导入（如有需要）](#a4)
  - [A5. 分享或投稿之前](#a5)
- [菜单名称对照：英文 ↔ 中文界面](#menu-names)

---

<a id="quick-checklist"></a>
## 快速清单

可以复制到笔记里，逐项打勾。

**首次使用前（每台电脑一次）**

- [ ] **B1** 已安装 Python ≥ 3.9（没有的话 agent 会引导你从 python.org 下载），`python --version`（或 `py -3 --version`）能正常输出版本号。*必需*
- [ ] **B2** Zotero 7+ 正在运行，已勾选“允许此计算机上的其他应用程序与 Zotero 通讯”，并已把勾选后的设置页**截图发给 agent**。*必需*
- [ ] **B3** 已在 Microsoft Word 中安装 Zotero 插件，并重启了 Word。*Refresh 时必需*
- [ ] **B4** 引文样式无需提前准备，之后可在 Word 的“文档首选项”中自行更换。*可选*
- [ ] **B5** Zotero 已登录 zotero.org 账号（大多数用户已登录；agent 检测到未登录时才会提醒你）。*出现问题时必需*
- [ ] **B6** 已设置 `ZWLC_MAILTO` / `NCBI_API_KEY`。*可选*
- [ ] **B7** 已安装技能、新开 agent 会话，`selftest.py` 全部 OK。*必需*

**每次任务**

- [ ] **T1** 已备份原稿，且没有他人正在编辑它。*建议*
- [ ] **T2** 已审阅“论断 → 文献”清单。*必需（这是你的责任）*
- [ ] **T3** 已处理有歧义的匹配（用 `zoteroKey` 锁定），已知悉重复条目。*出现时必需*
- [ ] **T4** 已**在 Zotero 窗口中选中**目标集合，确认条数和目标后明确回复“同意”。*每次导入前必需*
- [ ] **T5** 已审阅低置信度的引用位置（placements 模式）。*出现时必需*

**生成文档之后**

- [ ] **A1** 已用 **Microsoft Word** 打开输出文件（**不支持 WPS**，也不用 LibreOffice / Pages）。*必需*
- [ ] **A2** 已点击 **Zotero → Refresh（刷新）**，并处理了弹出的对话框。*必需*
- [ ] **A3** 已检查样式、编号和参考文献表；如需更换样式，已通过“文档首选项”修改。*必需*
- [ ] **A4** 已通过 `zwlc-import` 标签删除不需要的导入条目。*可选*
- [ ] **A5** 已妥善处理定稿或分享用的副本（做好备份；只在投稿副本上取消链接引用）。*建议*

---

<a id="before-first-use"></a>
## 首次使用前

<a id="b1"></a>
### B1. 安装 Python ≥ 3.9

**为什么。** 所有脚本都基于 Python 3.9+ 标准库。**本技能不会安装任何东西**，包括 Python 本身和任何第三方包。

**怎么做。**

| 系统 | 推荐方式 |
|---|---|
| Windows | 从 [python.org](https://www.python.org/downloads/) 下载安装，并勾选 *Add python.exe to PATH*。安装程序还会附带 `py` 启动器。 |
| macOS | 从 python.org 安装，或用 Homebrew 安装（`brew install python`），命令为 `python3`。 |
| Linux | 使用发行版自带的 `python3`（3.9 或更高）。 |

检查：

```bash
python --version
```

```bash
py -3 --version
```

> [!WARNING]
> **Windows：微软商店的 “python” 别名。** 在新装的 Windows 上输入 `python`，可能会打开微软商店，或提示 *“Python was not found; run without arguments to install from the Microsoft Store…”*。这只是一个占位程序，并不是 Python。解决办法：按上文安装正式版 Python 并使用 `py -3`，或者关闭这个别名：**设置 → 应用 → 高级应用设置 → 应用执行别名**，关闭 `python.exe` 和 `python3.exe`。

> [!TIP]
> **Codex 用户**的电脑上可能已经有 Codex 自带的 Python，位于 `~/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python`（Windows 上为 `python.exe`）。在没有系统 Python 时，技能说明允许 agent 使用它。

agent 会依次尝试 `python3`、`python`、`py -3`，选用第一个版本 ≥ 3.9 的。如果都不行，agent 会**引导你完成安装**：给出 python.org 下载地址，提醒 Windows 用户勾选 *Add python.exe to PATH*，装好后请你重开终端 / agent 会话再确认版本。它不会自己动手安装。

<a id="b2"></a>
### B2. 运行 Zotero 桌面版并允许本地通讯

**为什么。** 匹配和导入都要与你电脑上的 Zotero 桌面版通信，地址为 `http://127.0.0.1:23119`（本地 API：`http://127.0.0.1:23119/api/`）。这个接口默认关闭，需要你手动开启，而且只在 Zotero 运行时可用。

**怎么做。**

1. 从 [zotero.org](https://www.zotero.org/download/) 安装 **Zotero 7 或更高版本**。实测使用的是 Zotero 10.0.2。
2. 启动 Zotero，并在 agent 工作期间保持运行。
3. 打开设置：
   - Windows / Linux：**编辑 → 设置**（Edit → Settings）
   - macOS：**Zotero → 设置…**（Zotero → Settings…）
4. 进入**高级**（Advanced），在**杂项**（Miscellaneous）下勾选
   **“允许此计算机上的其他应用程序与 Zotero 通讯”**
   （**"Allow other applications on this computer to communicate with Zotero"**）。
5. **把勾选后的设置页截图发给 agent。** 本地 API 是本技能的必需条件，agent 会先看截图确认已勾选，再运行下面的检查复核；没有这一步不会进入匹配和导入。
6. 关闭设置窗口。一般不需要重启；如果下面的检查仍然失败，再重启 Zotero。

**检查。** `$S` 指技能的 `scripts/` 目录，例如 `~/.claude/skills/zotero-word-live-citations/scripts`（见 [usage.md § 约定](usage.md#conventions)）：

```bash
python "$S/zotero_local.py" status
```

应当看到 `"apiReachable": true` 和 `"itemsReadable": true`。如果 `connectorReachable` 为 true 而 `apiReachable` 为 false，说明上面的选项没有勾选，或者 Zotero 版本低于 7。`selftest.py` 也会做同样的检查（`zotero-running`、`zotero-local-api`、`zotero-read-items`）。

> [!NOTE]
> 本地 API 只监听 `127.0.0.1`，其他电脑无法访问，也不需要 API 密钥或密码。本技能从不修改 Zotero 设置，这个选项需要你自己勾选。

<a id="b3"></a>
### B3. 安装 Zotero Word 插件

**为什么。** 活引用域必须靠 Word 中的 Zotero 插件来刷新。没有插件，Word 里就没有 Zotero 选项卡，也就无法 Refresh。

**怎么做。**

1. 在 Zotero 中打开：**设置 → 引用 → 文字处理软件**（Settings → Cite → Word Processors）。
2. 点击**安装 Microsoft Word 加载项**（Install Microsoft Word Add-in）；如果已经装过，点击**重新安装**（Reinstall）。
3. **完全退出并重新启动 Word。** 功能区中应出现 **Zotero** 选项卡。

在 macOS 上，请允许 Word 或 Zotero 弹出的权限请求。如果选项卡没有出现，请参阅 [troubleshooting.md § Word 中的 Zotero Refresh](troubleshooting.md#zotero-refresh-in-word)。

<a id="b4"></a>
### B4. 引文样式（可选）

**不需要提前准备。** 生成后可以随时在 Word → Zotero → **文档首选项** 中更换成任何已安装的样式。技能写入的样式 ID（例如 `china-national-standard-gb-t-7714-2015-numeric`）只是初始值；如果它没安装，Refresh 时 Zotero 会尝试下载或让你另选一个。

**如需安装新样式。** Zotero → **设置 → 引用 → 样式**（Settings → Cite → Styles）→ 点击 **+** 或**获取更多样式…**（Get additional styles…）→ 搜索，例如 “GB/T 7714” 或期刊名称 → 安装。确认样式已经出现在列表中。

<a id="b5"></a>
### B5. 登录 Zotero 账号（通常已完成，出问题时再处理）

**大多数用户无需操作。** agent 会通过 `zotero_local.py status`（`"loggedIn"`）或 `selftest.py`（`zotero-logged-in`）自动检查。只有检测到未登录，或匹配时出现 *“cannot verify library namespace … local-only/unsynced”*，agent 才会请你按下面的步骤登录。

**怎么做（仅在 agent 提示时）。**

1. 如果还没有账号，在 [zotero.org](https://www.zotero.org/user/register) 免费注册一个。
2. Zotero → **设置 → 同步**（Settings → Sync），输入用户名和密码登录（密码只在 Zotero 里输入，**不要发给 agent**）。
3. 点击 Zotero 窗口右上角的同步按钮，同步一次。
4. **把显示已登录账号的同步页截图发给 agent**，agent 会重新检查并继续匹配。

以下是背后的原因，以及群组文库的说明。

**为什么。** Zotero 引用中保存着一个 URI，例如 `http://zotero.org/users/<id>/items/<KEY>` 或 `http://zotero.org/groups/<id>/items/<KEY>`。技能根据条目所在的文库生成这个 URI，而且**只在文库有真实的数字 ID 时才会生成**。这个 ID 要在与 zotero.org 同步后才会有。

| 文库 | 结果 |
|---|---|
| 个人文库，至少同步过一次 | 正常（`users/<id>`） |
| **从未同步过的个人文库（纯本地）** | 匹配时**拒绝**：条目会被归入 `missing`，原因为 *“cannot verify library namespace … local-only/unsynced”* |
| 群组文库 | 使用 `--library group:<id>` 匹配时正常（`groups/<id>`） |

**纯本地文库的解决办法：** 按上面的步骤登录并同步一次，然后重新匹配。（如果文档中已有 Zotero 生成的引用域，其中带有该条目的 URI，那个 URI 同样有效；技能只是不会凭空编造 URI。）

**群组文库。** 先用 `zotero_local.py groups` 列出群组，再用 `resolve_references.py --library group:<id> …` 匹配。请注意：

- 要导入的集合必须是你**有编辑权限**的，只读目标会被拒绝。
- 对于 map 中*没有*的 key，`[@zotero:KEY]` 标记只会在你的**个人**文库中查找。群组条目请先匹配进 map。
- `insert_zotero_fields.py` 每次运行只接受一个 map。如果要在同一次运行中同时引用个人文库和群组文库的条目，需要你自己把两个 map 的 `resolved` 部分合并到一个文件里。

<a id="b6"></a>
### B6. 可选的环境变量

| 变量 | 使用者 | 作用 |
|---|---|---|
| `ZWLC_MAILTO` | `search_literature.py` | 你的邮箱，作为 `mailto` 发给 Crossref 和 OpenAlex（进入它们的 “polite pool”，更稳定，更少被限流） |
| `NCBI_API_KEY` | `search_literature.py` | NCBI E-utilities 密钥，可提高 PubMed 的请求上限（没有密钥时请控制在每秒约 3 次） |
| `ZOTERO_LOCAL_BASE_URL` | 所有 Zotero 相关脚本 | 非默认的 Zotero 地址（默认 `http://127.0.0.1:23119`） |

bash / zsh（写入 `~/.bashrc` / `~/.zshrc` 可永久生效）：

```bash
export ZWLC_MAILTO="you@example.org"
```

```bash
export NCBI_API_KEY="your-ncbi-key"
```

PowerShell（仅当前会话）：

```powershell
$env:ZWLC_MAILTO = "you@example.org"
```

PowerShell（为当前用户永久设置）：

```powershell
[Environment]::SetEnvironmentVariable("ZWLC_MAILTO", "you@example.org", "User")
```

设置后请重启终端和 agent 会话。**只有文献检索需要联网**，匹配、导入、写入引用域和验证都在本机完成。

<a id="b7"></a>
### B7. 安装技能、新开会话、运行自检

安装方法见 [installation.md](installation.md)。安装后请**新开一个 Claude Code / Codex 会话**，因为技能是在会话启动时加载的。然后运行：

```bash
python ~/.claude/skills/zotero-word-live-citations/scripts/selftest.py
```

每一行都应显示 `[OK ]`。在 macOS / Linux 上 `microsoft-word` 可能显示 `NO`，这只意味着无法渲染 PDF。

---

<a id="for-every-task"></a>
## 每次任务

<a id="t1"></a>
### T1. 保护原稿

**为什么。** 技能总是写入**副本**（`<原名>-zotero-cited.docx`），并拒绝覆盖输入文件。但你自己的操作习惯同样重要。

**怎么做。**

- 重要稿件请保留备份或版本历史。
- **绝不要让 agent 覆盖原稿**，也不要把输出文件重命名成原稿的名字。
- **共享文档**（OneDrive / SharePoint / Teams 协同编辑、和导师共享的学位论文等）：先与合作者沟通。在副本上操作，未经同意不要刷新或另存别人的文档。
- 请 agent 重新生成之前，**先在 Word 中关闭输出文件**。被 Word 占用的文件无法替换；而且输出文件已存在时，除非使用 `--force`，脚本会拒绝写入。

<a id="t2"></a>
### T2. 审阅所选文献

**为什么。** agent 只能引用检索或查询工具真实返回的论文，也绝不会编造 DOI。**但一篇论文是否真能支撑你的论断，属于学术判断，这个判断由你负责。**

**怎么做。** 当 agent 展示“论断 → 文献”清单时：

- 每篇至少读一下题名和摘要；关键论断请查看全文。
- 注意文献类型：具体研究发现应引用原始研究，概括性表述可以引用综述。
- 留意已撤稿的论文、你不愿引用的预印本，以及发展迅速的领域中已经过时的研究。
- 随时可以要求替换，例如 *“请引用 2010 年的原始临床试验，而不是那篇综述”*。

<a id="t3"></a>
### T3. 处理有歧义的匹配和重复条目

**为什么。** 当一条参考文献可能对应文库中的多个条目时，技能**绝不会替你选择**。

**怎么做。** agent 会列出 `ambiguous` 中的候选条目（key、题名、年份、第一作者、得分）。告诉它哪一条是对的，它会在该参考文献记录中加上 `"zoteroKey": "ABCD1234"` 来锁定这一条，然后重新匹配。你也可以自己在 Zotero 中查找：选中条目后，key 就在条目 URI 中。

`duplicates` 表示你文库中有多个条目共用同一个 DOI/PMID。技能不会合并或删除它们。如果想整理，请使用 Zotero 左侧栏中的**重复条目**（Duplicate Items）。

<a id="t4"></a>
### T4. 导入之前：先选中目标集合，再批准

> [!CAUTION]
> **Zotero connector 会把条目导入 Zotero 窗口中当前选中的集合。** 没有可以指定集合的参数。如果你当前选中的是“未分类条目”或某个无关的项目文件夹，新条目就会进到那里。

**怎么做。**

1. 在 Zotero 中为这次导入**新建一个专用集合**（右键点击“我的文库” → *新建分类…* / New Collection…），例如 `agent 导入`，或者像实测中那样命名为 `肿瘤免疫测试`。
2. **单击选中**这个集合。
3. agent 运行 `zotero_local.py selected-target` 后会告诉你类似这样的话：*“18 条记录 → 文库 My Library 中的集合 肿瘤免疫测试，是否导入？”*
4. **核对条数和目标，然后明确回复“同意”。** “继续加引用吧”这样的话*不算*对导入的批准，agent 会明确地单独询问你。
5. agent 导入时会带上 `--expect-target "<集合名>"`。如果你在此期间点了别的集合，导入会被**拒绝**（退出码 2）。请重新选中并再次确认。

> [!TIP]
> agent 用 `--tag zwlc-import` 生成 RIS 时（推荐的默认做法），所有导入的记录都会带上 **`zwlc-import`** 标签，方便日后查找、检查或撤销（见 [A4](#a4)）。

想先看看要导入的记录？用任意文本编辑器打开生成的 `missing.ris` 即可，它是纯文本文件。

<a id="t5"></a>
### T5. 审阅不确定的引用位置

**为什么。** 在没有标记的现成文本中添加引用（`placements.json` 模式），或者把旧稿中的引用迁移到新稿时，有些位置可能无法确定。

**怎么做。** agent 会先试运行（dry run），并展示每个引用位置的上下文（`...前文 <<CITE>> 后文...`）。相似度较低（约低于 0.8）、句子被拆分或合并、或者论断在新稿中已消失的位置，都会单独列出来给你看。请逐一确认、调整或删除。agent 绝不会为了让锚点对上而改动你的正文。

---

<a id="after-the-output"></a>
## 生成文档之后

<a id="a1"></a>
### A1. 用 Microsoft Word 打开输出文件

> [!WARNING]
> **本技能不支持 WPS。** 请使用装有 Zotero 插件的 **Microsoft Word**。**不要用 WPS、LibreOffice、Pages 或在线转换工具打开并保存输出文件。** 如果电脑默认用 WPS 打开 `.docx`，请右键文件 → 打开方式 → Word。 它们可能把 Zotero 域变成纯文本，引用就不再“活”了。万一发生这种情况，请退回到最近一个完好的副本。

<a id="a2"></a>
### A2. 点击 Zotero → Refresh（刷新）

> [!IMPORTANT]
> **Refresh 永远不会自动执行。** 刷新之前，文中引用和参考文献表的文字都是**临时的**：简单的 `[1]` 或 `(作者, 年份)` 标签，以及一份类似 Vancouver 格式的简易列表。刷新后，Zotero 会按你选定的样式重新排版全部内容。

**怎么做。**

1. 在 Word 中打开 `<原名>-zotero-cited.docx`。
2. 功能区：**Zotero** 选项卡 → **Refresh**（刷新）。
3. 等待完成。文档较大时可能需要一些时间。

**可能出现的对话框：**

| 对话框 | 怎么处理 |
|---|---|
| *“You have modified this citation since Zotero generated it…”*（你在 Zotero 生成此引文后修改了它） | 有人改过某个域的显示文字。通常选择 **No（否）** 保留 Zotero 的版本，或撤销那处修改。如果大量出现，请停下来报告问题，不要一路点过去。 |
| *“… item not found in your library / could not be found”*（在文库中找不到该条目） | 该引用来自其他文库，例如合作者的文库。内嵌的 `itemData` 能保证它继续可用。除非你确实想这么做，否则不要重新关联。 |
| 样式选择窗口（文档首选项） | 选择样式并确认。 |

如果 agent 刚生成的引用在 Refresh 时被提示**已修改或找不到条目**，请停下来，记下是哪一处引用并报告（见 [troubleshooting.md](troubleshooting.md#zotero-refresh-in-word)）。

<a id="a3"></a>
### A3. 检查格式，必要时更换样式

检查引文样式、编号顺序，以及参考文献表是否完整、顺序是否正确。

**更换样式**随时都可以：**Zotero 选项卡 → Document Preferences（文档首选项）** → 选择样式（和语言）→ 确定。Zotero 会重新排版整篇文档。生成时选定的样式只是一个起点。

> [!TIP]
> 看到的是 `{ ADDIN ZOTERO_ITEM CSL_CITATION {...} }` 而不是引文？那是 Word 的域代码视图。按 **Alt+F9**（macOS：**Option+F9** / **fn+Option+F9**）即可切换回来。

<a id="a4"></a>
### A4. 撤销导入（如有需要）

本技能**从不删除** Zotero 中的任何东西。如需删除导入的条目：

1. 在 Zotero 中选中文库（或目标集合）。
2. 在左侧栏底部的**标签选择器**中，点击 **`zwlc-import`**。
3. 检查列出的条目；如果其中有些你在别处也引用了，请把它们从选择中去掉。
4. 选中条目 → **移到回收站…**（Move Item to Trash…）或按 Delete 键。
5. 之后可以按需清空回收站。

仍在某篇文档中被引用的条目，在该文档里依然可用，因为引用域中内嵌了 `itemData`。只是 Refresh 时会提示它们不在你的文库中。

> [!WARNING]
> **绝不要把同一个 RIS 文件导入两次。** Zotero connector 不会去重，第二次运行 `import-ris` 会把每个条目再建一份副本，之后 `resolve_references.py` 会把这些文献报告为 `ambiguous` / `duplicates`。再次导入之前，务必先重新运行 `resolve_references.py`，只导入仍处于 `missing` 状态的文献。
>
> **如果已经重复导入了：** 点击 `zwlc-import` 标签，按**添加日期**（Date Added）排序，删除多余的副本，或用**重复条目**（Duplicate Items）合并。**请保留已经被文档引用的那些副本**，它们的 key 记录在 `report.json`（`placements[].keys`）和 `reference-map.json`（`resolved.<refId>.key`）中。处理完后重新运行 `resolve_references.py`。另见 [troubleshooting.md § 导入](troubleshooting.md#importing)。

<a id="a5"></a>
### A5. 分享或投稿之前

- 把带活引用的版本保留为你的工作稿。
- 有些期刊要求纯文本引用：在 Word 中点击 **Zotero → Unlink Citations（取消链接引用）**，把域转换为静态文本。**请只在单独的投稿副本上这样做**，因为这一步无法再变回活引用。
- 把文档交给合作者时，请提醒他们使用装有 Zotero 插件的 Word，不要用 WPS / LibreOffice / Pages。

---

<a id="menu-names"></a>
## 菜单名称对照：英文 ↔ 中文界面

不同版本的 Zotero 和 Word 界面文字略有差异，找最接近的即可。

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
