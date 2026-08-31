# 当前阶段

- `phase_id`: `PHK_V23_R0B_FIRST_SWITCH_175_MINIMAL_V2`
- `phase_name`: PHK-V2.3 R0B 首次窗口切换 175-step 最小诊断
- `lifecycle_state`: `COMPLETE`
- `blocker_id`: `NONE`
- `claim_status`: `V22R_TERMINAL_NO_GO_PRESERVED_R0B_GRADIENT_STARVATION_PRECURSOR_NO_METHOD_EVIDENCE`
- `authorization_scope`: `R0B_AUTHORIZATION_CONSUMED_NO_FURTHER_RESEARCH_EXECUTION`
- `plan_status`: `R0B_COMPLETE`
- `contract_status`: `PHK_V23_R0B_MINIMAL_V2_CONSUMED_COMPLETE`
- `object_status`: `PHK_V21_FIXED_DISCRETIZATION_OBJECT_REUSED_WITHOUT_CONTINUUM_ORACLE_CLAIM`
- `method_selection_status`: `NO_CANDIDATE_ALL_FOUR_ARMS_INELIGIBLE`
- `candidate_status`: `NOT_FROZEN`
- `reference_status`: `CLOUD_REFERENCE_BLIND_NOMINAL_LOCAL_NON_VOTING_COMPLETE_STRESS_SEALED_UNREAD`
- `compute_status`: `R0B_175_STEPS_COMPLETE_ARTIFACTS_RECOVERED_AUTODL_SHUTDOWN_VERIFIED`
- `diagnostic_outcome`: `R0B_PRECURSOR_CANDIDATE_IDENTIFIED_GRADIENT_STARVATION`
- `next_research_execution_authorized`: `false`
- `git_authorization`: `CURRENT_R0B_SELECTIVE_COMMIT_AND_PUSH_AUTHORIZED`
- `external_publication_authorization`: `NOT_AUTHORIZED`
- `effective_date`: `2026-08-31`

## 当前允许

- 只读审查 [R0B closeout](docs/experiment/2026-08-31-phk-v23-r0b-first-switch-175-closeout.md)、compact artifact、manifest、raw run 与既有 terminal evidence。
- 完成本阶段剩余的文档一致性、ledger、测试、选择性 commit/push；继续排除其他会话或用户的未提交变更。
- 在不执行科研计算的前提下，草拟一个以 phase-head gradient materiality 为唯一原子干预轴的 R1a `PLAN_ONLY` 方案；该草案不产生授权。

## 当前禁止

- 第二次 R0B、seed 改动、176/1000-step 延长、warm start、checkpoint selection、early stop、recovery intervention、R1、PJGR、额外模块或结果导向调参。
- 启动 AutoDL/GPU、运行训练、forward/backward 诊断、factorial、teacher probe 或任何新科学计算。
- 在云端上传或读取 nominal/stress reference、reference-derived masks/metrics/evaluation/teacher probes。
- 打开任一 stress field/metric，创建 candidate freeze、confirmation 或 formal OOD。
- 把 temporal precursor candidate 表述为因果 root、competence 恢复、方法增益或正向论文结果。
- 联系作者、提交期刊、上传投稿系统或披露凭据。

## 当前主张边界

- `VERIFIED`：R0B 在 reference-blind 单轨迹中识别 `GRADIENT_STARVATION` 为 step 10 起、step 25 确认的最早持续前兆；随后还有 gradient conflict 与 electrothermal deficit。它不是因果 root。
- `VERIFIED`：175-step prefix 仍未通过两周期事件 competence；本地 nominal 结果仅为 non-voting appendix。V2.2R 四臂 terminal No-Go 与 R0A `R0A_INCONCLUSIVE` 保持有效。
- `SUPPORTED_INTERPRETATION`：若未来另行授权 R1a，最有信息增益的单一轴是 phase-head gradient materiality/balancing，而不是先加入 PJGR、换 seed 或延长预算。
- `HYPOTHESIS`：恢复 phase-head gradient materiality 可能使后续 gradient conflict 与 electrothermal deficit 变得可辨识或可修复。
- `UNKNOWN`：gradient starvation 的充分因果性、任何 R1 干预能否恢复 competence、任何方法能否获得增量，以及 stress/formal 结果。

权威决定见 [ADR 0050](docs/adr/0050-activate-phk-v23-r0b-first-switch-175-minimal-v2.md)，唯一 live plan 见 [NEXT_ACTIONS.md](docs/plans/NEXT_ACTIONS.md)。

~~~text
PHASE_ID=PHK_V23_R0B_FIRST_SWITCH_175_MINIMAL_V2
BLOCKER_ID=NONE
METHOD_SELECTION_STATUS=NO_CANDIDATE_ALL_FOUR_ARMS_INELIGIBLE
NEXT_RESEARCH_EXECUTION_AUTHORIZED=false
CURRENT_STAGE=R0B_COMPLETE_NO_FURTHER_EXECUTION_AUTHORIZED
~~~
