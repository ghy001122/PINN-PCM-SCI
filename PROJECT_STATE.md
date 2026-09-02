# 项目状态

更新时间：2026-09-03

- `phase_id`: `PHK_V23_R1X_BOUNDED_CLEAN_COUPLING_CAMPAIGN_EXECUTE`
- `lifecycle_state`: `ACTIVE`
- `blocker_id`: `AUTODL_RESTART_REQUIRED_FOR_E2_TOP_DIRICHLET_HARD_LIFT`
- `claim_status`: `V22R_TERMINAL_NO_GO_AND_R1A_NO_COMPETENCE_PRESERVED_R1X_E1_ET_NOT_READY_NO_COMPETENCE`
- `next_research_execution_authorized`: `true`
- `authorization_scope`: `RUN_FROZEN_E2_TOP_DIRICHLET_HARD_LIFT_AFTER_AUTODL_RESTART`
- `candidate_status`: `NOT_FROZEN`
- `object_status`: `PHK_V21_FIXED_DISCRETIZATION_BENCHMARK_REUSED`
- `reference_status`: `CLOUD_REFERENCE_BLIND_LOCAL_NOMINAL_AFTER_SHUTDOWN_STRESS_UNREAD_SEALED`
- `implementation_status`: `R1X_E1_COMPLETE_E2_TOP_DIRICHLET_HARD_LIFT_SELECTED`
- `method_selection_status`: `NO_CANDIDATE_ALL_FOUR_ARMS_INELIGIBLE`
- `compute_status`: `AUTODL_SHUTDOWN_VERIFIED_AWAITING_RESTART_FOR_E2_TOP_DIRICHLET_HARD_LIFT`
- `contract_status`: `PHK_V23_R1X_CAMPAIGN_AMENDED_ACTIVE`
- `paper_status`: `EXISTING_BOUNDED_NEGATIVE_ADVISOR_DRAFT_PRESERVED`
- `diagnostic_outcome`: `E1_ET_NOT_READY`

## 已核验证据

- PHK-V2.2R 四臂结果继续为 `MVP_NO_GO_NO_BASIC_COMPETENCE`。
- R0A=`R0A_INCONCLUSIVE`；R0B 仅识别 gradient-starvation temporal precursor；R0C 表明 Adam 预条件补偿 raw gradient；R1a=`R1A_CONFIG_RAW_NO_COMPETENCE`。
- R1a 已证明 standard ConFIG 的四组方向机制按定义工作且显著降低 PDE loss，但 phase activity 仍为零、两周期事件完全缺失。
- 历史两次 R1X E1 工程启动均在模型构造前以 0 update 终止；传递部署依赖随后闭合并通过 isolated preflight。
- 修复后的 E1 已在 V100/FP64/seed 17 上从 scratch 完成 300 个 warm-up updates，构成 1/3 条 non-voting exploration；五个 readiness checkpoints 均未通过，状态为 `E1_ET_NOT_READY`。
- E1 checkpoint、prediction、telemetry、log、manifest 与 summary 已完整回收且远端/本地 hash 一致；AutoDL 已关机，SSH probe 为 `Connection refused`。
- 关机后 frozen nominal evaluator 确认 phase activity 为 0、两个周期各失败 event/ROI peak/recovery；机器树唯一选择 `E2_TOP_DIRICHLET_HARD_LIFT`。
- 两份 stress references 继续 sealed/unread。

## 未回答的科学问题

top Dirichlet hard lift 能否在 E2 warm-up 中建立同时覆盖 W1/W3 ROI 的热激活与 cold kinetic drive，并进一步进入 coupling ramp/full closure、恢复 two-cycle event competence？答案仍为 `UNKNOWN`。

## 入口

- [active phase](active_phase.md)
- [live plan](docs/plans/NEXT_ACTIONS.md)
- [ADR 0053](docs/adr/0053-activate-phk-v23-r1x-bounded-clean-coupling-campaign.md)
- [ADR 0054](docs/adr/0054-resume-r1x-after-verified-engineering-repair.md)
- [R1X E1 closeout](docs/experiment/2026-09-03-phk-v23-r1x-e1-et-not-ready-closeout.md)
- [R1X engineering-blocked closeout](docs/experiment/2026-09-02-phk-v23-r1x-engineering-blocked-closeout.md)
- [R1a closeout](docs/experiment/2026-08-31-phk-v23-r1a-config-closeout.md)
- [V2.2R terminal closeout](docs/experiment/2026-08-30-phk-v22r-v11-nominal-terminal-closeout.md)
