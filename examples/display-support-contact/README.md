# 支撑脚接触：保留装配，突出关系

这是合成几何 DEMO，无物理实验。当前选中 [final2](selected/candidate-A-final2/figure.svg)。图宽固定 160 mm；不同局部视图采用不同尺度，详见同目录图注与完整四态 CSV。

同样输入的两种首稿保留在 `first-candidates/`。A 将装配与脚槽剖面、释放状态组合，便于区分铰接与可抬离接触；B 将四态叠在同一基座，便于比较角度，却容易被看成多根撑杆，因此未采用。A 的代价是 S1/S3 角度需看图注/CSV。

`candidate-A-refined` 是第一次自修。外部审阅要求明确剖切对应，随后 `candidate-A-final` 虽修好了截面，却把观察方向标签放到抬离箭头旁，产生新歧义。最终只改两处标签：观察方向进入视图标题，`Lift out` 直接归属橙色箭头。失败修复保留，不改记为首次成功。

## 重建

需要 Python、reportlab、numpy、Pillow、pypdf、Poppler 与 Arial 正常/粗体字体。将下面参数替换成当地实际路径；输出目录必须尚不存在。可从任意目录调用脚本的绝对路径。

```powershell
python build_final2.py --out NEW_OUTPUT --font ARIAL_TTF --bold-font ARIAL_BOLD_TTF --pdftoppm PDFTOPPM
```

`build_final2.py` 调用同目录 `build_final.py`、`build_candidates.py`、`native_geometry.py`，并读取 `source-input/finite-record.csv` 与前版场景/图注。所有依赖均包含在本例中。前版文件用于核对非文字图元没有变化，不能用已有 PNG 代替重新生成。

重建两种首稿：`python build_candidates.py --out NEW_OUTPUT --font ARIAL_TTF --bold-font ARIAL_BOLD_TTF --pdftoppm PDFTOPPM`。加 `--refined` 重建第一次自修。

`comparison.html` 展示原图、两首稿与最终选中图。`baseline/` 保留原装配和五个遮挡探针。`validate_development.py --baseline-root baseline --out .` 验证开发版几何；final2 的构建另断言所有非文字图元与经过几何验证的 final 完全相同。技术记录不会自动判断审美。最终模型定向复验见包内当前验收；未获得真人或作者认可。
