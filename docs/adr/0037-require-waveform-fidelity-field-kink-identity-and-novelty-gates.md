# 0037：在 TKF FULL_PLAN 前增加波形、保真、场身份与新颖性门

- `status`: `ACCEPTED`
- `accepted_at`: `2026-08-25`
- `decision_scope`: `HFO_TKF_PRE_FULL_PLAN_WAVEFORM_FIDELITY_FIELD_IDENTITY_AND_NOVELTY_GATES`
- `amends`: `ADR_0031, ADR_0034, ADR_0035, ADR_0036`
- `claim_status`: `PLANNING_DECISION_NO_NEW_SCIENTIFIC_EVIDENCE`

用户接受引用会话“深度论文审查”对 Q54–Q58 的对抗性修订。TKF-CANON-PINN 继续是唯一条件式 FULL_PLAN 设计靶标，但总裁决改为 `REVISE_BEFORE_FULL_PLAN_FINALIZATION`；这不是方法准入或执行授权。

唯一协议轴不再称为纯 amplitude/ramp-rate 轴，而冻结为 `SOURCE_ANCHORED_DERIVED_WAVEFORM_SCALE_AXIS`：G0 选择初态分支后，以固定时长的 RESET 或 SET 事件段单位形状 `v_hat_E(t)` 定义 `V(t;a)=V_fixed(t)+a v_hat_E(t)`，其中 `a0` 精确恢复 G0 资格化来源波形，其他波段、转折点和完整物理时间不随 `a` 改变。该 A′ 轴只允许主张“固定时长事件段波形缩放的局部响应”；若 G0 证明来源语义不允许这种派生族，或论文必须依赖纯幅值因果解释，则 TKF 路线停止，不增加第二协议轴。

对象进入方法路线前必须通过来源模型保真门：一个来源对齐单周期案例须同时满足可数字化端口轨迹和至少两个跨事件空位空间状态，并合并来源数字化、状态定位、离散、求解与 detector 不确定性。不得通过拟合决定 gap 拓扑或绝对时间的参数获得通过；不能闭合时对象只能降为 `LITERATURE_INSPIRED_SYNTHETIC_BENCHMARK_UNVALIDATED`，不得支撑当前 HFO 来源对齐方法论文。

`SIDE+` 不再足以准入 TKF。未来 strong-raw 完成 temporal/spatial 诊断后，还须在训练外以单一事件时间平移排除纯时间位移混淆，并在 `epsilon, epsilon/2, epsilon/4` 上建立 `FIELD_KINK_PLUS`。非线性时间扭曲、DTW 或结果导向对齐均禁止；物理时间事件误差仍是 headline 评价。中心结点还必须相对镜像错结点 `eta=±1/2` 控制显示特异性。

TKF 的身份试验必须另立、另审并另批 `TKF_DIAGNOSTIC_IDENTITY_PROTOCOL`，只使用 qualification cases；`delta=±1/4` 只作盲评价，不进入训练、配置选择或后续 pilot/formal 效应估计。身份通过只产生 `ELIGIBLE_FOR_FULL_PLAN_FINALIZATION_NOT_PILOT_AUTHORIZED`，失败产生 `METHOD_VETO_IDENTITY_FAILED`。

FULL_PLAN 定稿前还必须通过 `NOVELTY_SUFFICIENCY_GATE`：bounded primary-source refresh 必须排除 direct-near 等价，并确认存在一个不靠标准 hinge、HFO 对象复杂性、五视图拟合或治理流程冒充算法创新的可检验窄主张；FULL_PLAN 则必须把 smooth-quartic、镜像错结点、SA/direct Jacobian、平滑参数化 PINN、wider raw 与 extra-work raw 冻结为后续实际能力 kill set。该前门不把尚未运行的比较写成已胜出证据。direct-near 等价或只剩“把标准 hinge 放进 HFO”时，裁决 `METHOD_VETO_NOVELTY_INSUFFICIENT` 并关闭当前方法论文，不自动转入其他方法或论文类型。

因此当前状态为 `FULL_PLAN_STATUS=CONDITIONAL_DRAFT_NOT_FINALIZED / FULL_PLAN_FINALIZATION_GATE=SOURCE_MODEL_FIDELITY_FIELD_KINK_DIAGNOSTIC_IDENTITY_AND_NOVELTY_PASS_REQUIRED / METHOD_ADMISSION=NOT_ADMITTED / IMPLEMENTATION_AUTHORIZATION=NOT_AUTHORIZED / CLAIM_STATUS=NO_SCIENTIFIC_METHOD_CLAIMS`。G0–G1 的 12-intent、CPU 与授权边界不扩张，`delta=±1/4` 不加入当前 G1。
