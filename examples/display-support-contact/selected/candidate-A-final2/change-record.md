# 标注归属的单点修复

前版 `candidate-A-final` 新增了语义歧义：`View +y` 邻近橙色竖直箭头，可能把抬离方向读成观察方向。该版完整保留为失败修复记录，不能靠图注纠正画面。

当前只改两个文字图元：

1. 截面标题改为 `A · S2 section · view +y`，明确观察方向归属整个截面。
2. 原独立 `View +y` 改为橙色箭头旁的 `Lift out`，仍为8.5 pt。

全部非文字图元与前版逐项相同，数据CSV逐字相同；没有改几何、接触、箭头方向、状态或构图。160×99 mm、最小8.3 pt不变。代理已重新查看正常、灰度与名义96dpi成图，文字无出界，标签检查没有引线穿字项；六项保守多边形背景检查仍为 REVIEW_REQUIRED。不是新修订的独立验收或作者认可。

重建命令（输出目录必须尚不存在）：

```powershell
python ../../build_final2.py --out NEW_OUTPUT --font ARIAL_TTF --bold-font ARIAL_BOLD_TTF --pdftoppm PDFTOPPM
```

图注、替代文本与完整四态CSV均在本目录；真实技能未修改。
