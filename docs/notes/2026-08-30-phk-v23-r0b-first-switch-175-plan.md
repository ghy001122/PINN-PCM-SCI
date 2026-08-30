# PHK-V2.3 R0B FIRST_SWITCH_175 精确执行计划

- `date`: `2026-08-30`
- `task_id`: `PHK_V23_R0B_FIRST_SWITCH_175_PLAN_ONLY`
- `mode`: `PLAN_ONLY_PROPOSED_NOT_AUTHORIZED`
- `source_conversation_id`: `6a93c493-0068-83ee-a73a-7267af995849`
- `source_role`: `UNTRUSTED_RESEARCH_PLANNING_CONTEXT_VERIFIED_AGAINST_LIVE_REPOSITORY`
- `document_role`: `NON_AUTHORITATIVE_FUTURE_ROADMAP_NOT_LIVE_PLAN`
- `status`: `PROPOSED_NOT_AUTHORIZED`
- `evidence_anchor_commit`: `771d015b31ca7ac4d1ee75802580edff86ce275a`
- `scientific_execution`: `NONE`
- `scientific_claim_change`: `NONE`
- `gpu_hours_this_plan_task`: `0`
- `cloud_cost_this_plan_task_cny`: `0`
- `next_research_execution_authorized`: `false`

用户对 GitHub 交付的授权只允许持久化本次规划。它不把本笔记采纳为 ADR、live plan、program/method contract 或科研执行授权；[`active_phase.md`](../../active_phase.md)、[`PROJECT_STATE.md`](../../PROJECT_STATE.md) 与唯一 [live plan](../plans/NEXT_ACTIONS.md) 保持不变。R0A 的 `R0A_INCONCLUSIVE`、PHK-V2.2R terminal No-Go 与两份 stress seal 均不得被本笔记覆盖。

## 1. VERIFIED CURRENT STATE

### 1.1 仓库与授权

- `VERIFIED`：计划起草时核验基线的本地 `HEAD`、本地 `main` 与远端 `PINN-PCM-SCI/main` 均为 `771d015b31ca7ac4d1ee75802580edff86ce275a`；本地 `main` 未配置 upstream。该 SHA 是规划证据锚点，不冒充本计划提交后的新 `HEAD`。
- `VERIFIED`：活动阶段为 `PHK_V23_R0A_CPU_DIAGNOSTICS_AND_CONTRACT`，lifecycle 为 `COMPLETE`，R0A 裁决为 `R0A_INCONCLUSIVE`。
- `VERIFIED`：`next_research_execution_authorized=false`；R0B、R1、PJGR、GPU、AutoDL 与 stress access 均未授权。
- `VERIFIED`：本次 PLAN 未构造模型、未加载 checkpoint、未 forward/backward、未训练、未读取 nominal/stress reference、未运行测试、未使用 GPU 或云端。
- `VERIFIED`：工作树中另有其他会话/用户的无关 dirty；它们不属于本计划的交付范围。

R0A 数值、执行偏差与身份分别由 [closeout](../experiment/2026-08-30-phk-v23-r0a-cpu-diagnostics-closeout.md)、[machine artifact](../experiment/artifacts/20260830T-phk-v23-r0a-cpu-001.json) 和 [run manifest](../experiment/manifests/20260830T-phk-v23-r0a-cpu-001.json) 锚定。

### 1.2 R0A 的有效结论

- `VERIFIED`：R0A 是一次 CPU/FP64、零 optimizer step、零参数更新的只读诊断；模型 state tensors 与 SHA-256 前后相同，stress 未访问。
- `VERIFIED_EXECUTION_DEVIATION`：冻结 artifact 的 entry-to-exit CPU RNG 不相同，原因是 legacy model construction 发生在快照前；post-load-to-exit RNG 相同。该偏差没有改变 checkpoint 参数、冻结 pool 或测量。代码已修复但没有重跑科学诊断，因此不得宣称“修复后的 runner 已复现 artifact”。
- `VERIFIED`：sampled `T_max=0.100121<T_c=0.45`，sampled `phase_max=0.027510`，后续三窗最大 phase 为约 `0.001506/0.000308/0.000329`，所有 ROI positive kinetic-growth fraction 为 `0`。
- `VERIFIED`：final phase-head 出现 `THERMAL_PDE ↔ PHASE_PDE=-0.997743` 与 `PHASE_PDE ↔ PHASE_BC=-0.934733` 的强负余弦，但这是 final static evidence。
- `VERIFIED`：两个 teacher-contrast improvement ratios 为 `0.758656` 与 `0.880520`，Joule q95 reference/prediction ratio 为 `1.94795`；均未过冻结 `10×` 识别门。
- `SUPPORTED_INTERPRETATION`：低电热状态、phase-Jacobian 收缩、边界未充分满足和梯度冲突共同存在，但 final checkpoint 无法给出因果顺序。
- `UNKNOWN`：哪一项是 primary root cause；R0B 也最多识别冻结 taxonomy 下最早获得支持的 temporal precursor/candidate mechanism，不能凭单次无干预 replay 宣称因果根因。任何 recovery、PJGR、额外 seed、stress 或更长预算的结果仍为未知。

### 1.3 R0A adjudicator coverage gap

当前 R0A machine adjudicator 实际只消费 teacher/Joule ratio、gradient-norm ratio 与 conflict cosine；它没有完整执行化：

1. phase-output Jacobian conditioning；
2. potential boundary conditioning；
3. per-window electrothermal trajectory；
4. spatial Joule localization；
5. phase-temperature teacher contrast 的独立时间序列。

冻结 R0A artifact 不重裁、不重写。拟议 R0B 必须建立新的、结果可见前冻结的 executable taxonomy。由于 nominal-derived quantity 不得选择 intervention，teacher probes 只能在 reference-blind A–H 裁决排他落盘、云端产物回收且实例关闭后于本地运行，并作为 `NON_VOTING_POSTHOC_CONTEXT` 单独报告。

## 2. 审查整合与完整有界路线

### 2.1 当前最应解决的问题

`SUPPORTED_INTERPRETATION`：当前最高信息增益问题不是 Fourier、sampler 或 PJGR，而是确定以下三者的训练期先后顺序：

```text
potential/boundary 或 electrothermal drive 失败
→ phase output Jacobian 进入低敏感区
↔ loss/head gradient starvation 或 conflict
```

