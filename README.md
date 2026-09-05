# PINN-PCM-SCI

面向“物理信息神经网络 × 氧化物相变材料与器件”的纯软件研究项目。目标是形成证据闭合、可复现、达到中科院二区定位的论文初稿；这不是期刊接收承诺，合成数值证据也不等于实验验证。

## 当前状态

- `phase_id`: `PHK_V23_LF4_THRESHOLD_ALIGNED_INTERFACE_BAND_MECHANISM_AND_CONDITIONAL_PHYSICS_PILOT_EXECUTE`
- `lifecycle_state`: `COMPLETE`
- `blocker_id`: `NONE`
- `machine_outcome`: `LF4_NO_DEVELOPMENT_ENTRY`
- `mechanism_outcome`: `BOUNDARY_EXPOSURE_SUPPORTED`
- `claim_status`: `LF4_BOUNDARY_EXPOSURE_SUPPORTED_NO_DEVELOPMENT_ENTRY_NO_PINN_RESULT`
- `next_research_execution_authorized`: `false`

LF4 已完成三条 matched 400-step phase-only arms。DEV-M 相对等预算 DEV-G 将 minimum recall 提高 `0.089837` 且通过冻结质量条件，支持本 single-seed nominal 对象上的有界 boundary-exposure 增量；DEV-C 的 threshold BCE 虽继续提高 recall，却显著恶化 phase error，未通过完整机制门。

三臂均未通过完整 P0-entry，故 P0 未运行、candidate 为 none，终局为 `LF4_NO_DEVELOPMENT_ENTRY`。实例已在产物回收和哈希核验后关闭；本地 nominal evaluation 随后完成，stress 始终 sealed/unread。当前无后续科研执行授权。

## 当前入口

- 授权边界：[active_phase.md](active_phase.md)
- 已核验状态：[PROJECT_STATE.md](PROJECT_STATE.md)
- 唯一 live plan：[docs/plans/NEXT_ACTIONS.md](docs/plans/NEXT_ACTIONS.md)
- 当前关闭决定：[ADR 0062](docs/adr/0062-close-phk-v23-lf4-interface-band-pilot.md)
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
