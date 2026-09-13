# PINN-PCM-SCI

PINN × 相变材料与器件的纯软件研究；当前对象为二维合成、无量纲电—热—相态wall-cell，尚非实验标定氧化物器件。

## 当前状态

- `phase_id`: `PHK_V23_LF11_REMAINING_PDE_COUNTERFACTUAL_COMPLETE`
- `lifecycle_state`: `COMPLETE`
- `blocker_id`: `NONE`
- `claim_status`: `VALID_MEASURED_PDE_INFLUENCE_NO_MATCHED_PREDICTIVE_INCREMENT`
- `next_research_execution_authorized`: `false`

VERIFIED：本轮 D_C/P1/P_kappa 固定目标反事实已完整完成，未通过冻结的剩余 PDE 独立预测增量。共同父態的完整剩余 PDE 梯度为规定尺度的0.1077%，触发参考盲 kappa=92.84049；完整执行与科学解释见[终局](docs/experiment/2026-09-13-phk-v23-lf11-remaining-pde-terminal-closeout.md)。这不是仅凭小 loss 推断作用，也不把一次调权当作创新。

实际 669 次完整评估、零 Adam、29882 次训练正解与 29882 次伴随；当前 GPU 已回收关闭并确认，之后才本地评分。[paper_v29](paper/paper_v29/README.md)包含英文初稿、四组图、完整数表、主张矩阵和接受优化状态。用户已另行授权本轮重要成果发布及[V29 云端独立复评交接](docs/notes/2026-09-13-lf11-v29-results-cloud-review-handoff.md)，发布版本以本包所属提交和交付消息为准。下一方案为[PROPOSED_NOT_AUTHORIZED](docs/plans/NEXT_ACTIONS.md)。

保留 V28：D_E/P_E 均胜同电学层 B_E，但原 P_E−D_E 未通过匹配 A/B。电学接口修复、强基线收益、剩余 PDE 独立增量和消元必要性是不同证据层；新结论不改写旧终局。

## 当前入口

- 最新终局：[剩余 PDE 固定目标反事实](docs/experiment/2026-09-13-phk-v23-lf11-remaining-pde-terminal-closeout.md)
- 保留 V28：[电学消元与同层强基线](docs/experiment/2026-09-13-phk-v23-lf11-electrical-elimination-terminal-closeout.md)
- 当前论文：[paper_v29](paper/paper_v29/README.md)、[复现](paper/paper_v29/reproducibility.md)
- 保留 V27：[同父三臂与电学归一化](docs/experiment/2026-09-12-phk-v23-lf11-joint-terminal-closeout.md)、[论文](paper/paper_v27/README.md)
- 本轮云端复评与下一步规划请求：[V27 交接](docs/notes/2026-09-12-lf11-v27-results-cloud-review-handoff.md)
- 保留上轮：[V-only终局](docs/experiment/2026-09-12-phk-v23-lf11-v-continuation-terminal-closeout.md)、[paper_v26](paper/paper_v26/README.md)
- 上轮云端复评交接：[V26交接](docs/notes/2026-09-12-lf11-v26-results-cloud-review-handoff.md)

