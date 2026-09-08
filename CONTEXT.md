# PINN-PCM-SCI 当前研究设定与论文口径

- `document_role`: `CURRENT_RESEARCH_SETTING_AND_PAPER_LANGUAGE`
- `updated_at`: `2026-09-08`

## 当前研究问题

PHK-V2.2R 在 fixed-discretization nominal benchmark 上形成四臂 terminal No-Go；R0A/R0B/R0C 分别保留 inconclusive、temporal precursor 与 Adam-preconditioning 边界；R1a 表明 conflict-resolution-only 不足以恢复 competence。R1X E1/E2 两条 non-voting warm-up exploration 都未通过 W1/W3 readiness，并以冻结机器树的 `PURE_SCRATCH_COMPETENCE_RECOVERY_FAILED` 收口。

C0 已证明 nominal reference 自身通过 readiness 且 pool 未漏检；phase strict-interior native/strong-form 子门 compatible。E2 top hard lift 的内部下界存在表示包络混杂。LF0 随后用无该下界的 exact-top raw lift执行了 scratch A 与 medium-only warm-start B：A 无 competence；B0 未能忠实转移 medium 的事件并违反 potential validity，B final 虽恢复 potential validity仍无事件，故以 `LF0_NUMERICAL_OR_IDENTITY_INVALID` 收口且未运行条件 C。

LF1 使用 range-preserving exact-top 表示、event-balanced medium distillation 与固定 `0.1` persistent replay。B0 与 B final 均获得两周期 competence并通过 potential validity，证明稀疏事件可被转移且可在 physics refinement 中避免冷态坍塌；但 B final 相对 B0 与 direct `LF_ONLY` 的 phase noninferiority 和 temperature preservation 失败。固定 physics objective 的显著下降没有形成 accuracy-preserving Pareto 增量，故终局为 `LF1_DATA_ONLY_VALUE_NO_PINN_GAIN`，条件 C 未触发。

LF2 从精确 LF1-B0 权重出发，把 data-only objective 改为 evaluator-compatible target measure，并用 inequality augmented Lagrangian 约束事件 recall/active mass。唯一 M0 轨迹使 potential、temperature、phase 的 target-measure weighted error 相对 LF1-B0 分别降至约 `25.7%/6.55%/27.3%`，但 `phase_max` 同时回到约 `0.02995`，两个周期的 hard event support 全部消失。冻结 M0 gate 因此给出 `LF2_CALIBRATED_CARRIER_NOT_ESTABLISHED`，M1 未运行、candidate 为 none。这说明 sampling-measure mismatch 是 LF1 过宽 carrier 的因素，却不是建立准确稀有事件 carrier 的充分修复。

LF3 用 `Measure-Decoupled Phase-Latent Carrier` 执行了唯一 T0 轨迹：V/T 按 target measure 拟合，phase 按 14 个互斥事件类别等权拟合初值精确的完整 logit 增量。T0 恢复了合法、局域、时刻准确的双周期事件，precision 与 active-mass 门通过，但两周期 hard recall `0.805842/0.768603` 未达冻结 `0.90`，终局为 `LF3_CARRIER_NOT_ESTABLISHED`。P0 因此前提失败而未触发，故没有 PINN-specific pilot 或 candidate signal。

LF4 以三条 matched 400-step phase-only arms 检验 LF3 剩余误差是否来自界面暴露不足。DEV-G/M/C 的 `Rmin` 分别为 `0.819419/0.909256/0.941581`；DEV-M 相对等预算 DEV-G 提升 `0.089837` 且保持冻结质量条件，因此支持本 single-seed nominal 对象上的 `BOUNDARY_EXPOSURE_SUPPORTED`。DEV-C 虽再提升 `0.032325` 并修复 timing，却把 phase weighted MSE 提高到 `0.0296673` 并降低 cycle-2 recovery，故不支持 threshold-aligned BCE 的完整 load-bearing claim。三臂分别因 timing、timing、phase error 未通过完整 P0-entry，selected carrier 为 none，P0 未运行，终局为 `LF4_NO_DEVELOPMENT_ENTRY`。

LF5 的 CPU-T 重建 `68/68/64/64` 条合法 temporal edges，却发现 DEV-C 在两个 onset pool 的 teacher-secanted zero-level residual 都劣于 DEV-M，故冻结前提门返回 `LF5_TZL_ALIGNMENT_NOT_SUPPORTED_CPU`。用户知晓结果后只授权不变的 DEV-T 作 post-qualification exploratory evidence。该轨迹完成 400 updates，base/spatial stream 匹配，但 temporal stream 从 step 1 偏离冻结身份，未写出 checkpoint/prediction；P0 未运行。终局为 `LF5_NUMERICAL_OR_IDENTITY_INVALID`。step-400 recall `0.9175/0.9174` 与 cycle-1 timing error `0.0094` 只能作非投票方向性观察。

