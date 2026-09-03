# PINN-PCM-SCI

面向“物理信息神经网络 × 氧化物相变材料与器件”的纯软件研究项目。目标是形成证据闭合、可复现、达到中科院二区定位的论文初稿；这不是期刊接收承诺，合成数值证据也不等于实验验证。

## 当前状态

- `phase_id`: `PHK_V23_C0_REFERENCE_DISCRETE_STRONGFORM_COMPATIBILITY_AUDIT_EXECUTE`
- `lifecycle_state`: `COMPLETE`
- `blocker_id`: `C0_OUTPUT_TRANSFORM_INADMISSIBLE`
- `claim_status`: `V22R_AND_R1X_NEGATIVE_EVIDENCE_PRESERVED_C0_OUTPUT_TRANSFORM_INADMISSIBLE_NO_METHOD_EVIDENCE`
- `next_research_execution_authorized`: `false`

C0 CPU/FP64 audit 已完成：event-competent reference 通过原 R1X readiness，phase native/strong-form 子门 compatible；但 E2 top hard lift 的人工内部下界排除了 W1/W3 大部分 nominal event-support potential，机器 PRIMARY 为 `C0_OUTPUT_TRANSFORM_INADMISSIBLE`。该发现只收紧 E2 hard-lift 负结果的解释边界，不改写其他历史证据，也不授权下一训练。stress 仍 sealed/unread，C0 未触碰当前 AutoDL 实例。

## 当前入口

- 授权边界：[active_phase.md](active_phase.md)
- 已核验状态：[PROJECT_STATE.md](PROJECT_STATE.md)
- 唯一 live plan：[docs/plans/NEXT_ACTIONS.md](docs/plans/NEXT_ACTIONS.md)
- C0 结果：[compatibility closeout](docs/experiment/2026-09-03-phk-v23-c0-reference-discrete-strongform-compatibility-closeout.md)
- 当前决定：[ADR 0055](docs/adr/0055-activate-phk-v23-c0-reference-discrete-strongform-compatibility-audit.md)
- R1X 历史结果：[terminal closeout](docs/experiment/2026-09-03-phk-v23-r1x-e2-pure-scratch-stop-closeout.md)
- 论文历史包：[paper/paper_v22r](paper/paper_v22r/README.md)
- 文档地图：[docs/README.md](docs/README.md)
- 当前研究口径：[CONTEXT.md](CONTEXT.md)
