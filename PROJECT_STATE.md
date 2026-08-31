# 项目状态

更新时间：2026-08-31

- `phase_id`: `PHK_V23_R0B_FIRST_SWITCH_175_MINIMAL_V2`
- `lifecycle_state`: `COMPLETE`
- `blocker_id`: `NONE`
- `claim_status`: `V22R_TERMINAL_NO_GO_PRESERVED_R0B_GRADIENT_STARVATION_PRECURSOR_NO_METHOD_EVIDENCE`
- `authorization_scope`: `R0B_AUTHORIZATION_CONSUMED_NO_FURTHER_RESEARCH_EXECUTION`
- `candidate_status`: `NOT_FROZEN`
- `object_status`: `PHK_V21_FIXED_DISCRETIZATION_BENCHMARK_REUSED`
- `reference_status`: `CLOUD_REFERENCE_BLIND_NOMINAL_LOCAL_NON_VOTING_COMPLETE_TWO_STRESS_UNREAD_SEALED`
- `implementation_status`: `R0B_MINIMAL_V2_IMPLEMENTED_EXECUTED_AND_CLOSED`
- `method_selection_status`: `NO_CANDIDATE_ALL_FOUR_ARMS_INELIGIBLE`
- `compute_status`: `R0B_175_STEPS_COMPLETE_ARTIFACTS_RECOVERED_AUTODL_SHUTDOWN_CONFIRMED`
- `contract_status`: `PHK_V23_R0B_MINIMAL_V2_CONSUMED_COMPLETE`
- `paper_status`: `ENGLISH_BOUNDED_NEGATIVE_ADVISOR_DRAFT_FIVE_FIGURE_PACKAGE_VALID`
- `cloud_budget_cny_hard_cap`: `150`
- `cloud_estimated_cumulative_spend_cny_before_r0b`: `4.81005806532574`
- `cloud_estimated_incremental_r0b_cost_cny`: `0.09727051790253155`
- `cloud_estimated_cumulative_spend_cny_after_r0b`: `4.907328583228272`
- `diagnostic_outcome`: `R0B_PRECURSOR_CANDIDATE_IDENTIFIED`
- `primary_precursor_candidate`: `GRADIENT_STARVATION`
- `root_cause_status`: `CAUSAL_ROOT_NOT_IDENTIFIED_TEMPORAL_PRECURSOR_ONLY`
- `next_recommendation`: `R1A_PHASE_HEAD_GRADIENT_MATERIALITY_PLAN_ONLY_NOT_AUTHORIZED`
- `next_research_execution_authorized`: `false`

## VERIFIED

- source commit `8d072e2ece0668583adad4b3cefff3e978436f05` 已在 `Tesla V100-PCIE-32GB` 完成唯一一次 seed-17/FP64/STRONG_RAW scratch replay：175 canonical updates、schedule denominator 1000、cloud shadow steps 0。
- wall time 为 `186.262694 s`，按 `1.88 CNY/h` 估算增量费用 `0.0972705 CNY`；全部受控产物已回收并逐哈希核验。checkpoint update 为 175，内嵌 training config updates 为 1000。
- AutoDL 在回收核验后立即 shutdown，随后 SSH 探针返回 `Connection refused`。
- reference-blind machine decision 固定 `GRADIENT_STARVATION` 为最早持续前兆（step 10/25）；gradient conflict 为 step 75/100，electrothermal deficit 为 step 110/120。未识别因果 root。
- primary 不是 `SWITCH_INDUCED`，因此 factorial 固定 `FACTORIAL_NOT_RUN_NOT_NEEDED`。nominal reference 只在 decision 写入后本地打开，appendix 仍显示两周期 event missing，且不参与裁决。
- R0A 仍为 `R0A_INCONCLUSIVE`，V2.2R 四臂仍为 `MVP_NO_GO_NO_BASIC_COMPETENCE`；stress references 继续 sealed/unread。

## NEXT BUT NOT AUTHORIZED

- 只允许只读审查或制定一个 phase-head gradient materiality/balancing 的 R1a 原子干预 `PLAN_ONLY`；训练、GPU、R1、PJGR 与 stress 均需新的用户明确授权。

## UNKNOWN

- gradient starvation 是否为充分因果原因，以及哪个 loss、参数化或 optimizer interaction 造成该前兆。
- 任何 recovery/PJGR/新方法、其他 seed、更长预算、stress 或 formal OOD 的结果；这些均不在当前授权内。

## 当前入口

- [active phase](active_phase.md)
- [live plan](docs/plans/NEXT_ACTIONS.md)
- [ADR 0050](docs/adr/0050-activate-phk-v23-r0b-first-switch-175-minimal-v2.md)
- [R0B cloud run card](cloud/phk_v23_r0b_autodl/README.md)
- [R0B closeout](docs/experiment/2026-08-31-phk-v23-r0b-first-switch-175-closeout.md)
- [R0B compact artifact](docs/experiment/artifacts/20260831T095149-phk-v23-r0b-first-switch-175-8d072e2.json)
- [R0A closeout](docs/experiment/2026-08-30-phk-v23-r0a-cpu-diagnostics-closeout.md)
- [V2.2R terminal closeout](docs/experiment/2026-08-30-phk-v22r-v11-nominal-terminal-closeout.md)

PHK-V2.1、PHK-V2、V1 与更早 No-Go 均保持原样。
