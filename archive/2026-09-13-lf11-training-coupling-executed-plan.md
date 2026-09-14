# 当前执行：训练期电学耦合与事后电学修复

- `phase_id`: `PHK_V23_LF11_TRAINING_COUPLING_VS_POSTHOC_REPAIR_EXECUTE`
- `lifecycle_state`: `EXECUTE_AUTHORIZED`
- `blocker_id`: `NONE`
- `claim_status`: `PENDING_MATCHED_TRAINING_COUPLING_EVIDENCE`
- `next_research_execution_authorized`: `true`

当前执行：用户已于2026-09-14批准额外1次本地正解，授权总上限557。复用缓存仅补F_raw的t=0.0025 projected点，随后按原计划评价、裁决和paper_v30收口；两组训练已完成，GPU保持关闭。第56a条持续授权适用于以后同类最小工程恢复。

用户本轮完整执行请求使[指令](../notes/2026-09-13-lf11-training-coupling-authorized-sprint.md)生效；[评估报告](../notes/2026-09-13-lf11-v29-independent-review-training-coupling-plan.md)只解释设计。旧256正解主线提案归档，不作新的资格门。

1. 固定 V28 E0 父态、三场原头/T适配器、sparse、aE/bE、原三个物理池和1500＋300配方；复用同预算 P_E 及 D_E/E0/B_E，不重训。
2. 新软电学 F_raw/F_bal 共享原 P_F 数学内核；显式 FV 电平衡、半电阻 q、热单元与原 phase 残差，完整参数梯度，不加额外电BC。原尺度/分母不变。一次五块完整梯度给出 eta_bal=G0/||ge||，参考盲冻结；不可辨或等价按原指令裁决，不造齐对照。
3. 两配置各1500 Adam＋最多300次固定完整 L-BFGS 评估，原流、ramp及接受态回滚；0次训练电学正反求解。保存500/1000/1500和末次接受态，全部有效/无效轨迹保留。
4. 每个终点同时保存 network 和 projected；后者只固定自身 T/phase/σ 重求160×80电学，原上限278正解/终点、两配置556；本次补充授权为F_raw279、F_bal278、合计557（含丢弃1次）；两套场态与事件完全相同，不算独立模型。回收后真实关机确认，再本地评分。
5. 主比较 P_E 对两种 F/projected 的同一 A/B 层，10%增益/5%非劣和严格门分列；同时显示未投影、D_E/B_E及不同历史的V29背景。个别无效不取消另一臂，缺失强对照不构成消元获胜。
6. 仅主线无增量且会改变是否修正热接口的实际决策时，写明两种结果的行动后，执行指令中的两函数2×2敏感性检查，最多128正解、零训练/参数梯度/伴随。比较方法差值的变化，非仅共同绝对漂移；不随该检查继续修改或训练。
7. 形成 paper_v30：方法接口、真实匹配表、投影前后连线主图、事件图、计数与复现、主张矩阵。剩余热/phase PDE 独立必要性及材料标定仍 UNKNOWN；通用求解、VJP、L-BFGS和校准不各计原创。

不改变物理、观测、旧结论或stress边界，不自动commit/push/PR。后续独立初始化、干净新观测与完整新协议只作待批确认计划。到冻结停止条件收口，不能为保证阳性无界救援。
