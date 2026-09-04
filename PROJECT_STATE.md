# 项目状态

更新时间：2026-09-05

- `phase_id`: `PHK_V23_LF3_MEASURE_DECOUPLED_STARTUP_SCALED_PHASE_LATENT_CARRIER_PILOT_EXECUTE`
- `lifecycle_state`: `COMPLETE`
- `blocker_id`: `NONE`
- `claim_status`: `LF3_CARRIER_NOT_ESTABLISHED_P0_NOT_TRIGGERED_NEGATIVE_ADVISOR_DRAFT_COMPLETE`
- `next_research_execution_authorized`: `false`
- `authorization_scope`: `LF3_CAMPAIGN_CONSUMED_AND_CLOSED`
- `candidate_status`: `NONE`
- `object_status`: `PHK_V21_FIXED_DISCRETIZATION_BENCHMARK_REUSED`
- `reference_status`: `NOMINAL_FINE_EXTRA_EVALUATED_ONLY_AFTER_SHUTDOWN_STRESS_SEALED_UNREAD`
- `implementation_status`: `LF3_EXECUTED_LOCAL_EVALUATION_ROLE_IDENTITY_REPAIRED_AND_VERIFIED`
- `method_selection_status`: `LF3_COMBINATION_NEAR_PASS_NOT_A_CARRIER_OR_PINN_CANDIDATE`
- `compute_status`: `ONE_SCIENTIFIC_TRAJECTORY_1200_T0_UPDATES_P0_ZERO_INSTANCE_SHUTDOWN_VERIFIED`
- `contract_status`: `LF3_FOUR_CONTRACTS_EXECUTED_AND_TERMINALLY_ADJUDICATED`
- `paper_status`: `PAPER_V23_NEGATIVE_SOLVER_RECOVERY_ADVISOR_DRAFT_COMPLETE`
- `diagnostic_outcome`: `LF3_CARRIER_NOT_ESTABLISHED`
- `next_recommendation`: `STOP_LATENT_CARRIER_ROUTE_RETAIN_NEGATIVE_ADVISOR_DRAFT`

## 已核验证据

- LF3 唯一 V100/FP64/seed-17 轨迹完成 T0 1200 updates；1200 个 measure batch rolling hash 与冻结身份一致，T0 未构造 physics sampler，P0 因 carrier gate 失败执行 0 步。
- T0 所有值有限，potential maximum-principle 与 phase range 通过，phase maximum 为 `0.991187`，双周期事件、时间、precision、active mass、locality 和 recovery 均通过；两周期 hard recall `0.805842/0.768603<0.90` 是仅有的两个失败项，机器终局为 `LF3_CARRIER_NOT_ESTABLISHED`。
- 相对 LF1-B0，T0 potential、temperature、phase full-medium weighted-MSE ratio 为 `0.241890/0.0633841/0.0330773`。LF3 把 LF1 的过宽 false-positive event 和 LF2 的 cold collapse 收缩为高 precision、质量及时序正确但 boundary support 不完整的 near-pass；这只支持组合级解释。
- 完整回收与远端/本地哈希对账后 GPU 无训练进程，实例已关机并由 SSH `Connection refused` 验证。关机后 local evaluator 中 LF3-T0 event guard 通过，phase ROI RMS `0.0390008`，但 direct `LF_ONLY` 仍为 `0.00657038`，不存在强基线增量。
- 初次 local report 只在 fixed-physics role 键上错误沿用 LF2 命名；`-er1` 修复后实际 checkpoint 标为 LF3-T0，pool/scalar/reference metrics/decision 不变。canonical local adjudication SHA-256 为 `BB45AB4F...B23378`。
- `paper/paper_v23` 已形成英文导师初稿、五张主图、表格、claim audit、复现说明和审稿风险自检；定位为 failure-analysis + bounded solver-recovery，不是正面 PINN 方法稿。
- 云端未读取 fine、extra-fine、frozen evaluator、direct `LF_ONLY` 或 stress；fine/extra-fine 只在关机后本地评价，两份 stress references 始终 sealed/unread。
- LF3 CPU 资格通过：1,603,200 个 medium saved nodes 的 14 类分区完备非空；phase-logit 重构误差 `2.22e-16`，观测 `|q*|=1.8642<4.6052`；1200 个 T0 batch rolling hash 与 LF2 精确相同。资格阶段 optimizer updates、GPU 和 reference/stress I/O 均为 0。
- 快速一手来源闭包在 12 项论文/作者仓库内未发现完整功能同构碰撞，但组成件均有先例；LF3 因而仅以 attributed solver-recovery combination pilot 身份执行。
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

