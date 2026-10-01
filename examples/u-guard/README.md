# U形护架与穿入条

原创几何DEMO，三件实体及位置由input锁定，不是机械实验或实际稳定装配。新执行者只读材料、任务和冻结技能，未读开发产物或评审答案；它自行选了单个正交视图。保留first以及唯一一次自修final。

自修分开了首稿中投影相接的侧缘，并把上间隙8的标注移到白区。代价是穿越护架厚度的确切位置更依赖方向轴和图注，不能用间隙数值正确宣称读图全部完成。它验证了新源码和实际成图能力，不是旧/新技能对照，也不证明Nature完成度。

依赖Python、NumPy、Pillow、ReportLab、pypdf、Poppler和显式字体。SVG/PDF是表面位图加矢量标注的混合文件；几何可改参数化源码，非逐面可编辑SVG。重建从任意工作目录执行，传入下面的真实路径，输出必须是新目录：

```powershell
python <repo>/examples/u-guard/final/build.py --input <repo>/examples/u-guard/input.md --renderer <repo>/examples/u-guard/final/surface_renderer.py --out <new-output> --font <arial.ttf> --bold-font <arialbd.ttf> --pdftoppm <pdftoppm.exe>
```

first/build.py重建首稿，参数相同。两个版本各有160mm嵌入Word/PDF，正常色、灰度和单条件近似色觉图均保留。不要把源码边界检查、模型读图与作者认可合成一个PASS。未做真人、打印、全部色觉或原生Word编辑器试用。