首次 causal switch 可能触发或放大上述链条，因此只执行一次 `R0B_FIRST_SWITCH_175` 是当前最短的时间先后鉴别路径。它只识别“最早获得支持的前兆/候选机制”，不是 recovery、因果干预或方法贡献。

### 2.2 假设排序

1. `LOSS_OR_HEAD_GRADIENT_CONFLICT`：`SUPPORTED_INTERPRETATION`，但需要动态先行证据。
2. `PHASE_OUTPUT_JACOBIAN_CONDITIONING`：`HYPOTHESIS`，需判断收缩是原因还是结果。
3. `ELECTRICAL_OR_BOUNDARY_CONDITIONING_FAILURE / ELECTROTHERMAL_DRIVE_DEFICIT`：`HYPOTHESIS`，不能被 R0A teacher probes 排除。
4. `CAUSAL_OR_EARLY_TRAINING_DYNAMICS_UNRESOLVED`：鉴别轴，不是已经识别的具体根因。

### 2.3 后续阶段与止损

下表全部为 `PROPOSED_NOT_AUTHORIZED`。V2.3 全局硬上限保持 `34 GPU-hour / 95 CNY / 14 calendar days`；未来 program contract 必须把 `phase_start_utc` 冻结为激活 R0B 的 ADR 生效时间，绝对截止为 `phase_start_utc + 14*24 h`。未用余额不得换 seed、加模块或救援。

| 阶段 | 唯一目标 | GPU/费用上限 | 通过后 | 失败后 |
|---|---|---:|---|---|
| R0B | 识别首次 switch 前后最早获得支持的 temporal precursor/candidate mechanism | `1 h / 5 CNY` | 只形成一个 R1a atomic intervention 提案 | `R0B_INCONCLUSIVE_STOP` 则不授权 R1 |
| R1a/R1b | 先单轴、再至多一个预冻结复合 backbone 恢复 raw competence | 合计 `3 h / 10 CNY` | 冻结 competent common backbone | 两者均失败则停止纯 scratch；仅可另立 low-fidelity 合同 |
| R2A | seed 17 下验证唯一核心机制的独立增量 | `6 h / 16 CNY` | 才扩 seeds | proposed 不过门即停止 |
| R2B | seeds 29/43 与 seed 17 的方向一致性 | `6 h / 16 CNY` | 进入公平性校准 | raw 不稳或增量不稳即停止 |
| Fairness | parameter-matched 与 measured-time raw controls | `3 h / 8 CNY` | candidate/comparator 可冻结 | 增量消失即停止 |
| R3 | 两个 stress × 三个冻结角色，六 carrier 后一次性本地开封 | `15 h / 40 CNY` | 形成 sealed outcome | 任一 sealed guard 失败即终局 |
| R4 | 图表、Results、Discussion、Supplement、claim audit 与英文初稿 | CPU / `0 CNY` | evidence-bounded 稿件 | 删除无证据主张 |
| Low-fidelity pivot（R1a/R1b 均失败时的替代路线） | 另立对象、合同与论文身份，只做一次独立有界验证 | `6 h / 16 CNY`，非加法；占用原 R2A tranche，并永久取消本路线的 R2B/Fairness/R3 | 独立收口，不回流 pure-scratch Method-MVP | 终止该 pivot |

R0B outcome 到 R1a 的唯一映射：

| R0B primary precursor candidate | 唯一允许提议的 R1a |
|---|---|
| electrical/boundary | potential output/BC parameterization |
| electrothermal drive | electrothermal-first curriculum |
| phase Jacobian | phase latent/output reparameterization |
| gradient starvation | slow head-aware balancing |
| gradient conflict | kinetics-conditioned headwise conflict resolution；必须对照 generic conflict-free optimizer |
| causal switch：`trigger_component=WINDOW_MIXTURE` | causal schedule correction |
| causal switch：`trigger_component=W1_RESAMPLE` 或 `BOUNDARY_IC_REFRESH_MIXTURE` | refresh stabilization；仍只是一项 atomic proposal |
| causal switch：复合来源无法排他 | `R0B_INCONCLUSIVE_STOP`，不进入 R1 |
| fixed budget/other optimization | `BOUNDED_OPTIMIZATION_DIAGNOSTIC_PLAN_ONLY`；不得据此选择 R1 或延长预算 |
| inconclusive | `FINAL_PURE_SCRATCH_DIAGNOSTIC_STOP` |

R1 competence 恢复后只能选择一个 load-bearing method family：若 R0B 在冻结门下支持 conflict 是严格更早的 precursor candidate，优先审查 kinetics-conditioned headwise conflict resolution；只有 competent raw 的剩余误差确实局域于 phase interface/Joule hotspot 且显式 gate 有信息量时，PJGR 才从 `CONDITIONAL_CANDIDATE` 激活。两者不得结果后串行试错。成熟的 MF、RAR/RBAR、L-BFGS、continuation 与 block-coordinate training 只能作为透明归因的 backbone/comparator，不得各自包装为原创。

## 3. R0B SCIENTIFIC CONTRACT DRAFT

### 3.1 身份

```text
proposed_phase_id = PHK_V23_R0B_FIRST_SWITCH_175
status = PROPOSED_NOT_AUTHORIZED
scientific_role = FAILURE_TEMPORAL_PRECURSOR_DIAGNOSTIC
case = FULL nominal development case
arm = STRONG_RAW
initialization = SCRATCH_START
seed = 17
dtype = FP64
device = Tesla V100-PCIE-32GB only
canonical_optimizer_steps = 175
executed_optimizer_steps = 175  # alias for canonical persisted trajectory only
noncanonical_shadow_updates = 9  # 8 factorial cells + old-full-W1 anchor
scientific_schedule_denominator = 1000
reference_blind_cloud_replay = true
recovery_intervention = NONE
```

必须继承原 V2.2R strong-raw 的 model、physics、loss、sampler 与 Adam：width 64、4 hidden layers、raw normalized inputs、lr `1e-3`、global clip `10`、`512/128/128` collocation、uniform Sobol、refresh interval 250、loss weights `1/5/1`、四个原 causal windows。不得加载 final checkpoint、不得 warm start、不得改 threshold、不得 early stop、不得 checkpoint selection。

### 3.2 实现合同

