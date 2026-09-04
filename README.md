# PINN-PCM-SCI

面向“物理信息神经网络 × 氧化物相变材料与器件”的纯软件研究项目。目标是形成证据闭合、可复现、达到中科院二区定位的论文初稿；这不是期刊接收承诺，合成数值证据也不等于实验验证。

## 当前状态

- `phase_id`: `PHK_V23_LF3_MEASURE_DECOUPLED_STARTUP_SCALED_PHASE_LATENT_CARRIER_PILOT_EXECUTE`
- `lifecycle_state`: `COMPLETE`
- `blocker_id`: `NONE`
- `claim_status`: `LF3_CARRIER_NOT_ESTABLISHED_P0_NOT_TRIGGERED_NEGATIVE_ADVISOR_DRAFT_COMPLETE`
- `next_research_execution_authorized`: `false`

LF3 已完成唯一 V100/FP64/seed-17 轨迹。T0 恢复了合法、局域、时刻准确的双周期事件，但两周期 hard recall `0.805842/0.768603` 未达冻结 `0.90`，终局为 `LF3_CARRIER_NOT_ESTABLISHED`；P0 未触发，candidate 为 none。产物已回收核验，实例已关机；关机后的 nominal 评价与 `paper_v23` 导师初稿均已完成，stress 继续 sealed/unread。

当前不授权任何新科研执行、第二条轨迹、matched ablation、PJGR/R2、多 seed、OOD、stress 或投稿。LF2 终局与更早负面证据保持原边界。

## 当前入口

- 授权边界：[active_phase.md](active_phase.md)
- 已核验状态：[PROJECT_STATE.md](PROJECT_STATE.md)
- 唯一 live plan：[docs/plans/NEXT_ACTIONS.md](docs/plans/NEXT_ACTIONS.md)
- 当前终局决定：[ADR 0060](docs/adr/0060-close-phk-v23-lf3-carrier-not-established.md)
- LF3 终局：[terminal closeout](docs/experiment/2026-09-05-phk-v23-lf3-terminal-closeout.md)
- 当前论文初稿：[paper/paper_v23](paper/paper_v23/README.md)
- 激活决定：[ADR 0059](docs/adr/0059-activate-phk-v23-lf3-phase-latent-carrier-pilot.md)
- CPU 资格：[LF3 qualification](docs/experiment/2026-09-04-phk-v23-lf3-cpu-qualification.md)
- LF2 终局：[LF2 terminal closeout](docs/experiment/2026-09-04-phk-v23-lf2-terminal-closeout.md)
- LF1 终局：[LF1 terminal closeout](docs/experiment/2026-09-03-phk-v23-lf1-terminal-closeout.md)
- LF0 结果：[LF0 terminal closeout](docs/experiment/2026-09-03-phk-v23-lf0-terminal-closeout.md)
- C0 结果：[compatibility closeout](docs/experiment/2026-09-03-phk-v23-c0-reference-discrete-strongform-compatibility-closeout.md)
- 上一论文包：[paper/paper_v22r](paper/paper_v22r/README.md)
- 文档地图：[docs/README.md](docs/README.md)
- 当前研究口径：[CONTEXT.md](CONTEXT.md)
