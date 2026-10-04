# 第一次用：画一张机制图

先用公开的教学材料完成一个小任务。材料是构造示例，不需要上传未发表论文。先按[工具入口](install.md)安装技能。

## 直接拿材料试

1. [下载试用材料包](downloads/scientific-figure-studio-first-use.zip)并解压。
2. 本地工具读取整个目录；Claude 网页端上传 TASK.md 和 input/ 中的文件。
3. 告诉所用工具：**使用 FigureCraft（scientific-figure-studio），执行 TASK.md，把结果放进独立 output/。**

包中只有原始材料和任务要求，没有改写答案或已选构图。不需要先运行准备脚本。导出文件需要宿主环境中的实际依赖；安装步骤与[依赖说明](usage.md)分开。

## 喜欢用命令行时

在已安装技能的根目录运行：

```text
python scripts/first_run.py --host codex --out ../FigureCraft-try
```

`--host` 可换成 `claude-code`、`claude` 或 `workbuddy`。不传时仍为 Codex，兼容旧命令。输出目录必须是新目录，且位于技能目录外。

这条命令只复制材料、准备 TASK.md，不调用模型、不生成成品、不安装依赖。`claude` 使用相对附件路径；本地宿主的任务会指明实际技能路径。environment.json 是环境查找记录，不是运行结果。命令会显示所用 Python 和缺少的模块；材料准备成功不代表该 Python 已能导出成品。云端任务不检查本机 Python。

## 拿到什么，怎么看

得到可编辑图源、重建脚本、SVG/PDF/PNG、图注和简短中文说明。两路图像仍须使用同一份放置记录，画面不能引入材料未提供的物理位置。按 160 × 100 mm 看标签、对象和关系，不只检查放大的 PNG。

字体、模块或 PDF 渲染缺失时，应说明未完成的导出，不把文件存在当作视觉验收。作品效果仍需阅读和看图。

完成后再看[公开案例](../examples/paired-placement/README.md)，比较它怎样组织解释，而非逐句或逐形照抄。首次试用与固定源码重建是两种检查，记录见[本轮范围](multihost-validation.md)。

## 换成自己的材料

提供科学对象、关系、原图或数据，以及最终图宽。风格参考只用于构图与配色，不能代替研究事实。

材料不足时先完成有依据的部分，缺项单独列出。保留原件，新结果另存。
