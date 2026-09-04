# PINN-PCM-SCI

面向“物理信息神经网络 × 氧化物相变材料与器件”的纯软件研究项目。目标是形成证据闭合、可复现、达到中科院二区定位的论文初稿；这不是期刊接收承诺，合成数值证据也不等于实验验证。

## 当前状态

- `phase_id`: `PHK_V23_LF1_EVENT_PRESERVING_MULTIFIDELITY_PILOT`
- `lifecycle_state`: `COMPLETE`
- `blocker_id`: `NONE_TERMINAL`
- `claim_status`: `V22R_R0_R1A_R1X_C0_LF0_EVIDENCE_PRESERVED_LF1_DATA_ONLY_VALUE_NO_PINN_GAIN`
- `next_research_execution_authorized`: `false`

LF1 已终局完成。Run B0 的 event-balanced medium 蒸馏与 B final 的 persistent replay 都保留了两周期 competence，且固定 physics objective ratio 降至 `0.0571112`；但 B final 相对 B0 与 direct `LF_ONLY` 的 phase noninferiority 和 temperature preservation 失败。机器结果为 `LF1_DATA_ONLY_VALUE_NO_PINN_GAIN`，candidate 为 none，条件 C 未触发。两条 GPU 轨迹均已回收、哈希核验和关机；stress 继续 sealed/unread。

## 当前入口

- 授权边界：[active_phase.md](active_phase.md)
- 已核验状态：[PROJECT_STATE.md](PROJECT_STATE.md)
- 唯一 live plan：[docs/plans/NEXT_ACTIONS.md](docs/plans/NEXT_ACTIONS.md)
- 当前决定：[ADR 0057](docs/adr/0057-activate-phk-v23-lf1-event-preserving-multifidelity-pilot.md)
- CPU 资格：[LF1 qualification](docs/experiment/2026-09-03-phk-v23-lf1-cpu-qualification.md)
- LF1 终局：[LF1 terminal closeout](docs/experiment/2026-09-03-phk-v23-lf1-terminal-closeout.md)
- Run A 中间证据：[LF1 Run A interim closeout](docs/experiment/2026-09-03-phk-v23-lf1-run-a-interim-closeout.md)
- LF0 结果：[terminal closeout](docs/experiment/2026-09-03-phk-v23-lf0-terminal-closeout.md)
- C0 结果：[compatibility closeout](docs/experiment/2026-09-03-phk-v23-c0-reference-discrete-strongform-compatibility-closeout.md)
- R1X 历史结果：[terminal closeout](docs/experiment/2026-09-03-phk-v23-r1x-e2-pure-scratch-stop-closeout.md)
- 论文历史包：[paper/paper_v22r](paper/paper_v22r/README.md)
- 文档地图：[docs/README.md](docs/README.md)
- 当前研究口径：[CONTEXT.md](CONTEXT.md)
