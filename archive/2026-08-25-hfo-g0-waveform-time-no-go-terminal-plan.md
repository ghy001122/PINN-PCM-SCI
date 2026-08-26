# Archived plan：HFO-NP-v1 G0–G1 来源、来源模型保真、热因果、事件与单轴 side 预资格

- `phase_id`: `HFO_NP_V1_G0_WAVEFORM_TIME_NO_GO`
- `lifecycle_state`: `BLOCKED`
- `blocker_id`: `HFO_WAVEFORM_TIME_CONTRACT_CONTRADICTORY`
- `authorization_state`: `DOCUMENT_AND_NEGATIVE_EVIDENCE_CLOSEOUT_ONLY`
- `plan_status`: `G0_COMPLETED_TERMINAL_NO_GO_AWAITING_USER_ROUTE_DECISION`
- `candidate_status`: `G0_TERMINAL_NO_GO_CURRENT_ROUTE_CLOSED`
- `novelty_status`: `NOT_NOVELTY_CLEARED`
- `source_native_oracle_status`: `OPEN_INDEPENDENT_ORACLE_NO_GO`
- `derived_object_status`: `PLANNING_OBJECT_SELECTED_SOURCE_BLOCKED_NOT_AUTHORIZED`
- `fixed_slot_srpg_status`: `REVISE_MAJOR_NOT_ADMITTED`
- `side_method_status`: `CTH_PINN_SELECTED_AS_CONDITIONAL_FULL_PLAN_DESIGN_TARGET_NOT_ADMITTED`
- `full_plan_method_target`: `CTH_PINN`
- `method_selection_status`: `SELECTED_AS_CONDITIONAL_FULL_PLAN_DESIGN_TARGET_NOT_ADMITTED`
- `tkf_route_verdict`: `SUPERSEDED_BY_CTH_FINITE_BUDGET_HINGE_REFRAMING`
- `cth_route_verdict`: `NOT_REACHED_G0_ROUTE_CLOSED`
- `full_plan_status`: `NOT_ELIGIBLE_CURRENT_ROUTE`
- `full_plan_finalization_gate`: `BLOCKED_BY_WAVEFORM_TIME_NO_GO`
- `protocol_axis_status`: `UNRESOLVED_10X_TIME_CONFLICT`
- `source_model_fidelity_status`: `NOT_ELIGIBLE_AFTER_G0_NO_GO`
- `thermal_causality_status`: `NOT_ELIGIBLE_AFTER_G0_NO_GO`
- `field_kink_status`: `SUPERSEDED_BY_FIELD_HINGE_RELEVANCE_PLUS`
- `field_hinge_status`: `NOT_ELIGIBLE_AFTER_G0_NO_GO`
- `tkf_diagnostic_identity_status`: `SUPERSEDED_BY_CTH_DIAGNOSTIC_IDENTITY_PROTOCOL`
- `cth_diagnostic_identity_status`: `NOT_ELIGIBLE_AFTER_G0_NO_GO`
- `novelty_sufficiency_status`: `REQUIRED_NOT_RUN`
- `canonical_coefficient_admissibility_status`: `NOT_REACHED_G0_ROUTE_CLOSED`
- `mechanics_scope_status`: `UNRESOLVED_INDEPENDENT_G0_GAP_NO_AUTO_EXPANSION`
- `bundle_utility_baseline_status`: `NOT_REACHED_G0_ROUTE_CLOSED`
- `cth_design_contract_status`: `Q59_Q68_ACCEPTED_NOT_IMPLEMENTED`
- `cth_anchor_status`: `SOURCE_A0_UNRESOLVED_10X_TIME_CONFLICT`
- `cth_vector_primitive_status`: `SINGLE_JOINT_TRANSPORT_VECTOR_REQUIRED_NOT_IMPLEMENTED`
- `cth_output_transform_guard_status`: `SHARED_C1_JACOBIAN_ACTION_GUARD_REQUIRED_NOT_RUN`
- `information_status`: `REDUNDANT_BUT_POTENTIALLY_USEFUL_CONDITIONING`
- `ckc_np_status`: `CONDITIONAL_RETAIN_TEMPORAL_GATE_NOT_RUN`
- `source_review_authorized`: `false`
- `source_review_status`: `COMPLETED_WAVEFORM_TIME_NO_GO`
- `cpu_oracle_authorized`: `false`
- `cpu_pinn_development_authorized`: `false`
- `formal_or_gpu_authorized`: `false`
- `next_route_execution_authorized`: `false`
- `claim_status`: `BOUNDED_SOURCE_CONTRACT_NO_GO_NO_METHOD_EVIDENCE`

