# PINN-PCM-SCI

面向“物理信息神经网络 × 氧化物相变材料与器件”的纯软件研究项目。目标是形成证据闭合、可复现、达到中科院二区定位的论文初稿；这不是期刊接收承诺，合成数值证据也不等于实验验证。

## 当前状态

- `phase_id`: `PHK_V23_LF2_MEASURE_CALIBRATED_FEASIBLE_PINN_EXECUTE`
- `lifecycle_state`: `ACTIVE`
- `blocker_id`: `NONE`
- `claim_status`: `V22R_R0_R1A_R1X_C0_LF0_LF1_EVIDENCE_PRESERVED_LF2_CPU_QUALIFIED_GPU_RESULT_PENDING`
- `next_research_execution_authorized`: `true`

LF2 CPU 资格已通过，当前授权唯一一条 V100/FP64/seed-17 trajectory。它先用 evaluator-compatible target measure 校准 LF1-B0 的过宽事件 carrier，再条件式执行 inequality-constrained full physics refinement；GPU 结束后必须先回收、核验和关机，才能做本地 nominal 评价。LF1 的 `LF1_DATA_ONLY_VALUE_NO_PINN_GAIN` 保持不改写，stress 继续 sealed/unread。

## 当前入口

- 授权边界：[active_phase.md](active_phase.md)
- 已核验状态：[PROJECT_STATE.md](PROJECT_STATE.md)
- 唯一 live plan：[docs/plans/NEXT_ACTIONS.md](docs/plans/NEXT_ACTIONS.md)
- 当前决定：[ADR 0058](docs/adr/0058-activate-phk-v23-lf2-measure-calibrated-feasible-pinn.md)
- CPU 资格：[LF2 qualification](docs/experiment/2026-09-04-phk-v23-lf2-cpu-qualification.md)
- LF1 终局：[LF1 terminal closeout](docs/experiment/2026-09-03-phk-v23-lf1-terminal-closeout.md)
- Run A 中间证据：[LF1 Run A interim closeout](docs/experiment/2026-09-03-phk-v23-lf1-run-a-interim-closeout.md)
- LF0 结果：[terminal closeout](docs/experiment/2026-09-03-phk-v23-lf0-terminal-closeout.md)
- C0 结果：[compatibility closeout](docs/experiment/2026-09-03-phk-v23-c0-reference-discrete-strongform-compatibility-closeout.md)
- R1X 历史结果：[terminal closeout](docs/experiment/2026-09-03-phk-v23-r1x-e2-pure-scratch-stop-closeout.md)
- 论文历史包：[paper/paper_v22r](paper/paper_v22r/README.md)
- 文档地图：[docs/README.md](docs/README.md)
- 当前研究口径：[CONTEXT.md](CONTEXT.md)
