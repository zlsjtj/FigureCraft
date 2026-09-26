# 可编辑对象组件

`scripts/scene_components.py` 可配合 `Scene` 或其 JSON 字典使用，输出原渲染器支持的独立图元。旧命令和场景保持兼容。已有 SVG 或 Matplotlib 图可继续使用原流程。

## 建立场景

将 `scripts/` 放到 Python 模块搜索路径后，调用组件：

```python
from pathlib import Path
from make_examples import Scene
from scene_components import (coated_particle, layered_slab, detail_link,
                              declare_count)

s = Scene('demo', '一个包覆颗粒及同一颗粒的局部剖面', height=600)
s.s['output'].update(width_mm=160, placement_width_mm=160)
s.s['reference_palette'] = 'yellow_blue_sage'
s.s['role_map'] = {'core': {'swatch': 'yellow'}, 'shell': {'swatch': 'blue'},
                   'base': {'swatch': 'sage'}}
s.entity('particles', 'shell', '给定包覆颗粒')
s.entity('substrate', 'base', '支撑层')
layered_slab(s, 'base', x=70, y=360, width=330, depth_x=100,
             depth_y=-90, thickness=30, entity='substrate', role='base')
coated_particle(s, 'p0', x=190, y=265, radius=42, core_radius=27,
                entity='particles', shell_role='shell', core_role='core', view='whole')
coated_particle(s, 'detail0', x=680, y=260, radius=84, core_radius=54,
                entity='particles', shell_role='shell', core_role='core',
                view='section', detail_of='p0')
detail_link(s, 'p0-detail', 'p0', 'detail0', [[225,245],[590,200],[625,205]])
declare_count(s, 'particles', 'particles', ['p0'])
declare_count(s, 'layers', 'substrate', ['base'])
s.s['caption'] = '教学示意。局部图重复 p0，尺寸无测量含义。'
s.finish(Path('scene.json'))
```

这段代码演示接口，不规定构图。科学内容、标签、图注、阅读路径和证据由具体任务提供。`Scene` 默认是 DEMO，真实结果要另给来源。900 个视图单位宽、160 mm 入稿时，约 18–20 单位对应 9–10 pt；仍按最终缩放检查。

## 组件选择

| 接口 | 适用对象 | 需要注意 |
|---|---|---|
| `array_grid(... labels, x, y, columns, entity, role, states=None)` | 寄存器、通道、索引表 | 行优先，矩形与文字分离，每格一个主对象；布尔状态绑定填充和预期状态 |
| `index_correspondence(... source_cell, target_cell, meaning=...)` | 两阵列同一索引对应 | 无向虚线，默认从下到上；科学含义由调用者给出，其他几何可自行连线 |
| `layered_slab(... x,y,width,depth_x,depth_y,thickness,entity,role)` | 多层支撑结构 | 前左锚点，深度 x 为正、y 为负；顶面是主表示，侧面绑定同一对象；下层先画 |
| `coated_particle(... radius,core_radius,entity,shell_role,core_role,view=...)` | 包覆、内核和切面 | `whole` 隐藏内核，`cutaway` 显示楔形开口，`section` 是平面截面 |
| `detail_of='original'` | 重复局部图 | 继承原 ID 和实体，保留半径比，所有局部面记为 detail；绑定原对象而非另一局部图 |
| `detail_link(...)` | 整体与局部对应 | 无方向箭头的虚线，不表示因果；检查身份与端点，但不自动吸附边界或绕开障碍 |
| `declare_count(scene,name,entity,logical_ids)` | 跨视图计数 | 范围包含该实体的全部图元，副本和装饰须正确绑定 |
| `declare_occlusion(scene,back_item,front_item)` | 遮挡顺序 | 检查支持的边界重叠与绘制先后，不证明真实三维可见性 |

只有声明 `component_constraints`、`occlusion_constraints` 才检查相应项目。共享层边、截面、半径、部件绑定和顺序均为有限检查。未知组件需审阅；错误图配错误约束仍可能一致，必须回查原始内容。

`array_grid` 的等宽单元格表达条目顺序或槽位，不自动表达条目之间的数值距离。若本轮要让读者直接看出间隔、平移或不变形状，应另用已给数据计算坐标，并注明尺度和各视图的原点；不要只把数字填入默认网格就视为完成信息设计。原生 line、rect、path 等足以支持这类布局，不需要先为每种论文新增组件。

颗粒后排先画，前排后画；检查每个对象能否辨认。二维包围盒重叠只是辅助，不证明可见性。用轮廓和标签使灰度仍可读，文字保持平面。隐藏内核应在对象模型中逐个绑定；复合颗粒计数不等于验证了全部隐藏子对象。

## 圆面与旧版切开接口

`rounded_coated_particle` 使用相同中心、半径、角色和绑定参数，旧 `coated_particle` 不变。

- `whole`：上左径向明暗，涂层不透明，内核隐藏。
- `section`：平面圆截面，不加球面高光。
- `hemisphere`：曲面半球与斜切平面；`section_aspect` 在 0.25–1 之间，同时缩放内外截面。
- `cutaway`：涂层开口、可见曲面内核和两条平切边，是固定方向的 2.5D 示意，不能表示任意相机、多开口或实体布尔切割。

