# PHK-V2.3 LF2 CPU qualification

- `phase_id`: `PHK_V23_LF2_MEASURE_CALIBRATED_FEASIBLE_PINN_EXECUTE`
- `run_id`: `20260904T064642Z-phk-v23-lf2-cpu-qualification-e7f3152`
- `base_commit`: `e7f31523823675a90aee26f8703e71ebaff2f536`
- `source_identity`: `LF2-BUNDLE-AB0756BF7D4CBDCFDCA88F48C5BBB882760D586C65089999DA16F1DFA64E4AA3`
- `gate_outcome`: `LF2_CPU_QUALIFICATION_PASS`
- `next_research_execution_authorized`: `true`
- `next_action`: `REMOTE_ZERO_STEP_PREFLIGHT_THEN_SOLE_LF2_TRAJECTORY`

## VERIFIED

- medium 的 1,603,200 个 saved nodes 按优先级全部且仅分配到 14 类；所有类非空，目标测度质量和为 `0.9999999999999996`，分区哈希为 `EFD70886...B7A515`。
- 两周期 event 类目标测度质量分别为 `0.0007275/0.00068875`。LF1 的固定提案相对该测度平均放大 onset event `176.5225x`，persistent replay 平均放大 `353.0450x`。
- LF1-B0 全 medium 复算有限且 potential maximum-principle 通过；两周期 recall 为 `0.89863/0.94465`，但 precision 仅 `0.17052/0.16110`、active-mass ratio 为 `5.26976/5.86388`，event-time error 为 `0.04462/0.05178`。
- 冻结 target-measure estimator 通过常数恒等测试，绝对误差 `1.33e-15`；M0/M1 两条独立 stateful Sobol 流的 seed、调用顺序、首批与 8-draw rolling hash 已固定。
- 精确 LF1-B0 checkpoint 以 model weights only 方式加载，参数均为 FP64；M0 不构造或推进 physics sampler，M1 的首个 physics batch 与 LF1 的冻结 hash `5DEBCD...C2433` 相同。
- 100 项相关 focused/regression tests 通过；资格运行没有科学模型 optimizer update、GPU、fine/extra-fine evaluator I/O 或 stress I/O。

## SUPPORTED_INTERPRETATION

LF1 已解决“事件完全看不见”，但其均匀加权 minibatch objective 并不等价于冻结评价测度：事件支撑被放大约两个数量级，产生过早、过宽的 active region。LF2 因此先检验 measure-calibrated M0 是否能建立准确、可容许的 carrier，再检验 inequality-constrained full physics 能否形成 accuracy–physics Pareto；它不把数据迁移能力预先算作 PINN 增量。

## 边界

本记录只准入合同内唯一 V100/FP64/seed-17 trajectory。它不是 M0 成功、PINN competence、PINN-specific gain、多 seed、stress、formal OOD、continuum truth 或投稿级证据。phase-latent teacher、PJGR/R2、新 seed 与任何额外 GPU 轨迹仍未授权。

## 证据入口

- [compact qualification](artifacts/20260904T064642Z-phk-v23-lf2-cpu-qualification-e7f3152.json)
- [run manifest](manifests/20260904T064642Z-phk-v23-lf2-cpu-qualification-e7f3152.json)
- [deployed source manifest](../../cloud/phk_v23_lf2_autodl/deployed-source-manifest.json)
- [ADR 0058](../adr/0058-activate-phk-v23-lf2-measure-calibrated-feasible-pinn.md)
