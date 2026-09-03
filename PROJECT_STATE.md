# 项目状态

更新时间：2026-09-03

- `phase_id`: `PHK_V23_LF0_EXACT_TOP_WARMSTART_ATTRIBUTION_EXECUTE`
- `lifecycle_state`: `AWAITING`
- `blocker_id`: `AWAITING_AUTODL_RESTART_CAMPAIGN_AUTHORIZATION_REMAINS_ACTIVE`
- `claim_status`: `C0_OUTPUT_TRANSFORM_INADMISSIBLE_PRESERVED_LF0_CPU_QUALIFIED_NO_GPU_SCIENTIFIC_RESULT`
- `next_research_execution_authorized`: `true`
- `authorization_scope`: `LF0_CPU_GATE_THEN_A_B_AND_CONDITIONAL_C_ONLY`
- `candidate_status`: `NOT_FROZEN`
- `object_status`: `PHK_V21_FIXED_DISCRETIZATION_BENCHMARK_REUSED`
- `reference_status`: `MEDIUM_DECLARED_METHOD_INPUT_FINE_EXTRA_LOCAL_EVAL_ONLY_STRESS_SEALED_UNREAD`
- `implementation_status`: `LF0_IMPLEMENTATION_AND_DEPLOYMENT_PACKAGE_COMPLETE`
- `method_selection_status`: `NO_CANDIDATE_LF0_ATTRIBUTION_PENDING`
- `compute_status`: `LF0_CPU_QUALIFIED_GPU_ENDPOINT_OFFLINE_RUN_A_NOT_STARTED`
- `contract_status`: `LF0_FOUR_CONTRACTS_FROZEN_CPU_QUALIFIED`
- `paper_status`: `EXISTING_BOUNDED_NEGATIVE_ADVISOR_DRAFT_PRESERVED`
- `diagnostic_outcome`: `LF0_CPU_QUALIFIED`
- `next_recommendation`: `RESTART_AUTODL_AND_EXECUTE_LF0_RUN_A`

## 已核验证据

- C0 的输出包络裁决与全部历史负面证据保持冻结；LF0 尚未形成 GPU 科学结果。
- C0 官方 strong-form compatibility 子门为 residual/floor `1.91408`、RHS sign agreement `1.0`；不得改成 medium-only 分子重新裁决。
- medium fixed-discretization carrier 具备两周期 competence，并相对 extra-fine 在 phase primary 与 co-primary 上都存在超过冻结 component floor 的 correction headroom。
- exact-top raw affine lift 可在不施加 E2 内部下界的情况下严格满足 top Dirichlet 与零 waveform；201 项 focused/affected regression 与 document consistency 均通过。
- 正式 CPU 资格门通过：medium/fine/extra-fine 所需 exact-top latent 均有限，medium 两周期 competence 通过，C0 strong-form gate 为 `1.91408/1.0`，phase correction headroom 超过两个冻结 component floors。

## 当前任务

已完成 LF0 四合同、exact-top/medium-only 训练状态机、CPU 资格、必要回归与 Run-A 部署包。当前已知 AutoDL 端点不可达；实例重启后按 A→B→条件 C 机器树继续。任何 GPU 轨迹完成后先回收、随后立即关机，再做本地 nominal evaluation。

## 入口

- [active phase](active_phase.md)
- [live plan](docs/plans/NEXT_ACTIONS.md)
- [ADR 0056](docs/adr/0056-activate-phk-v23-lf0-exact-top-warmstart-attribution.md)
- [LF0 CPU qualification](docs/experiment/2026-09-03-phk-v23-lf0-cpu-qualification.md)
- [C0 closeout](docs/experiment/2026-09-03-phk-v23-c0-reference-discrete-strongform-compatibility-closeout.md)
- [R1X terminal closeout](docs/experiment/2026-09-03-phk-v23-r1x-e2-pure-scratch-stop-closeout.md)
