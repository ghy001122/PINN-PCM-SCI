# HFO-NP-v1、SRPG 与 KC′ 对抗性审查整合及最新路线裁决

- `date`: `2026-08-24`
- `report_role`: `BASE_OBJECT_AND_Q1_Q12_DESIGN_INTEGRATION`
- `input`: 用户提供的 `E:\PINN-PCM\HFO-NP-v1、SRPG 与 KC′ 对抗性深度审查报告.md`
- `execution`: `0 solve / 0 training / 0 formal / 0 GPU`
- `supersedes_in_part`: [2026-08-24 SRPG 综合文献与 Idea 审查](2026-08-24-srpg-integrated-literature-idea-review.md)
- `decision_record`: [ADR 0031](../adr/0031-revise-hfo-source-side-gate-and-method-routing.md)
- `current_method_forward_pointer`: [HFO Q1–Q68 决策总索引](../adr/research_decisions_HFO_Q1_Q68.md) 与 ADR 0039
- `single_verdict`: `REVISE_HARD_GATED_CONDITIONAL_RETAIN`

> **当前阅读边界**：本文是对象前门与 Q1–Q12 的基础审查快照。下文的 SRF 优先级和历史 12-intent G1 仅保留形成史；当前方法、身份角色、13-intent G1 与效用合同以 Q1–Q68 总索引、ADR 0038–0039 和唯一 live plan 为准。

## 1. 结论先行

新审查没有推翻 HFO-NP-v1 作为下一规划对象，也没有否定“side 与 temporal 证据分别决定方法”的总体路线。它推翻或收紧的是四个过强前提：

1. 不能把“来源支持预成丝有限 gap 初态”当成已经闭合的事实；
2. 第一轮 G1 不能同时资格化 SET 与 RESET 两个协议轴；
3. `5×` 数值不确定性只能证明响应超过数值噪声，不能排除普通光滑曲率或驻点；
4. same-network detached target 与固定 latent slots 不能提供独立物理信息，也不能建立唯一可辨的机制解释。

因此当前路线不是“实现 SRPG”，而是：先以零求解 G0 关闭 HFO 来源、初态、波形、边界和许可合同；再以零 PINN 的 G1 判断单一协议轴是否存在不能由光滑局部模型解释的 side-resolved 信息。只有 `SOURCE/OBJECT+` 和 `SIDE+` 后，才讨论物理输出响应场方法；只有未来 strong-raw 另行得到 `TEMPORAL+`，才讨论守恒全局时间坐标。

| 项目 | 最新状态 | 允许的表述 |
|---|---|---|
| HFO-NP-v1 | `CONDITIONAL_RETAIN / SOURCE_CONTRACT_BLOCKED / DERIVED_SYNTHETIC_ONLY` | 唯一规划对象，不是作者 COMSOL 重放或开放 oracle |
| fixed-slot SRPG | `REVISE_MAJOR_NOT_ADMITTED` | 可作受控诊断，不再是默认主方法 |
| TKB 侧向门 | `PROPOSED_G1_GATE_NOT_AUTHORIZED` | 复合资格门，不是已验证机制 |
| side 方法 | `NOT_SELECTED_PENDING_SIDE_PLUS` | SIDE+ 只打开新方法 PLAN；SRF-PINN 是 parking-lot 近邻之一 |
| cKC-NP | `CONDITIONAL_IF_FUTURE_TEMPORAL_PLUS` | 未来 TEMPORAL+ 后的候选，不称 electrothermal clock |
| SRF×cKC 组合 | `NOT_AUTHORIZED` | 仅 SIDE+ 与 TEMPORAL+ 同时成立后才可设计 2×2 |
| 科学主张 | `NO_SCIENTIFIC_METHOD_CLAIMS` | 当前只有设计修订和待执行门 |

## 2. 证据身份与采用边界

### 2.1 已由项目一手审查支持

[2026-08-23 一手来源审查](2026-08-23-srpg-pinn-primary-source-literature-and-collision-review.md)已经核到：2020 HfO₂₋ₓ 工作使用二维轴对称 COMSOL 5.4、Nernst–Planck 氧空位输运、电流连续、稳态 Joule 热、预置 filament 与慢三角波，并报告约 `+0.4 V RESET / -0.57 V SET`；论文没有提供固定开放代码、输入 deck、软件许可或 release。由此可 `VERIFIED` 的只是对象家族和开放资产边界，不是完整可执行合同。

