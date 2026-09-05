# 当前阶段

- `phase_id`: `PHK_V23_LF4_THRESHOLD_ALIGNED_INTERFACE_BAND_MECHANISM_AND_CONDITIONAL_PHYSICS_PILOT_EXECUTE`
- `phase_name`: PHK-V2.3 LF4 threshold-aligned two-sided interface-band mechanism screen and conditional physics pilot
- `lifecycle_state`: `EXECUTING_GPU_PENDING_ACTIVATION_COMMIT`
- `blocker_id`: `NONE`
- `claim_status`: `LF4_CPU_GEOMETRY_SUPPORT_ONLY_GPU_MECHANISM_UNTESTED`
- `next_research_execution_authorized`: `true`
- `authorization_scope`: `LF4_THREE_MATCHED_DEVELOPMENT_ARMS_AND_CONDITIONAL_P0_ONLY`
- `candidate_status`: `NONE`
- `reference_status`: `FINE_EXTRA_LF_ONLY_LOCAL_AFTER_SHUTDOWN_STRESS_SEALED_UNREAD`
- `compute_status`: `CPU_G_PASS_GPU_ZERO_UPDATES_PENDING`
- `next_recommendation`: `ACTIVATION_COMMIT_DEPLOY_RUN_DEV_G_M_C_THEN_CONDITIONAL_P0`
- `effective_date`: `2026-09-05`

## 授权边界

当前用户已明确授权 LF4 完整执行。三条 development arms 均须从 exact
LF3-T0 weights 运行到固定 step 400；不得因早臂失败提前关闭。至少一臂通过
P0-entry 时，必须按冻结选择规则运行 1200-step label-free full-physics P0。
不授权 full-from-LF1-B0 confirmation、新 seed、OOD、stress、PJGR/R2、替代
架构、kinetic teacher、投稿或作者联系。

## 当前证据

CPU-G 为零 optimizer update，通过输入、四个非周期界面池、phase-logit
数学和全部流哈希门。LF3-T0 的 481 FN 中 455 个、227 FP 中 199 个位于
teacher boundary graph distance 0。这是 `VERIFIED` 几何证据；界面机制
是否有增量仍为 `UNKNOWN`。

入口：[ADR 0061](docs/adr/0061-activate-phk-v23-lf4-interface-band-pilot.md)、
[CPU-G](docs/experiment/2026-09-05-phk-v23-lf4-cpu-qualification.md)、
[四合同](configs/phk_v23/program_contract_lf4_interface_band.json)与
[live plan](docs/plans/NEXT_ACTIONS.md)。