现有 `PhkTrainingConfig.updates=1000` 同时决定循环长度和 `_active_windows` 分母。R0B 禁止把它改成 175；未来实现必须新增独立的 execution limit：

```text
config.updates = 1000                    # scientific denominator and identity
execution_control.executed_steps = 175  # bounded loop limit
_active_windows(update_index, 1000)      # unchanged legacy schedule
```

observer 是现有 trainer 的可选只读 seam；`None` 时必须保持 legacy output、loss、gradient、optimizer、Sobol、collocation、checkpoint 与 parameter bytes 不变。callback 只可接收 read-only model view、不可变的 detached coordinate/batch context、冻结 effective weights、trainer 计算的 detached pre/post-update summaries，以及仅在 transition event 提供的 immutable deep-copied model/Adam-state snapshot；它不得接收 live sampler 或 canonical optimizer。需要 Jacobian/parameter-gradient 的常规 probe 只能由 observer 在独立重建的计算图上用 `autograd.grad` 计算，不得调用 `.backward()`、`zero_grad()` 或修改既有 `.grad`。不得复制第二套 trainer、PDE、sampler 或 evaluator。

为保证 all-on shadow 与 canonical step 151 exact equal，未来实现必须先从 legacy loop 中抽取唯一共享的 `training_step_kernel(model, optimizer, frozen_batches, config)`，保持 loss→backward→pre-clip log→clip→Adam step 的现有顺序。canonical trajectory 调用该 kernel 175 次；R0B adapter 只在 clones 上调用同一 kernel 9 次。`phk_v23_r0b.py` 不得复制 loss aggregation、backward、clip 或 Adam 逻辑；kernel 的 shadow mode 只关闭 canonical log/checkpoint side effects，不改变数值路径。

固定 diagnostic pools 使用独立 Sobol engine、seed 17、FP64：W1/W2 interior 各 512 点；每个 window 的每个 boundary side 各 32 点；固定 IC 128 点。坐标与 hashes 在模型构造前生成并冻结，training sampler 的 state/call count 不得因此改变。

### 3.3 Reference 边界

- 云端 trainer/model/loss/sampler/observer/decision 输入类型中不得出现 reference、label、oracle、reference path 或 stress control。
- 固定 W1/W2 interior、boundary 与 IC diagnostic pools 仅由物理域、独立 Sobol engine、冻结 seed/count 产生；不得读取 reference 决定坐标。
- 每个 observation 可保存本地 teacher probe 所需的 detached model-side tensors；云端不执行 teacher substitution。
- checkpoint、prediction、telemetry、log、manifest 和哈希全部回收，实例关闭并确认 SSH refused 后，才可在本地读取 frozen nominal development reference。
- 本地 reference 只进入 A–H 排他裁决之后的事后评价与 `NON_VOTING_POSTHOC_CONTEXT`；不得改变 primary precursor class，且不得选择 checkpoint、停止时间、loss、sampler、threshold 或 intervention。
- R0B 模块与阶段内 stress path 始终在任何文件 I/O 前 fail closed；全项目只有未来通过 candidate freeze 且六份 carrier 身份门后才可能另行授权本地开封。当前两份 stress fields/metrics 保持 sealed/unread。

### 3.4 RNG 与 observer invariance

- 整个 scratch construction + replay 位于 `torch.random.fork_rng(devices=[cuda_index])` 的有界域内；此外必须在进入前分别 snapshot Python `random` 与 NumPy RNG state，并用 `try/finally` 在成功或异常退出时恢复。域内先按 legacy 顺序 seed，再构造模型、optimizer 与 training sampler，使初始权重及训练随机序列与 observer-off legacy replay 一致。
- 每次 observer 另设嵌套 RNG guard；observer 前后 CPU RNG、当前 CUDA RNG、parameter、buffer、optimizer state 与已有 `.grad` 必须逐位相同。
- diagnostic sampler 使用独立 Sobol engine，绝不复用或推进 training sampler engine。
- observation state 记录 parameter/buffer/optimizer/collocation/RNG digest；只写 final step-175 checkpoint，不保存可供选择的中间 checkpoint。
- 冻结 R0A artifact 永久不可重建或覆盖。

## 4. EXACT SCHEDULE AND OBSERVATION SEMANTICS

| 记录名 | 完成的 zero-based update index | one-based optimizer step | active windows | refresh 语义 |
|---|---:|---:|---:|---|
| `pre_000` | 无 | 0 | observer 固定 W1/W2 pools；training cache 尚为空 | 无 optimizer/collocation |
| `post_001` | 0 | 1 | 1 | 初始 cache refresh；同时 `0 % 250 = 0` |
| `post_005` | 4 | 5 | 1 | 不刷新 |
| `post_010` | 9 | 10 | 1 | 不刷新 |
| `post_025` | 24 | 25 | 1 | 不刷新 |
| `post_050` | 49 | 50 | 1 | 不刷新 |
| `post_100` | 99 | 100 | 1 | 不刷新 |
| `post_149` | 148 | 149 | 1 | 不刷新 |
| `post_150` | 149 | 150 | 1 | W1-only 的最后一次 update |
| `post_151` | 150 | 151 | 2 | 首次 W1+W2 update；仅因 active-window 从 1 变 2 而 refresh |
| `post_160` | 159 | 160 | 2 | 不刷新 |
| `post_175` | 174 | 175 | 2 | final observation/final checkpoint |

因此 step 150 是 switch 前最后状态；step 151 才是第一个使用两窗 collocation 的 optimizer step。step 151 的 training interior 由 512 点在 W1/W2 等分为 256/256；同一次 refresh 还会完全重采样四侧 boundary 与 initial batch。实际-batch 跳变因而混合了“开启 W2 + W1 重采样 + boundary/IC 重采样”，不能单独归因为 W2。observer 的固定 W1/W2 pools 各自保持 512 点，不随 training refresh 改变，只有固定 W1 的 post-150/post-151 差值可用于 forgetting 判据。legacy 周期 refresh 的下一次 index 250 不在本 replay 内。

