# PLAN-PHK-V2.3-R1X：有界 clean-coupling campaign

- `phase_id`: `PHK_V23_R1X_BOUNDED_CLEAN_COUPLING_CAMPAIGN_EXECUTE`
- `lifecycle_state`: `ACTIVE`
- `blocker_id`: `NONE`
- `claim_status`: `V22R_TERMINAL_NO_GO_AND_R1A_NO_COMPETENCE_PRESERVED_R1X_E1_PENDING`
- `next_research_execution_authorized`: `true`
- `authorization_state`: `EXPLICIT_CAMPAIGN_EXECUTE_ACTIVE`
- `plan_status`: `R1X_E1_IMPLEMENTATION_AND_PREFLIGHT_ACTIVE`
- `current_stage`: `R1X_E1_IMPLEMENTATION_AND_PREFLIGHT`
- `supersedes`: `PLAN_PHK_V23_R1A_COMPLETE`
- `preserves`: `V22R_R0A_R0B_R0C_R1A_EVIDENCE`
- `program_contract`: `configs/phk_v23/program_contract_r1x_bounded_clean_coupling.json`
- `method_contract`: `configs/phk_v23/method_contract_r1x_clean_coupling.json`
- `exploration_contract`: `configs/phk_v23/exploration_contract_r1x_bounded_clean_coupling.json`
- `decision`: `docs/adr/0053-activate-phk-v23-r1x-bounded-clean-coupling-campaign.md`

## 唯一执行链

1. `IN_PROGRESS`: 完成合同、单一 trainer/residual seam、R1X adapter、focused/regression tests、run card、部署 bundle 和文档一致性门。
2. `PENDING`: 从 scratch 执行 E1 clean-coupling exploration；实时只读观察，完成后回收、哈希核验并立即关闭 AutoDL。
3. `PENDING`: 关机验证后，本地运行 frozen nominal evaluator；按预声明结果唯一选择 confirmation、对应 E2 或终止。
4. `CONDITIONAL`: 若 E2 有 material phase signal 但未 competent，执行同一 E2 身份加 500 full-joint updates 的 E3；否则终止 pure-scratch。
5. `CONDITIONAL`: 首条完整 competence signal 后，仅执行一次完全冻结、from-scratch confirmation。
6. `PENDING`: 写 compact evidence、ledger、closeout 与 terminal authority state，精确白名单提交并推送 main。

## 不变量与停止条件

- 所有轨迹固定 V100/FP64/seed17/STRONG_RAW/scratch/同一 Adam/ConFIG/pure Sobol；云端 reference-blind。
- 运行数硬上限为三条 exploration 和一条 confirmation；optimizer-step 上限按分支冻结。
- 每条运行结束必须先回收核验，立即关机并验证；之后才能本地 nominal 评价。
- stress 始终 sealed；不执行 PJGR、R2、low-fidelity、其他 seed 或投稿。
- 终点只能是 `R1C_PASS_HEADLINE_CORE_GATE_REVIEW_NOT_AUTHORIZED`、`PURE_SCRATCH_COMPETENCE_RECOVERY_FAILED`、`AWAITING_AUTODL_RESTART_CAMPAIGN_AUTHORIZATION_REMAINS_ACTIVE` 或 `ENGINEERING_BLOCKED`。
