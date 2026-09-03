# PINN-PCM-SCI 当前研究设定与论文口径

- `document_role`: `CURRENT_RESEARCH_SETTING_AND_PAPER_LANGUAGE`
- `updated_at`: `2026-09-03`

## 当前研究问题

PHK-V2.2R 在 fixed-discretization nominal benchmark 上形成四臂 terminal No-Go：PDE loss 下降但两周期相变事件完全缺失。R0A 没有识别单一根因；R0B 的 gradient-starvation 只是一项 temporal precursor；R0C 表明 Adam 预条件补偿 raw gradient；R1a 的 standard ConFIG 能按定义形成 conflict-free direction 并降低 PDE loss，但仍为 `R1A_CONFIG_RAW_NO_COMPETENCE`。

R1X 已有效执行 E1 clean coupling 与 E2 top-Dirichlet hard lift 两条 non-voting exploration。二者都在 300-step warm-up 未通过 W1/W3 readiness；E2 没有 material phase signal，冻结机器树据此以 `PURE_SCRATCH_COMPETENCE_RECOVERY_FAILED` 收口。E1/E2 均未进入 coupling ramp 或 full-physics closure，因此该结果只关闭冻结 R1X 树，不是对所有 pure-scratch PINN 策略的全局否定。

当前 C0 仅审计 nominal reference、native FVM 离散、continuous strong form、初值/边界、R1X readiness pool 与 E2 output parameterization 的兼容性。它不训练、不提供方法增益，也不把 extra-fine fixed-discretization carrier 称为 continuum truth。

## 物理对象与证据边界

对象仍是 PHK-V2.1 的透明、无量纲、literature-inspired synthetic 2D wall-cell；几何、PDE、本构、参数、IC/BC、ROI、事件与 frozen evaluator 均不改变。它不是材料常数校准、实验器件验证、continuum truth 或 formal OOD。

C0 仅在本地读取 nominal development carriers 与 E2 prediction carrier。reference 不进入训练、loss、sampler、初始化、阈值或 checkpoint selection；两份 stress references 始终 sealed/unread。当前 AutoDL 实例由先前用户例外保留，C0 不连接、不使用也不关闭它。

## 方法与论文身份

ConFIG、staggered blocks、coupling homotopy 与 output lift 都是 `SHARED_SOLVER_BACKBONE_NOT_AUTOMATIC_HEADLINE_INNOVATION`。C0 若发现 compatibility 问题，只能收紧相应负面结果的解释边界；不能追溯改写其他未受挑战的证据，也不能自动授权 low-fidelity、reparameterization、PJGR 或 R2。

## 权威路由

当前授权见 [active phase](active_phase.md)，事实见 [project state](PROJECT_STATE.md)，动作见 [live plan](docs/plans/NEXT_ACTIONS.md)，决定见 [ADR 0055](docs/adr/0055-activate-phk-v23-c0-reference-discrete-strongform-compatibility-audit.md)，前一阶段见 [R1X terminal closeout](docs/experiment/2026-09-03-phk-v23-r1x-e2-pure-scratch-stop-closeout.md)。
