# PHK-V2.3 R0C 25-step 有效更新物质性诊断收口

- `date`: `2026-08-31`
- `run_id`: `20260831T072029Z-phk-v23-r0c-effective-update-25-ec84907d`
- `task_id`: `PHK_V23_R0C_EFFECTIVE_UPDATE_25_V100`
- `execution_status`: `COMPLETED`
- `diagnostic_outcome`: `R0C_ADAM_PRECONDITIONING_COMPENSATES_RAW_GRADIENT`
- `causal_root_cause_identified`: `false`
- `competence_recovered`: `false`
- `method_gain_proven`: `false`
- `claim_status`: `V22R_TERMINAL_NO_GO_PRESERVED_R0C_ADAM_PRECONDITIONING_COMPENSATES_RAW_GRADIENT_NO_METHOD_EVIDENCE`
- `next_research_execution_authorized`: `false`
- `stress_reference_status`: `TWO_STRESS_REFERENCES_SEALED_UNREAD`

## 总裁决

`VERIFIED`：唯一一次 V100/FP64/seed-17 `STRONG_RAW` scratch replay 完成了 `25/25` 个 canonical Adam updates，科学 schedule denominator 保持 `1000`，只覆盖 W1，云端 shadow optimizer steps 为 `0`。reference-blind machine adjudication 固定为：

```text
status = R0C_ADAM_PRECONDITIONING_COMPENSATES_RAW_GRADIENT
qualifying_block = steps 10..19
next_recommendation = REJECT_GRADIENT_MAGNITUDE_RESCUE_AS_FIRST_R1A
causal_root_cause_identified = false
competence_recovered = false
method_gain_proven = false
next_stage_authorized = false
```

R0B 所见的 phase-head raw-gradient starvation 在 canonical Adam effective update 上没有保持同等量级的 starvation。冻结区间内 raw-gradient ratio 约为 `0.01086 → 0.00619`，而实际相对参数更新 ratio 约为 `0.5913 → 0.5951`；因此 Adam 的预条件与逐参数缩放对 raw-gradient 差异形成了物质补偿。该证据否决“只放大 phase gradient magnitude”作为首个 R1a 的充分依据，但不证明 Adam 已恢复 phase 动力学，也不排除梯度方向冲突、电热驱动不足或其他训练刚性。

## 执行身份与完整性

`VERIFIED`：

- 部署包身份：`R0C-BUNDLE-EC84907DCAF8F2B57AE4BB58F46500835DACC92C2EEB3FC52377BFAC204F9F9F`；基线 commit 为 `a935549808c879989c040e264a04a2456a057589`。
- 三份 R0C 合同 SHA-256 分别为 `95C9D569...223`、`F039C860...B8D`、`C1EE01DA...3AE`；远端 14 个绑定文件逐项匹配部署清单。
- 设备：`Tesla V100-PCIE-32GB`；dtype：FP64；seed：17；初始化：scratch；arm：`STRONG_RAW`。
- run wall time：`44.598549 s`；GPU time：`0.0123885 h`；按 `1.88 CNY/h` 估算增量费用 `0.0232904 CNY`。累计项目展示单价估算约为 `4.930619 CNY`；二者均不是平台账单。
- checkpoint `update=25`，内嵌 `training_config.updates=1000`；final manifest 为 `DIAGNOSTIC_PREFIX`，没有冒充完整 nominal 训练。
- 25 条 telemetry 恰好覆盖 steps 1–25；R0B 轨迹锚点在冻结容差内全部通过。
- observer 每次 callback 均保持参数 version、既有 `.grad`、model mode，以及 Python/NumPy/Torch CPU/CUDA RNG；训练 sampler 未被诊断 pool 推进。
- checkpoint、log、start/final manifest、telemetry、telemetry summary、environment 和 summary 全部回收；7 项 summary-bound artifacts 的本地 SHA-256 与大小一致，远端/本地 summary SHA-256 同为 `05C1D371...59E0`。
- 云端与本地裁决均未读取 nominal reference；两份 stress references 未读取。R0C 没有 prediction carrier、reference evaluation 或 teacher probe。

## AutoDL 关机

