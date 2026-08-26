# R1 电—热—Allen–Cahn、KC′ 与 IRAC 定向来源及碰撞审查

- `review_id`: `R1_P1_SOURCE_COLLISION_2026-08-22`
- `decision_identity`: `R1_FULL_DESIGN_GRILL_2026-08-22`
- `scope`: `PACKAGE_A_P1_ONLY`
- `review_date`: `2026-08-22`
- `review_outcome`: `P1_PASS_WITH_SCOPE_REDUCTION`
- `claim_status`: `SUPPORTED_INTERPRETATION_FOR_PHYSICAL_CLASS; HYPOTHESIS_FOR_METHOD_INCREMENT; NO_NUMERICAL_EVIDENCE`

## 结论

`SUPPORTED_INTERPRETATION`：二维电导—Joule 热—相场耦合、局域相变、接触/几何敏感性和材料空间非均匀性均有可追溯的一手依据，足以支撑一个透明的 `derived/synthetic` R1 benchmark 类别。它们不能为任何具名氧化物提供 R1 的定量参数 oracle。

`SUPPORTED_INTERPRETATION`：generic 时间处理、坐标变换 PINN、causal training、RAR/RAD/RAR-D/R3，以及针对陡峭界面或 Allen–Cahn 的自适应采样均已有直接先例。IRAC 的“界面信号＋PDE 残差信号驱动配点”核心高度碰撞，只能作为待检验的支撑性适配，不能写成独立首创。

`HYPOTHESIS`：本次有界检索未发现与“只对相态场 `eta` 使用空间局部、严格单调的时间坐标，同时对强形式执行完整链式回拉，而 `phi` 与 `T` 保持物理时间”完全同构的直接先例。KC′因此仅保留这一窄机制差异；是否产生可发表增量必须由 raw、generic clock、KC′及完整负控的同预算证据决定。

`VERIFIED`：P1 不允许“首次”“原创时间坐标”“原创界面自适应”“VO2 验证”“实验真值”或“组合本身即创新”等措辞。R1 可以进入 P2，但创新范围已主动缩减。

## 证据等级

| 等级 | 在 R1 中的含义 |
|---|---|
| `A` | 来源直接支持同一方程、现象或边界角色；仍不自动转移材料参数。 |
| `A′` | 来源支持模型类别或机制，但 R1 对几何、变量、边界或尺度作了透明适配。 |
| `ENGINEERING` | 为辨别方法而预声明的派生 benchmark 选择；不得借来源写成材料事实。 |

## 一手来源卡（11 项）

