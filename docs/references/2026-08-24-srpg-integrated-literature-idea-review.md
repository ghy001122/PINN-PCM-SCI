# SRPG-PINN 综合文献、Idea 碰撞与实施前审查

> 审查日期：2026-08-24  
> 文档状态：`SUPERSEDED_IN_PART_AS_CURRENT_DECISION_ENTRY`  
> 候选状态：`CONDITIONAL_RETAIN / REVISE_BEFORE_IMPLEMENTATION / PROPOSED_NOT_AUTHORIZED`  
> 科学主张：`NO_SCIENTIFIC_METHOD_CLAIMS`  
> 执行边界：本轮只整合文献与既有 IdeaSpark 审查；`0 solve / 0 training / 0 formal OOD`。  
> 当前覆盖：本报告保留为 SRPG 广义碰撞、来源对象与 IdeaSpark 演化快照；其当前对象、初态、side 门和方法路由已由 [HFO-NP-v1 对抗性审查整合](2026-08-24-hfo-np-v1-srpg-kc-adversarial-integration.md) 与 [ADR 0031](../adr/0031-revise-hfo-source-side-gate-and-method-routing.md) 部分覆盖。

## 1. 本轮整合了什么

本报告合并三类输入：

1. IdeaSpark 的完整候选演化、两次 abandon、最终 SRPG 方法合同和可实现性审计；
2. 项目内 2026-08-23 的一手来源审查，包括 48 项论文记录、26 个官方代码/数据载体和 10 个对象家族；
3. 用户提供的 `E:\PINN-PCM\deep-research-report2.md`。

第三项是内部深度调研输入，不是独立科学证据。只有能够回到一手论文、作者代码或既有项目核验记录的内容才被采纳。原文件中的会话式引用占位符、主观 1–5 分评分、未经固定版本支持的“最近提交”以及工具失败叙事均未迁入本报告。

## 2. 综合裁决

| 问题 | 当前裁决 | 决策含义 |
|---|---|---|
| 是否发现完整同构方法？ | `NO_EXACT_BUNDLE_COLLISION_FOUND_IN_BOUNDED_SEARCH` | `VERIFIED`：在本次有界一手来源集合中未发现完整覆盖 SRPG 全机制束的工作；这不是世界首创或投稿时新颖性保证。 |
| 宽泛创新是否成立？ | `BROAD_CLAIM_COLLISION_CONFIRMED` | `VERIFIED`：参数敏感 PINN、PDE 导数正则、stop-gradient 物理自目标、潜空间结构化、相场强训练和 causal/adaptive interface PINN 均已有直接先例。 |
| 当前是否有可直接使用的来源原生开放 oracle？ | `OPEN_INDEPENDENT_ORACLE_NO_GO` | `VERIFIED`：没有单一对象同时闭合开放许可、固定实现、动态电—热—相态、绝对时间和完整局域器件事件。 |
| 透明派生对象是否被永久禁止？ | `NO` | `VERIFIED`：[ADR 0026](../adr/0026-allow-transparent-derived-objects-and-bounded-method-recombination.md) 允许另行设计 `derived/synthetic` 对象；但当前尚未选择、推导或授权这种对象，且不得冒充来源原生 oracle。 |
| SRPG 是否可立即实现？ | `NO / NEW_PLAN_REQUIRED` | `SUPPORTED_INTERPRETATION`：当前最早阻塞是对象合同未选定；history/state 充分性、双侧非对称、strong raw 和方法可辨识性也未闭合。 |
| SRPG 是否值得保留？ | `CONDITIONAL_RETAIN` | `HYPOTHESIS`：只保留“阈值两侧不能由同一切线描述时，分侧有限响应是否有增量”这一窄问题。 |

最重要的更新是：**“没有来源原生开放 oracle”只关闭直接复现路线，不等于关闭所有透明派生对象；但在新的对象合同获得批准并通过资格门之前，SRPG 仍无实施资格。**

## 3. 当前唯一可保留的研究问题

安全的论文问题不是“参数敏感度能否提升 PINN”，而是：

> 当阈值、分岔或迟滞事件邻域的正负协议响应不能由同一个局部切线描述时，在固定时空支撑上分别保留两侧有限响应，能否相对 SA-PINN、Jacobian/tangent、FP64 strong raw 和最强相场 causal/adaptive 基线，稳定改善完整案例的 onset、coverage 与 recovery？

对应的安全方法定位是：

> **A fixed-support, side-resolved finite-protocol representation regularizer for PINNs near thresholded or hysteretic phase-field events.**

