# Contributing · 贡献指南

[English](#english) · [简体中文](#简体中文)

## English

Thanks for helping! Bug reports, documentation fixes, new style aliases, better matching heuristics and test cases are all welcome.

### Development setup

1. Install Python ≥ 3.9. No other packages are needed or allowed at runtime.
2. Clone the repository:

   ```bash
   git clone https://github.com/<owner>/zotero-word-live-citations.git
   ```

   ```bash
   cd zotero-word-live-citations
   ```

3. Run the tests from the tests folder:

   ```bash
   cd skills/zotero-word-live-citations/tests
   ```

   ```bash
   python -m unittest discover
   ```

   Expected: `Ran 38 tests … OK` (the number grows as tests are added). The tests are offline. They use fixtures and a fake Zotero library and need neither Zotero, Word nor the internet.

4. For manual end-to-end checks, install your working copy into a project folder so you don't disturb your personal install:

   ```bash
   python install.py --target claude --project ./sandbox
   ```

   Then run `python skills/zotero-word-live-citations/scripts/selftest.py` with Zotero running. Use a **dedicated test collection** in Zotero for any import tests.

### Rules that must never break

These rules are the reason people can trust the skill with their manuscripts and libraries. PRs that weaken them will not be merged.

1. **Standard library only.** No third-party imports and no `pip install`, in scripts or at runtime. The skill never installs anything on the user's machine.
2. **Never overwrite the input DOCX.** The output is a separate file, and `inputUnchanged` must stay verifiable.
3. **No Zotero write without explicit approval.** Imports need `--yes` and should be used with `--expect-target`. No editing, moving, merging or deleting items, and no changing Zotero preferences.
4. **Never guess identity.** Ambiguous matches go to the user. Never fabricate item keys, URIs, DOIs or references. URIs come only from the item's own `library` object.
5. **Parent items only.** Never cite attachments, notes or annotations.
6. **Never synthesize** `formattedCitation` / `plainCitation`. Never present plain text or ordinary Word fields as Zotero citations.
7. **Preserve existing content:** existing Zotero fields, bibliography and document preferences must survive, and non-target DOCX parts are copied byte-for-byte.
8. **Never run Zotero Refresh automatically.**
9. **Keep the three results separate:** structural validation, Word rendering and Zotero Refresh.
10. **Exit codes:** 0 success · 1 validation failure, or unresolved references in `resolve_references.py` (outputs still written) · 2 usage/environment error, including an unknown `[@…]` marker in `insert_zotero_fields.py` (nothing written).

### Style

- Python 3.9-compatible syntax (use `from __future__ import annotations` for modern type hints).
- Every script keeps a helpful module docstring and `--help`. If you add or change a flag, update `SKILL.md`/`references/` **and** `docs/en` + `docs/zh-CN`.
- UTF-8 everywhere (`utf8_stdio()` for console output; read JSON with `utf-8-sig`).
- Keep `SKILL.md` short. Details belong in `references/`.

### Pull request checklist

- [ ] `python -m unittest discover` passes in `skills/zotero-word-live-citations/tests`
- [ ] New behaviour has a test (fixtures instead of network/Zotero)
- [ ] No third-party dependencies added
- [ ] None of the "never break" rules weakened
- [ ] `--help` text, `SKILL.md`/`references/` and both language versions of the docs updated
- [ ] `CHANGELOG.md` entry under an "Unreleased" heading (English + Chinese)
- [ ] No personal data in code, fixtures, docs or screenshots (Zotero user IDs, e-mail addresses, private collection names, manuscripts)
- [ ] Commits and PR description explain *why*, not only *what*

### Reporting bugs

Open an issue with OS, Python/Zotero/Word versions, `selftest.py --json` output, the exact command and error. Security problems: see [SECURITY.md](SECURITY.md).

## 简体中文

感谢你愿意参与！无论是报告 bug、修正文档、增加样式别名、改进匹配算法还是补充测试用例，我们都很欢迎。

### 开发环境

1. 安装 Python ≥ 3.9。运行时不需要、也不允许依赖任何第三方包。
2. 克隆仓库：

   ```bash
   git clone https://github.com/<owner>/zotero-word-live-citations.git
   ```

   ```bash
   cd zotero-word-live-citations
   ```

3. 进入测试目录运行测试：

   ```bash
   cd skills/zotero-word-live-citations/tests
   ```

   ```bash
   python -m unittest discover
   ```

   正常输出为 `Ran 38 tests … OK`（数量会随测试增加而变化）。测试完全离线，使用固定数据和模拟的 Zotero 文库，不需要 Zotero、Word 或网络。

4. 做手动端到端测试时，建议把开发中的版本装到一个项目目录里，以免影响你个人的安装：

   ```bash
   python install.py --target claude --project ./sandbox
   ```

   然后在 Zotero 运行的情况下执行 `python skills/zotero-word-live-citations/scripts/selftest.py`。任何导入测试都请使用 Zotero 中**专门的测试集合**。

### 绝不能破坏的规则

用户之所以敢把稿件和文献库交给这个技能，靠的就是下面这些规则。削弱这些规则的 PR 不会被合并。

1. **只用标准库。** 脚本中不得引入第三方库，运行时也不得执行 `pip install`。本技能绝不在用户电脑上安装任何东西。
2. **绝不覆盖输入的 DOCX。** 输出必须是另一个文件，`inputUnchanged` 必须始终可以验证。
3. **未经明确批准不得写入 Zotero。** 导入必须带 `--yes`，并应配合 `--expect-target` 使用。不得编辑、移动、合并或删除条目，不得修改 Zotero 设置。
4. **绝不猜测条目身份。** 有歧义的匹配交给用户决定。绝不编造条目 key、URI、DOI 或参考文献。URI 只能根据条目自身的 `library` 对象生成。
5. **只引用父条目。** 不得引用附件、笔记或批注。
6. **绝不伪造** `formattedCitation` / `plainCitation`，也不得把纯文本或普通 Word 域冒充为 Zotero 引用。
7. **保留已有内容：** 已有的 Zotero 域、参考文献表和文档偏好必须保留，DOCX 中与本次修改无关的部分必须逐字节复制。
8. **绝不自动执行 Zotero Refresh。**
9. **三项结果分开报告：** 结构验证、Word 渲染、Zotero Refresh。
10. **退出码：** 0 成功；1 验证失败，或 `resolve_references.py` 中存在未解析的文献（输出文件照常写出）；2 用法或环境错误，包括 `insert_zotero_fields.py` 中未知的 `[@…]` 标记（不写出任何文件）。

### 代码风格

- 语法须兼容 Python 3.9（使用新式类型注解时加 `from __future__ import annotations`）。
- 每个脚本都要保留有用的模块 docstring 和 `--help`。新增或修改参数时，要同步更新 `SKILL.md` / `references/`，以及 `docs/en` 和 `docs/zh-CN`。
- 全程使用 UTF-8（控制台输出用 `utf8_stdio()`；读取 JSON 用 `utf-8-sig`）。
- `SKILL.md` 保持简短，细节放进 `references/`。

### PR 检查清单

- [ ] 在 `skills/zotero-word-live-citations/tests` 下运行 `python -m unittest discover` 全部通过
- [ ] 新功能配有测试（用固定数据代替网络或 Zotero）
- [ ] 没有引入第三方依赖
- [ ] 没有削弱任何一条“绝不能破坏的规则”
- [ ] 已同步更新 `--help`、`SKILL.md` / `references/` 以及中英文文档
- [ ] 已在 `CHANGELOG.md` 的 “Unreleased” 标题下补充中英文条目
- [ ] 代码、测试数据、文档和截图中没有个人信息（Zotero 用户 ID、邮箱、私人集合名称、稿件内容等）
- [ ] 提交信息和 PR 描述说明了“为什么改”，而不只是“改了什么”

### 报告 bug

提交 issue 时请写明操作系统、Python / Zotero / Word 版本、`selftest.py --json` 的输出，以及出错的完整命令和错误信息。安全问题请参阅 [SECURITY.md](SECURITY.md)。
