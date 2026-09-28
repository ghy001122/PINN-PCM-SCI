# 固定三次样条对照与焦耳能量时间分配：完成报告

**任务：** PCM-20260928-CUBIC-ENERGY-DISCRIMINATION-01。**状态：** 批准范围已完成；后续研究未启动。

## 1. 核心判断

**VERIFIED：**同样的197个电压观测改用固定not-a-knot三次样条，所得器件电流变化依工况而异。静息9 V的小误差进一步下降；抑制/A和B改善；12.5 V、15.8 V及激发/A和B恶化。这些角色各自的改善/恶化方向在两个保存步长一致，但不构成连续解收敛或总体成功率。负载电流的方向亦相同。没有按工况择优拼出第三种方法。

**VERIFIED：**CS在两种源步长的所有角色上都有保存时刻的负器件电流；动态角色也有负预测瞬时耗散。波形未裁剪。除静息外，全程能量绝对误差增大；196个区间的绝对误差总和却并非同步恶化。器件电流RMS、峰形、总能量与能量时间分配不能相互替代。

**SUPPORTED_INTERPRETATION：**这一个普通插值规则没有统一解决当前重构差距，且产生被动性方面的代价。它提高了后续比较的具体要求，但不代表所有传统平滑或状态估计失败，不证明二维热模型或PINN必要。总能量误差小，也不能认证温度、相态或迟滞历史。

**UNKNOWN：**绝对用途充分性、连续体精度、低阈值实验方法增量及内部热场质量。没有填入用途容差，没有执行新的PINN或条件热响应。

## 2. 固定输入和证据身份

基线为`9414c1da37cb9a101bf3ed812d248f63d4454470`，前轮科研成果为`fa475c257651c17fcfe83007ab0fe238c6c5995c`。五个作者模型工况、原1/0.5 ns保存轨迹共十个系统文件、十四个角色/步长比较；它们是已有开发记录上的追加对照，不是独立确认或真实材料实验。

CS只接收旧NPZ中的`observation_time`、`observation_voltage`、原生查询时间和已知Vin/C/RL。观测不重取，C=1.4534619293e−10 F、RL=12000 Ω，最后观测间隔32 ns。十套CS全部锁定后才打开源电流，原PCHIP预测不重新拟合。见[预测锁定](comparison/predictions-locked.json)、[固定配置](../../configs/cubic_energy_comparison_20260928.json)和[评分输入映射](scoring-subset/config.json)。无第三方法、第三步长、参数或采样扫描；实验CSV数值均未打开，4.1/3.9 V封存。

## 3. 全部配对电流结果

完整0–20 μs含两端，原生轴归一化梯形权重。Δ=E_PCHIP−E_CS，正数表示CS的该项RMS较小。固定1 mA归一值、最大差、有符号均值、两辅助窗口与双器件等权MSE联合值都保存在结果中；下表优先给绝对量。静息的极小误差变化不包装成重大实用收益。

| 工况 / 器件 | 源步长 ns | 器件 PCHIP→CS，μA | 器件改善 Δ，μA | 负载 PCHIP→CS，μA |
|---|---|---|---|---|
| single_9V/A | 1.0 | 0.066701 → 0.050560 | +0.016141 | 0.000505 → 0.000027 |
| single_9V/A | 0.5 | 0.050452 → 0.025310 | +0.025142 | 0.000503 → 0.000026 |
| single_12p5V/A | 1.0 | 211.037086 → 218.126093 | -7.089007 | 3.107787 → 3.419409 |
| single_12p5V/A | 0.5 | 211.451256 → 217.760319 | -6.309063 | 3.118527 → 3.413076 |
| single_15p8V/A | 1.0 | 64.160758 → 106.693050 | -42.532292 | 0.618307 → 1.411557 |
| single_15p8V/A | 0.5 | 63.276923 → 106.277066 | -43.000142 | 0.569717 → 1.380027 |
| pair_excitation/A | 1.0 | 114.772975 → 157.339365 | -42.566390 | 1.752637 → 2.502825 |
| pair_excitation/B | 1.0 | 118.039826 → 127.213618 | -9.173792 | 1.834730 → 2.094118 |
| pair_excitation/A | 0.5 | 103.868333 → 152.503708 | -48.635375 | 1.514965 → 2.352137 |
| pair_excitation/B | 0.5 | 117.384514 → 127.048810 | -9.664296 | 1.815436 → 2.077661 |
| pair_inhibition/A | 1.0 | 166.451788 → 145.147223 | +21.304565 | 2.510938 → 2.357851 |
| pair_inhibition/B | 1.0 | 134.442778 → 98.842971 | +35.599807 | 2.071348 → 1.688708 |
| pair_inhibition/A | 0.5 | 167.261256 → 145.458593 | +21.802663 | 2.526365 → 2.362933 |
| pair_inhibition/B | 0.5 | 137.117075 → 100.317605 | +36.799469 | 2.121570 → 1.721367 |

