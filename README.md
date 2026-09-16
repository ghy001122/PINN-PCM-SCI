# PINN-PCM-SCI

最新投稿候选稿：[paper_submission](paper/paper_submission/README.md)，含完整英文正文、可审阅PDF、六组主图、统一数表与合并补充材料。2026-09-16按用户Paper_Sprint授权完成已有证据成稿与报告性分析，零新训练/模型推理/求解，未启GPU；成稿阶段未执行Git发布。

用户随后另行授权本包提交云端及[论文改进独立评估交接](docs/notes/2026-09-16-paper-submission-cloud-review-handoff.md)。本包发布分支为`codex/paper-submission-results`，继承V32；实际发布提交以交付消息和远端分支为准。评估重点为固定模型参考敏感性、严格事件、剩余PDE独立贡献与材料关联，不授权新科研执行。

保留研究快照：[paper_v32](paper/paper_v32/README.md)。完整新脉冲协议与两个全新初始化配对已完成，GPU已回收关闭；[终局](docs/experiment/2026-09-15-phk-v23-lf11-protocol-terminal-closeout.md)与[下一计划](docs/plans/NEXT_ACTIONS.md)给出科学边界和待批项。

V32发布分支：`codex/v32-research-results`；[云端独立复评交接](docs/notes/2026-09-16-lf11-v32-results-cloud-review-handoff.md)汇总新增成果、历史反证和论文优先问题。用户于2026-09-16另行授权成果发布与评估交付，不产生新的科研执行授权。

继承稿：[paper_v31](paper/paper_v31/README.md)。全网格反事实及原协议两个全新初始化配对均已完成；[V31云端复评交接](docs/notes/2026-09-15-lf11-v31-results-cloud-review-handoff.md)保留当时证据与未决问题。

PINN × 相变材料与器件的纯软件研究；当前对象为二维合成、无量纲电—热—相态wall-cell，尚非实验标定氧化物器件。

VERIFIED：新协议中两个初始化的E均对锁定soft＋相同电学重求解和同层B_E通过原A/B；相对soft的phase误差下降20.22%/20.31%，功率误差下降57.21%/78.26%。严格双周期仍受第一周期recall限制，剩余热/phase PDE独立必要性未建立。跨协议数表与事件见[项目状态](PROJECT_STATE.md)；原协议seed43的B_E门不足等旧结果保留。新case为使用自身观测的重建/适配，不称零样本泛化。

## 当前状态

- `phase_id`: `PHK_V23_LF11_NEW_PROTOCOL_COMPLETE`
- `lifecycle_state`: `COMPLETE`
- `blocker_id`: `NONE`
- `claim_status`: `VALID_NEW_PROTOCOL_TWO_CLEAN_PAIRS_COMPLETE`
- `next_research_execution_authorized`: `false`

历史V30（VERIFIED）：E对两种有效F/projected均通过同一器件功能层B；底部电流/功率误差分别下降35.22%/35.99%与56.85%/58.70%。当时A与严格双周期未全过，剩余热/phase PDE独立必要性和独立初始化稳健性仍UNKNOWN。用户于2026-09-14另行授权成果发布及[V30云端独立复评](docs/notes/2026-09-14-lf11-v30-results-cloud-review-handoff.md)，随后另行授权F_full与条件确认；其新结果以V31为准。

## 保留V29历史结果

VERIFIED：V29的D_C/P1/P_kappa固定目标反事实已完整完成，未通过冻结的剩余 PDE 独立预测增量。共同父態的完整剩余 PDE 梯度为规定尺度的0.1077%，触发参考盲 kappa=92.84049；完整执行与科学解释见[终局](docs/experiment/2026-09-13-phk-v23-lf11-remaining-pde-terminal-closeout.md)。这不是仅凭小 loss 推断作用，也不把一次调权当作创新。

实际 669 次完整评估、零 Adam、29882 次训练正解与 29882 次伴随；当前 GPU 已回收关闭并确认，之后才本地评分。[paper_v29](paper/paper_v29/README.md)包含英文初稿、四组图、完整数表、主张矩阵和接受优化状态。用户已另行授权本轮重要成果发布及[V29 云端独立复评交接](docs/notes/2026-09-13-lf11-v29-results-cloud-review-handoff.md)，发布版本以本包所属提交和交付消息为准。下一方案为[PROPOSED_NOT_AUTHORIZED](docs/plans/NEXT_ACTIONS.md)。

保留 V28：D_E/P_E 均胜同电学层 B_E，但原 P_E−D_E 未通过匹配 A/B。电学接口修复、强基线收益、剩余 PDE 独立增量和消元必要性是不同证据层；新结论不改写旧终局。

## 当前入口

- 最新V32：[完整新脉冲确认](paper/paper_v32/README.md)、[终局](docs/experiment/2026-09-15-phk-v23-lf11-protocol-terminal-closeout.md)
- 保留V31：[全网格反事实](paper/paper_v31/README.md)、[终局](docs/experiment/2026-09-14-phk-v23-lf11-fullgrid-terminal-closeout.md)

- 保留V30：[训练期电学耦合与事后修复](docs/experiment/2026-09-13-phk-v23-lf11-training-coupling-terminal-closeout.md)
- 保留V29：[剩余 PDE 固定目标反事实](docs/experiment/2026-09-13-phk-v23-lf11-remaining-pde-terminal-closeout.md)
- 保留 V28：[电学消元与同层强基线](docs/experiment/2026-09-13-phk-v23-lf11-electrical-elimination-terminal-closeout.md)
- 当前论文：[投稿候选稿与合并补充](paper/paper_submission/README.md)；保留[paper_v32](paper/paper_v32/README.md)、[数值复现](paper/paper_v32/reproduction.md)
- 历史V30：[paper_v30](paper/paper_v30/README.md)、[复现](paper/paper_v30/reproducibility.md)
- 保留 V27：[同父三臂与电学归一化](docs/experiment/2026-09-12-phk-v23-lf11-joint-terminal-closeout.md)、[论文](paper/paper_v27/README.md)
- 本轮云端复评与论文改进请求：[投稿候选稿交接](docs/notes/2026-09-16-paper-submission-cloud-review-handoff.md)；保留[V30交接](docs/notes/2026-09-14-lf11-v30-results-cloud-review-handoff.md)
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
