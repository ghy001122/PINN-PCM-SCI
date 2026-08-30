# PHK-V2.3 R0A 本地 CPU 只读诊断收口

- `date`: `2026-08-30`
- `run_id`: `20260830T-phk-v23-r0a-cpu-001`
- `task_id`: `PHK_V23_R0A_CPU_DIAGNOSTICS_AND_CONTRACT`
- `execution_status`: `COMPLETED`
- `diagnostic_outcome`: `R0A_INCONCLUSIVE`
- `claim_status`: `NO_METHOD_OR_COMPETENCE_CLAIM_DIAGNOSTIC_ONLY`
- `next_research_execution_authorized`: `false`
- `stress_reference_status`: `TWO_STRESS_REFERENCES_SEALED_UNREAD`

## 执行边界

`VERIFIED`：本轮只在本地 CPU/FP64 上读取既有 seed-17 `STRONG_RAW` final checkpoint，并使用冻结的 2048 点四窗均衡 Sobol pool、每窗前 128 点的 512 点梯度子集以及本地 nominal development reference。正式诊断 wall time 为 `9.321135 s`，GPU 使用 `0 h`，新增云成本 `0 CNY`。

`VERIFIED`：未构造 optimizer、未调用 `optimizer.step`、未更新参数、未训练、未选择 checkpoint、未启动 AutoDL、未读取 stress field/metric，也未实施 R0B、R1、PJGR 或 recovery intervention。参数与缓冲的 combined SHA-256 在前后均为 `E972D7724BF436520F13792CB857300D5C38E5713D9AEC6C322CA3D7B4CF47BF`，所有 state tensors 逐位相等；模型模式与 persistent gradients 保持不变。

`VERIFIED_EXECUTION_DEVIATION`：正式 run 的 RNG 快照采集发生在 legacy model 构造并 strict-load checkpoint 之后。模型构造消耗了入口 Torch CPU RNG，因此不能声称 entry-to-exit RNG 不变；只能证明 post-checkpoint-load-to-exit RNG 不变。该偏差不改变 checkpoint 参数、诊断 pool、任何测量或机器裁决。收口时已修复 runner：legacy load 现在位于 `torch.random.fork_rng` 内，且 frozen artifact 已存在时会在 checkpoint I/O 前拒绝再次执行；本次未重跑科学诊断。

首次 CLI 调用在 checkpoint I/O 之前因 PowerShell 将空 `CUDA_VISIBLE_DEVICES` 表现为变量不存在而 fail-close；修复仅把 Windows 的 unset/empty 两种表示统一为同一空 GPU mask，并新增回归。该次没有加载 checkpoint/reference，不计为科学诊断。随后只执行了上述一次正式 R0A。

## 主要测量

### VERIFIED

- 2048 点 pool 与 512 点 gradient subset 的 frozen SHA-256 分别为 `4AF7927...B2F8F` 与 `F3E09240...335E`，四窗计数分别为 `512×4` 与 `128×4`。
- sampled prediction 的最大温度仅 `0.100121`，所有窗口的最大 `T-Tc` 都为负；nominal reference 在对应 pool 的最大温度为 `0.875552`。sampled phase 最大值为 `0.027510`，后续三个窗口最大值进一步降至 `0.001506/0.000308/0.000329`，所有 ROI 的 positive kinetic-growth fraction 为 `0`。
- reference 两周期 ROI peak activity 分别为 `0.0686983`（`t=0.35`）与 `0.0619835`（`t=1.585`），对应 peak phase 均约 `0.991`；这与旧 terminal event-missing 证据一致。
- reference/prediction Joule-power trace 的 q95 比为 `1.94795`，未达到预声明 `10×` 数量级门。
- 用 reference temperature 替换 phase kinetic 的单场 probe 没有降低 phase residual：base/teacher RMS improvement ratio 为 `0.758656`；用 reference constitutive T/phase 计算 QJ、同时保留 predicted `grad V` 的 thermal probe 也没有降低 residual，ratio 为 `0.880520`。两者都低于 `10×` teacher-contrast 门，且小于 1。
- final-checkpoint phase-head 梯度出现两组强负余弦：`THERMAL_PDE ↔ PHASE_PDE = -0.997743`，`PHASE_PDE ↔ PHASE_BC = -0.934733`。potential top 的 active-pulse sigmoid 均值只有 `0.572701`，但 sigmoid derivative below `0.01` 的比例为 `0`；因此这不是已证实的 hard saturation。
- 相对 deterministic seed-17 initialization reconstruction，final phase head 的 relative L2 displacement 为 `0.546947`。因为没有历史初始 checkpoint，这只是同构初始化重建，不冒充直接历史快照。

### SUPPORTED_INTERPRETATION

- final checkpoint 同时表现为低温、无正 phase growth、边界尚未满足和强梯度冲突；这些观测排除了“只看 aggregate PDE loss 就能确定根因”的做法。
- 单场 teacher substitutions 没有产生预声明数量级改善，所以仅凭低温或终局梯度冲突不能确定它们是训练失败的主因。final-checkpoint 静态梯度也不能说明冲突在何时出现、是否早于 phase collapse，或是否由首次 causal-window switch 放大。

### HYPOTHESIS

- `LOSS_OR_HEAD_GRADIENT_CONFLICT`：由两组 final phase-head 强负余弦支持，但训练期因果仍未建立。
- `CAUSAL_OR_EARLY_TRAINING_DYNAMICS_UNRESOLVED`：现有 final checkpoint 缺少 collapse 前后的 head/gradient/field 轨迹。

### UNKNOWN

- 低 electrothermal state、potential boundary mismatch、phase output Jacobian 收缩、梯度冲突和 causal schedule 中哪一项是 primary root cause。
- 任一 recovery intervention、R1 backbone、PJGR、其他 seed/预算或 stress case 的结果。

## 裁决与下一步

机器裁决为：

```text
status = R0A_INCONCLUSIVE
primary = null
hypotheses = [LOSS_OR_HEAD_GRADIENT_CONFLICT,
              CAUSAL_OR_EARLY_TRAINING_DYNAMICS_UNRESOLVED]
reason = NO_CLEAR_ORDER_OF_MAGNITUDE_AND_TEACHER_SUBSTITUTION_CONTRAST
next_recommendation = R0B_FIRST_SWITCH_175
```

`R0B_FIRST_SWITCH_175` 只是唯一建议，不是授权，也未执行。选择 175 而不是 149，是因为其 scientific schedule denominator 仍固定为 1000，同时能够观察首次 causal switch；149-step early-only replay 无法裁决跨窗动态。任何 R0B 都需要新的版本化合同、V100 上限和用户明确授权。

## 产物

- [机器诊断 artifact](artifacts/20260830T-phk-v23-r0a-cpu-001.json)，SHA-256 `5B767A6E2FB1C64C6EE0FE5B5552DD3546C586944B55DDADF07D4B0277F31843`
- [实验 manifest](manifests/20260830T-phk-v23-r0a-cpu-001.json)
- 三份合同：`configs/phk_v23/program_contract.json`、`method_contract.json`、`r0a_diagnostic_contract.json`

本记录不 supersede PHK-V2.2R nominal terminal closeout；旧四臂 No-Go、英文 bounded-negative advisor draft 与两份 stress seals 均继续有效。
