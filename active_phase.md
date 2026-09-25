<!-- WA_CURRENT_BEGIN -->
# 当前：连续主稿与固定温度条件演化

W连续主稿与完整补充材料已完成；A两条轨迹完成并通过数值资格，两热口径及开发参考方向支持后续证人搜索，但原C²修正族可行性仍为UNKNOWN。结果已回收核验、实例已关闭。无自动A+或新训练。

任务 `PCM-20260925-INTEGRATED-MANUSCRIPT-FEASIBILITY-02` 已由用户明确批准实施 W+A，见[授权与边界](docs/notes/2026-09-25-integrated-manuscript-conditional-ivp-authorized.md)及[本轮交付](paper/paper_revision_20260925_integrated/README.md)。本段 supersedes 下方旧任务的当前状态；旧结果不变。仅至多两条条件轨迹，无新训练、电学求解、参考生成或自动 A+。用户随后明确授权本轮成果提交云端，见[发布记录](docs/notes/2026-09-25-integrated-manuscript-conditional-ivp-release.md)；该授权 supersedes 此前本轮 Git 未授权措辞，不扩展科研授权。

- `phase_id`: `PHK_V23_INTEGRATED_MANUSCRIPT_CONDITIONAL_IVP`
- `lifecycle_state`: `CLOSED`
- `blocker_id`: `NONE`
- `claim_status`: `WA_COMPLETE_CONDITIONAL_IVP_SUPPORTS_FURTHER_WITNESS_SEARCH_ORIGINAL_FAMILY_UNKNOWN`
- `next_research_execution_authorized`: `false`

<!-- WA_CURRENT_END -->

# 历史：物理目标、采样与固定温度诊断已完成

**VERIFIED：** 四个保存状态的零更新诊断完成，确认标量目标/独立资格不一致及空间采样敏感；固定T的严格热一致性存在范围/端点障碍，原5%容限下能否有效补全仍 **UNKNOWN**。见[诊断结果、图表及唯一后续决策](paper/observation_preserving_phase_20260924/physics-objective-diagnostic.md)。V100诊断112.589秒，零参数更新/电学求解/参考场读取；结果已回收，实例已关闭。

用户2026-09-25指定交接任务已收口；历史 NO_COMPLETION_INCREMENT 与E/F正向结果保持。新训练和条件相态推进未执行或追加授权；用户随后明确授权本轮诊断成果提交云端，见[发布记录](docs/notes/2026-09-25-physics-objective-diagnostic-release.md)。P02/P03仍开放。

- `historical_phase_id`: `PHK_V23_PHYSICS_OBJECTIVE_FEASIBILITY`
- `historical_lifecycle_state`: `CLOSED`
- `historical_blocker_id`: `NONE`
- `historical_claim_status`: `VERIFIED_OBJECTIVE_MISMATCH_SAMPLING_SENSITIVITY_FIXED_T_LIMITS`
- `historical_next_research_execution_authorized`: `false`

# 历史：观测保持相态补全已收口

2026-09-25 用户另行明确授权将本轮重要结果与研究进程提交云端；精简发布范围和核验状态见[发布记录](docs/notes/2026-09-25-observation-preserving-phase-results-release.md)。本次仅更新交付状态，科研仍为 CLOSED，完整数组外部访问仍未闭合。该授权 supersedes 本任务此前 Git 未授权措辞。

**VERIFIED：NO_COMPLETION_INCREMENT。** 阶段0—3完成，N/G/S均未对冻结E29通过原A_w，也均未通过独立D物理资格。N集合误差降低34.209%，但相态RMS增加7.946%；其D内raw相态平方为基点10.287倍、热增加7.324%。不变性质和完整原生数组验证通过，严格双周期仍失败。全部1800 Adam/600完整L-BFGS已完成，实际为同一CPU训练，后续GPU审计/读出；产物已校验回收并关闭实例。见[完整结果](paper/observation_preserving_phase_20260924/results.md)和[实验收口](docs/experiment/2026-09-24-observation-preserving-phase-closeout.md)。

**SUPPORTED_INTERPRETATION：**本轮未建立合格或神经特有补全增量，阶段4条件未触发，停止新增科研计算。理论边界、代码、直接控制及阴性证据可复用；P02方法增量和P03完整数据外部访问仍未补齐。本段supersedes本任务此前准备/执行中状态，下方旧科学结论保留原身份。

- `historical_phase_id`: `PHK_V23_OBSERVATION_PRESERVING_PHASE`
- `historical_lifecycle_state`: `CLOSED`
- `historical_blocker_id`: `NONE`
- `historical_claim_status`: `VERIFIED_OBSERVATION_PRESERVING_PHASE_NO_COMPLETION_INCREMENT`
- `historical_next_research_execution_authorized`: `false`

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

