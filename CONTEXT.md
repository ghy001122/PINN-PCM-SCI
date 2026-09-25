2026-09-25 当前补充：[物理目标、采样与固定温度定向诊断](paper/observation_preserving_phase_20260924/physics-objective-diagnostic.md)已完成，结果回收且GPU已关闭。当前授权状态见 active_phase.md；下文观测补全训练与发布按各自历史时点读取。

# PINN-PCM-SCI 当前研究设定与论文口径

2026-09-25 用户另行明确授权将本轮重要结果与研究进程提交云端；精简发布范围和核验状态见[发布记录](docs/notes/2026-09-25-observation-preserving-phase-results-release.md)。本次仅更新交付状态，科研仍为 CLOSED，完整数组外部访问仍未闭合。该授权 supersedes 本任务此前 Git 未授权措辞。

## 当前研究问题（2026-09-25收口）

**VERIFIED：NO_COMPLETION_INCREMENT。** 冻结E29的观测保持相态补全三臂均未通过原A_w/独立物理资格。N的集合误差降低34.209%，连续相态RMS增加7.946%；D内raw相态平方为基点10.287倍。N/S保持观测预测、T/端口及加热事件，不能据此补齐原严格失败。一个基点、原参考、共同160×80读出，不是formal OOD或材料验证。见[完整结果](paper/observation_preserving_phase_20260924/results.md)。

**SUPPORTED_INTERPRETATION：**观测等价构造成立不等于合格物理/状态补全。当前配方及预算已收口，阶段4不触发；旧全标签配置收益与时间矩阴性均保留。实际CPU训练/GPU审计读出、内存恢复及关机证据已透明记录。P02/P03仍开放，没有新科研授权。以下均为历史口径。

## 历史研究问题（2026-09-23收口）

**VERIFIED：**相对相态残差／时间矩八臂开发按NO_INCREMENT_WITHIN_SCREEN_BUDGET收口。RIM有小幅连续改善，但未对D/P通过原A_w；相对简单L、RI、G的变化不足以建立组合或一阶矩必要性。八个严格双周期均未通过；数值求积检查通过，GPU已关闭。见[完整结果](paper/phase_moments_20260923/results.md)。本轮仅一个初始化、离线相态缺测重建，不是forecasting、formal OOD或材料验证。

**SUPPORTED_INTERPRETATION：**当前固定校准与短片目标未补齐论文的独立相态PDE贡献；不自动改写为D_E窄稿。初始loss尺度和时间矩接近是诊断线索，不是已证明的唯一根因。旧完整标签E/F配置收益、B1 0/12、B_E反例、六臂负续训及材料边界仍保留原身份。后续不同假设需另行规划授权，当前不追加训练或确认。下文仅为历史口径。

## 历史：同父三臂与条件归一化已完成

VERIFIED：D_I/D_B/P_U 与 R/G/N 六个合法固定终点，新增 6500 Adam updates、1500 次完整评估；五个匹配差分的 A/B 均未通过，D_N 未触发。当前入口为 [paper_v27](paper/paper_v27/README.md)、[终局](docs/experiment/2026-09-12-phk-v23-lf11-joint-terminal-closeout.md)和 [active_phase.md](active_phase.md)。CPU 训练已结束；用户后续授权本轮发布及独立复评，未授权新科研执行。旧门、旧分支和以下旧阶段口径均按各自日期保留。


## 历史：paper_v25 LF11后续拟合修复

VERIFIED：温度包络下界0.1504%；可见T误差17.8233%→1.1375%，三个T拟合门均过，phase不变。可见V误差0.8215%未达0.5%，是唯一未满足的拟合条件。完整nominal参考ROI T误差28.2210%→1.7475%，能量误差106.7402%→49.2006%。
新物理对照未运行；温度修复未建立适配器独立归因。底部V是下一优先定位对象，所有新执行仍未授权。[paper_v25](paper/paper_v25/README.md)与[终局](docs/experiment/2026-09-12-phk-v23-lf11-followup-terminal-closeout.md)保留该轮证据；这些当时的未运行状态和优先建议不描述最新轮次。