可用 `detail_of='P6'` 重复同一对象。截面边、内核、渐变和接触阴影不是额外颗粒。先确定轮廓和切开语义，再选择明暗；平切面不能使用球面渐变。阴影位置和绘制顺序由调用者负责。

## 连贯斜剖面与涂层开口

1.7 的两个接口针对不同操作：

| 接口 | 显示几何 | 回答的问题 |
|---|---|---|
| `sliced_coated_particle(...)` | 涂层与内核共同被一个斜平面切开 | 内部结构及涂层相对厚度 |
| `opened_coating_particle(...)` | 只移除涂层，平环形边缘前方保留完整曲面内核 | 局部打开涂层后看到什么 |

共同参数为 `x, y, radius, core_radius, entity, shell_role, core_role`，可选 `detail_of`，以及：

- `cut_offset`：切平面距球心的距离与外半径之比；`0 <= cut_offset < core_radius/radius`。0 为中心切面，正值移除更小球冠，没有测量支持时仅为示意。
- `normal_angle_deg`：与视轴的夹角 20–70 度，控制投影斜度，不表示材料性质。
- `face_direction`：`right` 或 `left`，镜像投影，保留上左示意光源。

```python
from scene_components import sliced_coated_particle, opened_coating_particle
sliced_coated_particle(s, 'section', x=580, y=210, radius=100,
    core_radius=65, entity='particles', shell_role='shell', core_role='core',
    detail_of='P6', cut_offset=0, normal_angle_deg=48)
# 另一场景 s2 中也须先建立原对象 P6，再画不同的局部图。
opened_coating_particle(s2, 'opening', x=580, y=210, radius=120,
    core_radius=78, entity='particles', shell_role='shell', core_role='core',
    detail_of='P6', cut_offset=.15, normal_angle_deg=65)
```

原对象必须已存在于同一场景；各面绑定其逻辑 ID，原始内外半径比保持不变。偏心切面在投影前的内外半径分别为 `sqrt(r²-d²)` 和 `sqrt(R²-d²)`，不能直接沿用原比值。开口内核用互补球冠投影，因此曲面从轮廓和明暗都能辨认。两种操作的涂层切边均为平面。

这是有限解析投影，不是任意 3D 网格、光照仿真或真实断裂证据。图注必须写清操作，不能因为内核颜色相同就把剖切称为完整内核。

构图先决定原对象与局部图的位置，再用短且可追踪的无向引线连接。只显示对应需要的 ID，完整对象集合留在元数据中。接触阴影贴合支撑面并绑定颗粒。连线可跨空白支撑面，不必绕整页；改几何后重查端点。

[两种构图的源脚本](../examples/material-polished-v17/build_material_v17.py)可独立生成示例。平面内核曾被错误用于“仅开涂层”的任务，因此现在分别提供剖切和开口接口；回归范围见[验收](../provenance/acceptance-v1.7.md)。

## 共享分支与数值模式

`scripts/relation_components.py` 只复用两种容易反复写错的几何，不包含领域数据、整页布局或自动美感评分。返回 `items` 是原场景格式的独立线、矩形和文字，可 `add_component(scene, result)` 接入 `Scene`/JSON，也可在原生绘图流程中逐项导出。旧接口不变。

```python
from relation_components import sampled_pattern, branch_bus, add_component
# 教学数据：同一非均匀采样模式在另一原点应用；不是实验测量。
shape = sampled_pattern('mask', [0, 3, 11, 14], x=50, y=100,
    units=8, entity='mask', role='shared')
result = sampled_pattern('use-a', [0, 3, 11, 14], x=330, y=70,
    units=8, base=200, labels=[2], entity='use-a', role='applied',
    source_pattern='mask')
links = branch_bus('read-mask', source=[185,100], targets=[[315,70],[315,160]],
    junction_x=240, source_entity='mask', target_entities=['use-a','use-b'],
    meaning='Both applications refer to the same mask', arrowheads=False)
# 在自己的场景声明实体、画 use-b、设置字号/最终尺寸后再添加。
for component in (links, shape, result):
    add_component(scene, component)
```

`sampled_pattern` 画数值轴上的采样位置，不画存储这些数值的容器；表项本身用 `array_grid` 或原生等距条目表示。它的 `x` 是局部零点，横位置为 `x + value * units`；`base` 只改变标签数值，不改变间隔。严格递增有限数值和正尺度是前提。`labels=None` 显示全部，`[]` 无数值，索引列表只显示选中项。`source_pattern` 保存来源关系，不推断物理复制、所有权或收益。原点/单位/省略、应用条件及必要校验值由图与图注说明。组件不自动添加断轴，不能将两个视窗接成假连续尺度。

`branch_bus` 要求显式锚点、实体和关系含义；`arrowheads=False` 返回无向关联，适合没有运动或传输含义的共同引用。默认 `True` 保留旧调用的箭头外观，调用者需根据科学含义选择；调用者检查线路是否绕字、终点是否属于正确对象。它不假定分支是时间顺序、真实通道或两份源对象。新几何的边界测试见 `tests/test_relation_components.py`；完整场景的科学与视觉审阅仍另做。
