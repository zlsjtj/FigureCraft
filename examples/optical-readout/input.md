# 双通道透射读出 DEMO：提供给编辑和绘图者的原始材料

这是原创教学内容，不是真实仪器、实验结果或待投稿研究。请用给定的 PaperCraft 和 FigureCraft 改善一段关键叙事并制作一张解释机制的图，交付可编辑源和实际图像。读者是具有基本实验常识、尚不了解本装置的人。目标：更快理解问题、设计作用及证据边界；图精美、清楚、适当有体积感、少小字，不把全部对象画成相同卡片。允许重组表达；不新增机制和性能事实。图放在 160 mm 宽版面，高度不超过 90 mm。

## 完整科学内容

- 只有一个光源 S、一个可开闭的快门 H、一个分光片 B、一个样品 P、两个探测器 R 和 T。
- 顺序是 S 到 H 再到 B。B 把入射光分到两条支路：参考支路直接到 R；测量支路穿过 P 再到 T。H 位于两条支路分开之前；关闭 H 时，两条支路都没有来自 S 的光。没有反馈光路、反射回路或第二个光源。
- 一次完整读出包含暗态和亮态：关 H 时记录 R0、T0；开 H 时记录 R1、T1。样品和探测器在两态中不移动，也不是两套仪器。
- 输出定义为 q=(T1-T0)/(R1-R0)。这只是本 DEMO 的读出定义，没有额外校准常数，不能称为绝对透射率或保证抵消所有漂移。
- 当 R1-R0<=0 时拒绝本次计算，返回 INVALID，不除以零，也不把错误置为零。
- 设计动机：直接比较 T1 会把探测器暗值和源强变化一起带入读数；本方案显式记录暗值，并用同期参考差值作归一化。没有噪声、光谱、时间漂移或真实装置准确度证据。
- 已完成的演示性逻辑检查如下。它们是构造的输入，不是实测：
  - R0=2,T0=3,R1=12,T1=8 → q=0.5。
  - R0=2,T0=3,R1=22,T1=13 → q=0.5。
  - R0=2,T0=3,R1=2,T1=8 → INVALID。
  - R0=2,T0=3,R1=1,T1=8 → INVALID。
- 前两个例子仅说明给定理想输入下比例相同；后两个核对无效分母的处理。无真实准确度、速度、信噪比或优于文献的结论。

## 原段落

The demonstrator comprises a source, a shutter, a splitter, a sample and two detectors. It acquires dark and illuminated readings and implements subtraction, division and denominator validation. Four constructed cases check the output and invalid-state handling. The components and software form a complete dual-channel readout procedure.

## 当前图的内容

旧图是顺序的相同矩形：Source → Shutter → Splitter；随后分叉为 Reference detector 和 Sample → Transmission detector。下方相同矩形写 Dark readings → Light readings → Subtract → Divide → Check denominator。后半流程顺序存在需要判断的问题。没有样品、分光片或快门的对象造型，没有表示两种状态下哪些对象相同。

## 本次交付

提交实际改写段落、图注、SVG（文字和对象可编辑）、矢量 PDF、PNG、重建脚本和简短说明。说明你加载了哪些技能文件、选择的表达方式、实际检查、遗留问题。无需给自己的作品打分；文件是否改善由后续对照审阅判断。原始目标和事实来自本任务书，技能提供方法，不把任务书里的建议当作版式答案。