## 单一目标

G0 已用最短证据链裁决当前 HFO-NP-v1 来源合同：同源十倍绝对时间冲突触发 `WAVEFORM_TIME_NO_GO`，当前 G0→G1 路径关闭。唯一下一目标是让用户在“重新选择来源完整对象”与“接受 literature-inspired synthetic benchmark 并收缩来源保真主张”之间明确决策；决策前不启动新的来源扫描、对象、求解或方法工作。

当前 Q1–Q68 的单一决策路由见 [HFO Q1–Q68 决策总索引](../docs/adr/research_decisions_HFO_Q1_Q68.md)。对象与前门裁决见 [HFO-NP-v1 对抗性审查整合](../docs/references/2026-08-24-hfo-np-v1-srpg-kc-adversarial-integration.md) 与 [ADR 0031](../docs/adr/0031-revise-hfo-source-side-gate-and-method-routing.md)；Q30–Q53 的训练、公平、主张、pilot 与碰撞合同由 [ADR 0032–0035](../docs/adr/README.md)逐层冻结；ADR 0036/0037 保留 TKF 形成史和仍有效的 waveform/fidelity/smooth-control 前门；[Q59–Q63](../docs/notes/2026-08-25-hfo-q59-q63-hinge-causality-admissibility-and-utility-integration.md)/[ADR 0038](../docs/adr/0038-reframe-tkf-as-cth-and-require-thermal-causality-admissibility-and-utility.md)将方法重构为 CTH；[Q64–Q68](../docs/notes/2026-08-25-hfo-q64-q68-cth-identity-anchor-transform-and-pareto-integration.md)/[ADR 0039](../docs/adr/0039-separate-cth-identity-evidence-and-freeze-anchor-vector-transform-and-utility.md)进一步冻结角色分离 identity、来源锚点、联合向量原语、公共输出变换和双轴 Pareto。所有这些文件都不是第二份 live plan，也不授权任何 future stage。

## 授权包 A：G0 来源与对象合同

### 当前授权

`CONSUMED_WAVEFORM_TIME_NO_GO_2026-08-25`。用户本轮批准的 G0 已完成并触发预声明停止条件；该授权不延伸到 G1、另一对象、synthetic benchmark、solver、代码实现或训练。

### 范围与预算

- 最多 8 项一手来源；
- `0 solve / 0 training / 0 GPU`；
- 只核对 HFO 目标来源、必要模型谱系和最危险方法近邻，不做无界 novelty 搜索；
- 唯一交付为一份 G0 来源/对象合同报告与单一 verdict。

### 必须冻结

1. HFO 2020 主文、Supplement、版本、数据可得性、论文许可与软件/输入资产许可分别记账；
2. Nernst–Planck 通量、电流连续、准稳态 Joule 热、`T ->` vacancy transport 反馈及可选力学化学势的完整方程、参数、单位和有效域；
3. 电、热、空位全部边界与接触，尤其侧向边界和 blocking no-flux；
4. 初态只允许二选一：来源连续 CF，或精确、可识别且可合法使用的 finite-gap reset snapshot/restart；
5. 慢双极三角波的全部节点、速率、dwell、极性与绝对时间；单向 ns 脉冲若只支持 RESET，必须与双极协议隔离；
6. 唯一 `SOURCE_ANCHORED_DERIVED_WAVEFORM_SCALE_AXIS`：以来源波形为 `a0`，连续 CF 只缩放固定时长 RESET 段，exact restart 才可缩放固定时长 SET 段；事件段之外的波形、转折点和 physical time 不变。G0 必须核验这种 A′ 家族是否物理可容许，不得称纯 amplitude、纯 ramp-rate 或 source-native axis；
7. 来源模型保真变量与不确定性：可数字化端口轨迹、至少两个跨事件空位空间状态、固定 ROI/gap/耗尽区/contour，以及数字化、状态定位、离散、求解与 detector 联合不确定性；
8. `A / A′ / ENGINEERING` 分层：决定 gap 拓扑、端口或绝对时间的量不得由 `A′`/`ENGINEERING` 补造或按结果拟合；
9. 完整案例、连续 history、来源单周期与 derived two-cycle stress 的身份；
10. TKB 所需连续观测、唯一派生波形缩放轴、两级扰动与 smooth-quadratic null 的定义，不冻结训练方法。
11. 力学化学势对来源模型保真和目标事件是否必要；必要时当前三物理块路线停止，不在同一计划内增加第四块。

### G0 停止条件

任一情况立即收口，不进入 G1：

