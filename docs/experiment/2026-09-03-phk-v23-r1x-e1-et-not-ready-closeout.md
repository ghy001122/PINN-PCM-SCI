# PHK-V2.3 R1X E1 clean-coupling exploration 收口

- `date`: `2026-09-03`
- `run_id`: `20260902T163530Z-phk-v23-r1x-e1-e32e188`
- `task_id`: `PHK_V23_R1X_BOUNDED_CLEAN_COUPLING_CAMPAIGN_EXECUTE`
- `trajectory`: `PHK_V23_R1X_E1_CLEAN_COUPLING_EXPLORATION`
- `evidence_role`: `NON_VOTING_DEVELOPMENT_EXPLORATION`
- `execution_status`: `COMPLETED_EARLY_POLICY_STOP`
- `machine_outcome`: `E1_ET_NOT_READY`
- `competence_recovered`: `false`
- `method_gain_proven`: `false`
- `next_machine_action`: `RUN_E2_TOP_DIRICHLET_HARD_LIFT`
- `campaign_state`: `AWAITING_AUTODL_RESTART_CAMPAIGN_AUTHORIZATION_REMAINS_ACTIVE`
- `stress_reference_status`: `TWO_STRESS_REFERENCES_SEALED_UNREAD`

## 裁决

`VERIFIED`：修复后的内容寻址 bundle 首次形成了有效 E1 科学轨迹。V100/FP64/seed-17 `STRONG_RAW` 从 scratch 完成 300 个 electrothermal warm-up updates；冻结 readiness gate 在 steps 200、225、250、275、300 全部失败，因此状态机按合同停止为 `ET_NOT_READY`，没有强行进入 phase ramp 或 full-physics joint closure。

关机后的本地冻结 nominal evaluator 同样判定 competence 失败：`phase_max=0.0295885`，`phase>=0.5` activity 为 0，两个周期均分别失败 event、ROI peak 与 recovery 三项。该轨迹是 non-voting development exploration，不构成方法增益或 candidate。

冻结机器树的唯一后续动作是：

```text
E1_ET_NOT_READY
→ E2_TOP_DIRICHLET_HARD_LIFT
→ 等待用户重新启动 AutoDL；campaign 授权保持有效
```

不得重跑 E1、选择其他 E2 分支、跳到 E3/confirmation，或执行 PJGR、R2、low-fidelity、stress 或其他 seed。

## 运行身份与完整性

- 执行 source commit：`e32e18890d9d5b5013f10e9260aba2201e91707b`；部署身份：`R1X-BUNDLE-0050A6EB7B436828081E4DC5888B702B804D11F915231F9492FC9CF9F413A820`。
- 设备：`Tesla V100-PCIE-32GB`；dtype：FP64；seed：17；arm：`STRONG_RAW`；初始化：scratch。
- 同一 Adam、标准 ConFIG stage groups、纯 Sobol、512/128/128 点数、accelerated windows 与 `alpha=0` cold-state coupling warm-up 均按冻结合同执行。
- optimizer updates 为 `300/1800`；这是 readiness policy 的正式早停，不是人工 early stopping。phase head 在 warm-up 中保持冻结；ramp updates=0，full-physics joint updates=0。
- 含 prediction wall time 为 `172.282172 s`（`0.0478562 GPU h`）；按运行时记录单价 `1.88 CNY/h` 估算费用 `0.0899696 CNY`。费用仅为报告字段。
- 远端 zero-update preflight 通过：V100、CUDA、physics materialization、source identity 和云端无 reference-like files 均满足要求。
- checkpoint、training log、telemetry、prediction、start/final manifests、environment、summary 和 console log 全部回收；远端/本地大小及 SHA-256 一致。
- 回收核验后立即执行 `/usr/bin/shutdown -h now`；关机探针返回 `Connection refused`。只有此后才读取本地 nominal reference。
- 云端 `reference_fields_read=false`、`stress_fields_or_metrics_read=false`；两份 stress reference 始终未读取。