每个 `post_s` observation 必须拆成两个不混用的 phase：`PRE_BACKWARD_ACTUAL_BATCH(step=s)` 在参数 `theta_(s-1)` 上记录实际 canonical batch、full-objective/逐项 gradients、pre-clip norm 与 hashes；`POST_STEP_FIXED_POOL(step=s)` 在参数 `theta_s` 上记录固定 W1/W2 outputs、latents、Jacobians、residuals 与 separate-graph gradient matrix。实际 head update 是 `theta_s-theta_(s-1)`。机器必须保存 phase 标签：A–E 的时间 onset 使用 `POST_STEP_FIXED_POOL`，F 同时使用 step-151 的 `PRE_BACKWARD_ACTUAL_BATCH`、shadow factorial 与 post-151/post-160 fixed-pool 持续性；任何 post-step 重算 gradient 都不得冒充产生该 canonical update 的 pre-backward gradient。

未来 observer 必须在 `theta_150`（完成 step 150、尚未执行 step 151）上生成一个不增加 canonical optimizer observation point 的 `transition_151_counterfactual`。该事件内部冻结两个 probe phases：`pre_151_before_refresh` 保存旧 W1 interior/boundary/IC batch 与 model/Adam state 的只读快照；trainer 随后按原顺序执行唯一一次 canonical refresh；`pre_151_after_refresh_before_backward` 在参数仍为 `theta_150` 时记录真正将驱动 step 151 的新 batch gradient/clip inputs。observer 不得自行调用 sampler或 canonical optimizer。

排他诊断使用八个一次性、非 canonical 的 clone-model/clone-Adam functional one-step factorial cells，三项二元因子为：`WINDOW_MIXTURE`（256 W1 重复为 512 vs 256 W1+256 W2）、`W1_RESAMPLE`（旧 W1 first-256 vs 新 W1-256）和 `BOUNDARY_IC_REFRESH_MIXTURE`（旧 vs 新 boundary/IC）。另运行一个 `OLD_FULL_W1_ANCHOR`：旧完整 512-W1 interior + 旧 boundary/IC。九个 shadows 均从完全相同的 `theta_150` 与 Adam moment snapshot 出发，loss 权重、clip 与 update 公式一致；只在 clones 上执行一次 shadow update，并在同一固定 W1 probe 上计算输出差值。anchor 与 factorial all-off 的差异专门量化“旧 W1 从 512 unique 点缩为 first-256 后重复”的 support bias：对每个冻结 response 定义 `delta_anchor=m_alloff-m_oldfull`、`relative_anchor=abs(delta_anchor)/max(abs(m_oldfull),epsilon)`、`trend_anchor=abs(delta_anchor)/d_pre(m)`；除 positive-growth fraction 外，任一 `relative_anchor>=0.10` 或 `trend_anchor>=1` 即失败，positive-growth fraction 则以 `abs(delta_anchor)>=0.05` 或 `trend_anchor>=1` 失败。方向只记录、不参与放行。有效 response 集合先应用后文统一的 zero-norm/null policy；anchor 或 all-off 任一侧为 null 时整项删除，删除后少于两个 responses 或没有 phase/Jacobian/gradient response 也转 H。失败写 `UNRESOLVED_W1_SUPPORT_REDUCTION` 并转 H。只有 anchor 门通过后才计算 factorial main effects/interactions 和唯一 `trigger_component`。所有 shadows 标为 `NONCANONICAL_COUNTERFACTUAL_NO_CLAIM`，不保存 checkpoint、不计入 175 canonical steps，也不能替代实际 post-151/post-160 持续性证据。

冻结 W2 为 `[0.35,1.25)`，而原 pulse 在 `t=0.35` 后为零。因此 W2 的 active-pulse potential-BC、instantaneous QJ 与 ROI/global QJ ratio 必须写成 `null` 并附 `NOT_APPLICABLE_ZERO_DRIVE`；`0/0` 不得编码成 0、不得进入 A/B/F 投票。active-pulse boundary 与 Joule-injection 判据只在 W1 的非零 waveform subset 上投票；W2 仍记录 T/phase、冷却/扩散/kinetic 与固定-pool forgetting 指标。

A、B 只用 W1 active masks；C 只用 `POST_STEP_FIXED_POOL` 的 W1 ROI；D/E 只用 W1 fixed interior + W1 fixed boundary + fixed IC 的 `POST_STEP_FIXED_POOL` gradients，phase-head update 一律取 relative-L2，实际 W1+W2 canonical-batch gradients只作 non-voting provenance；F 使用上文指定的 canonical W1 response/shadow supports；G 的六项 health votes 全部用 W1 fixed supports，并要求每一票在 151→160 与 160→175 两个区间均沿同一改善方向满足各自门。W2 或 pooled supports 除 F 的 `WINDOW_MIXTURE` factor 外一律不得触发 A–G。

每个 observation 对 W1 与 W2 分别记录：

1. V/T/phase min/max/mean/RMS/q05/q50/q95/q99；
2. phase activity 与 ROI positive kinetic-growth fraction；
3. V/T/phase latents、raw sigmoid derivatives 与 analytic output Jacobians；
4. active-pulse top/heater potential BC RMS、latent、sigmoid derivative 与 low-derivative fraction；
5. global/ROI spatial Joule-density statistics与定位比；
6. electric/thermal/phase residual decomposition，包括 net thermal drive；
7. 六 loss × 三 head 的 effective-weight gradient norms；这六行覆盖 electric/thermal/phase PDE 与 BC；另记录 IC-inclusive full-objective-by-head gradient norm 作为 E 的 materiality denominator，并把 aggregate IC-by-head 单列为 non-voting 完整性字段；
8. 同一 head 的全部非零 pairwise gradient cosines；只有第 5 节预冻结的两个 phase-head pairs 可投票，其余为 non-voting diagnostics；
9. 该 optimizer step 的每个 head 参数实际 `L2/max/relative-L2` update norm；`pre_000` 为 `null:NO_UPDATE`；
10. active-window count、refresh reason、training Sobol/RNG state、training/diagnostic coordinate hashes；
11. step 150/151 的同一固定 W1 pool 差值，以及 `theta_150` 上八个 factorial cells + 一个 old-full-W1 anchor 的 `transition_151_counterfactual` 三因子诊断；
12. observation 前后 parameter/buffer/optimizer/`.grad` identity；W2 的结构性无定义字段使用带 reason 的 nullable schema，不受“所有数值 finite”检查误判。

