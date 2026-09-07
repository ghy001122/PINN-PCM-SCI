# 当前阶段

- `phase_id`: `PHK_V23_LF6_EVENT_FRONTIER_RANK_BAND_AND_SAFETY_GATED_PHYSICS_PILOT_EXECUTE`
- `phase_name`: PHK-V2.3 LF6 cycle-resolved event-frontier rank-band alignment and safety-gated physics pilot
- `lifecycle_state`: `COMPLETE`
- `blocker_id`: `NONE`
- `machine_outcome`: `LF6_P0_PRESERVATION_FAILED`
- `mechanism_outcome`: `NO_RANK_SPECIFIC_INCREMENT`
- `claim_status`: `SAFETY_CARRIER_ENTERED_P0_BUT_PHYSICS_PRESERVATION_FAILED_NO_PINN_PARETO`
- `next_research_execution_authorized`: `false`
- `authorization_scope`: `NONE_TERMINAL`
- `candidate_status`: `NONE`
- `reference_status`: `FINE_EXTRA_LF_ONLY_FROZEN_EVALUATOR_READ_LOCAL_POST_SHUTDOWN_STRESS_SEALED_UNREAD`
- `compute_status`: `DEV_U_400_DEV_R_400_P0_1200_RECOVERED_HASH_VERIFIED_SHUTDOWN`
- `next_recommendation`: `PHYSICS_FORGETTING_RESULT_NO_RESCUE`
- `effective_date`: `2026-09-07`

PHASE_ID=PHK_V23_LF6_EVENT_FRONTIER_RANK_BAND_AND_SAFETY_GATED_PHYSICS_PILOT_EXECUTE
BLOCKER_ID=NONE
NEXT_RESEARCH_EXECUTION_AUTHORIZED=false

## 当前证据

DEV-U 与 DEV-R 各完成 400 个 matched phase-only updates。DEV-R 通过 safety
但仅因 cycle-1 timing 未通过 strict；DEV-U 也未通过 strict，故机制结论为
`NO_RANK_SPECIFIC_INCREMENT`。冻结选择规则仍合法选择 DEV-R 进入 P0。

P0 完成 1200 个无标签纯物理 updates，fixed-blind physics objective ratio 为
`0.0128142`，但 potential/temperature/phase/topology 相对 DEV-R 恶化
`28.62/52.60/25.84/20.03` 倍，并失去事件与恢复。因此终局为
`LF6_P0_PRESERVATION_FAILED`，不是 PINN Pareto 或 candidate。

## 边界

首个 P0 启动的 checkpoint identity 异常发生在 P0 optimizer 构造前；最小修复后
只执行 P0-only continuation，未重训 DEV-U/R，科学身份未变。全部产物已回收并
核验，进程/GPU 清零后实例关机，TCP 关闭且 SSH `Connection refused`。本地
fine/extra/direct LF_ONLY/frozen evaluation 仅在关机后运行。stress 保持
`TWO_STRESS_REFERENCES_SEALED_UNREAD`。任何后续科研均须新 PLAN 与 EXECUTE。
