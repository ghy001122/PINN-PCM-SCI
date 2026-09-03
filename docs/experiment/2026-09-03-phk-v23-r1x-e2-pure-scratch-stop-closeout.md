# PHK-V2.3 R1X E2 top-Dirichlet hard-lift 与 pure-scratch campaign 收口

- `date`: `2026-09-03`
- `run_id`: `20260903T010712Z-phk-v23-r1x-e2-top-hard-lift-ce64086`
- `task_id`: `PHK_V23_R1X_BOUNDED_CLEAN_COUPLING_CAMPAIGN_EXECUTE`
- `trajectory`: `PHK_V23_R1X_E2_TOP_DIRICHLET_HARD_LIFT`
- `evidence_role`: `NON_VOTING_DEVELOPMENT_EXPLORATION`
- `execution_status`: `COMPLETED_EARLY_POLICY_STOP`
- `machine_outcome`: `PURE_SCRATCH_EXPLORATION_STOP`
- `campaign_outcome`: `PURE_SCRATCH_COMPETENCE_RECOVERY_FAILED`
- `competence_recovered`: `false`
- `method_gain_proven`: `false`
- `confirmation_executed`: `false`
- `next_research_execution_authorized`: `false`
- `stress_reference_status`: `TWO_STRESS_REFERENCES_SEALED_UNREAD`

## 裁决

`VERIFIED`：E2 按冻结机器树在 V100/FP64/seed-17 `STRONG_RAW` 上从 scratch 执行。唯一单轴变化是 potential top-Dirichlet hard lift；运行完成 300 个 electrothermal warm-up updates 后，steps 200/225/250/275/300 的 readiness 检查全部失败，因而按 policy 停止，没有进入 phase ramp 或 full-physics closure。

hard lift 确实把 top potential BC RMS 压到 `0`，并使 W1/W3 ROI 的 QJ q95 明显高于 E1；全局 `Tmax` 也达到 `0.814532`，step 300 仍为 `0.745668`。但冻结 readiness 需要两窗同时满足局域热激活与 cold kinetic-growth：W1 thermal activation 在五次检查中始终为 `0`，W1/W3 positive cold kinetic-growth 均始终为 `0`。全局高温不能替代这一局域、两周期 readiness 条件。

最终 reference-blind prediction 的 `phase_max=0.0295885`、`phase>=0.5 activity=0`，且从未达到 material phase-signal 门。完整回收并核验产物后，本地 frozen nominal evaluator 仍判定两个周期各自失败 event、ROI peak 和 recovery 三项。冻结树因此禁止 E3 和 confirmation，并终止 pure-scratch campaign：

```text
E1_ET_NOT_READY
→ E2_TOP_DIRICHLET_HARD_LIFT
→ ET_NOT_READY + NO_MATERIAL_PHASE_SIGNAL
→ PURE_SCRATCH_EXPLORATION_STOP
→ PURE_SCRATCH_COMPETENCE_RECOVERY_FAILED
```

不得利用未消耗的第三条 exploration 数量槽绕过机器分支。后续只可在新合同与新执行授权下进入 low-fidelity-guided route，或保留当前 bounded-negative package。

## 运行身份与完整性

- 执行 source commit：`ce64086cf4fee3ad5a7a6eaf39ad707f56989b6e`；部署身份：`R1X-BUNDLE-5A8288C5F89B0D0B452853858E63BDE2BD7320D2108D03F799FFE044F1F6216B`。
- 设备：`Tesla V100-PCIE-32GB`；dtype：FP64；seed：17；arm：`STRONG_RAW`；初始化：scratch。
- 同一 Adam、standard ConFIG、纯 Sobol、512/128/128 点数、accelerated windows 和 `alpha=0` cold-state warm-up 均保持冻结身份。
- optimizer updates 为 `300/1800`；这是 readiness policy 的正式停止，不是人工 early stopping。phase head 在 warm-up 中保持冻结；ramp updates=`0`，full-physics joint updates=`0`。
- 含 prediction 的 wall time 为 `177.707108 s`（`0.0493631 GPU h`）；按实时记录单价 `1.88 CNY/h` 估算费用 `0.0928026 CNY`。费用仅为报告字段。
- checkpoint、training log、telemetry、prediction、start/final manifests、environment、summary 与 console log 全部回收，远端/本地 size 与 SHA-256 一致。
- 云端 `reference_fields_read=false`、`stress_fields_or_metrics_read=false`。本地 nominal evaluation 只在全部产物回收与哈希核验后开始，且没有把 reference 送回云端或进入训练决策量。

