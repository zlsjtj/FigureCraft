# 一次反馈修订：删除含混的开口引线

本稿是在读取 `anonymous-figure/assessment.md` 后进行的反馈修复，不是未见评语的独立生成。原评语副本为 `feedback-assessment.md`，SHA-256 为 `c7725ca1f9eaf8b1556d3ad04a24d5ab295e79293c56e344622f131947fff5d3`。该报告是独立模型辅助比较，不是真人阅读实验或作者认可。

## 判断与选择

值得检验删除方案。评阅者在未读图注的 B 初看记录中，已经从上端 C 形端缘、后方内壁和两侧纵向壁厚面识别了开口及其连续性；随后指出现有引线指向深色内壁，容易把“经开口看到的表面”当成开口本身。已有几何边界正在承担开口说明，引线却新增了对象归属歧义。继续把同一引线端点移到另一有色表面，不能可靠解决空间与表面的区别。

因此只删除 `opening-leader`、`opening-label` 和 `opening-label-2` 三个 SVG 元素；没有增加边界标记、说明文字或面板。保留 Sleeve、Solid core 以及 Radial gap = 4 和尺寸线。原 caption 本来已经命名并定义纵向开口，因此原样保留；alt text 只同步修正“有哪些图内标签”的叙述。

## 改善假设与代价

- 改善假设：读者沿顶部 C 形端缘和连续壁厚面识别开口，不再被一条指向后方内壁的引线带去解释“这个有色表面为何叫开口”。
- 明确代价：图内失去 Longitudinal opening 这一术语锚点，名称需由图注取得；右侧留白增大。仅凭标签数量下降不能证明更清楚。
- 保留的证据：完整对象组、上端环口、两条壁厚面、上端径向间隙及其尺寸线全部原样保留。单视图对周向间隙的证据仍弱于额外轴向视图；本次没有改变该权衡，也没有声称解决下端隐藏面的检查问题。

执行代理已查看本稿 PNG：开口的连续边界仍可见，没有因为删除标签而遮蔽任何物体或尺寸线。这只是生产端观察；“是否损失解释”“净改善是否成立”仍为原匿名评阅者待复查，作者认可未取得。

## 实际修改约束核查

`qa/protected-content-check.json` 记录以下结果：

- 几何、相机、画布尺寸、灯光、对象颜色、网格规格、对象数量及关系、全部锁定数值和图注均未改变。
- `surface.png`、`visible_roles.png`、`surface_record.json`、`caption.txt`、`input.md` 与此前 `final/` 的 SHA-256 完全相同。
- 将此前 SVG 的上述三个元素删除后，XML 序列化内容与本稿完全相同；余下全部文字与引线记录也完全相同。
- PDF 保持 160 × 95 mm；现有文字最小 10.5 pt。首稿和此前自修稿 PNG 哈希均未变化。

`qa/portable-rebuild.json` 记录复制源码、输入和评语至新目录后的实际执行命令。换工作目录、显式给出 `--skill` 后，重新生成的 SVG、PNG、表面图、灰度、近似色觉预览、caption、alt 共七项哈希一致。这是同源重建核验，不计作另一次反馈修订或无反馈生成。

## 使用与状态

主文件为 `figure.svg`、`figure.pdf`、`figure.png`，可编辑源为 `build_figure.py` 和 `figure_spec.json`。仍为混合文件：表面位图与独立矢量文字/引线。`comparison.html` 可同尺寸查看此前自修稿与本稿。

重建需要 Python 的 numpy、Pillow、reportlab、pypdf，以及 Poppler。命令参数与此前相同，新增：

```text
--revision post-review --review PATH/feedback-assessment.md
```

源码要求显式 `--skill` 候选技能根路径，拒绝覆盖已有输出。对应环境的完整运行命令见 `checks.json` 和 `qa/portable-rebuild.json`。

有限修改约束与重建核查已通过；原评阅者复查 PENDING，作者认可 NOT_RUN，整体 REVIEW_REQUIRED。没有使用自评分或虚构阅读效率来代替本稿。
