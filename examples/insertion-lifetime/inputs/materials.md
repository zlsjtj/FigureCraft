# 演示材料包：可取出的成像载片

本文件、数据、草稿均为本次原创 DEMO，用于测试科研表达与绘图能力，未进行实体实验，不可引用为真实研究结果。

## 未整理的原稿

The cartridge imaging system uses a camera, a removable carrier and a software program. The carrier has an identification code. There are three fiducial marks and eight circular specimen wells. The program calculates a coordinate transform. Different implementation variants were tested and the time and coordinate errors are listed in the table. One variant was faster than another. All target positions were converted to millimetres. This system provides an integrated solution for cartridge imaging. The transform is calculated from the three fiducials. We also implemented a generation counter. The counter is checked each frame. For a locked carrier the coordinate errors were similar. For reinserted carriers an old transform was inaccurate. Computing a transform each time was slower but remained accurate. At one frame per insertion the retained-transform program was a little slower. Identifiers alone were not sufficient. A missing fiducial caused the frame to be rejected. The system has several components and can be applied to cartridge measurements.

## 实现摘记

- 图像坐标为 u,v（像素），载片坐标为 x,y（mm）。二维仿射映射、三点拟合和二维码识别均为已有方法，演示没有提出新求解器或新编码。
- 每张载片40×30 mm。三枚圆形定位标记中心在载片坐标 (0,0)、(30,0)、(0,20)。内部8个圆形样品孔中心 x∈{6,12,18,24}，y∈{6,12}，孔半径1.8 mm。定位标记半径0.8 mm。载片轮廓在x∈[-5,35]，y∈[-5,25]。三个标记与孔不是同类对象。
- 机械锁闭触点只给出开/闭事件，不给出精确位姿。开锁立即使已保存映射不可用；重新闭锁递增 insertion generation。二维码只识别同一载片，不能识别该载片重新插入后的姿态。
- 程序V2每帧重新找齐三个标记并拟合仿射映射。该映射用于同一帧所有孔位。
- 程序V3第一次见到“载片ID + 当前generation”时找齐三个标记、拟合并保存映射。锁持续闭合时后续帧复用同一映射。ID或generation任一变化就重新拟合，不同时维护多套有效映射。
- 程序V1载片第一次识别后保存映射，此后仅检查ID。再次取出并插回同一载片不重新拟合。
- V3 首次拟合缺一个标记时，拒绝给出坐标而非沿用旧generation的矩阵；后续帧若读不到ID或锁状态未知也拒绝输出。传感器漏掉开锁事件的情况没有模拟，不能声称已排除所有陈旧映射。
- 锁定期间不验证载片是否微滑。假定锁住期间位置稳定；载片弯曲、镜头畸变、亚像素拟合和三标记共线未纳入此演示。矩阵求解没有因复用而变化。
- 输出坐标由同一组已知孔中心作误差参照。下表记录整段处理时间（图像读取、标记定位、拟合、ID和generation检查、坐标输出），不含相机曝光等待。检测与后处理实现固定，未把节省的拟合次数直接当作速度收益。
- 示例一次插入的三个图像点 (40,20),(640,20),(40,420) 分别对应上述三个载片标记。因此 x=0.05u−2，y=0.05v−1；图像点(280,140)对应载片点(12,6)。另一插入的矩阵需重算，没有提供其数值。

## 运行记录

完整数值见 results.csv。每组只进行一次确定性的演示回放，没有重复试验方差或置信区间。误差为每组各帧8孔中心的二维欧氏误差中位数（mm）。每帧输出8个点，不是8次独立拟合。时间是每组总时间，组长度不相同；不能直接跨组比较总时间以断言场景速度。

长序列的两组都80帧：A为一次插入后保持锁闭；B为同一载片反复插入8次，每次10帧。C为8次插入，每次1帧。D为B相同事件序列，但V3实验性关闭generation检查（ID仍检查），这是一个失效控制，不是另一个最终算法。E在新插入首次帧遮挡1枚定位标记，8次插入均发生；每组8帧。只记录是否输出和错误，拒绝率不是识别成功率。

## 解释资料与来源边界

本包中三点仿射变换是预先规定的基础工具。表格是为表达验证手工设定的演示数据，不能外推设备性能或声称工程首创。文稿可说明设计的差异、必要条件和演示所揭示的取舍，但不增加外部文献或真实用户采用。无需评价真实科研新颖性。
