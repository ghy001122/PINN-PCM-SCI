# 当前收口：B1第二周期相态缺测与论文修订

2026-09-22 用户另行授权本轮成果提交云端；发布分支为 `codex/paper-revision-results`，范围和远端核验状态见[发布记录](docs/notes/2026-09-22-b1-sprint-results-release.md)。科研阶段保持CLOSED，完整时空数组仍未公开。

**VERIFIED：**E/D_E的完整A_w通过0/12项参考／读出／seed检查；独立初始化只有两个。相态RMS相对改善范围为-4.231%至1.234%；负值表示E误差更大。窗外非劣代价出现在6/12项检查。 全部七个B1对象在每个参考／读出条件下均未通过完整严格双周期门。 全部冻结科学工作与PDF逐页检查已完成，实际GPU已回收关闭。**SUPPORTED_INTERPRETATION：**未建立对两个seed、三参考和双读出都稳定的额外动态残差增量；保留各项连续收益与失败，不能将不同条件的优点拼接成完整成功。

本段 supersedes 本轮执行中／准备待批状态；历史数值、授权和未执行措辞保留其原阶段身份。结果路由 `PREDECLARED_INCREMENT_NOT_ESTABLISHED`。交付与下一步见本仓库 `paper/paper_revision_20260921/README.md` 和 `docs/experiment/2026-09-21-b1-phase-gap-sprint-closeout.md`。

唯一下一步是作者作论文路线决策：以现有配置收益和条件性消融形成较窄的方法评估稿，或另立具有实质新方法贡献的研究任务。建议先据本轮完整证据评估较窄成稿的可投性；若继续以更强方法创新为目标，应单独设计并批准新任务。本轮不自动降级原研究目标，也不追加救援训练。

- `phase_id`: `PHK_V23_B1_SECOND_CYCLE_PHASE_GAP`
- `lifecycle_state`: `CLOSED`
- `blocker_id`: `NONE`
- `claim_status`: `VERIFIED_B1_PREDECLARED_INCREMENT_NOT_ESTABLISHED`
- `next_research_execution_authorized`: `false`

# 项目状态

## 历史准备：2026-09-21最终冲刺阶段0—2

用户当前指令 `PCM-20260921-FINAL-SPRINT-B1-01` 授权本地准备与既有数组复算，交付位于[20260921修订目录](paper/paper_revision_20260921/README.md)。本段对准备范围取代旧关闭记录中的禁止新接口修改限制，不覆盖既有科学结论或自动授权阶段3。

**VERIFIED（准备）：**原协议seed43跨参考／读出18记录先行复算通过，随后核心72记录通过；8项B1与4项继承测试通过。φ正时间标签保留17,094、移除11,781，V/T各28,875。B1训练暂存包独立加载通过且不含旧权重或参考数组。**UNKNOWN：**尚无B1父态、终点、模型读出或新科学优劣结论。GPU实例和资源待确认，`next_research_execution_authorized=false`；无新Git发布、公开上传或投稿。

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

更新时间：2026-09-20

- `historical_phase_id`: `PHK_V23_READOUT_AND_CLEAN_PDE_REVISION`
- `historical_lifecycle_state`: `CLOSED`
- `historical_blocker_id`: `NONE`
- `historical_claim_status`: `VERIFIED_READOUT_ROBUST_CLEAN_PDE_ABLATION_BOUNDED`
- `historical_next_research_execution_authorized`: `false`

## 历史写作交付：原投稿候选稿完成

用户随后另行授权本轮重要结果提交云端并交付独立评估。本包发布分支为`codex/paper-submission-results`；[本次交接](docs/notes/2026-09-16-paper-submission-cloud-review-handoff.md)要求评估论文质量与最优先补证，允许修正当前计划。下文“未commit/push/PR”专指此前成稿阶段；本次出版物打包和评估交付不产生新的科研执行授权。

VERIFIED：2026-09-16按用户Paper_Sprint授权，将V28—V32已有证据整理为[完整英文投稿候选稿](paper/paper_submission/README.md)，包括正文/PDF、六组可重绘主图、统一数表、准确参考文献与一份合并补充材料。没有新增训练、模型推理、电学/参考求解或stress读取，未启GPU，未commit/push/PR；`paper_v32`不覆盖。

