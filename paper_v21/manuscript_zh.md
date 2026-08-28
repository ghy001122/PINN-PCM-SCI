# 当“事件有效”不等于“Oracle 有效”：PINN 训练前两周期电热—相场 benchmark 的失败保全资格化

## 摘要

物理信息神经网络（PINN）的评价精度，不可能高于其所依赖的参考对象、数值求解器和端点定义本身的可信度。对于局域电热相变问题，这一依赖尤为关键：看似平滑且物理合理的开关轨迹，仍可能隐藏事件定位或网格细化不稳定。本文报告一项预注册、失败保全的资格化研究，目标是在开展后续 PINN 比较前，建立一个透明的二维合成电热—相场 benchmark。研究将非投票工程阶段与投票科学阶段严格分离。工程阶段先修复控制分支的 Newton 失败，再从 41 个有界候选中选择一个局域、两周期、完全恢复的事件对象。任何投票求解开始前，项目冻结了对象、128 个 complete-case 的数据拆分、14-intent oracle 阶梯、六个端点分量、机制/几何 controls、收敛规则、作者指标复现身份，以及下游 PHA-MF × field-selective kinetics clock 的归因规则。

14 个资格化 intent 全部完成，没有求解失败或 numerical hard-guard 失败。名义 coarse、medium、fine、extra-fine、半时间步、exact replay 和独立 solver cross-check 均形成两周期事件；zero-drive 与 Joule-off 均无事件；fine replay 的保存数组逐项完全一致。然而，两周期 event-time 分量的差异从 medium→fine 的 0.00120677 增大到 fine→extra-fine 的 0.00164868，违反逐分量单调收敛硬门，尽管其余五个分量均收缩。预注册路线因此返回 PHK_V21_ORACLE_NO_GO_STOP_BEFORE_PINN。Sharp-PINNs/PF-PINNs 作者指标复现、neural floor 封存、PINN 训练、PHA-MF、field-selective kinetics clock 以及 formal OOD 均未到达。该案例说明：事件存在、硬守卫通过、精确复放和肉眼上的跨分辨率一致，并不能共同保证 oracle 可准入。本文的核心贡献是一套具体的资格化模式，阻止未合格的参考过程被转化为表面上积极的 PINN 证据。

**关键词：** 物理信息神经网络；相场；电热开关；数值验证；事件定位；负结果；benchmark 资格化

## 1. 引言

PINN 将偏微分方程或本构残差显式纳入训练目标，已广泛用于正问题、反问题和代理建模。相场 PINN 又进一步引入 Fourier embedding、hard constraint、staggered training、自适应采样、gradient balancing、causal segmentation 与更深的残差架构，以处理移动界面和多尺度动力学。然而，这些网络侧改进不能消除一个更上游的依赖：参考解及其派生端点必须先具有足够的数值可信度。

这一问题很容易被低估。一个场轨迹可以保持有限、有界、在容差内守恒、能够精确复放，并且在多张网格图上看起来相似；每条轨迹也可以都发生开关事件。但阈值事件时间仍可能因空间—时间离散、界面几何与保存时刻插值的耦合而不单调收敛。如果这样的过程被直接称作 oracle，神经误差便是在一个自身尚未闭合的量上归一化，所谓 PINN “涨点”可能来自参考过程或指标抽取，而不是网络方法。

传统 verification and validation 区分代码正确性、数值解验证和模型验证。PINN 文献常将主要注意力放在网络侧，例如优化病态、残差采样、频谱表示和因果训练；参考求解器往往被压缩成一张标称网格或一份作者数据。对于电热相变系统，这种压缩风险很高，因为局域 Joule heating、本构反馈、界面动力学和脉冲历史相互耦合。

本文提出一个刻意前移的问题：在“魔改”强 phase-field PINN baseline 之前，能否先把一个二维、局域、两周期、可恢复的电热—相场对象及其参考求解器资格化到足以支持 neural attribution 的程度？原计划的下游方法由两个承重模块组成：phase–hotspot-aware multi-frequency routing（PHA-MF）与 field-selective monotone kinetics clock。Sharp-PINNs 是 phase-field anchor，PF-PINNs 是 sampling/weighting anchor，adaptive pseudo-time 是检验 kinetics-specific 叙事的强制反事实 control。但合同要求：oracle 门通过前，不运行作者指标复现，也不训练 PINN。

本文形成四项有界贡献：

