# 项目状态

更新时间：2026-09-02

- `phase_id`: `PHK_V23_R1X_BOUNDED_CLEAN_COUPLING_CAMPAIGN_EXECUTE`
- `lifecycle_state`: `ACTIVE`
- `blocker_id`: `NONE`
- `claim_status`: `V22R_TERMINAL_NO_GO_AND_R1A_NO_COMPETENCE_PRESERVED_R1X_E1_PENDING`
- `next_research_execution_authorized`: `true`
- `authorization_scope`: `MAX_THREE_NON_VOTING_EXPLORATIONS_AND_ONE_CONDITIONAL_FROZEN_CONFIRMATION`
- `candidate_status`: `NOT_FROZEN`
- `object_status`: `PHK_V21_FIXED_DISCRETIZATION_BENCHMARK_REUSED`
- `reference_status`: `CLOUD_REFERENCE_BLIND_LOCAL_NOMINAL_AFTER_SHUTDOWN_STRESS_UNREAD_SEALED`
- `implementation_status`: `R1X_CONTRACT_AND_E1_IMPLEMENTATION_IN_PROGRESS`
- `method_selection_status`: `NO_CANDIDATE_ALL_FOUR_ARMS_INELIGIBLE`
- `compute_status`: `E1_NOT_STARTED_LOCAL_PREFLIGHT_PENDING`
- `contract_status`: `PHK_V23_R1X_CONTRACTS_FROZEN_ACTIVE`
- `paper_status`: `EXISTING_BOUNDED_NEGATIVE_ADVISOR_DRAFT_PRESERVED`
- `diagnostic_outcome`: `R1X_CAMPAIGN_ACTIVE_E1_PENDING`

## 已核验证据

- PHK-V2.2R 四臂结果继续为 `MVP_NO_GO_NO_BASIC_COMPETENCE`。
- R0A=`R0A_INCONCLUSIVE`；R0B 仅识别 gradient-starvation temporal precursor；R0C 表明 Adam 预条件补偿 raw gradient；R1a=`R1A_CONFIG_RAW_NO_COMPETENCE`。
- R1a 已证明 standard ConFIG 的四组方向机制按定义工作且显著降低 PDE loss，但 phase activity 仍为零、两周期事件完全缺失。
- 两份 stress references 继续 sealed/unread。

## 当前待回答问题

避免随机 phase-head 污染早期反馈，先建立覆盖两周期的电热驱动，再通过 cold-state-to-learned-phase homotopy 恢复完整耦合，是否能产生并从 scratch 确认 two-cycle event competence？

## 入口

- [active phase](active_phase.md)
- [live plan](docs/plans/NEXT_ACTIONS.md)
- [ADR 0053](docs/adr/0053-activate-phk-v23-r1x-bounded-clean-coupling-campaign.md)
- [R1a closeout](docs/experiment/2026-08-31-phk-v23-r1a-config-closeout.md)
- [V2.2R terminal closeout](docs/experiment/2026-08-30-phk-v22r-v11-nominal-terminal-closeout.md)
