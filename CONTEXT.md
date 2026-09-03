# PINN-PCM-SCI 当前研究设定与论文口径

- `document_role`: `CURRENT_RESEARCH_SETTING_AND_PAPER_LANGUAGE`
- `updated_at`: `2026-09-03`

## 当前研究问题

PHK-V2.2R 在 fixed-discretization nominal benchmark 上形成四臂 terminal No-Go；R0A/R0B/R0C 分别保留 inconclusive、temporal precursor 与 Adam-preconditioning 边界；R1a 表明 conflict-resolution-only 不足以恢复 competence。R1X E1/E2 两条 non-voting warm-up exploration 都未通过 W1/W3 readiness，并以冻结机器树的 `PURE_SCRATCH_COMPETENCE_RECOVERY_FAILED` 收口。

C0 已证明 nominal reference 自身通过 readiness 且 pool 未漏检；phase strict-interior native/strong-form 子门 compatible。E2 top hard lift 的内部下界存在表示包络混杂。LF0 随后用无该下界的 exact-top raw lift执行了 scratch A 与 medium-only warm-start B：A 无 competence；B0 未能忠实转移 medium 的事件并违反 potential validity，B final 虽恢复 potential validity仍无事件，故以 `LF0_NUMERICAL_OR_IDENTITY_INVALID` 收口且未运行条件 C。

## 物理对象与证据边界

对象仍是 PHK-V2.1 的透明、无量纲、literature-inspired synthetic 2D wall-cell；几何、PDE、本构、参数、IC/BC、ROI、事件与 frozen evaluator 均不改变。extra-fine fixed-discretization carrier 不是 continuum truth；C0 saved-cadence strong residual 也不是 exact internal-step residual。

两份 stress references 始终 sealed/unread。LF0 云端只读取了 medium low-fidelity method input；fine/extra-fine 仅用于全部产物回收后的本地 development evaluation。用户明确要求本次保留实例在线，该生命周期例外不改变科学或授权边界。

## 方法与论文身份

ConFIG、staggered blocks、coupling homotopy、exact-top lift、medium warm-start 与 anchor annealing 都是 `SHARED_SOLVER_BACKBONE_NOT_AUTOMATIC_HEADLINE_INNOVATION`。当前没有 PINN competence、candidate 或方法增量。direct medium `LF_ONLY` 的两周期 competence 只能证明训练源含事件，不能替代 PINN 方法证据。后续若继续，首要问题是同时保持场可容许性与事件拓扑的低保真转移；任何新方案仍需另行批准，并最终面对强基线、关键消融、多 seed、sealed stress/formal OOD 与单一 load-bearing core。

## 权威路由

当前授权见 [active phase](active_phase.md)，事实见 [project state](PROJECT_STATE.md)，动作见 [live plan](docs/plans/NEXT_ACTIONS.md)，LF0 结果见 [terminal closeout](docs/experiment/2026-09-03-phk-v23-lf0-terminal-closeout.md)，C0 结果见 [compatibility closeout](docs/experiment/2026-09-03-phk-v23-c0-reference-discrete-strongform-compatibility-closeout.md)。
