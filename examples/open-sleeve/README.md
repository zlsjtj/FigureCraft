# 开口套筒的单视图与双视图

同一份几何输入，两个独立上下文分别读取修改前和候选技能，先生成首稿，再各自自修一次。没有指定相机或面板答案。输入是原创 DEMO，不是实验结果。它检验怎样用表面与遮挡解释开口、内芯和间隙，不代表所有材料机制图。

## 实际选择

`control/final` 的斜视图加轴向图，能更直接地看清不接触和周向间隙；代价是双视图对应和注意力转移。`candidate/final` 用一个正交立体视图，整体与壁厚更集中；间隙较依赖尺寸线，不能说少一个面板就全面更好。两者的第一次完整输出仍在 `first`。

匿名模型评阅先看图再看图注，详见 [原评阅](anonymous-assessment.md)：没有无条件胜者。两幅图的开口引线都可能让人把有色内壁当成开口。

`candidate/post-review` 是明确接受反馈后的一次修复。只删掉多余且含混的开口引线及标签；C形端缘、纵向壁厚面仍显示开口，图注给出术语。没有改变几何、相机、光照、间距、画布或字号，也没有把反馈修复倒记为首次生成。间隙优先的任务仍可选双视图，整体结构优先的任务可选单视图；这里没有固定模板答案。

## 重建

依赖 Python、NumPy、Pillow、ReportLab、pypdf 和 Poppler。字体显式给定，图宽160 mm、图高95 mm。以下从仓库根目录运行，所有输出目录必须是新的：

```powershell
$python = '<Python executable>'
$font = '<arial.ttf>'
$bold = '<arialbd.ttf>'
$poppler = '<pdftoppm.exe>'
& $python examples/open-sleeve/control/build_figure.py --skill . --input examples/open-sleeve/input.md --out output/sleeve-control --stage final --font $font --bold-font $bold --pdftoppm $poppler
& $python examples/open-sleeve/candidate/build_figure.py --skill . --input examples/open-sleeve/input.md --out output/sleeve-candidate --revision final --font $font --bold-font $bold --pdftoppm $poppler
```

反馈修复使用独立源码，不能用自修稿源码冒充。完整命令：

```powershell
& $python examples/open-sleeve/candidate/post-review/build_figure.py --skill . --input examples/open-sleeve/input.md --out output/sleeve-post-review --revision post-review --review examples/open-sleeve/candidate/post-review/feedback-assessment.md --font $font --bold-font $bold --pdftoppm $poppler
```

[反馈后的复查](post-review-assessment.md)确认：少了指错对象的风险，但也失去图内术语锚点；整体胜出没有得到证明。原DECISION和首次评语保留其当时状态，最终取舍以该复查为准。

SVG/PDF 均为混合文件：独立矢量文字、引线与嵌入表面位图。修改形状需编辑参数化源码后重建，不宣称全矢量或可在SVG内逐面编辑。正常色、灰度与一种色觉模拟均有导出。角色/深度抽样、源码重建、实际新材料生成和审美认可分开记录。

这不是严格控制计算预算的实验，没有普通提示组、重复采样或真人审美测试。它已进入示例包，后续不能再把同一题称为未见任务。技能PDF检查器对其中一份多重编码流未能解析；失败保留，另用pypdf检查字号，不将原失败改成通过。
