# 同一接口的展开与归属修复

唯一选定图在 `output/selected/`：160 × 100 mm 的 SVG/PDF/PNG，以及 `caption.md`、`alt_text.md`、`figure_spec.json` 和 `scene.json`。事实来自固定 constructed DEMO `input/notes.md`；未运行实验。本包是已知匿名模型评语之后的开发修订，不能作为未见材料盲测。

选定构图保留整体四块定位图，主图按 W1 副本 → READY 槽 → 匹配 → ghost → W0 边界使用展开。它让对象和动作相邻，代价是主图中的 W0 局部旋转 180°，查原方位仍需定位图与旋转说明。展开没有创造新邻接或对角交换。

评后仅改三项：明确 `queued (e,16)` 的身份，将拒绝支路连接到匹配检查；释放从金色实际使用边界起始并返回占槽；蓝色统一表示数据副本/使用，紫色只表示释放。后续过期消息处置仍未规定。未改变双槽、标签、等待或写入条件。

`REPORT.md` 记录依据与代价；`after-review-comparison.pdf` 第一页以同样 160 mm 宽显示评前/评后图，其余页为同轮夹具修复。`checks/` 包含最终 96 dpi 正常、灰度、deuteranopia 模拟、独立 SVG 导入、尺寸/哈希及异目录重建记录。生成方实际打开这些图，没有真人可读性接受。独立导入用 LibreOffice → PDF → Poppler，未认证浏览器渲染或真实打印。

## 重建

将 `source/` 和 `input/` 一起移动；从任意工作目录执行，输出目录须不存在：

```text
python -B -X utf8 source/build.py --revision selected --out NEW_DIR --font FONT.ttf --bold-font BOLD.ttf --pdftoppm PATH_TO_PDFTOPPM
```

需要 Python、ReportLab、Pillow、NumPy、pypdf、Poppler 和明确可用的字体。本次使用 Arial 常规/粗体。输出为 `NEW_DIR/selected`。SVG 是图元与文本；PDF 是矢量并嵌字；PNG 为实际渲染。仅复制源和输入的异目录重建已执行，SVG/PNG/场景及文本附件逐字节一致；ReportLab 的 PDF 日期/文档 ID 可变，其绘图流和抽取文字完全一致，见 `checks/portable-rebuild.json`。
