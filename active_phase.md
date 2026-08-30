# 当前阶段

- `phase_id`: `PHK_V23_R0B_FIRST_SWITCH_175_MINIMAL_V2`
- `phase_name`: PHK-V2.3 R0B 首次窗口切换 175-step 最小诊断
- `lifecycle_state`: `ACTIVE`
- `blocker_id`: `NONE`
- `claim_status`: `V22R_TERMINAL_NO_GO_PRESERVED_R0B_REFERENCE_BLIND_REPLAY_PENDING`
- `authorization_scope`: `ONE_R0B_V100_REPLAY_RECOVERY_SHUTDOWN_LOCAL_ADJUDICATION_AND_CLOSEOUT`
- `plan_status`: `R0B_AUTHORIZED_ACTIVE`
- `contract_status`: `PHK_V23_R0B_MINIMAL_V2_FROZEN_BEFORE_RESULTS`
- `object_status`: `PHK_V21_FIXED_DISCRETIZATION_OBJECT_REUSED_WITHOUT_CONTINUUM_ORACLE_CLAIM`
- `method_selection_status`: `NO_CANDIDATE_ALL_FOUR_ARMS_INELIGIBLE`
- `candidate_status`: `NOT_FROZEN`
- `reference_status`: `CLOUD_REFERENCE_BLIND_NOMINAL_LOCAL_POSTHOC_ONLY_STRESS_SEALED_UNREAD`
- `compute_status`: `ONE_V100_175_CANONICAL_STEP_REPLAY_AUTHORIZED_NOT_YET_EXECUTED`
- `diagnostic_outcome`: `PENDING`
- `next_research_execution_authorized`: `true`
- `git_authorization`: `CURRENT_R0B_SELECTIVE_COMMIT_AND_PUSH_AUTHORIZED`
- `external_publication_authorization`: `NOT_AUTHORIZED`
- `effective_date`: `2026-08-31`

## 当前允许

- 为 [R0B minimal-v2 合同](configs/phk_v23/program_contract_r0b_minimal_v2.json) 完成最小代码、focused tests、run card 与权威文档对齐。
- 在本地门禁全过后，使用当前已启动的 `Tesla V100-PCIE-32GB` 执行一次 FP64、seed-17、STRONG_RAW scratch、175 canonical-step reference-blind replay。
- 回收并核验 checkpoint、prediction、telemetry、transition bundle、log、manifest、environment 与 summary；随后立即关闭 AutoDL 并确认不可连接。
- 关机后先做本地 reference-blind adjudication；仅在 `SWITCH_INDUCED` 时做零 optimizer-step CPU gradient factorial；最后生成 nominal non-voting appendix。
- 选择性 commit/push 本次 R0B 白名单文件，继续排除其他会话或用户的未提交变更。

## 当前禁止

- 第二次 R0B、seed 改动、176/1000-step 延长、warm start、checkpoint selection、early stop、recovery intervention、R1、PJGR、额外模块或结果导向调参。
- 在云端上传或读取 nominal/stress reference、reference-derived masks/metrics/evaluation/teacher probes。
- 打开任一 stress field/metric，创建 candidate freeze、confirmation 或 formal OOD。
- 把 temporal precursor candidate 表述为因果 root、competence 恢复、方法增益或正向论文结果。
- 联系作者、提交期刊、上传投稿系统或披露凭据。

## 当前主张边界

- `VERIFIED`：V2.2R 四臂 terminal No-Go 与 R0A `R0A_INCONCLUSIVE` 保持有效。
- `SUPPORTED_INTERPRETATION`：首次窗口切换前后的动态 telemetry 是区分低电热、phase output conditioning、gradient starvation/conflict 与 switch-associated shock 的最短高信息增益路径。
- `HYPOTHESIS`：这些机制中可能存在一个更早的 persistent precursor；本阶段尚未产生运行证据。
- `UNKNOWN`：哪一项最早、任何 R1 干预能否恢复 competence、任何方法能否获得增量，以及 stress/formal 结果。

权威决定见 [ADR 0050](docs/adr/0050-activate-phk-v23-r0b-first-switch-175-minimal-v2.md)，唯一 live plan 见 [NEXT_ACTIONS.md](docs/plans/NEXT_ACTIONS.md)。

~~~text
PHASE_ID=PHK_V23_R0B_FIRST_SWITCH_175_MINIMAL_V2
BLOCKER_ID=NONE
METHOD_SELECTION_STATUS=NO_CANDIDATE_ALL_FOUR_ARMS_INELIGIBLE
NEXT_RESEARCH_EXECUTION_AUTHORIZED=true
CURRENT_STAGE=R0B_LOCAL_IMPLEMENTATION_AND_PREFLIGHT
~~~