[完整精度配对表](scoring-subset/results/paired-comparison.csv) · [完整波形指标](scoring-subset/results/waveform-metrics.csv) · [全部结构化结果](scoring-subset/results/results.json)。没有新胜出门，也不把10 μA/2 μA当作本包资格线。

## 4. 峰形与异常不能被RMS或峰数掩盖

以下为0.5 ns来源的全段摘要；两步长全部峰列表、匹配差与未配对峰在JSON中。原检测器及0.25 μs匹配约定不变，无峰时序为N/A。所有有峰角色两方法保留原峰数和配对数量，但CS的峰高误差与峰时RMS在此细步来源的各动态角色均增大：抑制两器件RMS改善，并不意味着峰形同向改善。

| 角色 | 方法 | 原/预测峰数 | 配对峰时RMS ns | 最大峰高绝对差 mA |
|---|---|---|---|---|
| single_9V/A | PCHIP | 0/0 | N/A | N/A |
| single_9V/A | CS | 0/0 | N/A | N/A |
| single_12p5V/A | PCHIP | 7/7 | 50.142 | 1.137221 |
| single_12p5V/A | CS | 7/7 | 50.664 | 1.415476 |
| single_15p8V/A | PCHIP | 3/3 | 19.837 | 0.641184 |
| single_15p8V/A | CS | 3/3 | 26.206 | 1.225109 |
| pair_excitation/A | PCHIP | 5/5 | 15.490 | 0.824132 |
| pair_excitation/A | CS | 5/5 | 29.979 | 1.179725 |
| pair_excitation/B | PCHIP | 5/5 | 39.525 | 0.691980 |
| pair_excitation/B | CS | 5/5 | 40.307 | 0.979695 |
| pair_inhibition/A | PCHIP | 7/7 | 44.049 | 0.448458 |
| pair_inhibition/A | CS | 7/7 | 47.109 | 0.640007 |
| pair_inhibition/B | PCHIP | 2/2 | 48.503 | 0.339734 |
| pair_inhibition/B | CS | 2/2 | 52.510 | 0.419315 |

以下异常只在保存查询时刻检查；没有声称连续全区间无过冲或无负值。9 V的负值很小，仍如实列出，不解释成真实器件反向导通。

