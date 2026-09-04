# PHK-V2.3 LF2 measure-calibrated feasible PINN 收口

- `phase_id`: `PHK_V23_LF2_MEASURE_CALIBRATED_FEASIBLE_PINN_EXECUTE`
- `lifecycle_state`: `COMPLETE`
- `machine_outcome`: `LF2_CALIBRATED_CARRIER_NOT_ESTABLISHED`
- `scientific_gpu_trajectories`: `1/1`
- `m0_updates`: `1200`
- `m1_updates`: `0_NOT_TRIGGERED`
- `candidate`: `none`
- `next_research_execution_authorized`: `false`
- `next_recommendation`: `PHASE_LATENT_TEACHER_BACKUP_REQUIRES_NEW_EXECUTE`
- `stress_reference_status`: `TWO_STRESS_REFERENCES_SEALED_UNREAD`

## 结论

`VERIFIED`：LF2 的 evaluator-compatible target-measure M0 显著降低了 LF1-B0 的三项全-medium 加权场误差，但没有建立准确事件 carrier。M0 的 potential、temperature、phase weighted-MSE ratio 分别为 `0.257104/0.0654992/0.273361`，potential maximum-principle 通过；与此同时，`phase_max` 从 LF1-B0 的 `0.754197` 降为 `0.0299479`，两个周期的 hard recall、active mass 和 event 全部归零。

冻结 full-medium gate 因此给出：

```text
LF2_CALIBRATED_CARRIER_NOT_ESTABLISHED
→ M1_NOT_TRIGGERED
→ PHASE_LATENT_TEACHER_BACKUP_REQUIRES_NEW_EXECUTE
```

M1 没有运行，不能写成 M1 失败。M0 是 data-only 校准阶段，不能把本次终局包装为完成的 PINN refinement，更不能声称 PINN-specific gain。candidate 为 none。

## 首步前工程故障与同身份重执行

首次远端启动在 `load_case_physics()` 的身份绑定阶段发现 source bundle 遗漏 `tests/test_phk_v21_benchmark.py`。进程在模型、Adam 和 optimizer 构造前退出，输出目录为空，optimizer update 和科学轨迹均为 0。console 与 exit-code 已回收，SHA-256 分别为 `8A8BC090...C7343` 与 `4355A46B...DD865`。

修复只补齐既有传递依赖，并新增在空隔离目录中真实调用 `load_case_physics("FULL")` 的回归；科学合同、medium、checkpoint、seed、loss、采样、门槛和预算均未变化。修复提交为 `841c7e2d8650a0283d74915155e68a4107b1c2c3`，工程重执行 source identity 为 `LF2-BUNDLE-9D06E26720363A39E5CC62D87E1B494A4AFA0116EEA727A103DB6B5FB2ABD455`。远端零步 preflight 通过后才开始唯一科学轨迹。

## 唯一 GPU 轨迹

| identity | device | seed/dtype | M0 | M1 | wall | GPU h | displayed price | estimated cost |
|---|---|---|---:|---:|---:|---:|---:|---:|
| `LF2_MEASURE_CALIBRATED_FEASIBLE_PINN` | Tesla V100-PCIE-32GB | 17 / FP64 | 1200 | 0 | 83.8726 s | 0.0232979 | 1.88 CNY/h | 0.0438001 CNY |

M0 使用独立 stateful deterministic Sobol target-measure stream，恰好 1200 draws，rolling SHA-256 为 `6E9957E8...8F28`；没有构造或推进 physics sampler，physics hash ledger 为 0 行、空文件 SHA-256。云端只读取 frozen medium carrier 与精确 LF1-B0 checkpoint，没有 fine、extra-fine、frozen evaluator 或 stress I/O。

## M0 full-medium gate

| 项目 | LF1-B0 | LF2-M0 | gate |
|---|---:|---:|---|
| phase weighted MSE | 0.0566884 | 0.0154964 | ratio 0.273361，PASS |
| temperature weighted MSE | 0.0112203 | 0.000734920 | ratio 0.0654992，PASS |
| potential weighted MSE | 0.000295493 | 0.0000759726 | ratio 0.257104，PASS |
| phase maximum | 0.754197 | 0.0299479 | FAIL，要求 ≥0.9 |
| two-cycle events | true | false | FAIL |
| hard recall cycle 1/2 | 0.898625 / 0.944646 | 0 / 0 | FAIL |
| hard active-mass ratio cycle 1/2 | 5.26976 / 5.86388 | 0 / 0 | FAIL |
| event time error cycle 1/2 | 0.04462 / 0.05178 | undefined / undefined | FAIL |
| potential validity | PASS | PASS | PASS |

