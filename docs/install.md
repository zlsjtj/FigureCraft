# 选择你使用的工具

四个入口使用同一份核心技能。名字是 `scientific-figure-studio`；FigureCraft 是展示名称。本版为 1.28.1；[固定版本下载](https://github.com/zlsjtj/FigureCraft/releases/tag/v1.28.1)和[验证范围](client-entry-validation.md)可单独查看。请从同一个版本取得完整包，不混装文件。

## Codex

新安装按 [Codex 当前文档](https://learn.chatgpt.com/docs/build-skills) 使用个人目录 `~/.agents/skills/`。如果你现有客户端已经从 `~/.codex/skills/` 或 `$CODEX_HOME/skills/` 加载此技能，沿用实际已加载目录；不要同时安装两个同名副本。本机旧目录可用，不代表所有客户端都采用同一路径。

安装 **GitHub 当前默认分支**，PowerShell：

```powershell
$skillRoot = Join-Path $env:USERPROFILE '.agents/skills'
New-Item -ItemType Directory -Force -Path $skillRoot | Out-Null
git clone https://github.com/zlsjtj/FigureCraft.git (Join-Path $skillRoot 'scientific-figure-studio')
```

macOS / Linux：

```bash
mkdir -p "$HOME/.agents/skills"
git clone https://github.com/zlsjtj/FigureCraft.git "$HOME/.agents/skills/scientific-figure-studio"
```

以上 clone 取得 GitHub 默认分支。若使用收到的安装 ZIP，请按下方的解压说明操作；ZIP 的内容以包内 manifest 为准。已有同名目录时先保留旧副本，不直接覆盖。安装后打开新会话，明确使用 `$scientific-figure-studio`；请它报告实际读取的 `SKILL.md` 路径，再开始任务。

## Claude Code

推荐使用插件管理安装；插件直接读取根目录的同一份 `SKILL.md`，没有另一套科学编辑指令。

在 Claude Code 中依次输入：

```text
/plugin marketplace add zlsjtj/FigureCraft
/plugin install figurecraft@zlsjtj-figurecraft
```

如果使用下载后的本地源码，可将第一行的 `zlsjtj/FigureCraft` 换成仓库绝对路径（Windows 可写 `E:/path/to/FigureCraft`）。两种方式只选一种。

启用并打开新会话后，调用 `/figurecraft:scientific-figure-studio`。也可以直接用技能名称描述任务。更新使用客户端插件管理，不把新源码混入旧插件缓存。

<details>
<summary>沿用个人技能目录安装（已在用的用户不必换）</summary>

PowerShell：

```powershell
$skillRoot = Join-Path $env:USERPROFILE '.claude/skills'
New-Item -ItemType Directory -Force -Path $skillRoot | Out-Null
git clone https://github.com/zlsjtj/FigureCraft.git (Join-Path $skillRoot 'scientific-figure-studio')
```

macOS / Linux：

```bash
mkdir -p "$HOME/.claude/skills"
git clone https://github.com/zlsjtj/FigureCraft.git "$HOME/.claude/skills/scientific-figure-studio"
```

已有目录不要覆盖。此入口调用 `/scientific-figure-studio`，与插件命名空间不同。两种方式选一种，避免同名旧副本抢先触发。

</details>

本地目录安装不等于网页账户已安装；网页启用技能向其他 Claude 产品的同步以当前账户与官方说明为准。[Claude Code 技能文档](https://code.claude.com/docs/en/skills) · [插件路径规则](https://code.claude.com/docs/en/plugins-reference)

### 用收到的 ZIP 安装本地技能

此方法适用于 Codex 与 Claude Code，使用交付包中的 `scientific-figure-studio-codex.zip` 或 `scientific-figure-studio-claude-code.zip`。仓库克隆与 ZIP 安装任选一种，不要混合两份文件。

1. 将 ZIP 解压到一个新的临时文件夹。应得到 `scientific-figure-studio/SKILL.md`，不要再套一层同名目录。
2. 把完整的 `scientific-figure-studio` 文件夹放到选定宿主的技能目录。若已存在，先把旧副本备份到技能扫描目录之外，再放入新副本；不要合并两版文件。
3. 重新打开会话，报告实际技能路径、版本与包内 `package-manifest.json` 的宿主字段。记录说明来源，不能证明宿主已触发技能或生成成功。
4. 执行[首次试用](first-use.md)。独立查看实际 Word/PDF 或图件之后，再用于自己的材料。

已有仓库源码也可放到新目录后明确要求读取那里的 `SKILL.md`；这能试用该副本，但不能算自动发现已经通过。

<a id="claude-web"></a>

## Claude 网页 / Desktop

1. [下载 Claude 技能包](https://github.com/zlsjtj/FigureCraft/releases/download/v1.28.1/scientific-figure-studio-claude.zip)，保留 ZIP，不要上传整份 GitHub 源码 ZIP。
2. 在 Claude 的 **Customize → Skills → + → Create skill → Upload a skill** 中导入并启用。账户需要开启代码执行与文件创建；组织策略可能限制导入。
3. [下载首次试用材料](https://github.com/zlsjtj/FigureCraft/releases/download/v1.28.1/scientific-figure-studio-first-use.zip)，解压后上传 TASK.md 和 input/ 内的文件，要求使用 `scientific-figure-studio` 完成任务。

无需在本机先安装 Python。实际执行环境仍需具备相应 Python 包和导出工具；缺少的能力会单独报告。此入口指 Claude 自定义技能，不把本地文件路径当作云端可访问附件。

[官方导入说明](https://support.claude.com/en/articles/12512180-use-skills-in-claude) · [官方包结构](https://support.claude.com/en/articles/12512198-how-to-create-custom-skills)

## WorkBuddy

1. [下载 WorkBuddy 技能包](https://github.com/zlsjtj/FigureCraft/releases/download/v1.28.1/scientific-figure-studio-workbuddy.zip)。
2. 在 **专家·技能·连接器 → 技能 → 添加技能 → 上传技能** 导入并启用；不同客户端版本可能缩写菜单名。
3. 解压[首次试用材料](https://github.com/zlsjtj/FigureCraft/releases/download/v1.28.1/scientific-figure-studio-first-use.zip)，把 TASK.md 和 input/ 交给 WorkBuddy，明确使用 `scientific-figure-studio`。

将技能 ZIP 保持压缩状态上传到技能管理；**试用材料 ZIP 要解压后交给对话**，两者用途不同。能看到文件不等于技能已启用；让它报告实际读取的 `scientific-figure-studio/SKILL.md` 和版本，再做首次任务。

包中保留完整脚本和参考，补充中英文简介、作者与版本，不更改研究方法，也不写死 WorkBuddy 内部目录。开放平台字段要求不代表客户端导入已经实测。

[官方安装说明](https://www.codebuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Skills-Market) · [包元信息说明](https://open.workbuddy.cn/en/docs/skill)

## 导入后遇到问题

| 现象 | 先检查 |
|---|---|
| 导入时找不到技能定义 | 下载的是本页宿主 ZIP，而不是 GitHub Source code ZIP 或试用材料包；其中应有 `scientific-figure-studio/SKILL.md` |
| Claude Code 找不到命令 | 插件使用 `/figurecraft:scientific-figure-studio`；个人目录使用 `/scientific-figure-studio`；确认插件已启用并开新会话 |
| WorkBuddy 只阅读了 ZIP，没有使用技能 | 回到技能管理导入技能 ZIP；对话中只交任务和原始材料 |
| 报 scripts/ 不存在 | 以本次实际读取的 SKILL.md 定位脚本，不能相对于论文目录运行；包内有运行入口说明 |
| Word 有了但 PDF/PNG 没有 | 按依赖页检查执行环境中的 LibreOffice/Poppler 与字体，不反复重新导入技能 |

## 依赖与第一次任务

技能包装的是工作方法和工具，不包含模型、账户、字体或 LibreOffice。安装成功后先完成[一个小任务](first-use.md)，再处理自己的整篇论文。[依赖与导出](usage.md)

Claude 和 WorkBuddy 目前只有包结构与本地工具验证，客户端导入、自动触发和新生成尚待实测；不要把这份教程当作已测成功的记录。
