# 三通旋塞选择器 DEMO

原始任务为 [source.md](source.md)，可编辑脚本为 [build.py](build.py)。这是维护者从新结构材料实际生成的例子，不是独立盲生成试验。结构是两个入口择一汇入一个测量池；两视图是同一装置的替代状态。它不沿用数值偏移、加法或一源分叉模板。

运行 `python build.py --font FONT.ttf --bold-font BOLD.ttf --pdftoppm PATH --out NEW_DIR`。需要 Python、ReportLab、pypdf、Pillow、numpy、Poppler；字体与外部二进制由宿主提供。脚本和 vector_export.py 放在同一目录，从任意工作目录运行；拒绝覆盖已有输出。

独立模型根据实际图和图注正确区分选通、关闭、液流、旋转、90°及停流条件。其后将两处 closed 标签向左移 11 pt，以清开轮廓；关系、数值和配色未变，由维护模型复查。没有真人参与、阅读时间或性能数据。首次导出把命名色传给要求 HEX 的工具，已改显式 HEX；不是一次生成成功。

最终图见 [exports/selector.svg](exports/selector.svg)、[PDF](exports/selector.pdf)、[PNG](exports/selector.png)。图注与替代文本随导出；外观与技术检查不证明真实阀门性能。
