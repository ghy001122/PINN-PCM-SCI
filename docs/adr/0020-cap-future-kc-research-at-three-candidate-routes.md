# 0020：未来 KC 正向研究最多消耗三条候选路线

- `status`: `SUPERSEDED`
- `accepted_at`: `2026-08-21`
- `superseded_at`: `2026-08-22`
- `superseded_by`: `ADR_0027`
- `decision_scope`: `FUTURE_KC_ROUTE_BUDGET_AND_STOP`
- `claim_status`: `PROPOSED_METHOD_NO_NUMERICAL_EVIDENCE`

本 ADR 保留 2026-08-21 当时接受的计数决定及其理由，但不再约束后续研究。用户于 2026-08-22 明确撤销固定次数上限；当前决定见 [ADR 0027](0027-remove-the-fixed-count-cap-on-future-research-routes.md)。

一条“候选研究路线”由一个来源闭合的二维物理对象，以及针对该对象冻结的“来源资格化 → 强 raw → 方法 pilot”分阶段证据链共同定义。文献与来源筛选不计数；对象通过准入、经用户批准并启动首次科学运行时消耗一个路线槽位。忠实于既定合同的实现修复或方法外执行损坏的原样重放不另计路线，但在已有科学结果后更换物理对象、几何、接触、动力学、substrate，或启用未预登记的网络/训练协议，均视为下一条路线，不能以重命名同一对象重置计数。

三路线预算从 ADR 0019 之后开始，历史 R3、R4、TAPF、ETPF 与 EAF 不占新预算，但继续作为排除重复失败类型的证据。未来最多消耗三条路线；若第三条路线收口时仍未形成支持正向 KC 方法论文的突破，则在第四条路线开始前放弃该 idea、另寻 idea。本 ADR 只冻结计数与止损语义，不选择对象，也不授权检索、实现或运行。
