# 局部叙事对照

## 原段落

The demonstrator comprises a source, a shutter, a splitter, a sample and two detectors. It acquires dark and illuminated readings and implements subtraction, division and denominator validation. Four constructed cases check the output and invalid-state handling. The components and software form a complete dual-channel readout procedure.

## 候选 A：从读数问题进入（选用）

An illuminated transmission reading T1 carries both the detector's dark value and changes in source strength. The DEMO therefore pairs dark subtraction with a reference channel: a single shutter H, placed before splitter B, blocks light from source S to both detectors when closed. When H opens, B sends one branch directly to reference detector R and the other through sample P to transmission detector T (Figure 1). The same sample and detectors remain in place while the two shutter states provide (R0, T0) and (R1, T1). The procedure first checks that the reference difference R1 − R0 is positive; only then does it compute q = (T1 − T0)/(R1 − R0). Otherwise it returns INVALID without division. In four constructed cases, doubling both dark-subtracted inputs preserves q = 0.5, whereas zero and negative reference differences are rejected. These checks establish the stated arithmetic and invalid-state handling for those inputs. They do not establish absolute transmittance, cancellation of all drift, or real-instrument accuracy, speed or signal-to-noise performance.

## 候选 B：从检查结果进入（未选）

Four constructed inputs test two parts of this DEMO's readout: the valid pairs yield q = 0.5, while zero and negative reference differences yield INVALID. The readout uses one source S and a shutter H upstream of splitter B, which feeds reference detector R directly and transmission detector T through sample P. Closing H removes source light from both branches to obtain R0 and T0; opening it obtains R1 and T1 with P, R and T unchanged. This paired acquisition makes the dark values explicit and supplies a contemporaneous reference difference for normalization, rather than comparing T1 alone. Division is allowed only when R1 − R0 > 0, giving q = (T1 − T0)/(R1 − R0); other cases are rejected. The constructed checks cover these arithmetic cases, without establishing absolute transmittance or real accuracy, speed, noise performance, or cancellation of all drift.

选择 A：面对尚不了解装置的读者，先提出 T1 所混合的两类因素，再解释 H 的位置及参考支路，避免读者在尚不知 R/T 含义时先处理四个结果。B 的检查范围更早出现，但装置动机延后。A 比原段长，代价是增加篇幅；增加的内容来自任务书已有事实，没有新增实验或创新结论。
