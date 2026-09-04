# 项目状态

更新时间：2026-09-04

- `phase_id`: `PHK_V23_LF1_EVENT_PRESERVING_MULTIFIDELITY_PILOT`
- `lifecycle_state`: `COMPLETE`
- `blocker_id`: `NONE_TERMINAL`
- `claim_status`: `V22R_R0_R1A_R1X_C0_LF0_EVIDENCE_PRESERVED_LF1_DATA_ONLY_VALUE_NO_PINN_GAIN`
- `next_research_execution_authorized`: `false`
- `authorization_scope`: `NONE_LF1_COMPLETE`
- `candidate_status`: `NONE_LF1_PROVISIONAL_GATE_FAILED`
- `object_status`: `PHK_V21_FIXED_DISCRETIZATION_BENCHMARK_REUSED`
- `reference_status`: `MEDIUM_ONLY_GPU_METHOD_INPUT_FINE_EXTRA_LOCAL_NOMINAL_ONLY_STRESS_SEALED_UNREAD`
- `implementation_status`: `LF1_CONTRACTS_RUNNER_QUALIFICATION_EVALUATION_CLOUD_AND_TERMINAL_EVIDENCE_COMPLETE`
- `method_selection_status`: `EVENT_TRANSFER_AND_REPLAY_COMPETENCE_VALID_PINN_SPECIFIC_GAIN_NOT_ESTABLISHED`
- `compute_status`: `RUN_A_AND_B_COMPLETE_3600_UPDATES_RECOVERED_HASH_VERIFIED_SHUTDOWN_VERIFIED_GPU_TRAJECTORIES_2_OF_3_C_NOT_RUN`
- `contract_status`: `LF1_FOUR_CONTRACTS_CONSUMED_AND_FROZEN`
- `paper_status`: `BOUNDED_FAILURE_ANALYSIS_AND_DATA_ONLY_BASELINE_EVIDENCE_NO_HEADLINE_METHOD`
- `diagnostic_outcome`: `LF1_DATA_ONLY_VALUE_NO_PINN_GAIN`
- `next_recommendation`: `RETAIN_DATA_ONLY_VALUE_AS_NON_PINN_BASELINE_STOP_METHOD_CLAIM`

## 已核验证据

- V2.2R、R0A/R0B/R0C、R1a、R1X、C0 与 LF0 的历史负证据保持原边界；LF0 terminal 仍为 `LF0_NUMERICAL_OR_IDENTITY_INVALID`。
- LF1 CPU qualification 证明旧 LF0 sampler 的事件暴露约为 0.2%，旧 B0 在 direct LF_ONLY 事件支撑上的两周期 recall 为 0；新 range-preserving exact-top 表示可重构 medium 且六个事件池非空。
- Run A 在 V100/FP64/seed 17 上完成 1200 个 physics updates并通过 potential validity，但 `phase_max=0.0299932`、两周期事件缺失。
- Run B0 完成 1200 个 event-aware medium-only updates；gate grid `phase_max=0.754197`，两周期 teacher-event support 预测 active 点为 `1046/1164` 与 `1041/1102`，全部 transfer 与 potential guards 通过。
- Run B final 完成另 1200 个 `full physics + 0.1 persistent replay` updates；B0 与 final 均通过 frozen two-cycle competence。final 事件时间为 `0.209693/1.431489`，没有回落到冷态。
- 固定 reference-blind physics objective 从 B0 `7.37464` 降为 final `0.421175`，ratio=`0.0571112 <= 0.5`。但 final 相对 B0 的 phase primary/co-primary ratios 为 `1.18109/1.31211`，相对 direct LF_ONLY 为 `58.9211/32.6403`；phase noninferiority 与 temperature preservation 均失败。
- 冻结机器树终局为 `LF1_DATA_ONLY_VALUE_NO_PINN_GAIN`。条件 C 未触发，不得称 C 失败；candidate 为 none。
- A/B 共 3600 updates、`0.418302 GPU h`、估算 `0.786408 CNY`。Run B 12 个文件及 summary 绑定的 11 个产物全部远端/本地哈希一致，A/B 的 1200 个 physics-local batches 逐步相同。
- Run B 回收后实例已关闭并以 SSH connection refused 验证；本地 nominal evaluation 只在关机后执行。云端只有 medium 训练源，stress 始终 sealed/unread。

## 当前任务

LF1 已达到预声明 terminal outcome，没有剩余授权科学动作。保留 event-aware `LF_DATA_ONLY` 作为 non-PINN baseline 和 failure-analysis 证据，停止当前 method claim。任何新的 accuracy-preserving PINN 路线、第三条 GPU、phase-latent teacher、PJGR/R2、多 seed、stress 或 formal OOD 都必须先建立新合同并获得用户明确授权。

## 入口

- [active phase](active_phase.md)
- [live plan](docs/plans/NEXT_ACTIONS.md)
- [ADR 0057](docs/adr/0057-activate-phk-v23-lf1-event-preserving-multifidelity-pilot.md)
- [LF1 terminal closeout](docs/experiment/2026-09-03-phk-v23-lf1-terminal-closeout.md)
- [LF1 terminal artifact](docs/experiment/artifacts/20260903T155306Z-phk-v23-lf1-terminal-dc091be.json)
- [LF1 CPU qualification](docs/experiment/2026-09-03-phk-v23-lf1-cpu-qualification.md)
- [LF0 terminal closeout](docs/experiment/2026-09-03-phk-v23-lf0-terminal-closeout.md)
