# 语义配色与可审计派生

## 两层资产

`assets/reference_palettes.json` 原样保存五图25对带标注色值与来源，绝不自动修正来源记录。`palette_tools.py validate` 检查 RGB 三个0–255整数与 HEX 算术是否相符；只证明算术。发现冲突应报告差异，保留原记录。

`role_map` 把科学角色映射到其中一个 swatch 或明确指定的 base。每个角色产生 base/fill/stroke/highlight/shadow/marker/text 七种 token，写入 manifest。新增 token 是本技能设计，不是参考原色。角色名应描述 control、candidate、core、coating、retained_input 等含义，不能用“好”“坏”替代实际对象；比较方法的色不随某个观测的正负翻转。

## 算法与限制

派生版本1.0.0：sRGB → linear RGB → Oklab，使用 Ottosson 2021 矩阵；固定明度/色相下每步将彩度乘0.95直到进入sRGB，最多100步。明度、彩度的具体规则在 derive() 中公开。优先改变明度和适度降低彩度；不用逐通道RGB加白冒充感知均匀。最终8bit量化可能略有色差，没有专业色彩设备校准。

文字在深墨/白色间选择较高对比度；填充浅时使用深描边及文字。W3C 4.5:1 用作普通文字的内部筛查参考，不是期刊规定。`composite(fg,bg,alpha)` 按编码sRGB做简单透明合成；不能把它称为线性光混合。透明叠加时必须在实际底色验证，复杂遮挡/渐变的实际对比度需看渲染图。自动检查只对**声明背景**负责，不能替代对真实叠层的检查。

当文字直接压在支撑面或曲面上，先定位实际承载它的图元，再填写 `background`，不能沿用白色默认值后引用对比度 PASS。对渐变/透明叠层应查看文字覆盖范围内最不利的实际背景，必要时移动标签或换字色。场景 API 不支持 `background_item_id` 自动绑定，也不自动采样合成背景；外来 SVG 的可选检查只覆盖显式画布和支持的实色矩形内部，见[已有 SVG 检查](existing-svg-review.md)。不将此有限覆盖宣称为通用合成背景审计。独立试用曾因声明白底而漏掉深色支撑上的低对比文字，人工看图才发现。

定量顺序数据用单调亮度尺度，正负变化可用围绕中性点的发散尺度；类别色不表达大小。当前脚本提供角色配色，不自动生成/认证连续科学色图；需要连续色图时使用已核实的绘图库并检查亮度单调性、量纲与色条。

## 非颜色线索与预览

形状、实线/虚线、直接标签、清晰边界、位置应至少提供一种独立辨识手段；色盲模拟后近色不等于任务失败，只靠近色区分才有风险。灰度预览采用linear-sRGB亮度。另一个预览使用 Machado 2009 deuteranomaly severity 100 的3×3矩阵并裁剪到sRGB；常称重度绿色觉缺失模拟。此处只有一种条件，没有安装colorspacious，不称为完整色觉认证。算法与参数随 manifest 保存，检查预览后单独记录审阅结果。

## 只换色

对本引擎场景使用 recolor 命令，比较 semantic_digest 与 geometry_digest，检查实际SVG颜色发生改变。几何哈希包含文字、位置、箭头、线宽、透明度、对象顺序、角色绑定和尺寸。对任意SVG/PDF必须使用相应解析/编辑工具建立等价锁；本引擎不自动把外来PDF变成可编辑场景。光栅图编辑遵循可用图像编辑工具工作流，明确文字和对象无法逐项编辑，不能假称矢量化。

来源：[Oklab作者说明](https://bottosson.github.io/posts/oklab/)，[W3C对比度说明](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html)，[Machado论文DOI](https://doi.org/10.1109/TVCG.2009.113)。本次矩阵交叉核对 colorspacious 的 cvd.py；不是该库运行测试。