- 决定 gap 拓扑或绝对时间的本构、初态、边界或波形仍缺失；
- finite-gap 初态只能靠人工构造，且连续 CF 分支又不能闭合目标事件；
- 必须混用慢三角波与单向 ns 脉冲的时间语义；
- 必须跨 TaOₓ、VO₂、Sevic、R1/R2 或其他材料移植关键物理参数；
- 必须按事件结果校准 mobility、gap、边界、波形、力学分支或阈值；
- 来源图表/数据不足以预冻结端口轨迹与至少两个跨事件空位空间状态，或来源锚定 fixed-duration waveform-scale A′ 不可容许而论文又依赖该轴；
- 来源/数据/许可身份不足以支持透明独立重建。
- 来源保真或目标事件必须依赖力学化学势，因而当前三块 HFO 对象不成立；
- 来源合同不存在可审计的 `T ->` vacancy transport 反馈，因而“电热缺陷态”因果链不闭合。

单一通过状态为 `HFO_G0_PASS_SOURCE_CONTRACT`；失败按最早原因记 `SOURCE_CONTRACT_NO_GO`、`INITIAL_STATE_NO_GO`、`WAVEFORM_TIME_NO_GO`、`BOUNDARY_CONSTITUTIVE_NO_GO` 或 `LICENSE_ASSET_NO_REPLAY`。软件 deck 缺失只关闭作者 replay；若物理合同完整，仍可计划 clean-room 派生实现。

## 授权包 B：G1 事件与 side 预资格

### 当前授权

`NOT_AUTHORIZED`。只有 G0 通过并由用户再次明确批准 G1 后才可执行。G1 允许的将是独立 CPU solver 预资格，仍为 `0 PINN / 0 training`。

### 进入前冻结

- 一个初态分支、一个慢双极波形和一个已由 G0 证明不需力学救援的三物理块合同；
- 一个 `SOURCE_ANCHORED_DERIVED_WAVEFORM_SCALE_AXIS`：连续 CF 选固定时长 RESET 段 scale，精确 finite-gap restart 才选固定时长 SET 段 scale；
- `a0`、`ε=rho*a0`、`rho` 与 `rho/2` 的数值、双侧 admissible envelope 和 no-clipping；`rho/4` 只登记为未来身份诊断尺度，不生成当前 G1 view；
- coarse/medium/fine 的空间—时间联合离散；
- total vacancy mass、no-flux、非负性、gap/soft-connectivity、固定截面通量、端口量和 hard connectivity evaluator；
- 来源对齐端口轨迹、跨事件空位空间状态、固定 ROI/contour、cycle persistence、端态漂移、联合误差包络和 detector robustness；
- thermal-feedback-off 的唯一消融定义：继续求解同一电学与准稳态热学，只在 transport 本构中把温度依赖冻结到预声明参考温度；
- 所有 intents 顺序门控，基础对象失败前不得启动 side 块。

### 预算分配

| 顺序 | 块 | intents | 目的 |
|---:|---|---:|---|
| 1 | 连续两周期基础案例 coarse/medium/fine | 3 | cycle 1 同时作来源单周期端口＋空间保真检查；cycle 2 作 derived stress；建立三层离散趋势 |
| 2 | medium 零驱动/闭系统 | 1 | 核对无伪事件、no-flux、质量与数值漂移 |
| 3 | medium thermal-feedback-off 配对消融 | 1 | 隔离 `T -> transport` 对 gap、连续空位量与端口的因果作用 |
| 4 | 唯一 waveform-scale 轴 `+ε,-ε,+ε/2,-ε/2` × medium/fine | 8 | TKB、quadratic null、连续量/端口方向与中细分支一致性 |
|  | **合计** | **13** | `≤48 h wall / ≤64 CPU-core-h / 0 PINN` |

### 来源模型保真通过合同

基础案例的 cycle 1 必须同时满足：

1. 来源支持的 I–V/G–V 完整区段或离散点、事件极性和阈值区间在联合不确定性内一致；
2. 至少两个与冻结初态分支相容、跨越同一来源支持事件的空位空间状态通过预冻结 ROI、gap 位置、耗尽面积、最小 gap 厚度和 vacancy contour；连续 CF 分支最低为 gap 形成前与 RESET gap 形成后，exact restart 分支则必须含精确来源 snapshot 及其下一来源状态；来源若还给出 SET 后状态则同时检查；
3. 端口与空间变量全部通过，`T/phi` 只作辅助守卫，不采用加权总分掩盖任一失败；
4. 不校准决定 gap 拓扑或绝对时间的物理参数；只允许与结果无关、通过三层趋势审查的 `ENGINEERING` 数值设置。