VERIFIED：新增报告性分析从保存事件表得到第二事件延迟缩短0.0316；E29/E43预测0.0279417/0.0307400，F29/F43预测0.0350000/0.0155800，B_E预测0.0252714。F29在该差值误差上略优于E29的反证保留。统一结果将每协议B_E只计一次；正文并列绝对误差、百分点与相对效应，完整披露严格事件失败及能量抵消。

SUPPORTED_INTERPRETATION：成稿核心为训练期电学约束相对共同事后修复的方法包收益；剩余PDE独立必要性、孤立VJP因果、连续体和材料验证仍UNKNOWN。最优先后续为针对初稿的科学/投稿审阅；唯一可提科研补证为固定模型的两协议时间参考敏感性，详见补充S9，仅`PROPOSED_NOT_AUTHORIZED`。

## 历史V32：完整新脉冲历史确认已完成

VERIFIED：第二脉冲固定从1.25提前到1.01，完成新support/reference、seed29/43两个全新父态及四个E/F_raw终点。E在两个新seed上均对F_raw/projected和同层B_E通过原相态层A、器件层B及全部非劣要求。实际GPU已回收关闭，随后完成本地参考评价与[paper_v32](paper/paper_v32/README.md)。

| 新协议角色 | raw Ephi | 电流NRMSE | 功率NRMSE | E对soft A/B | E对B_E A/B |
|---|---:|---:|---:|---|---|
| E，29 | 0.0190024138 | 0.994297% | 0.999332% | True/True | True/True |
| F/projected，29 | 0.0238184652 | 2.269914% | 2.335316% | 同父强对照 | — |
| E，43 | 0.0186192217 | 0.682119% | 0.672758% | True/True | True/True |
| F/projected，43 | 0.0233632244 | 2.991735% | 3.094686% | 同父强对照 | — |
| B_E，共享 | 0.0255235296 | 2.003186% | 2.048939% | 同求解层插值 | — |

VERIFIED：E相对F的phase误差下降20.22%/20.31%，电流下降56.20%/77.20%，功率下降57.21%/78.26%。seed43的S改善10.371143%裕量较窄，未四舍五入改门。两组E均通过两周期timing，但第一周期recall仅0.866607/0.875507，严格双周期仍未过。完整事件代价、分脉冲能量抵消及报告口径见[终局](docs/experiment/2026-09-15-phk-v23-lf11-protocol-terminal-closeout.md)。

VERIFIED：新协议第二脉冲前的ROI残余温度/相态更高，参考第二事件延迟从0.2484变为0.2168。两条主轨迹共5000主时间步、60503内部线性解；新增10800 Adam、2400完整评估、1173接受步，E正/伴随39186/39186，校准100/0，正式投影1390，均在原预算内。条件时间细化未触发，未新增训练分支或读取stress。

SUPPORTED_INTERPRETATION：训练期电学约束与一致焦耳接口的方法收益在一个新完整协议适配中得到配对支持。对象仍为合成无量纲二维模型；两个case×两个seed不等于四个独立case，case各用自身support重训不称零样本或formal OOD。D_E强、剩余PDE独立必要性、孤立VJP因果及材料/连续体验证UNKNOWN。按原路由进入成稿，不继续加模块；后续见[计划](docs/plans/NEXT_ACTIONS.md)。

2026-09-16用户另行明确授权V32成果提交云端及[独立复评交接](docs/notes/2026-09-16-lf11-v32-results-cloud-review-handoff.md)。发布分支为`codex/v32-research-results`，实际发布版本以本包所属提交和交付消息为准。科学执行阶段的“未Git发布”记录保留；此次发布和评估不授权新科研执行。

## 历史V31：全空间反事实与原协议确认

以下V31结果是继承事实，不计作本轮新增成果。

VERIFIED：本轮F_full已完成全空间软电学反事实。保留原父态、eta=1及原128单元T/phase抽样，只改变电学残差积分；固定模型的network/projected保留相同T/phase与完整事件。实际实例已回收关闭，随后本地读取nominal参考。

