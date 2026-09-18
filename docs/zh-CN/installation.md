# 安装

[English](../en/installation.md) · [返回 README](../../README.zh-CN.md)

## 目录

- [1. 前置条件](#prerequisites)
- [2. 获取代码](#get-the-code)
- [3. 方式 A：`install.py`（Claude Code 和/或 Codex）](#option-a)
- [4. 方式 B：Claude Code 插件市场](#option-b)
- [5. 方式 C：手动复制](#option-c)
- [6. 验证安装](#verify)
- [7. 更新](#updating)
- [8. 卸载](#uninstalling)
- [9. Python 的查找规则](#python-discovery)
- [10. 各操作系统注意事项](#per-os-notes)

---

<a id="prerequisites"></a>
## 1. 前置条件

| 组件 | 版本 | 用途 | 技能会替你安装吗？ |
|---|---|---|---|
| Python | ≥ 3.9（只用标准库） | 全部功能 | **不会，请自行安装** |
| Zotero 桌面版 | 7 及以上（实测 10.0.2），需保持运行，并允许本地通讯 | 条目匹配、导入 | **不会** |
| Microsoft Word + Zotero Word 插件 | Word 2016 / Microsoft 365（实测 Word 16） | 手动 Refresh；Windows 上渲染 PDF | **不会** |
| Claude Code 或 OpenAI Codex | 当前版本 | 以 agent 技能方式运行 | 否 |
| 联网 | | 仅文献检索需要 | |

> [!IMPORTANT]
> **本技能不会安装任何东西**：不装 Python，不装 pip 包，不装 Zotero 插件，也不装 Word 加载项。Python、Zotero 和 Word 插件的一次性配置步骤，详见 [manual-steps.md § 首次使用前](manual-steps.md#before-first-use)。

<a id="get-the-code"></a>
## 2. 获取代码

```bash
git clone https://github.com/milletvhyidavis/zotero-word-live-citations.git
```

```bash
cd zotero-word-live-citations
```

没有安装 git？可以在 GitHub 页面点击 **Code → Download ZIP** 下载压缩包并解压。

<a id="option-a"></a>
## 3. 方式 A：`install.py`（Claude Code 和/或 Codex）

`install.py` 会把 `skills/zotero-word-live-citations/` 复制到 agent 的技能目录（不包括 `tests/` 和缓存文件），它本身也只用标准库。

| 命令 | 安装位置 |
|---|---|
| `python install.py --target claude` | `~/.claude/skills/zotero-word-live-citations` |
| `python install.py --target codex` | `$CODEX_HOME/skills/zotero-word-live-citations`（默认 `~/.codex/skills/…`） |
| `python install.py --target both` | 以上两处 |
| `python install.py --target claude --project <目录>` | `<目录>/.claude/skills/zotero-word-live-citations`（仅对该项目有效） |
| `python install.py --target codex --project <目录>` | `<目录>/.codex/skills/zotero-word-live-citations` |

参数说明：

| 参数 | 含义 |
|---|---|
| `--target {claude,codex,both}` | 必填 |
| `--project DIR` | 安装到某个项目目录，而不是用户主目录 |
| `--dry-run` | 只显示将要执行的操作，不做任何改动 |
| `--force` | 替换内容不同的已有安装 |
| `--uninstall` | 删除已安装的技能目录（仅当目录中含有 `SKILL.md` 时才会删除） |

示例：

```bash
python install.py --target claude
```

```bash
python install.py --target both --dry-run
```

在 Windows 上，`~` 指 `%USERPROFILE%`，例如 `C:\Users\你的用户名\.claude\skills\zotero-word-live-citations`。

> [!NOTE]
> 如果已有安装与仓库中的版本不同，`install.py` 会逐一列出 `added`（新增）、`changed`（修改）、`removed`（删除）的文件，然后**停止**（退出码 1）。确认无误后加 `--force` 重新运行即可替换。如果内容完全相同，会提示 “already up to date”。

> [!NOTE]
> **Codex 目录。** 如果设置了环境变量 `CODEX_HOME`，Codex 目标会安装到 `$CODEX_HOME/skills`，否则安装到 `~/.codex/skills`。`--project` 会安装到 `<目录>/.codex/skills`，适用于支持仓库级技能的 Codex 版本。

安装完成后，`install.py` 会提醒你**新开一个 Claude Code / Codex 会话**（技能在会话启动时加载），并运行自检。

<a id="option-b"></a>
## 4. 方式 B：Claude Code 插件市场

本仓库同时也是一个 Claude Code 插件市场（`.claude-plugin/marketplace.json`）。在 Claude Code 中输入：

```text
/plugin marketplace add milletvhyidavis/zotero-word-live-citations
```

```text
/plugin install zotero-word-live-citations@zotero-word-live-citations
```

第一条命令从 GitHub 注册插件市场，第二条命令从名为 `zotero-word-live-citations` 的市场安装同名插件。完成后请重启 Claude Code，或新开一个会话。

如果已经克隆到本地，也可以用本地路径添加市场：

```text
/plugin marketplace add ./zotero-word-live-citations
```

> [!TIP]
> 通过插件市场安装的文件位于 Claude Code 的插件缓存中，而不是 `~/.claude/skills`。想手动运行自检，请使用克隆目录中的脚本：`python skills/zotero-word-live-citations/scripts/selftest.py`。

**Codex 插件清单。** 仓库中还有 `.codex-plugin/plugin.json`（其中 `"skills": "./skills/"`）和 `skills/zotero-word-live-citations/agents/openai.yaml`，供 Codex 插件工具使用。不过对 Codex 而言，经过测试、正式支持的方式仍是方式 A 或方式 C。

<a id="option-c"></a>
## 5. 方式 C：手动复制

复制 `skills/zotero-word-live-citations/` 文件夹，使 `SKILL.md` 位于以下位置之一：

| Agent | 路径 |
|---|---|
| Claude Code（个人全局） | `~/.claude/skills/zotero-word-live-citations/SKILL.md` |
| Claude Code（单个项目） | `<项目>/.claude/skills/zotero-word-live-citations/SKILL.md` |
| Codex | `~/.codex/skills/zotero-word-live-citations/SKILL.md`（或 `$CODEX_HOME/skills/…`） |

bash / zsh：

```bash
mkdir -p ~/.claude/skills
```

```bash
cp -R skills/zotero-word-live-citations ~/.claude/skills/
```

PowerShell：

```powershell
New-Item -ItemType Directory -Force "$HOME\.claude\skills"
```

```powershell
Copy-Item -Recurse skills\zotero-word-live-citations "$HOME\.claude\skills\"
```

运行时不需要 `tests/` 文件夹，可以从复制的目录中删掉。

<a id="verify"></a>
## 6. 验证安装

1. **检查文件：**

   ```bash
   ls ~/.claude/skills/zotero-word-live-citations
   ```

   应能看到 `SKILL.md`、`agents/`、`references/`、`scripts/`。

2. **运行自检。** 请先启动 Zotero：

   ```bash
   python ~/.claude/skills/zotero-word-live-citations/scripts/selftest.py
   ```

   PowerShell：

   ```powershell
   python "$HOME\.claude\skills\zotero-word-live-citations\scripts\selftest.py"
   ```

   正常情况下，`python`、`zotero-running`、`zotero-local-api`、`zotero-read-items`、`docx-pipeline` 都显示 `[OK ]`；装有 Office 的 Windows 上 `microsoft-word` 也是 `[OK ]`。加 `--json` 输出机器可读结果；加 `--strict` 则在 Zotero 条目不可读时以退出码 1 结束。

3. **新开 agent 会话。** 在新的 Claude Code / Codex 会话中问一句：*“你有 zotero-word-live-citations 技能吗？它能做什么？”* 在 Codex 中也可以用 `$zotero-word-live-citations` 直接调用。

<a id="updating"></a>
## 7. 更新

**用 `install.py` 安装的：**

```bash
git pull
```

```bash
python install.py --target claude --force
```

视情况改用 `--target codex` 或 `--target both`。不加 `--force` 时，`install.py` 只列出变化的文件然后停止。更新后请新开会话。

**通过插件市场安装的**（在 Claude Code 中）：

```text
/plugin marketplace update zotero-word-live-citations
```

然后在 `/plugin` 菜单中更新或重新安装插件，并重启。

**手动复制的：** 删除旧文件夹，再复制新版本。

<a id="uninstalling"></a>
## 8. 卸载

```bash
python install.py --target claude --uninstall
```

```bash
python install.py --target both --uninstall --dry-run
```

出于安全考虑，`--uninstall` 不会删除不含 `SKILL.md` 的目录。

通过插件市场安装的（在 Claude Code 中）：

```text
/plugin uninstall zotero-word-live-citations@zotero-word-live-citations
```

```text
/plugin marketplace remove zotero-word-live-citations
```

卸载技能**不会**影响你的 Zotero 文库、文档，也不会影响之前导入的条目（如果当时用了 `zwlc-import` 标签，这些条目都带有该标签）。

<a id="python-discovery"></a>
## 9. Python 的查找规则

每个任务开始时，agent 会确定一次要用的 Python（记作 `PY`）：依次尝试 `python3`、`python`、`py -3`，取**第一个** `--version` 显示 ≥ 3.9 的。在 Windows 上会跳过微软商店的占位程序。Codex 用户还可以使用 Codex 自带的 Python：

```text
~/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python      （macOS/Linux）
%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe   （Windows）
```

如果一个都找不到，agent 会请你自行安装 Python，除此之外不做任何事。

查看本机的 Python 版本：

```bash
python3 --version
```

```bash
python --version
```

```bash
py -3 --version
```

<a id="per-os-notes"></a>
## 10. 各操作系统注意事项

### Windows

- 请安装 python.org 上的正式版 Python，最稳妥的命令是 `py -3`。如果输入 `python` 会打开微软商店，请关闭应用执行别名（设置 → 应用 → 高级应用设置 → 应用执行别名）。
- PowerShell 与 bash 的区别：设置环境变量时，PowerShell 写作 `$env:NAME = "value"`，bash 写作 `export NAME="value"`。路径中用 `\` 或 `/` 均可。
- 中文路径和中文文件名没有问题，脚本会强制以 UTF-8 输出到控制台。如果旧式控制台中的中文显示为乱码，请参阅 [troubleshooting.md § Windows 编码与中文路径](troubleshooting.md#windows-encoding)。
- `word_render.py`（渲染 PDF）需要 Microsoft Word 和 PowerShell。脚本先在标准的 `Program Files` / `Program Files (x86)` 下的 `Microsoft Office\…\Office16`（或 `Office15`）目录中查找 Word；找不到时，再读取 Word 在 Windows 注册表 `App Paths\Winword.exe` 键（先 HKLM，后 HKCU）中登记的路径，因此安装在其他位置的 Word 也能被找到。

### macOS

- 使用 `python3`。除 `word_render.py` 外，其他功能都可用；PDF 渲染仅支持 Windows，在 macOS 上会显示“不可用”。
- 首次运行 Word 插件时，Zotero 和 Word 可能会请求自动化或辅助功能权限，请允许。
- 在 Word 中切换域代码显示：**Option+F9**（可能需要同时按 **fn**）。

### Linux

- 使用 `python3`。Zotero 桌面版支持 Linux，但 Microsoft Word 不支持，因此 Refresh 需要在装有 Word 和 Zotero 插件的 Windows 或 macOS 电脑上进行。**不要**用 LibreOffice 刷新或另存输出文件（见 [manual-steps.md § A1](manual-steps.md#a1)）。
- `word_render.py` 不可用。
