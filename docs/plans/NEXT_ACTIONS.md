# PLAN-PHK-V2.3-R1X：有界 clean-coupling campaign

- `phase_id`: `PHK_V23_R1X_BOUNDED_CLEAN_COUPLING_CAMPAIGN_EXECUTE`
- `lifecycle_state`: `COMPLETE`
- `blocker_id`: `R1X_E1_DEPLOYMENT_TRANSITIVE_IDENTITY_INCOMPLETE_RETRY_EXHAUSTED`
- `claim_status`: `V22R_TERMINAL_NO_GO_AND_R1A_NO_COMPETENCE_PRESERVED_R1X_ENGINEERING_BLOCKED_NO_SCIENTIFIC_EVIDENCE`
- `next_research_execution_authorized`: `false`
- `authorization_state`: `CONSUMED_CLOSED_ENGINEERING_BLOCKED`
- `plan_status`: `R1X_CAMPAIGN_ENGINEERING_BLOCKED`
- `current_stage`: `ENGINEERING_BLOCKED`
- `supersedes`: `PLAN_PHK_V23_R1A_COMPLETE`
- `preserves`: `V22R_R0A_R0B_R0C_R1A_EVIDENCE`
- `program_contract`: `configs/phk_v23/program_contract_r1x_bounded_clean_coupling.json`
- `method_contract`: `configs/phk_v23/method_contract_r1x_clean_coupling.json`
- `exploration_contract`: `configs/phk_v23/exploration_contract_r1x_bounded_clean_coupling.json`
- `decision`: `docs/adr/0053-activate-phk-v23-r1x-bounded-clean-coupling-campaign.md`

## 唯一执行链

1. `COMPLETED`: 完成合同、单一 trainer/residual seam、R1X adapter、focused/regression tests、run card、部署 bundle 和文档一致性门；激活提交已推送。
2. `COMPLETED_NO_SCIENTIFIC_TRAJECTORY`: 用户重启实例后核验 V100/FP64 环境并部署隔离 bundle；首次启动在模型构造前发现缺失 `engineering_contract.json`。
3. `COMPLETED_NO_SCIENTIFIC_TRAJECTORY`: 按合同唯一一次 engineering retry 补入并绑定该文件，但仍在模型构造前发现缺失传递依赖 `e1_solver_selection.json`；两次均为 0 optimizer updates。
4. `COMPLETED`: 回收两份失败日志并核对远端/本地 SHA-256，立即关闭 AutoDL；SSH probe 返回 `Connection refused`。nominal/stress 均未读取。
5. `TERMINAL`: retry 已耗尽，campaign 收口为 `ENGINEERING_BLOCKED`。post-blocker 仅闭合隔离 deployment identity 并增加 isolated-physics-load 回归测试，不得据此第三次启动。

## 不变量与停止条件

- 本 campaign 的科学轨迹计数为 0，不得把 engineering failure 写成 E1、pure-scratch 或方法 No-Go。
- 当前不授权再次运行 E1、E2、E3、confirmation、GPU、PJGR、R2、low-fidelity、其他 seed 或 stress。
- V2.2R/R0A/R0B/R0C/R1a 历史证据、benchmark、PDE、本构、reference 和 evaluator 均保持不变。
- 两份 stress references 始终 sealed/unread。
- 唯一终点为 `ENGINEERING_BLOCKED`；未来使用已修复 bundle 需要新的明确 EXECUTE 授权。

终局证据见 [R1X engineering-blocked closeout](../experiment/2026-09-02-phk-v23-r1x-engineering-blocked-closeout.md)。
