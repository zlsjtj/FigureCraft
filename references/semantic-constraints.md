# 对象、状态、方向与入稿尺寸（1.1）

`templates/semantic_scene.json` 可直接渲染。以下检查验证声明与图元的一致性，不能证明声明本身符合研究事实。真实任务先从原稿、实现或数据确定预期集合，不能按成图反向编造预期值来通过检查。

## 完整对象集合

```json
{
  "name": "storage cells",
  "expected": 2,
  "scope": {"id_prefix": "cell-"},
  "expected_logical_ids": ["source-cell", "target-cell"],
  "expected_states": {"source-cell": true, "target-cell": false},
  "state_field": "occupied",
  "state_styles": [
    {"state": true, "style": {"fill": "@storage.fill"}},
    {"state": false, "style": {"fill": "#FFFFFF"}}
  ]
}
```

`scope` 支持 `id_prefix` 或 `entity`，同时给定时取交集。必须覆盖整个被计数区域内相关的对象、装饰面、图例和局部放大；范围选择过窄会漏审，检查器不会从未标注的图形推断它也是一个存储格。每个命中的图元显式设置：

- `object_part: "primary"` 与 `logical_id`：每个逻辑对象恰有一个主表示。多画、漏画和同一对象重复主表示均失败。
- `object_part: "decoration"` 与原对象的 `logical_id`：例如侧面、阴影，不增加对象数。
- `object_part: "detail"` 与原对象的 `logical_id`：重复局部视图，不增加对象数；图注仍要说明其是放大视图。
- `object_part: "legend"`：图例符号，不计入实际对象。

有状态的对象还需 `expected_states` 覆盖全部逻辑ID，并指定每个主图元的状态字段。`state_styles` 将预期状态绑定到实际渲染属性；只比对布尔标记不足以发现“标记仍为占用、颜色却画为空”。可用填充、轮廓或其他显式图元属性，但要检查其科学含义。状态存在但未声明预期值或视觉编码时为 REVIEW_REQUIRED。

旧 `item_ids` 约束仍检查各对象存在、数量正确；缺少完整scope/状态信息时为 REVIEW_REQUIRED，而不是完整可数对象验收PASS。`locked_values` 是证据锁，不能替代对象计数。

## 关系端点与箭头

在已有 `id/from/to/kind/meaning` 关系上增加：

```json
"geometry": {
  "item_id": "transfer-line",
  "from": [300,165], "to": [480,165], "tolerance": 0.1,
  "arrow": {"item_id":"transfer-head", "tip":[480,165], "base":[463,165]}
}
```

`item_id` 指向带同一 `relation` ID 的线/开放路径。起点终点必须与预期方向吻合。箭头自动检查只支持三顶点polygon：尖端为 `tip`，另两点中点为 `base`，尖端必须落在线终点，方向必须与最后一段/曲线切向一致。线可多段；曲线碰撞仍不在自动保证范围内。无箭头的真实关系可显式 `arrow_required:false`；这不应被用来绕过一条本应有方向的箭头。

缺少geometry、复杂箭头形状、多子路径或闭合关系路径无法自动判向时，保留 REVIEW_REQUIRED。不要把未知方向写成PASS。自动方向检查也不能证明实体之间存在因果或科学联系。

## 实际入稿尺寸

`output.width_mm` 是独立导出尺寸；`output.placement_width_mm` 是最终文稿中的显示宽度。两者可不同。命令行 `--placement-width-mm` 覆盖本次检查/导出的放置尺寸声明。有效字号为：

`viewBox字号 × placement_width_mm × 72 / 25.4 / view_width`

默认8pt下限仅是工具检查策略。实际图宽读取当前文稿的 drawing 尺寸，不套用示例的160mm。未提供入稿尺寸时此项为 REVIEW_REQUIRED。提供了尺寸也必须查看最终Word/PDF页，检查裁剪、缩放和实际可读性。

## 外部SVG与其他后端

保留已有可编辑生成器。`scripts/semantic_audit.py` 的 `audit_semantics(spec)` 不依赖渲染库，可对外部后端提取的 `items/count_constraints/relations` 检查。但它不会自行解析任意SVG、滤镜或CSS。外部工作流必须从**实际最终SVG**提取几何/逻辑属性，绑定文件哈希，并记录哪些布局或碰撞不受核心检查支持；不能只检查未绑定的手写sidecar，然后声称成图已通过。

## 状态解释

`technical_status` 汇总实际技术失败；PDF、计数、状态或方向失败会向上传播。`status` 仅保留该字段的旧接口别名。`scientific_review_status`、`visual_review_status` 默认 REVIEW_REQUIRED；`overall_status` 在这些检查未做时不能PASS。真实代理/作者审阅应另存审阅人、版本哈希、观察和问题处理记录，不能改一行状态替代审阅。