| ID | 一手来源与固定入口 | 对 R1 的直接用途 | 等级与边界 | 代码、数据与许可 |
|---|---|---|---|---|
| S1 | Monas et al., *Phase field modeling of phase transitions stimulated by Joule heating*, J. Crystal Growth 375 (2013), [DOI 10.1016/j.jcrysgro.2013.04.017](https://doi.org/10.1016/j.jcrysgro.2013.04.017) | 电流/Joule 热驱动相界、薄膜冷却、导电率相依、成核/前沿与二维/三维形态。 | `A′`：支持电—热—相场类别；R1 的双周期、参数和器件几何不是该文作者 oracle。 | 出版物入口固定；未发现可采用的固定开放代码/数据包；按出版者权利使用事实与公式，不复制资产。 |
| S2 | Zhang et al., *High-throughput phase-field simulations and machine learning of resistive switching in resistive random-access memory*, npj Comput. Mater. 6, 198 (2020), [DOI 10.1038/s41524-020-00455-8](https://doi.org/10.1038/s41524-020-00455-8) | 二维氧化物器件中的电流连续性、Joule 热传输、自洽局域场及电极热沉边界。 | `A` 支持 `div(sigma grad phi)=0` 与 Joule 热项；`A′` 支持 R1 类别。其序参量是氧空位且热方程为其合同，不可冒充 R1 Allen–Cahn oracle。 | 论文 CC BY 4.0；页面给出补充材料，未提供本项目可直接复用的固定 solver 代码。 |
| S3 | Shi & Chen, *Current-Driven Insulator-To-Metal Transition in Strongly Correlated VO2*, Phys. Rev. Applied 11, 014059 (2019), [DOI 10.1103/PhysRevApplied.11.014059](https://doi.org/10.1103/PhysRevApplied.11.014059) | 氧化物 IMT 的相场/TDGL建模、域壁与电流/温度机制边界。 | `A′`：证明相场类别与域动力学相关；该文还明确非热电子机制可能存在，所以不能把 R1 纯电热模型表述为 VO2 完整机理。 | APS/CHORUS 文章与接受稿入口；未采用外部代码或数据。 |
| S4 | Kumar et al., *Local Temperature Redistribution and Structural Transition During Joule-Heating-Driven Conductance Switching in VO2*, Adv. Mater. 25 (2013), [DOI 10.1002/adma.201302046](https://doi.org/10.1002/adma.201302046) | 空间分辨温度重分布、结构转变与局域导电切换同时出现。 | `A` 支持“局域、空间异步现象值得建模”；`A′` 支持 R1 事件形态。不得把实验数据转写成 R1 GT。 | 出版物/作者稿入口；本项目不复制图像或实验数据。 |
| S5 | Joushaghani et al., *Voltage-controlled switching and thermal effects in VO2 nano-gap junctions*, Appl. Phys. Lett. 104, 221904 (2014), [DOI 10.1063/1.4881155](https://doi.org/10.1063/1.4881155) | 器件几何、接触材料与电流会显著影响 Joule 热和转变。 | `A` 支持独立的接触/几何因子 `A`；具体掩膜与接触比例为 `ENGINEERING`。 | OSTI/出版物元数据可追溯；未发现可采用的固定代码/数据包。 |
| S6 | O'Callahan et al., *Inhomogeneity of the ultrafast insulator-to-metal transition dynamics of VO2*, Nat. Commun. 6, 6849 (2015), [DOI 10.1038/ncomms7849](https://doi.org/10.1038/ncomms7849) | 纳米尺度转变时序与域形态对缺陷、掺杂、化学计量等微小空间差异敏感。 | `A` 支持独立材料非均匀性因子 `H`；R1 的确定性 `Tc`/mobility 场和幅度为 `ENGINEERING`。 | 开放网页提供正文；本项目不复制图像或原始数据。 |
| S7 | Ji et al., *Stiff-PINN: Physics-Informed Neural Network for Stiff Chemical Kinetics* (2020/2021), [arXiv:2011.04520](https://arxiv.org/abs/2011.04520) | 普通 PINN 在刚性动力学上可能失败；该文用 QSSA 降阶。 | `A′`：支持先诊断时间刚性；它不是 KC′直接先例，且 R1 不采用 QSSA 改物理。 | arXiv 固定稿；未将其代码或 QSSA 实现引入 R1。 |
| S8 | Wang, Sankaran & Perdikaris, *Respecting Causality for Training Physics-Informed Neural Networks*, CMAME 421, 116813 (2024), [arXiv:2203.07404](https://arxiv.org/abs/2203.07404) | 时间演化 PINN 的因果训练与时间加权是强 baseline/邻近工作。 | `A` 支持 causal/generic 时间 baseline；不等同于相态选择性局部坐标回拉。 | 官方 JAX-PI 仓库可追溯，但当前许可证限非营利研究并限制再分发；R1 不复制其代码，只独立实现合同所需比较器。 |
| S9 | Chen et al., *A coordinate transformation-based physics-informed neural networks for hyperbolic conservation laws*, JCP 2025, [DOI 10.1016/j.jcp.2025.114161](https://doi.org/10.1016/j.jcp.2025.114161) | 学习/使用坐标变换并在变换域执行 PDE 已有直接 PINN 先例。 | `A` 支持“坐标变换 PINN 非首创”；其特征曲线、双分支/子域方案与 KC′ 的 `eta` 局部单调时钟不完全同构。 | 出版物固定入口；本审查未确认可采用的固定开放代码许可，因此不复制实现。 |
| S10 | Wu et al., *A comprehensive study of non-adaptive and residual-based adaptive sampling for PINNs*, CMAME 403, 115671 (2023), [DOI 10.1016/j.cma.2022.115671](https://doi.org/10.1016/j.cma.2022.115671), [官方代码](https://github.com/lu-group/pinn-sampling) | RAD/RAR-D、残差分布采样及 Allen–Cahn 实验构成 IRAC 的强直接邻域和 baseline。 | `A`：残差自适应与 Allen–Cahn 组合已知；IRAC 不得据界面加权宣称首创。 | 官方仓库 Apache-2.0；仅作为 baseline 事实/设计参考，若后续采用代码须固定 commit 并保留许可。当前未复制。 |
| S11 | Daw et al., *Mitigating Propagation Failures in PINNs using Retain-Resample-Release (R3) Sampling*, ICML/PMLR 2023, [PMLR 论文](https://proceedings.mlr.press/v202/daw23a.html), [arXiv:2207.02338](https://arxiv.org/abs/2207.02338) | R3 用高残差保留—重采样—释放，且含 causal 扩展与 Allen–Cahn 结果。 | `A`：IRAC 的残差信号、固定点预算和动态重采样必须与 R3/RAD 类方法区分并比较。 | PMLR 论文固定开放；本项目不复制未核验许可的外部实现。 |

全部来源共同支持“类别与边界”，不允许跨来源拼接出一个不存在的作者级参数 oracle。

## 物理合同来源映射

| R1 元素 | 身份 | 来源与允许解释 | 尚未由来源决定的内容 |
|---|---|---|---|
| `div[sigma(eta,T) grad phi]=0` | `A` 方程类别，`A′` R1 适配 | S2 直接给出电流连续性；S1/S3 支持相依导电与相场耦合。 | `sigma` 插值、对比度、温度系数、接触电阻。 |
| `rho cp dT/dt = div(k grad T) + sigma|grad phi|^2 - q_loss` | `A′` | S1/S2 支持 Joule 热与散热/热沉；R1 用瞬态式闭合因果链。 | `rho cp`、`k`、损失形式、冷却时间、脉冲幅度。 |
| `d eta/dt = -L(T)[d_eta f - kappa laplacian eta]` | `A′` | S1/S3 支持相场/TDGL 类演化、界面与域动力学。 | 双阱形式、`L(T)`、`kappa`、界面宽度、噪声/成核处理。 |
| 接触/几何不对称 `A` | `A′` | S4/S5 支持局域热重分布及几何/接触敏感性。 | 掩膜、面积、偏置方向和强度均为 `ENGINEERING`。 |
| 材料非均匀性 `H` | `A′` | S6 支持空间变化的转变动力学/域形态。 | 确定性场的形状、幅度和随机种子均为 `ENGINEERING`。 |
| 二维尺寸、双 formation–recovery 周期、series resistor、无量纲尺度 | `ENGINEERING` | 用于让时间/空间瓶颈可辨并抑制失控，而不是拟合具名材料。 | 必须在 P2 首次结果前冻结事件阈值；参数修订只能留在 development 谱系。 |

R1 的无量纲化必须显式给出 `x/Lx, y/Ly, t/t_cycle, (T-Tamb)/DeltaT, phi/Vdrive`，并保存反向单位映射。选择的量纲数值若没有单一来源同构支持，一律标为 `ENGINEERING`，不得以“在文献范围内”替代谱系。

## claim–collision 矩阵

| 拟议元素 | 已知直接邻域 | 碰撞程度 | R1 仍可检验的窄差异 | 禁止主张 |
|---|---|---|---|---|
| strong raw 三场 PINN | 通用 strong-form PINN；S7/S8 的刚性/因果失败研究 | 高 | 作为共同基线和诊断器，无创新票。 | “新 PINN 架构”。 |
| generic monotone clock | 时间加权、causal training、时间分段/变换；S8/S9 | 高 | 作为 KC′ 的必要比较器。 | “首次可学习时间坐标”。 |
| KC′ | S8 的时间因果机制；S9 的坐标变换 PINN | 中高 | 只对 `eta` 使用空间局部、严格单调 `tau_eta(x,y,t)`；完整一/二阶回拉；`phi,T` 留在物理时间；计算图隔离和 kinetics-alignment 负控。 | “坐标变换/时间扭曲首创”“改变物理时间尺度后仍是原 PDE”。 |
| IRAC | S10 的 RAD/RAR-D；S11 的 R3/causal R3；Allen–Cahn 已被直接测试 | 很高 | detached、量纲归一的界面＋多 PDE 残差评分；固定候选池、实际预算与 score-shuffle 负控。 | “界面感知自适应配点首创”“残差采样首创”。 |
| KC′+IRAC | 时间机制与残差采样组合在广义上邻近 S8/S10/S11 | 高 | 只能用预注册 DID 交互量检验是否出现超加和增量；组合本身不是贡献。 | “两个已知模块组合即创新”“无 factorial 也可归因协同”。 |
| A×H 物理因子与四池拆分 | 物理现象由 S4–S6 支持；具体试验设计为本项目工程合同 | 中 | 作为因果拆分与泄漏防护，不作为科学新颖性。 | “首次发现几何/非均匀性影响”。 |

## FULL_DESIGN 闭合

- 论文去向：数值/PINN 方法论文候选；只能围绕派生多物理 benchmark 上的窄 KC′机制、可归因模块增量或有界负结果路由。具体期刊仍为 `UNKNOWN`，不影响 P2。
- 预期证据：独立 CPU oracle 的两周期局域异步事件、零驱动/耗散/守恒、两最细离散层收敛、外部 evaluator、完整 intent-to-run 台账。
- 强基线：strong raw、generic monotone/causal 时间 baseline、uniform sampling、残差自适应/RAD-R3 类 baseline；六臂固定为 B、generic clock、KC′、IRAC、KC′+IRAC、IRAC-score shuffle。
- 关键消融：`eta`-only 与 generic clock、完整回拉守卫、IRAC 与 shuffle、单模块与组合、A×H 四单元、相同候选池和实际计算预算。
- 数据拆分：oracle qualification、joint development、one-shot formal OOD、reserve 四池按完整几何/协议/非均匀性家族隔离。P1 不生成或读取 formal/reserve。
- formal OOD：设计保留，但授权包 A 明确关闭；P2–P5 只能使用 qualification/development。
- 预算：P2 首个可信事件不超过 48 墙钟小时或 64 CPU-core-hours；P3 不超过 12 qualification intents；P4 不超过 16 training intents；P5 不超过 12 training intents。
- 停止条件：物理/事件/收敛/守恒失败即停；raw 无共同基线或无可辨瓶颈即停；KC′不胜 generic clock、IRAC不胜 shuffle、任一守卫失败时删除对应创新票；不得换材料、移动阈值、追加 seed 或打开 formal/reserve 救援。

## P1 门禁裁决

`P1_PASS_WITH_SCOPE_REDUCTION`

1. 物理合同存在可追溯的类别级依据；具体 R1 参数、几何、边界与无量纲映射必须在 `R1PhysicalContract` 中透明标为 `ENGINEERING`。
2. 未发现 KC′窄定义的完全同构先例，但这只是有界检索后的 `HYPOTHESIS`，不是优先权结论。P2/P4/P5 仍须把 generic 时间方法和完整回拉作为硬比较。
3. IRAC 核心高度碰撞，降为支撑性模块候选；只有在严格 shuffle/RAD-R3 邻域对照和实际计算公平下出现独立增量，才可保留次级贡献。
4. P2 获准在授权包 A 内开始；若新对象无法在预冻结阈值下给出合格 A1H1 事件，R1 立即以有界 No-Go 收口。
