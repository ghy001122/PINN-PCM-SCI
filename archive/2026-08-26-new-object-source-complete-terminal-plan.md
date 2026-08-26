# Archived plan：新对象来源筛选有界 No-Go 收口

- `phase_id`: `NEW_OBJECT_SOURCE_COMPLETE_BOUNDED_NO_GO`
- `lifecycle_state`: `BLOCKED`
- `blocker_id`: `NEW_OBJECT_SOURCE_MODEL_ALIGNMENT_NO_GO`
- `authorization_state`: `DOCUMENT_AND_NEGATIVE_EVIDENCE_CLOSEOUT_ONLY`
- `plan_status`: `COMPLETED_TERMINAL_NO_GO_AWAITING_USER_ROUTE_DECISION`
- `candidate_status`: `NO_OBJECT_SELECTED`
- `idea_research_status`: `COMPLETED_BOUNDED_NO_GO`
- `object_selection_status`: `NO_OBJECT_SELECTED`
- `method_selection_status`: `NOT_REACHED`
- `source_scan_status`: `COMPLETED_1_FAMILY_3_SOURCES_BOUNDED_NO_GO`
- `compute_authorization`: `ZERO_SOLVE_ZERO_TRAINING_ZERO_GPU`
- `implementation_authorization`: `NOT_AUTHORIZED`
- `formal_or_gpu_authorization`: `NOT_AUTHORIZED`
- `prior_hfo_route_status`: `WAVEFORM_TIME_NO_GO_FROZEN`
- `novelty_status`: `NOT_REACHED`
- `claim_status`: `BOUNDED_SOURCE_CONTRACT_NO_GO_NO_METHOD_EVIDENCE`

## 单一裁决

阶段 1A 已按[来源审查](../docs/references/2026-08-25-new-object-source-complete-review.md)与 [ADR 0040](../docs/adr/0040-select-new-source-complete-object.md)收口为 `NEW_OBJECT_SOURCE_COMPLETE_BOUNDED_NO_GO`。本轮新增核验 3 项一手载体、深审 1 个对象家族；最早决定性失败是 2025 Pd/Ta₂O₅/TaOₓ/Pd 论文与固定作者模型对 vacancy hopping distance `a` 分别给出 `0.32 nm` 与 `0.16 nm`，且该量直接进入扩散与漂移速度。

固定模型没有嵌入全场数值解，固定资产也不能形成互斥完整实体角色；这些是独立次级失败。当前没有来源完整对象，因此 method、strong raw、oracle、pilot、formal OOD 和论文正向路线均未到达。

## 已完成产物

1. [新对象 source-complete 审查](../docs/references/2026-08-25-new-object-source-complete-review.md)：3 项一手来源、1 个深审家族、逐门证据与单一 No-Go；
2. [ADR 0040](../docs/adr/0040-select-new-source-complete-object.md)：接受有界不选择并冻结重启条件；
3. README、CONTEXT、active phase、PROJECT_STATE、docs map、ADR 索引和 archive 索引的终局同步；
4. 文档一致性与差异格式门。

## 当前授权边界

- 允许：核对本次收口文档和现有负证据；
- 不允许：继续填满 20 项来源或 4 个家族预算、换对象、补参、重开历史路线、object build、solver、PINN、training、pilot、formal OOD、GPU、付费计算或 Git 发布；
- 不允许：从“模型文件存在”推断 oracle 资格，从边界完整推断 paper–model alignment，或从本次对象失败推断 TaOₓ、氧化物忆阻器、传统求解器或 PINN 一般失败。

## 重新打开条件

当前没有可自动执行的下一研究动作。只有用户明确批准一份新的 PLAN，并提供实质改变前提的新证据或新研究范围，才可更新实时授权链。重开同一 Ta₂O₅/TaOₓ 家族至少需要能消除 `a=0.32/0.16 nm` 冲突的作者勘误或固定版本说明；仅补回 solution payload、增加案例或更换 PINN 方法不构成重开依据。

## 停止状态

```text
NEW_OBJECT_SOURCE_COMPLETE_BOUNDED_NO_GO
OBJECT_SELECTION_STATUS=NO_OBJECT_SELECTED
METHOD_SELECTION_STATUS=NOT_REACHED
NEXT_RESEARCH_EXECUTION_AUTHORIZED=false
```

该计划由用户于 2026-08-26 批准的授权包 A 和 [ADR 0041](../docs/adr/0041-adopt-one-object-one-bottleneck-goal-and-authorize-package-a.md)覆盖；其 TaOₓ C1 负证据保持有效。
