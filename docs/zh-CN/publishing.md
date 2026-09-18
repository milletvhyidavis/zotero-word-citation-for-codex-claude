# 发布指南（面向维护者）

[English](../en/publishing.md) · [返回 README](../../README.md)

本页写给负责把仓库发布到 GitHub 的人。技能的普通用户不需要阅读。

> [!IMPORTANT]
> **关于 `<owner>`。** 文档中所有 GitHub 地址和插件市场命令，都用占位符 **`<owner>`** 表示将来拥有该仓库的 GitHub 用户或组织，例如 `https://github.com/<owner>/zotero-word-citation-for-codex-claude`。这样做是为了在确定所有者之后一次性替换（见[第 4 步](#replace-owner)）。本指南本身保留 `<owner>` 占位符，不参与替换。

## 目录

- [1. 发布前检查](#pre-publish-checks)
- [2. 在 GitHub 上新建空仓库](#create-repo)
- [3. 推送代码](#push)
- [4. 替换 `<owner>`](#replace-owner)
- [5. 简介、主题标签和仓库设置](#settings)
- [6. 打标签并发布 v1.0.0](#release)
- [7. 从 GitHub 测试安装](#test-install)
- [8. 可选：提交到技能目录网站](#directories)
- [9. 后续版本](#later-releases)

---

<a id="pre-publish-checks"></a>
## 1. 发布前检查

第一次推送之前，请在仓库根目录下逐项检查。

1. **测试通过。**

   ```bash
   cd skills/zotero-word-live-citations/tests
   ```

   ```bash
   python -m unittest discover
   ```

   应输出 `Ran 38 tests … OK`。完成后回到仓库根目录。

2. **没有个人信息。** 搜索你的 Zotero 用户 ID、邮箱地址、私人集合名称和本机路径：

   ```bash
   grep -rn "你的Zotero用户ID\|you@your-domain\|C:/Users/" --exclude-dir=.git .
   ```

   PowerShell：

   ```powershell
   Get-ChildItem -Recurse -File | Where-Object { $_.FullName -notmatch "\\.git\\" } | Select-String -Pattern "你的Zotero用户ID","you@your-domain"
   ```

   > [!TIP]
   > 每次新增示例、测试数据或截图后，都请重新扫描一遍。仓库自带的示例使用的都是中性值（例如 `references/zotero-local-api.md` 中的用户 ID `123456`），你新增的内容也应如此。

3. **没有生成文件或测试文件。** `.gitignore` 已经排除了 `__pycache__/`、`*.pyc`、`.pytest_cache/`、`*-zotero-cited.docx`、Word 锁文件（`~$*.docx`）和 `e2e-tumor-immunology/`。请确认目录中没有你自己测试时留下的稿件、reference map、RIS 文件或 PDF：

   ```bash
   git status --short
   ```

4. **可选的个性化设置**（这些是代码或元数据文件，任何改动请自行审阅）：
   - `LICENSE`、`.claude-plugin/plugin.json`、`.claude-plugin/marketplace.json` 和 `.codex-plugin/plugin.json` 中的作者名是 `zotero-word-live-citations contributors`。你也可以改成自己的名字或组织名。
   - `skills/zotero-word-live-citations/scripts/_common.py` 中设置了 `USER_AGENT = "zotero-word-live-citations/1.0"`。OpenAlex 和 Crossref 建议 User-Agent 指向项目主页，因此仓库建好后可以在后面加上仓库地址，例如 `"zotero-word-live-citations/1.0 (+https://github.com/<owner>/zotero-word-citation-for-codex-claude)"`。这属于代码改动，[第 4 步](#replace-owner)的 `<owner>` 批量替换不会处理它，请直接写入真实的所有者名称。

5. **文档一致。** `docs/` 中每一页都有中英两个版本，`CHANGELOG.md` 中的发布日期符合你的预期。

<a id="create-repo"></a>
## 2. 在 GitHub 上新建空仓库

1. 打开 **github.com → New repository**。
2. Owner：你的用户或组织（也就是 `<owner>`）。仓库名：**`zotero-word-citation-for-codex-claude`**。
3. 可见性：**Public**。
4. **不要**勾选添加 README、`.gitignore` 或许可证。仓库里已经有这些文件；如果在 GitHub 上生成了初始提交，第一次推送会失败。
5. 点击 **Create repository**。

也可以改用 GitHub CLI 在终端完成同样的操作（一次性创建仓库、添加远程地址并推送）：

```bash
gh repo create <owner>/zotero-word-citation-for-codex-claude --public --source . --remote origin --push
```

如果用了这条命令，可以直接跳到[第 4 步](#replace-owner)。

<a id="push"></a>
## 3. 推送代码

如果这个文件夹还不是 git 仓库，先初始化并完成第一次提交：

```bash
git init
```

```bash
git add .
```

```bash
git commit -m "Initial public release v1.0.0"
```

然后关联 GitHub 并推送：

```bash
git remote add origin https://github.com/<owner>/zotero-word-citation-for-codex-claude.git
```

```bash
git branch -M main
```

```bash
git push -u origin main
```

请把命令中的 `<owner>` 换成你的 GitHub 用户名。如果 `origin` 已经存在，请用 `git remote set-url origin …` 代替 `git remote add`。

<a id="replace-owner"></a>
## 4. 替换 `<owner>`

占位符 `<owner>` 出现在以下文件和行中（不包括本指南及其英文版）：

| 文件 | 行号 | 内容 |
|---|---|---|
| `README.en.md` | 102 | `git clone https://github.com/<owner>/zotero-word-citation-for-codex-claude.git` |
| `README.en.md` | 120 | `/plugin marketplace add <owner>/zotero-word-citation-for-codex-claude` |
| `README.md` | 102 | `git clone https://github.com/<owner>/zotero-word-citation-for-codex-claude.git` |
| `README.md` | 120 | `/plugin marketplace add <owner>/zotero-word-citation-for-codex-claude` |
| `CHANGELOG.md` | 53 | `[1.0.0]: https://github.com/<owner>/zotero-word-citation-for-codex-claude/releases/tag/v1.0.0` |
| `CONTRIBUTING.md` | 15 | `git clone https://github.com/<owner>/zotero-word-citation-for-codex-claude.git`（英文部分） |
| `CONTRIBUTING.md` | 89 | `git clone https://github.com/<owner>/zotero-word-citation-for-codex-claude.git`（中文部分） |
| `SECURITY.md` | 26 | `https://github.com/<owner>/zotero-word-citation-for-codex-claude/security/advisories/new`（英文部分） |
| `SECURITY.md` | 52 | `https://github.com/<owner>/zotero-word-citation-for-codex-claude/security/advisories/new`（中文部分） |
| `docs/en/installation.md` | 36 | `git clone https://github.com/<owner>/zotero-word-citation-for-codex-claude.git` |
| `docs/en/installation.md` | 92 | `/plugin marketplace add <owner>/zotero-word-citation-for-codex-claude` |
| `docs/en/troubleshooting.md` | 164 | `https://github.com/<owner>/zotero-word-citation-for-codex-claude/issues` |
| `docs/zh-CN/installation.md` | 38 | `git clone https://github.com/<owner>/zotero-word-citation-for-codex-claude.git` |
| `docs/zh-CN/installation.md` | 96 | `/plugin marketplace add <owner>/zotero-word-citation-for-codex-claude` |
| `docs/zh-CN/troubleshooting.md` | 175 | `https://github.com/<owner>/zotero-word-citation-for-codex-claude/issues` |

代码、JSON 和 YAML 文件中都没有 `<owner>`。如果你先改动过这些文件，行号可能会变化，以下面 grep 命令的实时结果为准。

列出当前所有出现位置：

```bash
grep -rn "<owner>" --include="*.md" --exclude-dir=.git .
```

**批量替换（bash，Linux 或 Git Bash 中的 GNU sed）：**

```bash
OWNER=your-github-name
```

```bash
grep -rl "<owner>" --include="*.md" --exclude-dir=.git . | grep -v "/publishing.md$" | xargs sed -i "s/<owner>/$OWNER/g"
```

macOS（BSD sed）上请把 `sed -i` 改为 `sed -i ''`：

```bash
grep -rl "<owner>" --include="*.md" --exclude-dir=.git . | grep -v "/publishing.md$" | xargs sed -i '' "s/<owner>/$OWNER/g"
```

**批量替换（PowerShell）。** 以下命令写出不带 BOM 的 UTF-8，中文内容不会受影响：

```powershell
$Owner = "your-github-name"
```

```powershell
Get-ChildItem -Recurse -Filter *.md | Where-Object { $_.Name -ne "publishing.md" -and $_.FullName -notmatch "\\.git\\" } | ForEach-Object { $t = [IO.File]::ReadAllText($_.FullName); if ($t.Contains("<owner>")) { [IO.File]::WriteAllText($_.FullName, $t.Replace("<owner>", $Owner), (New-Object Text.UTF8Encoding($false))) } }
```

> [!NOTE]
> 在 Windows PowerShell 5.1 中不要用 `Set-Content` 做这件事。它默认使用系统 ANSI 代码页写文件，会把中文文件弄成乱码。

确认只剩两份发布指南中还有占位符，然后提交并推送：

```bash
grep -rn "<owner>" --include="*.md" --exclude-dir=.git .
```

```bash
git commit -am "docs: set repository owner"
```

```bash
git push
```

<a id="settings"></a>
## 5. 简介、主题标签和仓库设置

在仓库主页点击 **About** 旁边的齿轮图标：

- **Description（简介）：** 例如 *Agent skill for Claude Code and Codex: find papers, match them to Zotero, and write live, refreshable Zotero citations into Word DOCX.*
- **Topics（主题标签）：** `zotero`、`microsoft-word`、`docx`、`citations`、`bibliography`、`csl`、`claude-code`、`claude-skills`、`agent-skills`、`codex`、`literature-search`、`pubmed`、`openalex`、`crossref`

或者使用 GitHub CLI：

```bash
gh repo edit <owner>/zotero-word-citation-for-codex-claude --description "Agent skill for Claude Code and Codex: live, refreshable Zotero citations in Word DOCX"
```

```bash
gh repo edit <owner>/zotero-word-citation-for-codex-claude --add-topic zotero,microsoft-word,docx,citations,bibliography,csl,claude-code,claude-skills,agent-skills,codex,literature-search,pubmed,openalex,crossref
```

建议的设置：

- **Settings → Security → Private vulnerability reporting → Enable（启用私密漏洞报告）。** `SECURITY.md` 会引导报告者使用这个功能。（因 GitHub 界面版本不同，它可能位于 *Code security* 或 *Code security and analysis* 下。）
- **Settings → General → Features：** 保持 **Issues** 开启，`docs/*/troubleshooting.md` 会引导用户到那里提问。
- 可选：保护 `main` 分支（**Settings → Branches**），让改动都通过 pull request 合入。

<a id="release"></a>
## 6. 打标签并发布 v1.0.0

创建附注标签并推送：

```bash
git tag -a v1.0.0 -m "zotero-word-live-citations v1.0.0"
```

```bash
git push origin v1.0.0
```

创建 Release。最简单的做法是把 `CHANGELOG.md` 中 `## [1.0.0]` 这一节复制到仓库之外的一个临时文件里，例如 `../release-notes-1.0.0.md`，再用它作为发布说明：

```bash
gh release create v1.0.0 --title "v1.0.0" --notes-file ../release-notes-1.0.0.md
```

不用 CLI 的话：仓库 → **Releases → Draft a new release** → 选择标签 `v1.0.0` → 标题填 `v1.0.0` → 粘贴更新日志中的对应内容 → **Publish release**。

版本号必须与 `.claude-plugin/plugin.json`、`.claude-plugin/marketplace.json` 和 `.codex-plugin/plugin.json` 中的 `"version": "1.0.0"` 一致。

<a id="test-install"></a>
## 7. 从 GitHub 测试安装

请以新用户的身份测试，最好使用一台干净的电脑或一个新账户。

**Claude Code 插件市场：** 在新的 Claude Code 会话中输入：

```text
/plugin marketplace add <owner>/zotero-word-citation-for-codex-claude
```

```text
/plugin install zotero-word-live-citations@zotero-word-live-citations
```

重启 Claude Code，然后问一句 *“你有 zotero-word-live-citations 技能吗？”*，再试一个小任务（例如“检查这个 DOCX 中的 Zotero 域是否有效”）。

**从全新克隆使用 `install.py`：**

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

**Codex：** 运行 `python install.py --target codex`，新开一个 Codex 会话，用 `$zotero-word-live-citations` 调用。

另外请检查 README 和 `docs/` 中的所有链接在 GitHub 上都能打开（中英文都要看），mermaid 流程图和提示框（alert）也能正常显示。

<a id="directories"></a>
## 8. 可选：提交到技能目录网站

有一些由社区维护的列表和目录网站会收录 Claude Code 插件、agent 技能和 Codex 技能（例如 GitHub 上的各种 “awesome” 列表和插件市场聚合站）。如果希望更多人发现这个技能：

1. 找到仍在活跃维护、接受投稿的目录，阅读其投稿说明。
2. 提交仓库地址 `https://github.com/<owner>/zotero-word-citation-for-codex-claude`，附上一句话简介，例如 *Live, refreshable Zotero citations in Word DOCX: literature search, Zotero matching, approved imports, field insertion and validation.*
3. 如实说明使用条件：Zotero 桌面版 7+、Refresh 需要装有 Zotero 插件的 Microsoft Word、Python ≥ 3.9。
4. 不要暗示与 Zotero、Microsoft、Anthropic 或 OpenAI 有任何隶属关系。

<a id="later-releases"></a>
## 9. 后续版本

1. 有改动合入时，在 `CHANGELOG.md` 的 `## [Unreleased]` 标题下补充中英文条目。
2. 发布时把它改为 `## [x.y.z] — YYYY-MM-DD`，并在文件末尾添加对应的链接行。
3. 更新 `.claude-plugin/plugin.json`、`.claude-plugin/marketplace.json` 和 `.codex-plugin/plugin.json` 中的 `"version"`。如果 `_common.py` 的 `USER_AGENT` 中含有版本号，也一并更新。
4. 运行测试、提交，然后按[第 6 步](#release)打标签并发布。
5. 用户更新方式：`git pull` + `python install.py --target … --force`，或在 Claude Code 中运行 `/plugin marketplace update zotero-word-live-citations`。
