# 当前阶段

- `phase_id`: `PHK_V23_R1A_CONFIG_COMPETENCE_RECOVERY`
- `phase_name`: PHK-V2.3 R1a ConFIG 基本能力恢复
- `lifecycle_state`: `AWAITING`
- `blocker_id`: `AUTODL_ENDPOINT_OR_PRICE`
- `claim_status`: `V22R_TERMINAL_NO_GO_PRESERVED_R1A_INFRASTRUCTURE_BLOCKED_NO_SCIENTIFIC_RUN`
- `authorization_scope`: `R1A_AUTHORIZATION_UNCONSUMED_AWAIT_LIVE_AUTODL_ENDPOINT_AND_PRICE`
- `plan_status`: `R1A_PREFLIGHT_BLOCKED`
- `contract_status`: `PHK_V23_R1A_CONFIG_CONTRACT_FROZEN_ACTIVE`
- `object_status`: `PHK_V21_FIXED_DISCRETIZATION_OBJECT_REUSED_WITHOUT_CONTINUUM_ORACLE_CLAIM`
- `method_selection_status`: `NO_CANDIDATE_ALL_FOUR_ARMS_INELIGIBLE`
- `candidate_status`: `NOT_FROZEN`
- `reference_status`: `CLOUD_REFERENCE_BLIND_LOCAL_NOMINAL_EVALUATION_ONLY_AFTER_SHUTDOWN_STRESS_SEALED_UNREAD`
- `compute_status`: `LOCAL_GATES_PASS_GPU_RUN_NOT_CONSUMED_SSH_CONNECTION_REFUSED`
- `diagnostic_outcome`: `R1A_BUDGET_OR_INFRASTRUCTURE_BLOCKED`
- `next_research_execution_authorized`: `false`
- `git_authorization`: `SELECTIVE_R1A_COMMIT_PUSH_AUTHORIZED`
- `external_publication_authorization`: `NOT_AUTHORIZED`
- `effective_date`: `2026-08-31`

## 当前唯一允许的科研动作

合同、实现、测试与部署 bundle 已通过本地门禁，但已核验的 AutoDL SSH 入口连续两次返回 `Connection refused`，且无法取得当前实例页面的实时价格。唯一科学 run 尚未消耗。只有用户启动实例并提供当前 SSH endpoint 与页面价格后，才可恢复一次 `Tesla V100-PCIE-32GB`、FP64、seed 17、`STRONG_RAW` scratch、1000-update 的 reference-blind R1a。

## 明确禁止

- 第二次 R1a、seed 变更、延长训练、checkpoint selection、early stop 或结果导向救援。
- R1b、MultiAdam、phase learning-rate multiplier、continuation、L-BFGS、Fourier/sampler 改动或 PJGR。
- stress prediction、stress reference 读取或开封；作者联系、投稿和投稿系统操作。

## 主张边界

- `VERIFIED`：V2.2R terminal No-Go、R0A/R0B/R0C 证据保持原样；R0C 已排除“raw gradient 小必然导致 Adam 有效更新小”。
- `HYPOTHESIS`：标准 ConFIG 可能通过处理多目标方向冲突恢复 two-cycle competence。
- `UNKNOWN`：R1a 是否恢复 competence；在本次冻结评价前不得写成正面结果。

权威决定见 [ADR 0052](docs/adr/0052-activate-phk-v23-r1a-config-competence-recovery.md)，唯一 live plan 见 [NEXT_ACTIONS.md](docs/plans/NEXT_ACTIONS.md)。

~~~text
PHASE_ID=PHK_V23_R1A_CONFIG_COMPETENCE_RECOVERY
BLOCKER_ID=AUTODL_ENDPOINT_OR_PRICE
METHOD_SELECTION_STATUS=NO_CANDIDATE_ALL_FOUR_ARMS_INELIGIBLE
NEXT_RESEARCH_EXECUTION_AUTHORIZED=false
CURRENT_STAGE=R1A_AWAIT_LIVE_AUTODL_ENDPOINT_AND_PRICE
~~~
