# PLAN-PHK-V2.3-LF0：exact-top warm-start attribution campaign

- `phase_id`: `PHK_V23_LF0_EXACT_TOP_WARMSTART_ATTRIBUTION_EXECUTE`
- `lifecycle_state`: `AWAITING`
- `blocker_id`: `AWAITING_AUTODL_RESTART_CAMPAIGN_AUTHORIZATION_REMAINS_ACTIVE`
- `claim_status`: `C0_OUTPUT_TRANSFORM_INADMISSIBLE_PRESERVED_LF0_CPU_QUALIFIED_NO_GPU_SCIENTIFIC_RESULT`
- `next_research_execution_authorized`: `true`
- `authorization_state`: `USER_EXPLICIT_LF0_EXECUTE_ACTIVE`
- `plan_status`: `LF0_CPU_QUALIFIED_AWAITING_AUTODL_RESTART`
- `current_stage`: `LF0_RUN_A_READY_INSTANCE_RESTART_REQUIRED`
- `supersedes`: `PLAN_PHK_V23_C0_COMPLETE`
- `preserves`: `V22R_R0A_R0B_R0C_R1A_R1X_C0_EVIDENCE`
- `contracts`: `configs/phk_v23/{program_contract_lf0_exact_top_warmstart,method_contract_lf0_exact_top_warmstart,data_contract_lf0_medium_only,decision_contract_lf0_attribution}.json`
- `decision`: `docs/adr/0056-activate-phk-v23-lf0-exact-top-warmstart-attribution.md`
- `next_recommendation`: `RESTART_AUTODL_AND_EXECUTE_LF0_RUN_A`

## 当前步骤

1. exact-top raw potential transform、medium-only LF stream、A/B/C runner、201 项 focused/affected regression 与 CPU qualification 已完成并通过。
2. 当前等待用户重启 AutoDL；已知旧端点不可达，Run A 尚未启动、scientific GPU run count 仍为 0。
3. 实例恢复后执行 Run A。回收后立即关机；本地评价完成后等待用户重启以执行固定 Run B。
4. Run B 后按冻结增量门决定是否执行 C；未触发 C 时直接收口。
5. 每次状态变化仅提交本 campaign 白名单文件，保持 stress sealed/unread，不执行 PJGR、R2、其他 seed 或投稿。

## 停止条件

达到 decision contract 中任一穷尽 machine outcome，或需要用户重启 AutoDL 时立即停止当前运行阶段。不存在结果导向改门、第四条科学轨迹或隐式新模块。
