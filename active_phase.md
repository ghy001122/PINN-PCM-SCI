# 当前阶段

- `phase_id`: `PHK_V23_R1X_BOUNDED_CLEAN_COUPLING_CAMPAIGN_EXECUTE`
- `phase_name`: PHK-V2.3 R1X 有界 clean-coupling campaign（工程修复后恢复）
- `lifecycle_state`: `ACTIVE`
- `blocker_id`: `NONE_VERIFIED_ENGINEERING_REPAIR_COMPLETE`
- `claim_status`: `V22R_TERMINAL_NO_GO_AND_R1A_NO_COMPETENCE_PRESERVED_R1X_ENGINEERING_BLOCKED_NO_SCIENTIFIC_EVIDENCE`
- `next_research_execution_authorized`: `true`
- `authorization_scope`: `RESUME_ORIGINAL_R1X_E1_AND_FROZEN_MACHINE_TREE_AFTER_VERIFIED_ENGINEERING_REPAIR`
- `plan_status`: `R1X_E1_REAUTHORIZED_PREFLIGHT_PENDING`
- `contract_status`: `PHK_V23_R1X_CAMPAIGN_AMENDED_ACTIVE`
- `object_status`: `PHK_V21_FIXED_DISCRETIZATION_OBJECT_REUSED_WITHOUT_CONTINUUM_ORACLE_CLAIM`
- `method_selection_status`: `NO_CANDIDATE_ALL_FOUR_ARMS_INELIGIBLE`
- `candidate_status`: `NOT_FROZEN`
- `reference_status`: `CLOUD_REFERENCE_BLIND_LOCAL_NOMINAL_ONLY_AFTER_SHUTDOWN_STRESS_SEALED_UNREAD`
- `compute_status`: `AUTODL_V100_ONLINE_E1_DEPLOYMENT_PREFLIGHT_PENDING`
- `diagnostic_outcome`: `R1X_E1_PENDING`
- `git_authorization`: `SELECTIVE_R1X_COMMIT_PUSH_MAIN_AUTHORIZED`
- `external_publication_authorization`: `NOT_AUTHORIZED`
- `effective_date`: `2026-09-03`

## 当前授权边界

用户已明确覆盖旧合同的一次 engineering-retry 限制，并建立“首个 optimizer step 前的纯工程故障在根因明确且隔离回归证明完全修复后，可继续相同冻结任务”的通用规则。当前授权使用修复后的内容寻址 bundle 恢复原 E1；此前两次工程启动不计入 3 条 exploration 上限。E1 完成后仍按 ADR 0053 的冻结机器树路由，且每条 GPU 轨迹结束后必须立即回收并关闭 AutoDL。

## 明确禁止

- 改变原 R1X 科学身份、seed、机器树、阈值、物理、reference 或 evaluator；
- stress 读取/预测、PJGR、R2、low-fidelity、benchmark/PDE/reference/evaluator 改写；
- 投稿、对外披露或自动扩展本 campaign。

## 证据边界

- `VERIFIED`: V2.2R terminal No-Go、R0A、R0B、R0C 与 R1a `R1A_CONFIG_RAW_NO_COMPETENCE` 保持不变。
- `VERIFIED`: 两次 R1X 启动均在物理合同物化期间、模型和 optimizer 构造前 fail-closed；optimizer updates=0，科学轨迹=0，AutoDL 已关机，nominal/stress 均未读取。
- `VERIFIED`: 传递部署依赖已闭合，内容寻址清单 identity 与 isolated physics-load 回归通过；用户已明确授权恢复原任务。
- `SUPPORTED_INTERPRETATION`: conflict-resolution-only 不足以恢复当前 strong-raw competence。
- `HYPOTHESIS`: clean cold-state electrothermal warm-up、coupling ramp 和完整 joint closure 可能避免过早进入冷态兼容解；本轮没有执行该假设。
- `UNKNOWN`: E1 readiness、phase signal、competence、E2/E3/confirmation，以及所有 stress、其他 seed 和 R2 结果。

恢复决定见 [ADR 0054](docs/adr/0054-resume-r1x-after-verified-engineering-repair.md)，原科学合同见 [ADR 0053](docs/adr/0053-activate-phk-v23-r1x-bounded-clean-coupling-campaign.md)，唯一 live plan 见 [NEXT_ACTIONS.md](docs/plans/NEXT_ACTIONS.md)，历史工程阻塞见 [R1X engineering-blocked closeout](docs/experiment/2026-09-02-phk-v23-r1x-engineering-blocked-closeout.md)。

~~~text
PHASE_ID=PHK_V23_R1X_BOUNDED_CLEAN_COUPLING_CAMPAIGN_EXECUTE
BLOCKER_ID=NONE_VERIFIED_ENGINEERING_REPAIR_COMPLETE
METHOD_SELECTION_STATUS=NO_CANDIDATE_ALL_FOUR_ARMS_INELIGIBLE
NEXT_RESEARCH_EXECUTION_AUTHORIZED=true
CURRENT_STAGE=R1X_E1_REAUTHORIZED_PREFLIGHT_PENDING
~~~
