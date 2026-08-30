# PLAN-PHK-V2.3-R0B：首次窗口切换 175-step 最小诊断

- `phase_id`: `PHK_V23_R0B_FIRST_SWITCH_175_MINIMAL_V2`
- `lifecycle_state`: `ACTIVE`
- `blocker_id`: `NONE`
- `claim_status`: `V22R_TERMINAL_NO_GO_PRESERVED_R0B_REFERENCE_BLIND_REPLAY_PENDING`
- `next_research_execution_authorized`: `true`
- `authorization_state`: `CURRENT_USER_EXPLICIT_R0B_AND_GPU_EXECUTE`
- `plan_status`: `R0B_CONTRACT_IMPLEMENT_TEST_RUN_RECOVER_SHUTDOWN_ADJUDICATE`
- `current_stage`: `LOCAL_IMPLEMENTATION_AND_PREFLIGHT`
- `supersedes`: `PLAN_PHK_V23_R0A_COMPLETE`
- `preserves`: `PHK_V23_R0A_INCONCLUSIVE_AND_PHK_V22R_TERMINAL_NO_GO`
- `program_contract`: `configs/phk_v23/program_contract_r0b_minimal_v2.json`
- `method_contract`: `configs/phk_v23/method_contract_r0b_minimal_v2.json`
- `diagnostic_contract`: `configs/phk_v23/r0b_diagnostic_contract_minimal_v2.json`
- `decision`: `docs/adr/0050-activate-phk-v23-r0b-first-switch-175-minimal-v2.md`

## 论文去向与唯一问题

本阶段只服务于论文 Discussion/Methods failure analysis：识别从 scratch 到首次 W1→W1+W2 切换期间，哪一类机制最早获得持续的 reference-blind 支持。输出是 `PRIMARY_PRECURSOR_CANDIDATE`，不是因果根因、competence 恢复或方法增益。

当前强基线仍是旧 `STRONG_RAW`。本阶段没有 proposed method、方法消融或 formal OOD；其价值是决定未来最多一个 R1a 原子干预是否值得另立计划。两份 stress reference 保持 sealed/unread。

## 唯一执行链

1. 冻结三份 R0B minimal-v2 合同、ADR、单一 observer seam、runner、machine adjudicator、focused tests 与 AutoDL run card。
2. 本地运行 focused tests、受影响 legacy regression、ledger 与 `DOCUMENT_CONSISTENCY_VALID`；失败则不启动 GPU。
3. 选择性 commit/push 白名单文件；保留工作树中其他会话/用户的全部无关变更。
4. 远端核验 V100、环境、空进程、source commit、合同与预算；只运行一次 seed-17/FP64/STRONG_RAW scratch replay。
5. 保持 `training_config.updates=1000` 作为科学 schedule denominator，只执行 175 个 canonical optimizer steps；step 151 必须是首次 W1+W2 refresh/update。云端 shadow optimizer steps 固定为 0。
6. 生成 final step-175 checkpoint、reference-blind telemetry、transition diagnostic bundle、prediction、log、manifest、environment 与 summary。
7. 下载并核对远端/本地哈希、数量、source/contract/run identity 后，立即关闭 AutoDL 实例并确认 SSH refused。
8. 不打开任何 reference，先执行机器 A–H adjudication并不可变写入。仅当 primary 为 `SWITCH_INDUCED` 时运行本地 CPU gradient-only factorial；否则记录 `FACTORIAL_NOT_RUN_NOT_NEEDED`。
9. reference-blind decision 固定后才允许本地打开 nominal development reference，生成 non-voting evaluation appendix；它不得改变 primary 或下一阶段授权。
10. 写入 manifest、ledger、closeout、状态与文档门禁后停止；不自动进入 R1、PJGR、stress 或第二次 run。

## 预算与停止

- V100 paid work：soft stop 45 min，hard stop 60 min；增量估算费用 hard cap 5 CNY。
- 条件性本地 CPU factorial hard cap 2 h；不构造 optimizer、不更新参数。
- V2.3 全局 hard caps：34 GPU-h、95 CNY、从 ADR 激活起 14 days；项目绝对云成本 hard cap 150 CNY。
- 身份/GPU/合同漂移、reference 可达、observer state/RNG/grad 变化、非有限值、重复进程、预算超门、非 175 steps、错误 switch/refresh 或产物不完整均立即停止且不自动重跑。

## 当前边界

R0B 只可执行一次。R0A `R0A_INCONCLUSIVE`、V2.2R `MVP_NO_GO_NO_BASIC_COMPETENCE`、bounded-negative advisor draft 与两份 stress seal 均不可改写。作者联系、投稿、投稿系统上传与凭据披露仍未授权。
