# 0039：分离 CTH 身份证据并冻结锚点、向量原语、输出变换与效用裁决

- `status`: `ACCEPTED`
- `accepted_at`: `2026-08-25`
- `decision_scope`: `HFO_CTH_IDENTITY_ROLE_ANCHOR_VECTOR_TRANSFORM_AND_UTILITY`
- `amends`: `ADR_0033, ADR_0035, ADR_0036, ADR_0037, ADR_0038`
- `supersedes_in_part`: `CTH_IDENTITY_USES_QUALIFICATION_CASES_AND_SINGLE_UTILITY_KILL`
- `claim_status`: `PLANNING_DECISION_NO_NEW_SCIENTIFIC_EVIDENCE`

用户接受 grill-with-docs Q64–Q68 的全部推荐。`FIELD_HINGE_RELEVANCE_PLUS` 与 `CTH_DIAGNOSTIC_IDENTITY_PROTOCOL` 不得复用同一完整案例证据：前者只使用 qualification cases 选择是否保留 CTH 假设；架构、公共 base、controls、阈值与配置冻结后，后者必须在互斥的 identity-development complete cases 上训练五个视图并一次打开盲 `delta=+/-1/4` microviews。若案例角色或预算不足以保持这种分离，不得作身份裁决。

canonical hinge 结点永久固定在 G0 来源锚点 `a0`。若资格证据表明有限尺度尖锐响应的中心明显偏离该锚点，记 `CTH_ANCHOR_MISMATCH_NO_GO`；不得依据 oracle 重定中心、学习 knot、增加第二 hinge 或改写协议轴。

唯一可训练原语冻结为一个联合 transport vector coefficient `h=(h_c,h_J)`。其分量由同一联合系数网络、同一容量和同一损失权重产生，不得拆成候选专属 heads、分别调参或赋予唯一物理场语义；smooth4 必须匹配向量维度、系数场容量与实际计算。科学评价只读取经共同输出变换重建的物理 `c_v` 与 `J_v` 及其事件/守卫。

CTH、smooth4、参数条件化 raw 与公平控制必须共用事前冻结、来源兼容且不显含协议 side/hinge 的 `C1` 输出变换 `B`。identity protocol 还须在训练外审查事件 ROI 中的 Jacobian 作用量；若非零系数主要落入 `D_qB(q0)` 的饱和、退化或不可观测方向，记 `CTH_TRANSFORM_NULLSPACE_INVALID`，不得用 coefficient 热图支撑机制，也不得看结果后更换 `B`。

协议束效用采用不可压成单分数的双轴 Pareto。五个已见协议上，CTH 与 aggregate-compute-matched 的独立逐协议 `IND-5` 比较事件保真和总训练成本；盲 microviews 上，CTH 与零重训的 parameter-conditioned strong raw 和 smooth4 比较；`IND-7` 只估计独立方法补算两个新协议的增量成本。若 CTH 在已见协议被 `IND-5` 严格支配，且盲 microviews 又不优于强平滑参数化模型，记 `CTH_BUNDLE_UTILITY_NO_GO`。

这些决定只完成 future FULL_PLAN 的设计收紧。CTH 仍为 `SELECTED_AS_CONDITIONAL_FULL_PLAN_DESIGN_TARGET_NOT_ADMITTED / REVISE_BEFORE_FULL_PLAN_FINALIZATION / NOT_AUTHORIZED / NOT_NOVELTY_CLEARED`；G0、G1、solver、PINN、training、formal、GPU、付费计算和 Git 发布均未获授权。
