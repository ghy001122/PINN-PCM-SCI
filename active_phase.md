# 当前阶段

- `phase_id`: `PHK_V23_LF6_EVENT_FRONTIER_RANK_BAND_AND_SAFETY_GATED_PHYSICS_PILOT_EXECUTE`
- `phase_name`: PHK-V2.3 LF6 cycle-resolved event-frontier rank-band alignment and safety-gated physics pilot
- `lifecycle_state`: `ACTIVE`
- `blocker_id`: `NONE`
- `claim_status`: `CPU_F_QUALIFIED_MATCHED_EVENT_FRONTIER_AND_CONDITIONAL_PHYSICS_EXECUTION_PENDING`
- `next_research_execution_authorized`: `true`
- `authorization_scope`: `DEV_U_THEN_DEV_R_THEN_SELECTED_SAFETY_P0`
- `candidate_status`: `NONE_PRE_RESULT`
- `reference_status`: `FINE_EXTRA_LF_ONLY_FROZEN_EVALUATOR_LOCAL_POST_SHUTDOWN_ONLY_STRESS_SEALED_UNREAD`
- `compute_status`: `CPU_F_COMPLETE_GPU_PENDING`
- `effective_date`: `2026-09-06`

PHASE_ID=PHK_V23_LF6_EVENT_FRONTIER_RANK_BAND_AND_SAFETY_GATED_PHYSICS_PILOT_EXECUTE
BLOCKER_ID=NONE
NEXT_RESEARCH_EXECUTION_AUTHORIZED=true

## 当前授权

CPU-F 已通过并冻结全部训练与评价坐标。允许依次运行 fixed 400-step
DEV-U、fixed 400-step DEV-R，以及按冻结规则选出的唯一 1200-step 纯物理
P0。不得从 telemetry 选模、调权、重跑或改变 seed。云端不得读取
fine、extra-fine、direct LF_ONLY、frozen evaluator 或 stress；本地评价必须
等待产物回收、GPU/进程清零和实例关机验证完成。

## 论文边界

开发臂是 data-only。只有 P0 的 loss 明确包含 PDE/BC/IC residual，才可称
PINN。匹配臂只允许判断 generic endpoint 与 event-frontier 的冻结机制关系；
single-seed、nominal 结果不是 multi-seed、OOD、stress、SOTA 或投稿就绪证据。