- `document_role`: `CURRENT_RESEARCH_SETTING_AND_PAPER_LANGUAGE`
- `updated_at`: `2026-09-12`

## 历史研究问题（2026-09-12）

SUPPORTED_INTERPRETATION：汇总 BC、连续 AD 残差、事件及双端器件读出不能互相替代。本轮已用嵌套目标和 R/G/N 排除所测试归一化作为充分修复；局部相态优势仍未转化为器件优势。HYPOTHESIS：下一步电学子问题消元与同信息 D_E/P_E/B_E 对照，见[唯一下一计划](docs/plans/NEXT_ACTIONS.md)。尚无竞争性 PINN 方法优势、独立确认、formal OOD 或材料标定。

## 历史研究链（按原阶段口径保留）

**原 LF11 四臂结论（VERIFIED）：** 稀疏等观测四臂已完整执行，共同起点与四臂共6000 updates。D_B→P_U独立物理目标下降80.37%，S/Ephi却恶化40.68%/17.74%；同目标界面重要性采样改善4.49%/4.22%，相态测度更改仅再改善0.0763%/0.00981%，均无预声明匹配增量。零训练后验波形感知插值使电流NRMSE从103.08%降至0.428%，相态和温度完全不变；它不替换原正式裁决。

**SUPPORTED_INTERPRETATION：** 真实Adam局部方向优先指向electric/BC对phase的作用，没有发现破坏性phase residual→T，latent条件未触发。下一步电边界相容表示及electric→phase归因仅为PROPOSED_NOT_AUTHORIZED。[paper_v24](paper/paper_v24/README.md)承载本轮完整结果；下列旧阶段事实及paper_v23均保留。

PHK-V2.2R 在 fixed-discretization nominal benchmark 上形成四臂 terminal No-Go；R0A/R0B/R0C 分别保留 inconclusive、temporal precursor 与 Adam-preconditioning 边界；R1a 表明 conflict-resolution-only 不足以恢复 competence。R1X E1/E2 两条 non-voting warm-up exploration 都未通过 W1/W3 readiness，并以冻结机器树的 `PURE_SCRATCH_COMPETENCE_RECOVERY_FAILED` 收口。

C0 已证明 nominal reference 自身通过 readiness 且 pool 未漏检；phase strict-interior native/strong-form 子门 compatible。E2 top hard lift 的内部下界存在表示包络混杂。LF0 随后用无该下界的 exact-top raw lift执行了 scratch A 与 medium-only warm-start B：A 无 competence；B0 未能忠实转移 medium 的事件并违反 potential validity，B final 虽恢复 potential validity仍无事件，故以 `LF0_NUMERICAL_OR_IDENTITY_INVALID` 收口且未运行条件 C。

LF1 使用 range-preserving exact-top 表示、event-balanced medium distillation 与固定 `0.1` persistent replay。B0 与 B final 均获得两周期 competence并通过 potential validity，证明稀疏事件可被转移且可在 physics refinement 中避免冷态坍塌；但 B final 相对 B0 与 direct `LF_ONLY` 的 phase noninferiority 和 temperature preservation 失败。固定 physics objective 的显著下降没有形成 accuracy-preserving Pareto 增量，故终局为 `LF1_DATA_ONLY_VALUE_NO_PINN_GAIN`，条件 C 未触发。

LF2 从精确 LF1-B0 权重出发，把 data-only objective 改为 evaluator-compatible target measure，并用 inequality augmented Lagrangian 约束事件 recall/active mass。唯一 M0 轨迹使 potential、temperature、phase 的 target-measure weighted error 相对 LF1-B0 分别降至约 `25.7%/6.55%/27.3%`，但 `phase_max` 同时回到约 `0.02995`，两个周期的 hard event support 全部消失。冻结 M0 gate 因此给出 `LF2_CALIBRATED_CARRIER_NOT_ESTABLISHED`，M1 未运行、candidate 为 none。这说明 sampling-measure mismatch 是 LF1 过宽 carrier 的因素，却不是建立准确稀有事件 carrier 的充分修复。

