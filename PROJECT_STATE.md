# 项目状态

更新时间：2026-09-04

- `phase_id`: `PHK_V23_LF2_MEASURE_CALIBRATED_FEASIBLE_PINN_EXECUTE`
- `lifecycle_state`: `COMPLETE`
- `blocker_id`: `NONE`
- `claim_status`: `V22R_R0_R1A_R1X_C0_LF0_LF1_EVIDENCE_PRESERVED_LF2_CALIBRATED_CARRIER_NOT_ESTABLISHED`
- `next_research_execution_authorized`: `false`
- `authorization_scope`: `LF2_CAMPAIGN_CONSUMED_AND_CLOSED`
- `candidate_status`: `NONE`
- `object_status`: `PHK_V21_FIXED_DISCRETIZATION_BENCHMARK_REUSED`
- `reference_status`: `NOMINAL_LOCAL_DEVELOPMENT_EVALUATED_AFTER_SHUTDOWN_STRESS_SEALED_UNREAD`
- `implementation_status`: `LF2_TRAJECTORY_RECOVERED_HASH_VERIFIED_AND_TERMINALLY_ADJUDICATED`
- `method_selection_status`: `MEASURE_CALIBRATION_NOT_SUFFICIENT_TO_ESTABLISH_EVENT_CARRIER`
- `compute_status`: `ONE_V100_FP64_SEED17_TRAJECTORY_1200_M0_UPDATES_M1_ZERO_INSTANCE_SHUTDOWN_VERIFIED`
- `contract_status`: `LF2_FOUR_CONTRACTS_FROZEN_CONSUMED`
- `paper_status`: `BOUNDED_FAILURE_ANALYSIS_REUSABLE_NO_POSITIVE_LF2_METHOD_CLAIM`
- `diagnostic_outcome`: `LF2_CALIBRATED_CARRIER_NOT_ESTABLISHED`
- `next_recommendation`: `PHASE_LATENT_TEACHER_BACKUP_REQUIRES_NEW_EXECUTE`

## 已核验证据

- V2.2R、R0A/R0B/R0C、R1a、R1X、C0、LF0 与 LF1 的历史证据保持原边界。LF1 terminal 仍为 `LF1_DATA_ONLY_VALUE_NO_PINN_GAIN`。
- LF2 CPU 资格通过；medium 的 1,603,200 个 saved nodes 被互斥穷尽分为 14 类，分区哈希为 `EFD70886DD85AC467F06F38B48FB0EE6C0132471CE74817E3A4D68E752B7A515`。
- 首次远端启动因 bundle 遗漏 `tests/test_phk_v21_benchmark.py` 而在模型、Adam 和 optimizer 构造前退出，科学轨迹与 optimizer updates 均为 0。依赖闭包由隔离真实 physics-load 回归修复，同一科学身份工程重执行合法完成。
- 唯一科学轨迹使用 Tesla V100-PCIE-32GB、FP64、seed 17 和 `LF2-BUNDLE-9D06E26720363A39E5CC62D87E1B494A4AFA0116EEA727A103DB6B5FB2ABD455`；M0 恰好执行 1200 个 target-measure data-only updates，M1 因 M0 gate 失败而执行 0 步。
- M0 全-medium potential maximum-principle 通过且所有值有限，但 `phase_max=0.0299479`、两周期 hard active mass/recall 均为 0，无事件。相对 LF1-B0 的 potential、temperature、phase weighted-MSE ratio 分别为 `0.257104/0.0654992/0.273361`：全局目标测度误差下降没有保留稀疏事件拓扑。
- 本地 frozen evaluator 在完整回收、哈希核验和 SSH `Connection refused` 关机证明之后运行。LF2-M0 的 phase ROI RMS 为 `0.110564`、phase symmetric difference 为 `0.00515`，六个 event/topology hard guards 全部失败；direct `LF_ONLY` 仍两周期 competent，phase ROI RMS 为 `0.00657038`。
- M0 在固定 reference-blind physics pool 上的 objective 为 `0.571770`；由于 M1 未运行，final/M0 ratio 未定义，不能形成 PINN-specific gain 或候选。
- GPU 运行 wall time 为 `83.8726 s`，即 `0.0232979 GPU h`；按 `1.88 CNY/h` 估算增量费用为 `0.0438001 CNY`。全部 summary-bound 产物完成远端/本地 size 与 SHA-256 对账，AutoDL 已关闭并确认 SSH 拒绝连接。
- 云端仅有 medium 训练源与精确 LF1-B0 checkpoint；没有读取 fine、extra-fine、frozen evaluator 或 stress。fine/extra-fine 仅在关机后用于本地 nominal development evaluation；两份 stress references 始终 sealed/unread。

## 科学裁决

- `VERIFIED`：评价兼容 target measure 显著降低三项全局加权场误差，但把 LF1-B0 的两周期事件载体压回冷态；M0 gate 失败，M1 未触发，candidate 为 none。
- `SUPPORTED_INTERPRETATION`：sampling-measure mismatch 是 LF1 过宽 carrier 的真实因素，但不是建立准确事件载体的充分修复；稀有事件拓扑与全局测度误差仍可发生目标错位。
- `HYPOTHESIS`：若另行授权，下一条最小后备应直接监督 phase latent 或 kinetic RHS，而不是延长 M0、调权重、换 optimizer 或跳过 gate 运行 M1。
- `UNKNOWN`：phase-latent teacher 是否能建立合法两周期 carrier；其后 full physics 是否能在强 `LF_ONLY` 基线容限内产生独立增量；多 seed、stress、formal OOD 与投稿级有效性。

## 当前任务

LF2 已终局，无科研动作处于授权状态。下一步只能先形成并由用户批准新的、独立的 phase-latent teacher 最小合同；在 competent backbone 建立前不得推进 PJGR/R2、multi-seed 或 stress，也不得把治理、哈希或代码完成表述为科研进展。

## 入口

- [active phase](active_phase.md)
- [live plan](docs/plans/NEXT_ACTIONS.md)
- [ADR 0058](docs/adr/0058-activate-phk-v23-lf2-measure-calibrated-feasible-pinn.md)
- [LF2 terminal closeout](docs/experiment/2026-09-04-phk-v23-lf2-terminal-closeout.md)
- [LF2 CPU qualification](docs/experiment/2026-09-04-phk-v23-lf2-cpu-qualification.md)
- [LF1 terminal closeout](docs/experiment/2026-09-03-phk-v23-lf1-terminal-closeout.md)
