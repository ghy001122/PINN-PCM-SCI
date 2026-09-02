# PLAN-PHK-V2.3-R1X：有界 clean-coupling campaign

- `phase_id`: `PHK_V23_R1X_BOUNDED_CLEAN_COUPLING_CAMPAIGN_EXECUTE`
- `lifecycle_state`: `ACTIVE`
- `blocker_id`: `AUTODL_RESTART_REQUIRED_FOR_E2_TOP_DIRICHLET_HARD_LIFT`
- `claim_status`: `V22R_TERMINAL_NO_GO_AND_R1A_NO_COMPETENCE_PRESERVED_R1X_E1_ET_NOT_READY_NO_COMPETENCE`
- `next_research_execution_authorized`: `true`
- `authorization_state`: `EXPLICITLY_REAUTHORIZED_AFTER_VERIFIED_ENGINEERING_REPAIR`
- `plan_status`: `AWAITING_AUTODL_RESTART_CAMPAIGN_AUTHORIZATION_REMAINS_ACTIVE`
- `current_stage`: `R1X_E2_TOP_DIRICHLET_HARD_LIFT_WAITING_FOR_AUTODL_RESTART`
- `supersedes`: `PLAN_PHK_V23_R1A_COMPLETE`
- `preserves`: `V22R_R0A_R0B_R0C_R1A_EVIDENCE`
- `program_contract`: `configs/phk_v23/program_contract_r1x_bounded_clean_coupling.json`
- `method_contract`: `configs/phk_v23/method_contract_r1x_clean_coupling.json`
- `exploration_contract`: `configs/phk_v23/exploration_contract_r1x_bounded_clean_coupling.json`
- `decision`: `docs/adr/0054-resume-r1x-after-verified-engineering-repair.md`
- `execution_override`: `configs/phk_v23/execution_override_r1x_verified_engineering_repair.json`

## 唯一执行链

1. `COMPLETED`: 完成合同、单一 trainer/residual seam、R1X adapter、focused/regression tests、run card、部署 bundle 和文档一致性门；激活提交已推送。
2. `COMPLETED_NO_SCIENTIFIC_TRAJECTORY`: 用户重启实例后核验 V100/FP64 环境并部署隔离 bundle；首次启动在模型构造前发现缺失 `engineering_contract.json`。
3. `COMPLETED_NO_SCIENTIFIC_TRAJECTORY`: 按合同唯一一次 engineering retry 补入并绑定该文件，但仍在模型构造前发现缺失传递依赖 `e1_solver_selection.json`；两次均为 0 optimizer updates。
4. `COMPLETED`: 回收两份失败日志并核对远端/本地 SHA-256，立即关闭 AutoDL；SSH probe 返回 `Connection refused`。nominal/stress 均未读取。
5. `SUPERSEDED_AUTHORITY`: 2026-09-02 曾因 retry 耗尽收口为 `ENGINEERING_BLOCKED`；该历史事实保留，但其停止权限已由用户 2026-09-03 的明确覆盖和 ADR 0054 取代。
6. `COMPLETED_SCIENTIFIC_TRAJECTORY_1_OF_3`: 修复后的 E1 通过云端隔离前检，在 V100/FP64/seed 17 上从 scratch 完成 300 warm-up updates；steps 200/225/250/275/300 readiness 均失败，按冻结 policy 停止为 `E1_ET_NOT_READY`。
7. `COMPLETED`: E1 产物完整回收并核对 hash，AutoDL 立即关机且 SSH 为 `Connection refused`；关机后 frozen nominal evaluator 确认无两周期 competence。
8. `AWAITING_AUTODL_RESTART`: 冻结机器树唯一选择 `E2_TOP_DIRICHLET_HARD_LIFT`。用户只需重新启动实例并提供 endpoint；campaign 科学授权无需重批。
9. `PENDING_MACHINE_TREE`: E2 结束后仍仅可按原冻结规则进入 E3、confirmation 或 pure-scratch stop。

## 不变量与停止条件

- 本 campaign 已执行 1/3 条 non-voting exploration、0/1 条 confirmation；历史 engineering failure 仍为 0-step 工程证据，不计 exploration。
- 当前只授权原 R1X E1 及其后由冻结机器树唯一到达的 E2/E3/confirmation；不授权 PJGR、R2、low-fidelity、其他 seed 或 stress。
- V2.2R/R0A/R0B/R0C/R1a 历史证据、benchmark、PDE、本构、reference 和 evaluator 均保持不变。
- 两份 stress references 始终 sealed/unread。
- 工程故障只有在首步前、0 科学轨迹、根因明确且隔离回归证明完全修复时才可继续相同冻结任务；其余停止条件仍按原合同执行。

恢复决定见 [ADR 0054](../adr/0054-resume-r1x-after-verified-engineering-repair.md)；历史工程阻塞见 [R1X engineering-blocked closeout](../experiment/2026-09-02-phk-v23-r1x-engineering-blocked-closeout.md)。
E1 科学轨迹与机器路由见 [R1X E1 closeout](../experiment/2026-09-03-phk-v23-r1x-e1-et-not-ready-closeout.md)。
