# 可执行场景契约 v1（1.1兼容扩展）

本引擎使用JSON，不需YAML。`templates/figure_spec.json`是最小可运行DEMO契约；真实任务替换内容与几何，不能只改标题。更多可运行例子在examples。程序检查有限必填字段及引用，不是全功能JSON Schema验证器。

| 字段 | 含义 |
|---|---|
| figure_id, schema_version, mode | 稳定图名、1、new_schematic/recolor/quantitative等任务模式 |
| scientific_message, demo, evidence_status | 一句话信息；DEMO标志；证据状态需具体，不等于作者认可 |
| source_refs, forbidden_implications | 原始材料/出处/哈希、不能引申的结论 |
| entities | id、semantic_role、description；可数对象也在locked_values记录 |
| relations | id/from/to/kind/meaning；端点为实体id，含义不能只写arrow |
| exact_labels, locked_values | 不得丢失的实际文字与数字/单位；自动presence检查不等于数值真实性 |
| count_constraints | 可数图必填。新图使用完整scope、expected_logical_ids及必要的expected_states/state_styles，见[语义约束](semantic-constraints.md)。旧item_ids仍兼容，但只能验证枚举对象存在，其额外对象与状态检查为REVIEW_REQUIRED。 |
| reference_palette, role_map | 色卡id；角色→swatch或base，衍生token由脚本写入manifest |
| layout, depth | archetype/reading_order；mode:D0或D1_shallow_2_5d，affects_quantitative_encoding必须false |
| edit_scope | 允许与保护字段、原图版本；不是执行权限提示 |
| output | width_mm、view_width、view_height（有限正数），font_profile；placement_width_mm记录实际入稿图宽，触发缩放后字号检查 |
| publication | target_journal可null，eligibility未核实保持unverified |
| data_source, data_sha256, data | 相对spec的CSV及SHA、重新计算的记录（可选） |
| items | 按后→前绘制的扁平图元序列，稳定id，独立绑定entity/role/relation |
| caption, alt_text | 说明范围、DEMO、口径、重复局部图、适当文字替代 |

## 图元

共同字段：`id,type,fill,stroke,stroke_width,opacity,entity,role,relation`；计数范围内另有 `logical_id/object_part`。颜色是`#RRGGBB`、`none`或`@role.token`；token为base/fill/stroke/highlight/shadow/marker/text。无字体继承的魔法默认。关系可提供 `geometry` 端点与三角箭头定义；没有可审核定义时不声称方向已自动核实。

- rect: x,y,w,h,radius可选。
- circle: x,y,r；ellipse: x,y,rx,ry。
- polygon/line: points:[[x,y],...]，line一般只stroke；dash:[6,4]可选。
- path: commands:[["M",x,y],["L",x,y],["C",x1,y1,x2,y2,x3,y3],["Z"]]。
- text: text,x,y(首行baseline),size(viewBox单位),align:left/center/right,leading,max_width,background(实际声明底色)。换行用真正JSON换行转义`\n`；wrap_text依据字体宽度算。

1.6 optionally accepts `fill_gradient` on filled geometry. Radial form: `{ "kind":"radial", "cx":100, "cy":100, "r":60, "stops":[[0,"@shell.highlight"],[0.6,"@shell.base"],[1,"@shell.shadow"]] }`. Linear form uses `x1,y1,x2,y2` in the same scene coordinates. Stop positions must increase strictly from 0 to 1. Colors retain semantic role tokens. SVG exports native user-space gradients; PDF exports native clipped shading, with encoded-sRGB/DeviceRGB interpolation. Both remain vector. The gradient geometry and stop positions participate in the geometry lock; only stop colors are excluded. Gradients on text or lines are rejected. The renderer does not simulate physical lighting.

视图x右/y下，源单位与物理点由output统一换算。图元不是任意SVG/CSS解析器。条件箭头/3D网格/TeX等需要手动建立明确图元或采用其他真实后端。未知算子报错。

最小脚本API：`Scene.entity/relation/add/text/line/arrow/sphere`在make_examples.py。数组对应、分层板、包覆颗粒及重复剖面另见[组件API](scene-components.md)。其可选`component_constraints`与`occlusion_constraints`只在出现时检查，旧规格仍可渲染。它们提供几何便利，不负责科学推理。需要其他对象可以直接构造JSON图元。

导出每个SVG顶层g的id与场景一一对应，绑定字段使用data属性，文本保留text/tspan；PDF字体按显式路径嵌入。manifest记录源规格、语义、几何、角色和导出SHA。recolor只改主题；对比时几何和语义均必须一致。不要删manifest里未验证的子项来获得更漂亮的状态。
