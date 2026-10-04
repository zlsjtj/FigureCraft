# FigureCraft 客户端入口与首页改进

2026-10-04；版本 1.28.1 的发布前验证。发布结果以 [GitHub Release](https://github.com/zlsjtj/FigureCraft/releases/tag/v1.28.1) 为准。基线提交 `dcebd93084df1eee1a54b36833be08e486199c57`，分支 `feature/evidence-and-visual-compression`；修改前工作树干净。已保存完整回滚 ZIP。

## 问题与实际修改

| 确认的问题 | 修改后的行为 |
|---|---|
| Claude Code 只能手动克隆技能目录 | 新增 `.claude-plugin/` 市场与插件清单，直接引用根 SKILL.md，不维护第二套核心内容；个人目录方式继续可用 |
| 试用脚本无法指定插件命名空间；可搬移任务只有内部 API | `--installation plugin` 使用插件命名空间；`--portable` 为 WorkBuddy 等生成相对路径任务，原默认命令保持不变 |
| 示例命令相对 scripts/，在论文目录照抄会找错位置 | 两技能入口接到运行说明，以实际读取的 SKILL.md 定位脚本，成品放任务目录；不假设 Codex 专属 API 在其他宿主存在 |
| 安装、试用材料、成品入口分散 | 首页保留连续曲面大图，用两个较小作品入口展示装配、剖面与共享关系，减少连续大图占屏；源码随作品出现。 首页可直接选客户端，区分技能 ZIP 与原始材料 ZIP；新增按症状排查入口 |

WorkBuddy 已有作者、版本、中英文简介及完整资源，不重复改写；只在 Claude Code 包中放插件清单。没有默认开启额外工具权限、钩子或外部服务。

## 实际验证

| 层次 | 结果 |
|---|---|
| Claude Code 官方命令 | 2.1.289 在隔离配置目录中校验插件和市场均通过，无警告；实际注册本地市场、安装、启用成功，读取新版源码 |
| 四种宿主包 | 从新目录解压、逐文件核对 manifest；在不同工作目录和含中文空格路径执行准备脚本均成功；可重复打包、拒绝覆盖与旧命令回归通过 |
| 本地 Python 工具 | 单元发现运行 93 项通过；通用 skill 校验通过（隔离 PyYAML + UTF-8 模式） |
| 导出 | WorkBuddy 包解压后在本地 Python 重建：复杂 Word 清稿/黄色稿转 PDF；机制图从源码输出 SVG/PDF/PNG。不是 WorkBuddy 内生成 |
| 保全与页面 | 复杂 Word 的公式内容及 XML、表格、域、超链接等保全；实际两页输出分别查看，旧修订与新黄色可区分；实际成图已查看 |
| Claude 模型调用、网页/Desktop 账户导入、WorkBuddy 客户端导入/生成 | **未执行**；没有可用账户会话，不把插件安装和包检查写成生成成功 |
| GitHub 页面 | 原内置浏览器不可用；已改用隔离无头 Chrome 查看公开页面。发布后复核桌面、390 px 窄屏与深色模式；窄屏模拟不等于真机测试 |
| Star 增长、真实用户认可 | **未验证** |

常驻 Codex 安装副本仍为 1.27.1，未覆盖；此次测试明确指定新仓库或新解压路径。代码内容标识 `ad0b576c43f5bae63f1b66d30f64ea58117dfaf23f43dd7f603c135be4d3abf8`，由入口、运行说明、两脚本、两清单与新增测试的 SHA-256 组合计算，对应提交可从本页上方的固定版本入口查看。

初次官方技能校验缺 PyYAML，补充隔离依赖后遇到 Windows 默认 GBK 读取问题；改用 `python -X utf8` 后通过。首次 npm 获取 CLI 未完整结束，后从官方平台包下载并验证 SHA-512。初次市场校验提示缺 description，补齐后两清单均无警告通过。这些修复不代表论文或图形质量提高。

## 参考了什么

- [Anthropic skills 的 marketplace](https://github.com/anthropics/skills/blob/main/.claude-plugin/marketplace.json)：技能资源和客户端安装入口分开，保持入口可发现。
- [Hugging Face skills](https://github.com/huggingface/skills)：首页直接给安装方式，其 manifest 允许直接引用含 SKILL.md 的目录。参考安装组织，不复制其发布代码。
- [WorkBuddy Skill Hub 适配说明](https://github.com/sandbaseai/workbuddy-skill/blob/main/docs/adapting-skills.zh-CN.md)：区分包来源、平台字段与实际导入，给清楚的 ZIP 入口；客户端要求仍以官方为准。
- [SciencePlots](https://github.com/garrettj403/SciencePlots) 与 [Scientific Visualization Book](https://github.com/rougier/scientific-visualization-book)：用途、作品与最小用法相邻。此次采用作品导航，未复制别人的图、文字或 Star 数据。
- [Claude 插件规范](https://code.claude.com/docs/en/plugins-reference)、[Claude 自定义技能](https://support.claude.com/en/articles/12512198-how-to-create-custom-skills)、[WorkBuddy 元信息](https://open.workbuddy.cn/docs/skill)：确认目录、入口和所需字段。社区示例使用 ZIP 根目录 SKILL.md，官方文档展示技能文件夹；现有单文件夹包未证实不兼容，因此未凭推测更换目录结构。


## 本次发布范围

本次按维护者决定跳过 Claude 网页与 WorkBuddy 的客户端生成实测，不以此阻塞展示与安装包发布。对应能力仍标记未验证。发布后继续根据允许公开的使用反馈改进；本版不新增科研效果、Star 增长或投稿结果声明。
