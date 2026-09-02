# PINN-PCM-SCI

面向“物理信息神经网络 × 氧化物相变材料与器件”的纯软件研究项目。目标是形成证据闭合、可复现、达到中科院二区定位的论文初稿；这不是期刊接收承诺，合成数值证据也不等于实验验证。

## 当前状态

- `phase_id`: `PHK_V23_R1X_BOUNDED_CLEAN_COUPLING_CAMPAIGN_EXECUTE`
- `lifecycle_state`: `COMPLETE`
- `blocker_id`: `R1X_E1_DEPLOYMENT_TRANSITIVE_IDENTITY_INCOMPLETE_RETRY_EXHAUSTED`
- `claim_status`: `V22R_TERMINAL_NO_GO_AND_R1A_NO_COMPETENCE_PRESERVED_R1X_ENGINEERING_BLOCKED_NO_SCIENTIFIC_EVIDENCE`
- `next_research_execution_authorized`: `false`

PHK-V2.2R 的 `MVP_NO_GO_NO_BASIC_COMPETENCE` 与 R0A/R0B/R0C/R1a 结果保持冻结。R1X E1 首次启动和唯一 engineering retry 均在模型构造前因隔离部署的传递身份依赖不完整而 fail-closed；没有科学 trajectory、optimizer update、checkpoint、prediction 或 nominal evaluation。AutoDL 已关闭并验证，campaign 终止为 `ENGINEERING_BLOCKED`，下一科研执行未授权。两份 stress references 继续 sealed/unread。

## 当前入口

- 授权边界：[active_phase.md](active_phase.md)
- 已核验状态：[PROJECT_STATE.md](PROJECT_STATE.md)
- 唯一 live plan：[docs/plans/NEXT_ACTIONS.md](docs/plans/NEXT_ACTIONS.md)
- 当前决定：[ADR 0053](docs/adr/0053-activate-phk-v23-r1x-bounded-clean-coupling-campaign.md)
- 当前终局记录：[R1X engineering-blocked closeout](docs/experiment/2026-09-02-phk-v23-r1x-engineering-blocked-closeout.md)
- R1a 历史结果：[R1a closeout](docs/experiment/2026-08-31-phk-v23-r1a-config-closeout.md)
- V2.2R 终局结果：[nominal terminal closeout](docs/experiment/2026-08-30-phk-v22r-v11-nominal-terminal-closeout.md)
- 论文历史包：[paper/paper_v22r](paper/paper_v22r/README.md)
- 文档地图：[docs/README.md](docs/README.md)
- 当前研究口径：[CONTEXT.md](CONTEXT.md)