1. 建立工程—科学双阶段工作流：工程阶段允许广泛但不投票的修复与搜索；对象选定后，所有科学决策在首个投票求解前冻结。
2. 给出一个透明二维合成电热—相场对象的完整 14-intent 资格化记录，覆盖名义细化、时间细化、精确复放、机制 controls、几何 controls 和独立 fixed-solver cross-check。
3. 固定一个具体失败模式：所有名义分辨率均“事件有效”，但 event-time 分量未通过预注册收敛规则，故不具备 oracle 身份。
4. 保全该失败的科学后果：不开展 neural experiment，不把候选 floor 文件改称合格 neural floor。

![PHK-V2.1 失败保全路线](figures/figure-01-route-outcome.png)

**图 1.** 独立 PHK-V2.1 路线先完成 solver engineering、有界对象筛选、科学冻结和 14/14 资格化执行；event-time 收敛失败在作者指标复现和 PINN 训练前关闭路线。

## 2. 研究设计

### 2.1 工程证据与科学证据分离

旧 PHK-V2 终止于自己的 Oracle No-Go。PHK-V2.1 没有修改或重跑旧 intent，而是建立独立对象、独立合同和独立实验身份。工程阶段包括：

- 对旧 control-branch failure 的最小红色复现；
- legacy damped Newton、trust-region reflective、logit analytic Newton、pseudo-transient Newton、smaller-step diagnostic 与 Anderson outer coupling 的有界比较；
- 16 个 coarse factorial、16 个 refinement 和最多 3 个 medium promotion；
- 最终候选的 zero/Joule-off/conductivity-off/latent-off/wide-heater/narrow-interface controls。

工程输出只决定哪个对象和固定 solver 进入 S0，不能投票，也不进入 neural floor。最终选择 logit analytic Newton；41/41 个有界工程 case 完成，并选定唯一候选 PHK_V21_E2_STAGE2_0A1813B1D968F573。

随后冻结五份科学合同：object/numerical、128-case split、oracle/floor、baseline replication 和 method attribution。冻结发生在任何 S1 数值结果之前。Q、D、I1、I2、F_A、F_O 与 reserve 按完整 case 身份分离，同一个器件/几何/协议/历史不跨 pool。

### 2.2 透明合成对象

对象是无量纲、literature-inspired 的二维 wall-cell，并非某种真实 PCM 材料或商业器件的校准模型。状态包括相场、温度和电势；因果链为电势梯度产生 Joule heating，温度和相依赖系数驱动相态演化，相态再反馈导电与热行为。边界和波形在 object contract 中显式给出。

选择标准要求每个周期均产生新的 upward event，事件至少持续三个保存步，周期恢复率不低于 0.70，峰值漂移不超过 0.20，全域和 ROI 外峰值受限，Joule-off 不得发生事件，所有 controls 可执行且 numerical guards 通过。工程候选满足这些条件后才进入冻结。

这种透明性同时限定主张：对象适合检验求解、事件抽取和 PINN 方法流程，却不支持材料定量预测、实验验证或真实器件性能主张。

### 2.3 14-intent qualification ladder

![14-intent qualification ladder](figures/figure-02-qualification-ladder.png)

**图 2.** 14 个预注册 intent 均完成且没有替换。wide-heater control 丢失第二周期事件，但该 control 只要求完成并通过数值守卫；最终判决来自完整收敛比较，而非 execution failure。

冻结顺序包括：

1. manufactured operator；
2. zero-drive medium；
3–6. nominal coarse、medium、fine、extra-fine；
7. nominal medium half-dt；
8. fine exact replay；
9. Joule gain zero；
10. conductivity phase ratio one；
11. latent ratio zero；
12. heater width 0.50；
13. interface width 0.025；
14. pseudo-transient solver cross-check。

每个 intent 保留 immutable intent、result/report、manifest、CPU accounting 和哈希身份。失败不得替换 case 或 seed，也不得在看到结果后救援式调整 solver。

### 2.4 事件、守卫和六分量收敛

每个周期从 ROI phase fraction 的预注册 upward threshold crossing 提取 event time，并记录 event existence、peak、duration、locality 和 recovery。数值守卫独立检查状态 bounds、质量/热/电平衡、有限性、残差、端口符号和复放一致性；守卫不能被均值指标抵消。

oracle 收敛采用六个承重分量：

1. phase-field ROI RMS；
2. temperature-field ROI RMS；
3. terminal-current trace RMS；
4. two-cycle event-time RMS；
5. time-averaged phase-region symmetric difference；
6. two-cycle recovery RMS。