| 角色 | 源步长 ns | 最小器件电流 μA | 最小功率 mW | 负电流样本数 | 电压最小/最大 V |
|---|---|---|---|---|---|
| single_9V/A | 1 | -0.211545 | -0.000001 | 3 | 0.000000 / 6.776434 |
| single_9V/A | 0.5 | -0.080329 | -0.000000 | 2 | 0.000000 / 6.776434 |
| single_12p5V/A | 1 | -150.207763 | -1.204013 | 63 | 0.000000 / 8.113801 |
| single_12p5V/A | 0.5 | -156.490680 | -1.254426 | 127 | 0.000000 / 8.115318 |
| single_15p8V/A | 1 | -325.226501 | -2.819248 | 62 | 0.000000 / 8.864541 |
| single_15p8V/A | 0.5 | -331.714071 | -2.874734 | 123 | 0.000000 / 8.865548 |
| pair_excitation/A | 1 | -89.545113 | -0.664252 | 39 | 0.000000 / 7.484471 |
| pair_excitation/B | 1 | -82.982766 | -0.549548 | 41 | 0.000000 / 6.673654 |
| pair_excitation/A | 0.5 | -94.426888 | -0.700628 | 75 | 0.000000 / 7.485793 |
| pair_excitation/B | 0.5 | -87.554907 | -0.579794 | 78 | 0.000000 / 6.674326 |
| pair_inhibition/A | 1 | -69.914294 | -0.482997 | 32 | 0.000000 / 6.974875 |
| pair_inhibition/B | 1 | -222.128135 | -1.829835 | 50 | 0.000000 / 8.364309 |
| pair_inhibition/A | 0.5 | -56.498581 | -0.390191 | 55 | 0.000000 / 6.968780 |
| pair_inhibition/B | 0.5 | -211.210805 | -1.739009 | 94 | 0.000000 / 8.358741 |

预先具名的12.5 V/A展示见[完整波形](figures/circuit-waveform-single_12p5V-A.png)及[首峰局部图](figures/circuit-waveform-single_12p5V-A-first-peak.png)。局部窗口固定为粗源第一参考峰2.612 μs附近±0.25 μs，两步长使用同一物理时间窗口；只有电压面板画观测点，窗口不改变全程评分。

## 5. 焦耳能量：总量、时间分配和相消

预测使用同一连续分段三次电压p：W=∫(Vin·p−p²)/RL dt−C[p(b)²−p(a)²]/2，逐真实多项式片段解析积分六次项p²。参考使用保存同层功率V·I_D的分段线性精确积分；非原生节点边界先在**功率**上分割。两者差同时含重构误差和原保存离散因素，不作为连续热力学误差认证。

下面的0.5 ns源结果用nJ显示。Σ|ΔW_j|衡量196个固定区间上的绝对能量差累计；它不是瞬时功率L1误差。总误差可能由正负区间相消。最后32 ns区间保留。两步长、全/前半/后半三窗口及197边界累计量完整输出。

| 角色 | 方法 | 参考总W nJ | 总ΔW nJ | 区间绝对误差之和 nJ | 最大区间绝对误差 nJ |
|---|---|---|---|---|---|
| single_9V/A | PCHIP | 22.437271 | -0.000672 | 0.000672 | 0.000025 |
| single_9V/A | CS | 22.437271 | -0.000668 | 0.000668 | 0.000025 |
| single_12p5V/A | PCHIP | 51.602131 | -0.010824 | 0.080346 | 0.006142 |
| single_12p5V/A | CS | 51.602131 | -0.025929 | 0.079453 | 0.006457 |
| single_15p8V/A | PCHIP | 57.388225 | -0.005162 | 0.024695 | 0.008463 |
| single_15p8V/A | CS | 57.388225 | -0.008830 | 0.020650 | 0.008117 |
| pair_excitation/A | PCHIP | 38.280421 | -0.009868 | 0.043620 | 0.003924 |
| pair_excitation/A | CS | 38.280421 | -0.018059 | 0.045191 | 0.003704 |
| pair_excitation/B | PCHIP | 28.831699 | -0.005723 | 0.036638 | 0.002856 |
| pair_excitation/B | CS | 28.831699 | -0.012539 | 0.036723 | 0.003424 |
| pair_inhibition/A | PCHIP | 40.566736 | -0.009423 | 0.060252 | 0.004414 |
| pair_inhibition/A | CS | 40.566736 | -0.020337 | 0.058172 | 0.005466 |
| pair_inhibition/B | PCHIP | 49.702995 | -0.003035 | 0.026905 | 0.006259 |
| pair_inhibition/B | CS | 49.702995 | -0.008635 | 0.027877 | 0.007347 |

