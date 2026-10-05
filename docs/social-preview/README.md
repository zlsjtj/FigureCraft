# FigureCraft 品牌封面

![FigureCraft 封面](social-preview.jpg)

这张图用于 GitHub 分享预览，完整封面保留在本页。仓库首页将实际作品前置。深墨色、分层曲面与卷绕造型构成主视觉，缩小后仍以项目名称和用途为重点。

## 文件

- `artwork.png`：选定的原始封面，1774 × 887 像素。
- `social-preview.jpg`：网页与分享版本，小于 1 MB。
- `social-preview.png`：无损副本；`preview-400.png`、`preview-640.png` 用于小尺寸检查。
- `prompt.txt`：本次内置 image_gen 的生成提示词。
- `build.py`、`build-record.json`：格式导出脚本与文件记录。

## 重建导出文件

在仓库根目录运行，输出目录必须尚不存在：

```sh
python -m pip install Pillow
python docs/social-preview/build.py --out /path/to/new-output
```

脚本从已保存的原图导出 JPEG 和小尺寸预览，不调用图像服务，不改布局。重复运行生成提示词会得到新的候选，不能保证逐像素复现。

## 用途与来源

本图由内置 image_gen 生成，用于品牌展示。它是位图插画，不是实验结果，也不是 `scientific-figure-studio` 科研产出的验收案例。实际案例、原始材料和可编辑图源见[案例页](../examples.md)。封面中的输出格式指技能交付能力，不表示此封面自身具有独立可编辑的矢量图层。

上一版的通用图标式构图已改为一个更突出的主体，并减少重复的功能说明。设计比较及小尺寸检查属于模型辅助评估，没有记录为真人审美测试。
