# 项目状态

更新时间：2026-08-31

- `phase_id`: `PHK_V23_R0B_FIRST_SWITCH_175_MINIMAL_V2`
- `lifecycle_state`: `ACTIVE`
- `blocker_id`: `NONE`
- `claim_status`: `V22R_TERMINAL_NO_GO_PRESERVED_R0B_REFERENCE_BLIND_REPLAY_PENDING`
- `authorization_scope`: `ONE_R0B_V100_REPLAY_RECOVERY_SHUTDOWN_LOCAL_ADJUDICATION_AND_CLOSEOUT`
- `candidate_status`: `NOT_FROZEN`
- `object_status`: `PHK_V21_FIXED_DISCRETIZATION_BENCHMARK_REUSED`
- `reference_status`: `CLOUD_REFERENCE_BLIND_NOMINAL_POSTHOC_PENDING_TWO_STRESS_UNREAD_SEALED`
- `implementation_status`: `R0B_MINIMAL_V2_IMPLEMENTATION_AND_PREFLIGHT_IN_PROGRESS`
- `method_selection_status`: `NO_CANDIDATE_ALL_FOUR_ARMS_INELIGIBLE`
- `compute_status`: `GPU_ON_IDLE_PRECHECK_VALID_ONE_RUN_NOT_STARTED`
- `contract_status`: `PHK_V23_R0B_MINIMAL_V2_FROZEN_BEFORE_RESULTS`
- `paper_status`: `ENGLISH_BOUNDED_NEGATIVE_ADVISOR_DRAFT_FIVE_FIGURE_PACKAGE_VALID`
- `cloud_budget_cny_hard_cap`: `150`
- `cloud_estimated_cumulative_spend_cny_before_r0b`: `4.81005806532574`
- `diagnostic_outcome`: `PENDING`
- `root_cause_status`: `CAUSAL_ROOT_CLAIM_FORBIDDEN_PRECURSOR_PENDING`
- `next_recommendation`: `RUN_EXACTLY_ONE_R0B_MINIMAL_V2_THEN_STOP`
- `next_research_execution_authorized`: `true`

## VERIFIED

- 当前用户明确授权完整 R0B 与 GPU 运行，并要求付费产物回收完成后立即关闭 AutoDL。
- preflight 时本地 HEAD、main 与远端跟踪分支均为 `0f561b58cb019ab3eb52bb4a0795f8b64f5e7e94`；既有无关 dirty 保留且不进入本阶段白名单。
- AutoDL live preflight 显示 `Tesla V100-PCIE-32GB`、0 MiB、0% utilization 且无训练进程；该快照只证明 preflight 时状态。
- R0A 仍为 `R0A_INCONCLUSIVE`：final static conflict、低 T/phase 与零正 growth 共同存在，但 teacher contrasts 未过 10× 门。
- V2.2R 四臂仍为 `MVP_NO_GO_NO_BASIC_COMPETENCE`；stress references 继续 sealed/unread。

## PENDING

- R0B local gates、source commit、唯一 175-step cloud replay、产物回收/关机、reference-blind adjudication、条件性 CPU factorial、nominal non-voting appendix 与 closeout。

## UNKNOWN

- 低 electrothermal drive、boundary conditioning、phase output conditioning、gradient starvation/conflict 或首次窗口切换中哪一项最早获得持续支持。
- 任何 recovery/PJGR/新方法、其他 seed、更长预算、stress 或 formal OOD 的结果；这些均不在本阶段授权内。

## 当前入口

- [active phase](active_phase.md)
- [live plan](docs/plans/NEXT_ACTIONS.md)
- [ADR 0050](docs/adr/0050-activate-phk-v23-r0b-first-switch-175-minimal-v2.md)
- [R0B cloud run card](cloud/phk_v23_r0b_autodl/README.md)
- [R0A closeout](docs/experiment/2026-08-30-phk-v23-r0a-cpu-diagnostics-closeout.md)
- [V2.2R terminal closeout](docs/experiment/2026-08-30-phk-v22r-v11-nominal-terminal-closeout.md)

PHK-V2.1、PHK-V2、V1 与更早 No-Go 均保持原样。
