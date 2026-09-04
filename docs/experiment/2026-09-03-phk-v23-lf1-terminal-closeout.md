# PHK-V2.3 LF1 event-preserving multi-fidelity pilot 收口

- `phase_id`: `PHK_V23_LF1_EVENT_PRESERVING_MULTIFIDELITY_PILOT`
- `lifecycle_state`: `COMPLETE`
- `machine_outcome`: `LF1_DATA_ONLY_VALUE_NO_PINN_GAIN`
- `scientific_gpu_runs`: `2/3`
- `run_c_executed`: `false`
- `candidate`: `none`
- `next_research_execution_authorized`: `false`
- `next_recommendation`: `RETAIN_DATA_ONLY_VALUE_AS_NON_PINN_BASELINE_STOP_METHOD_CLAIM`
- `stress_reference_status`: `TWO_STRESS_REFERENCES_SEALED_UNREAD`

## 结论

`VERIFIED`：LF1 修复了 LF0 的两个直接失败点。范围保持的 exact-top potential 表示使 A、B0 与 B final 都通过 maximum-principle validity；event-balanced medium distillation 使固定 B0 获得两周期 competence；固定 `0.1` persistent replay 使 B final 在 1200 步完整 physics refinement 后仍保留两周期 competence，没有再次塌回冷态。

但是 B final 没有通过冻结的增量门。固定 reference-blind full-physics objective 从 B0 的 `7.37464` 降到 `0.421175`，比例 `0.0571112 <= 0.5`；与此同时，相对 B0 和 direct `LF_ONLY` 的 phase noninferiority 与 temperature preservation 都失败。机器树因此给出终局：

```text
LF1_DATA_ONLY_VALUE_NO_PINN_GAIN
→ C_NOT_RUN
→ RETAIN_DATA_ONLY_VALUE_AS_NON_PINN_BASELINE_STOP_METHOD_CLAIM
```

这不是“LF1 无法转移事件”，也不是“B final 没有 competence”。准确结论是：data-only event transfer 与 replay 防遗忘均有效，但当前 physics refinement 的 accuracy–residual trade-off 不足以建立 PINN-specific method gain。

## GPU 轨迹与预算

| Run | 冻结身份 | updates | wall | GPU h | 估算费用 | 终态 |
|---|---|---:|---:|---:|---:|---|
| A | range-preserving scratch pure physics | 1200 physics | 722.434 s | 0.200676 | 0.377271 CNY | valid，冷态无事件 |
| B | event-aware data-only + persistent-replay physics | 1200 data + 1200 physics | 783.453 s | 0.217626 | 0.409137 CNY | B0 与 final 均 competent |
| C | exact B0 data-only continuation control | 0 | 0 | 0 | 0 | provisional 门失败，未触发 |

合计 3600 optimizer steps、`0.418302 GPU h`、`0.786408 CNY`。两条运行均使用 Tesla V100-PCIE-32GB、FP64、seed 17 与同一 source identity；A/B 的 1200 个 physics-local batches 逐步完全一致。云端仅 medium 是训练标签源，未读取 fine、extra-fine、frozen evaluator 或 stress。

## B0 transfer gate

B0 恰好完成 1200 个 event-aware medium-only updates 后通过全部预冻结门：

- gate grid `phase_max=0.754197`；
- 两周期 teacher-event support 中预测 active 点为 `1046/1164` 与 `1041/1102`；
- 六个 event/transition/recovery pools 均非空；
- potential maximum-principle 在 W1–W4 与全域均为 0 excess；
- full nominal carrier 上 `phase_max=0.764470`，`phase>=0.5` fraction=`0.0188881`，两周期事件时间为 `0.193394/1.442144`，全部 frozen competence guards 通过。

因此 LF0 中“普通全局 field MSE 未转移稀疏事件”的阻塞，在本冻结的 event-balanced data-only 阶段已经被实证解除。

## B final 与冻结比较

B1 恰好完成 1200 个 `full physics + 0.1 persistent replay` updates。B final 仍通过 potential validity 与全部两周期 competence guards：`phase_max=0.664466`，`phase>=0.5` fraction=`0.0215782`，事件时间为 `0.209693/1.431489`。

| Role | competent | phase primary | phase ROI RMS | temperature ROI RMS | current NRMSE |
|---|---|---:|---:|---:|---:|
| direct `LF_ONLY` | true | 0.000349531 | 0.00657038 | 0.00180069 | 0.00352214 |
| B0 `LF_DATA_ONLY` | true | 0.0174370 | 0.163446 | 0.0545925 | 0.256194 |
| B final | true | 0.0205948 | 0.214459 | 0.0793024 | 0.138757 |

相对 B0，B final 的 primary/co-primary/geometric ratios 为 `1.18109/1.31211/1.24488`；相对 direct `LF_ONLY` 为 `58.9211/32.6403/43.8543`。两组 phase noninferiority 均失败。temperature preservation 对两组 comparator 均失败；current preservation 均通过。固定 physics ratio 的通过不能覆盖这些预冻结精度与 preservation 失败。

`SUPPORTED_INTERPRETATION`：persistent replay 确实阻止了 LF0 式冷态坍塌，但当前固定权重和联合目标保留的是偏早、偏宽的 active support；physics closure 降低 residual 的同时进一步恶化了 phase 与 temperature 误差。现有证据不支持把该折衷写成方法增益。

## 条件 C、回收与实例生命周期

Run C 只用于 B 已通过 provisional gate 后排除“只是更多 data-only updates”的解释。B 未通过该门，故 C 不可达；不得写成 C 失败或把未使用的第三条额度转作救援运行。

Run B 共回收 12 个文件；summary 绑定的 11 个产物均完成远端/本地 size 与 SHA-256 对账。event-data、physics 与 training ledgers 分别为 2400、1200 与 98 行。完整回收后实例执行关机，随后 SSH 返回 `Connection refused`。本地 nominal evaluation 只在该关机验证后读取 fine/extra-fine；stress 始终 sealed/unread。

## 验证

LF1 focused、cloud、evaluation、experiment ledger 与 document-consistency 共 40 个 `unittest` 全部通过；实际仓库门禁返回 `DOCUMENT_CONSISTENCY_VALID`。终局 artifact 与 manifest 均通过严格 JSON 解析。项目虚拟环境未安装 `pytest`，因此未增加依赖，改用仓库现有 `unittest` 入口；这不影响测试覆盖或科学裁决。

## 证据边界

- `VERIFIED`：event-balanced B0 转移了两周期 competence；B final 保留 competence并显著降低固定 physics objective；全部 potential guards 通过；冻结 phase/temperature 增量门失败；C 未运行；实例已关机；stress 未读。
- `SUPPORTED_INTERPRETATION`：主要剩余矛盾已从“事件能否被转移/保留”转为“physics residual 改善能否在强 data-only baseline 的误差容限内实现”。
- `HYPOTHESIS`：未来若另行授权，需要直接约束 accuracy–physics Pareto 或改变可写 claim，而不是延长同一 B、调 seed、换 optimizer 或补跑 C。
- `UNKNOWN`：新的有界方法能否相对 direct `LF_ONLY` 建立 noninferior PINN-specific value；multi-seed、stress、formal OOD 与 headline core 增量。

本 campaign 已终止，不自动授权 phase-latent teacher、PJGR、R2、多 seed、stress 或任何新科学运行。机器证据见 [compact artifact](artifacts/20260903T155306Z-phk-v23-lf1-terminal-dc091be.json)；最终运行身份见同名 manifest。checkpoint、prediction 与完整日志保留在 git-ignored `outputs/runs/`。
