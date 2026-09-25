# 当前：观测保持相态补全已收口

2026-09-25 用户另行明确授权将本轮重要结果与研究进程提交云端；精简发布范围和核验状态见[发布记录](docs/notes/2026-09-25-observation-preserving-phase-results-release.md)。本次仅更新交付状态，科研仍为 CLOSED，完整数组外部访问仍未闭合。该授权 supersedes 本任务此前 Git 未授权措辞。

**VERIFIED：NO_COMPLETION_INCREMENT。** 阶段0—3完成，N/G/S均未对冻结E29通过原A_w，也均未通过独立D物理资格。N集合误差降低34.209%，但相态RMS增加7.946%；其D内raw相态平方为基点10.287倍、热增加7.324%。不变性质和完整原生数组验证通过，严格双周期仍失败。全部1800 Adam/600完整L-BFGS已完成，实际为同一CPU训练，后续GPU审计/读出；产物已校验回收并关闭实例。见[完整结果](paper/observation_preserving_phase_20260924/results.md)和[实验收口](docs/experiment/2026-09-24-observation-preserving-phase-closeout.md)。

**SUPPORTED_INTERPRETATION：**本轮未建立合格或神经特有补全增量，阶段4条件未触发，停止新增科研计算。理论边界、代码、直接控制及阴性证据可复用；P02方法增量和P03完整数据外部访问仍未补齐。本段supersedes本任务此前准备/执行中状态，下方旧科学结论保留原身份。

- `phase_id`: `PHK_V23_OBSERVATION_PRESERVING_PHASE`
- `lifecycle_state`: `CLOSED`
- `blocker_id`: `NONE`
- `claim_status`: `VERIFIED_OBSERVATION_PRESERVING_PHASE_NO_COMPLETION_INCREMENT`
- `next_research_execution_authorized`: `false`

# 历史收口：相对相态残差与时间矩开发

**VERIFIED：**八臂数值有效且预算完整；所有候选均未对D和P建立原A_w增量。RIM相对D的W相态RMS改善1.918%、S改善2.202%；相对P分别改善2.264%、2.633%，低于原10%门。电热非劣与窗外代价不是此次失败原因。 全部八臂严格双周期未通过；16/32与补充8/16数值检查通过。GPU结果已回收并关机。完整事实见[本轮结果](paper/phase_moments_20260923/results.md)与[实验收口](docs/experiment/2026-09-23-relative-phase-moments-closeout.md)。本段supersedes本轮执行中状态；下方旧B1结论与发布记录保留历史身份。

**SUPPORTED_INTERPRETATION：**本轮没有建立独立相态目标或时间矩增量。按预声明条件停止，不追加确认、调权或训练，不自动转为D_E主导窄稿。原论文的相态PDE贡献与严格事件证据仍未补齐；不同科学假设须另立任务。用户已另行授权并完成[精简成果发布](docs/notes/2026-09-23-phase-moments-results-release.md)，但没有新增科研授权。

- `historical_phase_id`: `PHK_V23_RELATIVE_PHASE_MOMENTS`
- `historical_lifecycle_state`: `CLOSED`
- `historical_blocker_id`: `NONE`
- `historical_claim_status`: `VERIFIED_PHASE_MOMENTS_NO_INCREMENT_WITHIN_SCREEN_BUDGET`
- `historical_next_research_execution_authorized`: `false`

# 历史收口：B1第二周期相态缺测与论文修订

2026-09-22 用户另行授权本轮成果提交云端；发布分支为 `codex/paper-revision-results`，范围和远端核验状态见[发布记录](docs/notes/2026-09-22-b1-sprint-results-release.md)。科研阶段保持CLOSED，完整时空数组仍未公开。

2026-09-22 用户另行授权本轮成果提交云端；发布分支为 `codex/paper-revision-results`，范围和远端核验状态见[发布记录](docs/notes/2026-09-22-b1-sprint-results-release.md)。科研阶段保持CLOSED，完整时空数组仍未公开。

**VERIFIED：**E/D_E的完整A_w通过0/12项参考／读出／seed检查；独立初始化只有两个。相态RMS相对改善范围为-4.231%至1.234%；负值表示E误差更大。窗外非劣代价出现在6/12项检查。 全部七个B1对象在每个参考／读出条件下均未通过完整严格双周期门。 全部冻结科学工作与PDF逐页检查已完成，实际GPU已回收关闭。**SUPPORTED_INTERPRETATION：**未建立对两个seed、三参考和双读出都稳定的额外动态残差增量；保留各项连续收益与失败，不能将不同条件的优点拼接成完整成功。