例如12.5 V细步，器件电流RMS从211.451变为217.760 μA；总能量误差从−0.010824变为−0.025929 nJ，但Σ|区间ΔW|从0.080346小幅变为0.079453 nJ。15.8 V细步器件RMS恶化明显，Σ|区间ΔW|却从0.024695降至0.020650 nJ。抑制/A细步器件RMS下降21.803 μA，Σ|区间ΔW|小降，但总误差绝对值增大。以上是目标量不同的实际表现，不进行替代成功判定。

[三个窗口能量](scoring-subset/results/energy-windows.csv) · [全部196区间](scoring-subset/results/energy-intervals.csv) · [累计能量误差](scoring-subset/results/energy-cumulative.csv) · [电荷](scoring-subset/results/charge-metrics.csv)。电荷、焦耳耗散、电容储能、源能量和负载耗散保持不同身份；本轮没有把电容储能再加为热源。

## 6. 数值资格与可分辨范围

继承成功源码的KCL、κ、A+B+X+K、原电荷、权重和峰函数保持不变；CS与PCHIP均通过对应工程检查。分解继续在非终点子网格重新归一，主RMS继续含终点。B为导数平方项，X/K带符号；完整[分解表](scoring-subset/results/error-decomposition.csv)保留。此分解描述现有误差组成，不证明热先验可消除它。

新增Euler能量左和核对保留 +CΣ(Δv)²/2 离散项和 −Σh·v·κ。它不要求梯形参考满足左和恒等式，不把离散项当真实额外热源。全部三窗口通过；最大闭合缺陷为6.61744e-24 J，最大缺陷/固定工程容差为1.25032e-05。[Euler记账](scoring-subset/results/euler-energy.csv)。

下面三列均在共同1 ns轴上使用梯形权重，列出CS器件支路，单位μA。误差曲线差、重构曲线差与源波形差分别保存；PCHIP和负载支路完整值见[敏感性表](scoring-subset/results/step-sensitivity.csv)。

| 角色 | 原电流粗细差RMS | 各自重构误差曲线差RMS | 重构电流曲线差RMS |
|---|---|---|---|
| single_9V/A | 0.005610 | 0.025272 | 0.022566 |
| single_12p5V/A | 39.721550 | 35.520195 | 19.875301 |
| single_15p8V/A | 7.986713 | 6.260075 | 5.434113 |
| pair_excitation/A | 34.753045 | 28.736082 | 20.083934 |
| pair_excitation/B | 12.592380 | 10.231796 | 9.049294 |
| pair_inhibition/A | 22.383301 | 17.733807 | 13.298958 |
| pair_inhibition/B | 9.997153 | 8.590628 | 6.948209 |

当前配对差能在指定保存记录与FP64口径下复算；两步长方向一致只能支持这个有限离散范围的方向稳定。12.5 V源电流粗细差约39.72 μA，不能由重构误差变化较小宣称已达2 μA连续精度。所有步长差均不是统计置信区间或连续误差上界。

旧PCHIP波形标量与历史分数在预先固定的64ε运算尺度内一致，最大标准化差0.0212096；峰结果精确一致。跨平台点积最后几位差异没有修改旧科学阈值或布尔裁决。新包第一次评分与独立目录评分的完整结果JSON逐值精确一致。

## 7. 独立复算、成稿和数据处理

最小子集含十条原始time/V/三支电流、原有限观测、两种锁定预测及多项式、来源/单位和实际评分入口。原波形直接裁自保存来源，非预测反造。共享time/观测/参考数组每系统只存一次。包内没有T/R/H、低阈值实验CSV或求解器；不调用旧24.6 GB全包。

[独立运行记录](build/independent-reproduction.json)确认在工作区外目录运行一次，研究仓库文件读取被审计钩子拒绝，既有Python虚拟环境作为依赖例外保留；指定输入暂缺时立即报错，不回退旧绝对路径。38个输入/代码文件合计39.88 MiB。见[可移交子集入口](scoring-subset/README.md)。这验证本包保存数组重评分能力，不等于神经AD重算或旧稿全场P03闭合。