云端还保存每个 observation 的 reference-blind detached tensors：coordinates、T、phase、grad-V、lap-phase、phase-time、thermal-nonjoule 与 base residuals。它们只供关机后的本地 frozen nominal teacher probes 使用。

## 5. EXECUTABLE TEMPORAL-PRECURSOR DECISION TABLE

### 5.1 结果可见前冻结的公共阈值

以下为未来合同提案，不是当前已生效阈值：

```text
zero_norm_epsilon = 1e-18                  # 继承 R0A
order_of_magnitude_ratio = 10              # 继承 R0A
gradient_conflict_cosine = -0.90           # 继承 R0A
gradient_pair_material_fraction = 0.10     # 相对 IC-inclusive total head gradient
phase_output_jacobian_floor = 0.01          # 继承 R0A
low_jacobian_fraction = 0.95               # 继承 R0A
minimum_material_relative_change = 0.10    # R0B 新提案
dominant_component_ratio = 10              # R0B transition factorial
maximum_interaction_fraction = 0.10        # 相对 dominant main effect
minimum_consecutive_observations = 2       # R0B 新提案
potential_boundary_error_rms_floor = 0.10  # R0B 新提案
low_positive_drive_fraction = 0.05         # R0B 新提案
roi_to_global_joule_ratio_floor = 0.10     # R0B 新提案
phase_activity_threshold = 0.50            # 继承 R0A
```

新 predicate 必须在两个连续的已冻结 observation points 为真；只在 step 175 首次出现的 predicate 不得成为 primary。一直从 scratch initialization 为真的 predicate 只能列为背景 hypothesis，除非随后出现可观测的“先改善、再恶化”顺序。scalar loss share 永远不能单独触发任何类别。

除 positive-growth fraction 已明确使用绝对变化外，所有“改善/恶化 `10%`”均按相邻冻结 observation 的 `abs(m_new-m_old)/max(abs(m_old),epsilon)` 计算，并由预声明的 higher-is-better/lower-is-better 极性决定符号；不得用结果后选择分母或区间。

定义 downstream phase-collapse onset 为以下任一项从 false 变 true 并连续两个 observation 保持：phase q95 相对此前最大值下降至少 `10×`；positive-growth fraction 从大于 `0.05` 降至不大于 `0.05`；或 phase-head update norm 相对 V/T 最大值下降至少 `10×`。phase Jacobian 低敏感本身作为候选原因，不放进该 downstream 定义。

为使时间先后规则可机器执行，冻结以下别名与极性：`temperature_deficit=max(Tc-ROI_T_max,0)`；`electrothermal_degradation` 是 temperature deficit、W1 active-pulse BC RMS 任一上升 `>=10%`，或 W1 QJ q95/net-positive-drive fraction 任一下降 `>=10%` 的首个两点持续 onset；`phase_degradation` 就是上段 downstream phase-collapse onset。BC error、temperature deficit、residual RMS、low-Jacobian fraction 与 conflict severity 上升为不利；W1 QJ、positive-drive fraction、phase q95/activity、output-Jacobian 与 head-update norm 下降为不利。`early_activation_proxy=true` 仅当 ROI phase q95 `>=0.50` 且 ROI activity fraction `>0`，不冒充完整 event competence。

step-151 shock 对任意固定 W1 标量 `m` 只使用冻结的 100/149/150 基线：

```text
d_pre = max(abs(m_150 - m_149), abs(m_149 - m_100) / 49, epsilon)
J_151 = abs(m_151 - m_150) / d_pre
```

只有 `J_151>=10` 且 `abs(m_151-m_150)/max(abs(m_150),epsilon)>=0.10` 时才是 material shock。cosine 必须从 `>-0.90` 跨越至 `<=-0.90`，不用相对除法。shock 还必须在 step 160 保持同一不利 predicate 才可投票。

A/B 公共量严格定义为：`active_mask = waveform(t)>1e-12`；固定 ROI 为 `abs(x)<=0.55 and 0<=z<=0.55`；bottom-heater mask 另要求 `abs(x)<=0.35`。top normalized sigmoid error 为 `1-sigmoid(h_V)`，bottom-heater normalized sigmoid error 为 `sigmoid(h_V)`，分别在 W1 active mask 上取 RMS。`net_thermal_drive = 0.10*lap(T)-4*T+4*QJ-0.05*phi_t`，positive fraction 是 W1 active ROI 内 `net_thermal_drive>0` 的点比例。`joule_localization_ratio = q95(QJ[W1 active ROI])/q95(QJ[W1 active domain])`；分母 `<=epsilon` 时 ratio=`null:ZERO_GLOBAL_JOULE` 并由 B 的 zero-global 分支处理，禁止写成 0。

八-cell factorial 对每个 response `m` 采用 `x_M,x_R,x_B in {-1,+1}` 编码，并冻结方向：`x_M=-1` 为把 `x_R` 选中的 W1-256 重复成 512、`+1` 为该 W1-256 + W2-256；`x_R=-1` 为 old W1 first-256、`+1` 为 new W1-256；`x_B=-1` 为旧 boundary/IC、`+1` 为新 boundary/IC。不得交换正负编码。

```text
beta_S(m)   = (1/8) * sum_x(product(x_j for j in S) * m_x)
effect_S(m) = 2 * beta_S(m)              # S 为 main 或 interaction
adverse_score_i(m) = polarity(m) * effect_i(m) / d_pre(m)
interaction_score  = max_m,S:|S|>=2 abs(effect_S(m)) / d_pre(m)
```

冻结且仅允许以下 F responses：active-pulse BC RMS、temperature deficit、voting-pair conflict severity（`max(0,-min(voting cosines))`）为 adverse polarity `+1`；phase q95、positive-growth fraction、phase-output-Jacobian q50、phase-head shadow-update norm 为 `-1`。若任一 factorial cell 的两个 voting pairs 都因任一梯度范数 `<=epsilon` 而 cosine 为 null，则 conflict response 从全部八 cell 的 F factorial 中整项删除并标记 `NON_VOTING_ZERO_NORM`，不得以 0 填充；删除后不足两个有效 responses 则转 H。除 positive-growth fraction 要求绝对 effect `>=0.05` 外，其余 response 要求 `abs(effect_i)/max(abs(m_150),epsilon)>=0.10` 才算 material。每个 factor 的 `component_score` 是其 material adverse scores 的第二大值；少于两个 material responses，或其中没有 phase/Jacobian/gradient response，则 score=0。唯一 trigger 要求 dominant `component_score>=10`、`dominant>=10*max(second_largest_component_score,1)` 且 `interaction_score<=0.10*dominant`；否则转 H。canonical `shock_set` 也只由这些 responses 构成，且必须与 dominant factor 的 material-adverse response 集合至少重合两项，其中至少一项属于 phase/Jacobian/gradient；同一组重合 predicates 必须在 step 160 保持不利。这样 response 归约、主效应、交互与多指标合并均无结果后裁量。

