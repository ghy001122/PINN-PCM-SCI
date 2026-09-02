# PINN-PCM-SCI

面向“物理信息神经网络 × 氧化物相变材料与器件”的纯软件研究项目。目标是形成证据闭合、可复现、达到中科院二区定位的论文初稿；这不是期刊接收承诺，合成数值证据也不等于实验验证。

## 当前状态

- `phase_id`: `PHK_V23_R1X_BOUNDED_CLEAN_COUPLING_CAMPAIGN_EXECUTE`
- `lifecycle_state`: `ACTIVE`
- `blocker_id`: `NONE_VERIFIED_ENGINEERING_REPAIR_COMPLETE`
- `claim_status`: `V22R_TERMINAL_NO_GO_AND_R1A_NO_COMPETENCE_PRESERVED_R1X_ENGINEERING_BLOCKED_NO_SCIENTIFIC_EVIDENCE`
- `next_research_execution_authorized`: `true`

PHK-V2.2R 的 `MVP_NO_GO_NO_BASIC_COMPETENCE` 与 R0A/R0B/R0C/R1a 结果保持冻结。R1X E1 的两次历史工程启动均在模型构造前 fail-closed，科学轨迹计数仍为 0；传递部署依赖现已闭合并通过隔离回归。用户已明确覆盖旧 engineering-retry 次数限制并授权恢复原 E1；科学身份、三条 exploration/一条 confirmation 上限和两份 sealed/unread stress references 均不变。

## 当前入口

- 授权边界：[active_phase.md](active_phase.md)
- 已核验状态：[PROJECT_STATE.md](PROJECT_STATE.md)
- 唯一 live plan：[docs/plans/NEXT_ACTIONS.md](docs/plans/NEXT_ACTIONS.md)
- 当前恢复决定：[ADR 0054](docs/adr/0054-resume-r1x-after-verified-engineering-repair.md)
- 原 campaign 决定：[ADR 0053](docs/adr/0053-activate-phk-v23-r1x-bounded-clean-coupling-campaign.md)
- 历史工程阻塞记录：[R1X engineering-blocked closeout](docs/experiment/2026-09-02-phk-v23-r1x-engineering-blocked-closeout.md)
- R1a 历史结果：[R1a closeout](docs/experiment/2026-08-31-phk-v23-r1a-config-closeout.md)
- V2.2R 终局结果：[nominal terminal closeout](docs/experiment/2026-08-30-phk-v22r-v11-nominal-terminal-closeout.md)
- 论文历史包：[paper/paper_v22r](paper/paper_v22r/README.md)
- 文档地图：[docs/README.md](docs/README.md)
- 当前研究口径：[CONTEXT.md](CONTEXT.md)
