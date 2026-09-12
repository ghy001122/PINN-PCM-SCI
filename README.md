# PINN-PCM-SCI

面向“物理信息神经网络 × 氧化物相变材料与器件”的纯软件研究项目。目标是形成证据闭合、可复现、达到中科院二区定位的论文初稿；这不是期刊接收承诺，合成数值证据也不等于实验验证。

## 当前状态

- `phase_id`: `PHK_V23_LF11_FOLLOWUP_FIT_AND_ELECTRIC_BLOCK_SPRINT_COMPLETE`
- `lifecycle_state`: `CLOSED`
- `blocker_id`: `NONE`
- `claim_status`: `VALID_THERMAL_FIT_REPAIR_NO_NEW_PINN_COMPARISON`
- `next_research_execution_authorized`: `false`

VERIFIED：温度包络下界0.1504%；可见T误差17.8233%→1.1375%，三个T拟合门均过，phase不变。可见V误差0.8215%未达0.5%，是唯一未满足的拟合条件。完整nominal参考ROI T误差28.2210%→1.7475%，能量误差106.7402%→49.2006%。

新的物理/归一化分支因V拟合前提未满足而未运行，不记为失败。paper_v25已整合实际结果；本轮未启动GPU实例。旧LF11与paper_v24保留，无新科研执行授权，stress sealed/unread。

## 当前入口

- LF11后续终局：[closeout](docs/experiment/2026-09-12-phk-v23-lf11-followup-terminal-closeout.md)
- 当前论文：[paper_v25](paper/paper_v25/README.md)
- 授权边界：[active_phase.md](active_phase.md)
- 已核验状态：[PROJECT_STATE.md](PROJECT_STATE.md)
- 唯一 live plan：[docs/plans/NEXT_ACTIONS.md](docs/plans/NEXT_ACTIONS.md)
- LF11终局：[terminal closeout](docs/experiment/2026-09-11-phk-v23-lf11-terminal-closeout.md)
- 上轮论文快照与图表：[paper/paper_v24](paper/paper_v24/README.md)
- LF10 关闭决定：[ADR 0074](docs/adr/0074-close-phk-v23-lf10-feasible-direction-replication.md)
- LF10 终局：[terminal closeout](docs/experiment/2026-09-09-phk-v23-lf10-terminal-closeout.md)
- LF10 激活决定：[ADR 0073](docs/adr/0073-activate-phk-v23-lf10-feasible-direction-replication.md)
- LF10 CPU 资格：[CPU qualification](docs/experiment/2026-09-09-phk-v23-lf10-cpu-qualification.md)
- LF9关闭决定：[ADR 0072](docs/adr/0072-close-phk-v23-lf9-equation-routed-thermal-cv-refinement.md)
- LF9 终局：[terminal closeout](docs/experiment/2026-09-08-phk-v23-lf9-terminal-closeout.md)
- LF9 激活决定：[ADR 0071](docs/adr/0071-activate-phk-v23-lf9-equation-routed-thermal-cv-refinement.md)
- LF9 CPU 资格：[CPU qualification](docs/experiment/2026-09-08-phk-v23-lf9-cpu-qualification.md)
- LF8关闭决定：[ADR 0070](docs/adr/0070-close-phk-v23-lf8-competence-filter-completion.md)
- LF8 终局：[terminal closeout](docs/experiment/2026-09-08-phk-v23-lf8-terminal-closeout.md)
- LF8 激活决定：[ADR 0069](docs/adr/0069-activate-phk-v23-lf8-competence-filter-completion.md)
- LF8 CPU 资格：[CPU qualification](docs/experiment/2026-09-08-phk-v23-lf8-cpu-qualification.md)
- LF7关闭决定：[ADR 0068](docs/adr/0068-close-phk-v23-lf7-competence-filtered-refinement.md)
- LF7 终局：[terminal closeout](docs/experiment/2026-09-07-phk-v23-lf7-terminal-closeout.md)
- LF7 激活决定：[ADR 0067](docs/adr/0067-activate-phk-v23-lf7-competence-filtered-refinement.md)
- LF7 CPU 资格：[CPU qualification](docs/experiment/2026-09-07-phk-v23-lf7-cpu-qualification.md)
- LF7 prior art：[constrained-refinement prior-art closure](docs/references/2026-09-07-phk-v23-lf7-constrained-refinement-prior-art.md)
- 上一关闭决定：[ADR 0066](docs/adr/0066-close-phk-v23-lf6-event-frontier-pilot.md)
- LF6 终局：[terminal closeout](docs/experiment/2026-09-06-phk-v23-lf6-terminal-closeout.md)
- 上一关闭决定：[ADR 0064](docs/adr/0064-close-phk-v23-lf5-temporal-zero-level-pilot.md)
- LF5 终局：[terminal closeout](docs/experiment/2026-09-05-phk-v23-lf5-terminal-closeout.md)
- LF5 激活决定：[ADR 0063](docs/adr/0063-activate-phk-v23-lf5-temporal-zero-level-pilot.md)
- LF5 CPU-T：[CPU-T qualification](docs/experiment/2026-09-05-phk-v23-lf5-cpu-qualification.md)
- LF4 关闭决定：[ADR 0062](docs/adr/0062-close-phk-v23-lf4-interface-band-pilot.md)
- LF4 终局：[terminal closeout](docs/experiment/2026-09-05-phk-v23-lf4-terminal-closeout.md)
- LF4 CPU 资格：[CPU-G qualification](docs/experiment/2026-09-05-phk-v23-lf4-cpu-qualification.md)
- 上一阶段：[LF3 terminal closeout](docs/experiment/2026-09-05-phk-v23-lf3-terminal-closeout.md)
- 保留论文快照：[paper/paper_v23](paper/paper_v23/README.md)
- 上一关闭决定：[ADR 0060](docs/adr/0060-close-phk-v23-lf3-carrier-not-established.md)
- LF2 终局：[LF2 terminal closeout](docs/experiment/2026-09-04-phk-v23-lf2-terminal-closeout.md)
- LF1 终局：[LF1 terminal closeout](docs/experiment/2026-09-03-phk-v23-lf1-terminal-closeout.md)
- LF0 结果：[LF0 terminal closeout](docs/experiment/2026-09-03-phk-v23-lf0-terminal-closeout.md)
- C0 结果：[compatibility closeout](docs/experiment/2026-09-03-phk-v23-c0-reference-discrete-strongform-compatibility-closeout.md)
- 上一论文包：[paper/paper_v22r](paper/paper_v22r/README.md)
- 文档地图：[docs/README.md](docs/README.md)
- 当前研究口径：[CONTEXT.md](CONTEXT.md)