- `VERIFIED`：LF3-T0 恢复了 finite、potential-valid、双周期局域事件，但两周期 hard recall 未达冻结门；carrier 未建立，P0 未触发，candidate 为 none。
- `SUPPORTED_INTERPRETATION`：LF3 组合把主导错误从 LF1 的 diffuse false-positive mass 与 LF2 的 cold collapse 收缩为 high-precision incomplete support；不能归因于 logit teacher 单件。
- `HYPOTHESIS`：剩余 mismatch 主要是 event-boundary coverage，而非冷态、全局过宽或 temporal misplacement；本合同未继续检验。
- `UNKNOWN`：未来是否能建立合格 carrier；label-free physics 能否形成 P0-vs-T0 和 direct `LF_ONLY` Pareto；matched 单因素、多 seed、formal OOD、stress 与投稿级有效性。

以下 LF2 终局裁决作为历史证据保留：

- `VERIFIED`：评价兼容 target measure 显著降低三项全局加权场误差，但把 LF1-B0 的两周期事件载体压回冷态；M0 gate 失败，M1 未触发，candidate 为 none。
- `SUPPORTED_INTERPRETATION`：sampling-measure mismatch 是 LF1 过宽 carrier 的真实因素，但不是建立准确事件载体的充分修复；稀有事件拓扑与全局测度误差仍可发生目标错位。
- `HYPOTHESIS`：若另行授权，下一条最小后备应直接监督 phase latent 或 kinetic RHS，而不是延长 M0、调权重、换 optimizer 或跳过 gate 运行 M1。
- `UNKNOWN`：phase-latent teacher 是否能建立合法两周期 carrier；其后 full physics 是否能在强 `LF_ONLY` 基线容限内产生独立增量；多 seed、stress、formal OOD 与投稿级有效性。

## 当前任务

LF3 已终局完成。当前只保留结果、论文初稿与证据边界，不授权自动推进额外轨迹、seed、ablation、OOD、stress、PJGR/R2、kinetic teacher 或投稿；任何新科研路线需新的明确授权。

## 入口

- [active phase](active_phase.md)
- [live plan](docs/plans/NEXT_ACTIONS.md)
- [ADR 0060](docs/adr/0060-close-phk-v23-lf3-carrier-not-established.md)
- [LF3 terminal closeout](docs/experiment/2026-09-05-phk-v23-lf3-terminal-closeout.md)
- [paper_v23 advisor draft](paper/paper_v23/README.md)
- [ADR 0059 activation](docs/adr/0059-activate-phk-v23-lf3-phase-latent-carrier-pilot.md)
- [LF3 CPU qualification](docs/experiment/2026-09-04-phk-v23-lf3-cpu-qualification.md)
- [ADR 0058](docs/adr/0058-activate-phk-v23-lf2-measure-calibrated-feasible-pinn.md)
- [LF2 terminal closeout](docs/experiment/2026-09-04-phk-v23-lf2-terminal-closeout.md)
- [LF2 CPU qualification](docs/experiment/2026-09-04-phk-v23-lf2-cpu-qualification.md)
- [LF1 terminal closeout](docs/experiment/2026-09-03-phk-v23-lf1-terminal-closeout.md)