“event-faithful”只能表示研究目标，不能在训练前作为已证明性质写入标题或结论。“parameter sensitivity”“physics self-distillation”“latent physics discovery”“first phase-field PINN”均不得作为主要新颖性表述。

## 4. 修订后的 SRPG 方法合同

### 4.1 协议与 history/state 充分性

迟滞对象中的瞬时电压不是天然充分状态。[Sevic–Juston–Kobayashi 2025](https://arxiv.org/abs/2506.17421)直接研究形貌自洽的 memristive I–V hysteresis；同一个瞬时控制值可对应不同历史和不同内部形貌。因此，未来合同必须在二者中选择一个：

- `p` 是包含脉冲/扫压历史的完整协议描述，并与初态、周期和 branch identity 一起进入完整案例身份；或
- 网络显式接收足以区分分支的当前物理 state/history representation。

若两个历史不同的案例在相同瞬时控制值下产生显著不同状态，而模型输入无法区分，裁决 `HISTORY_SUFFICIENCY_NO_GO`。此时不得把 `p+` 与 `p-` 解释为围绕同一物理状态的两侧响应。

### 4.2 固定支撑双侧视图

对冻结协议表示 `p`、方向 `d`、物理尺度 `A_d` 和扰动比例 `ε_p`，只在两侧均位于许可协议包络内时构造：

\[
p_d^s=p+s\,\epsilon_p A_d e_d,\qquad s\in\{-1,+1\}.
\]

`p`、`p+`、`p-` 必须共享时空坐标、IC/BC/PDE mask 和完整案例身份。不得 clipping、只保留成功一侧、按结果选方向或移动 attribution track 的 collocation support。

### 4.3 同网络相律响应与固定槽位

\[
r_d^s(\xi)=\operatorname{sg}\!\left[
\frac{\Phi_\eta(u_\theta(\xi;p_d^s))-\Phi_\eta(u_\theta(\xi;p))}{S_\Phi}
\right].
\]

固定不可训练选择器 `q_{d,s}` 读取 pre-head latent 位移，并用标量 Huber 损失与 `r_d^s` 对齐。`r_d^s` 由同一网络产生，只是 PDE-derived auxiliary conditioning；stop-gradient 不会把它变成外部物理真值，也不能证明 latent slot 具有唯一物理语义。

### 4.4 双侧非对称资格指标

外部报告提出了有价值的低成本 kill-test，但其符号 `A_d` 与协议物理尺度重名。本报告改记为：

\[
\mathcal A_{\mathrm{side},d}=
\frac{\left\|\Delta\Phi_d^+ + \Delta\Phi_d^-\right\|}
{\left\|\Delta\Phi_d^+\right\|+\left\|\Delta\Phi_d^-\right\|+\varepsilon_{\mathrm{den}}}.
\]

该量只能由独立 oracle/资格轨迹评价，不进入训练。平滑局部线性区预期 `ΔΦ+≈−ΔΦ−`，因而 `𝒜_side,d≈0`；若所有事件邻域均接近零，SA-PINN/切线信息已可能足够，应裁决 `NO_SIDE_RESOLVED_INFORMATION`，停止 SRPG，而不是继续调 `ε_p` 或损失权重。

这仍是 `HYPOTHESIS` 和未来 PLAN 的候选门，不是已执行结果。

## 5. 关键碰撞与强基线

| 工作 | 已占据的空间 | SRPG 仅剩差异 | 当前作用 |
|---|---|---|---|
| [SA-PINN](https://arxiv.org/abs/2301.02428) | 标称参数邻域的 PDE/IC/BC 参数导数正则与局部敏感度 | 显式正负有限响应、latent side slots、事件端点 | **最危险 direct-near；必须是主基线** |
| [gPINN](https://arxiv.org/abs/2111.02801) 与 [DC-PINN](https://doi.org/10.1103/5bbf-p6zk) | residual gradient 与单边导数约束 | 协议双侧、同点有限响应及表示几何 | 阻止宽泛 derivative-enhanced claim |
| [NPSolver](https://arxiv.org/abs/2605.25786) 与 [PIDO](https://arxiv.org/abs/2411.19125) | 同输出物理修正后的 stop-gradient target；同模型 latent pseudo-label alignment | 双侧协议相律响应与固定槽 | self-target/self-distillation 强碰撞 |
| [PF-PINNs](https://doi.org/10.1016/j.jcp.2025.113843) | AC/CH normalization、界面自适应采样与 NTK weighting | 不建模分侧协议表示 | 相场 strong raw 基线；[代码](https://github.com/NanxiiChen/PF-PINNs)为 GPL-3.0 |
| [Sharp-PINNs](https://arxiv.org/abs/2502.11942) | staggered AC/CH、RFF、modified MLP、hard constraints、causal/RAR | 无 `p±` response slots | 相场强架构基线；[代码](https://github.com/NanxiiChen/sharp-pinns)为 GPL-3.0 |
| [Causality-RBAR](https://arxiv.org/abs/2410.20212) | causal training 与 residual-based refinement 改善 Allen–Cahn interface | 通过移动/加密 support，而非 side geometry | 证明 bulk residual 失配真实存在，同时提供替代解释 |
| [FP64 is All You Need](https://arxiv.org/abs/2505.10949) | 指出部分 PINN failure 可由 FP32/L-BFGS 提前停止解释 | 不提出 SRPG | FP64 必须进入 strong raw；[官方代码](https://github.com/miniHuiHui/PINN_FP64)公开但本轮未确认软件许可 |
| [When PINNs Go Wrong](https://arxiv.org/abs/2604.23528) | pseudo-time、上一迭代冻结目标与局部 residual Jacobian | 无协议双侧 latent slots | causal/pseudo-time 和 frozen-target 强对照；[jaxpi2](https://github.com/sifanexisted/jaxpi2)为 Apache-2.0 |
| [Sevic–Kobayashi 2023](https://arxiv.org/abs/2307.14582) / [2025](https://arxiv.org/abs/2506.17421) | 电热相场导电丝与形貌自洽迟滞对象 | 不使用 PINN/SRPG；无作者开放 app/deck | 对象与 history gate 的主要来源，不是可直接重放 oracle |

结论保持：`BROAD_CLAIM_COLLISION_CONFIRMED`；未发现完整 bundle 只允许保留窄假设，不能升级为 novelty clearance。

## 6. 对象与 oracle 路由

### 6.1 来源原生路线

截至 2026-08-23 的审查没有发现同时满足固定实现与许可、动态电—热—相态、绝对时间、完整局域事件和开放重放材料的单一对象，因此该路线为 `OPEN_INDEPENDENT_ORACLE_NO_GO`。

2023/2025 Sevic–Kobayashi 对象最接近方程与迟滞语义，但没有作者公开的 MOOSE app/input deck/固定输出；HfO₂₋ₓ、TaOₓ 等对象具有强物理或事件证据，却依赖专有 COMSOL 且缺少合格开放实现；Q-POP 与 FerroX 分别受对象语义和既有终止证据约束。

### 6.2 透明派生路线

ADR 0026 允许另立 `derived/synthetic` 对象，但未来 PLAN 必须：

- 为每个方程、参数、边界和接口标明 `A / A′ / ENGINEERING`；
- 说明为何派生对象仍闭合电—热—相态，且不冒充作者重放、实验真值或材料定量验证；
- 使用独立 evaluator、网格/时间收敛、守恒和完整事件资格化；
- 在首次求解前冻结一个对象，不根据 SRPG 结果自动换对象或拼接救援。

当前没有选定这种对象，也没有批准其求解。因此当前实施 blocker 应写成 `SRPG_OBJECT_CONTRACT_NOT_QUALIFIED`，而不是把“来源原生开放对象不存在”夸大成所有派生路线永久失败。

## 7. 两条比较轨道

外部报告对比较设计的最有价值修订，是把归因与最佳效能分开：

| 轨道 | 回答的问题 | 最小方法集合 |
|---|---|---|
| **attribution track** | SRPG 增量是否来自固定支撑的分侧协议几何？ | 所有臂共享固定 support、网络与实际计算预算：FP64 raw、SA-PINN、gPINN/Jacobian、pairing-off、side-collapsed、SRPG |
| **best-method track** | 在现实强训练条件下 SRPG 是否仍有实用增量？ | 预冻结 PF-PINNs/Sharp-PINNs/causal-pseudo-time/RBAR 中的最强兼容基线，与 SRPG-enhanced strong solver 比较 |

固定 support 是 attribution 合同，不应被写成对 adaptive sampling 的普遍优越性。若只运行 attribution track，不能声称击败最强相场方法；若把 RAR 同时加入 SRPG，则必须另行保留固定 support 的因果归因实验。

## 8. 必须冻结的门与停止条件

### G0：对象合同

选择且只选择一个来源原生或透明派生对象，冻结许可、版本、方程、参数层级、单位、边界、绝对时间、协议和事件身份。当前尚未通过。

### G1：history 与双侧信息资格

- 运行前冻结 protocol/history/state 表示；
- 用同一瞬时控制、不同历史的完整案例检验输入充分性；
- 在独立资格轨迹上评价 `𝒜_side,d` 与 `ε_p` 稳定区间；
- `HISTORY_SUFFICIENCY_NO_GO` 或 `NO_SIDE_RESOLVED_INFORMATION` 任一触发即停止 SRPG。

本报告只定义未来门，不授权这些求解。

### G2：事件与 oracle

对象必须形成收敛、局部、部分覆盖、可重复的 onset—coverage—recovery；整域瞬翻、单网格事件、周期残留或守恒失败均终止。

### G3：FP64 strong raw 与瓶颈

strong raw 至少包含 FP64，并预先选择 causal/pseudo-time 或相场强架构。raw 到达 oracle 不确定性地板时记 `NO_BOTTLENECK`；raw 无法解析事件时记 `RAW_INCOMPETENT_ROUTE_NO_TEST`。两者都不允许 SRPG 救援。

### G4：方法可辨识性

最小控制包括：

- SA-PINN、direct output secant/Jacobian 与 gPINN；
- 相同 `1+2|D|` views 和实际计算量的 `λ_SRPG=0`；
- side-collapsed、side-balanced permutation 与 response shuffle；
- identity `Q` 对预声明随机正交 `Q`；
- 保持输出等价的 latent scale/head compensation；
- same-network target 对 delayed/EMA target 的诊断性对照；EMA 不自动成为主方法；
- wall-clock、forward/backward、AD 操作、参数量和峰值内存报告。

若随机正交基改变结论、side shuffle 不退化、SA-PINN 达到同等事件增益、strong raw 已解决问题，或效果只见于 residual/L2 而不见于完整案例事件，均停止路线。

### G5：投稿前 novelty refresh

formal 前重新核对 SA-PINN、NPSolver/PIDO、参数化 latent PINN、PF-PINNs/Sharp-PINNs、Causality-RBAR、FP64/pseudo-time 及其最新引用和作者代码。任何检索仍只能产生有界结论。

## 9. 实施就绪性

现有 IdeaSpark 可实现性审计列出的 8 个作者决策仍未关闭：完整 case/split 与协议轴、`S_Φ`、latent tap、Huber/总损失权重、事件检测器、物理守卫与聚合、Jacobian/tangent 对照、head-only control。本轮新增两个先于这些实现参数的科学决策：

1. protocol/history/state 是否足以定义同一物理分支上的 `p±`；
2. qualified object 是否存在稳定且非零的双侧非对称信息。

因此当前工程结论仍是 `REVISE_BEFORE_IMPLEMENTATION`。合成 AC/CH 小例可在未来作为机制诊断，但不能替代项目要求的二维电—热—相态主体，也不能在对象 G0 前被当作自动获批的“低成本先跑”。

## 10. 当前权威状态与下一步

```text
phase: SRPG_PREIMPLEMENTATION_REVIEW_BLOCKED
candidate: CONDITIONAL_RETAIN
novelty: NOT_NOVELTY_CLEARED
source-native object: OPEN_INDEPENDENT_ORACLE_NO_GO
derived object: NOT_SELECTED / NOT_AUTHORIZED
implementation: REVISE_BEFORE_IMPLEMENTATION / NOT_AUTHORIZED
claim: NO_SCIENTIFIC_METHOD_CLAIMS
```

下一步不是实现，而是由用户另行审查一个只处理 G0–G1 的新 PLAN。该 PLAN 必须先决定对象身份和 protocol/history 语义，再定义是否允许低成本资格求解、预算与停止条件。未经新授权，不运行 solver、oracle、PINN、training、formal OOD、GPU 或付费计算，也不重启 Q-POP、R1、R2 或自动切换新材料。

## 11. 主要来源入口

- 方法最近邻：[SA-PINN](https://arxiv.org/abs/2301.02428)、[gPINN](https://arxiv.org/abs/2111.02801)、[NPSolver](https://arxiv.org/abs/2605.25786)、[PIDO](https://arxiv.org/abs/2411.19125)。
- 相场强基线：[PF-PINNs](https://doi.org/10.1016/j.jcp.2025.113843)、[Sharp-PINNs](https://arxiv.org/abs/2502.11942)、[Causality-RBAR](https://arxiv.org/abs/2410.20212)。
- 训练可靠性：[FP64 is All You Need](https://arxiv.org/abs/2505.10949)、[When PINNs Go Wrong](https://arxiv.org/abs/2604.23528)。
- 对象与迟滞：[Sevic–Kobayashi 2023](https://arxiv.org/abs/2307.14582)、[Sevic–Juston–Kobayashi 2025](https://arxiv.org/abs/2506.17421)。
- 更完整的 48 项论文/26 个官方载体矩阵及许可账本保留在 [2026-08-23 一手审查](2026-08-23-srpg-pinn-primary-source-literature-and-collision-review.md) 中。
