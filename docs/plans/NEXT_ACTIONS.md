# PLAN-PHK-V2.3-LF0：exact-top warm-start attribution campaign

- `phase_id`: `PHK_V23_LF0_EXACT_TOP_WARMSTART_ATTRIBUTION_EXECUTE`
- `lifecycle_state`: `ACTIVE`
- `blocker_id`: `LF0_CPU_QUALIFICATION_PENDING`
- `claim_status`: `C0_OUTPUT_TRANSFORM_INADMISSIBLE_PRESERVED_LF0_AUTHORIZED_NO_NEW_RESULT`
- `next_research_execution_authorized`: `true`
- `authorization_state`: `USER_EXPLICIT_LF0_EXECUTE_ACTIVE`
- `plan_status`: `LF0_EXECUTION_ACTIVE`
- `current_stage`: `LF0_IMPLEMENTATION_AND_CPU_QUALIFICATION`
- `supersedes`: `PLAN_PHK_V23_C0_COMPLETE`
- `preserves`: `V22R_R0A_R0B_R0C_R1A_R1X_C0_EVIDENCE`
- `contracts`: `configs/phk_v23/{program_contract_lf0_exact_top_warmstart,method_contract_lf0_exact_top_warmstart,data_contract_lf0_medium_only,decision_contract_lf0_attribution}.json`
- `decision`: `docs/adr/0056-activate-phk-v23-lf0-exact-top-warmstart-attribution.md`
- `next_recommendation`: `EXECUTE_LF0_FROZEN_MACHINE_TREE`

## 当前步骤

1. 实现 exact-top raw potential transform、CPU qualification、medium-only LF stream 与 A/B/C runner；通过 focused 和受影响回归。
2. 运行一次 CPU/FP64 qualification；任一门失败即以 `LF0_CPU_QUALIFICATION_BLOCKED` 收口，不启动 GPU。
3. CPU PASS 后执行 Run A。回收后立即关机；本地评价完成后等待用户重启以执行固定 Run B。
4. Run B 后按冻结增量门决定是否执行 C；未触发 C 时直接收口。
5. 每次状态变化仅提交本 campaign 白名单文件，保持 stress sealed/unread，不执行 PJGR、R2、其他 seed 或投稿。

## 停止条件

达到 decision contract 中任一穷尽 machine outcome，或需要用户重启 AutoDL 时立即停止当前运行阶段。不存在结果导向改门、第四条科学轨迹或隐式新模块。
