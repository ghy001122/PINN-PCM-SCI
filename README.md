# PINN-PCM-SCI

面向“物理信息神经网络 × 氧化物相变材料与器件”的纯软件研究项目。目标是形成证据闭合、可复现、达到中科院二区定位的论文初稿；这不是期刊接收承诺，合成数值证据也不等于实验验证。

## 当前状态

- `phase_id`: `PHK_V23_LF2_MEASURE_CALIBRATED_FEASIBLE_PINN_EXECUTE`
- `lifecycle_state`: `COMPLETE`
- `blocker_id`: `NONE`
- `claim_status`: `V22R_R0_R1A_R1X_C0_LF0_LF1_EVIDENCE_PRESERVED_LF2_CALIBRATED_CARRIER_NOT_ESTABLISHED`
- `next_research_execution_authorized`: `false`

LF2 唯一 V100/FP64/seed-17 轨迹在 M0 完成 1200 个 target-measure data-only updates 后停止。三项全局加权场误差均比 LF1-B0 低，potential guard 通过，但 `phase_max≈0.02995` 且两周期事件完全消失，因此终局为 `LF2_CALIBRATED_CARRIER_NOT_ESTABLISHED`；M1 未运行，candidate 为 none。产物已回收核验、AutoDL 已关机，nominal 仅在关机后本地评价，stress 继续 sealed/unread。

下一机器建议是需要新授权的 phase-latent teacher 后备；当前不授权训练、PJGR/R2、多 seed、stress、formal OOD 或投稿。

## 当前入口

- 授权边界：[active_phase.md](active_phase.md)
- 已核验状态：[PROJECT_STATE.md](PROJECT_STATE.md)
- 唯一 live plan：[docs/plans/NEXT_ACTIONS.md](docs/plans/NEXT_ACTIONS.md)
- 当前决定：[ADR 0058](docs/adr/0058-activate-phk-v23-lf2-measure-calibrated-feasible-pinn.md)
- LF2 终局：[terminal closeout](docs/experiment/2026-09-04-phk-v23-lf2-terminal-closeout.md)
- CPU 资格：[LF2 qualification](docs/experiment/2026-09-04-phk-v23-lf2-cpu-qualification.md)
- LF1 终局：[LF1 terminal closeout](docs/experiment/2026-09-03-phk-v23-lf1-terminal-closeout.md)
- LF0 结果：[LF0 terminal closeout](docs/experiment/2026-09-03-phk-v23-lf0-terminal-closeout.md)
- C0 结果：[compatibility closeout](docs/experiment/2026-09-03-phk-v23-c0-reference-discrete-strongform-compatibility-closeout.md)
- 论文历史包：[paper/paper_v22r](paper/paper_v22r/README.md)
- 文档地图：[docs/README.md](docs/README.md)
- 当前研究口径：[CONTEXT.md](CONTEXT.md)
