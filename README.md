# PINN-PCM-SCI

面向“物理信息神经网络 × 氧化物相变材料与器件”的纯软件研究项目。目标是形成证据闭合、可复现、达到中科院二区定位的论文初稿；这不是期刊接收承诺，合成数值证据也不等于实验验证。

## 当前状态

- `phase_id`: `PHK_V23_LF3_MEASURE_DECOUPLED_STARTUP_SCALED_PHASE_LATENT_CARRIER_PILOT_EXECUTE`
- `lifecycle_state`: `CPU_QUALIFIED_GPU_EXECUTION_AUTHORIZED`
- `blocker_id`: `NONE`
- `claim_status`: `LF2_EVIDENCE_PRESERVED_LF3_CPU_QUALIFIED_NO_GPU_RESULT_YET`
- `next_research_execution_authorized`: `true`

LF3 已完成四合同、实现、快速 prior-art closure 与零步 CPU 资格。当前只授权唯一 V100/FP64/seed-17 的 T0→条件 P0 轨迹：T0 检验 14 类等权 phase-logit teacher 能否建立合法事件 carrier；只有 T0 全门通过才运行无标签 full-physics P0。fine/extra-fine 与 frozen evaluator 仅允许在产物回收、哈希核验和关机后本地读取，stress 继续 sealed/unread。

不授权第二条轨迹、matched ablation、PJGR/R2、多 seed、OOD、stress 或投稿。LF2 终局与更早负面证据保持原边界。

## 当前入口

- 授权边界：[active_phase.md](active_phase.md)
- 已核验状态：[PROJECT_STATE.md](PROJECT_STATE.md)
- 唯一 live plan：[docs/plans/NEXT_ACTIONS.md](docs/plans/NEXT_ACTIONS.md)
- 当前决定：[ADR 0059](docs/adr/0059-activate-phk-v23-lf3-phase-latent-carrier-pilot.md)
- CPU 资格：[LF3 qualification](docs/experiment/2026-09-04-phk-v23-lf3-cpu-qualification.md)
- LF2 终局：[LF2 terminal closeout](docs/experiment/2026-09-04-phk-v23-lf2-terminal-closeout.md)
- LF1 终局：[LF1 terminal closeout](docs/experiment/2026-09-03-phk-v23-lf1-terminal-closeout.md)
- LF0 结果：[LF0 terminal closeout](docs/experiment/2026-09-03-phk-v23-lf0-terminal-closeout.md)
- C0 结果：[compatibility closeout](docs/experiment/2026-09-03-phk-v23-c0-reference-discrete-strongform-compatibility-closeout.md)
- 论文历史包：[paper/paper_v22r](paper/paper_v22r/README.md)
- 文档地图：[docs/README.md](docs/README.md)
- 当前研究口径：[CONTEXT.md](CONTEXT.md)