- LF11后续终局：[closeout](docs/experiment/2026-09-12-phk-v23-lf11-followup-terminal-closeout.md)
- 保留论文：[paper_v25](paper/paper_v25/README.md)
- 授权边界：[active_phase.md](active_phase.md)
- 已核验状态：[PROJECT_STATE.md](PROJECT_STATE.md)
- 唯一 live plan：[docs/plans/NEXT_ACTIONS.md](docs/plans/NEXT_ACTIONS.md)
- LF11终局：[terminal closeout](docs/experiment/2026-09-11-phk-v23-lf11-terminal-closeout.md)
- 上轮论文快照与图表：[paper/paper_v24](paper/paper_v24/README.md)
- LF10 关闭决定：[ADR 0074](docs/adr/0074-close-phk-v23-lf10-feasible-direction-replication.md)
- LF10 终局：[terminal closeout](docs/experiment/2026-09-09-phk-v23-lf10-terminal-closeout.md)
- LF10 激活决定：[ADR 0073](docs/adr/0073-activate-phk-v23-lf10-feasible-direction-replication.md)
- LF10 CPU 资格：[CPU qualification](docs/experiment/2026-09-09-phk-v23-lf10-cpu-qualification.md)
- LF9关闭决定：[ADR 0072](docs/adr/0072-close-phk-v23-lf9-equation-routed-thermal-cv-refinement.md)
- LF9 终局：[terminal closeout](docs/experiment/2026-09-08-phk-v23-lf9-terminal-closeout.md)
- LF9 激活决定：[ADR 0071](docs/adr/0071-activate-phk-v23-lf9-equation-routed-thermal-cv-refinement.md)
- LF9 CPU 资格：[CPU qualification](docs/experiment/2026-09-08-phk-v23-lf9-cpu-qualification.md)
- LF8关闭决定：[ADR 0070](docs/adr/0070-close-phk-v23-lf8-competence-filter-completion.md)
- LF8 终局：[terminal closeout](docs/experiment/2026-09-08-phk-v23-lf8-terminal-closeout.md)
- LF8 激活决定：[ADR 0069](docs/adr/0069-activate-phk-v23-lf8-competence-filter-completion.md)
- LF8 CPU 资格：[CPU qualification](docs/experiment/2026-09-08-phk-v23-lf8-cpu-qualification.md)
- LF7关闭决定：[ADR 0068](docs/adr/0068-close-phk-v23-lf7-competence-filtered-refinement.md)
- LF7 终局：[terminal closeout](docs/experiment/2026-09-07-phk-v23-lf7-terminal-closeout.md)
- LF7 激活决定：[ADR 0067](docs/adr/0067-activate-phk-v23-lf7-competence-filtered-refinement.md)
- LF7 CPU 资格：[CPU qualification](docs/experiment/2026-09-07-phk-v23-lf7-cpu-qualification.md)
- LF7 prior art：[constrained-refinement prior-art closure](docs/references/2026-09-07-phk-v23-lf7-constrained-refinement-prior-art.md)
- 上一关闭决定：[ADR 0066](docs/adr/0066-close-phk-v23-lf6-event-frontier-pilot.md)
- LF6 终局：[terminal closeout](docs/experiment/2026-09-06-phk-v23-lf6-terminal-closeout.md)
- 上一关闭决定：[ADR 0064](docs/adr/0064-close-phk-v23-lf5-temporal-zero-level-pilot.md)
- LF5 终局：[terminal closeout](docs/experiment/2026-09-05-phk-v23-lf5-terminal-closeout.md)
- LF5 激活决定：[ADR 0063](docs/adr/0063-activate-phk-v23-lf5-temporal-zero-level-pilot.md)
- LF5 CPU-T：[CPU-T qualification](docs/experiment/2026-09-05-phk-v23-lf5-cpu-qualification.md)
- LF4 关闭决定：[ADR 0062](docs/adr/0062-close-phk-v23-lf4-interface-band-pilot.md)
- LF4 终局：[terminal closeout](docs/experiment/2026-09-05-phk-v23-lf4-terminal-closeout.md)
- LF4 CPU 资格：[CPU-G qualification](docs/experiment/2026-09-05-phk-v23-lf4-cpu-qualification.md)
- 上一阶段：[LF3 terminal closeout](docs/experiment/2026-09-05-phk-v23-lf3-terminal-closeout.md)
- 保留论文快照：[paper/paper_v23](paper/paper_v23/README.md)
- 上一关闭决定：[ADR 0060](docs/adr/0060-close-phk-v23-lf3-carrier-not-established.md)
- LF2 终局：[LF2 terminal closeout](docs/experiment/2026-09-04-phk-v23-lf2-terminal-closeout.md)
- LF1 终局：[LF1 terminal closeout](docs/experiment/2026-09-03-phk-v23-lf1-terminal-closeout.md)
- LF0 结果：[LF0 terminal closeout](docs/experiment/2026-09-03-phk-v23-lf0-terminal-closeout.md)
- C0 结果：[compatibility closeout](docs/experiment/2026-09-03-phk-v23-c0-reference-discrete-strongform-compatibility-closeout.md)
- 上一论文包：[paper/paper_v22r](paper/paper_v22r/README.md)
- 文档地图：[docs/README.md](docs/README.md)
- 当前研究口径：[CONTEXT.md](CONTEXT.md)

## 历史 V28 执行与发布记录

[完整指令](docs/notes/2026-09-13-lf11-elimination-authorized-sprint.md)已完成；P_F 的冻结条件为 false。实际实例已关闭并确认，随后本地评分。当前结果和接受优化状态均已保存；用户随后明确授权本轮提交、推送及[云端独立复评交接](docs/notes/2026-09-13-lf11-v28-results-cloud-review-handoff.md)。此发布不产生下一研究执行授权；实际远端版本由交付消息提供。