### 5.2 八类判据

| 类别 | executable predicate | 时间要求与动作 |
|---|---|---|
| A `ELECTRICAL_OR_BOUNDARY_CONDITIONING_FAILURE` | W1 active-pulse top/heater sigmoid-error RMS 任一 `>=0.10`，并且 low-derivative fraction `>=0.95`，或 BC error 在两个连续 observation intervals 的改善均 `<10%` 而 electric-BC→potential gradient 与 potential update 均非零 | A onset 必须严格早于 `electrothermal_degradation` 与 `phase_degradation`；否则只作 hypothesis。通过只提议 potential/BC reparameterization |
| B `ELECTROTHERMAL_DRIVE_DEFICIT` | A 不成立，且 W1 active-pulse ROI `T_max<Tc`，且满足以下至少一项：net-thermal-drive positive fraction `<=0.05`；global QJ q95 `<=epsilon`；global QJ q95 `>epsilon` 且 ROI/global QJ q95 `<=0.10` | 两个连续点成立并严格先于 `phase_degradation`；只提议 electrothermal-first curriculum。关机后 teacher contrast 为 non-voting，不得改变 B |
| C `PHASE_OUTPUT_JACOBIAN_CONDITIONING` | 至少 `95%` ROI points 的 `|dphi/dh_phi|<=0.01`，同时 phase-PDE→phase-head gradient 未满足 starvation，且此前至少一个 observation 满足 ROI positive kinetic-growth fraction `>0.05` 或 ROI phase q95 `>=0.10` | Jacobian-low onset 必须先于 downstream phase collapse；只提议 phase output reparameterization |
| D `LOSS_OR_HEAD_GRADIENT_STARVATION` | `N_phase=max(||g_PHASE_PDE→phase||,||g_PHASE_BC→phase||)`；`D_phase=max(||g_ELECTRIC_PDE→phase||,||g_THERMAL_PDE→phase||,||g_ELECTRIC_BC→phase||,||g_THERMAL_BC→phase||,epsilon)`；要求 `N_phase<=0.1*D_phase`，且 phase-head actual update norm `<=0.1*max(potential-head update,temperature-head update)` | 两个连续点、C 不成立且严格先于 `phase_degradation`；只提议 slow head-aware balancing。其他 heads 的 starvation 仅作 non-voting diagnostics |
| E `LOSS_OR_HEAD_GRADIENT_CONFLICT` | 只允许两个预冻结 voting pairs：phase head 的 `THERMAL_PDE__PHASE_PDE` 与 `PHASE_PDE__PHASE_BC`；同一 pair 的两项范数均 `>=0.10*max(||g_full_objective→phase||,epsilon)` 且 cosine `<=-0.90`；`g_full_objective` 包含 PDE、BC 与 IC | 同一冻结 pair 两个连续点且严格先于 `phase_degradation`；其他 pair 仅作 non-voting diagnostics。generic conflict-free optimizer 是强 baseline，不能把普通 conflict handling 当新颖性 |
| F `CAUSAL_SWITCH_INDUCED_CONFLICT_OR_FORGETTING` | old-full-W1 anchor 门通过；canonical `shock_set` 与唯一 dominant factor 的 material-adverse responses 至少重合两项，其中至少一项来自 phase/Jacobian/gradient；同一重合 predicates 在 canonical step 160 持续 | 记录唯一 `trigger_component=WINDOW_MIXTURE|W1_RESAMPLE|BOUNDARY_IC_REFRESH_MIXTURE`。前者只提议 causal schedule correction，后两者只提议 refresh stabilization；不满足任一排他门即转 H。F 的 candidate onset 固定为 151、confirmation 为 160；与任何 A–E 同刻 onset 均转 H |
| G `FIXED_BUDGET_OR_OTHER_OPTIMIZATION_UNRESOLVED` | A–F 均不成立；151→160→175 期间六项预冻结 health votes 中至少三项成立：(1) BC error 下降 `>=10%`；(2) temperature deficit 下降 `>=10%`；(3) W1 QJ q95 上升 `>=10%`；(4) positive-growth fraction 绝对上升 `>=0.05`；(5) phase q95 上升 `>=10%`；(6) phase-Jacobian q95 上升 `>=10%` 或始终 `>=0.01`；head updates 非零、无 C/D/E pathology，且 `early_activation_proxy=false` | 只产生 `BOUNDED_OPTIMIZATION_DIAGNOSTIC_PLAN_ONLY`；不得据此选择 R1、自动延长预算或继续训练 |
| H `R0B_INCONCLUSIVE_STOP` | ties、同时 onset、从初始化即混合失败、只在 175 新出现、证据通道相互矛盾，或不满足 A–G | `primary=null`；`next=FINAL_PURE_SCRATCH_DIAGNOSTIC_STOP`；绝不授权 R1 |

### 5.3 primary/secondary 机器选择

1. 对 A–E，`candidate_onset` 是 predicate 首次为真的冻结 observation，`confirmation` 是其后的下一个冻结 observation 仍为真；排序使用 candidate onset，confirmation 只决定其是否合格。首次在 175 出现者不合格。F 的 candidate/confirmation 固定为 151/160。
2. 在所有合格 A–F 中按 candidate onset 排序：唯一最早者成为 primary precursor candidate；两个类别同刻即转 H，不用人工优先级破同分。因而 A–E 在 150 onset 时严格早于 F，在 151 onset 时与 F 同刻转 H；F 没有特殊优先权。
3. secondary 只允许以下无环 relation，且 candidate onset 必须严格晚于 primary：`A→{B,C,E,D}`、`B→{C,E,D}`、`C→{E,D}`、`E→{D}`、`F→{C,E,D}`；D/G/H 没有 secondary。同刻不算“更晚”。符合 relation 的最早类别可作为唯一 secondary；其余只列 observations，不进入 hypotheses。
4. 若 A–F 均不合格，再判断 G；G 不得与另一 primary 并列，也没有 R1 映射。
5. 其余全部 H。机器输出必须是“一个 `primary_precursor_candidate` + 至多一个 `secondary_candidate`”或 `R0B_INCONCLUSIVE_STOP`；字段名与正文均不得宣称 `ROOT_CAUSE_IDENTIFIED`。