`VERIFIED_INFRASTRUCTURE_ONLY`：产物回收和远端/本地哈希核验完成后，首次尝试的 `/sbin/shutdown` 在该镜像中不存在，因此没有发生状态变化。随即只读定位到实际入口 `/usr/bin/shutdown` 并执行 `/usr/bin/shutdown -h now`；关机后 SSH 探针返回 `Connection refused`。实例已关闭，不再产生本阶段 GPU 费用。

## Reference-blind 有效更新证据

### VERIFIED

- 冻结 raw-gradient starvation 门为 phase/head ratio `<= 0.1`；Adam-effective update compensation 门为相对参数更新 ratio `>= 0.5`，并要求 steps 10–25 内至少 10 个连续 steps。
- step 10：raw-gradient ratio `0.0108636`，effective-update ratio `0.591302`，Adam compensation factor `54.4297`；phase 相对更新 `0.00429165`，最大其他 head 相对更新 `0.00725797`。
- step 19：raw-gradient ratio `0.00619411`，effective-update ratio `0.595078`，Adam compensation factor `96.0716`。steps 10–19 构成首个完整冻结连续区间。
- step 25：raw-gradient ratio `0.00434522`，effective-update ratio `0.563137`，Adam compensation factor `129.599`；phase 相对更新 `0.00495693`，最大其他 head 相对更新 `0.00880235`。
- canonical pre-clip 与 post-clip 三 head gradient norms 在所列 steps 相同，且全局 norm 低于 clip 阈值；该结果不是 clipping 伪造的补偿。
- electrothermal confound 未在 steps 10–25 触发：W1 最大温度从 step 10 的 `0.725556` 到 step 25 的 `0.647039`，对应 ROI positive-growth fraction 从 `0.160256` 到 `0.108974`，均未同时达到冻结低驱动门。
- output-conditioning confound 未触发：step 10 的 phase Jacobian q95 为 `0.0748920`，低 Jacobian fraction 为 `0.0683594`；虽然两项局部 capacity 都很小，但完整联合门未满足。
- step 25 的 W1 phase 最大值仍只有 `0.0243292`，final training loss 为 `0.293006`。R0C 不运行 competence evaluator，损失下降与有效更新存在均不能充当事件 competence。

### SUPPORTED_INTERPRETATION

- R0B 的“phase raw gradient 比其他 heads 小两个数量级”是真实可复现的前兆，但 Adam 的有效参数位移只落后约 `40%–44%`，不是同量级的 update starvation。因此，单纯提高 phase loss 权重或梯度幅值很可能重复补偿 optimizer 已经部分完成的工作，且可能加剧已观察到的方向冲突。
- 后续若另立 R1 规划，首要问题应从“phase 是否完全没更新”改为“这些物质更新是否方向错误、被冲突抵消，或在电热驱动下降时推动了错误的冷态吸引子”。这只是下一步设计依据，不是新执行授权。

### UNKNOWN

- Adam 补偿后的 phase 更新方向是否与目标事件动力学一致，以及梯度冲突是否是更接近干预层的机制。
- 电热驱动下降与 phase 更新方向之间的因果顺序和可分离性。
- 任一单一 recovery intervention 能否恢复两周期 event competence。
- PJGR、其他 seed、更长预算、stress、formal OOD 或正向方法增益的结果。

## 产物与下一步边界

- [compact machine artifact](artifacts/20260831T072029Z-phk-v23-r0c-effective-update-25-ec84907d.json)
- [experiment manifest](manifests/20260831T072029Z-phk-v23-r0c-effective-update-25-ec84907d.json)
- raw run：`outputs/runs/20260831T072029Z-phk-v23-r0c-effective-update-25-ec84907d/`（git-ignored）

本阶段在 `R0C_ADAM_PRECONDITIONING_COMPENSATES_RAW_GRADIENT` 收口。下一研究执行未授权；不得自动运行 R1、PJGR、第二次 R0C、stress、其他 seed、预算延长、作者联系或投稿。可允许后续只读审查，或另立一个不把 gradient magnitude rescue 作为默认首轴的 `PLAN_ONLY` 研究合同。

本记录不 supersede PHK-V2.2R terminal closeout、R0A/R0B closeout、bounded-negative advisor draft 或 stress seals。
