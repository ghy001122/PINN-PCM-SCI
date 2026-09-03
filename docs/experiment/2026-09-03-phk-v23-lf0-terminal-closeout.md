# PHK-V2.3 LF0 exact-top warm-start attribution campaign 收口

- `phase_id`: `PHK_V23_LF0_EXACT_TOP_WARMSTART_ATTRIBUTION_EXECUTE`
- `lifecycle_state`: `COMPLETE`
- `machine_outcome`: `LF0_NUMERICAL_OR_IDENTITY_INVALID`
- `scientific_gpu_runs`: `2/3`
- `run_c_executed`: `false`
- `candidate`: `none`
- `next_research_execution_authorized`: `false`
- `next_recommendation`: `INVALID_RUN_REQUIRES_USER_REVIEW_NO_AUTOMATIC_SCIENTIFIC_RETRY`
- `stress_reference_status`: `TWO_STRESS_REFERENCES_SEALED_UNREAD`

## 结论

`VERIFIED`：Run A 与 Run B 均在 `Tesla V100-PCIE-32GB`、FP64、seed 17、`STRONG_RAW`、scratch、exact-top raw potential transform 下完成。A 的 1200-step pure-physics scratch PINN 没有两周期 competence。B 完成 800-step medium data-only warm-start、200-step cosine anchor 与 1000-step pure-physics closure，但固定的 step-800 `LF_DATA_ONLY` checkpoint 在 W1/W3 违反 potential maximum-principle validity guard，因此按冻结优先级得到终局：

```text
LF0_NUMERICAL_OR_IDENTITY_INVALID
→ C_NOT_RUN
→ INVALID_RUN_REQUIRES_USER_REVIEW_NO_AUTOMATIC_SCIENTIFIC_RETRY
```

这不是部署故障，也不允许自动重试 B。C 的用途是 B 通过有效性与 provisional 增量门后的 compute control；B 已在更高优先级 validity gate 失败，所以 C 不可达。

## GPU 轨迹

| Run | 训练身份 | updates | wall | GPU h | 估算费用 | 终态 |
|---|---|---:|---:|---:|---:|---|
| A | exact-top scratch、pure physics | 1200 | 685.832 s | 0.190509 | 0.358157 CNY | valid, no competence |
| B | 800 LF-only + 200 anchor + 1000 physics | 2000 | 732.704 s | 0.203529 | 0.382634 CNY | `LF_DATA_ONLY` potential invalid |
| C | conditional exact-top scratch compute control | 0 | 0 | 0 | 0 | not triggered |

合计 3200 optimizer steps、`0.394038 GPU h`、`0.740791 CNY`。费用只作报告，不是停止门。A/B 前 1200 个 physics-local batches 逐步相同，rolling SHA 均为 `536E6706A0B68EBB1277A97F402D273AFA2EA1E0B27106F26CB4222B7EC05C53`；B0 optimizer 在 B1 前销毁，B1/B2 使用同一个新 Adam 且不重置。

两条运行使用 cloud source commit `9b98320f4082dbfcc77ddeb74c32bf0d2b998b2b` 与 source identity `LF0-BUNDLE-0D41A552D8CCB789D508387E6FEAB4F5D7D7F41C4D8705764FB1E0330057B7E7`。云端只读取声明的 medium carrier；未读取 fine、extra-fine、evaluator 或 stress。

## 冻结有效性门

A final、B final 与 direct `LF_ONLY` 均通过 potential maximum principle。B 的固定 `LF_DATA_ONLY` checkpoint 未通过：

| Scope | max absolute excess | violation fraction |
|---|---:|---:|
| W1 | 0.0256042 | 0.00337333 |
| W3 | 0.0300911 | 0.00426917 |
| global | 0.0300911 | 0.00107315 |

W2/W4 无 violation。该门在合同中同时约束 `LF_DATA_ONLY`；因此即使 B final 后来恢复合法 potential，也不能把 B0 当作有效 warm-start comparator，亦不能进入方法增量或 C-trigger 裁决。

固定 reference-blind CPU physics pool仍给出 B final / B0 full summed objective ratio `0.0143558 <= 0.8`，说明物理闭合显著降低了固定池目标；它不能覆盖 B0 的数学有效性失败。

