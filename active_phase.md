# 当前阶段

- `phase_id`: `PHK_V23_R1X_BOUNDED_CLEAN_COUPLING_CAMPAIGN_EXECUTE`
- `phase_name`: PHK-V2.3 R1X 有界 clean-coupling campaign（E1 已完成，等待 E2 重启）
- `lifecycle_state`: `ACTIVE`
- `blocker_id`: `AUTODL_RESTART_REQUIRED_FOR_E2_TOP_DIRICHLET_HARD_LIFT`
- `claim_status`: `V22R_TERMINAL_NO_GO_AND_R1A_NO_COMPETENCE_PRESERVED_R1X_E1_ET_NOT_READY_NO_COMPETENCE`
- `next_research_execution_authorized`: `true`
- `authorization_scope`: `RUN_FROZEN_E2_TOP_DIRICHLET_HARD_LIFT_AFTER_AUTODL_RESTART`
- `plan_status`: `AWAITING_AUTODL_RESTART_CAMPAIGN_AUTHORIZATION_REMAINS_ACTIVE`
- `contract_status`: `PHK_V23_R1X_CAMPAIGN_AMENDED_ACTIVE`
- `object_status`: `PHK_V21_FIXED_DISCRETIZATION_OBJECT_REUSED_WITHOUT_CONTINUUM_ORACLE_CLAIM`
- `method_selection_status`: `NO_CANDIDATE_ALL_FOUR_ARMS_INELIGIBLE`
- `candidate_status`: `NOT_FROZEN`
- `reference_status`: `CLOUD_REFERENCE_BLIND_LOCAL_NOMINAL_ONLY_AFTER_SHUTDOWN_STRESS_SEALED_UNREAD`
- `compute_status`: `AUTODL_SHUTDOWN_VERIFIED_AWAITING_RESTART_FOR_E2_TOP_DIRICHLET_HARD_LIFT`
- `diagnostic_outcome`: `E1_ET_NOT_READY`
- `git_authorization`: `SELECTIVE_R1X_COMMIT_PUSH_MAIN_AUTHORIZED`
- `external_publication_authorization`: `NOT_AUTHORIZED`
- `effective_date`: `2026-09-03`

## 当前授权边界

用户已明确覆盖旧合同的一次 engineering-retry 限制，并建立“首个 optimizer step 前的纯工程故障在根因明确且隔离回归证明完全修复后，可继续相同冻结任务”的通用规则。修复后的 E1 已形成第一条有效科学轨迹，并在 step 300 按冻结 readiness gate 停止为 `E1_ET_NOT_READY`。机器树唯一选择 `E2_TOP_DIRICHLET_HARD_LIFT`；该 E2 已由原 campaign 授权，但须等待用户重新启动 AutoDL。每条 GPU 轨迹结束后仍必须立即回收并关闭实例。

## 明确禁止

- 改变原 R1X 科学身份、seed、机器树、阈值、物理、reference 或 evaluator；
- stress 读取/预测、PJGR、R2、low-fidelity、benchmark/PDE/reference/evaluator 改写；
- 投稿、对外披露或自动扩展本 campaign。

## 证据边界

- `VERIFIED`: V2.2R terminal No-Go、R0A、R0B、R0C 与 R1a `R1A_CONFIG_RAW_NO_COMPETENCE` 保持不变。
- `VERIFIED`: 历史两次工程启动均为 0 update；其后修复的 E1 在 V100/FP64/seed 17 上从 scratch 完成 300 个 warm-up updates，五个 readiness checkpoints 均失败，ramp/full closure 未进入。
- `VERIFIED`: E1 产物已完整回收并核对远端/本地 hash，AutoDL 已关机且 SSH 为 `Connection refused`；关机后本地 frozen evaluator 裁决 `E1_ET_NOT_READY`，两周期事件仍完全缺失。
- `SUPPORTED_INTERPRETATION`: conflict-resolution-only 不足以恢复当前 strong-raw competence。
- `HYPOTHESIS`: top Dirichlet hard lift 可能建立同时覆盖 W1/W3 ROI 的热激活与 cold kinetic drive；尚未执行 E2。
- `UNKNOWN`: E2 readiness、phase signal、ramp/full closure、competence、E3/confirmation，以及所有 stress、其他 seed 和 R2 结果。

E1 结果见 [E1 closeout](docs/experiment/2026-09-03-phk-v23-r1x-e1-et-not-ready-closeout.md)，恢复决定见 [ADR 0054](docs/adr/0054-resume-r1x-after-verified-engineering-repair.md)，原科学合同见 [ADR 0053](docs/adr/0053-activate-phk-v23-r1x-bounded-clean-coupling-campaign.md)，唯一 live plan 见 [NEXT_ACTIONS.md](docs/plans/NEXT_ACTIONS.md)。

~~~text
PHASE_ID=PHK_V23_R1X_BOUNDED_CLEAN_COUPLING_CAMPAIGN_EXECUTE
BLOCKER_ID=AUTODL_RESTART_REQUIRED_FOR_E2_TOP_DIRICHLET_HARD_LIFT
METHOD_SELECTION_STATUS=NO_CANDIDATE_ALL_FOUR_ARMS_INELIGIBLE
NEXT_RESEARCH_EXECUTION_AUTHORIZED=true
CURRENT_STAGE=AWAITING_AUTODL_RESTART_CAMPAIGN_AUTHORIZATION_REMAINS_ACTIVE
~~~
