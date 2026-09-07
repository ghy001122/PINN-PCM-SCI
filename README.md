# PINN-PCM-SCI

面向“物理信息神经网络 × 氧化物相变材料与器件”的纯软件研究项目。目标是形成证据闭合、可复现、达到中科院二区定位的论文初稿；这不是期刊接收承诺，合成数值证据也不等于实验验证。

## 当前状态

- `phase_id`: `PHK_V23_LF6_EVENT_FRONTIER_RANK_BAND_AND_SAFETY_GATED_PHYSICS_PILOT_EXECUTE`
- `lifecycle_state`: `ACTIVE`
- `blocker_id`: `NONE`
- `machine_outcome`: `PENDING`
- `mechanism_outcome`: `PENDING_MATCHED_DEV_U_DEV_R`
- `claim_status`: `CPU_F_QUALIFIED_MATCHED_EVENT_FRONTIER_AND_CONDITIONAL_PHYSICS_EXECUTION_PENDING`
- `next_research_execution_authorized`: `true`

LF6 CPU-F 已在零 optimizer update 下冻结 ROI 临界秩、matched DEV-U/DEV-R endpoint、全部 development/P0 batches 与 blind physics pool，并重新核验 exact historical DEV-M safety fallback。当前只执行 fixed 400+400 matched screen 和由冻结规则选择的唯一 1200-step label-free P0；fine、extra-fine、direct LF_ONLY 与 frozen evaluator 仅在关机后本地读取，stress 保持 sealed/unread。

## 当前入口

- 授权边界：[active_phase.md](active_phase.md)
- 已核验状态：[PROJECT_STATE.md](PROJECT_STATE.md)
- 唯一 live plan：[docs/plans/NEXT_ACTIONS.md](docs/plans/NEXT_ACTIONS.md)
- 当前激活决定：[ADR 0065](docs/adr/0065-activate-phk-v23-lf6-event-frontier-pilot.md)
- LF6 CPU-F：[CPU-F qualification](docs/experiment/2026-09-06-phk-v23-lf6-cpu-qualification.md)
- LF6 prior art：[event-frontier prior-art closure](docs/references/2026-09-06-phk-v23-lf6-event-frontier-prior-art.md)
- 当前关闭决定：[ADR 0064](docs/adr/0064-close-phk-v23-lf5-temporal-zero-level-pilot.md)
- LF5 终局：[terminal closeout](docs/experiment/2026-09-05-phk-v23-lf5-terminal-closeout.md)
- LF5 激活决定：[ADR 0063](docs/adr/0063-activate-phk-v23-lf5-temporal-zero-level-pilot.md)
- LF5 CPU-T：[CPU-T qualification](docs/experiment/2026-09-05-phk-v23-lf5-cpu-qualification.md)
- LF4 关闭决定：[ADR 0062](docs/adr/0062-close-phk-v23-lf4-interface-band-pilot.md)
- LF4 终局：[terminal closeout](docs/experiment/2026-09-05-phk-v23-lf4-terminal-closeout.md)
- LF4 CPU 资格：[CPU-G qualification](docs/experiment/2026-09-05-phk-v23-lf4-cpu-qualification.md)
- 上一阶段：[LF3 terminal closeout](docs/experiment/2026-09-05-phk-v23-lf3-terminal-closeout.md)
- 当前论文初稿：[paper/paper_v23](paper/paper_v23/README.md)
- 上一关闭决定：[ADR 0060](docs/adr/0060-close-phk-v23-lf3-carrier-not-established.md)
- LF2 终局：[LF2 terminal closeout](docs/experiment/2026-09-04-phk-v23-lf2-terminal-closeout.md)
- LF1 终局：[LF1 terminal closeout](docs/experiment/2026-09-03-phk-v23-lf1-terminal-closeout.md)
- LF0 结果：[LF0 terminal closeout](docs/experiment/2026-09-03-phk-v23-lf0-terminal-closeout.md)
- C0 结果：[compatibility closeout](docs/experiment/2026-09-03-phk-v23-c0-reference-discrete-strongform-compatibility-closeout.md)
- 上一论文包：[paper/paper_v22r](paper/paper_v22r/README.md)
- 文档地图：[docs/README.md](docs/README.md)
- 当前研究口径：[CONTEXT.md](CONTEXT.md)
