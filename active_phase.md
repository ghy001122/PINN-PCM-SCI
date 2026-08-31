# 当前阶段

- `phase_id`: `PHK_V23_R1A_CONFIG_COMPETENCE_RECOVERY`
- `phase_name`: PHK-V2.3 R1a ConFIG 基本能力恢复
- `lifecycle_state`: `COMPLETE`
- `blocker_id`: `NONE`
- `claim_status`: `V22R_TERMINAL_NO_GO_PRESERVED_R1A_CONFIG_RAW_NO_COMPETENCE_NO_METHOD_EVIDENCE`
- `authorization_scope`: `R1A_AUTHORIZATION_CONSUMED_NO_NEXT_EXECUTION_AUTHORIZED`
- `plan_status`: `R1A_TERMINAL_NO_GO_COMPLETE`
- `contract_status`: `PHK_V23_R1A_CONFIG_CONTRACT_FROZEN_ACTIVE`
- `object_status`: `PHK_V21_FIXED_DISCRETIZATION_OBJECT_REUSED_WITHOUT_CONTINUUM_ORACLE_CLAIM`
- `method_selection_status`: `NO_CANDIDATE_ALL_FOUR_ARMS_INELIGIBLE`
- `candidate_status`: `NOT_FROZEN`
- `reference_status`: `CLOUD_REFERENCE_BLIND_LOCAL_NOMINAL_EVALUATION_ONLY_AFTER_SHUTDOWN_STRESS_SEALED_UNREAD`
- `compute_status`: `V100_RUN_COMPLETE_ARTIFACTS_RECOVERED_AUTODL_SHUTDOWN_CONFIRMED`
- `diagnostic_outcome`: `R1A_CONFIG_RAW_NO_COMPETENCE`
- `next_research_execution_authorized`: `false`
- `git_authorization`: `SELECTIVE_R1A_COMMIT_PUSH_AUTHORIZED`
- `external_publication_authorization`: `NOT_AUTHORIZED`
- `effective_date`: `2026-08-31`

## 当前唯一允许的科研动作

没有新的科研执行授权。唯一一次 FP64、seed 17、`STRONG_RAW` scratch、1000-update reference-blind R1a 已完成、回收、验哈希并关机；本地 frozen nominal evaluator 裁决 `R1A_CONFIG_RAW_NO_COMPETENCE`。只允许只读审查、证据核验与本阶段选择性 Git 收口。

## 明确禁止

- 第二次 R1a、seed 变更、延长训练、checkpoint selection、early stop 或结果导向救援。
- R1b、MultiAdam、phase learning-rate multiplier、continuation、L-BFGS、Fourier/sampler 改动或 PJGR。
- stress prediction、stress reference 读取或开封；作者联系、投稿和投稿系统操作。

## 主张边界

- `VERIFIED`：V2.2R terminal No-Go、R0A/R0B/R0C 证据保持原样；R0C 已排除“raw gradient 小必然导致 Adam 有效更新小”。
- `VERIFIED`：标准 ConFIG 在全部冻结机制节点产生与四个 loss groups 正向的合成方向，但预测 `phase>=0.5` 活动比例仍为 0，两周期各失败 event、ROI peak 与 recovery 三项门。
- `SUPPORTED_INTERPRETATION`：仅消除四组梯度方向冲突不足以恢复当前 strong-raw 的相变事件能力；这不是对 ConFIG 或 PINN 的全局否定。
- `UNKNOWN`：任何尚未授权的 R1b/PJGR、其他 seed、stress 或 formal OOD 结果。

权威决定见 [ADR 0052](docs/adr/0052-activate-phk-v23-r1a-config-competence-recovery.md)，唯一 live plan 见 [NEXT_ACTIONS.md](docs/plans/NEXT_ACTIONS.md)。
终局证据见 [R1a ConFIG closeout](docs/experiment/2026-08-31-phk-v23-r1a-config-closeout.md)。

~~~text
PHASE_ID=PHK_V23_R1A_CONFIG_COMPETENCE_RECOVERY
BLOCKER_ID=NONE
METHOD_SELECTION_STATUS=NO_CANDIDATE_ALL_FOUR_ARMS_INELIGIBLE
NEXT_RESEARCH_EXECUTION_AUTHORIZED=false
CURRENT_STAGE=R1A_CONFIG_RAW_NO_COMPETENCE_COMPLETE
~~~
