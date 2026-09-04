# PLAN-PHK-V2.3-LF2：measure-calibrated feasible PINN

- `phase_id`: `PHK_V23_LF2_MEASURE_CALIBRATED_FEASIBLE_PINN_EXECUTE`
- `lifecycle_state`: `ACTIVE`
- `blocker_id`: `NONE`
- `claim_status`: `V22R_R0_R1A_R1X_C0_LF0_LF1_EVIDENCE_PRESERVED_LF2_CPU_QUALIFIED_GPU_RESULT_PENDING`
- `next_research_execution_authorized`: `true`
- `authorization_state`: `EXPLICIT_USER_EXECUTE_ACTIVE`
- `plan_status`: `LF2_GPU_EXECUTION_READY`
- `current_stage`: `REMOTE_ZERO_STEP_PREFLIGHT_PENDING`
- `supersedes`: `PLAN_PHK_V23_LF1_TERMINAL_COMPLETE`
- `preserves`: `V22R_R0A_R0B_R0C_R1A_R1X_C0_LF0_LF1_EVIDENCE`
- `contracts`: `configs/phk_v23/{program_contract_lf2_measure_calibrated_feasible_pinn,method_contract_lf2_measure_calibrated_feasible_pinn,data_contract_lf2_measure_calibrated_medium,decision_contract_lf2_measure_calibrated_feasible_pinn}.json`
- `decision`: `docs/adr/0058-activate-phk-v23-lf2-measure-calibrated-feasible-pinn.md`
- `next_recommendation`: `REMOTE_ZERO_STEP_PREFLIGHT_THEN_SOLE_LF2_TRAJECTORY`

## 当前关键路径

1. 将精确 LF2 source bundle、medium carrier、LF1-B0 checkpoint 上传到隔离部署根；按 live price 执行零 optimizer-step preflight。
2. 若 preflight 通过，运行唯一 trajectory：M0 1200-step target-measure data-only calibration；仅当 M0 full-medium gate 通过时运行 M1 1200-step full physics + feasibility inequalities。
3. 回收 summary 及其全部绑定文件，在本地逐项复算大小与 SHA256；随后立即关闭实例并以 SSH refused 证明关机。
4. 关机后在本地用未修改 frozen evaluator 比较 LF1 A、direct LF_ONLY、LF1 B0、LF1 B final、LF2 M0 与存在时的 LF2 final；同时计算固定 seed-17301 physics objective 和逐步 batch identity。
5. 按七类机器结局唯一映射生成 terminal artifact/manifest/closeout，关闭授权并精确提交、推送。

## Go/No-Go 与止损

- CPU 资格已经通过；远端身份或边界失败时不得开始 optimizer。
- M0 任一数值、potential、两周期事件、recall/precision/mass/event-time 或 V/T/phase 误差门失败，立即以相应 terminal outcome 停止，不运行 M1。
- M1 只使用原 full physics objective 与 AL feasibility constraints；不加固定 replay weight、不做 sweep、不做 checkpoint selection。
- 第一科学步后不授权工程重跑；最多一条 LF2 科学轨迹。stress、PJGR/R2、phase-latent teacher、新 seed 与 formal OOD 均保持关闭。

## 论文映射

M0 回答“评价测度校准能否把 LF1 的过宽事件 carrier 修回准确可容许状态”；M1 回答“full physics residual 能否在显式 accuracy/event 可行域内下降”。只有冻结 provisional gate 全部通过才能形成 single-seed nominal candidate；其余结果进入 failure-analysis 与强 non-PINN baseline 叙事，不夸大为一般 PINN 失败。