## Readiness 结果

| step | ready | ROI T activation W1/W3 | cold growth W1/W3 | ROI QJ q95 W1/W3 | global Tmax |
|---:|---|---|---|---|---:|
| 200 | false | 0 / 0.224359 | 0 / 0 | 0.0186962 / 0.0169263 | 0.661488 |
| 225 | false | 0 / 0 | 0 / 0 | 0.0270968 / 0.0257560 | 0.593251 |
| 250 | false | 0 / 0 | 0 / 0 | 0.0364833 / 0.0356821 | 0.536654 |
| 275 | false | 0 / 0 | 0 / 0 | 0.0505086 / 0.0475462 | 0.488795 |
| 300 | false | 0 / 0 | 0 / 0 | 0.0593626 / 0.0546794 | 0.461357 |

QJ 的非零性门持续通过，但 W1 的 ROI thermal activation 始终为 0，W1/W3 的 cold kinetic-growth fraction 始终为 0；因而从未出现连续两个完整 readiness PASS。全局 `Tmax` 超过 `Tc=0.45` 不能替代冻结的 W1/W3 ROI readiness 条件。

## 本地冻结评价

- hard guards：false；六项失败为两个周期各自的 `event_missing`、`roi_peak_below_minimum`、`recovery_failure`。
- cycle 1/2 event time 均为 null；peak ROI fraction 和 recovery fraction 均为 0。
- primary `time_averaged_phase_region_symmetric_difference=0.00515`；co-primary `phase_roi_continuous_rms=0.108234`。
- `potential_full_rms=0.0597910`，`temperature_roi_rms=0.253221`，`terminal_current_trace_nrmse=0.574756`，`pulse_energy_relative_error=0.860744`。
- PDE loss 从 `0.117634` 降到 `0.0231320`，但这没有建立相变事件 competence。

## 本地收口工程修复

首次写 adjudication 时，冻结 evaluator 用正无穷表示缺失事件距离和空界面 Hausdorff 距离，而 strict JSON writer 禁止非有限 JSON 数值，导致在 exclusive 文件写入过程中终止并留下 partial file。根因已精确定位；partial file 被安全删除后，writer 改为“先严格序列化、后 exclusive open”，并把预期无穷 sentinel 显式编码为 `POSITIVE_INFINITY`，NaN 仍 fail-closed。定向回归通过，随后只重跑相同 adjudication；GPU 轨迹、prediction 和 frozen evaluation 均未改变。

## 证据边界

- `VERIFIED`: E1 是第一条有效 R1X 科学轨迹；300 个 warm-up updates 有限完成；readiness 五次均失败；产物哈希一致；AutoDL 已关机；本地 evaluator 和机器裁决为 `E1_ET_NOT_READY`。
- `SUPPORTED_INTERPRETATION`: 原 potential transform 的软 top Dirichlet conditioning 没有在 warm-up 内建立同时覆盖 W1/W3 ROI 的有效热激活与 cold kinetic drive；冻结机器树因此选择 top hard lift。
- `HYPOTHESIS`: top hard lift 精确施加电势上边界后可能提高并稳定 ROI Joule/thermal drive，使 E2 通过 readiness；尚未执行。
- `UNKNOWN`: E2 readiness、phase ramp、完整 joint closure、competence、E3/confirmation、其他 seed 与全部 stress 结果。

机器可读证据见 [compact artifact](artifacts/20260902T163530Z-phk-v23-r1x-e1-e32e188.json)；raw 产物保存在 git-ignored `outputs/runs/20260902T163530Z-phk-v23-r1x-e1-e32e188/`。历史工程阻塞记录保持在 [R1X engineering-blocked closeout](2026-09-02-phk-v23-r1x-engineering-blocked-closeout.md)，不得改写成 E1 科学失败。
