# 项目状态

更新时间：2026-09-04

- `phase_id`: `PHK_V23_LF2_MEASURE_CALIBRATED_FEASIBLE_PINN_EXECUTE`
- `lifecycle_state`: `ACTIVE`
- `blocker_id`: `NONE`
- `claim_status`: `V22R_R0_R1A_R1X_C0_LF0_LF1_EVIDENCE_PRESERVED_LF2_CPU_QUALIFIED_GPU_RESULT_PENDING`
- `next_research_execution_authorized`: `true`
- `authorization_scope`: `ONE_REFERENCE_BLIND_V100_FP64_SEED17_TRAJECTORY_THEN_RECOVERY_SHUTDOWN_LOCAL_NOMINAL_EVALUATION`
- `candidate_status`: `NONE_PENDING_FROZEN_LF2_ADJUDICATION`
- `object_status`: `PHK_V21_FIXED_DISCRETIZATION_BENCHMARK_REUSED`
- `reference_status`: `MEDIUM_ONLY_GPU_METHOD_INPUT_FINE_EXTRA_LOCAL_NOMINAL_ONLY_AFTER_SHUTDOWN_STRESS_SEALED_UNREAD`
- `implementation_status`: `LF2_CONTRACTS_RUNNER_QUALIFICATION_EVALUATION_CLOUD_AND_TESTS_READY`
- `method_selection_status`: `MEASURE_CALIBRATED_M0_THEN_CONDITIONAL_FEASIBILITY_CONSTRAINED_FULL_PHYSICS`
- `compute_status`: `CPU_QUALIFIED_ZERO_LF2_SCIENTIFIC_GPU_TRAJECTORIES_REMOTE_PREFLIGHT_PENDING`
- `contract_status`: `LF2_FOUR_CONTRACTS_FROZEN_ACTIVE`
- `paper_status`: `LF1_FAILURE_ANALYSIS_REUSABLE_LF2_ACCURACY_PHYSICS_PARETO_PILOT_PENDING`
- `diagnostic_outcome`: `LF2_CPU_QUALIFICATION_PASS`
- `next_recommendation`: `REMOTE_ZERO_STEP_PREFLIGHT_THEN_SOLE_LF2_TRAJECTORY`

## 已核验证据

- V2.2R、R0A/R0B/R0C、R1a、R1X、C0、LF0 与 LF1 的历史证据保持原边界；LF1 terminal 仍为 `LF1_DATA_ONLY_VALUE_NO_PINN_GAIN`，条件 C 未运行。
- LF2 的 program/method/data/decision 四合同已冻结；唯一科学轨迹上限为 2400 updates、1 V100 hour、3 CNY、seed 17。
- CPU 资格把 medium 的 1,603,200 个 saved nodes 互斥穷尽分成 14 类，所有类非空且测度质量和为 1；分区哈希为 `EFD70886DD85AC467F06F38B48FB0EE6C0132471CE74817E3A4D68E752B7A515`。
- LF1-B0 的全-medium target-measure audit 复算有限、potential validity 通过且有两周期事件，但 precision 为 `0.17052/0.16110`、active-mass ratio 为 `5.26976/5.86388`、event-time error 为 `0.04462/0.05178`。
- LF1 B0/replay 的 onset-event proposal 相对 target measure 平均放大 `176.5225x/353.0450x`，支持“训练测度错配”作为 LF2 的首要可检验阻塞。
- 常数 weighted-estimator 恒等、AL 公式、M0 无 physics RNG、M1 physics 批次身份、数值守卫、七类结局与云端 reference boundary 均通过测试；相关 focused/regression tests 共 100 项通过。
- 部署 source identity 为 `LF2-BUNDLE-AB0756BF7D4CBDCFDCA88F48C5BBB882760D586C65089999DA16F1DFA64E4AA3`。CPU 资格没有科学模型更新、GPU、fine/extra-fine evaluator 或 stress I/O。

## 当前任务

在 live price、精确 V100、零重复进程、source/checkpoint/qualification hash 与禁止引用文件边界全部通过远端零步 preflight 后，运行唯一 LF2 trajectory。运行完成后必须先回收、核验并关机，再做本地 nominal adjudication。M0 gate 失败时不进入 M1；任何数值/身份失败或 terminal outcome 均按七类唯一映射收口，不做自动科学重试。

## 入口

- [active phase](active_phase.md)
- [live plan](docs/plans/NEXT_ACTIONS.md)
- [ADR 0058](docs/adr/0058-activate-phk-v23-lf2-measure-calibrated-feasible-pinn.md)
- [LF2 CPU qualification](docs/experiment/2026-09-04-phk-v23-lf2-cpu-qualification.md)
- [LF1 terminal closeout](docs/experiment/2026-09-03-phk-v23-lf1-terminal-closeout.md)
