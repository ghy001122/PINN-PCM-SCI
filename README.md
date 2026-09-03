# PINN-PCM-SCI

面向“物理信息神经网络 × 氧化物相变材料与器件”的纯软件研究项目。目标是形成证据闭合、可复现、达到中科院二区定位的论文初稿；这不是期刊接收承诺，合成数值证据也不等于实验验证。

## 当前状态

- `phase_id`: `PHK_V23_C0_REFERENCE_DISCRETE_STRONGFORM_COMPATIBILITY_AUDIT_EXECUTE`
- `lifecycle_state`: `ACTIVE`
- `blocker_id`: `C0_CPU_COMPATIBILITY_DIAGNOSTIC_PENDING`
- `claim_status`: `V22R_AND_R1X_NEGATIVE_EVIDENCE_PRESERVED_C0_DIAGNOSTIC_PENDING`
- `next_research_execution_authorized`: `true`

PHK-V2.2R、R0A/R0B/R0C、R1a 和 R1X 的既有证据保持冻结。R1X 两条 pure-scratch explorations 均未通过 readiness；当前仅授权一次本地 CPU/FP64 compatibility audit，检查 reference、FVM 离散、continuous strong form、初值/边界与 output transform 的可比性。C0 不训练、不使用 GPU、不触碰当前 AutoDL 实例，也不读取 stress。

## 当前入口

- 授权边界：[active_phase.md](active_phase.md)
- 已核验状态：[PROJECT_STATE.md](PROJECT_STATE.md)
- 唯一 live plan：[docs/plans/NEXT_ACTIONS.md](docs/plans/NEXT_ACTIONS.md)
- C0 合同：[compatibility contract](configs/phk_v23/c0_reference_discrete_strongform_compatibility_contract.json)
- 当前决定：[ADR 0055](docs/adr/0055-activate-phk-v23-c0-reference-discrete-strongform-compatibility-audit.md)
- R1X 历史结果：[terminal closeout](docs/experiment/2026-09-03-phk-v23-r1x-e2-pure-scratch-stop-closeout.md)
- 论文历史包：[paper/paper_v22r](paper/paper_v22r/README.md)
- 文档地图：[docs/README.md](docs/README.md)
- 当前研究口径：[CONTEXT.md](CONTEXT.md)