同一审查还确认：当前没有单一来源原生对象同时闭合开放许可、固定实现、动态电—热—内部态、绝对时间和可重放局域事件，故 `OPEN_INDEPENDENT_ORACLE_NO_GO` 保持不变。ADR 0026 允许透明 `derived/synthetic` 重建，但不得把不同来源拼成“作者 replay”。

### 2.2 必须留到 G0 回源的主张

用户提供的对抗性报告是高价值调研输入，但不是一手来源账本；其正文也没有给出足以逐条锁定全部论文、附件、仓库和许可的完整引用表。因此以下内容当前统一为 `UNVERIFIED_PENDING_PRIMARY_SOURCE`：

- 2020 来源初态究竟是贯通连续 CF，还是存在可合法使用的有限-gap reset snapshot/restart；
- filament 的完整浓度、半径、形貌与 gap 区域定义；
- 慢三角波的全部节点、斜率、dwell、周期和绝对时间语义；
- `+1.1 V` 脉冲、`10 ps–10 μs` 及 `18/23 ns` 分支的精确对象和事件含义；
- 全部电导率、热导率、扩散/迁移本构参数及单位；
- 侧向电、热、空位边界，blocking no-flux 的完整域边界；
- 弹性/力学化学势分支是否进入目标合同；
- Supplement、raw data、COMSOL deck、restart 和软件资产的实际可得性与许可；
- 报告中新列 2024–2026 方法工作的精确版本、代码、release 与 license。

这些项可以生成 G0 核查清单，不能直接迁为 `VERIFIED`，也不能用跨材料参数补齐。

### 2.3 本轮可接受的本地分析结论

以下结论来自方程与可构造反例，作为本地分析而非外部论文事实成立：

- 原 `5×` 门只能把信号与离散/测量不确定性分开，无法把阈值 kink 与平滑二次曲率分开；例如驻点附近的光滑二次函数也能产生稳定双侧差异。
- 归一化斜率跳跃本身在驻点也可能看似不随扰动缩小，因此必须与显式 smooth-quadratic null 联合使用。
- same-network response target 即使 stop-gradient，也不增加独立物理信息；固定 slots 还受 latent basis、scale、output-head nullspace 与重参数化影响，不能据低辅助损失宣称物理语义。
- 若目标热方程确为无热容项的准稳态椭圆方程，温度没有独立热松弛状态；未来时间坐标只能针对缺陷输运的时间刚性，不能包装为 electrothermal relaxation clock。
- 局部协议束若逐束独立初始化、完整隔离且不跨器件摊销，仍属于逐案例 PINN；准确名称是“bundle-conditioned case-specific multi-view PINN”，不是全局神经算子。

## 3. 对 ADR 0030 / Q1–Q12 的调整

| 原决策 | 最新处置 | 调整后的合同 |
|---|---|---|
| Q1 快速取得 Go/No-Go | 保留 | 快速指最短判别链，不指最快写代码或首图 |
| Q2 接受守恒缺陷态 | 保留并收紧 | 只称二维电热缺陷态忆阻器，不称结构晶相或铁电相变 |
| Q3 HFO-NP-v1 | 条件保留 | 唯一规划对象；完整来源合同未闭合前不实现 |
| Q4 side/temporal 路由 | 保留并前置来源门 | `SOURCE/OBJECT−` 直接停止；G1 只判 side，temporal 留给 future strong-raw |
| Q5 局部协议束 | 保留隔离接口，撤回 fixed-slot 绑定 | 改称逐束协议条件化多视图 PINN |
| Q6 gap 事件 | 保留，修订顺序 | 连续 CF 分支先 RESET opening 后 SET closing；精确 reset restart 分支才可反向开始 |
| Q7 预成丝有限 gap | 撤回为来源事实 | 初态由 G0 在连续 CF 与精确来源 restart 中二选一；无来源 snapshot 不得自造 gap |
| Q8 完整 history/state | 保留并收紧 | 两周期连续携带内部态，周期间不得重置 |
| Q9 SET/RESET 双轴 | 首轮 G1 撤回 | 只冻结一个轴；连续 CF 选 RESET amplitude，精确 finite-gap restart 才选 SET amplitude |
| Q10 A/A′/ENGINEERING | 保留 | 决定拓扑/时间的缺失物理量不得结果导向校准 |
| Q11 G0/G1 有界预算 | 保留并去除重复 | 当时为 G0 `0 solve / ≤8 sources`、G1 `12 CPU intents / 0 PINN`；ADR 0038 后 G1 为 13 intents，但墙钟、CPU-core-hour 与 0 PINN 上限不变 |
| Q12 `5×` side 门 | 撤回为充分条件 | `5×`只作显著性成分；采用 TKB＋两尺度＋光滑二次零假设＋连续量/硬事件分层 |

