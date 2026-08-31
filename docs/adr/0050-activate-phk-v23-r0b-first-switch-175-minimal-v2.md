# ADR 0050：激活 PHK-V2.3 R0B 首次窗口切换最小诊断

- `status`: `ACCEPTED_COMPLETE`
- `date`: `2026-08-31`
- `phase_id`: `PHK_V23_R0B_FIRST_SWITCH_175_MINIMAL_V2`
- `supersedes`: `ADR_0049_FUTURE_RESEARCH_AUTHORIZATION_ONLY`
- `preserves`: `ADR_0049_R0A_INCONCLUSIVE_AND_PHK_V22R_TERMINAL_NO_GO`
- `decision_source`: 当前用户明确授权完整执行 R0B、使用已启动 GPU，并要求结束后立即关闭 AutoDL 实例

## 决定

接受一次 reference-blind、seed-17、FP64、`STRONG_RAW` scratch replay。冻结科学 schedule denominator 为 `1000`，但只执行 `175` 个 canonical Adam updates；step 151 是首次从 W1-only 切换到 W1+W2 并刷新 collocation 的更新。该运行只识别训练期最早获得支持的 temporal precursor candidate，不恢复 competence、不证明方法增益，也不把单次无干预轨迹写成因果根因。

采用现有 trainer 上的一个可选只读 observer seam。observer 不接收 sampler 或 optimizer，不调用 `backward`、`zero_grad` 或 optimizer step；它只在冻结节点用独立 Sobol pool 与 `autograd.grad` 记录场、Jacobian、PDE 分项和 loss-by-head gradients。observer 关闭时保持旧 trainer 行为；不得建立平行 trainer、PDE、sampler 或 evaluator。

旧计划中的九次云端 shadow updates 被本决定否决。V100 只执行 175 个 canonical updates。只有 reference-blind machine decision 为 `SWITCH_INDUCED` 时，才允许实例关闭后在本地 CPU 对 step-151 transition bundle 做零 optimizer-step 的 gradient-only factorial；否则固定记录 `FACTORIAL_NOT_RUN_NOT_NEEDED`。

## Reference 与证据边界

- 云端代码、合同、observer、loss、sampler、checkpoint、prediction 与 machine telemetry 均不得出现 nominal/stress reference。
- 云端产物回收并核验后立即关机；reference-blind adjudication 必须先不可变写入。
- 只有其后才可本地打开 nominal development reference，形成 non-voting appendix；不得改变 primary precursor candidate、阈值、checkpoint、intervention 或下一阶段授权。
- 两份 stress reference 继续 `SEALED_UNREAD`，R0B 数据流在任何文件 I/O 前对其 fail closed。

## 预算与停止

- GPU：`Tesla V100-PCIE-32GB`；FP64；seed 17；唯一科学运行。
- GPU wall hard cap `1 h`，付费工作 soft stop `45 min`，增量估算费用 hard cap `5 CNY`。
- V2.3 全局上限仍为 `34 GPU-h / 95 CNY / 14 days`，项目绝对云成本上限仍为 `150 CNY`；未用余额不能换 seed、模块或救援。
- 身份/GPU/合同漂移、reference 可达、observer 改变训练状态、非有限值、重复进程、超时、非 175 updates 或 switch 身份错误均立即停止且不自动重跑。
- 完成 R0B 后不自动授权 R1、PJGR、stress、第二次 run、作者联系或投稿。

## 保留结论

R0A `R0A_INCONCLUSIVE` 与 V2.2R `MVP_NO_GO_NO_BASIC_COMPETENCE` 原样保留。R0B 即使识别一个 precursor candidate，也只产生下一项原子干预的计划线索，不产生正向论文方法证据。

## 执行结果

一次性授权已由 run `20260831T095149-phk-v23-r0b-first-switch-175-8d072e2` 消耗。V100 完成 175 canonical updates、0 cloud shadow steps，产物回收并逐哈希核验后 AutoDL 已 shutdown，SSH 复核为 `Connection refused`。

reference-blind decision 为 `R0B_PRECURSOR_CANDIDATE_IDENTIFIED`，primary 是 `GRADIENT_STARVATION`（step 10/25）；后续支持 `GRADIENT_CONFLICT`（75/100）与 `ELECTROTHERMAL_DRIVE_DEFICIT`（110/120）。primary 不是 `SWITCH_INDUCED`，所以 factorial 固定为 `FACTORIAL_NOT_RUN_NOT_NEEDED`。nominal appendix 只在 decision 不可变写入后本地生成且不参与投票。完整边界见 [R0B closeout](../experiment/2026-08-31-phk-v23-r0b-first-switch-175-closeout.md)。本 ADR 不授权任何后续执行。