| 方法 | 底流NRMSE | 功率NRMSE | raw Ephi | S |
|---|---:|---:|---:|---:|
| P_E | 0.693819% | 0.681731% | 0.0159996773 | 0.0008190625 |
| F_raw/projected | 1.071112% | 1.065121% | 0.0166913896 | 0.000858203125 |
| F_full/projected | 1.186645% | 1.190184% | 0.0172242878 | 0.000905078125 |
| F_bal/projected | 1.607770% | 1.650530% | 0.0171664543 | 0.000862890625 |
| D_E | 0.724257% | 0.721323% | 0.0155821211 | 0.00078703125 |
| B_E | 1.728229% | 1.756229% | 0.0237697822 | 0.0014084375 |

VERIFIED：E对全部三个有效soft/projected的同层裁决为A=False、B=True。完整增益、非劣子项和反向比较均保留；未过10%不等于等效。

VERIFIED：预声明规则的非支配集合为F_raw；选择状态UNIQUE_COMPARATOR_LOCKED。阶段B：TWO_CLEAN_PAIRS_COMPLETE。

实际新增12300 Adam、2700完整目标/梯度评估；训练正/伴随39172/39172，正式推理解1390。均在总上限内。

SUPPORTED_INTERPRETATION：新比较检验空间积分解释，仍没有单独隔离初始电势、有限罚项与精确约束、时间位置或VJP。V30阳性按原边界保留。剩余热/phase PDE独立必要性、完整新case、材料标定与实验验证仍UNKNOWN。

## 两个干净初始化的实际配对

| 新初始化 | 方法 | 底流NRMSE | 功率NRMSE | raw Ephi | S | E对soft的A/B |
|---|---|---:|---:|---:|---:|---|
| 29 | E/projected | 0.858273% | 0.862489% | 0.0200420628 | 0.00103007812 | True/True |
| 29 | F_raw/projected | 1.687845% | 1.727434% | 0.0239867136 | 0.001225 | 同父强对照 |
| 43 | E/projected | 1.571784% | 1.592751% | 0.0216191612 | 0.00113164062 | False/True |
| 43 | F_raw/projected | 3.069658% | 3.175752% | 0.0244820854 | 0.0012525 | 同父强对照 |

VERIFIED：每seed使用全新网络及零输出T适配器，经同一冻结纯观测配方形成共同父态，再分叉E与锁定F_raw；没有加载旧训练权重、重新挑seed或使用reference选终点。历史17具有不同培养流程，未计入本配对集合。完整事件、拟合程度与尺度、实际计数分别见paper_v31的clean-complete-events、clean-common-fit、clean-execution数表。

SUPPORTED_INTERPRETATION：E对锁定soft＋projection的原器件功能层B在两个预声明新初始化上均得到支持，构成有限的干净初始化确认；不推断总体成功概率、精确置信区间、新case泛化或剩余PDE独立必要性。

VERIFIED：seed29/43的相对电流改善分别49.1498%/48.7961%，功率改善50.0711%/49.8465%，所有原场非劣条件通过。相态A只通过seed29；seed43的S改善9.64945%，不能四舍五入当10%。对同求解层B_E，seed29通过A/B，seed43均未通过：其raw Ephi/电流/功率改善约9.04771%/9.05231%/9.30851%。因此，强插值基线的冻结效应门尚未在两组同时确认。

VERIFIED：四个新模型均未过严格双周期。seed29的E第二周期timing由soft的0.0042375变为0.00643333，能量积分误差由0.160928%变为0.275172%；seed43的E第一周期recall由0.840581变为0.802726，虽精度与timing改善，仍不能声称逐事件或全指标领先。父态V拟合程度、phase拟合及公共尺度同时变化，不能仅凭两组记录将绝对性能差异归因于V拟合一个因素。

[初稿](paper/paper_v31/manuscript.md) · [主张矩阵](paper/paper_v31/claim_evidence_matrix.md) · [终局](docs/experiment/2026-09-14-phk-v23-lf11-fullgrid-terminal-closeout.md) · [下一计划](docs/plans/NEXT_ACTIONS.md)。旧稿保留原边界。本轮没有自动Git发布。
