# 匿名首次阅读评估

本报告是独立模型辅助评估，不是真人阅读测试或作者认可。只读取了 `blind/` 内的问题、原始材料、两稿全部实际 PDF 页面 PNG 与 Markdown，以及两图的参考尺寸 PNG、完整 PNG 和图注。先分别形成理解，再比较；论文与图的 A/B 独立对待，不推断条件。160 × 100 mm 的 96 dpi 文件只作为参考显示，不能保证屏幕物理尺寸。匿名材料无法说明开发历史，本评阅不称为留出验证。

## 各版本先读所得

**论文 A。** 我理解的改变是：保留原有 20 s 事件时间窗口与 count/sum，改为 5 s 首发暂定记录，在窗口关闭后固定 120 s 内接受迟到包并替换整条记录。引言的 “Our change separates first emission from subsequent replacement” 直接给出主张。采用理由是提前获得可修订结果；代价是保留状态和额外发送，且首发仍可能不完整。输入 sample ID 去重、输出重复投递、输出乱序、count/sum 混版分别有交代。第 2 节的 “Complete replacement prevents a duplicated correction from being added twice; the revision check prevents an older delivery from undoing a newer result.” 使各机制的职责容易复述。

证据也能读对：bursty 中 R5 是 31→48，F120 首发即 48，I5 留在 31；U5 仍替换完整记录，仅撤去接收端版本顺序检查，因此 10 个窗口被旧记录覆盖，最终 38。它支持给定投递下的版本顺序检查，不支持整体稳健性。beyond_retention 的 12 个初始不完整窗口只修好 8 个，其余所需包在 180 s 才到；R5 与 F120 均止于 44。这是固定截止规则的边界，不是普遍失败率或阈值最优性证明。

**论文 B。** 我读到相同的机制与证据边界。引言将新需求接到接收端：“This change creates a receiver-side obligation: a corrected aggregate must survive repeated and out-of-order deliveries without reverting to an older result or mixing two versions.” 接着介绍完整替换和版本顺序，动机到机制的衔接自然。输入重复与聚合记录重复由 “A duplicate input packet is ignored, independently of any duplicate aggregate delivery to the receiver.” 明确区分。第 2 节保留了固定失效、拒收而不转入下一窗口、事务成对替换和未测故障场景。

结果段首句 “The bursty comparison separates early output from eventual agreement.” 提供了阅读表格的角度，末尾又点明 on_time 没有一致性收益。48 个窗口不是重复试验，5 s/120 s 是配置等待，不是执行速度；状态数不等于进程内存，修订数不含网络重复发送。没有把教学记录写成真实 benchmark，也没有把现成组件写成发明。

**图 A。** 左侧蓝色 A 的上半缺口、赭色 B 的下半缺口都有直接引线；“Lower B” 把两者保持在装配对应位置。右上是装配后的同一对构件，虚线和 c 引线把交叉部位关联到右下剖面。剖面明确 A 在 0–8、B 在 8–16，接触线为 8；“Flush top and base” 与完整装配视图共同说明齐平。下方 “Each notch crosses the full width” 和 “Two members, three views” 排除了盲孔和新增构件的读法。

独看左侧形状时，A 的前侧台阶清楚，B 下缺口的可见部分较短，并遮住 A 的部分后侧边界；“Lower notch” 引线有帮助，但仅凭轮廓看清两处通宽需要多看一眼。图注补充尺寸、理想零间隙和不同显示比例，主要是在解释，不是在否认图里画出的实体重叠。

**图 B。** 左侧将赭色 B 与青色 A 完全拉开，两个开放缺口的侧面轮廓更容易分别辨认：B 去掉中央下半，A 去掉中央上半。颜色图例建立身份；向上的 “Lift B” 配合 “Separated for explanation” 能读作分解动作。右上装配图与右下 “Same joint: centre section” 表明仍是两个构件。剖面的 “Flush top · z = 16”“Contact · z = 8”“Flush base · z = 0” 直接交代顶面、接触和底面。

这幅图没有从装配图指向剖面的切线，读者需凭 “Crossing only · y = 0” 自行对应中心位置。图注明确通宽、A/B 的坐标方向和 8 mm 去除量，属于解释与消歧；未观察到需要靠“without volume overlap”去纠正的相反几何。两图均未出现销钉、胶层、载荷或材料性能暗示。

## 比较：实际阅读效果与取舍

- **贡献与继承：两稿实质相当，B 的引导略顺。** 都能回答“改了什么、为何用、付出什么”，都明确已有窗口/聚合与本次发射策略的关系。B 先提出接收端义务再给方案，首次读者较容易跟上；A 将不主张的新颖性逐项列出，并在结论重提 retained sample IDs，职责和范围更显式。B 不再列 watermarks，但没有转而主张发明水位线；来源段也保留无外部新颖性主张，不能判作科学退步。
- **证据与代价：B 的结果解释更集中，A 的机制分工更醒目。** B 的 “Thus early repair adds retained state and record transmissions, gives no agreement benefit in on_time, and cannot repair arrivals after eviction.” 把收益为空的情形与代价接在一起，比 A 让读者从数值自行合成这一判断更有用。A 上述完整替换/版本检查并列句更适合帮助新读者区分两项保护。两稿都保留加法修订的开发失败及“没有测量结果”，也都没有把 U5 当成所有机制的消融证明。未发现重要负结果被删去。
- **页面完成度：B 的收束更连贯，双方表格层级都普通。** A 的结论在第 2 页底部开始，跨到第 3 页才完成，读者被迫翻页收束论点，尾页大部空白；B 的结果、结论与来源在第 2 页顺次完成。不过 B 第 1 页末的 “The prototype has one writer per” 到下一页孤立的 “stream.” 才结束，也有断句干扰。判断依据是阅读中断的位置，不是页数少即更好。两表数值可读且与原始表一致，但 profile 组间没有明显视觉分隔，查组别还需逐行辨认。
- **图的操作各有得失，不能给出全面胜者。** B 更便于“先辨认两个零件各去掉哪一半”，分离轮廓和净空较清楚；A 更便于“把零件放回原位，并找到剖面所取的位置”，因为对位关系、直接对象标签及 c 切线都在图中。A 左图较拥挤，B 则要求在上方图例与构件之间往返，并自行把剖面对应到装配中心。
- **参考尺寸下的视觉完成度：两图均可读，但并非同一优势。** A 的分图标题与缺口标签较有层级，蓝/赭对照稳定；主图大，却让 B 的下缺口被遮挡得更明显。B 的轮廓、色面和空白较安定，双缺口更醒目；顶部尺寸图例和右下高度说明在参考显示中较细，底面说明也靠近下边缘。高分辨率放大后两者都清楚，不能用放大效果抵消小幅面取舍。两份图注都承担必要解释，未见靠图注“纠错”才成立的几何。

## 科学阻断项与无法判定处

对照给定教学材料，未发现需阻断的数值、机制或几何矛盾：完整记录替换、固定截止、两类重复、初始/最终一致性、中央接触及齐平关系均成立。原始材料本身不支持外部创新、真实性能、生产稳健性或接头强度；两类产物均保留这些界限。

单凭当前图无法完整验证隐藏面几何，但可见轮廓、剖面和图注相互一致，没有观察到实体穿插或盲孔证据。以上结论不证明首次人类读者一定理解，也不证明某项技能整体有效。论文 B 的因果组织有所受益、图 B 的独立缺口更易读，与 A 在机制显式程度和装配对应关系上的优势应分别保留。
