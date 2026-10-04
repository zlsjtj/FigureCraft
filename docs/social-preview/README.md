# FigureCraft 分享预览

[PNG](social-preview.png) · [可编辑 SVG](social-preview.svg) · [PDF](social-preview.pdf) · [布局内容](layout.json)

用于分享仓库链接时的预览，1280 × 640。右侧是[共同卷绕示例](../../examples/co-wound-laminate/README.md)原 SVG 中 `assembly` 主体的原始图像；像素和宽高比保持原样，只调整页面放置。尾端放大和标注见完整原图，因此标为“原图局部”。它是原创构造示意，不是测量图或新生成效果测试。

采用已有作品排版，没有重新生成科研对象。字体、配色和导航层级与 PaperCraft 配套。SVG 的文字和布局可编辑，卷绕主体是原有位图，改变结构应修改原案例的源码后重建；不称为全矢量。打开 SVG 时需要对应字体，PDF 已嵌入所用字形，没有分发字体文件。

## 重建

需要 Python 的 `reportlab`、`pypdf`，支持中文的 TrueType 字体（可为 TTC），以及 Poppler 的 `pdftoppm`。在仓库根目录执行，将占位替换为本机路径：

```text
python docs/social-preview/build.py --out ../FigureCraft-share --font CJK_TTF --bold-font CJK_BOLD_TTF --latin-font LATIN_TTF --latin-bold-font LATIN_BOLD_TTF --pdftoppm PDFTOPPM
```

输出目录必须不存在且在仓库外。工具检查文字越界、PDF 文字、PNG 尺寸和体积；`build-record.json` 保存图元来源、字体及输出哈希。这些检查不能证明版式好看，需要打开实际 PNG 复核。

生成 PNG 后，在仓库 Settings → Social preview 上传；本地重建不会上传或改设置。[GitHub 说明](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/customizing-your-repositorys-social-media-preview)

该图未重复插入首页；首页继续展示带局部放大与必要标签的完整卷绕图，科学图内颜色和内容没有为品牌排版而更改。
