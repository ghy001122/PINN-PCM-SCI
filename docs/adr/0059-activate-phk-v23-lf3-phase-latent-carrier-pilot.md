# ADR 0059：激活 PHK-V2.3 LF3 phase-latent carrier pilot

- `status`: `ACCEPTED_EXECUTING`
- `date`: `2026-09-04`
- `phase_id`: `PHK_V23_LF3_MEASURE_DECOUPLED_STARTUP_SCALED_PHASE_LATENT_CARRIER_PILOT_EXECUTE`
- `starting_head`: `6ec084cbffcbbd754da3aaff191ffb1862a20b0e`
- `preserves_scientific_evidence`: `V22R_R0A_R0B_R0C_R1A_R1X_C0_LF0_LF1_LF2`

## 决定

执行唯一一条 V100/FP64/seed-17、最多 2400 optimizer updates 的 `T0 -> conditional P0` 科学轨迹。T0 从精确 LF1-B0 权重以 fresh Adam 启动：V/T 使用 target measure，phase 使用 14 个互斥类别等权的 startup-scaled 完整 logit-increment teacher。只有 T0 通过冻结 full-medium carrier gate 才运行 P0；P0 不再读取任何 label，先冻结 phase head 550 步，再以同一 P0 optimizer 联合 full-physics continuation 到 1200 步。

取消独立 D0。LF2 raw 日志中 AL 从早期压倒 field/topology objective、事件快速消失与乘子尖峰，只支持 AL 接口失效解释，不保证 LF3 成功。仅保留零步 phase-logit 数学可容许性和 LF2 matched-stream 身份检查。

## 科学与论文身份

快速一手来源闭包未发现完整功能同构碰撞，但 logit distillation、类别重平衡、exact boundary、phase-field PINN 与 physics-informed fine-tuning 均有先例。LF3 冻结为 `ATTRIBUTED_SOLVER_RECOVERY_COMBINATION_PILOT`，不是 headline novelty。

裁决分三层：T0 carrier success；P0 相对同架构 T0 的 single-seed PINN-specific Pareto pilot；相对 direct `LF_ONLY` 的 candidate/paper-positive signal。前两层不能降格强直接基线；若仍远差于 `LF_ONLY`，只允许 failure-analysis/solver-recovery 叙事，不允许精度优越、效率、OOD、泛化或投稿级方法 claim。

## 停止与后续边界

T0 不通过即停止且不称 P0 失败。P0 不保持 carrier 或不产生冻结 physics Pareto 即收口。无论结果如何，不自动增加 GPU 臂、seed、output-phase matched ablation、OOD、stress、PJGR/R2、kinetic teacher 或投稿；这些均需新授权。无关 dirty 工作树必须原样保留，禁止自动 stash/reset/clean/restore/checkout/delete/move。

精确机器定义见 LF3 [program](../../configs/phk_v23/program_contract_lf3_phase_latent_carrier.json)、[method](../../configs/phk_v23/method_contract_lf3_phase_latent_carrier.json)、[data](../../configs/phk_v23/data_contract_lf3_phase_latent_carrier.json) 与 [decision](../../configs/phk_v23/decision_contract_lf3_phase_latent_carrier.json) 合同；来源边界见 [prior-art closure](../references/2026-09-04-phk-v23-lf3-prior-art-closure.md)。
