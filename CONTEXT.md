# PINN-PCM-SCI 当前研究设定与论文口径

- `document_role`: `CURRENT_RESEARCH_SETTING_AND_PAPER_LANGUAGE`
- `updated_at`: `2026-09-02`

## 当前研究问题

PHK-V2.2R 在 fixed-discretization nominal benchmark 上形成四臂 terminal No-Go：PDE loss 下降但两周期相变事件完全缺失。R0A 没有识别单一根因；R0B 的 gradient-starvation 只是一项 temporal precursor；R0C 表明 Adam 预条件补偿 raw gradient；R1a 的 standard ConFIG 能按定义形成四组 conflict-free direction 并降低 PDE loss，但仍为 `R1A_CONFIG_RAW_NO_COMPETENCE`。

当前 R1X campaign 检验：在不让随机 phase head 污染早期 conductivity/latent feedback 的前提下，先建立两周期 `V -> QJ -> T` 驱动，再通过透明 cold-state-to-learned-phase coupling homotopy 和完整 joint closure，能否恢复 two-cycle event competence。

## 物理对象与证据边界

对象仍是 PHK-V2.1 的透明、无量纲、literature-inspired synthetic 2D wall-cell；几何、PDE、本构、参数、IC/BC、ROI、事件与 frozen evaluator 均不改变。它不是材料常数校准、实验器件验证、continuum truth 或 formal OOD。

所有云端训练、observer、trigger 和 prediction 均 reference-blind。nominal extra-fine reference 仅可在每条运行完成、产物回收核验、AutoDL 关机并验证后用于本地 development evaluation；不得进入 loss、sampler、初始化、readiness、alpha、checkpoint selection、early stop 或阈值。两份 stress references 始终 sealed/unread。

## 方法与论文身份

ConFIG、staggered blocks、coupling homotopy、top hard lift 与 Jacobian-normalized phase transform均默认为 `SHARED_SOLVER_BACKBONE_NOT_AUTOMATIC_HEADLINE_INNOVATION`，并保留透明来源和适配身份。R1X 的目标仅是恢复 solver competence；non-voting exploration 不能冒充 confirmation，单 seed nominal confirmation 也不能支撑多-seed、stress 或投稿 superiority。

若 frozen confirmation PASS，下一步只能进入 headline-core gate review；PJGR 仅在 competent backbone 的残余误差确实局域于 interface/hotspot 且 gate informativeness 与 ungated 对照通过时才可重新考虑。若 pure-scratch 路线失败，只能另立合同选择 low-fidelity-guided route 或保留 bounded-negative package。

## 权威路由

当前授权见 [active phase](active_phase.md)，事实见 [project state](PROJECT_STATE.md)，动作见 [live plan](docs/plans/NEXT_ACTIONS.md)，决定见 [ADR 0053](docs/adr/0053-activate-phk-v23-r1x-bounded-clean-coupling-campaign.md)。历史终局证据见 [V2.2R closeout](docs/experiment/2026-08-30-phk-v22r-v11-nominal-terminal-closeout.md) 与 [R1a closeout](docs/experiment/2026-08-31-phk-v23-r1a-config-closeout.md)。
