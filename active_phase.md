# 当前阶段

- `phase_id`: `PHK_V23_LF2_MEASURE_CALIBRATED_FEASIBLE_PINN_EXECUTE`
- `phase_name`: PHK-V2.3 LF2 measure-calibrated feasible PINN single-seed nominal pilot
- `lifecycle_state`: `ACTIVE`
- `blocker_id`: `NONE`
- `claim_status`: `V22R_R0_R1A_R1X_C0_LF0_LF1_EVIDENCE_PRESERVED_LF2_CPU_QUALIFIED_GPU_RESULT_PENDING`
- `next_research_execution_authorized`: `true`
- `authorization_scope`: `ONE_REFERENCE_BLIND_V100_FP64_SEED17_TRAJECTORY_THEN_RECOVERY_SHUTDOWN_LOCAL_NOMINAL_EVALUATION`
- `plan_status`: `LF2_GPU_EXECUTION_READY`
- `contract_status`: `LF2_FOUR_CONTRACTS_FROZEN_ACTIVE`
- `object_status`: `PHK_V21_FIXED_DISCRETIZATION_OBJECT_REUSED_WITHOUT_CONTINUUM_ORACLE_CLAIM`
- `method_selection_status`: `MEASURE_CALIBRATED_M0_THEN_CONDITIONAL_FEASIBILITY_CONSTRAINED_FULL_PHYSICS`
- `candidate_status`: `NONE_PENDING_FROZEN_LF2_ADJUDICATION`
- `reference_status`: `MEDIUM_ONLY_GPU_METHOD_INPUT_FINE_EXTRA_LOCAL_NOMINAL_ONLY_AFTER_SHUTDOWN_STRESS_SEALED_UNREAD`
- `compute_status`: `CPU_QUALIFIED_ZERO_LF2_SCIENTIFIC_GPU_TRAJECTORIES_REMOTE_PREFLIGHT_PENDING`
- `diagnostic_outcome`: `LF2_CPU_QUALIFICATION_PASS`
- `next_recommendation`: `REMOTE_ZERO_STEP_PREFLIGHT_THEN_SOLE_LF2_TRAJECTORY`
- `git_authorization`: `AUTHORIZED_EXACT_LF2_WHITELIST_ACTIVATION_AND_TERMINAL_PUSH_MAIN`
- `external_publication_authorization`: `NOT_AUTHORIZED`
- `effective_date`: `2026-09-04`

## 当前授权边界

用户已明确授权完整执行 `PHK_V23_LF2_MEASURE_CALIBRATED_FEASIBLE_PINN_EXECUTE`。CPU 资格门已通过；当前可执行唯一一条 V100/FP64/seed-17 reference-blind trajectory，最多 2400 updates、1 V100 hour 和 3 CNY。M0 固定为 1200-step target-measure data-only 校准且不得构造或推进 physics sampler；只有 M0 full-medium gate 全部通过才进入 1200-step M1。M1 使用原 full-physics objective、独立 measure-constraint stream 和与 LF1 逐步相同的 physics batches。

云端只允许 medium label carrier 与精确 LF1-B0 checkpoint；fine、extra-fine、frozen evaluator 和 stress 不得出现。GPU 结束后必须完整回收并核验 summary-bound artifacts，立即关机且确认 SSH refused，之后才能在本地读取 nominal fine/extra-fine 并运行未修改的 frozen evaluator。

不授权第二条 LF2 科学轨迹、新 seed、phase-latent teacher 后备、PJGR/R2、stress、formal OOD、评价器/阈值/物理对象修改或投稿。任何 terminal outcome 都不自动授权下一阶段。

~~~text
PHASE_ID=PHK_V23_LF2_MEASURE_CALIBRATED_FEASIBLE_PINN_EXECUTE
BLOCKER_ID=NONE
METHOD_SELECTION_STATUS=MEASURE_CALIBRATED_M0_THEN_CONDITIONAL_FEASIBILITY_CONSTRAINED_FULL_PHYSICS
NEXT_RESEARCH_EXECUTION_AUTHORIZED=true
CURRENT_STAGE=REMOTE_ZERO_STEP_PREFLIGHT_PENDING
~~~

## 当前证据入口

CPU 资格事实与边界见 [LF2 CPU qualification](docs/experiment/2026-09-04-phk-v23-lf2-cpu-qualification.md)，决定理由见 [ADR 0058](docs/adr/0058-activate-phk-v23-lf2-measure-calibrated-feasible-pinn.md)。LF1 terminal `LF1_DATA_ONLY_VALUE_NO_PINN_GAIN` 保持不改写。
