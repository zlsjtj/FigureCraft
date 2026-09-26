# 旋转检修罩示例

这是几何定义明确的教学DEMO，不是真实科研结果。8个固定接点由旋转罩的90度开口选择性显露：初态1、2，顺时针转90度后3、4。其余6点由不透明罩遮住；三幅图是同一装置的不同状态。

`description.md`给出英文说明、图注、替代文本和完整角度表；`figure.svg`是可编辑源，`figure.pdf`是嵌入字体的矢量输出，`figure.png`是浏览图。脚本重建到新目录，不覆盖旧输出。

```powershell
python rebuild.py --out new-output --font PATH_TO_ARIAL_TTF --bold-font PATH_TO_ARIAL_BOLD_TTF --pdftoppm PATH_TO_PDFTOPPM
```

依赖Python及reportlab、pypdf、Pillow、numpy、Poppler；字体不打包。用其他字体时重新审阅文字边界。SVG保留文字对象，依赖Arial或兼容字体；PDF嵌入字体子集。

用图学习“固定对象不变，遮挡边界改变可见集合”，不要把圆盘构图套给不相关题材。浅侧缘仅为层次示意，不是真实三维模型。

新上下文试用给出了几何及有限文件检查、两种实际构图、模型自审和换目录重建。未执行实物、真实读者、打印或安全/性能验证；不能把可见集合推导升级为工程效率结论。