任何 nonfinite、identity drift、observer mutation、reference/stress reachability 或非预算原因导致 canonical steps/shadow calls 身份不符，均为 `R0B_INVALID_STOP`，不是科学根因，也不得重跑。预算类停止使用下文单独的 budget status，不与 invalid 混写。

## 6. MINIMAL PATCH FILE LIST

未来只有在单独授权的 implementation/execute 阶段才可修改：

| 文件 | 最小改动 |
|---|---|
| `configs/phk_v23/r0b_program_contract.json` | 单次授权、1 h/5 CNY、全局预算、reference/stress 与终局状态 |
| `configs/phk_v23/r0b_method_contract.json` | strong-raw identity、1000 denominator、175 canonical steps、9 noncanonical shadow updates、observation/pool/hash identity |
| `configs/phk_v23/r0b_diagnostic_contract.json` | schema、公共阈值、factorial cells/interactions、A–H 完整机器判据、输出字段 |
| `pinn_pcm_sci/phk_v22r_training.py` | 抽取 canonical/shadow 唯一共享的 single-step kernel，并增加默认关闭的 execution-control/observer seam；callback 只接收 read-only model view、不可变 batch/event context、effective weights、detached summaries，并仅在 transition event 接收 deep-copied state snapshot；不接收 live sampler/canonical optimizer；R0B checkpoint/manifest/timing 写真实 175 steps 与 `DIAGNOSTIC_PREFIX`，默认路径语义不变 |
| `pinn_pcm_sci/phk_v23_r0b.py` | 薄 runner、observer、八-cell + anchor 的 noncanonical shadow orchestrator、telemetry writer、local-only adjudicator；只调用共享 step kernel/PDE/sampler，不复制训练步或建立平行 trainer |
| `tests/test_phk_v23_r0b.py` | schedule、invariance、reference isolation、taxonomy、预算与一次性输出测试 |
| `tests/test_phk_v22r_pinn.py` | 仅增加 legacy observer-off exact regression，如新测试文件无法覆盖 |
| `cloud/phk_v23_r0b_autodl/README.md` | 唯一 V100 run/recovery card；不包含 reference |
| `docs/adr/0050-activate-phk-v23-r0b-first-switch-175.md` 及权威状态入口 | 只有未来明确 EXECUTE 后才激活；保留 R0A/V2.2R |
| `docs/experiment/...` | 未来 run manifest、machine artifact、closeout 与 ledger；不得预写结果 |

不得建立平行 trainer、平行 evaluator、第二套 live plan 或第二个权威状态文件。

## 7. FOCUSED TEST PLAN

未来 V100 运行前必须通过：

1. `config.updates=1000` 且 loop 恰好 175 steps；
2. step 150 仍为 W1-only，step 151 是首个 W1+W2 optimizer step；
3. step 151 由 active-window change 精确 refresh，observer 不触发额外 refresh；
4. 只在授权前的 tiny CPU fixture 上执行 observer off/on 等价测试，证明 scratch initialization、training Sobol、collocation、loss、gradients、optimizer state 与 final parameters exact equal；正式 V100 仍只允许运行 observer-on 一次；
5. observer 前后 Torch CPU 与当前 CUDA RNG exact equal；外层 run entry/exit 的 Torch CPU/CUDA、Python `random` 与 NumPy RNG state 分别 exact equal，包括异常路径；
6. trainer/model/loss/sampler/observer API 不接受 nominal/stress reference path、label 或 oracle；
7. stress opener 在任何文件 I/O 前 fail closed；
8. every observation 的 output/state/optimizer/coordinate hashes 完整；数值字段 finite，W2 零驱动字段必须是 `null:NOT_APPLICABLE_ZERO_DRIVE`，且不得参与投票；
9. fixed run/artifact 已存在或路径不匹配时，在 GPU/model I/O 前拒绝；
10. wall-time/cost projection 超上限时 fail closed，partial run 不进入 adjudication；
11. observer-disabled 路径与 V2.2R legacy golden semantics 无 drift；
12. A–H synthetic trajectories 覆盖每一分支、K=2、175-only refusal、tie→H、allowed primary→secondary DAG 与最多一个 secondary；另以 `theta_150` transition fixtures 证明 W2 exposure、W1 resample、boundary/IC resample 三者可排他，复合命中转 H；
13. final checkpoint 必须写 `update=175` 且 embedded config 仍为 `updates=1000`；manifest/ledger 必须写 `canonical_optimizer_steps=175`、`noncanonical_shadow_step_calls=9`、`total_step_kernel_calls=184`、`scientific_schedule_denominator=1000`、每类 elapsed/status、timing denominator `175`、terminal log step `175` 与 status `DIAGNOSTIC_PREFIX`，绝不得把 175 冒充总 kernel calls 或标为 nominal `COMPLETE`；
14. 八个 factorial cells 与 old-full-W1 anchor 从逐位相同的 `theta_150`/Adam snapshot 开始、绝不推进 canonical optimizer/RNG/sampler；all-on cell 的一步结果与 canonical step-151 update exact equal，anchor subset-bias、factorial main-effect/interaction、zero-norm null policy 与 dominance/overlap 门均由 synthetic fixtures 覆盖，任何 shadow checkpoint 写入均 fail closed。

当前 PLAN 不运行这些测试；它们是未来合同写入后的前门。

## 8. V100 RUN AND RECOVERY PLAN

未来授权后顺序固定为：

