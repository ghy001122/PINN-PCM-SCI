# 项目状态

更新时间：2026-09-03

- `phase_id`: `PHK_V23_LF0_EXACT_TOP_WARMSTART_ATTRIBUTION_EXECUTE`
- `lifecycle_state`: `COMPLETE`
- `blocker_id`: `NONE`
- `claim_status`: `V22R_R1X_C0_PRESERVED_LF0_NUMERICAL_OR_IDENTITY_INVALID_NO_METHOD_EVIDENCE`
- `next_research_execution_authorized`: `false`
- `authorization_scope`: `NONE_LF0_CAMPAIGN_CONSUMED`
- `candidate_status`: `NONE`
- `object_status`: `PHK_V21_FIXED_DISCRETIZATION_BENCHMARK_REUSED`
- `reference_status`: `MEDIUM_METHOD_INPUT_FINE_EXTRA_LOCAL_DEVELOPMENT_ONLY_STRESS_SEALED_UNREAD`
- `implementation_status`: `LF0_IMPLEMENTED_EXECUTED_AND_CLOSED`
- `method_selection_status`: `NO_CANDIDATE_LF0_INVALID`
- `compute_status`: `A_AND_B_COMPLETE_C_NOT_RUN_INSTANCE_RETAINED_IDLE_BY_USER_OVERRIDE`
- `contract_status`: `LF0_FOUR_CONTRACTS_CONSUMED_AND_CLOSED`
- `paper_status`: `EXISTING_BOUNDED_NEGATIVE_ADVISOR_DRAFT_PRESERVED`
- `diagnostic_outcome`: `LF0_NUMERICAL_OR_IDENTITY_INVALID`
- `next_recommendation`: `INVALID_RUN_REQUIRES_USER_REVIEW_NO_AUTOMATIC_SCIENTIFIC_RETRY`

## 已核验证据

- Run A：1200-step exact-top scratch PINN 完成，potential validity 通过，但 `phase_max=0.0299932`、activity=0，两周期各失败 event、ROI peak 与 recovery。
- Run B：800-step low-fidelity-only、200-step anchor、1000-step physics closure 完成；A/B 的 1200 个 physics batches 逐步一致。
- B0 `LF_DATA_ONLY` 达到 `phase_max=0.477584`，但 W1/W3 potential maximum-principle guard 失败；B final potential 合法，却回到 `phase_max=0.0299932` 且仍无事件。
- direct medium `LF_ONLY` comparator 本身通过两周期 competence，说明失败不是低保真 carrier 缺少事件，而是当前网络转移与 closure 未能有效保留事件。
- 冻结优先级给出 `LF0_NUMERICAL_OR_IDENTITY_INVALID`，C 未触发，无 candidate、无方法增量证据。
- 两次正式运行合计 3200 updates、`0.394038 GPU h`、估算 `0.740791 CNY`；stress 未读取。

## 当前任务

LF0 已收口。下一研究动作必须由用户在审查无效原因后重新授权；当前不得自动重试 B、运行 C、修改门槛、读取 stress 或转入 R2/PJGR。

## 入口

- [active phase](active_phase.md)
- [live plan](docs/plans/NEXT_ACTIONS.md)
- [ADR 0056](docs/adr/0056-activate-phk-v23-lf0-exact-top-warmstart-attribution.md)
- [LF0 terminal closeout](docs/experiment/2026-09-03-phk-v23-lf0-terminal-closeout.md)
- [LF0 CPU qualification](docs/experiment/2026-09-03-phk-v23-lf0-cpu-qualification.md)
- [C0 closeout](docs/experiment/2026-09-03-phk-v23-c0-reference-discrete-strongform-compatibility-closeout.md)
