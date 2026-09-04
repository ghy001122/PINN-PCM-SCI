# ADR 0058：激活 PHK-V2.3 LF2 measure-calibrated feasible PINN

- `status`: `ACCEPTED_ACTIVE`
- `date`: `2026-09-04`
- `phase_id`: `PHK_V23_LF2_MEASURE_CALIBRATED_FEASIBLE_PINN_EXECUTE`
- `supersedes_authorization_only`: `PHK_V23_LF1_EVENT_PRESERVING_MULTIFIDELITY_PILOT_COMPLETE`
- `preserves_scientific_evidence`: `V22R_R0A_R0B_R0C_R1A_R1X_C0_LF0_LF1`

## 决定

接受用户当前明确的完整执行授权，运行唯一一条 V100/FP64/seed-17、最多 2400 updates 的 nominal trajectory。M0 从精确 LF1-B0 model weights 开始，用评价兼容的 trapezoid-time × cell-volume 目标测度、14 类互斥穷尽分层、field/topology loss 与逐步 inequality augmented Lagrangian 做 1200-step data-only 校准；M0 不构造或推进 physics sampler。只有固定 full-medium gate 全部通过，M1 才用新 Adam、原 full-physics objective、与 LF1 逐步相同的 1200 个 physics batches，以及相对 M0 的显式可行性不等式继续 1200 steps。

## 选择理由

LF1-B0 已有两周期事件，却把 event active mass 放大到 medium teacher 的约 `5.27/5.86` 倍，precision 约 `0.17/0.16`，event time 提前约 `0.045/0.052`。CPU 资格进一步证明 LF1 提案相对 evaluator-compatible target measure 对 onset event 平均放大约 `176.5x`，persistent replay 约 `353.0x`。因此首要可证伪问题是 sampling objective 与评价测度失配，而不是继续延长过采样、增加固定 replay 权重或换 optimizer。

## 方法与来源边界

分层 importance estimator 属于已知抽样思想；multi-fidelity neural-network 背景归因于 [arXiv:1903.00104](https://arxiv.org/abs/1903.00104)，不等式 augmented-Lagrangian/PINN 背景归因于 [arXiv:2109.14860](https://arxiv.org/abs/2109.14860)。本阶段不对这些组成部分主张原创性；唯一候选身份只是“measure-calibrated rare-event transfer + feasibility-constrained full-physics interface”的组合，且必须由冻结增量门支持。

## 证据与停止边界

M0 任一 full-medium gate 失败即停止且不进入 M1；M1 可行性失败即保留有界负结果。只有 M0/final 均通过数值、事件与冻结 nominal competence，final 相对 M0 和 direct `LF_ONLY` 非劣，且固定 physics objective ratio `<=0.5`，才允许 single-seed `PROVISIONAL_SIGNAL`。无论结果如何都不自动授权多 seed、stress、formal OOD、phase-latent teacher、PJGR/R2 或投稿。

精确机器合同见 [program](../../configs/phk_v23/program_contract_lf2_measure_calibrated_feasible_pinn.json)、[method](../../configs/phk_v23/method_contract_lf2_measure_calibrated_feasible_pinn.json)、[data](../../configs/phk_v23/data_contract_lf2_measure_calibrated_medium.json) 与 [decision](../../configs/phk_v23/decision_contract_lf2_measure_calibrated_feasible_pinn.json)。CPU 准入事实见 [qualification](../experiment/2026-09-04-phk-v23-lf2-cpu-qualification.md)。