LF3 用 `Measure-Decoupled Phase-Latent Carrier` 执行了唯一 T0 轨迹：V/T 按 target measure 拟合，phase 按 14 个互斥事件类别等权拟合初值精确的完整 logit 增量。T0 恢复了合法、局域、时刻准确的双周期事件，precision 与 active-mass 门通过，但两周期 hard recall `0.805842/0.768603` 未达冻结 `0.90`，终局为 `LF3_CARRIER_NOT_ESTABLISHED`。P0 因此前提失败而未触发，故没有 PINN-specific pilot 或 candidate signal。

LF4 以三条 matched 400-step phase-only arms 检验 LF3 剩余误差是否来自界面暴露不足。DEV-G/M/C 的 `Rmin` 分别为 `0.819419/0.909256/0.941581`；DEV-M 相对等预算 DEV-G 提升 `0.089837` 且保持冻结质量条件，因此支持本 single-seed nominal 对象上的 `BOUNDARY_EXPOSURE_SUPPORTED`。DEV-C 虽再提升 `0.032325` 并修复 timing，却把 phase weighted MSE 提高到 `0.0296673` 并降低 cycle-2 recovery，故不支持 threshold-aligned BCE 的完整 load-bearing claim。三臂分别因 timing、timing、phase error 未通过完整 P0-entry，selected carrier 为 none，P0 未运行，终局为 `LF4_NO_DEVELOPMENT_ENTRY`。

LF5 的 CPU-T 重建 `68/68/64/64` 条合法 temporal edges，却发现 DEV-C 在两个 onset pool 的 teacher-secanted zero-level residual 都劣于 DEV-M，故冻结前提门返回 `LF5_TZL_ALIGNMENT_NOT_SUPPORTED_CPU`。用户知晓结果后只授权不变的 DEV-T 作 post-qualification exploratory evidence。该轨迹完成 400 updates，base/spatial stream 匹配，但 temporal stream 从 step 1 偏离冻结身份，未写出 checkpoint/prediction；P0 未运行。终局为 `LF5_NUMERICAL_OR_IDENTITY_INVALID`。step-400 recall `0.9175/0.9174` 与 cycle-1 timing error `0.0094` 只能作非投票方向性观察。

LF6 用同起点、同预算的 DEV-U/DEV-R 隔离 generic endpoint 与 teacher-side event-frontier rank-band。DEV-R 通过 safety，DEV-U/DEV-R 均未通过 strict，故机制结论为 `NO_RANK_SPECIFIC_INCREMENT`。冻结 safety carrier 是指达到进入物理 continuation 的最低有效门，不等于方法优胜或 candidate。DEV-R 进入 1200-step label-free P0 后，fixed-blind physics objective ratio 降至 `0.0128142265`，但 V/T/phase/topology preservation ratios 恶化至 `28.62/52.60/25.84/20.03`，两周期 recall 最终均为零。这里的 physics preservation failure 指物理目标下降与已建立事件/场载体同时崩解；它是有效的 bounded negative PINN-refinement evidence，不是数值无效。

LF7 从 exact DEV-R 运行 matched 小步长与 competence-filtered physics refinement。P0-S 完成 1,200 updates，fixed-blind ratio 为 `0.6030763369`，但事件和场 competence 仍坍塌，形成有效的小步长负面 arm。P0-F 尝试 150、接受 25 updates 后出现 post-step rollback identity drift，无合法 endpoint；事后定位为非空 Adam snapshot tensor aliasing。修复未用于科学重跑。终局为 `LF7_MATCHED_SCREEN_INCOMPLETE_IDENTITY_INVALID`：保留 P0-S 结果，但不能归因 filter 机制增量、PINN Pareto 或 candidate。

LF8/LF9 在修复 rollback 身份后分别测试 strong-form filter completion 与 equation-routed strong/thermal-CV。它们均只保留一个 25-update 局部安全前缀，未完成冻结 200-update screen，故没有完整 PINN Pareto 或 filter/schedule 归因。

LF10 以同批次 exact DEV-R 审计基线匹配 CTRL 与 event-competence PROJ。两臂各保留一个有效 25-update safety prefix，但均未完成 200 accepted updates；投影未延长安全路径，full/control 未触发。独立的 streams 17/23/29 复现建立 `INTERFACE_EFFECT_STREAM_REPLICATED` 与 `PHYSICS_FORGETTING_STREAM_REPLICATED`；direct `LF_ONLY` 仅在 mean-symmetric-difference predicate 上领先全部 375 个可用 role-grid comparisons。终局为 `LF10_FEASIBLE_DIRECTION_SCREEN_NEGATIVE_PAPER_STRENGTHENED`，无 candidate。

