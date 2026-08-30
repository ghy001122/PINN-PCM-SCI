# PINN-PCM-SCI

面向“物理信息神经网络 × 氧化物/相变材料与器件”的纯软件研究项目。目标是以可复现、证据闭合的方式形成中科院二区定位的论文初稿；这不是期刊接收承诺，合成数值证据也不等于实验验证。

## 当前状态

- `phase_id`: `PHK_V23_R0A_CPU_DIAGNOSTICS_AND_CONTRACT`
- `lifecycle_state`: `COMPLETE`
- `blocker_id`: `NONE`
- `claim_status`: `V22R_TERMINAL_NO_GO_PRESERVED_R0A_INCONCLUSIVE_NO_METHOD_EVIDENCE`
- `next_research_execution_authorized`: `false`

PHK-V2.2R v1.1 的 `MVP_NO_GO_NO_BASIC_COMPETENCE` 保持冻结。PHK-V2.3 R0A 已在本地 CPU/FP64 上完成一次只读诊断，裁决为 `R0A_INCONCLUSIVE`：final checkpoint 存在低 electrothermal state、无正 phase growth 与 phase-head 强梯度冲突，但 teacher substitutions 未达到预声明数量级门，不能确定 primary root cause。未训练、未更新参数、未使用 GPU、未读 stress，也没有正向方法结果。

现有证据支持的核心表述是：在固定单 seed、1000-update、fixed-discretization nominal 协议下，physics-loss 收敛与小的全域平均误差没有构成局域事件 competence 证书。它不表示 PINN 全局失败，不支持 continuum、formal OOD、材料校准或实验主张。

## 当前入口

- 授权边界：[active_phase.md](active_phase.md)
- 已核验状态：[PROJECT_STATE.md](PROJECT_STATE.md)
- 唯一 live plan：[docs/plans/NEXT_ACTIONS.md](docs/plans/NEXT_ACTIONS.md)
- 终局运行记录：[nominal terminal closeout](docs/experiment/2026-08-30-phk-v22r-v11-nominal-terminal-closeout.md)
- R0A 诊断收口：[PHK-V2.3 R0A CPU closeout](docs/experiment/2026-08-30-phk-v23-r0a-cpu-diagnostics-closeout.md)
- 英文导师初稿与五图复现包：[paper/paper_v22r](paper/paper_v22r/README.md)
- 文档地图：[docs/README.md](docs/README.md)
- 当前研究口径：[CONTEXT.md](CONTEXT.md)

PHK-V2.1 的 `PHK_V21_ORACLE_NO_GO_STOP_BEFORE_PINN`、PHK-V2、V1 与更早历史结果均保持原样。本轮只新增一项边界清楚的 neural Method-MVP 负面证据。
