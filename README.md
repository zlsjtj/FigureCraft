<h1 align="center">FigureCraft</h1>
<p align="center"><strong>让图形讲清关系，让作品经得起细看。</strong><br>科研绘图与语义配色 · 可编辑图源 · SVG / PDF / PNG</p>
<p align="center"><a href="#作品与图源">看作品</a> · <a href="#开始使用">下载安装</a> · <a href="docs/examples.md">案例与源码</a> · <a href="LICENSE">MIT</a></p>

给 AI 研究助手使用的科研绘图技能。把研究材料变成**对象可辨、关系清楚、层次分明**的机制图与结构图，交付**可编辑源文件、SVG / PDF / PNG 和重建脚本**。从构图到语义配色，让画面承担解释。

## 作品与图源

[![三层连续卷绕：主体与同一尾端的立体局部](examples/co-wound-editorial/selected/figure.png)](examples/co-wound-editorial/README.md)

**一张图，连起整体与局部。** 三层材料共同卷绕，局部放大同一尾端；颜色追踪材料，曲面与端面交代层序，虚线说明两幅视图的对应。

**[打开完整案例](examples/co-wound-editorial/README.md)** · [可编辑源码](examples/co-wound-editorial/build_figure.py) · [SVG](examples/co-wound-editorial/selected/figure.svg) · [PDF](examples/co-wound-editorial/selected/figure.pdf)

<sub>原创结构演示。曲面为位图、标签为矢量；修改源码可重建曲面。</sub>

### 同一个问题，两张图接着讲

[![先自由贴合，再保持接触锁定；条带比较三种操作模式](examples/lock-timing-story/selected/mechanism.png)](examples/lock-timing-story/README.md)

**先解释怎么做，再看值不值得。** 机制图让同一夹具的两个状态接起来，结果图保留九行数据的全部三项指标。两图已经进入 PaperCraft 的三页完整稿，图注、正文与数据可以一起核对。

**[看整套图与取舍](examples/lock-timing-story/README.md)** · [完整结果图](examples/lock-timing-story/selected/results.png) · [可编辑源码](examples/lock-timing-story/build.py) · [看实际论文页面](https://github.com/zlsjtj/PaperCraft/blob/main/examples/clamp-timing/complete/selected/clean.pdf)

<sub>公开教学构造案例。机制图为矢量示意；定量图保持二维，全部数值可从 CSV 核对。</sub>

## 开始使用

**[看一次完整试用](docs/first-run/README.md)**：从材料包开始，复制任务，再打开实际生成的文件。

选择你使用的 AI 客户端，安装技能后交给它材料：

- **Claude 网页 / Desktop**：[下载技能 ZIP](https://github.com/zlsjtj/FigureCraft/releases/download/v1.28.1/scientific-figure-studio-claude.zip) · [导入说明](docs/install.md#claude-web)
- **WorkBuddy**：[下载技能 ZIP](https://github.com/zlsjtj/FigureCraft/releases/download/v1.28.1/scientific-figure-studio-workbuddy.zip) · [导入说明](docs/install.md#workbuddy)
- **Claude Code**：[插件安装，两条命令](docs/install.md#claude-code)
- **Codex**：[安装到技能目录](docs/install.md#codex)

**先画一张机制图：**[下载示例材料](https://github.com/zlsjtj/FigureCraft/releases/download/v1.28.1/scientific-figure-studio-first-use.zip)，解压后把 `TASK.md` 和 `input/` 交给客户端。技能 ZIP 保持压缩状态导入；示例材料 ZIP 解压后使用。

有自己的材料，可以直接说：

```text
使用 scientific-figure-studio，根据这份材料画一张机制图。
自行确定最需要看懂的关系，再选择构图。
保留必要标签、条件和单位；按 160 mm 图宽检查。
交付可编辑图源、SVG/PDF/PNG、图注和重建方法。
```

[完整使用教程](docs/first-use.md) · [安装与常见问题](docs/install.md) · [导出与运行依赖](docs/usage.md)

## 看图，也能带走源码

- [支架接触与释放](examples/display-support-contact/README.md)：把整体、接触局部和解除状态连起来。
- [装配与剖面](examples/cross-lap-trial/README.md)：追踪互补缺口与剖切位置。
- [共享记录与对象变化](examples/paired-placement/README.md)：区分共同读取与重采样。
- [离子交换示意](examples/exchange-granularity/README.md)：用局部变化解释大量重复单元。
- [从材料到构图](docs/from-materials-to-paper.md)：保留什么、放进图注什么，以及怎样选择方案。

[完整作品集](docs/examples.md) · [32 秒作品导览](docs/quick-tour/tour.gif)

## 下一张图，一起画好

欢迎[带一张难画的图来提 Issue](https://github.com/zlsjtj/FigureCraft/issues/new?template=usage.yml)：附允许公开的材料、目标尺寸，以及你希望读者看懂的关系。

**觉得作品和源码有用，点个 Star，留作下次画图的参考。** 论文叙事可搭配 [PaperCraft](https://github.com/zlsjtj/PaperCraft)。

[转发这个案例](docs/from-materials-to-paper.md) · 原创部分采用 [MIT](LICENSE)；[第三方许可](docs/licensing.md)、[实现与验证记录](docs/client-entry-validation.md)另列。
