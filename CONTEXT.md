# PINN-PCM-SCI 当前研究设定与论文口径

- `document_role`: `CURRENT_RESEARCH_SETTING_AND_PAPER_LANGUAGE`
- `updated_at`: `2026-09-05`

## 当前研究问题

PHK-V2.2R 在 fixed-discretization nominal benchmark 上形成四臂 terminal No-Go；R0A/R0B/R0C 分别保留 inconclusive、temporal precursor 与 Adam-preconditioning 边界；R1a 表明 conflict-resolution-only 不足以恢复 competence。R1X E1/E2 两条 non-voting warm-up exploration 都未通过 W1/W3 readiness，并以冻结机器树的 `PURE_SCRATCH_COMPETENCE_RECOVERY_FAILED` 收口。

C0 已证明 nominal reference 自身通过 readiness 且 pool 未漏检；phase strict-interior native/strong-form 子门 compatible。E2 top hard lift 的内部下界存在表示包络混杂。LF0 随后用无该下界的 exact-top raw lift执行了 scratch A 与 medium-only warm-start B：A 无 competence；B0 未能忠实转移 medium 的事件并违反 potential validity，B final 虽恢复 potential validity仍无事件，故以 `LF0_NUMERICAL_OR_IDENTITY_INVALID` 收口且未运行条件 C。

LF1 使用 range-preserving exact-top 表示、event-balanced medium distillation 与固定 `0.1` persistent replay。B0 与 B final 均获得两周期 competence并通过 potential validity，证明稀疏事件可被转移且可在 physics refinement 中避免冷态坍塌；但 B final 相对 B0 与 direct `LF_ONLY` 的 phase noninferiority 和 temperature preservation 失败。固定 physics objective 的显著下降没有形成 accuracy-preserving Pareto 增量，故终局为 `LF1_DATA_ONLY_VALUE_NO_PINN_GAIN`，条件 C 未触发。

LF2 从精确 LF1-B0 权重出发，把 data-only objective 改为 evaluator-compatible target measure，并用 inequality augmented Lagrangian 约束事件 recall/active mass。唯一 M0 轨迹使 potential、temperature、phase 的 target-measure weighted error 相对 LF1-B0 分别降至约 `25.7%/6.55%/27.3%`，但 `phase_max` 同时回到约 `0.02995`，两个周期的 hard event support 全部消失。冻结 M0 gate 因此给出 `LF2_CALIBRATED_CARRIER_NOT_ESTABLISHED`，M1 未运行、candidate 为 none。这说明 sampling-measure mismatch 是 LF1 过宽 carrier 的因素，却不是建立准确稀有事件 carrier 的充分修复。

LF3 用 `Measure-Decoupled Phase-Latent Carrier` 执行了唯一 T0 轨迹：V/T 按 target measure 拟合，phase 按 14 个互斥事件类别等权拟合初值精确的完整 logit 增量。T0 恢复了合法、局域、时刻准确的双周期事件，precision 与 active-mass 门通过，但两周期 hard recall `0.805842/0.768603` 未达冻结 `0.90`，终局为 `LF3_CARRIER_NOT_ESTABLISHED`。P0 因此前提失败而未触发，故没有 PINN-specific pilot 或 candidate signal。

LF4 以三条 matched 400-step phase-only arms 检验 LF3 剩余误差是否来自界面暴露不足。DEV-G/M/C 的 `Rmin` 分别为 `0.819419/0.909256/0.941581`；DEV-M 相对等预算 DEV-G 提升 `0.089837` 且保持冻结质量条件，因此支持本 single-seed nominal 对象上的 `BOUNDARY_EXPOSURE_SUPPORTED`。DEV-C 虽再提升 `0.032325` 并修复 timing，却把 phase weighted MSE 提高到 `0.0296673` 并降低 cycle-2 recovery，故不支持 threshold-aligned BCE 的完整 load-bearing claim。三臂分别因 timing、timing、phase error 未通过完整 P0-entry，selected carrier 为 none，P0 未运行，终局为 `LF4_NO_DEVELOPMENT_ENTRY`。

## 物理对象与证据边界

对象仍是 PHK-V2.1 的透明、无量纲、literature-inspired synthetic 2D wall-cell；几何、PDE、本构、参数、IC/BC、ROI、事件与 frozen evaluator 均不改变。extra-fine fixed-discretization carrier 不是 continuum truth；C0 saved-cadence strong residual 也不是 exact internal-step residual。

两份 stress references 始终 sealed/unread。LF0/LF1/LF2/LF3 云端只读取了获准的 medium low-fidelity method input；LF2/LF3 另读取精确 LF1-B0 model checkpoint，LF4 读取 medium 与 exact LF3-T0 checkpoint。fine/extra-fine 与 direct `LF_ONLY` 仅用于全部产物回收、哈希核验且实例关机验证后的本地 development evaluation。LF4 三条 development 轨迹已回收、核验并关机，P0 未运行。

## 方法与论文身份

ConFIG、staggered blocks、coupling homotopy、exact-top lift、medium warm-start、event-balanced distillation、persistent replay、target-measure calibration、普通 augmented Lagrangian、inverse-link distillation、类别重平衡、interface sampling 与 BCE-with-logits 都是 `SHARED_SOLVER_BACKBONE_NOT_AUTOMATIC_HEADLINE_INNOVATION`。LF1 建立过 single-seed nominal competence但没有强基线增量；LF2 证明全局测度误差改善不能替代稀有事件 competence；LF3 把失败收缩为高 precision 但 support recall 不足；LF4 又以 matched control 验证界面暴露可提高最低召回，但没有建立完整 entry 或 PINN 结果。direct medium `LF_ONLY` 与 B0 `LF_DATA_ONLY` 仍是必须保留的强 non-PINN comparators。当前稿件只能承载有界 failure-analysis 与 solver-recovery mechanism evidence；任何正面路线仍须面对强基线、关键单因素消融、多 seed、sealed stress/formal OOD 与单一 load-bearing core。

## 权威路由

当前完成态与无后续授权边界见 [active phase](active_phase.md)，事实见 [project state](PROJECT_STATE.md)，终局动作见 [live plan](docs/plans/NEXT_ACTIONS.md)，LF4 证据见 [terminal closeout](docs/experiment/2026-09-05-phk-v23-lf4-terminal-closeout.md) 与 [ADR 0062](docs/adr/0062-close-phk-v23-lf4-interface-band-pilot.md)，导师初稿见 [paper_v23](paper/paper_v23/README.md)。LF3/LF2/LF1/LF0/C0 历史入口继续由对应 terminal closeout 保留。
