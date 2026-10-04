# 在当前客户端执行

从本次实际读取的 `SKILL.md` 所在目录定位脚本与参考，不能假设终端当前目录就是技能目录。根目录记为 `SKILL_ROOT`（是下文占位符，不是预设环境变量）。将命令中的脚本改成这个目录下的实际路径，带空格的路径作为一个参数传入。输入与输出使用任务工作区路径；不向安装目录或插件缓存写成品。

| 使用位置 | 文件与调用 |
|---|---|
| Claude Code 个人技能 | `/scientific-figure-studio`；按已读取的文件定位资源 |
| Claude Code 插件 | `/figurecraft:scientific-figure-studio`；资源仍是同一份根目录 SKILL.md 与 scripts/ |
| Claude 网页 / Desktop 自定义技能 | 使用已启用的 `scientific-figure-studio`，从当前任务附件读取输入；原电脑的绝对路径在云端不可用 |
| WorkBuddy | 从已启用的技能进入；检查输入是在本地任务目录还是附件工作区，不猜测内部安装目录 |
| Codex | `$scientific-figure-studio`；已有正确环境继续沿用 |

有 `package-manifest.json` 时可核对宿主与入口哈希；它是来源记录，不能证明自动触发或生成已成功。多份同名技能并存时记录实际读取的路径，不静默切到旧副本。

选择当前宿主真实可调用的 Python，再按[依赖说明](dependencies.md)检查库、字体和导出程序。在 Codex 可使用其依赖发现工具；其他客户端使用自己的终端与环境，不调用 Codex 专属 API。不要为了准备试用材料就安装全部依赖。

从任意工作目录准备公开小任务（用实际路径替换占位符）：

```text
python "SKILL_ROOT/scripts/first_run.py" --host workbuddy --portable --out NEW_TASK_DIR
python "SKILL_ROOT/scripts/first_run.py" --host claude-code --installation plugin --out NEW_TASK_DIR
```

这两个命令只复制输入和任务说明。随后模型读取任务和原始材料，进行实际编辑或绘图，再运行导出并查看文件。云端交付当前会话可下载的附件，本地交付可打开的实际路径；未导出的 PDF 或 PNG 不能列为成品。
