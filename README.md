# PINN-PCM-SCI

面向“物理信息神经网络 × 氧化物相变材料与器件”的纯软件研究项目。目标是形成证据闭合、可复现、达到中科院二区定位的论文初稿；这不是期刊接收承诺，合成数值证据也不等于实验验证。

## 当前状态

- `phase_id`: `PHK_V23_LF0_EXACT_TOP_WARMSTART_ATTRIBUTION_EXECUTE`
- `lifecycle_state`: `ACTIVE`
- `blocker_id`: `LF0_CPU_QUALIFICATION_PENDING`
- `claim_status`: `C0_OUTPUT_TRANSFORM_INADMISSIBLE_PRESERVED_LF0_AUTHORIZED_NO_NEW_RESULT`
- `next_research_execution_authorized`: `true`

LF0 已获用户明确授权并进入实现与 CPU 资格阶段。该 campaign 用无 E2 内部下界的 exact-top raw potential transform 对照 scratch 与唯一 medium-only warm-start，固定执行 A、B，并仅在 B 通过 provisional 增量门时执行 C；最多三条 V100/FP64/seed-17 科学轨迹。stress 保持 sealed/unread，尚无 LF0 科学结果。

## 当前入口

- 授权边界：[active_phase.md](active_phase.md)
- 已核验状态：[PROJECT_STATE.md](PROJECT_STATE.md)
- 唯一 live plan：[docs/plans/NEXT_ACTIONS.md](docs/plans/NEXT_ACTIONS.md)
- 当前决定：[ADR 0056](docs/adr/0056-activate-phk-v23-lf0-exact-top-warmstart-attribution.md)
- C0 结果：[compatibility closeout](docs/experiment/2026-09-03-phk-v23-c0-reference-discrete-strongform-compatibility-closeout.md)
- R1X 历史结果：[terminal closeout](docs/experiment/2026-09-03-phk-v23-r1x-e2-pure-scratch-stop-closeout.md)
- 论文历史包：[paper/paper_v22r](paper/paper_v22r/README.md)
- 文档地图：[docs/README.md](docs/README.md)
- 当前研究口径：[CONTEXT.md](CONTEXT.md)
