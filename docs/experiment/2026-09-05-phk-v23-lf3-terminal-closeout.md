# PHK-V2.3 LF3 phase-latent carrier pilot 终局收口

- `phase_id`: `PHK_V23_LF3_MEASURE_DECOUPLED_STARTUP_SCALED_PHASE_LATENT_CARRIER_PILOT_EXECUTE`
- `lifecycle_state`: `COMPLETE`
- `machine_outcome`: `LF3_CARRIER_NOT_ESTABLISHED`
- `scientific_gpu_trajectories`: `1/1`
- `T0_updates`: `1200`
- `P0_updates`: `0_NOT_TRIGGERED`
- `candidate`: `none`
- `next_research_execution_authorized`: `false`
- `next_recommendation`: `STOP_LATENT_CARRIER_ROUTE_RETAIN_NEGATIVE_ADVISOR_DRAFT`
- `stress_reference_status`: `TWO_STRESS_REFERENCES_SEALED_UNREAD`

## 结论

`VERIFIED`：LF3-T0 的 measure-decoupled startup-scaled phase-logit 组合把
LF2 的冷态坍塌恢复成了合法、局域且时刻准确的双周期事件。T0 的 potential
maximum-principle、phase range、finite、phase maximum、事件存在、时间、
precision、active mass、locality 与 recovery 门均通过；只有两周期 hard recall
为 `0.805842/0.768603`，低于预冻结的 `0.90`。冻结全-medium gate 因而给出：

```text
LF3_CARRIER_NOT_ESTABLISHED
→ P0_NOT_TRIGGERED_BECAUSE_T0_GATE_FAILED
→ STOP_LATENT_CARRIER_ROUTE_RETAIN_NEGATIVE_ADVISOR_DRAFT
```

P0 没有运行，不能称为 P0 失败。T0 只含 medium data objective，不含 PDE 或
本构残差，不能称为 PINN 结果。candidate 为 none。

## 唯一 GPU 科学轨迹

| identity | device | seed/dtype | T0 | P0 | wall |
|---|---|---|---:|---:|---:|
| `LF3_MEASURE_DECOUPLED_PHASE_LATENT_CARRIER_PILOT` | Tesla V100-PCIE-32GB | 17 / FP64 | 1200 | 0 | 81.3416 s |

T0 从精确 LF1-B0 model weights 以 fresh Adam 启动，更新三个独立 field heads。
V/T 使用 target measure；phase 使用 14 个互斥类别等权的完整 logit-increment
MSE。1200 个 batch 与 LF2 stream 逐步同身份，rolling SHA-256 为
`6E9957E8...8F28`。T0 未构造或推进 physics sampler；云端未读取 fine、
extra-fine、`LF_ONLY`、frozen evaluator 或 stress。

## Full-medium carrier gate

| 项目 | cycle 1 | cycle 2 | 冻结门 | 结果 |
|---|---:|---:|---:|---|
| phase maximum | 0.991187 | — | ≥ 0.90 | PASS |
| event-time absolute error | 0.00485 | 0.00170 | ≤ 0.005 | PASS/PASS |
| hard recall | 0.805842 | 0.768603 | ≥ 0.90 | **FAIL/FAIL** |
| hard precision | 0.907157 | 0.866053 | ≥ 0.80 | PASS/PASS |
| active-mass ratio | 0.888316 | 0.887477 | [0.80, 1.20] | PASS/PASS |
| ROI peak fraction | 0.072314 | 0.067149 | ≥ 0.02 | PASS/PASS |
| outside-ROI peak | 0 | 0 | ≤ 0.10 | PASS/PASS |
| recovery | 1.0 | 1.0 | ≥ 0.70 | PASS/PASS |

所有值有限；phase 最小/最大为 `2.67e-9/0.991187`；potential maximum-
principle 的 maximum excess 与 violation fraction 均为 0。相对 LF1-B0，
potential、temperature、phase weighted-MSE ratio 为
`0.241890/0.0633841/0.0330773`。连续场误差显著下降不能覆盖 hard recall
失败。

## 论文相关的实质解释

`SUPPORTED_INTERPRETATION`：LF1-B0 以约 `5.27/5.86` 倍 active mass 获得
高 recall，但 precision 仅约 `0.171/0.161`；LF2 又把事件完全抹除。LF3 把
主导误差从 diffuse false-positive mass 收缩为 event-boundary missed support：
precision、质量、时刻和事件核心均恢复，但漏掉约 19.4%/23.1% 的 medium
teacher support。这是组合级 solver-recovery 证据，不是 phase-logit 单因素
归因。

