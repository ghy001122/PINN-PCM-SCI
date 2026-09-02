# 当前阶段

- `phase_id`: `PHK_V23_R1X_BOUNDED_CLEAN_COUPLING_CAMPAIGN_EXECUTE`
- `phase_name`: PHK-V2.3 R1X 有界 clean-coupling campaign
- `lifecycle_state`: `ACTIVE`
- `blocker_id`: `AUTODL_INSTANCE_OFFLINE_CONNECTION_REFUSED`
- `claim_status`: `V22R_TERMINAL_NO_GO_AND_R1A_NO_COMPETENCE_PRESERVED_R1X_E1_NOT_STARTED_INFRASTRUCTURE_WAIT`
- `next_research_execution_authorized`: `true`
- `authorization_scope`: `MAX_THREE_NON_VOTING_EXPLORATIONS_AND_ONE_CONDITIONAL_FROZEN_CONFIRMATION`
- `plan_status`: `R1X_E1_AWAITING_AUTODL_RESTART`
- `contract_status`: `PHK_V23_R1X_CONTRACTS_FROZEN_ACTIVE`
- `object_status`: `PHK_V21_FIXED_DISCRETIZATION_OBJECT_REUSED_WITHOUT_CONTINUUM_ORACLE_CLAIM`
- `method_selection_status`: `NO_CANDIDATE_ALL_FOUR_ARMS_INELIGIBLE`
- `candidate_status`: `NOT_FROZEN`
- `reference_status`: `CLOUD_REFERENCE_BLIND_LOCAL_NOMINAL_ONLY_AFTER_SHUTDOWN_STRESS_SEALED_UNREAD`
- `compute_status`: `NO_R1X_GPU_RUN_ENDPOINT_CONNECTION_REFUSED`
- `diagnostic_outcome`: `AWAITING_AUTODL_RESTART_CAMPAIGN_AUTHORIZATION_REMAINS_ACTIVE`
- `git_authorization`: `SELECTIVE_R1X_COMMIT_PUSH_MAIN_AUTHORIZED`
- `external_publication_authorization`: `NOT_AUTHORIZED`
- `effective_date`: `2026-09-02`

## 当前唯一允许的科研动作

按冻结 machine tree 实施最多三条 non-voting exploration；首条完整 competence signal 后最多执行一条 from-scratch frozen confirmation。每条云端轨迹必须 reference-blind，回收核验后立即关闭 AutoDL，关机验证后才允许本地 nominal development 评价。

## 明确禁止

- 第四条 exploration、第二条 confirmation、seed 变更或继承上一轨迹状态；
- stress 读取/预测、PJGR、R2、low-fidelity、benchmark/PDE/reference/evaluator 改写；
- 投稿、对外披露或自动扩展本 campaign。

## 证据边界

- `VERIFIED`: V2.2R terminal No-Go、R0A、R0B、R0C 与 R1a `R1A_CONFIG_RAW_NO_COMPETENCE` 保持不变。
- `SUPPORTED_INTERPRETATION`: conflict-resolution-only 不足以恢复当前 strong-raw competence。
- `HYPOTHESIS`: clean cold-state electrothermal warm-up、coupling ramp 和完整 joint closure 可能避免过早进入冷态兼容解。
- `UNKNOWN`: R1X 是否恢复 competence、是否触发 E2/E3/confirmation，以及所有 stress、其他 seed 和 R2 结果。

权威决定见 [ADR 0053](docs/adr/0053-activate-phk-v23-r1x-bounded-clean-coupling-campaign.md)，唯一 live plan 见 [NEXT_ACTIONS.md](docs/plans/NEXT_ACTIONS.md)，本次基础设施阻塞见 [E1 preflight record](docs/experiment/2026-09-02-phk-v23-r1x-e1-preflight-blocked.md)。

~~~text
PHASE_ID=PHK_V23_R1X_BOUNDED_CLEAN_COUPLING_CAMPAIGN_EXECUTE
BLOCKER_ID=AUTODL_INSTANCE_OFFLINE_CONNECTION_REFUSED
METHOD_SELECTION_STATUS=NO_CANDIDATE_ALL_FOUR_ARMS_INELIGIBLE
NEXT_RESEARCH_EXECUTION_AUTHORIZED=true
CURRENT_STAGE=AWAITING_AUTODL_RESTART_CAMPAIGN_AUTHORIZATION_REMAINS_ACTIVE
~~~
