# 当前阶段

- `phase_id`: `PHK_V23_LF9_EQUATION_ROUTED_THERMAL_CONTROL_VOLUME_REFINEMENT_EXECUTE`
- `phase_name`: PHK-V2.3 LF9 equation-routed thermal control-volume competence-filtered refinement
- `lifecycle_state`: `ACTIVE`
- `blocker_id`: `NONE`
- `machine_outcome`: `PENDING_ER_S_AND_ER_CV_SCREENS`
- `mechanism_outcome`: `PENDING_MATCHED_ADJUDICATION`
- `claim_status`: `CPU_QUALIFIED_GPU_MECHANISM_UNTESTED`
- `next_research_execution_authorized`: `true`
- `authorization_scope`: `TWO_MANDATORY_SCREENS_THEN_CONDITIONAL_FILTERED_FULL_PATH_AND_NO_FILTER_CONTROL`
- `candidate_status`: `NONE`
- `reference_status`: `CPU_REFERENCE_BLIND_STRESS_SEALED`
- `compute_status`: `CPU_QUALIFICATION_PASS_GPU_EXECUTION_PENDING`
- `next_recommendation`: `EXECUTE_FROZEN_LF9_CAMPAIGN`
- `effective_date`: `2026-09-08`

PHASE_ID=PHK_V23_LF9_EQUATION_ROUTED_THERMAL_CONTROL_VOLUME_REFINEMENT_EXECUTE
BLOCKER_ID=NONE
NEXT_RESEARCH_EXECUTION_AUTHORIZED=true

## 当前授权

执行 exact DEV-R 起点的 mandatory `ER-S` 与 `ER-CV` 200-accepted-update
matched screens。若至少一臂通过，按冻结机制选择继续至 filtered 1,200 accepted
updates 或有效 stall；仅当云端 selected endpoint 达到
`PRELOCAL_INTERNAL_PARETO` 时，运行 matched no-filter schedule control。

`PRELOCAL_INTERNAL_PARETO` 只是在 reference-blind 云端可计算门上通过，不得称
完整 PINN Pareto。实例关机后还须由 frozen local evaluator 形成
`COMPLETE_INTERNAL_PINN_PARETO`，再与 direct `LF_ONLY` 裁决 paper-value。

## 边界

CPU qualification 是零科学更新的工程准入，不是方法结果。不得改物理对象、
网络、冻结 streams、CV normalization、filter gates 或强基线；不授权 sparse、
new seed、OOD/stress、phase weak-form、PJGR/R2/SRPG 或投稿。两份 stress
references 保持 `TWO_STRESS_REFERENCES_SEALED_UNREAD`。
