# 共用放置记录的两路图像

这是原创MosaicPair构造演示，不是实验图像或研究结果。科学任务是两路tile读取同一份放置记录，分别重采样到各自mosaic。图内没有规定的掩膜形状不补画。

原图让配准、回退和处理框占据主体；新图让输入与其放置后的对象上下对应，共用记录置于中央。对两个不同构图进行匿名模型比较后，选择成对上下结构，再吸收另一候选的read t标签与共同坐标例子。普通支线表示引用，箭头表示重采样。读者可直接跟踪对象的位置变化。

两版均160×100 mm，最低9 pt，没有缩字或扩大画布。代价是图注由约135词增至约170词，用于承接选择规则、未知掩膜和适用边界。图形变清楚不等于全文文字都变少。首评与定向复验保留，没有真人审美认可。

## 重建

需要Python、reportlab、pypdf、Pillow、numpy、Arial正常/粗体字体和Poppler。输入在source/inputs，生成器参数化且不依赖私有文稿。

```powershell
python -B source/build.py --out rebuilt --variant vertical --font ARIAL_TTF --bold-font ARIAL_BOLD_TTF --pdftoppm PDFTOPPM
python -B source/verify.py --root . --rendered rebuilt --rebuild-out verification-rebuilt --receipt verification.json --font ARIAL_TTF --bold-font ARIAL_BOLD_TTF --pdftoppm PDFTOPPM
```

输出目录必须不存在；导出SVG、矢量PDF、PNG、灰度及选定色觉模拟、图注和替代文本。固定源码已跨目录重建；自然语言创作与模型审阅是另一层验证。本例是开发后作品，今后不再作为未见材料。

第二条命令核对19项具体几何与语义条件，并从源码再生成一份文件，与第一份的7个导出文件逐一比对。它不评价美观程度，也不把固定源码重建当作技能自主创作的证明。