ADR 0030 保留为当时已接受的规划快照；[ADR 0031](../adr/0031-revise-hfo-source-side-gate-and-method-routing.md)显式部分覆盖 Q3、Q5–Q7、Q9 和 Q12，避免静默改写历史。

## 4. HFO-NP-v1 的修订对象与事件合同

### 4.1 G0 必须二选一的初态分支

**分支 A：来源连续 CF。** 若主文/Supplement 证实 post-forming 初态为贯通连续 filament，则计分顺序必须是正向 RESET 形成局部 gap，再由反向 SET 闭合 gap。第一轮协议轴只允许 RESET amplitude。

**分支 B：精确 reset snapshot。** 只有在来源给出可识别、可合法使用且字段/单位足够的 reset snapshot/restart 时，才允许从有限 gap 开始，并把第一轮协议轴设为 SET amplitude。

若两者都不能形成来源闭合、可独立重建的初态，裁决 `HFO_INITIAL_STATE_NO_GO`。不得用理想矩形 gap、结果导向 gap 宽度或另一材料的 restart 救援。

### 4.2 协议和周期身份

- 为保持双极 gap 事件目标，首选来源一致的慢双极三角波；
- 单向正压脉冲若只证明 RESET，不得与慢三角波拼成双极周期，也不得用其 ns 时间替代慢波形的绝对时间；
- 第一个周期承担来源一致性检查；连续第二周期是 `derived two-cycle stress test`，不称作者两周期 replay；
- 两周期必须连续传递缺陷场与所有必要内部状态，周期间不得重置；
- 力学化学势只允许选择一个来源闭合分支，不能按事件结果开关。

### 4.3 事件与守卫

- 结构主身份：局部 gap、连续 soft-connectivity、hard connectivity；
- TKB 连续观测：gap 区空位质量、固定截面通量、soft gap thickness/soft-connectivity、terminal current/conductance；
- hard connectivity、onset 和 pass/fail 只作 branch confirmation，不单独生产 TKB；
- 端口 `I(t)`、`G(t)` 和 I–V 回线是独立器件守卫；
- 总空位质量、blocking no-flux、非负性/有界性和离散收敛是资格条件。

## 5. Tangent–Kink/Branch（TKB）复合门

对预冻结协议轴 `a`、连续观测向量 `F(a)` 与扰动 `ε`，定义一侧割线：

\[
g_+(\epsilon)=\frac{F(a+\epsilon)-F(a)}{\epsilon},\qquad
g_-(\epsilon)=\frac{F(a)-F(a-\epsilon)}{\epsilon}.
\]

斜率跳跃的未归一化量为 `Δg(ε)=g+(ε)-g−(ε)`；同时报告基于预冻结协方差/不确定性的显著性 `Z_Δg`。归一化诊断可写为：

\[
J(\epsilon)=
\frac{\|\Delta g(\epsilon)\|_{\Sigma^{-1}}}
{\|g_+(\epsilon)\|_{\Sigma^{-1}}+\|g_-(\epsilon)\|_{\Sigma^{-1}}+\eta}.
\]

在 `ε` 与 `ε/2` 上同时评价，并报告尺度指数：

\[
\alpha_J=\log_2\frac{J(\epsilon)}{J(\epsilon/2)}.
\]

但 `J` 与 `α_J` 不能单独裁决：光滑驻点也可能给出近常数归一化跳跃。必须在 `a±ε` 与 `a±ε/2` 上拟合预声明的光滑二次零假设；只有同时满足以下条件才记 `SIDE+`：

1. 两个扰动尺度的未归一化斜率跳跃均超过数值不确定性门；
2. 响应没有按普通光滑 `O(ε)` 规律坍缩；
3. smooth-quadratic null 被预声明检验拒绝；
4. gap/通量连续量与端口量方向一致；
5. hard event 在中/细离散层落在同一物理分支，且对检测阈值小扰动稳定。

