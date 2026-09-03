# PLAN-PHK-V2.3-C0：reference/discrete/strong-form compatibility audit

- `phase_id`: `PHK_V23_C0_REFERENCE_DISCRETE_STRONGFORM_COMPATIBILITY_AUDIT_EXECUTE`
- `lifecycle_state`: `ACTIVE`
- `blocker_id`: `C0_CPU_COMPATIBILITY_DIAGNOSTIC_PENDING`
- `claim_status`: `V22R_AND_R1X_NEGATIVE_EVIDENCE_PRESERVED_C0_DIAGNOSTIC_PENDING`
- `next_research_execution_authorized`: `true`
- `authorization_state`: `ONE_C0_CPU_FP64_DIAGNOSTIC_AUTHORIZED`
- `plan_status`: `C0_EXECUTION_ACTIVE`
- `current_stage`: `PRE_EXECUTION_VALIDATION`
- `supersedes`: `PLAN_PHK_V23_R1X_COMPLETE`
- `preserves`: `V22R_R0A_R0B_R0C_R1A_R1X_EVIDENCE`
- `contract`: `configs/phk_v23/c0_reference_discrete_strongform_compatibility_contract.json`
- `decision`: `docs/adr/0055-activate-phk-v23-c0-reference-discrete-strongform-compatibility-audit.md`

## 执行顺序

1. 冻结并测试 carrier、物理对象、FVM 算子、R1X pool、mask、公式与五类裁决。
2. 运行受影响的 CPU regressions、ledger validator 和 document-consistency gate。
3. 以精确 source commit 执行一次 CPU/FP64 C0 audit；不使用神经 checkpoint、GPU 或 AutoDL。
4. 保存 compact statistics、manifest、closeout 和 ledger；不保存 reference 场或派生数组。
5. 将机器 primary/secondary 与唯一 next recommendation 同步到权威状态，关闭本阶段并精确提交、推送。

## 停止条件

得到五类机器结果之一后立即停止。任何输入 hash、shape、finite、source identity 或 stress fail-close 失败均属于工程阻塞，不得伪装成科学结果。C0 完成不自动授权下一路线。
