# 同一材料的两种构图：共享参考与独立记录

这是原创教学示意，不包含实验结果。固定材料在 [input/figure-task.md](input/figure-task.md)。一块被动棋盘由两台固定相机观察，各自计算角点残差并写入自己的记录；没有相机互传，也没有记录合并。

## 实际选择及代价

| 候选 | 得到什么 | 失去什么 | 结论 |
|---|---|---|---|
| [旧技能候选](alternative/figure.png) | 观察/写入标签紧邻对应分支，版面较干净 | 相机外形近似普通盒子 | 保留；需要优先保证关系归属时有价值 |
| [新版技能候选](figure.png) | 镜头、支架让相机更易识别，标题点明共享参考与独立记录 | 残差标签离输出箭头较远，相向相机可能诱发真实光路推断 | 保留为可审阅候选，不能宣称全面胜出 |

两个产物由不同的新上下文代理根据同一输入生成，独立代理匿名盲读后作出上述取舍判断。没有真人测试。维护者没有在看到盲读结果后修图再冒充初次产物。旧图 160 × 96 mm，新图 160 × 90 mm，均在同宽度比较；屏幕物理尺寸未校准。

这不是一个要求照搬的模板。它展示：少字与更易认出的实体并不自动解决关系归属；图注能说明示意条件，却不能消除画面诱发的所有空间误读。保留旧候选是允许的维护决策。

## 重建

从仓库根目录运行，字体及 Poppler 使用自己的实际路径：

```powershell
python examples/common-reference-demo/rebuild.py --out test-output/common-reference --font $figureFont --pdftoppm $figureRaster
python examples/common-reference-demo/alternative/build.py --out test-output/common-reference-alternative --font $figureFont --bold-font (Join-Path $env:WINDIR 'Fonts/arialbd.ttf') --pdftoppm $figureRaster
```

新版源为 [figure_spec.json](figure_spec.json)，旧候选的几何源为 [alternative/build.py](alternative/build.py)。SVG 中各对象可编辑；重建要用新目录。新版采用 reference 与 flow 两种场景关系，不把无方向观察画成数字传输。此案例未调用 relation_branch，不能用它替代该组件的单元验证。

本例是固定源码重建。再次让技能根据原材料生成，是另一项验证；不能把二者混为一谈。
