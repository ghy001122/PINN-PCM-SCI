<!-- WA_CURRENT_BEGIN -->
# 当前：连续主稿与固定温度条件演化

W连续主稿与完整补充材料已完成；A两条轨迹完成并通过数值资格，两热口径及开发参考方向支持后续证人搜索，但原C²修正族可行性仍为UNKNOWN。结果已回收核验、实例已关闭。无自动A+或新训练。

任务 `PCM-20260925-INTEGRATED-MANUSCRIPT-FEASIBILITY-02` 已由用户明确批准实施 W+A，见[授权与边界](../../docs/notes/2026-09-25-integrated-manuscript-conditional-ivp-authorized.md)及[本轮交付](../../paper/paper_revision_20260925_integrated/README.md)。本段 supersedes 下方旧任务的当前状态；旧结果不变。仅至多两条条件轨迹，无新训练、电学求解、参考生成或自动 A+。用户随后明确授权本轮成果提交云端，见[发布记录](../notes/2026-09-25-integrated-manuscript-conditional-ivp-release.md)；该授权 supersedes 此前本轮 Git 未授权措辞，不扩展科研授权。

- `phase_id`: `PHK_V23_INTEGRATED_MANUSCRIPT_CONDITIONAL_IVP`
- `lifecycle_state`: `CLOSED`
- `blocker_id`: `NONE`
- `claim_status`: `WA_COMPLETE_CONDITIONAL_IVP_SUPPORTS_FURTHER_WITNESS_SEARCH_ORIGINAL_FAMILY_UNKNOWN`
- `next_research_execution_authorized`: `false`

<!-- WA_CURRENT_END -->

# 历史：物理目标、采样与固定温度诊断已完成

**VERIFIED：** 四个保存状态的零更新诊断完成，确认标量目标/独立资格不一致及空间采样敏感；固定T的严格热一致性存在范围/端点障碍，原5%容限下能否有效补全仍 **UNKNOWN**。见[诊断结果、图表及唯一后续决策](../../paper/observation_preserving_phase_20260924/physics-objective-diagnostic.md)。V100诊断112.589秒，零参数更新/电学求解/参考场读取；结果已回收，实例已关闭。

用户2026-09-25指定交接任务已收口；历史 NO_COMPLETION_INCREMENT 与E/F正向结果保持。新训练和条件相态推进未执行或追加授权；用户随后明确授权本轮诊断成果提交云端，见[发布记录](../notes/2026-09-25-physics-objective-diagnostic-release.md)。P02/P03仍开放。

- `historical_phase_id`: `PHK_V23_PHYSICS_OBJECTIVE_FEASIBILITY`
- `historical_lifecycle_state`: `CLOSED`
- `historical_blocker_id`: `NONE`
- `historical_claim_status`: `VERIFIED_OBJECTIVE_MISMATCH_SAMPLING_SENSITIVITY_FIXED_T_LIMITS`
- `historical_next_research_execution_authorized`: `false`

# 历史：观测保持相态补全已收口

2026-09-25 用户另行明确授权将本轮重要结果与研究进程提交云端；精简发布范围和核验状态见[发布记录](../notes/2026-09-25-observation-preserving-phase-results-release.md)。本次仅更新交付状态，科研仍为 CLOSED，完整数组外部访问仍未闭合。该授权 supersedes 本任务此前 Git 未授权措辞。

**VERIFIED：NO_COMPLETION_INCREMENT。** 阶段0—3完成，N/G/S均未对冻结E29通过原A_w，也均未通过独立D物理资格。N集合误差降低34.209%，但相态RMS增加7.946%；其D内raw相态平方为基点10.287倍、热增加7.324%。不变性质和完整原生数组验证通过，严格双周期仍失败。全部1800 Adam/600完整L-BFGS已完成，实际为同一CPU训练，后续GPU审计/读出；产物已校验回收并关闭实例。见[完整结果](../../paper/observation_preserving_phase_20260924/results.md)和[实验收口](../experiment/2026-09-24-observation-preserving-phase-closeout.md)。

**SUPPORTED_INTERPRETATION：**本轮未建立合格或神经特有补全增量，阶段4条件未触发，停止新增科研计算。理论边界、代码、直接控制及阴性证据可复用；P02方法增量和P03完整数据外部访问仍未补齐。本段supersedes本任务此前准备/执行中状态，下方旧科学结论保留原身份。

- `historical_phase_id`: `PHK_V23_OBSERVATION_PRESERVING_PHASE`
- `historical_lifecycle_state`: `CLOSED`
- `historical_blocker_id`: `NONE`
- `historical_claim_status`: `VERIFIED_OBSERVATION_PRESERVING_PHASE_NO_COMPLETION_INCREMENT`
- `historical_next_research_execution_authorized`: `false`

# 历史收口：相对相态残差与时间矩开发

**VERIFIED：**八臂数值有效且预算完整；所有候选均未对D和P建立原A_w增量。RIM相对D的W相态RMS改善1.918%、S改善2.202%；相对P分别改善2.264%、2.633%，低于原10%门。电热非劣与窗外代价不是此次失败原因。 全部八臂严格双周期未通过；16/32与补充8/16数值检查通过。GPU结果已回收并关机。完整事实见[本轮结果](../../paper/phase_moments_20260923/results.md)与[实验收口](../../docs/experiment/2026-09-23-relative-phase-moments-closeout.md)。本段supersedes本轮执行中状态；下方旧B1结论与发布记录保留历史身份。

