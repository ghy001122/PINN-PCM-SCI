# PINN-PCM-SCI

面向“物理信息神经网络 × 氧化物/相变材料与器件”的纯软件研究项目。目标是以可复现、证据闭合的方式形成中科院二区定位的论文初稿；这不是期刊接收承诺，合成数值证据也不等于实验验证。

## 当前状态

- `phase_id`: `PHK_V23_R0C_EFFECTIVE_UPDATE_25_V100`
- `lifecycle_state`: `COMPLETE`
- `blocker_id`: `NONE`
- `claim_status`: `V22R_TERMINAL_NO_GO_PRESERVED_R0C_ADAM_PRECONDITIONING_COMPENSATES_RAW_GRADIENT_NO_METHOD_EVIDENCE`
- `next_research_execution_authorized`: `false`

PHK-V2.2R v1.1 的 `MVP_NO_GO_NO_BASIC_COMPETENCE` 与 PHK-V2.3 R0A `R0A_INCONCLUSIVE` 保持冻结。R0B 识别 `GRADIENT_STARVATION` 为最早持续前兆；随后完成的一次性 R0C 25-step V100 reference-blind replay 表明该 raw-gradient 差异被 Adam 在有效相对参数更新上物质补偿，机器裁决为 `R0C_ADAM_PRECONDITIONING_COMPENSATES_RAW_GRADIENT`。因此不应直接把 gradient magnitude rescue 作为首个 R1a。该结果不是因果 root、competence 恢复或方法增益。产物核验后 AutoDL 已关闭，两份 stress references 继续 sealed/unread，下一研究执行未授权。

现有证据支持的核心表述是：在固定单 seed、1000-update、fixed-discretization nominal 协议下，physics-loss 收敛与小的全域平均误差没有构成局域事件 competence 证书。它不表示 PINN 全局失败，不支持 continuum、formal OOD、材料校准或实验主张。

## 当前入口

- 授权边界：[active_phase.md](active_phase.md)
- 已核验状态：[PROJECT_STATE.md](PROJECT_STATE.md)
- 唯一 live plan：[docs/plans/NEXT_ACTIONS.md](docs/plans/NEXT_ACTIONS.md)
- 终局运行记录：[nominal terminal closeout](docs/experiment/2026-08-30-phk-v22r-v11-nominal-terminal-closeout.md)
- R0A 诊断收口：[PHK-V2.3 R0A CPU closeout](docs/experiment/2026-08-30-phk-v23-r0a-cpu-diagnostics-closeout.md)
- 当前 R0B 决定：[ADR 0050](docs/adr/0050-activate-phk-v23-r0b-first-switch-175-minimal-v2.md)
- R0B 云端 run card：[cloud/phk_v23_r0b_autodl](cloud/phk_v23_r0b_autodl/README.md)
- R0B 诊断收口：[PHK-V2.3 R0B closeout](docs/experiment/2026-08-31-phk-v23-r0b-first-switch-175-closeout.md)
- 当前 R0C 决定：[ADR 0051](docs/adr/0051-activate-phk-v23-r0c-effective-update-25-v100.md)
- R0C 云端 run card：[cloud/phk_v23_r0c_autodl](cloud/phk_v23_r0c_autodl/README.md)
- R0C 诊断收口：[PHK-V2.3 R0C closeout](docs/experiment/2026-08-31-phk-v23-r0c-effective-update-25-closeout.md)
- 英文导师初稿与五图复现包：[paper/paper_v22r](paper/paper_v22r/README.md)
- 文档地图：[docs/README.md](docs/README.md)
- 当前研究口径：[CONTEXT.md](CONTEXT.md)

PHK-V2.1 的 `PHK_V21_ORACLE_NO_GO_STOP_BEFORE_PINN`、PHK-V2、V1 与更早历史结果均保持原样。本轮只新增一项边界清楚的 neural Method-MVP 负面证据。
