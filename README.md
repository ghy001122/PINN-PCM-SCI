# PINN-PCM-SCI

面向“物理信息神经网络 × 氧化物/相变材料与器件”的纯软件研究项目。目标是以可复现、证据闭合的方式形成中科院二区定位的论文初稿；这不是期刊接收承诺，合成数值证据也不等于实验验证。

## 当前状态

- `phase_id`: `PHK_V23_R1A_CONFIG_COMPETENCE_RECOVERY`
- `lifecycle_state`: `AWAITING`
- `blocker_id`: `AUTODL_ENDPOINT_OR_PRICE`
- `claim_status`: `V22R_TERMINAL_NO_GO_PRESERVED_R1A_INFRASTRUCTURE_BLOCKED_NO_SCIENTIFIC_RUN`
- `next_research_execution_authorized`: `false`

PHK-V2.2R v1.1 的 `MVP_NO_GO_NO_BASIC_COMPETENCE` 与 PHK-V2.3 R0A/R0B/R0C 结果保持冻结。R1a 合同、实现、测试与部署 bundle 已就绪，但已知 AutoDL SSH endpoint 连续两次 `Connection refused`，实时页面价格也不可取得，因此唯一科学 run 尚未消耗。等待用户启动实例并提供当前 endpoint 与价格；两份 stress references 继续 sealed/unread。

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
- 当前 R1a 决定：[ADR 0052](docs/adr/0052-activate-phk-v23-r1a-config-competence-recovery.md)
- R1a 云端 run card：[cloud/phk_v23_r1a_config_autodl](cloud/phk_v23_r1a_config_autodl/README.md)
- 英文导师初稿与五图复现包：[paper/paper_v22r](paper/paper_v22r/README.md)
- 文档地图：[docs/README.md](docs/README.md)
- 当前研究口径：[CONTEXT.md](CONTEXT.md)

PHK-V2.1 的 `PHK_V21_ORACLE_NO_GO_STOP_BEFORE_PINN`、PHK-V2、V1 与更早历史结果均保持原样。本轮只新增一项边界清楚的 neural Method-MVP 负面证据。
