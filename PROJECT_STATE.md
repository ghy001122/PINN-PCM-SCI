# 项目状态

更新时间：2026-08-31

- `phase_id`: `PHK_V23_R1A_CONFIG_COMPETENCE_RECOVERY`
- `lifecycle_state`: `AWAITING`
- `blocker_id`: `AUTODL_ENDPOINT_OR_PRICE`
- `claim_status`: `V22R_TERMINAL_NO_GO_PRESERVED_R1A_INFRASTRUCTURE_BLOCKED_NO_SCIENTIFIC_RUN`
- `next_research_execution_authorized`: `false`
- `authorization_scope`: `R1A_AUTHORIZATION_UNCONSUMED_AWAIT_LIVE_AUTODL_ENDPOINT_AND_PRICE`
- `candidate_status`: `NOT_FROZEN`
- `object_status`: `PHK_V21_FIXED_DISCRETIZATION_BENCHMARK_REUSED`
- `reference_status`: `CLOUD_REFERENCE_BLIND_LOCAL_NOMINAL_AFTER_SHUTDOWN_STRESS_UNREAD_SEALED`
- `implementation_status`: `R1A_CONTRACT_IMPLEMENTATION_TESTS_AND_DEPLOYMENT_BUNDLE_READY`
- `method_selection_status`: `NO_CANDIDATE_ALL_FOUR_ARMS_INELIGIBLE`
- `compute_status`: `GPU_RUN_NOT_CONSUMED_SSH_CONNECTION_REFUSED`
- `contract_status`: `PHK_V23_R1A_CONFIG_CONTRACT_FROZEN_ACTIVE`
- `paper_status`: `ENGLISH_BOUNDED_NEGATIVE_ADVISOR_DRAFT_FIVE_FIGURE_PACKAGE_VALID`
- `diagnostic_outcome`: `R1A_BUDGET_OR_INFRASTRUCTURE_BLOCKED`

## 已核验证据

- PHK-V2.2R 四臂继续为 `MVP_NO_GO_NO_BASIC_COMPETENCE`；旧 run、evaluation、decision、closeout 和论文包不回写。
- R0B 的 gradient-starvation temporal precursor 与 R0C 的 `R0C_ADAM_PRECONDITIONING_COMPENSATES_RAW_GRADIENT` 均保持有效。
- R1a 只把旧 summed-loss backward 替换为透明归因的标准 ConFIG 四组梯度合成；物理对象、模型、采样、预算、Adam、裁剪和 evaluator 均冻结。
- 两份 stress references 继续 sealed/unread。

## 当前待回答问题

一次冻结的 standard-ConFIG shared solver backbone 能否使 seed-17 STRONG_RAW 通过全部 two-cycle competence guards。当前无科学结果：SSH 连续两次 `Connection refused`，唯一 run 未消耗；需用户提供已启动实例的 SSH endpoint 和页面实时价格后才能继续。

## 入口

- [active phase](active_phase.md)
- [live plan](docs/plans/NEXT_ACTIONS.md)
- [ADR 0052](docs/adr/0052-activate-phk-v23-r1a-config-competence-recovery.md)
- [R0C closeout](docs/experiment/2026-08-31-phk-v23-r0c-effective-update-25-closeout.md)
- [V2.2R terminal closeout](docs/experiment/2026-08-30-phk-v22r-v11-nominal-terminal-closeout.md)