**VERIFIED：**E/D_E的完整A_w通过0/12项参考／读出／seed检查；独立初始化只有两个。相态RMS相对改善范围为-4.231%至1.234%；负值表示E误差更大。窗外非劣代价出现在6/12项检查。 全部七个B1对象在每个参考／读出条件下均未通过完整严格双周期门。 全部冻结科学工作与PDF逐页检查已完成，实际GPU已回收关闭。**SUPPORTED_INTERPRETATION：**未建立对两个seed、三参考和双读出都稳定的额外动态残差增量；保留各项连续收益与失败，不能将不同条件的优点拼接成完整成功。

本段 supersedes 本轮执行中／准备待批状态；历史数值、授权和未执行措辞保留其原阶段身份。结果路由 `PREDECLARED_INCREMENT_NOT_ESTABLISHED`。交付与下一步见本仓库 `paper/paper_revision_20260921/README.md` 和 `docs/experiment/2026-09-21-b1-phase-gap-sprint-closeout.md`。

唯一下一步是作者作论文路线决策：以现有配置收益和条件性消融形成较窄的方法评估稿，或另立具有实质新方法贡献的研究任务。建议先据本轮完整证据评估较窄成稿的可投性；若继续以更强方法创新为目标，应单独设计并批准新任务。本轮不自动降级原研究目标，也不追加救援训练。

- `historical_phase_id`: `PHK_V23_B1_SECOND_CYCLE_PHASE_GAP`
- `historical_lifecycle_state`: `CLOSED`
- `historical_blocker_id`: `NONE`
- `historical_claim_status`: `VERIFIED_B1_PREDECLARED_INCREMENT_NOT_ESTABLISHED`
- `historical_next_research_execution_authorized`: `false`

# 当前阶段

## 历史准备：2026-09-21最终冲刺阶段0—2

用户明确授权执行 `PCM-20260921-FINAL-SPRINT-B1-01` 的本地修稿、可见数据接口、聚焦测试、既有数组重评分和本地打包，见[本轮交付](paper/paper_revision_20260921/README.md)。此项覆盖下方历史关闭记录对这些准备动作的限制；不重开旧科学轨迹。B1新父态、六分支及模型读出仍须本轮GPU实例与资源确认，`next_research_execution_authorized`保持`false`。

**VERIFIED（准备）：**核心72条保存数组记录按原容差和精确布尔值复算通过；B1可见训练包、接口测试与独立暂存包已准备。**UNKNOWN：**B1科学增量及其对论文目标的实质提升。完整B1评分和最终PDF尚未执行；旧正反证据及下方历史身份保留。

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

- `historical_phase_id`: `PHK_V23_READOUT_AND_CLEAN_PDE_REVISION`
- `historical_lifecycle_state`: `CLOSED`
- `historical_blocker_id`: `NONE`
- `historical_claim_status`: `VERIFIED_READOUT_ROBUST_CLEAN_PDE_ABLATION_BOUNDED`
- `historical_next_research_execution_authorized`: `false`

2026-09-16用户另行明确授权完整投稿候选稿及重要结果提交云端，并交付论文改进独立评估；本包使用`codex/paper-submission-results`，详见[交接](docs/notes/2026-09-16-paper-submission-cloud-review-handoff.md)。范围为已有成果发布、评估与方案设计，不授权新训练、求解、checkpoint前反向或stress读取，不改变下文科学终局。

HISTORICAL_PHASE_ID=PHK_V23_READOUT_AND_CLEAN_PDE_REVISION
HISTORICAL_BLOCKER_ID=NONE
HISTORICAL_NEXT_RESEARCH_EXECUTION_AUTHORIZED=false

VERIFIED：用户于2026-09-15授权的[新脉冲协议冲刺](docs/notes/2026-09-15-lf11-protocol-authorized-sprint.md)已完成。两条新参考/支持轨迹和两个全新父态E/F_raw配对形成有效终点；E在两组均对F/projected及B_E通过原A/B。严格双周期未通过，条件时间细化未触发。实际GPU已回收关闭，stress未读；科学执行阶段未执行Git发布。

2026-09-16用户另行授权本轮重要成果提交云端，以及向“推进PINN相变研究”交付[独立复评材料](docs/notes/2026-09-16-lf11-v32-results-cloud-review-handoff.md)。此项授权覆盖V32精选成果的提交/推送与评估交付，不覆盖新的训练、求解、stress读取或科学预算扩张；`next_research_execution_authorized`保持`false`。

[终局](docs/experiment/2026-09-15-phk-v23-lf11-protocol-terminal-closeout.md)与[paper_v32](paper/paper_v32/README.md)保存实际结果。按原结果路由进入成稿，不再添加训练模块；[下一计划](docs/plans/NEXT_ACTIONS.md)不授权新的科学执行。

2026-09-16用户进一步授权执行`E:/PINN-PCM/Paper_Sprint.md`，本地[投稿候选稿](paper/paper_submission/README.md)已完成：完整英文正文/PDF、六组主图、去重统一数表、参考文献及合并补充材料。此项是已有结果分析和写作，零新训练、checkpoint前反向或电学/参考求解，stress未读、未启GPU，未commit/push/PR。V32科学终局与旧稿保持不变；可选固定模型时间参考敏感性仅为待批项，`next_research_execution_authorized`仍为`false`。
