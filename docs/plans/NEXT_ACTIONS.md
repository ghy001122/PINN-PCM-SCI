# PLAN-PHK-V2.3-LF3：GPU execution ready

- `phase_id`: `PHK_V23_LF3_MEASURE_DECOUPLED_STARTUP_SCALED_PHASE_LATENT_CARRIER_PILOT_EXECUTE`
- `lifecycle_state`: `CPU_QUALIFIED_GPU_EXECUTION_AUTHORIZED`
- `blocker_id`: `NONE`
- `claim_status`: `LF2_EVIDENCE_PRESERVED_LF3_CPU_QUALIFIED_NO_GPU_RESULT_YET`
- `next_research_execution_authorized`: `true`
- `authorization_state`: `LF3_CURRENT_USER_EXECUTE_ACTIVE`
- `plan_status`: `LF3_GPU_EXECUTION_READY`
- `current_stage`: `REMOTE_ZERO_STEP_PREFLIGHT_THEN_SOLE_GPU_TRAJECTORY`
- `supersedes`: `PLAN_PHK_V23_LF2_TERMINAL_DISPOSITION`
- `preserves`: `V22R_R0A_R0B_R0C_R1A_R1X_C0_LF0_LF1_LF2_EVIDENCE`
- `contracts`: `configs/phk_v23/{program_contract_lf3_phase_latent_carrier,method_contract_lf3_phase_latent_carrier,data_contract_lf3_phase_latent_carrier,decision_contract_lf3_phase_latent_carrier}.json`
- `decision`: `docs/adr/0059-activate-phk-v23-lf3-phase-latent-carrier-pilot.md`
- `next_recommendation`: `EXECUTE_SOLE_T0_TO_CONDITIONAL_P0_AND_ADJUDICATE`

## 当前执行序列

1. 已完成四合同、实现、focused tests、prior-art closure、零步 CPU 资格和 hash-bound bundle。
2. 精确部署 bundle、medium 与 LF1-B0 checkpoint，运行 remote zero-step preflight。
3. preflight 通过后运行 T0 恰好 1200 updates；T0 carrier gate 失败即停止。仅当全通过时，从精确 T0 权重以新 Adam 运行 P0 恰好 1200 updates，其中前 550 步冻结 phase head、后 650 步联合更新；P0 零 label/replay/anchor。
4. 回收 summary-bound 全部产物并逐项核验；终止训练进程、关机并确认 SSH 拒绝。
5. 关机后本地运行 frozen nominal evaluation，按 carrier、single-seed PINN Pareto、direct `LF_ONLY` candidate signal 三层裁决，完成 advisor draft、closeout、manifest 和精确白名单 Git 交付。

## 停止边界

最多一条科学 GPU 轨迹、2400 updates、1800 秒；达到冻结机器结局立即停止。不运行 D0、第二臂、参数 sweep、matched ablation、新 seed、OOD、stress、PJGR/R2 或 kinetic teacher。T0 失败时 P0 是 `NOT_TRIGGERED` 而非失败。无关 dirty 工作树保持不动。

## 论文去向

本轮必须形成 `paper/paper_v23/` 导师初稿。若 LF3 阴性，写成不夸大的 failure-analysis + solver-recovery 边界；若有 Level 2，只写 single-seed nominal within-architecture PINN-specific pilot；只有 Level 3 才记 provisional candidate signal，且仍需新授权的 matched output-phase ablation、多 seed 与 formal OOD/stress 才可能升级为投稿级正面方法。两份 stress references 继续 sealed/unread。
