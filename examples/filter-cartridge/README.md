# 过滤盒：用对象关系接替重复说明

这是维护者构造的二维几何教学材料，不是用户的研究，也没有机械性能数据。输入见 [source_material.md](source_material.md)，原段落与条件均保留。原始 provenance 中“current user task as relayed”指任务转交，不意味着这些几何事实来自用户的科研记录。

实际初稿见 [before/figure.png](before/figure.png)，最终图见 [figure.png](figure.png)。已装入和已抽出两状态中，相同框架、滤层编号和邻接关系表达整体移动及层序。初稿同时写了“带两个接口”“两滤层随框架”和“层序保留”等说明；反馈后删除已经可见的重复句。停流条件仍在图内，不能为减字而删除。图注解释不按比例和证据边界。

图源 [figure_spec.json](figure_spec.json) 含独立对象和 motion 关系。英文 [paragraph.md](paragraph.md) 与 [caption.md](caption.md) 为示例产物；[review.md](review.md) 记录实际审阅范围。不是统一卡片模板，也不要求每张图使用轻立体。

## 已做与未做

新执行上下文只收到输入材料、目标及新版技能。初次未能接受 motion；之后修复引擎。两状态初稿仍需要维护者反馈才完成减字，最终不能作为无反馈一次生成成功的证明。已经检查最终正常色、灰度、选定色觉模拟及声明几何；未获得原始几何日志，未作真人阅读、实物、制造和流体试验。

## 重建

安装 Python 的 reportlab、pypdf、Pillow、numpy，并准备 Arial 或兼容字体及 Poppler。将三个输入文件一起复制到任意目录，然后运行：

```powershell
python rebuild.py --skill-root '<scientific-figure-studio目录>' --font '<Arial.ttf>' --pdftoppm '<pdftoppm.exe>' --out '<尚不存在的输出目录>'
```

三个输入为 rebuild.py、figure_spec.json、source_material.md。技能路径必须指向支持 motion 的当前引擎。便携重建已执行；重建固定规格不等同于再次从自然语言生成。
