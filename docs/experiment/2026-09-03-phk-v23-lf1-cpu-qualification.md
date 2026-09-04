# PHK-V2.3 LF1 CPU qualification

- `phase_id`: `PHK_V23_LF1_EVENT_PRESERVING_MULTIFIDELITY_PILOT`
- `run_id`: `20260903T113005Z-phk-v23-lf1-cpu-qualification-dc091be`
- `base_commit`: `dc091be9079768244a09cc5bf1ffb06791f4303c`
- `source_identity`: `LF1-BUNDLE-6A0583CD6EEA23280365E9E575BCAFDE793A6BC84F27B367328AF40DBA9DCDCE`
- `gate_outcome`: `LF1_CPU_QUALIFICATION_PASS`
- `next_research_execution_authorized`: `true`
- `next_action`: `REMOTE_ZERO_STEP_PREFLIGHT_THEN_RUN_A`

## VERIFIED

- 只读重放旧 LF0 sampler 的 800 个 draws，共 819,200 points；cycle 1/2 event points 分别为 1,783/1,595，占全部点 `0.0021765/0.0019470`。
- 旧 B0 对 direct LF_ONLY event support 的两周期 recall 均为 0，预测 active point 均为 0。event phase normalized MSE 为 `1.42375/1.48328`，background complement 为 `0.00309498`。
- 旧 B0 的 4,096 个 event-support probes 中，phase output Jacobian 中位数 `1.01862`，5%–95% 为 `0.50027–1.73926`；没有 phase transform saturation 证据。
- 六个冻结 pool 均非空：event `1164/1102`、transition `7888/14796`、recovery `16600/15170`。
- 新 range-preserving exact-top transform 对 medium 441,600 个可重构点全部可容许；最大重构误差 `1.11e-16`，latent derivative 最大误差 `1.09e-16`，top-zeta derivative 最大误差 `3.64e-12`。

## SUPPORTED_INTERPRETATION

LF0 B0 的首要可操作阻塞是 event support 在普通总体 field sampling/loss 中被稀释；phase 表示本身仍有有效 Jacobian。旧 B0 potential violation 与 direct LF_ONLY event support 的交集为 0，因此 potential invalidity 是必须修复的独立 validity seam，但不是缺失事件的充分解释。

## 边界

本资格运行没有 optimizer step、GPU、fine/extra-fine reference evaluation 或 stress I/O。它只准入 LF1 Run A，不是 PINN competence、方法增量或论文正面结果。

## 证据入口

- [CPU qualification artifact](artifacts/20260903T113005Z-phk-v23-lf1-cpu-qualification-dc091be.json)
- [run manifest](manifests/20260903T113005Z-phk-v23-lf1-cpu-qualification-dc091be.json)
- [deployed source manifest](../../cloud/phk_v23_lf1_autodl/deployed-source-manifest.json)