每个分量都必须满足 medium→fine→extra-fine 的单调收缩及合同规定的 strict contraction。合格 floor 应在 neural work 前按同一端点定义封存。任一分量失败均关闭 oracle；禁止先对六分量平均，再让五项通过掩盖一项失败。

## 3. 结果

### 3.1 所有名义分辨率均形成两周期事件

14 个 intent 全部完成，0 solver execution failure、0 hard-guard failure。coarse、medium、fine 和 extra-fine 的两周期 event times 分别为：

| 分辨率 | 周期 1 | 周期 2 |
| --- | ---: | ---: |
| coarse | 0.2271 | 1.4871 |
| medium | 0.2378 | 1.4942 |
| fine | 0.2389833 | 1.495975 |
| extra-fine | 0.2406 | 1.4984 |

所有 nominal recovery 均为 1.0。单看场图、峰值和事件时刻，这四条轨迹很容易被判断为“已经收敛得足够好”。

![名义两周期事件](figures/figure-03-nominal-events.png)

**图 3.** 四个名义分辨率均出现局域两周期事件并完全恢复。图形稳定性说明 event existence 只是必要条件，而不是 oracle qualification 的充分条件。

### 3.2 Controls 支持有限的因果与几何解释

zero-drive 和 Joule-off 的 ROI peak 均为零且无事件。因而在该透明合成对象、该冻结参数和波形下，Joule heating 对名义事件是必要条件。conductivity-ratio-one 与 latent-off 仍保留两周期事件，说明相依赖导电反馈和冻结 latent term 在各自单项 control 下并非事件形成的必要条件。wide-heater 保留第一周期但失去第二周期事件；narrow-interface 仍形成两周期事件，表明对象具有明确的几何敏感性。

这些结论不外推到真实材料，也不证明被关闭机制在一般条件下无关。

![机制与几何 controls](figures/figure-04-controls.png)

**图 4.** nominal 与五个 controls 的 ROI peak。Joule-off 消除事件，conductivity-ratio-one 和 latent-off 保留事件，wide-heater 丢失第二周期，narrow-interface 仍为两周期 event-positive。

### 3.3 一个派生分量独立关闭 oracle

medium→fine 与 fine→extra-fine 的六分量差异为：

| 分量 | medium→fine | fine→extra-fine | 判决 |
| --- | ---: | ---: | --- |
| phase-field ROI RMS | 0.00916472 | 0.00459165 | pass |
| temperature ROI RMS | 0.00253754 | 0.00125692 | pass |
| terminal-current RMS | 0.00232607 | 0.00121072 | pass |
| two-cycle event-time RMS | 0.00120677 | 0.00164868 | **fail** |
| phase-region symmetric difference | 0.00030375 | 0.000145 | pass |
| two-cycle recovery RMS | 0 | 0 | pass |

event-time 的 fine→extra-fine 差异约为前一级的 1.37 倍，既不单调也不收缩。其他五项不能把这一失败平均掉。terminal summary 因此返回 PHK_V21_ORACLE_NO_GO_STOP_BEFORE_PINN，且 floor_sealed_and_converged=false。

![决定性的逐分量收敛门](figures/figure-05-convergence-gate.png)

**图 5.** 纵轴为 fine→extra-fine 差异除以 medium→fine 差异与该分量容差两者较大值。比值不超过 1 才通过。五个分量通过，event-time 单独关闭 oracle。

候选 floor carrier 仍被保留，因为它记录了所有比较和 normalizer；但它不是合格 neural floor，任何下游方法不得消费它。

### 3.4 两个实现缺陷在不改变科学数值的条件下得到协调

intent 2 的 immutable carrier 中，dataclasses.asdict 保留 tuple，而 list-only 的 no-event helper 将其拒绝。项目没有重跑 solver，而是对原始两周期值重新计算 Boolean，并将原 result/report/manifest 保留为不可变证据。

第一次 terminal summary 尝试又发现 inherited short labels 与 V2.1 long labels 不一致。修复仅做 position-preserving label mapping，不重排、不重算任何值；失败尝试没有写出 summary、floor、intent、manifest 或 ledger row。

两项 amendment 都是实现层 reconciliation，不提供科学证据，也不改变 No-Go 的原因。

## 4. 为什么没有后续 PINN 实验

