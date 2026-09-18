# 故障排查

[English](../en/troubleshooting.md) · [返回 README](../../README.md)

下面每张表都按 **现象 → 原因 → 解决办法** 排列。遇到问题请先运行自检，它通常能直接指出问题所在：

```bash
python "$S/selftest.py"
```

`$S` 指技能的 `scripts/` 目录（见 [usage.md § 约定](usage.md#conventions)）。

## 目录

- [Python](#python)
- [Zotero 连接](#zotero-connection)
- [参考文献匹配](#matching-references)
- [导入](#importing)
- [文献检索与网络](#literature-search-and-network)
- [写入引用域](#inserting-fields)
- [验证与 Word 渲染](#validation-and-word-rendering)
- [Word 中的 Zotero Refresh](#zotero-refresh-in-word)
- [Windows 编码与中文路径](#windows-encoding)
- [安装](#installation)
- [仍未解决？](#still-stuck)

---

<a id="python"></a>
## Python

| 现象 | 原因 | 解决办法 |
|---|---|---|
| `Python was not found; run without arguments to install from the Microsoft Store…` | Windows 的**微软商店别名占位程序**，并不是真正的 Python | 从 python.org 安装 Python 3.9+ 并使用 `py -3`；或关闭别名：设置 → 应用 → 高级应用设置 → **应用执行别名** → 关闭 `python.exe` / `python3.exe`。Codex 用户可以使用自带的 Python（见 [installation.md](installation.md#python-discovery)）。 |
| 出现 `SyntaxError` 或 `TypeError`，提到 `list[str]` / `str \| None` | Python 版本低于 3.9 | 安装 Python ≥ 3.9，并确认实际调用的就是它（`python --version`）。 |
| `ModuleNotFoundError: _common` | 脚本被单独复制到了别处 | 请在安装后的 `scripts/` 目录中运行脚本，它们之间相互引用。 |
| agent 说找不到 Python | `python3`、`python`、`py -3` 都不可用 | 请自行安装 Python。本技能不会安装任何东西。 |

<a id="zotero-connection"></a>
## Zotero 连接

| 现象 | 原因 | 解决办法 |
|---|---|---|
| `selftest` 显示 `[NO ] zotero-running … not reachable at http://127.0.0.1:23119` | Zotero 桌面版没有运行 | 启动 Zotero 并保持打开。 |
| Zotero 在运行，但仍然连不上 | 防火墙、VPN 或代理工具拦截了 `127.0.0.1:23119`；或者 Zotero 配置了其他端口 | 允许 Zotero 的本地连接；在代理中把 `127.0.0.1` 设为直连；如果改过端口，请设置 `ZOTERO_LOCAL_BASE_URL` 或传入 `--base-url`。 |
| `zotero-running` 正常但 `zotero-local-api` 为 NO；`status` 显示 `connectorReachable: true`、`apiReachable: false`（常见 HTTP **403**） | 本地 API 未开启 | Zotero → **设置 → 高级 → 杂项** → 勾选 **“允许此计算机上的其他应用程序与 Zotero 通讯”**（Settings → Advanced → Miscellaneous → Allow other applications on this computer to communicate with Zotero）。仍不行就重启 Zotero。 |
| `/api/` 返回 404 | Zotero 6 或更早版本 | 升级到 Zotero 7+。 |
| API 正常但 `zotero-read-items` 为 NO | 文库还在加载，或数据库被锁定 | 等 Zotero 完全启动；关闭弹出的对话框；再试一次。 |
| `resolve_references.py` 报 `ERROR: Zotero not reachable: …`（退出码 2） | 运行过程中 Zotero 被关闭 | 启动 Zotero 后重新运行。这一步是只读的，可以放心重复。 |

<a id="matching-references"></a>
## 参考文献匹配

| 现象 | 原因 | 解决办法 |
|---|---|---|
| `cannot verify library namespace for item … local-only/unsynced` | 个人文库从未同步过，没有可以写进 URI 的数字用户 ID | 用 zotero.org 账号同步一次（Zotero → 设置 → 同步），然后重新匹配。或者改用群组文库中的条目。 |
| 明明 Zotero 里有这个 DOI，结果却是 `missing` | DOI 只以其他形式保存在 *Extra*（其他）或 URL 字段中，或者条目在**群组**文库里 | 把 DOI 填到条目的 DOI 字段；群组文库请用 `--library group:<id>`（`zotero_local.py groups` 可列出 ID）。也可以直接锁定：在记录中加 `"zoteroKey": "KEY"`。 |
| `ambiguous`，原因是 *“N library items share this DOI”* | 文库中有重复条目 | 选定一条，用 `"zoteroKey"` 锁定。如果愿意，可以在 Zotero 中合并重复条目（*重复条目*）。技能从不合并。 |
| `ambiguous`，原因是 *“several plausible title matches”* | 题名相似，又没有 DOI/PMID | 用 `"zoteroKey"` 锁定正确的条目，或在记录中补上 DOI。 |
| `missing`，原因是 *“no candidate passed the title/author/year threshold”*，并附有 `nearest` | 题名差异太大，或年份冲突 | 查看 `nearest`，如果其中有正确的条目就锁定它；否则说明文库里确实没有，需要导入。 |
| `pinned key … is not a citable parent item` | 填的是附件或笔记的 key | 改用父条目的 key。 |
| 纯文本参考文献列表匹配效果差 | 题名是从排版后的字符串中推测出来的 | 优先使用 `search_literature.py` / `lookup` 输出的 JSON，或 RIS；尽量带上 DOI。 |

<a id="importing"></a>
## 导入

| 现象 | 原因 | 解决办法 |
|---|---|---|
| `Refusing to write: this would import N record(s) into '…'`（退出码 2） | 缺少 `--yes`。这是有意的设计。 | agent 必须先得到你的明确批准，然后才会加上 `--yes` 重新运行。 |
| `selected Zotero target is 'X', expected 'Y'. Select the right collection in Zotero.` | Zotero 窗口中当前选中的集合与批准时的目标不一致 | 在 Zotero 中点击目标集合，然后再次批准。 |
| `selected Zotero target '…' is not editable` | 选中的是只读的群组或集合 | 选中一个你有编辑权限的集合。 |
| 导入的条目进了错误的集合 | 导入时选中的是别的集合，可能当时没用 `--expect-target` | 在 Zotero 中点击 `zwlc-import` 标签，选中这些条目，拖到正确的集合（或从错误的集合中移除）。下次请先选中集合。见 [manual-steps.md § T4](manual-steps.md#t4)。 |
| 重新匹配后，新导入的条目仍是 `missing` | Zotero 还在建立索引 | 等几秒再匹配一次。确认目标可编辑，且导入时报告了记录数。 |
| 导入后出现了与已有条目重复的条目 | 条目原本就在，但没有匹配上（例如没有 DOI） | 技能会报告重复条目，但从不删除。请在 Zotero 中用*重复条目*合并。 |
| `no RIS records found in …` | 文件为空或不是 RIS 格式 | 用 `build_import_file.py` 重新生成。 |
| `build_import_file.py` 报 `SKIPPED … no structured title` | 记录没有题名（例如来自纯文本列表） | 先查询元数据：`search_literature.py lookup --doi …`。 |
| 第二次导入后，`resolve_references.py` 把同样的文献报告为 `ambiguous`（*“N library items share this DOI”*）或列在 `duplicates` 中 | 对同一个 RIS 文件运行了两次 `import-ris`。connector 不会去重，每运行一次就新建一套副本。 | 见下方警告。 |
| 想撤销一次导入 | | 标签选择器 → `zwlc-import` → 选中 → 移到回收站。见 [manual-steps.md § A4](manual-steps.md#a4)。 |

> [!WARNING]
> **同一个 RIS 导入两次会产生重复条目。** Zotero connector 不会去重，每运行一次 `import-ris` 都会新增一整套副本。之后 `resolve_references.py` 会把这些文献报告为 `ambiguous` / `duplicates`。
>
> **在 Zotero 中这样修复：**
> 1. 在标签选择器中点击 **`zwlc-import`** 标签，按**添加日期**（Date Added）排序。
> 2. 确认哪些副本已经被你的文档引用了。它们的 key 记录在 `report.json`（`placements[].keys`）和 `reference-map.json`（`resolved.<refId>.key`）中。**请保留这些副本。**
> 3. 删除多余的副本（移到回收站），或用**重复条目**（Duplicate Items）合并，合并时把已被引用的那条设为主条目。
> 4. 重新运行 `resolve_references.py`，确认这些文献都能正常匹配。
>
> **预防办法：** 每次导入之后、再次导入之前，都要先重新运行 `resolve_references.py`。不要为了“保险”而重复导入同一个文件，新的 RIS 中只应包含仍然处于 `missing` 状态的文献。

<a id="literature-search-and-network"></a>
## 文献检索与网络

| 现象 | 原因 | 解决办法 |
|---|---|---|
| 提示 `WARNING: openalex failed: …`，但结果照常写出 | 某个来源失败，其他来源仍有返回 | 不用处理，或稍后重试。 |
| 退出码 1，所有来源都失败 | 没有网络、代理或防火墙问题，或者所有 API 都宕机了 | 检查网络连接或代理设置（脚本使用 Python `urllib` 所遵循的系统代理 / `HTTPS_PROXY` 设置）。 |
| HTTP **429** / 被限流 | 请求过多 | 脚本会在 2 秒后自动重试一次。设置 `ZWLC_MAILTO`（Crossref/OpenAlex 的 polite pool）和 `NCBI_API_KEY`（PubMed）；放慢速度；减小 `--limit`。 |
| 结果太少或不相关 | 检索词太长或太具体 | 用 3–7 个英文概念词；试试 `--source crossref`；前沿主题可以加 `--from-year`。 |
| 某个 DOI 的 `lookup` 失败 | DOI 有误，或未在 Crossref 注册 | 不要使用这条文献，改用题名检索。 |

只有文献检索需要联网，匹配、导入、写入和验证都在本机完成。

<a id="inserting-fields"></a>
## 写入引用域

| 现象 | 原因 | 解决办法 |
|---|---|---|
| `refId X is not resolved in --items map (missing/ambiguous refs cannot be cited)` | 标记指向一条尚未匹配成功的参考文献 | 导入或锁定该条目，重新匹配，再写入。本次没有写出任何文件。 |
| `DOI … is not resolved in --items map` | `[@doi:…]` 标记中的 DOI 不在 `resolved` 中 | 把这条文献加进 `refs.json` 并重新匹配。 |
| `bad placeholder token` | 标记写错了 | 使用 `[@ref:ID]`、`[@zotero:KEY]`、`[@key:KEY]`、`[@doi:10.x/y]`，多个之间用 `;` 分隔。 |
| `output exists: … (use --force to replace it)` | 之前的输出文件还在。 | 删除或重命名旧的输出文件，或加 `--force`。请先在 Word 中关闭它。 |
| `output must differ from input` | `--output` 与 `--input` 相同 | 换一个文件名。原稿永远不会被覆盖。 |
| `anchor not found` | 文字不一致（连字符与破折号、不间断空格、修订痕迹），或锚点跨越了已有的域 | 用 `--list-paragraphs` 核对；复制准确的原文；先接受或拒绝修订；缩短锚点。 |
| `anchor matches N places` | 锚点不唯一 | 加上 `occurrence`、`paragraph` 或 `paragraphContains`。 |
| `two citations target the same location` | 两个引用落在同一位置 | 合并成一个带多个 `refs` 的引用。 |
| `footnote/endnote citations are not supported yet` | `noteIndex` 不为 0 | 本版本只插入文中引用。 |
| `input DOCX fails validation; fix it first` | 输入文件本身已损坏（例如域已破损） | 用 `validate_zotero_docx.py --json` 检查；退回到一个完好的副本。 |
| 引文出现在文本框里的错误位置，或根本没出现 | 含文本框的段落被当作容器跳过 | 把锚点定在文本框内部的段落上。 |
| 参考文献表被加到了文末，而不是你的标题下面 | 标题文字与 `--bibliography-heading` 不完全相同 | 让标题文字完全一致（例如 `参考文献` 与 `参考文献：` 是不同的）。 |
| 原有的参考文献表没有被替换 | 设计如此：已有的 `ZOTERO_BIBL` 会被保留 | 不用处理，Refresh 时会更新。 |
| 文档中的样式不是你传入的那个 | 文档原本就有 Zotero 偏好，会被保留 | 在 Word 中通过 Zotero → 文档首选项修改样式。 |

<a id="validation-and-word-rendering"></a>
## 验证与 Word 渲染

| 现象 | 原因 | 解决办法 |
|---|---|---|
| `expected Zotero field count to increase by N, observed M` | `N` 填错了（它统计的是**域**，不是文献），或者写入失败 | 使用 `report.json` 中的 `fieldsInserted`。 |
| `N citation item(s) lack embedded itemData` | 引用来自其他工具或旧文档 | 只有加了 `--require-item-data` 才判定失败。这类引用要求读者的文库中有对应条目。 |
| `expected document style gb-t-7714-numeric, found …` | `--expect-style` 需要样式 ID 的最后一段，而不是别名 | 改用 `--expect-style china-national-standard-gb-t-7714-2015-numeric`。 |
| `--json` 输出中 `mixedLibraryNamespaces: true` | 引用来自多个文库 | 在合作文档中很正常，知道即可。 |
| `word_render.py`：`Microsoft Word (Windows) not available; visual check skipped`（退出码 2） | macOS/Linux；或者在标准的 `Program Files\Microsoft Office\…\Office16/15` 目录和注册表 `App Paths\Winword.exe`（HKLM/HKCU）中都找不到 Word | 非 Windows 系统上属于正常现象。在 Windows 上请确认 Word 已安装且能正常启动；修复 Office 可以恢复其注册表项。渲染是可选步骤。 |
| `word_render.py`：`Word did not finish within 180s` | Word 卡在某个对话框上（激活、安全模式、加载项提示），或文档太大 | 手动打开一次 Word，把对话框处理掉；用 `--timeout 600` 重试。 |
| `word_render.py` 返回 `ok: false` 和 COM 错误 | Word 正忙，或有隐藏的 Word 进程挂起 | 关闭所有 Word 窗口（以及任务管理器中残留的 `WINWORD.EXE`），然后重试。 |

<a id="zotero-refresh-in-word"></a>
## Word 中的 Zotero Refresh

| 现象 | 原因 | 解决办法 |
|---|---|---|
| Word 中没有 **Zotero** 选项卡 | 插件未安装或被禁用 | Zotero → 设置 → 引用 → 文字处理软件 → **（重新）安装 Microsoft Word 加载项**，然后重启 Word。在 Windows 上，还要检查 Word → 文件 → 选项 → 加载项 → *COM 加载项 / 模板* 中 Zotero 是否被禁用。 |
| Word 显示 `{ ADDIN ZOTERO_ITEM CSL_CITATION {...} }` | 打开了域代码视图 | 按 **Alt+F9**（macOS 为 **Option+F9**）。 |
| Refresh 提示 *“You have modified this citation…”* | 有人改过某个域的显示文字 | 选择 **No（否）** 保留 Zotero 的版本，或撤销那处修改。如果大量出现，请停下来报告。 |
| Refresh 提示条目 *“not found in your library”* | 引用来自其他文库（例如合作者的） | 内嵌的 `itemData` 能保证它继续可用。除非你确实想这么做，否则不要重新关联。 |
| Refresh 后样式不是预期的那个 | Zotero 中没有安装该样式 | Zotero → 设置 → 引用 → 样式 → 安装，然后在 Word → Zotero → **文档首选项** 中选择它。 |
| Refresh 时要求你选择样式 | 偏好缺失或无法读取 | 在对话框中选择样式即可。 |
| 刷新前编号看起来很奇怪 | 显示的只是临时文字 | 执行 Refresh。 |
| 别人编辑过之后，引用变成了纯文本 | 文档被 WPS / Pages / LibreOffice / 在线转换工具打开并保存过 | 退回到最近一个完好的副本；只用 Microsoft Word。 |
| Refresh 非常慢 | 文档大、引用多 | 耐心等待。在文档首选项中，存储格式请保持为“域”（Fields）。 |

<a id="windows-encoding"></a>
## Windows 编码与中文路径

| 现象 | 原因 | 解决办法 |
|---|---|---|
| 控制台中的中文显示为乱码 | 旧式 GBK（代码页 936）控制台 | 脚本输出的是 UTF-8。请使用 Windows Terminal，或先运行 `chcp 65001`，或在 PowerShell 中执行 `[Console]::OutputEncoding = [Text.Encoding]::UTF8`。写到磁盘上的文件始终是正确的 UTF-8。 |
| 用 `>` 重定向写出的 JSON 读不回来（`UnicodeDecodeError`、`JSONDecodeError`） | Windows PowerShell 5.1 的 `>` 会写成 UTF-16 | 改用脚本自带的 `--out` / `--report` 参数，不要用重定向。 |
| 读取 `refs.json` / `.md` / `.ris` 时报 `UnicodeDecodeError` | 文件保存成了 ANSI / GBK 编码 | 另存为 UTF-8（带不带 BOM 都可以）。 |
| 含空格或中文的路径出错 | 路径没加引号 | 加上引号：`"D:\论文\综述 草稿.docx"`。 |

<a id="installation"></a>
## 安装

| 现象 | 原因 | 解决办法 |
|---|---|---|
| `install.py` 报 `existing installation differs … re-run with --force`（退出码 1） | 已安装的是旧版本或改动过的副本 | 看一下列出的文件，确认后加 `--force`。 |
| `refusing to remove …: no SKILL.md` | `--uninstall` 的目标不是技能目录 | 这是安全检查。如果确定，请手动删除。 |
| agent 不认识这个技能 | 会话是在安装之前启动的，或者装错了目录 | **新开**一个会话；确认 `SKILL.md` 位于 `~/.claude/skills/zotero-word-live-citations/SKILL.md`（或 Codex 对应路径）。 |
| Codex 找不到技能 | `CODEX_HOME` 指向了别处 | 安装时让 `CODEX_HOME` 的设置与运行 Codex 时一致，或者直接复制到 `$CODEX_HOME/skills`。 |

<a id="still-stuck"></a>
## 仍未解决？

请到 `https://github.com/milletvhyidavis/zotero-word-citation-for-codex-claude/issues` 提交 issue，并附上：

- 操作系统、Python、Zotero 和 Word 的版本
- `selftest.py --json` 的输出（其中不含文库内容）
- 出错的完整命令和错误信息
- 如果是 DOCX 的问题：`validate_zotero_docx.py 文件.docx --json` 的输出。**请不要上传保密稿件。**