任一项失败记 `HFO_SOURCE_MODEL_FIDELITY_NO_GO`，当前来源对齐 HFO 方法论文路线停止。对象可降为 `LITERATURE_INSPIRED_SYNTHETIC_BENCHMARK_UNVALIDATED` 作为内部资产，但不自动转为 benchmark/resource paper，也不进入 CTH 方法投票。

### 热反馈因果通过合同

基础 medium 与 thermal-feedback-off medium 必须在相同离散、容差、初态、波形和输出时刻下配对。至少一个预冻结的连续 gap/空位量或端口事件指标变化须高于 medium/fine 综合数值不确定性，并且方向与来源的 `T -> transport` 本构一致；仅温度场不同或 hard detector 翻转不构成通过。效应不显著记 `HFO_THERMAL_CAUSALITY_NO_GO`，关闭当前电热 HFO 方法论文路线；预算内不能裁决记 `INCONCLUSIVE_BUDGET_EXHAUSTED`，不增加 intent、墙钟或 core-hour。

### TKB 通过合同

`SIDE+` 必须同时满足：

1. 两个扰动尺度的未归一化一侧斜率跳跃均超过预冻结数值不确定性门；原 `5×` 只作为候选显著性倍率；
2. 响应不按普通光滑 `O(ε)` 规律坍缩；
3. 在 `±ε, ±ε/2` 上的 smooth-quadratic null 被拒绝；
4. gap 区空位质量、固定截面通量/soft-connectivity 与 terminal current/conductance 方向一致；
5. hard connectivity 只确认同一物理 branch，且中/细网格与 detector 小扰动下稳定。

### G1 对象停止条件与 side 裁决

- 非负性/有界性失败、blocking BC 或全域质量守恒失败；
- 基础事件在三层联合离散上不收敛、无局部 gap、整域同步变化或只在单一网格存在；
- 来源对齐端口轨迹与跨事件空位空间状态不能同时通过联合不确定性；
- thermal-feedback-off 与全耦合对象在连续事件/端口指标上不可辨，或其方向违背冻结本构；
- 第二周期不能连续运行、必须重置内部态，或 cycle drift 超过预冻结容限；
- 基础两周期慢三角波超出冻结预算。

这些情况关闭对象路线；最后一种记 `INCONCLUSIVE_BUDGET_EXHAUSTED` 或环境 `BLOCKED`。不得换 ns pulse、缩放物理时间、切换协议轴、追加阈值或调参救援。

基础对象获得 `EVENT+` 后，TKB 只产生以下互斥 side 结果：

- 全部 TKB 条件满足：`HFO_NP_V1_SIDE_PREQUALIFIED`；
- 响应按光滑规律消失、smooth-quadratic null 不能拒绝、连续量/端口不一致或 side effect 不高于数值不确定性：`HFO_NP_V1_EVENT_PREQUALIFIED_SIDE_NEGATIVE`；它关闭 side 方法，但不把对象事件改判失败；
- side 块在冻结预算内没有可裁决结果：`HFO_NP_V1_EVENT_PREQUALIFIED_SIDE_INCONCLUSIVE`；不调整 `ε`、阈值或协议救援，后续是否只做 temporal 诊断须另行决定。

任何 G1 正面对象结果都不记 `ORACLE_QUALIFIED`、`SRPG_SUPPORTED`、`SRF_SUPPORTED`、`TEMPORAL+` 或论文方法结论。

## G1 后的证据路由

```text
SOURCE/OBJECT− or SOURCE_MODEL_FIDELITY− or THERMAL_CAUSALITY− → STOP
SOURCE/OBJECT+ and SOURCE_MODEL_FIDELITY+ and THERMAL_CAUSALITY+ but EVENT− → STOP
SOURCE/OBJECT+ and SOURCE_MODEL_FIDELITY+ and THERMAL_CAUSALITY+ and EVENT+ → 记录 SIDE+/SIDE−；可另行请求 development-oracle 与 strong-raw 诊断 PLAN
  ├─ SIDE− / TEMPORAL− → 方法路线 STOP
  ├─ SIDE+ / TEMPORAL− → 仅保留 CTH 条件靶标；raw/transport/field-hinge/identity/utility/novelty 前门通过后才可定稿 FULL_PLAN
  ├─ SIDE− / TEMPORAL+ → 才可另审 cKC-NP
  └─ SIDE+ / TEMPORAL+ → CTH 与 cKC 两腿先独立通过，才可另审 side×clock 2×2
```