## 物理对象与证据边界

LF11训练只读取新导出的稀疏V/T/phase和已知物理，由新初始化构造共同起点，不读取旧模型权重或dense事件池。全部端点回收且实际实例关闭后才本地读取高保真nominal。后验波形与方向诊断属于nominal开发/归因，没有独立初始化、实体级留出或formal OOD。

对象仍是 PHK-V2.1 的透明、无量纲、literature-inspired synthetic 2D wall-cell；几何、PDE、本构、参数、IC/BC、ROI、事件与 frozen evaluator 均不改变。extra-fine fixed-discretization carrier 不是 continuum truth；C0 saved-cadence strong residual 也不是 exact internal-step residual。

两份 stress references 始终 sealed/unread。LF0/LF1/LF2/LF3 云端只读取了获准的 medium low-fidelity method input；LF2/LF3 另读取精确 LF1-B0 model checkpoint，LF4/LF5/LF6 读取 medium 与 exact LF3-T0 checkpoint，LF6 还按合同只读 exact DEV-M fallback 与预物化 streams。LF7/LF8 云端只读取 medium audit、exact DEV-R、预物化 physics ledger 与 CPU qualification。LF9 另读取预物化 thermal-CV ledger；LF10 另读取预物化 audit/interface/forgetting streams。两阶段均未在云端读取 fine/extra/direct `LF_ONLY`/frozen evaluator/stress，且本地 nominal evaluation 仅在产物回收、哈希核验和关机后执行。

## 方法与论文身份

**Competence-filtered safety path**: a sequence of accepted strong-form physics
blocks that strictly reduces the blind objective while retaining the frozen
event-and-field safety conjunction. A stopped valid prefix is evidence about
path feasibility, not a completed PINN Pareto result.

**Accepted-schedule control**: a fresh exact-DEV-R trajectory that replays the
learning-rate schedule accepted by a complete safety path but performs no
competence audit, rejection or rollback. It isolates schedule sufficiency from
the load-bearing effect of filtering.

**Equation-routed multiphysics refinement**: a coupled PINN refinement in which
every equation retains full coupled values and coordinate derivatives, while
parameter gradients are assigned only to the head that owns that equation.
_Avoid_: detached coupling, sequential field update

**Thermal control-volume residual**: the normalized space-time integral of the
unchanged thermal equation over a finite-volume cell and adjacent saved-time
interval. _Avoid_: replacement thermal physics, label-derived balance

**Event-competence feasible-direction projection**: a per-head nearest-feasible
projection of the unchanged Adam physics proposal onto linearized field/event
audit constraints normalized by exact DEV-R on the identical materialized
batch. _Avoid_: adding medium data to the physics loss, replay training

**PRELOCAL_INTERNAL_PARETO**: a reference-blind cloud trigger satisfying every
available internal gate before shutdown. It is not a complete Pareto claim.

**COMPLETE_INTERNAL_PINN_PARETO**: an internal PINN result that also passes the
post-shutdown frozen local evaluator. It remains distinct from direct-baseline
paper value.

ConFIG、staggered blocks、coupling homotopy、exact-top lift、medium warm-start、event-balanced distillation、persistent replay、target-measure calibration、普通 augmented Lagrangian、inverse-link distillation、类别重平衡、interface sampling、BCE-with-logits、event-frontier rank-band 与 competence-filter/backtracking 都是 `SHARED_SOLVER_BACKBONE_NOT_AUTOMATIC_HEADLINE_INNOVATION`。LF1 建立过 single-seed nominal competence但没有强基线增量；LF2 证明全局测度误差改善不能替代稀有事件 competence；LF3 把失败收缩为 high-precision/low-recall support；LF4 验证界面暴露可提高最低召回；LF6/LF7 证明 bulk residual 下降和更小步长均未保存事件载体。LF8 证明 identity-correct filter 可保留一个 25-step local feasible prefix。LF9 进一步证明 equation routing 与 thermal-CV replacement 各自也只能保留近似相同的 25-step prefix，均无法完成冻结 200-update screen；因此 tested strong/thermal-CV rescue family 已关闭，而 full-path filter-versus-schedule attribution仍未知。direct medium `LF_ONLY` 与 B0 `LF_DATA_ONLY` 仍是强 comparators。当前稿件只能承载有界 failure-analysis、solver-recovery mechanism evidence、physics-forgetting 与 valid-prefix stall 负结果。