本研究没有训练 PINN，并非工作遗漏，而是预注册停止规则正确执行。下游链条依赖合格 oracle：

qualified object → oracle/event/controls/floor → Sharp/PF author-metric replication → strong raw → bottleneck diagnosis → PHA/KC attribution → formal OOD。

S1 oracle 门失败后，Sharp/PF、neural floor、strong raw、四臂诊断、PHA-MF、KC、2×2、GPU、formal/OOD 全部标记 NOT_REACHED，训练 case intent 为零。不能将 NOT_REACHED 写成 baseline 或方法失败，也不能把 candidate floor 用于训练误差归一化。

![证据边界与计算计账](figures/figure-06-claim-boundary.png)

**图 6.** 证据只累积到 14 个资格化 intent。Oracle 层返回 No-Go，后续作者指标复现、PINN、PHA/KC 与 formal OOD 未到达。S1 求解共记录 1.128515625 CPU core-hours，无 GPU、无失败 solver intent。

## 5. 讨论

### 5.1 事件存在弱于事件收敛

四个名义分辨率都发生事件，并不意味着阈值事件时间已经收敛。事件时间是场解、阈值和插值共同作用的派生量，对界面运动和保存时刻尤其敏感。只有 event existence 或一张平滑曲线，无法替代端点级 convergence check。

### 5.2 逐分量硬门防止“有利平均”

若先把六分量聚合成一个均值，phase、temperature、current、region 和 recovery 的改善可能掩盖 event-time 的反向变化。本文把每个承重端点作为独立硬门，因而保留了方法论文真正需要的端点可信度。

### 5.3 工程成功不等于科学资格化

solver 修复成功、41 个工程 case 完成、14/14 scientific intents 完成，都不自动等于 oracle PASS。工程阶段回答“能否稳定执行并找到候选”，科学阶段回答“冻结对象及其端点是否达到投票资格”。二者必须分层。

### 5.4 负资格化可以节约 neural compute

路线在任何 PINN 训练前终止，避免了在不合格 floor 上运行多 seed、2×2 attribution 和 formal OOD。节省计算不是主要贡献，但说明上游资格化具有直接方法学价值。

## 6. 局限与未来工作

首先，对象是透明的合成 wall-cell，不能支持真实材料或器件定量结论。其次，本研究只判决冻结的网格、时间步、事件抽取和收敛规则；不同的 prospective contract 是否能恢复 event-time 单调收敛仍为 UNKNOWN。第三，pseudo-transient cross-check 支持独立 solver 轨迹一致，但不能替代细化收敛。第四，Sharp/PF 作者指标与 PHA/KC 模块完全未运行，因此本文没有方法优劣证据。

任何后续路线都必须建立新的前瞻合同，而不能回写本 No-Go。合理选项包括：在新合同中提高 event localization order、改变保存时刻与 threshold-interpolation 方案，或重新设计对象使事件时间远离离散敏感区；这些都需要重新冻结对象、numerical hierarchy 与 endpoint rule。只有新的 oracle 实际通过后，才能恢复 baseline replication 和 PINN attribution。

## 7. 结论

本文尝试在 PINN 方法比较前，资格化一个二维、局域、两周期电热—相场 benchmark。控制 solver 得到修复，唯一工程候选被选定，五份科学合同在结果前冻结，14 个 qualification intents 全部完成。名义事件、controls、hard guards、exact replay 和独立 solver cross-check 均按预期工作，但两周期 event-time 分量未通过空间收敛硬门。因此路线在作者指标复现和神经训练前关闭。

该结果支持一条实用原则：轨迹可以 event-valid，却不一定 oracle-valid。PINN 比较应把 reference qualification 视为上游科学门，而不是背景工程细节。当该门失败时，保全失败并停止，比继续生成 neural curves 更可信。

## 数据与代码可得性

本地复现包包括五份冻结合同、两项 implementation amendment、14 个 intent/report/result/manifest 身份、terminal summary、candidate floor carrier、六份 figure CSV、六幅 PNG/PDF、表格、补充材料、复现说明、claim–evidence matrix 和 reviewer-risk audit。包中不含外部 GPL 源码树、商业模型资产、凭据或实验数据。外部上传、投稿和期刊接收均不属于本文科学结论。

## 声明

**经费：** 由作者在投稿前补充。

**利益冲突：** 由作者在投稿前补充。

**作者贡献：** 由作者在投稿前补充。

**致谢：** 由作者在投稿前补充。