所有值有限。M0 topology weighted loss 为 `0.0540840`，最终 augmented-Lagrangian 项为 `1249.218`；高约束代价与 hard gate 同时显示事件约束没有被满足，不能用较低的全局 field error 覆盖。

## 关机后的本地 nominal 裁决

全部运行产物完成远端/本地 size 与 SHA-256 对账后，AutoDL 被立即关闭；TCP 探测失败且 SSH 明确返回 `Connection refused`。只有此后本地 evaluator 才读取 nominal fine/extra-fine。canonical adjudication 为：

```text
outputs/runs/20260904T074000Z-phk-v23-lf2-local-adjudication-841c7e2-er1/adjudication.json
SHA256=D37EDDD10BBDC183C30DF973C1031599D4A303A891B9FB1AF4EC909EFAAD75A4
```

| role | event competent | phase ROI RMS | phase symmetric diff | T ROI RMS | current NRMSE | event failures |
|---|---|---:|---:|---:|---:|---:|
| direct `LF_ONLY` | true | 0.00657038 | 0.000349531 | 0.00180069 | 0.00352214 | 0 |
| LF1 `B0_LF_DATA_ONLY` | true | 0.163446 | 0.0174370 | 0.0545925 | 0.256194 | 0 |
| LF1 `B_FINAL` | true | 0.214459 | 0.0205948 | 0.0793024 | 0.138757 | 0 |
| `LF2_M0_CALIBRATED_CARRIER` | false | 0.110564 | 0.00515 | 0.0175980 | 0.146374 | 6 |

LF2-M0 的 potential RMS 为 `0.00616749`，pulse-energy relative error 为 `0.0911309`，hotspot-location error 为 `0.0125`。固定 seed-17301 reference-blind physics pool SHA-256 为 `FD285AFC...E64CF`，M0 objective 为 `0.571770`；M1/final 不存在，因此 final/M0 physics ratio 未定义且不可裁决为通过。

## 科学解释边界

- `VERIFIED`：target measure 修正了 LF1-B0 的全局连续场误差，却抹除了稀疏两周期事件；M0 gate 失败，M1 未触发，无 candidate。
- `SUPPORTED_INTERPRETATION`：sampling-measure mismatch 是 LF1 过宽事件 carrier 的真实因素，但全局 measure calibration 仍偏好占测度绝对多数的冷态背景，不能单独保护稀有事件拓扑。
- `HYPOTHESIS`：若另行授权，最小后备应直接监督 phase latent 或 kinetic RHS，使事件动力学信号绕开当前 cold-state 表示/优化盆地；延长 M0、增大同一 field loss、换 optimizer 或绕过门禁运行 M1 都缺少针对性。
- `UNKNOWN`：phase-latent teacher 能否建立合法两周期 carrier；之后 full physics 能否相对 direct `LF_ONLY` 和 LF1-B0 形成冻结容限内的 PINN-specific Pareto；多 seed、stress、formal OOD 与投稿级有效性。

该结果只属于 single-seed nominal fixed-discretization development evidence；不外推为 PINN 类失败、物理模型失败、continuum truth、实验验证或投稿结论。

## 回收、验证与生命周期

有效运行共回收 13 个文件；summary 绑定的 10 个产物全部逐项通过远端/本地 size 与 SHA-256 对账。checkpoint、prediction、完整日志和 local adjudication 保留在 git-ignored `outputs/runs/`。20 项 LF2 focused tests 与覆盖 LF2/LF1/LF0/C0/R0/R1/V2.2R/ledger/document-consistency 的 227 项回归全部通过；终局 JSON、实验账本与仓库文档一致性另行严格校验。

两份 stress references 始终 `TWO_STRESS_REFERENCES_SEALED_UNREAD`。本 campaign 完成后不自动授权 phase-latent teacher、PJGR/R2、多 seed、stress、formal OOD 或投稿。机器证据见 [compact artifact](artifacts/20260904T074000Z-phk-v23-lf2-terminal-841c7e2.json)，运行身份见同名 manifest。