LF6 用同起点、同预算的 DEV-U/DEV-R 隔离 generic endpoint 与 teacher-side event-frontier rank-band。DEV-R 通过 safety，DEV-U/DEV-R 均未通过 strict，故机制结论为 `NO_RANK_SPECIFIC_INCREMENT`。冻结 safety carrier 是指达到进入物理 continuation 的最低有效门，不等于方法优胜或 candidate。DEV-R 进入 1200-step label-free P0 后，fixed-blind physics objective ratio 降至 `0.0128142265`，但 V/T/phase/topology preservation ratios 恶化至 `28.62/52.60/25.84/20.03`，两周期 recall 最终均为零。这里的 physics preservation failure 指物理目标下降与已建立事件/场载体同时崩解；它是有效的 bounded negative PINN-refinement evidence，不是数值无效。

LF7 从 exact DEV-R 运行 matched 小步长与 competence-filtered physics refinement。P0-S 完成 1,200 updates，fixed-blind ratio 为 `0.6030763369`，但事件和场 competence 仍坍塌，形成有效的小步长负面 arm。P0-F 尝试 150、接受 25 updates 后出现 post-step rollback identity drift，无合法 endpoint；事后定位为非空 Adam snapshot tensor aliasing。修复未用于科学重跑。终局为 `LF7_MATCHED_SCREEN_INCOMPLETE_IDENTITY_INVALID`：保留 P0-S 结果，但不能归因 filter 机制增量、PINN Pareto 或 candidate。

## 物理对象与证据边界

对象仍是 PHK-V2.1 的透明、无量纲、literature-inspired synthetic 2D wall-cell；几何、PDE、本构、参数、IC/BC、ROI、事件与 frozen evaluator 均不改变。extra-fine fixed-discretization carrier 不是 continuum truth；C0 saved-cadence strong residual 也不是 exact internal-step residual。

两份 stress references 始终 sealed/unread。LF0/LF1/LF2/LF3 云端只读取了获准的 medium low-fidelity method input；LF2/LF3 另读取精确 LF1-B0 model checkpoint，LF4/LF5/LF6 读取 medium 与 exact LF3-T0 checkpoint，LF6 还按合同只读 exact DEV-M fallback 与预物化 streams。LF7 云端只读取 medium audit、exact DEV-R、预物化 physics ledger 与 CPU qualification。fine/extra-fine、direct `LF_ONLY` 和 frozen evaluator 只在 LF7 关机后本地读取；raw 产物已回收并按哈希核验。

## 方法与论文身份

**Competence-filtered safety path**: a sequence of accepted strong-form physics
blocks that strictly reduces the blind objective while retaining the frozen
event-and-field safety conjunction. A stopped valid prefix is evidence about
path feasibility, not a completed PINN Pareto result.

**Accepted-schedule control**: a fresh exact-DEV-R trajectory that replays the
learning-rate schedule accepted by a complete safety path but performs no
competence audit, rejection or rollback. It isolates schedule sufficiency from
the load-bearing effect of filtering.

ConFIG、staggered blocks、coupling homotopy、exact-top lift、medium warm-start、event-balanced distillation、persistent replay、target-measure calibration、普通 augmented Lagrangian、inverse-link distillation、类别重平衡、interface sampling、BCE-with-logits、event-frontier rank-band 与 competence-filter/backtracking 都是 `SHARED_SOLVER_BACKBONE_NOT_AUTOMATIC_HEADLINE_INNOVATION`。LF1 建立过 single-seed nominal competence但没有强基线增量；LF2 证明全局测度误差改善不能替代稀有事件 competence；LF3 把失败收缩为 high-precision/low-recall support；LF4 验证界面暴露可提高最低召回；LF6/LF7 证明 bulk residual 下降和更小步长均未保存事件载体。LF8 证明 identity-correct filter 可保留一个 25-step local feasible prefix，但无法在最小冻结学习率接受第二个 block；因此 tested long-path strong-form continuation 已关闭，而 filter-versus-schedule attribution 仍未知。direct medium `LF_ONLY` 与 B0 `LF_DATA_ONLY` 仍是强 comparators。当前稿件只能承载有界 failure-analysis、solver-recovery mechanism evidence、physics-forgetting 与 valid-prefix stall 负结果。

## 权威路由

LF8 terminal evidence and its boundary are defined by [ADR 0070](docs/adr/0070-close-phk-v23-lf8-competence-filter-completion.md), [terminal closeout](docs/experiment/2026-09-08-phk-v23-lf8-terminal-closeout.md), [active phase](active_phase.md), [project state](PROJECT_STATE.md) and the [live plan](docs/plans/NEXT_ACTIONS.md). The mixed weak/control-volume route is a recommendation requiring `NEW EXECUTE`; it is not current authorization and does not rewrite LF7 or earlier evidence.

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
