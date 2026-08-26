# 0044：采纳 GOAL-PAPER-ONE-SHOT-V1 一次性本地研究执行授权

- `status`: `ACCEPTED`
- `accepted_at`: `2026-08-26`
- `decision_scope`: `ONE_SHOT_LOCAL_RESEARCH_EXECUTION_TO_COMPLETE_MANUSCRIPT`
- `supersedes`: `ADR_0043_PLANNING_AND_SEPARATE_PACKAGE_AUTHORIZATION_SEMANTICS`
- `preserves`: `ADR_0042_AND_ALL_HISTORICAL_NO_GO_AND_NEGATIVE_EVIDENCE`
- `claim_status`: `BOUNDED_SOURCE_PORTFOLIO_NO_GO_NO_METHOD_EVIDENCE`

## 背景

当前真实状态仍是 Package A 的组合级来源 No-Go：没有对象锁定，也没有 oracle、event、strong raw、CTH、development 或 formal 证据。ADR 0043 随后提出模块化主锚点路线，但保持 `PROPOSED` 并要求 CPU、GPU、formal 与写作逐包批准。

用户现明确批准 `GOAL-PAPER-ONE-SHOT-V1`，并逐项授权有界来源研究、合法 COMSOL 审计、项目内实现、CPU oracle、本地 GPU development、sealed formal、图表统计及本地论文/补充材料写作；同时明确禁止付费计算、凭据披露、作者联系、投稿、外部上传和 Git 远程操作。用户还规定分支 No-Go 不等于总目标完成，必须按预注册切换表继续，直到完整稿件包交付。

## 决定

1. 采纳 [GOAL-PAPER-ONE-SHOT-V1](../plans/NEXT_ACTIONS.md) 为唯一 live plan，旧 `PLAN-MSA-01` 原文移入归档，不追溯改写。
2. 本次用户指令构成 S0–S6 及本地稿件的一次性执行授权；门通过后不再逐包或 formal 前申请批准。
3. 先完成 S0 冻结并通过文档一致性门，再开始新的来源检索、求解或训练。
4. 路线按 `COMSOL64-first → 预冻结 source-only fallback → SYN_EDT_2D_V1` 执行；对象一旦通过来源合同，不得因方法结果换对象。来源对象在 oracle/event 失败时只关闭该来源分支并转预冻结 synthetic route。
5. CTH 仍是条件式方法：必须先有合格 object/oracle/event、strong raw competence、transport-only 有限预算瓶颈、非神经响应和 novelty 前门。失败时保留对象并转与真实证据一致的 comparative/benchmark 稿。
6. 总预算固定为 12 个新增一手载体、COMSOL64 加 1 个 fallback、40 个 CPU solver intents、256 CPU core-hours、96 development GPU-hours、128 formal GPU-hours；失败运行计入预算，formal reserve 不借给 development。
7. 只有完整论文、实际结果、最终图表/主表、参考文献、补充材料、复现包和主张边界自检全部交付后，目标才完成。

## 被拒绝的替代方案

1. **继续沿用逐包批准。** 与用户本轮明确的一次性授权冲突，会把已作出的决定重新变成审批阻塞。
2. **把首个对象或方法 No-Go 当作总任务完成。** 不满足用户要求，也不能形成完整科学稿件。
3. **为保证阳性而放宽门或救援。** 会破坏对象盲选、formal 封存、计算公平和负结果完整性。
4. **重开 HFO-NP-v1、TaOₓ C1 或 Package A。** 会覆盖已冻结的来源冲突和有界 No-Go；本 GOAL 明确保留这些终点。

## 后果

- `active_phase.md` 进入 `GOAL_PAPER_ONE_SHOT_V1_S0 / ACTIVE`；授权事实不改变当前科学 claim 状态。
- ADR 0043 的模块化来源思想和强控制可作为可移植设计输入，但其 `PROPOSED_NOT_AUTHORIZED`、逐包批准与无自动 fallback 语义被本决定覆盖。
- 普通科学失败不触发用户暂停；只有用户专属凭据/许可、机器安全边界、工作区外破坏性动作、付费支出或法律伦理冲突可以暂停。
- Git 远程、外部发布、投稿及任何付费资源仍需另行明确授权。
