# 当前阶段

- `phase_id`: `PHK_V23_R0C_EFFECTIVE_UPDATE_25_V100`
- `phase_name`: PHK-V2.3 R0C 25-step 有效更新物质性诊断
- `lifecycle_state`: `COMPLETE`
- `blocker_id`: `NONE`
- `claim_status`: `V22R_TERMINAL_NO_GO_PRESERVED_R0C_ADAM_PRECONDITIONING_COMPENSATES_RAW_GRADIENT_NO_METHOD_EVIDENCE`
- `authorization_scope`: `R0C_COMPLETE_FUTURE_RESEARCH_AUTHORIZATION_ONLY`
- `plan_status`: `R0C_COMPLETE`
- `contract_status`: `PHK_V23_R0C_CONTRACT_CONSUMED_COMPLETE`
- `object_status`: `PHK_V21_FIXED_DISCRETIZATION_OBJECT_REUSED_WITHOUT_CONTINUUM_ORACLE_CLAIM`
- `method_selection_status`: `NO_CANDIDATE_ALL_FOUR_ARMS_INELIGIBLE`
- `candidate_status`: `NOT_FROZEN`
- `reference_status`: `R0C_COMPLETE_NO_NOMINAL_OR_STRESS_ACCESS_TWO_STRESS_SEALED_UNREAD`
- `compute_status`: `R0C_ARTIFACTS_RECOVERED_AUTODL_SHUTDOWN_VERIFIED`
- `diagnostic_outcome`: `R0C_ADAM_PRECONDITIONING_COMPENSATES_RAW_GRADIENT`
- `next_research_execution_authorized`: `false`
- `git_authorization`: `R0C_COMMIT_PUSH_NOT_AUTHORIZED`
- `external_publication_authorization`: `NOT_AUTHORIZED`
- `effective_date`: `2026-08-31`

## 当前允许

- 只读审查 R0C 合同、实现、raw artifact、compact artifact、manifest 与 closeout。
- 在不产生新科研事实的前提下维护文档一致性或复现既有机器裁决。

## 当前禁止

- R1/recovery/PJGR、第二次 R0C、seed 改动、warm start、延长到 26/175/1000 steps、checkpoint selection、early stop 或结果导向调参。
- 云端或本地读取 nominal/stress reference、reference-derived masks/metrics/evaluation/teacher probes。
- 把 R0C 写成 competence 恢复、因果 root、方法增益或正向论文证据。
- 作者联系、投稿、投稿系统上传、凭据披露、commit 或 push。

## 当前主张边界

- `VERIFIED`：R0B 的 raw-gradient starvation 可复现；R0C 在 steps 10–19 发现 phase raw-gradient ratio 很小，但 Adam-effective relative-update ratio 约为 `0.59`，机器裁决为 `R0C_ADAM_PRECONDITIONING_COMPENSATES_RAW_GRADIENT`。
- `SUPPORTED_INTERPRETATION`：单纯放大 phase gradient magnitude 不应作为首个 R1a；这不证明更新方向正确，也不恢复 competence。
- `UNKNOWN`：phase 有效更新方向、gradient conflict 与 electrothermal drive 的干预优先级。
- V2.2R `MVP_NO_GO_NO_BASIC_COMPETENCE`、R0A `R0A_INCONCLUSIVE` 与两份 stress seal 均保持原样。

权威决定见 [ADR 0051](docs/adr/0051-activate-phk-v23-r0c-effective-update-25-v100.md)，唯一 live plan 见 [NEXT_ACTIONS.md](docs/plans/NEXT_ACTIONS.md)。

~~~text
PHASE_ID=PHK_V23_R0C_EFFECTIVE_UPDATE_25_V100
BLOCKER_ID=NONE
METHOD_SELECTION_STATUS=NO_CANDIDATE_ALL_FOUR_ARMS_INELIGIBLE
NEXT_RESEARCH_EXECUTION_AUTHORIZED=false
CURRENT_STAGE=R0C_COMPLETE
~~~
