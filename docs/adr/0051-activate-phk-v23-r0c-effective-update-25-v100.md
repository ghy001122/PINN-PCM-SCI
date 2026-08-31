# ADR 0051：激活 PHK-V2.3 R0C 25-step 有效更新诊断

- `status`: `ACCEPTED_COMPLETE`
- `date`: `2026-08-31`
- `phase_id`: `PHK_V23_R0C_EFFECTIVE_UPDATE_25_V100`
- `supersedes`: `ADR_0050_FUTURE_RESEARCH_AUTHORIZATION_ONLY`
- `preserves`: `ADR_0050_R0B_PRECURSOR_RESULT_R0A_INCONCLUSIVE_AND_PHK_V22R_TERMINAL_NO_GO`
- `decision_source`: 用户明确发送 `EXECUTE PHK_V23_R0C_EFFECTIVE_UPDATE_25_V100`

## 决定

只执行一次 reference-blind、seed-17、FP64、`STRONG_RAW` scratch replay。科学 schedule denominator 保持 `1000`，实际只执行 `25` 个 canonical Adam updates。R0C 同步记录 V/T/phase 三个独立 head 的 canonical pre-clip/post-clip gradient norm、实际单步参数位移与只读 Adam state 摘要，以判断 R0B 的 raw-gradient starvation 是否在 optimizer-effective update 上仍然具有物质性。

R0C 不恢复 competence、不实现 recovery/PJGR、不修改 physics/loss/sampler/optimizer，不选择 checkpoint，不读取 nominal/stress reference，不产生方法增益或因果 root claim。结果只能是 `R0C_EFFECTIVE_UPDATE_STARVATION_SUPPORTED`、`R0C_ADAM_PRECONDITIONING_COMPENSATES_RAW_GRADIENT` 或 `R0C_INCONCLUSIVE_STOP`；身份或执行完整性失败单列为 `R0C_INVALID_EXECUTION`。

实现只扩展现有 `TrainingObserver` seam；不得建立平行 trainer/evaluator。observer 不取得 live optimizer/sampler，不调用 `backward`、`zero_grad` 或 optimizer step，也不得改变参数、buffer、RNG、mode 或既有 `.grad`。

## 预算与停止

- GPU 仅允许 `Tesla V100-PCIE-32GB`，FP64，seed 17，唯一 25-step run。
- GPU wall hard cap `0.5 h`，paid-work soft stop `20 min`，增量估算费用 hard cap `2 CNY`。
- V2.3 总上限继续为 `34 GPU-h / 95 CNY / 14 days`，项目绝对云成本上限继续为 `150 CNY`。
- 身份/GPU/合同漂移、reference 可达、重复进程、非有限值、非 25 updates、轨迹身份门失败或产物不完整均立即停止，且不得自动重跑。
- 受控产物回收与 SHA-256 核验完成后必须立即关闭 AutoDL 实例并验证关机状态。

完成 R0C 不自动授权 R1、PJGR、stress、第二次 run、作者联系或投稿。

## 执行结果

一次性授权已由 run `20260831T072029Z-phk-v23-r0c-effective-update-25-ec84907d` 消费。25/25 canonical updates、25 条 reference-blind telemetry、R0B 轨迹身份、产物回收、SHA-256 核验和 AutoDL shutdown 均已完成。

机器结果为 `R0C_ADAM_PRECONDITIONING_COMPENSATES_RAW_GRADIENT`：steps 10–19 的 phase raw-gradient ratio 保持很小，但 Adam-effective relative-update ratio 约为 `0.59`，故下一建议固定为 `REJECT_GRADIENT_MAGNITUDE_RESCUE_AS_FIRST_R1A`。结果不恢复 competence、不证明因果 root 或方法增益，不产生后续执行授权。详见 [R0C closeout](../experiment/2026-08-31-phk-v23-r0c-effective-update-25-closeout.md)。
