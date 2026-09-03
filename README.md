# PINN-PCM-SCI

面向“物理信息神经网络 × 氧化物相变材料与器件”的纯软件研究项目。目标是形成证据闭合、可复现、达到中科院二区定位的论文初稿；这不是期刊接收承诺，合成数值证据也不等于实验验证。

## 当前状态

- `phase_id`: `PHK_V23_LF0_EXACT_TOP_WARMSTART_ATTRIBUTION_EXECUTE`
- `lifecycle_state`: `COMPLETE`
- `blocker_id`: `NONE`
- `claim_status`: `V22R_R1X_C0_PRESERVED_LF0_NUMERICAL_OR_IDENTITY_INVALID_NO_METHOD_EVIDENCE`
- `next_research_execution_authorized`: `false`

LF0 已执行并收口。A 的 exact-top scratch PINN 没有两周期 competence；B 的固定 step-800 `LF_DATA_ONLY` checkpoint 违反 potential validity，B final 虽恢复合法 potential 仍无事件。机器终局为 `LF0_NUMERICAL_OR_IDENTITY_INVALID`，条件 C 未运行，无 candidate 或方法增量证据。用户明确要求本次保留空闲 GPU 实例；这不是后续科研授权。stress 保持 sealed/unread。

## 当前入口

- 授权边界：[active_phase.md](active_phase.md)
- 已核验状态：[PROJECT_STATE.md](PROJECT_STATE.md)
- 唯一 live plan：[docs/plans/NEXT_ACTIONS.md](docs/plans/NEXT_ACTIONS.md)
- 当前决定：[ADR 0056](docs/adr/0056-activate-phk-v23-lf0-exact-top-warmstart-attribution.md)
- LF0 结果：[terminal closeout](docs/experiment/2026-09-03-phk-v23-lf0-terminal-closeout.md)
- CPU 资格：[LF0 qualification](docs/experiment/2026-09-03-phk-v23-lf0-cpu-qualification.md)
- C0 结果：[compatibility closeout](docs/experiment/2026-09-03-phk-v23-c0-reference-discrete-strongform-compatibility-closeout.md)
- R1X 历史结果：[terminal closeout](docs/experiment/2026-09-03-phk-v23-r1x-e2-pure-scratch-stop-closeout.md)
- 论文历史包：[paper/paper_v22r](paper/paper_v22r/README.md)
- 文档地图：[docs/README.md](docs/README.md)
- 当前研究口径：[CONTEXT.md](CONTEXT.md)