`TEMPORAL` 只能由未来另批的 strong-raw 建立，不能由 G1 的 TKB 或传统求解器轨迹推断。fixed-slot SRPG 保持 `REVISE_MAJOR_NOT_ADMITTED`；历史 TKF-CANON 已由 ADR 0038 重构为 CTH-PINN，后者只是 future FULL_PLAN 的条件式设计靶标，不是本计划的执行对象。未来 strong-raw 与 temporal/spatial diagnosis 通过后，还须用训练外单一事件时间平移排除纯 time-shift，并在 `ε, ε/2, ε/4` 的连续 `c_v/J_v` 上建立 `FIELD_HINGE_RELEVANCE_PLUS`；该门只支持有限尺度 hinge relevance，不证明真实物理解映射不可微。

只有 `FIELD_HINGE_RELEVANCE_PLUS` 在 qualification complete cases 成立，才可冻结 CTH、smooth4、`h=0`、中心/镜像错结点、公共 base、`C1` 输出变换、配置和判据，并另行形成、审查与授权 `CTH_DIAGNOSTIC_IDENTITY_PROTOCOL`。identity 必须改用互斥的 identity-development complete cases；每个案例只训练五个视图，`δ=±1/4` 在所有选择完成后一次打开且不得回流。案例角色不足记 `IDENTITY_EVIDENCE_ROLE_INSUFFICIENT`。hinge 结点永久固定来源 `a0`，错位记 `CTH_ANCHOR_MISMATCH_NO_GO`；不得重定中心或学习 knot。唯一原语是同一联合网络产生的向量 `h=(h_c,h_J)`，所有臂共享来源兼容、无 side/hinge 旁路的 `B`；事件 ROI 中 `D_qB(q0)h` 若被饱和或 nullspace 吸收，记 `CTH_TRANSFORM_NULLSPACE_INVALID`。身份 PASS 只把方法改为 `ELIGIBLE_FOR_FULL_PLAN_FINALIZATION_NOT_PILOT_AUTHORIZED`。

随后协议束效用按双轴 Pareto 裁决：五个已见协议与 aggregate-compute-matched `IND-5` 比较事件保真和总训练成本；盲 microviews 与零重训的 parameter-conditioned raw 和 smooth4 比较；`IND-7` 只报告独立方法补算两个新协议的增量成本。CTH 若在 seen protocols 被 `IND-5` 严格支配且 blind microviews 无增量，记 `CTH_BUNDLE_UTILITY_NO_GO`。通过后仍须 bounded primary-source `NOVELTY_SUFFICIENCY_GATE`。任一门失败分别记 `CTH_FIELD_RELEVANCE_NO_GO`、`METHOD_VETO_IDENTITY_FAILED`、`CTH_BUNDLE_UTILITY_NO_GO` 或 `METHOD_VETO_NOVELTY_INSUFFICIENT` 并关闭当前方法论文，不自动切换方法或论文类型。

因此当前证据顺序为 `SOURCE_CONTRACT → SOURCE_MODEL_FIDELITY → THERMAL_CAUSALITY → EVENT → SIDE → RAW_COMPETENCE → TEMPORAL/SPATIAL_DIAGNOSIS → FIELD_HINGE_RELEVANCE_PLUS → ROLE_SEPARATED_CTH_DIAGNOSTIC_IDENTITY → DUAL_AXIS_BUNDLE_UTILITY → NOVELTY_SUFFICIENCY → FULL_PLAN 可提交用户审查`。即使全部通过，pilot 仍须新的明确授权。`δ=±1/4`、错结点控制、identity-development cases、`IND-5/IND-7` 与 novelty refresh 不能占用或改写当前五视图、13-intent G1。SRF-PINN、GCV-DC-PINN、cKC-NP、PHA、IRAC、采样/界面模块仍为 parking lot，`SPATIAL+` 不自动启动新模块。

## 当前下一动作

G0 已以 [来源与对象合同报告](../docs/references/2026-08-25-hfo-g0-source-and-object-contract-review.md)中的 `WAVEFORM_TIME_NO_GO` 收口。当前只等待一个最小用户决策：

1. 授权重新筛选一个来源完整的二维电—热—内部态对象；或
2. 明确接受 literature-inspired synthetic benchmark，并同步撤回作者模型复现/来源模型保真主张，只保留透明派生对象上的方法证据目标。

任一选择都属于新的科学合同，须先形成有界 PLAN；当前不自动启动来源扫描、对象实现、solver、PINN、训练、formal OOD、GPU 或付费计算。

旧 SRPG 等待计划已归档为 [`archive/2026-08-24-srpg-preimplementation-review-terminal-plan.md`](2026-08-24-srpg-preimplementation-review-terminal-plan.md)。R1、R2/FerroX、Q-POP、TAPF、ETPF 与 EAF 的历史 No-Go 和授权消耗均不变。
