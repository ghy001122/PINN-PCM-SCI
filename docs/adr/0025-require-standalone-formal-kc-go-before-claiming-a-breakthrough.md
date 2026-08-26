# 0025：只有 standalone formal KC_GO 才算路线突破

- `status`: `ACCEPTED`
- `accepted_at`: `2026-08-22`
- `superseded_in_part_by`: `ADR_0027`
- `decision_scope`: `FUTURE_ROUTE_BREAKTHROUGH_FAIRNESS_AND_MODULE_SEQUENCE`
- `claim_status`: `PROPOSED_METHOD_NO_NUMERICAL_EVIDENCE`

ADR 0027 已撤销本 ADR 中“路线槽位消耗”的计数语义；未触碰 formal 池、`KC_GO` 归因门和实际计算公平要求继续有效。

只有独立 KC 在未触碰 formal 池上获得 `KC_GO` 才算路线突破；事件门、raw 门、正向 pilot 或组合开发通过都只是准入。路线槽位消耗后，以 `NO_BOTTLENECK`、`RAW_INCOMPETENT_ROUTE_NO_TEST`、`INCONCLUSIVE_BUDGET_EXHAUSTED` 或科学 No-Go 收口均不算突破；KC 独立失败时，组合不能改写处置。

raw、KC、第二模块与组合必须使用相同完整案例、seed、基础网络族和调参机会，以包含 KC 额外导数/时钟开销的实际计算预算为主要公平轴，同时报告参数量、更新数和墙钟时间。第二模块只能在 KC 已于开发池独立通过、且未读取 formal 结果便验证出不同剩余瓶颈后开发；它也必须独立通过开发门。锁定后四者共同进入同一未触碰 formal 池，KC 或第二模块任一未通过自身门，组合即失去论文主方法资格。本 ADR 不冻结具体预算或模块，也不授权执行。