实际CPU成本：CS十系统预测1.066 s；首次完整评分7.107 s；独立复制、受隔离评分及缺输入检查共10.674 s。仅十次CS拟合，旧PCHIP拟合零次；两次评分分别为正式分析与要求的独立复算。GPU未启动，无关机动作或远端计算。本地新交付待下次获准实例会话同步，不为同步启动GPU。

本轮[主稿](manuscript.pdf)只更新发布身份和真实访问状态；完整补充沿用[既有58页版本](../paper_revision_20260927_circuit_screen/supplement.pdf)。[修改说明](revision-notes.md)、[构建依赖](build-dependencies.json)和[访问方案](data-access-plan.md)记录实际能力。没有Git提交/推送、DOI、数据公开、投稿或作者联系。

## 8. 唯一优先下一动作

**SUPPORTED_INTERPRETATION／PROPOSED_NOT_AUTHORIZED：**使用本轮[测量澄清草稿](measurement-request-draft.md)，取得五条低阈值开发记录的可核验接线、通道/驱动与C/RL说明。当前尚不能把理想电路算子安全映射到这些实验，因此这项输入闭合最直接改变可执行任务，而不是继续枚举插值器或立即启动PINN。草稿尚未发送；来源缺项见[逐项状态](measurement-source-status.md)。仅C缺失时的积分校准属于另行批准的后续任务。

后续若提出热/迟滞状态估计，应让传统方法与PINN共享合法物理与观测。已知线性热模型中的无显式电压求导变量变换，仅为条件模型的代数设计线索；本轮没有运行它，不能用来声称内部场准确。动态RC训练期接口相对共同事后重放的增量仍是待检验假设，4000/800预算未启动。

## 9. 来源与完整图件

方法接口：[SciPy 1.14.1 CubicSpline官方文档](https://docs.scipy.org/doc/scipy-1.14.1/reference/generated/scipy.interpolate.CubicSpline.html)。参数与保存规则沿用[原冻结合同](../paper_revision_20260927_circuit_screen/evidence/core-revision/vo2/frozen-config.json)，作者代码固定于217d4f0ed6bfc680240021b07142a121cb4963d1；原文[Qiu et al., DOI 10.1002/adma.202306818](https://doi.org/10.1002/adma.202306818)。标准样条、能量恒等式与误差整理不作为原创原理。

新评估来源为[Review_and_Next_Plan](review-and-next-plan.md)与[补充研究方案](research-improvement-plan.md)，执行以[本轮明确指令](instructions.md)为准；旧PLAN_Review_Amendments属于上一轮PCHIP任务，不覆盖本轮明确新增一个CS的授权。

- single_9V/A：[完整波形](figures/circuit-waveform-single_9V-A.png) · [能量分配](figures/circuit-energy-single_9V-A.png)

- single_12p5V/A：[完整波形](figures/circuit-waveform-single_12p5V-A.png) · [能量分配](figures/circuit-energy-single_12p5V-A.png)

- single_15p8V/A：[完整波形](figures/circuit-waveform-single_15p8V-A.png) · [能量分配](figures/circuit-energy-single_15p8V-A.png)

- pair_excitation/A：[完整波形](figures/circuit-waveform-pair_excitation-A.png) · [能量分配](figures/circuit-energy-pair_excitation-A.png)

- pair_excitation/B：[完整波形](figures/circuit-waveform-pair_excitation-B.png) · [能量分配](figures/circuit-energy-pair_excitation-B.png)

- pair_inhibition/A：[完整波形](figures/circuit-waveform-pair_inhibition-A.png) · [能量分配](figures/circuit-energy-pair_inhibition-A.png)

- pair_inhibition/B：[完整波形](figures/circuit-waveform-pair_inhibition-B.png) · [能量分配](figures/circuit-energy-pair_inhibition-B.png)
