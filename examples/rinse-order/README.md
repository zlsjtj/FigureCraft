# 冲洗顺序：从原始笔记到完整图文

这是构造演示，不是真实实验或性能结果。输入只有零散研究笔记、粗稿和14行结果表，没有预写的贡献主旨。新执行上下文读取本轮技能后生成初稿、自修稿，再由另一模型先看作品、后看来源。评语交回原执行者，由其判断并修成最终稿。没有真人读者参与。

## 这份案例为什么保留

执行者自行选择“同样用液量与时长下，冲洗顺序是否影响所给记录”为主线，先呈现P/Q比较，再解释对L的用液和时间取舍；C的失败与F的许可含义没有被省略。图用一份液路拓扑和两行逆序表达，不凭未知尺寸补内部结构。完整数值留在表中。

独立读者能恢复主线、失败边界和液路，没有发现必须修正的事实或拓扑错误。首次读图对管段边界、传感器作用和Q后续阀态有疑问；源材料复核后确认前两项由图注承担，最后一项本来未给，不能补造。执行者最终只精确限定一个短标签的阶段范围，并补全替代文本；没有为了显示修改量重写已清楚正文。

这证明一次限定材料上的完整流程可执行，不证明新版在所有题材胜过旧版。此任务没有普通提示/旧技能/新技能三组同期比较，也没有重复抽样；本例不能独立归因两版技能的优劣。真实稿件的匿名前后比较另在本地验收中记录，未发表材料不随仓库分发。

## 文件

- `input/`：生成前冻结的任务、笔记、CSV。
- `first/`、`self/`、`final/`：实际各阶段英文正文、caption、alt、可编辑图源及导出。没有回填初稿。
- `READERS_RESPONSE.md`：逐条说明接受或保留的依据。
- `review-first.md`、`review-source.md`：独立模型的首次理解与来源复核，保留得失。
- `hashes.json`：本例文件标识；完整本机运行回执单独归档。

## 重建

字体、Python依赖、Poppler由使用者提供，不随示例分发。先按FigureCraft的README安装其依赖。在FigureCraft仓库中运行；PaperCraft里的相同示例需要把`--skill-root`替换为自己的FigureCraft目录。

```powershell
python examples/rinse-order/final/build_figure.py --skill-root . --input-dir examples/rinse-order/input --out rebuilt-rinse --font C:/Windows/Fonts/arial.ttf --pdftoppm (Get-Command pdftoppm).Source
```

输出目录必须新建。该命令重建已生成源码，不是再次从自然语言生成。SVG可编辑，PDF为矢量，PNG用于入稿；实际图宽160 mm。独立生成与固定源码重建在验收中分别报告。

## Word样例

`documents/`附确切清稿、黄色稿和由原生Word只读导出的PDF。黄色标示这份从粗稿重新组织的新增正文，不是原生Track Changes，也不表示每处都发生了评后修改。first/self/final之间的差异另有阶段文件。

下面的排版适配器不改写正文；先运行前面的图源重建命令，再运行：

```powershell
python examples/rinse-order/build_document.py --input examples/rinse-order/final/manuscript.md --caption examples/rinse-order/final/caption.md --image rebuilt-rinse/exports/figure.png --alt examples/rinse-order/final/alt_text.txt --figure-before-heading "2.2 Ordered rinse and guarded transitions" --output rebuilt-documents/Rinse_clean.docx
```

加`--review`并使用不同输出路径生成黄色稿。Python环境需有python-docx；PDF渲染按宿主文档流程进行，原生Word并非技能随附依赖。最终图注已保持同页，表头按实际列宽核验；首轮图注跨页和表头断词的页面留在本机，未冒称首次排版成功。

本例在本轮生成与审阅结束后才收入技能，首次任务没有看到这些答案。它现在是可学习的开发示例，以后不能再把同一材料声称为独立留出验证。