原 `5×` 最细两层综合不确定性保留为第 1 项的候选显著性倍率，不再是独立充分门。若不能拒绝光滑二次零假设，裁决 `NO_SIDE_RESOLVED_INFORMATION`，不得调 `ε`、事件阈值或先训练方法救援。

## 6. 方法理解与最新路由

```text
SOURCE/OBJECT−  → HFO-NP-v1 STOP
SOURCE/OBJECT+
  ├─ SIDE− / TEMPORAL− → STOP
  ├─ SIDE+ / TEMPORAL− → new side-method PLAN; method not selected
  ├─ SIDE− / TEMPORAL+ → cKC-NP candidate
  └─ SIDE+ / TEMPORAL+ → identity / side / clock / side×clock 2×2
```

G1 只能给出 `SOURCE/OBJECT` 与 `SIDE` 的预资格结果，不能判 `TEMPORAL`。`TEMPORAL+` 必须在未来另行授权的 FP64 strong-raw 瓶颈实验中获得；低预算 raw 已到误差地板为 `NO_BOTTLENECK`，高预算 raw 仍不能解析事件为 `RAW_INCOMPETENT_ROUTE_NO_TEST`，两者都不允许 KC 救援。

### 6.1 fixed-slot SRPG 的处置

fixed-slot SRPG 不再是默认主方法。它可以留作 parameterization-specific 诊断，必须带随机正交 basis、scale/head compensation、slot-to-output Jacobian/intervention、pairing-off、shuffle 与 detach 变化等负控；即使有增益，也只能声称某种优化参数化在冻结实现中有效，不能声称 slots 发现了唯一物理方向。

### 6.2 SIDE+ 后可优先审查的 SRF-PINN

`SRF-PINN`（Side-Resolved Physical Response-Field PINN）是 SIDE+ 后的优先审查线索，以可解释的物理输出响应场替代任意 latent slots：基础视图与 `a±ε` 重建视图都直接满足同一来源固定 PDE/BC/IC。它仍只是 parking-lot `HYPOTHESIS`；SIDE+ 不自动选择或授权它，新的方法 PLAN 还须将其与 SA-PINN、direct output secant/Jacobian、gPINN/DC-PINN、相同五视图但 pairing-off、以及 fixed-support strong raw 做可实现性与碰撞比较。

### 6.3 TEMPORAL+ 后的 cKC-NP 候选

`cKC-NP` 只允许全局、空间无关且严格单调的 `τ=τ(t,p)`，令 `s=dτ/dt>0`。守恒式必须保持为：

\[
s\,\partial_\tau c+\nabla\!\cdot J=0,
\]

并保持 no-flux、全域质量与物理时间评价。禁止空间相关时钟静默改变散度通量；禁止把准稳态温度称为独立热动力学时钟。clock 与扩散/迁移率的可辨识性必须另立约束和消融。

### 6.4 不自动启动的候选

GCV-DC-PINN 可留在 future parking lot，但若控制体约束对原守恒残差冗余即停止。PHA-MF、IRAC、采样/界面模块均不作为 `SIDE−/TEMPORAL−` 后的自动 fallback；任何新模块都需新的科学 PLAN 和授权。

## 7. 修订后的 G0–G1 计划

当前仅完成 PLAN，不授权执行。

### G0：来源与对象合同，`0 solve / ≤8 primary sources`

交付一个来源账本，逐项冻结：

- HFO 2020 主文、Supplement、版本、数据与许可身份；
- NP、电流连续、准稳态热和可选力学分支的完整方程、参数、单位和有效域；
- 连续 CF 或精确 reset restart 的初态身份；
- 慢三角波完整节点/时间，或单向脉冲的独立单事件身份；
- 电、热、空位全部边界与接触；
- `A / A′ / ENGINEERING` 分层和禁止跨材料移植项；
- 方法碰撞所需的最小强基线身份，不做无界 novelty 搜索；
- 单一裁决：`HFO_G0_PASS_SOURCE_CONTRACT` 或具体来源 No-Go。

任一决定 gap 拓扑、端口量或绝对时间的输入仍缺失，或必须通过事件结果校准，立即以 `SOURCE_CONTRACT_NO_GO`、`INITIAL_STATE_NO_GO`、`WAVEFORM_TIME_NO_GO` 或 `BOUNDARY_CONSTITUTIVE_NO_GO` 收口。

