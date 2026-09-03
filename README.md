# PINN-PCM-SCI

面向“物理信息神经网络 × 氧化物相变材料与器件”的纯软件研究项目。目标是形成证据闭合、可复现、达到中科院二区定位的论文初稿；这不是期刊接收承诺，合成数值证据也不等于实验验证。

## 当前状态

- `phase_id`: `PHK_V23_R1X_BOUNDED_CLEAN_COUPLING_CAMPAIGN_EXECUTE`
- `lifecycle_state`: `COMPLETE`
- `blocker_id`: `PURE_SCRATCH_COMPETENCE_RECOVERY_FAILED`
- `claim_status`: `V22R_TERMINAL_NO_GO_AND_R1A_NO_COMPETENCE_PRESERVED_R1X_PURE_SCRATCH_COMPETENCE_RECOVERY_FAILED`
- `next_research_execution_authorized`: `false`

PHK-V2.2R 的 `MVP_NO_GO_NO_BASIC_COMPETENCE` 与 R0A/R0B/R0C/R1a 结果保持冻结。R1X 已执行两条 non-voting pure-scratch explorations：E1 clean-coupling 与 E2 top-Dirichlet hard lift 均在 step 300 未通过两窗 ROI readiness；E2 虽改善电热驱动并精确满足 top potential boundary，仍没有 material phase signal或两周期 competence。冻结机器树禁止 E3/confirmation，campaign 终局为 `PURE_SCRATCH_COMPETENCE_RECOVERY_FAILED`。两份 stress references 继续 sealed/unread。

当前没有新科研执行授权。low-fidelity-guided route 需要新合同与新 `EXECUTE`。本次用户明确要求保留 AutoDL，实例当前在线但 GPU 空闲、无 R1X 训练进程；未来默认仍为使用完 GPU 后及时关机，除非用户明确覆盖。

## 当前入口

- 授权边界：[active_phase.md](active_phase.md)
- 已核验状态：[PROJECT_STATE.md](PROJECT_STATE.md)
- 唯一 live plan：[docs/plans/NEXT_ACTIONS.md](docs/plans/NEXT_ACTIONS.md)
- R1X 最终结果：[E2/campaign closeout](docs/experiment/2026-09-03-phk-v23-r1x-e2-pure-scratch-stop-closeout.md)
- E1 结果：[R1X E1 closeout](docs/experiment/2026-09-03-phk-v23-r1x-e1-et-not-ready-closeout.md)
- 当前恢复决定：[ADR 0054](docs/adr/0054-resume-r1x-after-verified-engineering-repair.md)
- 原 campaign 决定：[ADR 0053](docs/adr/0053-activate-phk-v23-r1x-bounded-clean-coupling-campaign.md)
- 历史工程阻塞记录：[R1X engineering-blocked closeout](docs/experiment/2026-09-02-phk-v23-r1x-engineering-blocked-closeout.md)
- R1a 历史结果：[R1a closeout](docs/experiment/2026-08-31-phk-v23-r1a-config-closeout.md)
- V2.2R 终局结果：[nominal terminal closeout](docs/experiment/2026-08-30-phk-v22r-v11-nominal-terminal-closeout.md)
- 论文历史包：[paper/paper_v22r](paper/paper_v22r/README.md)
- 文档地图：[docs/README.md](docs/README.md)
- 当前研究口径：[CONTEXT.md](CONTEXT.md)
