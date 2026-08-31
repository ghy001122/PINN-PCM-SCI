# PLAN-PHK-V2.3-R1A：ConFIG competence recovery

- `phase_id`: `PHK_V23_R1A_CONFIG_COMPETENCE_RECOVERY`
- `lifecycle_state`: `COMPLETE`
- `blocker_id`: `NONE`
- `claim_status`: `V22R_TERMINAL_NO_GO_PRESERVED_R1A_CONFIG_RAW_NO_COMPETENCE_NO_METHOD_EVIDENCE`
- `next_research_execution_authorized`: `false`
- `authorization_state`: `R1A_AUTHORIZATION_CONSUMED_NO_NEXT_EXECUTION_AUTHORIZED`
- `plan_status`: `R1A_TERMINAL_NO_GO_COMPLETE`
- `current_stage`: `R1A_CONFIG_RAW_NO_COMPETENCE_COMPLETE`
- `supersedes`: `PLAN_PHK_V23_R0C_COMPLETE_FUTURE_AUTHORIZATION_ONLY`
- `preserves`: `R0C_R0B_R0A_AND_PHK_V22R_TERMINAL_EVIDENCE`
- `program_contract`: `configs/phk_v23/program_contract_r1a_config.json`
- `method_contract`: `configs/phk_v23/method_contract_r1a_config.json`
- `decision`: `docs/adr/0052-activate-phk-v23-r1a-config-competence-recovery.md`

## 唯一执行链

1. `COMPLETED`：完成合同、单一 gradient-combiner seam、ConFIG adapter、focused tests、run card、部署 bundle 和文档一致性门。
2. `COMPLETED`：用户已恢复实例；SSH、V100、空闲 GPU、远端环境和 `1.88 CNY/h` 公开实时单价已通过前检。
3. `COMPLETED`：冻结 bundle 逐文件哈希通过；唯一一次 FP64/seed-17/STRONG_RAW scratch 1000-update standard-ConFIG run 与 reference-free prediction 完成。
4. `COMPLETED`：全部产物回收并核验 SHA-256；AutoDL 已执行 `/usr/bin/shutdown -h now`，关机探针为 `Connection refused`。
5. `COMPLETED`：关机后本地 frozen nominal evaluator 裁决 `R1A_CONFIG_RAW_NO_COMPETENCE`；两周期各失败 event、ROI peak 与 recovery 三项门。
6. `COMPLETED`：compact artifact、manifest、ledger、closeout、claim audit 与状态收口完成；只余选择性 commit/push。

## 终局边界

- ConFIG 在 12 个冻结机制节点均产生对四组梯度正向的合成方向，但 `phase>=0.5` 活动比例仍为 0；不得写成 competence 或方法收益。
- 本 R1a 授权已消耗。R1b、PJGR、第二 seed、训练延长、其他模块、stress 与投稿均未授权。

## 冻结停止条件

- 四组损失之和不在 FP64 `rtol=1e-12, atol=1e-14` 内等于旧总目标：`R1A_LOSS_DECOMPOSITION_IDENTITY_BLOCKED`。
- 任一损失、组梯度、合成梯度或模型产物非有限：`R1A_NUMERICAL_INVALID_STOP`，不得 fallback。
- endpoint、live price、V100 身份、预算、部署哈希或 reference isolation 失败：`R1A_BUDGET_OR_INFRASTRUCTURE_BLOCKED`。
- 全部 competence guards PASS 才是 solver-level competence recovery；任一 guard 失败即 bounded No-Go。本计划不授权自动救援。