## 权威路由

LF11 is complete under its [terminal closeout](docs/experiment/2026-09-11-phk-v23-lf11-terminal-closeout.md), [active phase](active_phase.md), [project state](PROJECT_STATE.md), and the [live plan](docs/plans/NEXT_ACTIONS.md). No further research execution is authorized. [LF10](docs/experiment/2026-09-09-phk-v23-lf10-terminal-closeout.md) and earlier terminal evidence remain unchanged.

# LF9 terminal context (2026-09-09)

LF9 compared equation-routed strong and thermal control-volume refinement from
exact DEV-R. Both identity-valid screens accepted one 25-update block at the
minimum frozen learning rate and stalled on the next block because temperature
preservation failed. Neither completed the frozen 200-update screen, so the
filtered full path and schedule control were not run. Their near-identical blind,
field and event endpoints provide no evidence that the thermal-CV replacement
opens a longer safe path. The terminal outcome is
`LF9_NO_SAFE_MIXED_FORM_SCREEN`; no complete PINN Pareto, direct-baseline gain,
candidate or further rescue authorization exists.

LF7 终局证据见 [ADR 0068](docs/adr/0068-close-phk-v23-lf7-competence-filtered-refinement.md) 与 [terminal closeout](docs/experiment/2026-09-07-phk-v23-lf7-terminal-closeout.md)。导师初稿见 [paper_v23](paper/paper_v23/README.md)。LF7 及更早证据继续由对应 terminal closeout 保留，不被 LF8 激活追溯修改。

# LF5 terminal context (2026-09-06)

LF5 tested whether LF4 DEV-C's aggregate timing improvement also improved a
teacher-anchored per-cell saved-cadence zero-level residual. CPU-T found the
opposite in both onset cycles, while geometry, identity, sign, and gradient
checks passed. On 2026-09-06 the user explicitly authorized the otherwise
unchanged DEV-T as post-qualification exploratory evidence. DEV-T completed
400 updates but its temporal stream drifted from the frozen identity at step 1;
the terminal gate raised before checkpoint writing and P0 was not run. This
does not rehabilitate or rewrite the CPU premise, and no retry is authorized.

# LF6 terminal context (2026-09-07)

LF6 compared teacher-side event-frontier rank-band cells against a
same-cardinality generic endpoint control. DEV-R passed safety and was selected,
but both matched arms failed strict, so the narrow result is
`NO_RANK_SPECIFIC_INCREMENT`. The selected endpoint then completed a separate
label-free physics continuation. During the phase-frozen block V/T drifted;
after joint unfreezing event support collapsed. The fixed-blind physics
objective nevertheless fell to `0.0128142265` of entry, demonstrating that bulk
physics reduction did not preserve this event-bearing multiphysics carrier.
The terminal status is `LF6_P0_PRESERVATION_FAILED`, with no PINN Pareto,
direct-LF_ONLY gain, candidate, or next research authorization.

# LF7 terminal context (2026-09-08)

LF7 attempted the preregistered matched P0-S/P0-F screen from exact DEV-R.
P0-S completed 1,200 updates and is a valid negative arm: the fixed-blind
objective fell to `0.6030763369` of entry while event and field competence
collapsed. P0-F accepted one 25-update block, then failed a post-step rollback
identity check after 150 attempted updates; it has no valid endpoint and was not
retried. The terminal-tree snapshot fix was not scientifically executed. The
outcome is `LF7_MATCHED_SCREEN_INCOMPLETE_IDENTITY_INVALID`, with no mechanism
attribution, PINN Pareto, candidate or next authorization. Stress remains sealed.
