# 项目状态

更新时间：2026-09-12

- `phase_id`: `PHK_V23_LF11_JOINT_BC_PDE_COMPLETE`
- `lifecycle_state`: `CLOSED`
- `blocker_id`: `NONE`
- `claim_status`: `VALID_MATCHED_CONSTRAINT_STUDY_NO_DECLARED_INCREMENT`
- `next_research_execution_authorized`: `false`

## 最新 VERIFIED

VERIFIED：同父 D_I/D_B/P_U 与条件 R/G/N 六个固定终点均合法，实际新增 6500 Adam updates、1500 次完整固定评估。五个匹配差分的重建 A / 功能 B 均未通过；D_N 未触发、未运行。局部相态及顶流改善与接触/功率代价并存，归一化未建立独立增量。

- D_B 对 D_I：总 BC 下降 61.44%，heater 子项却上升 20.92%，完整接触迹 RMS 上升 9.02%。raw Ephi 改善 3.10%、顶流改善 15.71%，底流/功率误差上升 7.74%/10.48%。
- P_U 对 D_B：独立 AD 物理目标下降 55.75%，raw Ephi 改善 2.81%，EV 却上升 8.33%，底流/功率误差上升 5.87%/9.14%。两个周期 timing 改善但 recall 下降。
- N 对 R：顶流误差下降 46.41%，底流/功率误差上升 12.75%/15.64%，raw Ephi 上升 5.20%；N 对 G 的底流/功率误差上升 17.09%/22.39%。G 的底流/功率改善 3.71%/5.52%，不足冻结效应门。
- 三个原 P_U Adam 节点均满足同一 electric-amplitude→T 的局部判据，因此条件路径实际执行；局部分量并不等于历史动量或总方向。六个端点都未通过严格器件门。

## 解释、论文与未知

SUPPORTED_INTERPRETATION：汇总 BC、连续 AD 残差和有限体积器件读出不能相互替代；局部幅值通道存在不足以保证本次归一化有效。接触迹/增量与耗散分解，以及局部 FV 残差到双端电流/功率缺陷的代数关系，形成可入稿机制证据。各新臂 T/phase/σ 均改变，不能移用旧 V-only 的固定 σ 因果百分比。

[本轮终局](docs/experiment/2026-09-12-phk-v23-lf11-joint-terminal-closeout.md)、[paper_v27 六图与数表](paper/paper_v27/README.md)、[主张矩阵](paper/paper_v27/claim_evidence_matrix.md)、[复现](paper/paper_v27/reproducibility.md)为最新入口。通用拟合、适配器及已知代数恒等式不单独算 PINN 创新；竞争性的正面 PINN 方法、独立初始化、mask/完整案例确认、formal OOD、连续体真值及材料标定仍未建立。

HYPOTHESIS / PROPOSED_NOT_AUTHORIZED：下一优先为电学子问题消元与一致焦耳读出，D_E/P_E/B_E 共用相同电学层，检验热/相态 PDE 的独立增量。详见[唯一下一计划](docs/plans/NEXT_ACTIONS.md)。该方法尚未实现、求解或训练。

## 保留的历史与运行边界

paper_v26 的 V-only 0.5618% 仍未通过原 0.5% 门，旧分支仍是未运行；本轮直接起于该指定父态，未替换旧裁决。paper_v23/v24/v25/v26 的界面暴露、物理遗忘、拟合修复与接触控制证据保持原样。新父态、新校准和新预算的组合不能单独归因于拟合修复。

全部科学训练已结束，CPU-only，未启动云实例，stress 未读，未增加观测、独立 seed 或新物理。用户随后明确授权发布 paper_v27 与关键证据，并交付“推进PINN相变研究”独立评估；[本轮交接](docs/notes/2026-09-12-lf11-v27-results-cloud-review-handoff.md)随成果提交，实际云端版本及送达状态由交付消息确认。下一轮研究执行仍未授权，运行时未发布字段保留为历史快照。
