# 项目状态

更新时间：2026-09-08

- `phase_id`: `PHK_V23_LF7_COMPETENCE_FILTERED_BLOCKWISE_BACKTRACKING_PHYSICS_REFINEMENT_PILOT_EXECUTE`
- `lifecycle_state`: `COMPLETE`
- `blocker_id`: `NONE`
- `machine_outcome`: `LF7_MATCHED_SCREEN_INCOMPLETE_IDENTITY_INVALID`
- `mechanism_outcome`: `MATCHED_SCREEN_INCOMPLETE_IDENTITY_INVALID`
- `claim_status`: `VALID_SMALL_STEP_NEGATIVE_ARM_FILTER_ARM_IDENTITY_INVALID_NO_MECHANISM_ATTRIBUTION`
- `next_research_execution_authorized`: `false`
- `candidate_status`: `NONE`
- `object_status`: `PHK_V21_FIXED_DISCRETIZATION_BENCHMARK_REUSED_UNCHANGED`
- `implementation_status`: `LF7_EXECUTED_ACTIVATION_SOURCE_POST_RUN_ROLLBACK_FIX_UNEXECUTED`
- `compute_status`: `GPU_COMPLETE_RECOVERED_HASH_VERIFIED_SHUTDOWN`
- `paper_status`: `PAPER_V23_TERMINAL_UPDATED`
- `stress_status`: `TWO_STRESS_REFERENCES_SEALED_UNREAD`
- `unique_next`: `RETAIN_VALID_ARM_NO_MECHANISM_ATTRIBUTION`

## VERIFIED

- P0-S 完成全部 1,200 个冻结 physics updates，endpoint finite 且
  potential/phase valid；fixed-blind ratio 为 `0.6030763369`，但两周期事件与场精度崩解。
- P0-F 尝试 150、接受 25 updates 后出现 post-step rollback identity drift；
  无 checkpoint/prediction endpoint，合同禁止 scientific retry。
- 事后定位为非空 Adam snapshot tensor aliasing；修复与回归未用于本次科学运行，
  不改变终局。
- 13/13 云端产物 remote/local size 与 SHA 一致；GPU/训练进程清零后关机，
  SSH `Connection refused` 先于本地评价。

## Evidence boundary

P0-S 只支持“小步长不足以形成 accuracy-preserving physics path”的单 seed
nominal 负面结果。P0-F 只支持 identity-invalid 记录，不能用于判断 competence
filter 的科学效果。没有 PINN Pareto、direct-baseline gain、candidate、multi-seed、
sparse/OOD/stress、SOTA 或实验验证；direct `LF_ONLY` 仍是更强基线。
