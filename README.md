# FigureCraft｜科研绘图与配色

把研究中的结构、动作和关系画清楚，交付 **可编辑图源、SVG / PDF / PNG 和重建脚本**。

**[拿公开材料画一张图](docs/first-use.md)** · [安装技能](docs/install.md) · [看前后对照](#让对象变化成为主角)

[![三层材料共同卷绕，尾端露出连续结构的层序；点击查看原图](examples/co-wound-laminate/selected/figure.png)](examples/co-wound-laminate/selected/figure.png)

三层材料共同卷绕，尾端露出层序。颜色对应材料身份，局部展开仍属于同一整体。

[SVG](examples/co-wound-laminate/selected/figure.svg) · [PDF](examples/co-wound-laminate/selected/figure.pdf) · [Python 源码](examples/co-wound-laminate/build_laminate.py) · [输入与构图选择](examples/co-wound-laminate/README.md)

本页均为原创构造示例，不代表实验结果。上图的曲面为位图、标签为矢量；曲面可通过源码修改后重建。

## 开始使用

这是在 Codex 等 AI 工具中使用的技能，需要所用工具能够读写文件、执行代码。

先用[公开材料包](docs/downloads/scientific-figure-studio-first-use.zip)做一张机制图：解压后把 TASK.md 和 input/ 交给所用工具，不需要自己先写绘图代码。

| 你使用的工具 | 安装入口 |
|---|---|
| Codex | [本地安装](docs/install.md#codex) |
| Claude Code | [本地安装](docs/install.md#claude-code) |
| Claude 网页 / Desktop | [上传技能 ZIP](docs/install.md#claude-web) |
| WorkBuddy | [上传技能 ZIP](docs/install.md#workbuddy) |

Codex 已有本地产出；Claude 与 WorkBuddy 的包已检查，客户端实测待完成。[具体范围](docs/multihost-validation.md)

安装后，有自己的材料可以这样说：

```text
使用 scientific-figure-studio。
根据这份材料重画一张机制图。
先确定最需要看懂的关系，再选择构图。
保留必要标签、条件和单位。
按 160 mm 图宽检查，交付可编辑图源、
SVG/PDF/PNG、图注与前后对照。
```

图宽可以换成你的版式。只想调整配色，也可以明确保留现有内容和构图。[依赖与导出命令](docs/usage.md)

## 让对象变化成为主角

两路图像使用同一份放置记录。改图把输入与结果上下对应，共用记录放在中间，读者可以沿对象追踪变化。

[![改图：两路输入与结果上下对应，共用记录居中](examples/paired-placement/selected/figure.png)](examples/paired-placement/selected/figure.png)

<details>
<summary>展开原图：多个处理步骤占据主画面</summary>

[![原图：选择、分支和重采样分散在多个处理框中](examples/paired-placement/before/figure.png)](examples/paired-placement/before/figure.png)

</details>

两图均为 **160 × 100 mm**，标签没有缩小。图内保留关键选择条件与坐标例子；无箭头支线表示共同读取，箭头表示重采样。图注补充读图规则与适用边界，手机上可点图放大。

[SVG](examples/paired-placement/selected/figure.svg) · [PDF](examples/paired-placement/selected/figure.pdf) · [图注、输入与源码](examples/paired-placement/README.md)

## 不同结构，换一种画法

- 构件如何装配，缺口是否露得清楚：[交叉搭接与剖面](examples/cross-lap-trial/README.md)。
- 接触部位怎样解除：[支架整体、局部接触与释放状态](examples/display-support-contact/README.md)。
- 重复单元很多，怎样解释局部变化：[离子交换示意](examples/exchange-granularity/README.md)。

[更多作品](docs/examples.md) · [构图教程](docs/from-materials-to-paper.md) · [32 秒案例导览](docs/quick-tour/tour.gif)

案例导览展示已完成作品，不是实时生成录像。完整案例保留了首次方案、修改理由和没有解决的取舍。

## 使用边界与反馈

科学关系和数据以材料为准。低分辨率截图不能恢复缺失实验数据；机制示意也不能冒充测量结果。定量图保持准确尺度，最终图仍需按入稿尺寸核对。[验证记录](docs/usage.md#检查与复用)

SVG/PDF 的可编辑范围依绘图方式而定；混合位图会单独说明。案例经过开发和模型审阅，不能代替作者的科学判断与审美认可。

如果一条连线容易读错，或标签入稿后太小，欢迎[提交反馈](https://github.com/zlsjtj/FigureCraft/issues/new?template=usage.yml)，附上允许公开的示例和目标尺寸。

如果这些图和源码对你有用，欢迎点一个 Star，留作绘图参考。论文表达可配合 [PaperCraft](https://github.com/zlsjtj/PaperCraft)。

原创代码与文字采用 [MIT](LICENSE) 许可；第三方内容见[许可说明](docs/licensing.md)。