**SUPPORTED_INTERPRETATION：**本轮没有建立独立相态目标或时间矩增量。按预声明条件停止，不追加确认、调权或训练，不自动转为D_E主导窄稿。原论文的相态PDE贡献与严格事件证据仍未补齐；不同科学假设须另立任务。用户已另行授权并完成[精简成果发布](../notes/2026-09-23-phase-moments-results-release.md)，但没有新增科研授权。

- `historical_phase_id`: `PHK_V23_RELATIVE_PHASE_MOMENTS`
- `historical_lifecycle_state`: `CLOSED`
- `historical_blocker_id`: `NONE`
- `historical_claim_status`: `VERIFIED_PHASE_MOMENTS_NO_INCREMENT_WITHIN_SCREEN_BUDGET`
- `historical_next_research_execution_authorized`: `false`

# 历史收口：B1第二周期相态缺测与论文修订

2026-09-22 用户另行授权本轮成果提交云端；发布分支为 `codex/paper-revision-results`，范围和远端核验状态见[发布记录](../notes/2026-09-22-b1-sprint-results-release.md)。科研阶段保持CLOSED，完整时空数组仍未公开。

**VERIFIED：**E/D_E的完整A_w通过0/12项参考／读出／seed检查；独立初始化只有两个。相态RMS相对改善范围为-4.231%至1.234%；负值表示E误差更大。窗外非劣代价出现在6/12项检查。 全部七个B1对象在每个参考／读出条件下均未通过完整严格双周期门。 全部冻结科学工作与PDF逐页检查已完成，实际GPU已回收关闭。**SUPPORTED_INTERPRETATION：**未建立对两个seed、三参考和双读出都稳定的额外动态残差增量；保留各项连续收益与失败，不能将不同条件的优点拼接成完整成功。

本段 supersedes 本轮执行中／准备待批状态；历史数值、授权和未执行措辞保留其原阶段身份。结果路由 `PREDECLARED_INCREMENT_NOT_ESTABLISHED`。交付与下一步见本仓库 `paper/paper_revision_20260921/README.md` 和 `docs/experiment/2026-09-21-b1-phase-gap-sprint-closeout.md`。

唯一下一步是作者作论文路线决策：以现有配置收益和条件性消融形成较窄的方法评估稿，或另立具有实质新方法贡献的研究任务。建议先据本轮完整证据评估较窄成稿的可投性；若继续以更强方法创新为目标，应单独设计并批准新任务。本轮不自动降级原研究目标，也不追加救援训练。

- `historical_phase_id`: `PHK_V23_B1_SECOND_CYCLE_PHASE_GAP`
- `historical_lifecycle_state`: `CLOSED`
- `historical_blocker_id`: `NONE`
- `historical_claim_status`: `VERIFIED_B1_PREDECLARED_INCREMENT_NOT_ESTABLISHED`
- `historical_next_research_execution_authorized`: `false`

# 历史准备：B1阶段3算力确认

2026-09-21用户指令 `PCM-20260921-FINAL-SPRINT-B1-01` 对本次本地准备范围 supersedes 下方旧后续清单，具体交付与实际命令见[冲刺准备](../../paper/paper_revision_20260921/README.md)。阶段0—2已经完成：局部修稿、P04/P05、指定来源核验、72条核心数组复算、可见训练包、聚焦测试与本地暂存。

唯一下一步是确认本轮实际GPU实例、型号、开机状态、费用／墙钟上限及暂存、回收、关机策略。获批后按冻结的两个新父态、六个分支和共同读出顺序执行，统一评分后一次成稿；不重新询问已固定的窗口、seed、方法或阈值。阶段3未获批前不执行新训练／模型读出／电学求解。P03完整数据对外访问和作者事实另待落实，局部准备完成不等于科学目标或二区竞争力已达成。

## 历史：投稿前修订成果发布与作者收束

- `historical_phase_id`: `PHK_V23_READOUT_AND_CLEAN_PDE_REVISION`
- `historical_lifecycle_state`: `CLOSED`
- `historical_claim_status`: `VERIFIED_READOUT_ROBUST_CLEAN_PDE_ABLATION_BOUNDED`
- `historical_next_research_execution_authorized`: `false`
- `historical_blocker_id`: `NONE`

用户批准的[六阶段计划](../notes/2026-09-18-readout-clean-pde-authorized-plan.md)已执行收口，实际科学结果见[终局](../experiment/2026-09-18-readout-clean-pde-revision-closeout.md)和[完整稿](../../paper/paper_revision_20260918/README.md)。GPU关闭，完整分包本地保留。2026-09-20用户另行授权精简成果提交云端，见[发布总结](../notes/2026-09-20-readout-clean-pde-results-release.md)；本次不上传完整数组、不实际投稿。

1. 作者补齐真实身份、贡献、基金、利益与最终AI声明；确认稿件责任。
2. 选择计算方法类目标期刊，按其当时正式指南适配模板和附件；不承诺接收。
3. 确定代码/数据发布许可并批准完整数组公开及持久标识，再更新可用性声明。
4. 完成最终作者审阅批准后投稿。严格事件、材料验证和普遍泛化仍是独立后续研究问题。

新训练/求解/网络改动/参数搜索/额外case保持PROPOSED_NOT_AUTHORIZED。已完成的阴性消融不触发自动救援；未过优势门不证明等效。
