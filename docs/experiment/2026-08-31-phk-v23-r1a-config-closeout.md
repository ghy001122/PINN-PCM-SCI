# PHK-V2.3 R1a ConFIG competence-recovery 收口

- `date`: `2026-08-31`
- `run_id`: `20260831T144554Z-phk-v23-r1a-config-5d8accc`
- `task_id`: `PHK_V23_R1A_CONFIG_COMPETENCE_RECOVERY`
- `execution_status`: `COMPLETED`
- `r1a_outcome`: `R1A_CONFIG_RAW_NO_COMPETENCE`
- `competence_recovered`: `false`
- `method_gain_proven`: `false`
- `claim_status`: `V22R_TERMINAL_NO_GO_PRESERVED_R1A_CONFIG_RAW_NO_COMPETENCE_NO_METHOD_EVIDENCE`
- `next_research_execution_authorized`: `false`
- `stress_reference_status`: `TWO_STRESS_REFERENCES_SEALED_UNREAD`

## 总裁决

`VERIFIED`：唯一一次 V100/FP64/seed-17 `STRONG_RAW` scratch R1a 完成了 `1000/1000` 个 Adam updates，并在每一步以标准 ConFIG 合成四个冻结 loss groups 的梯度。云端训练和 prediction reference-blind；产物回收、远端/本地哈希核验及 AutoDL 关机完成后，才在本地运行冻结 nominal evaluator。

机器裁决为：

```text
status = R1A_CONFIG_RAW_NO_COMPETENCE
competence_recovered = false
cycle_1 = event_missing + ROI_peak_below_minimum + recovery_failure
cycle_2 = event_missing + ROI_peak_below_minimum + recovery_failure
stress_unseal_authorized = false
next_research_execution_authorized = false
```

ConFIG 在全部 12 个冻结机制节点上都产生了与四个 group gradients 正向的合成方向，但预测在整个时轴的 `phase >= 0.5` 活动比例仍为 `0`，两个参考相变事件均未重建。因此本轮只支持一个有边界的负面结论：**单独用标准 ConFIG 处理四组多目标方向冲突，不足以恢复该冻结 strong-raw solver 的 two-cycle event competence。**

## 执行身份与完整性

`VERIFIED`：

- 执行 source commit：`5d8accc0ac3d4bee81f696d400afac6bdd0eef32`；部署身份：`R1A-CONFIG-BUNDLE-D37FE6C0C044109EAF5EA583680D69A94D6F9830C687F0C330C120C4B3928244`。
- 设备：`Tesla V100-PCIE-32GB`；dtype：FP64；seed：17；arm：`STRONG_RAW`；初始化：scratch；updates：1000。
- 冻结物理对象、三独立 heads、原 Sobol sampler、causal windows、512/128/128 点数、Adam `lr=1e-3`、clip 10 与 frozen evaluator 均未改变。
- 唯一训练轴是 `legacy total.backward()` 改为四组标准 ConFIG 梯度合成后仍由同一个 Adam step 更新；适配源为 Liu、Chu、Thuerey 的 ConFIG，官方实现 commit `94862437f451f175673bce9c85f3e14bd9182c21`，MIT 许可。它是透明归因的 shared solver backbone，不是本项目原创方法。
- `G1+G2+G3+G4` 与旧总目标在冻结 FP64 容差内一致；1000 次 ConFIG application、12 条机制记录均完成，无 zero-norm group、非有限值或 clipping 触发。
- 含 prediction 的 wall time 为 `606.016834 s`，即 `0.168338 h`；按 AutoDL 公开 V100 单价 `1.88 CNY/h` 估算增量费用 `0.316475 CNY`，累计项目展示单价估算约 `5.247094 CNY`。均不是平台账单。
- checkpoint、training log、start/final manifests、mechanism telemetry、prediction 和 environment 全部回收；7 项 summary-bound artifacts 的本地 hash/size 与 summary 一致。远端/本地 summary SHA-256 同为 `62EBC51A...DE22`。
- 云端没有 nominal/stress reference 路径，run summary 固定 `reference_fields_read=false` 与 `stress_fields_or_metrics_read=false`。

## AutoDL 关机

`VERIFIED_INFRASTRUCTURE_ONLY`：产物回收并完成远端/本地 summary SHA-256 对照后执行 `/usr/bin/shutdown -h now`。关机后 SSH 探针返回 `Connection refused`；本阶段 GPU 使用已结束。

## 冻结评价

### VERIFIED

- prediction 全网格 `phase_max=0.0299932`，`phase>=0.5` 活动比例为 `0`；`temperature_max=0.103909`。
- cycle 1 与 cycle 2 的 event time 均为 `null`，ROI peak 与 recovery fraction 均为 `0`；实际 hard-guard failures 恰为每周期三项，共六项。
- primary `time_averaged_phase_region_symmetric_difference=0.00515`；co-primary `phase_roi_continuous_rms=0.110516`。前者仍是稀疏事件被全域平均稀释后的数值，不能解释为预测准确。
- PDE loss 从 `0.117633` 降至 `0.00326393`，final/first ratio 为 `0.0277467`。该下降没有构成 event competence。
- `phase_high_k_relative_error=0.999909`，`temperature_roi_rms=0.171987`，`terminal_current_trace_nrmse=0.267106`，`pulse_energy_relative_error=0.555933`。

### SUPPORTED_INTERPRETATION

- ConFIG 的最小 frozen combined cosine 为正值 `0.0425029`，说明所实现的 conflict-free direction 机制按定义工作；但它没有把相态推离冷态吸引子。
- 因而“观察到梯度冲突”不等于“消除冲突即可恢复相变事件”。当前失败更可能需要一个同时改变训练时序、驱动传递或相态动力学可学习性的后续复合 backbone；具体组合仍需另立合同，不得从本轮自动推断。

### UNKNOWN

- 预声明的 R1b 复合 solver backbone 能否恢复 competence。
- competent raw 背景是否存在，以及 PJGR 是否有独立增量。
- 其他 seed、stress、formal OOD、连续体真值、材料校准或实验有效性。

## 产物与边界

- [compact machine artifact](artifacts/20260831T144554Z-phk-v23-r1a-config-5d8accc.json)
- [experiment manifest](manifests/20260831T144554Z-phk-v23-r1a-config-5d8accc.json)
- raw run：`outputs/runs/20260831T144554Z-phk-v23-r1a-config-5d8accc/`（git-ignored）

本阶段在 `R1A_CONFIG_RAW_NO_COMPETENCE` 收口。不得自动执行 R1b、PJGR、第二个 seed、延长训练、添加模块、stress prediction/unseal、作者联系或投稿。本记录不 supersede PHK-V2.2R terminal No-Go、R0A/R0B/R0C closeout、bounded-negative advisor draft 或 stress seals。
