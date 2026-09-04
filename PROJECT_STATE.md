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
- `implementation_status`: `LF2_DEPLOYMENT_TRANSITIVE_CLOSURE_REPAIRED_ISOLATED_PHYSICS_LOAD_VALID`
- `method_selection_status`: `MEASURE_CALIBRATED_M0_THEN_CONDITIONAL_FEASIBILITY_CONSTRAINED_FULL_PHYSICS`
- `compute_status`: `CPU_QUALIFIED_ZERO_LF2_SCIENTIFIC_GPU_TRAJECTORIES_ONE_PRESTEP_ENGINEERING_FAILURE_ER1_READY`
- `contract_status`: `LF2_FOUR_CONTRACTS_FROZEN_ACTIVE`
- `paper_status`: `LF1_FAILURE_ANALYSIS_REUSABLE_LF2_ACCURACY_PHYSICS_PARETO_PILOT_PENDING`
- `diagnostic_outcome`: `LF2_CPU_QUALIFICATION_PASS`
- `next_recommendation`: `REMOTE_ER1_ZERO_STEP_PREFLIGHT_THEN_SOLE_LF2_TRAJECTORY`

## 已核验证据

- V2.2R、R0A/R0B/R0C、R1a、R1X、C0、LF0 与 LF1 的历史证据保持原边界；LF1 terminal 仍为 `LF1_DATA_ONLY_VALUE_NO_PINN_GAIN`，条件 C 未运行。
- LF2 的 program/method/data/decision 四合同已冻结；唯一科学轨迹上限为 2400 updates、1 V100 hour、3 CNY、seed 17。
- CPU 资格把 medium 的 1,603,200 个 saved nodes 互斥穷尽分成 14 类，所有类非空且测度质量和为 1；分区哈希为 `EFD70886DD85AC467F06F38B48FB0EE6C0132471CE74817E3A4D68E752B7A515`。
- LF1-B0 的全-medium target-measure audit 复算有限、potential validity 通过且有两周期事件，但 precision 为 `0.17052/0.16110`、active-mass ratio 为 `5.26976/5.86388`、event-time error 为 `0.04462/0.05178`。
- LF1 B0/replay 的 onset-event proposal 相对 target measure 平均放大 `176.5225x/353.0450x`，支持“训练测度错配”作为 LF2 的首要可检验阻塞。
- 常数 weighted-estimator 恒等、AL 公式、M0 无 physics RNG、M1 physics 批次身份、数值守卫、七类结局与云端 reference boundary 均通过测试；相关 focused/regression tests 共 100 项通过。
- 首次远端启动在 `load_case_physics()` 阶段因部署包遗漏其哈希绑定依赖 `tests/test_phk_v21_benchmark.py` 而退出；输出目录为空，模型、Adam 与 optimizer 均未构造，科学轨迹仍为 0。闭包现已补齐，并由解包隔离目录中的真实 physics load 回归证明。
- 工程重执行 source identity 为 `LF2-BUNDLE-9D06E26720363A39E5CC62D87E1B494A4AFA0116EEA727A103DB6B5FB2ABD455`。科学合同、medium、LF1-B0 checkpoint、seed、阶段、loss、采样与运行上限均未改变；CPU 资格及本次工程失败均没有 fine/extra-fine evaluator 或 stress I/O。

## 当前任务

按用户已明确的首步前纯工程故障覆盖规则，以完全相同科学身份执行一次工程重启：新闭包必须先在远端再次通过 live price、精确 V100、零重复进程、source/checkpoint/qualification hash 与禁止引用文件边界零步 preflight。随后运行唯一 LF2 trajectory；运行完成后必须先回收、核验并关机，再做本地 nominal adjudication。M0 gate 失败时不进入 M1；首个 optimizer step 后不得科学重试。

## 入口

- [active phase](active_phase.md)
- [live plan](docs/plans/NEXT_ACTIONS.md)
- [ADR 0058](docs/adr/0058-activate-phk-v23-lf2-measure-calibrated-feasible-pinn.md)
- [LF2 CPU qualification](docs/experiment/2026-09-04-phk-v23-lf2-cpu-qualification.md)
- [LF1 terminal closeout](docs/experiment/2026-09-03-phk-v23-lf1-terminal-closeout.md)