本段 supersedes 本轮执行中／准备待批状态；历史数值、授权和未执行措辞保留其原阶段身份。结果路由 `PREDECLARED_INCREMENT_NOT_ESTABLISHED`。交付与下一步见本仓库 `paper/paper_revision_20260921/README.md` 和 `docs/experiment/2026-09-21-b1-phase-gap-sprint-closeout.md`。

唯一下一步是作者作论文路线决策：以现有配置收益和条件性消融形成较窄的方法评估稿，或另立具有实质新方法贡献的研究任务。建议先据本轮完整证据评估较窄成稿的可投性；若继续以更强方法创新为目标，应单独设计并批准新任务。本轮不自动降级原研究目标，也不追加救援训练。

- `historical_phase_id`: `PHK_V23_B1_SECOND_CYCLE_PHASE_GAP`
- `historical_lifecycle_state`: `CLOSED`
- `historical_blocker_id`: `NONE`
- `historical_claim_status`: `VERIFIED_B1_PREDECLARED_INCREMENT_NOT_ESTABLISHED`
- `historical_next_research_execution_authorized`: `false`

# PINN-PCM-SCI

## 历史：共同读出、干净PDE消融与投稿修订成果发布

**VERIFIED：**四组E/F完整器件优势在三套参考、两种共同电学读出网格下均保留；两个干净D_E对照未证明剩余热／相态PDE的独立收益。原协议seed43对B_E在空间参考、细读出下失去器件优势门，反例完整保留。结果见[发布总结](docs/notes/2026-09-20-readout-clean-pde-results-release.md)、[完整修订稿](paper/paper_revision_20260918/README.md)和[科学终局](docs/experiment/2026-09-18-readout-clean-pde-revision-closeout.md)。

2026-09-20用户另行授权重要结果提交云端；发布分支为`codex/paper-revision-results`。精简证据、源码和稿件纳入此次发布，完整大型数组仍本地分包保存。科学执行保持CLOSED；本次无新增计算或实际投稿。GPU已按完成记录关闭。作者事实、目标期刊、完整数据公开及最终作者批准仍需落实。下方旧权限、未发布措辞及数值按各自历史阶段理解。

**2026-09-18发布与第二轮审核：**用户另行授权近期成果提交云端及academic-research-suite全面复审。[发布范围与重要结果](docs/notes/2026-09-18-revision-results-release.md)、[新Revision Roadmap](paper/review_20260917_round2/Revision_Roadmap.md)记录本次交付。科学阶段仍CLOSED，无新增训练/推理/求解授权；先前“未发布”措辞保留其历史阶段身份。公开包是精简证据，不含全部数组。

## 历史：固定预测空间参考与优先修订已完成

**VERIFIED：**2026-09-17按用户批准的[实施方案](paper/review_20260917/Implementation_Plan.md)，完成两个既有协议的240×120、dt=0.0003125参考，共16000主步、170979内部线性解。16套预测与原电学读出固定，四组E/F完整器件优势在原、时间细化、空间参考下均保持。实际证据见[终局](docs/experiment/2026-09-17-fixed-prediction-spatial-reference-closeout.md)。

**VERIFIED：**三项历史A/B随空间参考改变：original/29对B_E及shorter/43对F的相态判据失去通过；original/43对B_E器件判据从未过变为通过。空间参考下16对象均无严格双周期通过；shorter/43/E_I的第一周期recall由时间参考下0.902063降至0.897527。原阈值、预测及旧结论均未改写。

**SUPPORTED_INTERPRETATION：**核心器件收益在所测数值参考改变下保持，部分阈值结论需收窄。**UNKNOWN：**空间收敛、连续体精度、预测电学读出网格独立性、剩余PDE独立必要性、孤立VJP因果与材料验证。本轮零新训练/模型前反向/预测电学重求解，不读stress、未启GPU、未发布Git。

[完整修订稿](paper/paper_revision_20260917/README.md)为正文21页、补充35页；[逐项Revision响应](paper/review_20260917/Roadmap_Execution_Report.md)记录全部落实及作者待办。本轮有界执行已关闭，无自动追加科研授权；下方保留各轮历史身份。

