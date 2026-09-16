# 项目状态

更新时间：2026-09-16

- `phase_id`: `PHK_V23_LF11_NEW_PROTOCOL_COMPLETE`
- `lifecycle_state`: `COMPLETE`
- `blocker_id`: `NONE`
- `claim_status`: `VALID_NEW_PROTOCOL_TWO_CLEAN_PAIRS_COMPLETE`
- `next_research_execution_authorized`: `false`

## 当前V32：完整新脉冲历史确认已完成

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
