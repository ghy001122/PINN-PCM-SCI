# 0027：撤销未来研究路线的固定次数上限

- `status`: `ACCEPTED`
- `accepted_at`: `2026-08-22`
- `decision_scope`: `GLOBAL_FUTURE_RESEARCH_ROUTE_COUNT_CAP`
- `claim_status`: `NO_SCIENTIFIC_CLAIMS`
- `user_basis`: `USER_REVOKED_THREE_FORMAL_STUDIES_CONSTRAINT_2026-08-22`
- `supersedes`: `ADR_0020_AND_ROUTE_SLOT_COUNTING_SEMANTICS`

用户在接受论文目标、派生对象身份、创新底线和 48 小时裁决语义后，明确撤销“后续最多三次正式研究”的约束。后续研究路线不再共享固定的全局次数预算，现行状态与计划不得再用 `0/3`、剩余槽位或“第三次失败后必须放弃 idea”决定研究去留。

取消全局次数上限不等于允许无界搜索或救援式重复。每条拟启动路线仍须单独遵循 `PLAN → 用户批准 → EXECUTE`，并在执行前冻结论文去向、物理对象、强基线、关键消融、完整 case/formal OOD、实际计算预算和该路线自己的证据停止条件。当前路线达到预声明通过、失败或阻塞条件后必须收口；提出下一条路线时，须说明新前提、新接口或新证据价值，不能靠改名、移动阈值、读取 formal 结果后换协议或重复同类失败来延长旧路线。

ADR 0020 因此整体转为历史记录。ADR 0023/0025 及其他文档中凡以“消耗路线槽位”表达全局计数或剩余额度的语义均被本 ADR 覆盖；其中事件资格、strong-raw 准入、独立 formal claim、公平预算和路线内停止门继续有效。既有实验、扫描和归档材料可以保留当时的计数背景，但该背景不再产生当前或未来授权约束。

本 ADR 只修改治理与计划语义，不授权 solver、代码、训练、formal、GPU、付费计算或任何科学执行。