## Readiness 与最终量

| step | ready | ROI T activation W1/W3 | cold growth W1/W3 | ROI QJ q95 W1/W3 | global Tmax |
|---:|---|---|---|---|---:|
| 200 | false | 0 / 0.275641 | 0 / 0 | 0.187633 / 0.149015 | 0.814532 |
| 225 | false | 0 / 0.237179 | 0 / 0 | 0.198396 / 0.162274 | 0.788508 |
| 250 | false | 0 / 0.230769 | 0 / 0 | 0.219576 / 0.182564 | 0.783615 |
| 275 | false | 0 / 0.0769231 | 0 / 0 | 0.214320 / 0.170469 | 0.751805 |
| 300 | false | 0 / 0.0576923 | 0 / 0 | 0.216772 / 0.164134 | 0.745668 |

- final top potential BC RMS=`0`；heater BC RMS=`0.157321`。
- PDE loss 从首个记录的 `0.0866140` 降至 `0.0389427`；final total loss=`0.0845594`。
- final/max-observed phase=`0.0295885`；phase activity=`0`；首次 `phase_max>=0.10` 和首次活动步均不存在。
- 全局 positive kinetic-growth fraction 在 step 300 为 `0.0908203`，但冻结的 W1/W3 ROI cold-growth 指标均为 `0`，因此不能据此宣布 readiness。

## 本地冻结评价

- hard guards：false；六项失败为两个周期各自的 `event_missing`、`roi_peak_below_minimum`、`recovery_failure`。
- cycle 1/2 event time 均为 null；peak ROI fraction 和 recovery fraction 均为 `0`。
- primary `time_averaged_phase_region_symmetric_difference=0.00515`；co-primary `phase_roi_continuous_rms=0.108234`。
- `potential_full_rms=0.0446618`；`temperature_roi_rms=0.351724`；`terminal_current_trace_nrmse=0.225301`；`pulse_energy_relative_error=0.539667`。
- `phase_high_k_relative_error=0.998395`。

## 工程启动事实与实例生命周期例外

本次有效 E2 之前的一次启动因 tmux 中的相对 `PYTHONPATH=.` 未指向隔离部署根而在 import 阶段终止；没有构造模型或执行 optimizer step。改用绝对部署根后，隔离 CLI import 回归通过，随后才从 scratch 启动唯一有效 E2。该零步工程启动不计 exploration，也不改变科学身份。

用户在本次运行中明确要求执行后保留实例开机，覆盖了本条运行的“立即关机”生命周期要求。E2 完成后核验：SSH 可达、V100 utilization=`0%`、memory used=`0 MiB`，没有 R1X 训练进程。实例保持运行是显式用户例外，不是 campaign 科学继续授权；未来默认仍为 GPU 使用结束后及时关机，除非用户再次明确覆盖。

## 证据边界

- `VERIFIED`：top hard lift 精确满足 top potential boundary；有效 E2 完成 300 warm-up updates；五次 readiness 均失败；无 material phase signal；产物哈希一致；本地 frozen evaluator 无两周期 competence；stress 未读。
- `SUPPORTED_INTERPRETATION`：soft top-Dirichlet conditioning 不是当前失败的充分解释。hard lift 增强了全局/局部电热量，但仍未建立同时覆盖 W1/W3 ROI 的相变方向 cold kinetic drive。
- `HYPOTHESIS`：当前 fixed-discretization pure-scratch 对象需要外部低保真状态/驱动引导，才能离开低相态兼容轨迹；本 campaign 没有检验该路线。
- `UNKNOWN`：low-fidelity-guided PINN、其他 seed、stress、formal OOD、PJGR 和 R2 的结果。

机器可读证据见 [compact artifact](artifacts/20260903T010712Z-phk-v23-r1x-e2-top-hard-lift-ce64086.json)，运行身份见 [manifest](manifests/20260903T010712Z-phk-v23-r1x-e2-top-hard-lift-ce64086.json)。raw 产物保存在 git-ignored `outputs/runs/20260903T010712Z-phk-v23-r1x-e2-top-hard-lift-ce64086/`，未上传 checkpoint、prediction carrier 或完整日志。
