# 同一根电缆的四层包覆

原创结构 DEMO：铜芯、连续绝缘层、实心金属屏蔽套与外护套。半径和长度只是绘图参数，没有尺寸、传输或性能含义。输入见 `input.md`。

这是冻结新版技能后的一次新上下文生成。执行者只获得材料、输出要求与技能；没有预给成图答案。首稿保存在 `first/`；一次自修缩短铜芯，修复端面尖刺，成品在 `final/`。没有普通提示或旧技能对照，不能据此声称因果胜出。

画面用同轴轮廓、错阶端面、连续表面和就近引线解释四层，而非四张材料卡片。空间感来自整体造型与统一明暗；没有流动箭头或虚构机械组件。主标签均10.5 pt，160×90 mm输出；SVG/PDF可编辑，PNG300 dpi。

```powershell
python -m pip install -r examples/stepped-cable/requirements.txt
python examples/stepped-cable/final/build_figure.py --out rebuilt-cable --input examples/stepped-cable/input.md --font "$env:WINDIR/Fonts/arial.ttf" --bold-font "$env:WINDIR/Fonts/arialbd.ttf" --pdftoppm (Get-Command pdftoppm).Source --revision final
```

从FigureCraft仓库根目录执行，输出目录必须不存在。字体与Poppler使用本机安装，不随仓库分发。异目录固定源码重建三个主图字节相同；这与技能从新材料生成源码是两项验证。复现首稿用 `first/build_figure.py --revision first`。

正常色、灰度、一种deuteranomaly模拟和160mm预览已经实际查看；有界SVG审计不覆盖渐变和曲线路径，仍报待审，不能借技术脚本声称科学与视觉全通过。未进行原生三维建模、人类视力或审美试验。浏览器直接SVG截图未生成文件的失败另留本地收据；PDF/PNG与源对象仍已核对。
