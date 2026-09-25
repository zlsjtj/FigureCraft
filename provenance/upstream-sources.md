# 来源与第三方内容

## 直接复用的代码

`vendor/nature-figure/audit_pdf_text.py` 来自 [Yuan1z0825/nature-skills](https://github.com/Yuan1z0825/nature-skills/tree/79c9f986501ff462f4b9d1294c8223bfee1a5149)，固定提交为 `79c9f986501ff462f4b9d1294c8223bfee1a5149`。该文件保持原样，Apache-2.0 LICENSE 和 NOTICE 保留在同目录。

检查器扫描支持的 PDF 流中的 Tf 字号，不考虑全部坐标变换，不能代替通用碰撞检查或科学审阅。本包显式传入 `--min-pt 8`；这个阈值是内部可读性检查，不是 Nature 或其他期刊的官方标准。

## 数学与设计参考

- Oklab 使用 [Ottosson 的说明](https://bottosson.github.io/posts/oklab/)中的 2021 矩阵。
- 文字对比度参考 [W3C 的解释](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html)，作为内部筛查。
- 选定色觉模拟的 severity 100 矩阵参考 [colorspacious 的 cvd.py](https://github.com/njsmith/colorspacious/blob/master/colorspacious/cvd.py) 中归于 Machado 2009 的数值；本包未复制其 Python 函数，也不把这个移动分支链接当作固定版本软件验证。实际矩阵在 `scripts/palette_tools.py` 中。

其余绘图、语义检查和 DEMO 代码独立实现。采纳了先确定图级信息、跨图角色一致、渲染后检查等方法，没有引入期刊认证、录用保证或“接口调用即科学正确”的假设。

## 参考图与配色

设计参考来自用户提供的五张图及其 RGB/HEX 标注。`assets/reference_palettes.json` 保留 25 对标注色值与来源信息。它们不是从压缩像素反推的数据，也不代表原论文的完整设计系统。

原始截图、期刊页面、字体和私人稿件未分发。截图权利不受上述 Apache 许可覆盖，示例不复制第三方图形或医学机制。五类参考的结构观察见[参考图分析](../references/five-image-style-analysis.md)。

公开版排除了本机执行日志与私人材料，保留通用实现、构造示例、来源说明及可重跑测试。许可状态见 [LICENSE.md](../LICENSE.md)。
