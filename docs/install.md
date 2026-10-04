# 选择你使用的工具

四个入口使用同一份核心技能。名字是 `scientific-figure-studio`；FigureCraft 是展示名称。本版为 1.28.0；下载包与验证范围见[本轮记录](multihost-validation.md)。 首次安装请沿本页入口下载；GitHub Releases 中的包按历史标签固定，可能早于默认分支，不应混装。

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

将技能放入个人目录 `~/.claude/skills/scientific-figure-studio/`。

```powershell
$skillRoot = Join-Path $env:USERPROFILE '.claude/skills'
New-Item -ItemType Directory -Force -Path $skillRoot | Out-Null
git clone https://github.com/zlsjtj/FigureCraft.git (Join-Path $skillRoot 'scientific-figure-studio')
```

macOS / Linux 使用 `mkdir -p ~/.claude/skills`，再把仓库克隆到 `~/.claude/skills/scientific-figure-studio`。打开新会话，用 `/scientific-figure-studio` 或在请求中明确技能名。已有目录不要直接覆盖。

这是本地 Claude Code 入口，不能据此认为网页或 Cowork 已安装。路径和调用规则依据 [Claude Code 官方文档](https://code.claude.com/docs/en/skills)。

### 用收到的 ZIP 安装本地技能

此方法适用于 Codex 与 Claude Code，使用交付包中的 `scientific-figure-studio-codex.zip` 或 `scientific-figure-studio-claude-code.zip`。仓库克隆与 ZIP 安装任选一种，不要混合两份文件。

1. 将 ZIP 解压到一个新的临时文件夹。应得到 `scientific-figure-studio/SKILL.md`，不要再套一层同名目录。
2. 把完整的 `scientific-figure-studio` 文件夹放到选定宿主的技能目录。若已存在，先把旧副本备份到技能扫描目录之外，再放入新副本；不要合并两版文件。
3. 重新打开会话，报告实际技能路径、版本与包内 `package-manifest.json` 的宿主字段。记录说明来源，不能证明宿主已触发技能或生成成功。
4. 执行[首次试用](first-use.md)。独立查看实际 Word/PDF 或图件之后，再用于自己的材料。

已有仓库源码也可放到新目录后明确要求读取那里的 `SKILL.md`；这能试用该副本，但不能算自动发现已经通过。

<a id="claude-web"></a>

## Claude 网页 / Desktop

1. [下载 Claude 技能包](downloads/scientific-figure-studio-claude.zip)，保留 ZIP，不要上传整份 GitHub 源码 ZIP。
2. 在 Claude 的 **Customize → Skills → + → Create skill → Upload a skill** 中导入并启用。账户需要开启代码执行与文件创建；组织策略可能限制导入。
3. [下载首次试用材料](downloads/scientific-figure-studio-first-use.zip)，解压后上传 TASK.md 和 input/ 内的文件，要求使用 `scientific-figure-studio` 完成任务。

无需在本机先安装 Python。实际执行环境仍需具备相应 Python 包和导出工具；缺少的能力会单独报告。此入口指 Claude 自定义技能，不把本地文件路径当作云端可访问附件。

[官方导入说明](https://support.claude.com/en/articles/12512180-use-skills-in-claude) · [官方包结构](https://support.claude.com/en/articles/12512198-how-to-create-custom-skills)

## WorkBuddy

1. [下载 WorkBuddy 技能包](downloads/scientific-figure-studio-workbuddy.zip)。
2. 在 **技能 → 添加技能 → 上传技能** 导入并启用。
3. 解压[首次试用材料](downloads/scientific-figure-studio-first-use.zip)，把 TASK.md 和 input/ 交给 WorkBuddy，明确使用 `scientific-figure-studio`。

不要求手动猜测 WorkBuddy 的内部安装目录。包中补充了它要求的中英文简介、作者和版本字段；核心方法与其他包同源。

[官方安装说明](https://www.codebuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Skills-Market) · [包元信息说明](https://open.workbuddy.cn/en/docs/skill)

## 依赖与第一次任务

技能包装的是工作方法和工具，不包含模型、账户、字体或 LibreOffice。安装成功后先完成[一个小任务](first-use.md)，再处理自己的整篇论文。[依赖与导出](usage.md)

Claude 和 WorkBuddy 目前只有包结构与本地工具验证，客户端导入、自动触发和新生成尚待实测；不要把这份教程当作已测成功的记录。
