# PLAN-PHK-V2.3-R1A：ConFIG competence recovery

- `phase_id`: `PHK_V23_R1A_CONFIG_COMPETENCE_RECOVERY`
- `lifecycle_state`: `AWAITING`
- `blocker_id`: `AUTODL_ENDPOINT_OR_PRICE`
- `claim_status`: `V22R_TERMINAL_NO_GO_PRESERVED_R1A_INFRASTRUCTURE_BLOCKED_NO_SCIENTIFIC_RUN`
- `next_research_execution_authorized`: `false`
- `authorization_state`: `ONE_R1A_CONFIG_EXECUTION_AUTHORIZED_BUT_UNCONSUMED`
- `plan_status`: `R1A_PREFLIGHT_BLOCKED`
- `current_stage`: `AWAIT_LIVE_AUTODL_ENDPOINT_AND_PRICE`
- `supersedes`: `PLAN_PHK_V23_R0C_COMPLETE_FUTURE_AUTHORIZATION_ONLY`
- `preserves`: `R0C_R0B_R0A_AND_PHK_V22R_TERMINAL_EVIDENCE`
- `program_contract`: `configs/phk_v23/program_contract_r1a_config.json`
- `method_contract`: `configs/phk_v23/method_contract_r1a_config.json`
- `decision`: `docs/adr/0052-activate-phk-v23-r1a-config-competence-recovery.md`

## 唯一执行链

1. `COMPLETED`：完成合同、单一 gradient-combiner seam、ConFIG adapter、focused tests、run card、部署 bundle 和文档一致性门。
2. `BLOCKED`：已核验旧 SSH endpoint 连续两次 `Connection refused`；等待用户启动实例并提供当前 SSH endpoint 与页面实时价格，再核验 V100、空闲 GPU、远端环境、部署哈希与 reference-blind 边界。
3. `PENDING`：只执行一次 FP64/seed-17/STRONG_RAW scratch 1000-update standard-ConFIG run，并写 final checkpoint、training/mechanism logs、manifests、prediction、environment 和 cost summary。
4. `PENDING`：回收全部产物并逐文件核验 SHA-256，随后立即关闭 AutoDL；关机失败时只处理基础设施，不得本地开 reference。
5. `PENDING`：关机确认后在本地运行冻结 nominal evaluator，裁决 `R1A_CONFIG_RAW_COMPETENCE_RECOVERED` 或 `R1A_CONFIG_RAW_NO_COMPETENCE`。
6. `PENDING`：完成 compact artifact、manifest、ledger、closeout、claim audit、状态收口和选择性 commit/push。

## 冻结停止条件

- 四组损失之和不在 FP64 `rtol=1e-12, atol=1e-14` 内等于旧总目标：`R1A_LOSS_DECOMPOSITION_IDENTITY_BLOCKED`。
- 任一损失、组梯度、合成梯度或模型产物非有限：`R1A_NUMERICAL_INVALID_STOP`，不得 fallback。
- endpoint、live price、V100 身份、预算、部署哈希或 reference isolation 失败：`R1A_BUDGET_OR_INFRASTRUCTURE_BLOCKED`。
- 全部 competence guards PASS 才是 solver-level competence recovery；任一 guard 失败即 bounded No-Go。本计划不授权自动救援。
