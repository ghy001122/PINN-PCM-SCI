# 当前阶段

- `phase_id`: `PHK_V23_LF7_COMPETENCE_FILTERED_BLOCKWISE_BACKTRACKING_PHYSICS_REFINEMENT_PILOT_EXECUTE`
- `phase_name`: PHK-V2.3 LF7 competence-filtered blockwise backtracking physics refinement pilot
- `lifecycle_state`: `ACTIVE`
- `blocker_id`: `NONE`
- `machine_outcome`: `PENDING_GPU_MATCHED_SCREEN`
- `mechanism_outcome`: `PENDING`
- `claim_status`: `CPU_QUALIFIED_GPU_MECHANISM_UNTESTED`
- `next_research_execution_authorized`: `true`
- `authorization_scope`: `TWO_MATCHED_PHYSICS_REFINEMENT_ARMS`
- `candidate_status`: `NONE_PENDING_EVIDENCE`
- `reference_status`: `CLOUD_REFERENCE_BLIND_STRESS_SEALED`
- `compute_status`: `CPU_QUALIFICATION_PASS_GPU_PENDING`
- `next_recommendation`: `EXECUTE_AUTHORIZED_LF7_MATCHED_GPU_SCREEN`
- `effective_date`: `2026-09-07`

PHASE_ID=PHK_V23_LF7_COMPETENCE_FILTERED_BLOCKWISE_BACKTRACKING_PHYSICS_REFINEMENT_PILOT_EXECUTE
BLOCKER_ID=NONE
NEXT_RESEARCH_EXECUTION_AUTHORIZED=true

## 当前授权

从 exact LF6 DEV-R 分别执行 P0-S 固定小步长控制与 fresh P0-F
competence-filtered blockwise backtracking。两臂使用同一预物化 1,200-step
physics stream；P0-F 的 medium 只参加每 25 步 accept/reject，不进入梯度。

## 已通过门

CPU/FP64 零步资格的 24 项检查全部通过，精确复核
`J0=4.9278721846990505`、DEV-R full-medium audit、1,200-step ledger、fixed
blind pool、rollback/RNG 和真实有限 backward。该门不含科研性能 premise。

## 边界

最多两条科学 GPU 轨迹；P0-S 固定 1,200 updates，P0-F 最多 1,200
accepted / 2,400 attempted updates。禁止新增 anchor/replay、优化器、seed、
sparse/OOD/stress、weak-form/control-volume 或其他救援。本阶段完成后必须回收、
关机并在本地裁决；后续研究仍须新授权。