`HYPOTHESIS`：剩余误差主要位于事件边界覆盖，而非冷态、全域过热或时序错位；
本合同没有授权延长训练、改 loss 或新增 matched arm 来检验该假设。

`UNKNOWN`：合格 carrier 能否建立；之后 label-free physics 是否形成
P0-vs-T0 Pareto；相对 direct `LF_ONLY` 是否存在任何预声明增量；多 seed、
formal OOD、stress、continuum 与实验有效性。

## 关机后的 nominal 评价与强基线

全部 summary-bound 产物回收并逐项通过远端/本地 size 与 SHA-256 对账后，
GPU 无 compute process，实例已执行关机并由 SSH `Connection refused` 验证。
只有随后本地 evaluator 才读取 nominal fine/extra-fine。canonical adjudication：

```text
outputs/runs/20260904T150300Z-phk-v23-lf3-local-adjudication-97a5b74-er1/adjudication.json
SHA256=BB45AB4FAFE0A0ADC8E4F21A35E96E3A05B233594933C04AC0F3C58401B23378
```

| role | evaluator event guard | phase ROI RMS | phase symmetric diff | T ROI RMS | current nRMSE |
|---|---|---:|---:|---:|---:|
| direct `LF_ONLY` | PASS | 0.00657038 | 0.000349531 | 0.00180069 | 0.00352214 |
| LF1-B0 | PASS | 0.163446 | 0.0174370 | 0.0545925 | 0.256194 |
| LF1-final | PASS | 0.214459 | 0.0205948 | 0.0793024 | 0.138757 |
| LF2-M0 | FAIL (6) | 0.110564 | 0.0051500 | 0.0175980 | 0.146374 |
| LF3-T0 | PASS | 0.0390008 | 0.00202578 | 0.0173618 | 0.137297 |

extra-fine evaluator 的 event-existence/locality/recovery guard 与 LF3
teacher-relative `recall≥0.90` carrier gate 回答不同问题；前者通过不覆盖后者
失败。direct `LF_ONLY` 仍在所有主误差上显著更强，因此不存在 paper-positive
accuracy 或 candidate signal。

初次本地报告把实际 LF3-T0 checkpoint 的 fixed-pool 键沿用了 LF2 role 名。
评价代码只做报告身份修复并生成 `-er1`：pool、checkpoint、physics value
`6.571589165588435`、reference metrics 与机器结局均未改变。旧报告保留在
git-ignored run storage，不作为 canonical terminal record。

## 运行完整性与 launcher 记录缺陷

run summary 绑定的 7 个文件全部通过对账；training/audit/T0 batch ledger
分别为 7/7/1200 行，P0 ledger 为 0 行。远端/本地 run summary SHA-256 均为
`335DBF21...5D12`。launcher 的 exit capture 因 shell 转义写入了字面 `$?`
加换行，原始 3 bytes 与 SHA-256 `097D68F4...DD96` 已原样保留。它是运行结束
后的 wrapper logging defect；terminal summary、固定 1200 updates、checkpoint、
prediction、audit 和全部 artifact hash 已独立证明科学轨迹完成，不授权也未执行
第二条科学轨迹。

## 论文初稿交付

[paper_v23](../../paper/paper_v23/README.md) 已形成英文导师初稿、五张 PNG/PDF
主图、表格、claim-evidence matrix、复现说明、审稿风险自检和中文研究判断。
稿件定位为 failure-analysis + bounded solver-recovery，不声称原创 latent 单件、
合格 carrier、PINN-specific gain、强基线优越性或投稿就绪。

218 项相关研究链回归与 15 项 LF3 focused 测试全部通过；严格 JSON、experiment
ledger 与 document consistency 均有效。机器证据见
[compact artifact](artifacts/20260904T160901Z-phk-v23-lf3-terminal-97a5b74.json)，
运行身份见[同名 manifest](manifests/20260904T160901Z-phk-v23-lf3-terminal-97a5b74.json)。

本 campaign 完成后 `next_research_execution_authorized=false`。不自动运行
第二臂、新 seed、matched ablation、OOD、stress、PJGR/R2、kinetic teacher
或投稿；两份 stress references 始终 `TWO_STRESS_REFERENCES_SEALED_UNREAD`。