## 历史已完成：相态网络反事实、时间参考补证与论文修订

**VERIFIED：**按[用户完整指令](docs/notes/2026-09-16-phase-adapter-authorized-sprint.md)，六个耦合PINN终点、两条时间细化参考、16套固定预测的两参考评分及一次干净归档复算均已完成。实际GPU已回收关机。本轮3600 Adam、600完整评估；参考16000主步、170722内部线性解，均在预算内。没有读取stress、重推旧模型或自动Git/公开上传。

**VERIFIED：**历史四组E/F器件优势与全部历史A/B裁决在此次时间细化下保持。新E_R/E_I对继续训练E_C均未建立A/B增量；仅E_I/seed43在细化参考下跨严格双周期门，旧参考不通过。此参考特定信号不证明稳定严格能力，也不支持把门控升级为已验证核心创新。

完整交付：[修订稿、正文/PDF、补充与图表](paper/paper_revision_20260916/README.md)；[科研终局和下一步](docs/experiment/2026-09-16-phase-adapter-reference-closeout.md)。时间参考补证已完成；剩余PDE独立必要性、空间收敛、材料验证和参考稳定的严格能力仍UNKNOWN。后续新科学执行保持PROPOSED_NOT_AUTHORIZED。

以下保留此前各轮的完成记录及当时授权身份；本轮不覆盖历史结果。

保留投稿候选稿：[paper_submission](paper/paper_submission/README.md)，含完整英文正文、可审阅PDF、六组主图、统一数表与合并补充材料。2026-09-16按用户Paper_Sprint授权完成已有证据成稿与报告性分析，零新训练/模型推理/求解，未启GPU；成稿阶段未执行Git发布。

用户随后另行授权本包提交云端及[论文改进独立评估交接](docs/notes/2026-09-16-paper-submission-cloud-review-handoff.md)。本包发布分支为`codex/paper-submission-results`，继承V32；实际发布提交以交付消息和远端分支为准。评估重点为固定模型参考敏感性、严格事件、剩余PDE独立贡献与材料关联，不授权新科研执行。

保留研究快照：[paper_v32](paper/paper_v32/README.md)。完整新脉冲协议与两个全新初始化配对已完成，GPU已回收关闭；[终局](docs/experiment/2026-09-15-phk-v23-lf11-protocol-terminal-closeout.md)与[下一计划](docs/plans/NEXT_ACTIONS.md)给出科学边界和待批项。

V32发布分支：`codex/v32-research-results`；[云端独立复评交接](docs/notes/2026-09-16-lf11-v32-results-cloud-review-handoff.md)汇总新增成果、历史反证和论文优先问题。用户于2026-09-16另行授权成果发布与评估交付，不产生新的科研执行授权。

继承稿：[paper_v31](paper/paper_v31/README.md)。全网格反事实及原协议两个全新初始化配对均已完成；[V31云端复评交接](docs/notes/2026-09-15-lf11-v31-results-cloud-review-handoff.md)保留当时证据与未决问题。

PINN × 相变材料与器件的纯软件研究；当前对象为二维合成、无量纲电—热—相态wall-cell，尚非实验标定氧化物器件。

VERIFIED：新协议中两个初始化的E均对锁定soft＋相同电学重求解和同层B_E通过原A/B；相对soft的phase误差下降20.22%/20.31%，功率误差下降57.21%/78.26%。严格双周期仍受第一周期recall限制，剩余热/phase PDE独立必要性未建立。跨协议数表与事件见[项目状态](PROJECT_STATE.md)；原协议seed43的B_E门不足等旧结果保留。新case为使用自身观测的重建/适配，不称零样本泛化。

## 当前状态

- `historical_phase_id`: `PHK_V23_READOUT_AND_CLEAN_PDE_REVISION`
- `historical_lifecycle_state`: `CLOSED`
- `historical_blocker_id`: `NONE`
- `historical_claim_status`: `VERIFIED_READOUT_ROBUST_CLEAN_PDE_ABLATION_BOUNDED`
- `historical_next_research_execution_authorized`: `false`

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
- 当前论文：[网络实验与参考补证修订稿](paper/paper_revision_20260916/README.md)；保留[原投稿稿](paper/paper_submission/README.md)与[paper_v32](paper/paper_v32/README.md)、[数值复现](paper/paper_v32/reproduction.md)
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
