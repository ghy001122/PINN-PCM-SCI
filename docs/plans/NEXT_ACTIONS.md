# PLAN-PHK-V2.3-R0B：首次窗口切换 175-step 最小诊断

- `phase_id`: `PHK_V23_R0B_FIRST_SWITCH_175_MINIMAL_V2`
- `lifecycle_state`: `COMPLETE`
- `blocker_id`: `NONE`
- `claim_status`: `V22R_TERMINAL_NO_GO_PRESERVED_R0B_GRADIENT_STARVATION_PRECURSOR_NO_METHOD_EVIDENCE`
- `next_research_execution_authorized`: `false`
- `authorization_state`: `R0B_EXECUTION_AUTHORIZATION_CONSUMED`
- `plan_status`: `R0B_COMPLETE`
- `current_stage`: `CLOSEOUT_COMPLETE_NO_FURTHER_EXECUTION_AUTHORIZED`
- `supersedes`: `PLAN_PHK_V23_R0A_COMPLETE`
- `preserves`: `PHK_V23_R0A_INCONCLUSIVE_AND_PHK_V22R_TERMINAL_NO_GO`
- `program_contract`: `configs/phk_v23/program_contract_r0b_minimal_v2.json`
- `method_contract`: `configs/phk_v23/method_contract_r0b_minimal_v2.json`
- `diagnostic_contract`: `configs/phk_v23/r0b_diagnostic_contract_minimal_v2.json`
- `decision`: `docs/adr/0050-activate-phk-v23-r0b-first-switch-175-minimal-v2.md`

## 论文去向与唯一问题

本阶段只服务于论文 Discussion/Methods failure analysis：识别从 scratch 到首次 W1→W1+W2 切换期间，哪一类机制最早获得持续的 reference-blind 支持。输出是 `PRIMARY_PRECURSOR_CANDIDATE`，不是因果根因、competence 恢复或方法增益。

当前强基线仍是旧 `STRONG_RAW`。本阶段没有 proposed method、方法消融或 formal OOD；其价值是决定未来最多一个 R1a 原子干预是否值得另立计划。两份 stress reference 保持 sealed/unread。

## 已完成的唯一执行链

1. `COMPLETED`：冻结三份 R0B minimal-v2 合同、ADR、单一 observer seam、runner、machine adjudicator、focused tests 与 AutoDL run card。
2. `COMPLETED`：本地 focused tests、受影响 legacy regression、ledger 与 `DOCUMENT_CONSISTENCY_VALID` 全过后才启动 GPU。
3. `COMPLETED`：source commit `8d072e2ece0668583adad4b3cefff3e978436f05` 已选择性推送；无关 dirty 未纳入。
4. `COMPLETED`：远端前检确认 V100、环境、空进程、source/contract identity 与预算；只运行一次 seed-17/FP64/STRONG_RAW scratch replay。
5. `COMPLETED`：`training_config.updates=1000` 保持科学 denominator，仅执行 175 canonical steps；step 151 为首次 W1+W2 refresh/update；cloud shadow steps 为 0。
6. `COMPLETED`：checkpoint、reference-blind telemetry、transition bundle、prediction、log、manifest、environment 与 summary 全部生成并回收。
7. `COMPLETED`：远端/本地哈希与身份全过后立即 shutdown；SSH 确认为 `Connection refused`。
8. `COMPLETED`：reference-blind adjudication 先写入，primary 为 `GRADIENT_STARVATION`；factorial 按门记录 `FACTORIAL_NOT_RUN_NOT_NEEDED`。
9. `COMPLETED`：随后才在本地生成 nominal non-voting appendix；它没有改变 primary 或授权。
10. `COMPLETED`：manifest、ledger、closeout 与状态已收口；不自动进入 R1、PJGR、stress 或第二次 run。

## 结果

- `VERIFIED`：`GRADIENT_STARVATION` 是最早持续前兆（step 10 起、step 25 确认）；`GRADIENT_CONFLICT` 与 `ELECTROTHERMAL_DRIVE_DEFICIT` 分别在 step 75/100 与 110/120 获得后续支持。
- `VERIFIED`：没有冻结的 switch shock，因此不运行 factorial。175-step prefix 的 nominal non-voting appendix 仍未重建两周期事件。
- `BOUNDARY`：结果不证明因果 root、competence 恢复或方法增益，不改写 V2.2R terminal No-Go。

## 预算与停止

- V100 paid work：soft stop 45 min，hard stop 60 min；增量估算费用 hard cap 5 CNY。
- 条件性本地 CPU factorial hard cap 2 h；不构造 optimizer、不更新参数。
- V2.3 全局 hard caps：34 GPU-h、95 CNY、从 ADR 激活起 14 days；项目绝对云成本 hard cap 150 CNY。
- 身份/GPU/合同漂移、reference 可达、observer state/RNG/grad 变化、非有限值、重复进程、预算超门、非 175 steps、错误 switch/refresh 或产物不完整均立即停止且不自动重跑。

## 完成后边界

R0B 的一次性执行授权已经消耗。R0A `R0A_INCONCLUSIVE`、V2.2R `MVP_NO_GO_NO_BASIC_COMPETENCE`、bounded-negative advisor draft 与两份 stress seal 均不可改写。下一步最多可规划一个以 phase-head gradient materiality 为单一轴的 R1a，但训练、GPU、R1、PJGR、stress、第二次 run、作者联系、投稿、投稿系统上传与凭据披露均未授权。证据见 [R0B closeout](../experiment/2026-08-31-phk-v23-r0b-first-switch-175-closeout.md)。
