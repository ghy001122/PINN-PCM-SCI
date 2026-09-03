# PLAN-PHK-V2.3-R1X：有界 clean-coupling campaign（完成）

- `phase_id`: `PHK_V23_R1X_BOUNDED_CLEAN_COUPLING_CAMPAIGN_EXECUTE`
- `lifecycle_state`: `COMPLETE`
- `blocker_id`: `PURE_SCRATCH_COMPETENCE_RECOVERY_FAILED`
- `claim_status`: `V22R_TERMINAL_NO_GO_AND_R1A_NO_COMPETENCE_PRESERVED_R1X_PURE_SCRATCH_COMPETENCE_RECOVERY_FAILED`
- `next_research_execution_authorized`: `false`
- `authorization_state`: `CAMPAIGN_CONSUMED_NO_FURTHER_EXECUTION_AUTHORIZED`
- `plan_status`: `PURE_SCRATCH_COMPETENCE_RECOVERY_FAILED`
- `current_stage`: `TERMINAL_PURE_SCRATCH_STOP`
- `supersedes`: `PLAN_PHK_V23_R1A_COMPLETE`
- `preserves`: `V22R_R0A_R0B_R0C_R1A_EVIDENCE`
- `program_contract`: `configs/phk_v23/program_contract_r1x_bounded_clean_coupling.json`
- `method_contract`: `configs/phk_v23/method_contract_r1x_clean_coupling.json`
- `exploration_contract`: `configs/phk_v23/exploration_contract_r1x_bounded_clean_coupling.json`
- `decision`: `docs/adr/0053-activate-phk-v23-r1x-bounded-clean-coupling-campaign.md`
- `execution_override`: `configs/phk_v23/execution_override_r1x_verified_engineering_repair.json`

## 已执行链

1. `COMPLETED`: 建立并激活 R1X 合同、trainer/residual seam、adapter、focused/regression tests、run card 与内容寻址部署。
2. `PRESERVED_ENGINEERING_HISTORY`: 两次历史 E1 启动在模型构造前因隔离部署传递依赖缺失而 0-update 终止；用户覆盖原一次 retry 上限后，依赖闭合并通过 isolated preflight。
3. `COMPLETED_EXPLORATION_1_OF_3`: 修复后的 E1 在 V100/FP64/seed 17 上从 scratch 完成 300 warm-up updates；五次 readiness 均失败，裁决为 `E1_ET_NOT_READY`。
4. `COMPLETED_MACHINE_BRANCH`: 冻结树唯一选择 E2 top-Dirichlet hard lift；用户重启实例后部署 source commit `ce64086c...`。
5. `PRESERVED_ZERO_STEP_STARTUP`: E2 首次 tmux 启动因相对 `PYTHONPATH` 未指向隔离根而在 import 前 0-update 终止；改用绝对路径并通过 isolated import regression，不计 exploration。
6. `COMPLETED_EXPLORATION_2_OF_3`: 有效 E2 从 scratch 完成 300 warm-up updates；top BC 精确满足，但五次 readiness 仍失败，且无 material phase signal。
7. `COMPLETED_LOCAL_ADJUDICATION`: 全部产物回收并核验 hash 后，本地 frozen nominal evaluator 确认两周期 event/ROI peak/recovery 全部失败。
8. `MACHINE_TREE_TERMINAL`: E2 未产生 material phase signal，故 E3 与 confirmation 不可达；终局为 `PURE_SCRATCH_COMPETENCE_RECOVERY_FAILED`。
9. `INSTANCE_LIFECYCLE_OVERRIDE`: 用户明确要求本条运行后不关机；实例保持在线但 GPU 空闲、无 R1X 进程。该事实不产生新科研授权。

## 最终计数与边界

- 有效 non-voting explorations：`2/3`；冻结树下剩余可达 exploration：`0`。
- frozen confirmations：`0/1`；当前不可达。
- E1/E2 均从 scratch、V100/FP64/seed 17、reference-blind；stress 始终 sealed/unread。
- V2.2R/R0A/R0B/R0C/R1a 历史证据、benchmark、PDE、本构、reference 与 evaluator 保持不变。
- 当前不得使用未消耗的数量槽重新选择 E2、进入 E3、执行 confirmation、PJGR、R2、其他 seed 或 stress。
- 下一研究路线仅可是 `LOW_FIDELITY_GUIDED_ROUTE_REQUIRES_NEW_CONTRACT_AND_EXECUTE`，或保留 bounded-negative package；本文件不授权其执行。
- 未来默认 GPU 生命周期仍为使用结束后及时关机；仅在用户对具体运行明确要求时保留实例。

最终证据见 [R1X E2/campaign closeout](../experiment/2026-09-03-phk-v23-r1x-e2-pure-scratch-stop-closeout.md)，E1 证据见 [R1X E1 closeout](../experiment/2026-09-03-phk-v23-r1x-e1-et-not-ready-closeout.md)，历史工程阻塞见 [R1X engineering-blocked closeout](../experiment/2026-09-02-phk-v23-r1x-engineering-blocked-closeout.md)。
