# 当前阶段

- `phase_id`: `PHK_V23_LF7_COMPETENCE_FILTERED_BLOCKWISE_BACKTRACKING_PHYSICS_REFINEMENT_PILOT_EXECUTE`
- `phase_name`: PHK-V2.3 LF7 competence-filtered blockwise backtracking physics refinement pilot
- `lifecycle_state`: `COMPLETE`
- `blocker_id`: `NONE`
- `machine_outcome`: `LF7_MATCHED_SCREEN_INCOMPLETE_IDENTITY_INVALID`
- `mechanism_outcome`: `MATCHED_SCREEN_INCOMPLETE_IDENTITY_INVALID`
- `claim_status`: `VALID_SMALL_STEP_NEGATIVE_ARM_FILTER_ARM_IDENTITY_INVALID_NO_MECHANISM_ATTRIBUTION`
- `next_research_execution_authorized`: `false`
- `authorization_scope`: `NONE_TERMINAL`
- `candidate_status`: `NONE`
- `reference_status`: `LOCAL_NOMINAL_ADJUDICATED_STRESS_SEALED`
- `compute_status`: `GPU_COMPLETE_ARTIFACTS_RECOVERED_INSTANCE_SHUTDOWN`
- `next_recommendation`: `RETAIN_VALID_ARM_NO_MECHANISM_ATTRIBUTION`
- `effective_date`: `2026-09-08`

PHASE_ID=PHK_V23_LF7_COMPETENCE_FILTERED_BLOCKWISE_BACKTRACKING_PHYSICS_REFINEMENT_PILOT_EXECUTE
BLOCKER_ID=NONE
NEXT_RESEARCH_EXECUTION_AUTHORIZED=false

## 终局

P0-S 完成 1,200 updates，是有效的 bounded negative arm：fixed-blind
`J/J0=0.6030763369`，且场与事件 competence 坍塌。P0-F 接受 25、尝试
150 updates 后触发 post-step rollback identity drift，无合法 endpoint，按合同不重试。
因此 matched screen 不完整，不能归因 function-space filter 增量。

## 证据边界

终局为 `LF7_MATCHED_SCREEN_INCOMPLETE_IDENTITY_INVALID`，candidate 为 none。
产物已回收并逐项核验，实例已关机，关机后完成本地 nominal 裁决。post-run
rollback 修复未重新执行，属于 engineering-only、non-voting 变更。direct
`LF_ONLY` 仍显著更强；stress 保持 sealed/unread。任何后续研究均须新的明确授权。