### G1：零 PINN 的事件与 side 预资格（历史 12-intent 版本；当前 live plan 为 13 intents）

本历史版本为避免重复计算确定性第一周期，将原 2+2+8 结构折叠为以下 12 intents；当前 live plan 另加 thermal-feedback-off 配对，合计 13 intents：

| 块 | intents | 作用 |
|---|---:|---|
| 连续两周期基础案例，coarse/medium/fine | 3 | cycle 1 同时承担来源单周期检查；cycle 2 是 derived stress；建立三层离散趋势 |
| medium 零驱动/闭系统检查 | 1 | 核对漂移、no-flux、质量与非物理事件 |
| 唯一协议轴的 `±ε, ±ε/2`，medium/fine | 8 | TKB、quadratic null、连续量/端口一致性 |
| **合计** | **12** | `0 PINN / ≤48 h wall / ≤64 CPU-core-h` |

如果 G0 选连续 CF，唯一轴为 RESET amplitude；只有 G0 选定精确 finite-gap restart 时才用 SET amplitude。失败后不得切换轴、波形、初态、材料、阈值或力学分支。

对象立即停止条件包括：非负性/有界性失败、blocking BC 或全域质量失败、三层基础事件不收敛、无局部 gap、整域同步变化、第二周期无法连续或事件只在单网格出现。对象事件通过后，TKB 随 `ε` 按光滑规律消失、quadratic null 不能拒绝、gap 与端口方向冲突或 side effect 与数值地板同量级，均裁为 `SIDE−`；它关闭 side 方法，但不把已合格的对象事件改判失败，也不得据此调整扰动、阈值或协议救援。

G1 必须分别记录 `EVENT` 与 `SIDE`：`EVENT+/SIDE+` 可记 `HFO_NP_V1_SIDE_PREQUALIFIED`，`EVENT+/SIDE−` 记 `HFO_NP_V1_EVENT_PREQUALIFIED_SIDE_NEGATIVE`。两者都不是完整 oracle 资格、PINN 支持、TEMPORAL+ 或论文方法结论；只要对象事件合格，未来可另立 strong-raw PLAN 判断 temporal/spatial 瓶颈。方法实现、strong-raw、training、formal、GPU 与 Git 发布始终另批。

## 8. 碰撞与可行性最新理解

既有一手矩阵已确认宽泛碰撞：参数敏感 PINN、PDE 导数正则、stop-gradient 自目标、latent structure、相场强训练、causal/adaptive 与 pseudo-time 均已有直接先例。因此当前不能以“HFO + PINN”“双侧有限差分”“stop-gradient physics target”“fixed slots”或“KC”本身作为创新。

尚可保留的窄研究故事是：在来源闭合、守恒且具有局域 gap 事件的二维缺陷态对象上，先用 TKB 证明一阶敏感度和光滑二次局部模型都不足，再比较实际物理输出响应场与强参数敏感基线；若未来另有独立时间瓶颈，再测试守恒全局动力学坐标及二者交互。这个故事仍为 `NOT_NOVELTY_CLEARED`，formal 前必须刷新同期工作。

## 9. 最新权威状态

```text
phase: HFO_NP_V1_G0_G1_PLAN_REVISED_BLOCKED
blocker: HFO_SOURCE_CONTRACT_NOT_CLOSED
object: PLANNING_OBJECT_SELECTED_SOURCE_BLOCKED_NOT_AUTHORIZED
fixed-slot SRPG: REVISE_MAJOR_NOT_ADMITTED
TKB: PROPOSED_G1_GATE_NOT_AUTHORIZED
side method: NOT_SELECTED_PENDING_SIDE_PLUS
SRF-PINN: PARKED_CANDIDATE_IF_SIDE_PLUS
cKC-NP: CONDITIONAL_IF_FUTURE_TEMPORAL_PLUS
implementation: NOT_AUTHORIZED
claim: NO_SCIENTIFIC_METHOD_CLAIMS
```

本报告更新研究理解、ADR、状态和 live plan，但不运行或授权 source search、solver、oracle、PINN、training、formal、GPU、付费计算、Git 提交/推送，也不自动重启 Q-POP、R1、R2/FerroX 或其他历史对象。
