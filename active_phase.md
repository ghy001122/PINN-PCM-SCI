# 当前阶段

- `phase_id`: `PHK_V23_LF3_MEASURE_DECOUPLED_STARTUP_SCALED_PHASE_LATENT_CARRIER_PILOT_EXECUTE`
- `phase_name`: PHK-V2.3 LF3 measure-decoupled startup-scaled phase-latent carrier pilot
- `lifecycle_state`: `CPU_QUALIFIED_GPU_EXECUTION_AUTHORIZED`
- `blocker_id`: `NONE`
- `claim_status`: `LF2_EVIDENCE_PRESERVED_LF3_CPU_QUALIFIED_NO_GPU_RESULT_YET`
- `next_research_execution_authorized`: `true`
- `authorization_scope`: `SOLE_LF3_T0_TO_CONDITIONAL_P0_V100_FP64_SEED17_TRAJECTORY`
- `plan_status`: `LF3_GPU_EXECUTION_READY`
- `contract_status`: `LF3_FOUR_CONTRACTS_FROZEN_CPU_QUALIFIED`
- `object_status`: `PHK_V21_FIXED_DISCRETIZATION_OBJECT_REUSED_WITHOUT_CONTINUUM_ORACLE_CLAIM`
- `method_selection_status`: `ATTRIBUTED_SOLVER_RECOVERY_COMBINATION_PILOT_PENDING_GPU_RESULT`
- `candidate_status`: `NONE`
- `reference_status`: `FINE_EXTRA_FROZEN_EVALUATOR_LOCAL_ONLY_AFTER_SHUTDOWN_STRESS_SEALED_UNREAD`
- `compute_status`: `ZERO_SCIENTIFIC_UPDATES_CPU_GATE_PASS_REMOTE_PREFLIGHT_AND_SOLE_TRAJECTORY_PENDING`
- `diagnostic_outcome`: `LF3_CPU_QUALIFICATION_PASS`
- `next_recommendation`: `REMOTE_ZERO_STEP_PREFLIGHT_THEN_T0_TO_CONDITIONAL_P0`
- `git_authorization`: `LF3_ACTIVATION_AND_TERMINAL_EXACT_WHITELIST_COMMIT_AND_PUSH_MAIN`
- `external_publication_authorization`: `NOT_AUTHORIZED`
- `effective_date`: `2026-09-04`

## 当前授权边界

用户已明确授权 `PHK_V23_LF3_MEASURE_DECOUPLED_STARTUP_SCALED_PHASE_LATENT_CARRIER_PILOT_EXECUTE`。CPU 资格门已通过，允许部署并执行唯一一条 V100/FP64/seed-17 `T0 -> conditional P0` 科学轨迹，总更新上限 2400。T0 失败即停止且 P0 不得称为失败；只有 T0 carrier gate 全通过才进入无标签 P0。

不授权第二条轨迹、新 seed、matched output-phase ablation、OOD、stress、PJGR/R2、kinetic teacher、冻结 evaluator 或物理对象修改。fine、extra-fine 和 evaluator 只能在完整回收、哈希核验、关机并确认 SSH 拒绝后于本地读取。两份 stress references 继续 `TWO_STRESS_REFERENCES_SEALED_UNREAD`。

~~~text
PHASE_ID=PHK_V23_LF3_MEASURE_DECOUPLED_STARTUP_SCALED_PHASE_LATENT_CARRIER_PILOT_EXECUTE
BLOCKER_ID=NONE
METHOD_SELECTION_STATUS=ATTRIBUTED_SOLVER_RECOVERY_COMBINATION_PILOT_PENDING_GPU_RESULT
NEXT_RESEARCH_EXECUTION_AUTHORIZED=true
CURRENT_STAGE=REMOTE_ZERO_STEP_PREFLIGHT_THEN_SOLE_GPU_TRAJECTORY
~~~

## 当前证据入口

LF3 资格事实见 [CPU qualification](docs/experiment/2026-09-04-phk-v23-lf3-cpu-qualification.md)，冻结决定见 [ADR 0059](docs/adr/0059-activate-phk-v23-lf3-phase-latent-carrier-pilot.md)。LF2 terminal `LF2_CALIBRATED_CARRIER_NOT_ESTABLISHED` 及更早证据保持不改写。
