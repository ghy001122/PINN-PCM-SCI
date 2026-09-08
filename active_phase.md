# 当前阶段

- `phase_id`: `PHK_V23_LF8_IDENTITY_CORRECT_COMPETENCE_FILTER_COMPLETION_AND_SCHEDULE_ATTRIBUTION_EXECUTE`
- `phase_name`: PHK-V2.3 LF8 identity-correct competence-filter completion and conditional schedule attribution
- `lifecycle_state`: `ACTIVE`
- `blocker_id`: `NONE`
- `machine_outcome`: `PENDING_MANDATORY_P0_FSTAR`
- `mechanism_outcome`: `PENDING`
- `claim_status`: `CPU_QUALIFIED_GPU_FILTER_UNTESTED`
- `next_research_execution_authorized`: `true`
- `authorization_scope`: `ONE_MANDATORY_P0_FSTAR_THEN_CONDITIONAL_SCHEDULE_CONTROL`
- `candidate_status`: `NONE_PENDING_EVIDENCE`
- `reference_status`: `CLOUD_REFERENCE_BLIND_STRESS_SEALED`
- `compute_status`: `CPU_QUALIFICATION_PASS_GPU_PENDING`
- `next_recommendation`: `EXECUTE_AUTHORIZED_P0_FSTAR`
- `effective_date`: `2026-09-08`

PHASE_ID=PHK_V23_LF8_IDENTITY_CORRECT_COMPETENCE_FILTER_COMPLETION_AND_SCHEDULE_ATTRIBUTION_EXECUTE
BLOCKER_ID=NONE
NEXT_RESEARCH_EXECUTION_AUTHORIZED=true

## 当前授权

从 exact LF6 DEV-R 执行 mandatory P0-F* identity-correct competence-filtered
strong-form refinement。仅当 F* 接受全部 1,200 updates、保持安全且降低
fixed-blind objective 时，才从 exact DEV-R 执行 accepted-schedule matched control。

## 已通过门

CPU/FP64 零步资格的九项检查全部通过。真实三头模型与 28 个非空 Adam
state entries 通过两个连续 mutate/reject/restore 循环；快照与 live optimizer
无 tensor alias，模型、优化器及 RNG 状态 bitwise 恢复。该门仅是工程身份事实。

## 边界

F* 最多 1,200 accepted / 2,400 attempted updates；conditional control 固定
1,200 updates。禁止额外 strong-form rescue、seed、sparse、weak/control-volume、
OOD/stress、PJGR/R2/SRPG 或投稿。本阶段结束后必须回收、关机、本地裁决并关闭授权。