1. 核验实现 commit、三份 R0B contract hashes、live price、剩余全局预算与两份 stress seals；远端 run directory 与本地 canonical artifact 必须不存在。
2. 只上传 source-pinned code/config/test/run-card 白名单；nominal/stress reference、旧本地 evaluation 与 sealed paths 一律不上云。
3. 核验设备必须为 `Tesla V100-PCIE-32GB`、Python 3.11.9/PyTorch 2.5.1+cu118/CUDA 11.8，并显式 `OMP_NUM_THREADS=1`。
4. 在唯一 tmux session 中执行 focused preflight；确认无第二训练进程。
5. 启动一次 seed-17/FP64/STRONG_RAW scratch 175-canonical-step replay；transition 内另有 9 次 noncanonical clone step calls。cloud artifact 只含 reference-blind telemetry、shadow provenance/counters、final checkpoint、prediction、logs、environment、manifest 与 cost ledger。
6. 每个 observation 更新剩余时间/费用投影；超软门立即写 `R0B_BUDGET_STOP_INCOMPLETE`，不作科学 adjudication、不自动重跑。
7. 远端完成后计算白名单 SHA-256；下载到新的本地 staging directory，核对数量、字节、hash、run/contract/commit identity。
8. 回收验证完成后立即关闭实例，并验证 SSH refused；只有此后才能本地打开 nominal development reference。
9. 本地先在不打开任何 reference 的条件下，仅用 cloud telemetry 执行 A–H machine，并排他写入 immutable adjudication artifact。
10. A–H 已锁定后才可打开 frozen nominal development reference，写单独的 non-voting teacher/evaluation appendix；它不得改变 `primary_precursor_candidate` 或 R1 提案映射。随后写 exactly-one closeout：一个 primary precursor candidate + 至多一个 secondary candidate，或 `R0B_INCONCLUSIVE_STOP`；不自动启动 R1。

## 9. BUDGET PROJECTION METHOD

预估使用已版本化实测量，不把估计冒充账单：

```text
base_s_per_update = max(0.486627 nominal, 0.549665 profile)
base_training_s = 175 * base_s_per_update = 96.19 s
regular_observer_reserve_s = 3 * 12 * 9.321135 = 335.56086 s
transition_shadow_reserve_s = 9 * 9.321135 = 83.890215 s
prediction_reserve_s = 120 s  # conservative planning allowance, not a measured evidence claim
recovery_shutdown_reserve_s = 600 s
preflight_projected_total_s ≈ 1235.64 s ≈ 0.35 h
```

这里的 `9.321135 s` 来自上文所链 R0A closeout；ordinary observation 的乘数 `3` 是结果可见前采用的保守 planning safety factor，不是新测量，覆盖 separate-graph gradients、CUDA synchronization 与 telemetry I/O。九个 shadow calls 另各保留一整个 R0A wall time，不被 ordinary observation 均值吸收。`120 s` prediction reserve 同样是保守 allowance，不冒充历史实测。若未来 implementation preflight 的逐项投影更高，必须使用更高值或触发预算停止，不能缩减 reserve 以放行。

future projected cost 为 `live_displayed_price_cny_per_hour * projected_total_hours`。启动前必须同时满足 projected GPU time `<1 h`、projected cost `<5 CNY`、V2.3 累计投影不超过 `34 h/95 CNY`，且项目历史与新增云成本合计不接近 `150 CNY` 绝对上限。在 run 内按实测 update 与 observer elapsed 重算：

```text
remaining_shadow_reserve = 0                                      # shadows complete
  or max((9-completed_shadows) * 9.321135,
         (9-completed_shadows) * observed_s_per_shadow)           # before/during transition
projected_remaining = remaining_updates * observed_s_per_update
                    + remaining_observations * max(observed_s_per_observation,
                                                    3 * 9.321135)
                    + remaining_shadow_reserve
                    + remaining_prediction_reserve
                    + remaining_recovery_shutdown_reserve
```

在 step 151 前 `remaining_shadow_reserve` 必须始终至少为冻结的 `83.890215 s`；运行时低均值不得把尚未发生的 transition 成本冲掉。preflight 已超门写 `R0B_BUDGET_PREFLIGHT_BLOCKED` 且不启动；运行中软投影或实际硬门触发统一写 `R0B_BUDGET_STOP_INCOMPLETE`（reason=`SOFT_PROJECTED|HARD_ACTUAL`），立即回收/关机且不作 A–H adjudication。只有非预算完整性失败才用 `R0B_INVALID_STOP`。

45 分钟是 paid-work 软停止门，以保留 15 分钟回收/关机；60 分钟是实例硬停止门。旧 V2.2R 约 `4.8101 CNY` 仍单独报告，不改写为平台账单。

## 10. STOP CONDITIONS

以下任一项立即停止且不自动重跑：

- HEAD/contract/source/environment/GPU/hash drift；
- stress path 可达、nominal reference 出现在云端或任何训练/observer API；
- observer 改变 RNG、collocation、loss、gradient、optimizer、parameter、buffer 或 `.grad`；
- nonfinite、exception、duplicate process 或 duplicate artifact：`R0B_INVALID_STOP`；预算/时间投影或实际硬门超限：`R0B_BUDGET_STOP_INCOMPLETE`；
- 未完成恰好 175 steps，或 step-151 switch/refresh 身份不符；
- decision table tie、时间先行不足、只在 175 出现或 evidence conflict：`R0B_INCONCLUSIVE_STOP`；
- A–H 裁决完成后停止，不进入 R1；
- 全局 `34 GPU-hour / 95 CNY / 14-day` 任一达到或投影接近即停止新云运行。

R0B 不能修改 V2.2R No-Go、不能恢复 competence claim、不能证明新方法、不能访问 stress、不能以一次动态信号包装成论文结果。

## 11. REQUIRED FUTURE USER AUTHORIZATION STRING

只有在 R0B contracts、implementation、focused tests、cloud run card、document consistency 与 source commit 全部可审查后，用户发出以下精确字符串，才允许未来执行：

```text
EXECUTE PHK_V23_R0B_FIRST_SWITCH_175
```

该字符串仅授权上述单次 V100/FP64/seed-17/175-step reference-blind replay 与必要的产物回收、关机、本地 nominal adjudication；不授权 R1、PJGR、low-fidelity、stress、作者联系、投稿或第二次 run。

## 12. 本笔记的后续使用规则

本笔记是执行计划草案，不是科研结果。未来若用户接受，必须把接受内容版本化为新合同与 ADR，并在结果可见前冻结所有阈值、hash、预算和 decision rules；不得直接把本笔记当作 runnable authorization。目标会话中的 prior-art 判断在回到原始来源前只能作为待核验线索，不得据此宣称首创或完成 novelty clearance。