## 本地 nominal development 结果

本地 frozen evaluator 在全部云端产物回收后执行。用户本次明确要求保留实例在线，因此 reference role 如实记录为 `NOMINAL_LOCAL_DEVELOPMENT_ONLY_AFTER_RECOVERY_INSTANCE_RETAINED_BY_EXPLICIT_USER_OVERRIDE`，没有虚报关机。

| Role | competent | phase max | phase>=0.5 | Tmax | phase primary | phase ROI RMS |
|---|---|---:|---:|---:|---:|---:|
| A final | false | 0.0299932 | 0 | 0.140069 | 0.00515 | 0.110479 |
| B0 `LF_DATA_ONLY` | false | 0.477584 | 0 | 0.609780 | 0.00515 | 0.0924313 |
| B final | false | 0.0299932 | 0 | 0.421203 | 0.00515 | 0.110386 |
| direct `LF_ONLY` medium | true | 0.991515 | 0.00530423 | 0.926046 | 0.000349531 | 0.00657038 |

A、B0 与 B final 都缺失两个周期事件，并各有 event missing、ROI peak、recovery 六项失败。direct `LF_ONLY` 的 cycle-1/2 event times 为 `0.2381/1.49545`，两周期 guards 全部通过。

`SUPPORTED_INTERPRETATION`：低保真 carrier 本身包含可用两周期事件，但当前 800-step data-only network 没有忠实转移该轨迹；它只把 phase 拉到接近阈值，同时产生 potential inadmissibility。随后的 1200-step physics closure 修复了 potential validity，却没有保留或恢复 phase event，最终 phase 回到低相态。

不能据此声称低保真 guidance 普遍无效，也不能把 B 的较低 final loss 写成 solver competence。当前只证明这一个冻结的 `data-only warm-start + annealed anchor + physics closure` 实现没有形成有效方法证据。

## 两次零步工程启动

正式 A 前有两次相同的 isolated deployment import failure：source bundle 漏列 `pinn_pcm_sci/artifacts.py`，均在模型、CUDA 与 optimizer 构造前终止，optimizer steps=0，不消耗科学 run。根因定位后由 commit `9b98320f4082dbfcc77ddeb74c32bf0d2b998b2b` 补齐 runtime closure，并以 isolated LF0 CLI import 回归证明修复；随后 A/B 使用同一修复后 source identity。

## 实例生命周期

用户明确覆盖本次默认关机规则，要求执行后保留实例。终局核验时 V100 memory used=`0 MiB`、utilization=`0%`，无 LF0 training process；本次未执行 shutdown。该例外不授权 C 或任何新研究。今后仍默认 GPU 使用结束后及时关机，除非用户再次明确覆盖。

## 证据边界与下一步

- `VERIFIED`：A 无 competence；direct LF_ONLY 有两周期 competence；B0 potential guard 失败；B final potential 合法但仍无事件；C 未运行；stress sealed/unread。
- `SUPPORTED_INTERPRETATION`：失败的首要位置已经从“是否存在低保真事件”收缩到“网络能否在保持场可容许性的同时转移事件拓扑，并在 physics closure 中保留它”。
- `HYPOTHESIS`：下一路线若继续，应把 event-preserving/admissibility-preserving transfer 作为先决门，而不是直接重复延长 B0、提高 data weight 或运行 C。
- `UNKNOWN`：一种有效的事件保持 warm-start 能否恢复 PINN competence；多 seed、stress、formal OOD 与 headline core 增量。

按冻结合同，本 campaign 不自动授权任何科学重试。唯一下一建议是 `INVALID_RUN_REQUIRES_USER_REVIEW_NO_AUTOMATIC_SCIENTIFIC_RETRY`。

机器证据见 [compact artifact](artifacts/20260903T092416Z-phk-v23-lf0-terminal-172ae2c.json)；最终运行身份见同名 [manifest](manifests/20260903T092416Z-phk-v23-lf0-terminal-172ae2c.json)。checkpoint、prediction 与完整日志保留在 git-ignored `outputs/runs/`，不上传 GitHub。
