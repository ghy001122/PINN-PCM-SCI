# 当前阶段

- `phase_id`: `PHK_V23_LF4_THRESHOLD_ALIGNED_INTERFACE_BAND_MECHANISM_AND_CONDITIONAL_PHYSICS_PILOT_EXECUTE`
- `phase_name`: PHK-V2.3 LF4 threshold-aligned two-sided interface-band mechanism screen and conditional physics pilot
- `lifecycle_state`: `COMPLETE`
- `blocker_id`: `NONE`
- `machine_outcome`: `LF4_NO_DEVELOPMENT_ENTRY`
- `mechanism_outcome`: `BOUNDARY_EXPOSURE_SUPPORTED`
- `claim_status`: `LF4_BOUNDARY_EXPOSURE_SUPPORTED_NO_DEVELOPMENT_ENTRY_NO_PINN_RESULT`
- `next_research_execution_authorized`: `false`
- `authorization_scope`: `NONE_TERMINAL`
- `candidate_status`: `NONE`
- `reference_status`: `NOMINAL_LOCAL_EVALUATION_COMPLETE_STRESS_SEALED_UNREAD`
- `compute_status`: `THREE_DEVELOPMENT_ARMS_COMPLETE_P0_NOT_RUN_INSTANCE_SHUTDOWN_VERIFIED`
- `next_recommendation`: `P0_NOT_RUN_THREE_ARM_MECHANISM_NEGATIVE_UPDATE_PAPER`
- `effective_date`: `2026-09-05`

## 终局证据

三条 matched phase-only development arms 均从 exact LF3-T0 weights 完成固定
400 updates。`Rmin` 从 DEV-G 的 `0.819419` 提升到 DEV-M 的 `0.909256`
（`+0.089837`），且 DEV-M 保持冻结的 precision、active-mass、locality、
recovery 与 field-quality 条件，因此在本 single-seed nominal 对象上支持
`BOUNDARY_EXPOSURE_SUPPORTED`。DEV-C 虽将 `Rmin` 再提高 `0.032325` 并修复
timing，却令 phase weighted MSE 升至 `0.0296673` 且 cycle-2 recovery 降至
`0.767857`，不支持 threshold-aligned BCE 的 load-bearing claim。

DEV-G、DEV-M、DEV-C 分别因 timing、timing、phase error 未通过完整 P0-entry；
selected carrier 为 none，P0 按合同 `NOT_RUN`，不是 P0 失败。终局无 PINN
Pareto、无 strong-baseline gain、无 candidate。全部产物已回收并核验，实例已
关机且 SSH `Connection refused`；本地 nominal evaluation 此后才读取
fine/extra-fine 与 direct `LF_ONLY`。两份 stress references 始终 sealed/unread。

## 授权边界

LF4 完成不授权任何新训练、确认臂、混合 DEV-M/DEV-C、调权、新 seed、OOD、
stress、PJGR/R2、替代架构、kinetic teacher、投稿或作者联系。任何后续科研
动作都必须获得新的明确 EXECUTE 授权。

终局入口：[ADR 0062](docs/adr/0062-close-phk-v23-lf4-interface-band-pilot.md)、
[terminal closeout](docs/experiment/2026-09-05-phk-v23-lf4-terminal-closeout.md)、
[terminal artifact](docs/experiment/artifacts/20260905T082728Z-phk-v23-lf4-terminal.json)、
[terminal manifest](docs/experiment/manifests/20260905T082728Z-phk-v23-lf4-terminal.json)与
[paper_v23](paper/paper_v23/README.md)。
