# PINN-PCM-SCI 当前研究设定与论文口径

- `document_role`: `CURRENT_RESEARCH_SETTING_AND_PAPER_LANGUAGE`
- `updated_at`: `2026-09-04`

## 当前研究问题

PHK-V2.2R 在 fixed-discretization nominal benchmark 上形成四臂 terminal No-Go；R0A/R0B/R0C 分别保留 inconclusive、temporal precursor 与 Adam-preconditioning 边界；R1a 表明 conflict-resolution-only 不足以恢复 competence。R1X E1/E2 两条 non-voting warm-up exploration 都未通过 W1/W3 readiness，并以冻结机器树的 `PURE_SCRATCH_COMPETENCE_RECOVERY_FAILED` 收口。

C0 已证明 nominal reference 自身通过 readiness 且 pool 未漏检；phase strict-interior native/strong-form 子门 compatible。E2 top hard lift 的内部下界存在表示包络混杂。LF0 随后用无该下界的 exact-top raw lift执行了 scratch A 与 medium-only warm-start B：A 无 competence；B0 未能忠实转移 medium 的事件并违反 potential validity，B final 虽恢复 potential validity仍无事件，故以 `LF0_NUMERICAL_OR_IDENTITY_INVALID` 收口且未运行条件 C。

LF1 使用 range-preserving exact-top 表示、event-balanced medium distillation 与固定 `0.1` persistent replay。B0 与 B final 均获得两周期 competence并通过 potential validity，证明稀疏事件可被转移且可在 physics refinement 中避免冷态坍塌；但 B final 相对 B0 与 direct `LF_ONLY` 的 phase noninferiority 和 temperature preservation 失败。固定 physics objective 的显著下降没有形成 accuracy-preserving Pareto 增量，故终局为 `LF1_DATA_ONLY_VALUE_NO_PINN_GAIN`，条件 C 未触发。

LF2 从精确 LF1-B0 权重出发，把 data-only objective 改为 evaluator-compatible target measure，并用 inequality augmented Lagrangian 约束事件 recall/active mass。唯一 M0 轨迹使 potential、temperature、phase 的 target-measure weighted error 相对 LF1-B0 分别降至约 `25.7%/6.55%/27.3%`，但 `phase_max` 同时回到约 `0.02995`，两个周期的 hard event support 全部消失。冻结 M0 gate 因此给出 `LF2_CALIBRATED_CARRIER_NOT_ESTABLISHED`，M1 未运行、candidate 为 none。这说明 sampling-measure mismatch 是 LF1 过宽 carrier 的因素，却不是建立准确稀有事件 carrier 的充分修复。

## 物理对象与证据边界

对象仍是 PHK-V2.1 的透明、无量纲、literature-inspired synthetic 2D wall-cell；几何、PDE、本构、参数、IC/BC、ROI、事件与 frozen evaluator 均不改变。extra-fine fixed-discretization carrier 不是 continuum truth；C0 saved-cadence strong residual 也不是 exact internal-step residual。

两份 stress references 始终 sealed/unread。LF0/LF1/LF2 云端只读取了 medium low-fidelity method input；LF2 另读取精确 LF1-B0 model checkpoint。fine/extra-fine 仅用于全部产物回收且实例关机验证后的本地 development evaluation。LF2 唯一 GPU 轨迹已回收、哈希核验并关机。

## 方法与论文身份

ConFIG、staggered blocks、coupling homotopy、exact-top lift、medium warm-start、event-balanced distillation、persistent replay、target-measure calibration 与普通 augmented Lagrangian 都是 `SHARED_SOLVER_BACKBONE_NOT_AUTOMATIC_HEADLINE_INNOVATION`。LF1 曾建立 single-seed nominal PINN competence但没有强基线增量；LF2 又证明全局测度误差改善不能替代稀有事件 competence。direct medium `LF_ONLY` 与 B0 `LF_DATA_ONLY` 仍是必须保留的强 non-PINN comparators。当前唯一后备建议是另行授权的 phase-latent/kinetic teacher 最小检验；它尚未执行，更不是 candidate。任何正面路线最终仍须面对强基线、关键消融、多 seed、sealed stress/formal OOD 与单一 load-bearing core。

## 权威路由

当前授权见 [active phase](active_phase.md)，事实见 [project state](PROJECT_STATE.md)，动作见 [live plan](docs/plans/NEXT_ACTIONS.md)，LF2 结果见 [terminal closeout](docs/experiment/2026-09-04-phk-v23-lf2-terminal-closeout.md)，LF1 结果见 [previous terminal closeout](docs/experiment/2026-09-03-phk-v23-lf1-terminal-closeout.md)，LF0 结果见 [LF0 closeout](docs/experiment/2026-09-03-phk-v23-lf0-terminal-closeout.md)，C0 结果见 [compatibility closeout](docs/experiment/2026-09-03-phk-v23-c0-reference-discrete-strongform-compatibility-closeout.md)。
