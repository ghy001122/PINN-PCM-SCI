# 0036：选择 canonical TKF 作为待身份诊断的 FULL_PLAN 靶标

- `status`: `ACCEPTED`
- `accepted_at`: `2026-08-25`
- `decision_scope`: `HFO_CONDITIONAL_SIDE_METHOD_TARGET_AND_DIAGNOSTIC_IDENTITY_GATE`
- `amends`: `ADR_0032, ADR_0035`
- `supersedes_in_part`: `TKF_PINN_V0_PROVISIONAL_SELECTION`
- `claim_status`: `PLANNING_DECISION_NO_NUMERICAL_EVIDENCE`

用户要求在解决现有非阻塞 warning 后，为后续完整研究 PLAN 选择具体方法，并把选择交给引用会话“深度论文审查”对抗审查。审查给出 `DEFER_PENDING_DIAGNOSTIC_IDENTITY`：自由平滑分支的 TKF-PINN-v0 在现有五个协议节点上不可辨识，不能进入 FULL_PLAN。该否决由本地可复核的代数反例支持，不依赖外部会话的权威身份。

本 ADR 选择 **TKF-CANON-PINN（Canonical Transport Kink-Field PINN）** 作为唯一 future FULL_PLAN 条件式设计靶标，但不把它记为已准入方法。其输运公共坐标必须采用固定规范基

\[
q_{\mathrm{tr}}(x,t,\delta)
=q_0(x,t)+\delta q_1(x,t)+\delta^2 q_2(x,t)+|\delta|k(x,t),
\]

其中 `q0/q1/q2/k` 由同一个系数场网络联合输出，只读取物理时空与已冻结的完整案例状态，不读取 `δ`、side ID、`|δ|` 或其他协议旁路。相对于固定的二次光滑基，`k` 是唯一新增系数场；该规范基只定义一种可审计参数化，不能把 `k` 自动解释为独立物理信息或真实场解的导数不连续。

TKF-PINN-v0 的自由 `q_s(x,t,δ)+|δ|k(x,t)` 被否决：在 `δ∈{-1,-1/2,0,1/2,1}` 上，光滑多项式

\[
P(\delta)=\frac{7}{3}\delta^2-\frac{4}{3}\delta^4
\]

与 `|δ|` 完全同值，故任意 `k→k+h` 都可由 `q_s→q_s-P(δ)h` 吸收而不改变五视图上的场、残差、边界或守卫。原 `δ²k` 负控也不能隔离“hinge”解释。

TKF-CANON-PINN 的最强平滑 kill control 固定为参数量、系数场数、前向、时空自动微分与 support 匹配的

\[
q_{\mathrm{smooth4}}(x,t,\delta)
=q_0+\delta q_1+\delta^2q_2+\delta^4h(x,t).
\]

其四个系数场和主要计算与 TKF-CANON 匹配；`q2` 与 `h` 可在原五节点精确构造前述 `P(δ)k`，但整个协议表示保持光滑且没有一侧导数跳跃。因而 FULL_PLAN 定稿前必须先另行规划并批准不参与训练、调参或配置选择的 `δ=±1/4` held-out protocol microviews。真实 hinge 与 smooth-quartic control 若在该身份探针的场、gap 质量、固定截面空位通量、端口响应及事件端点上不可区分，裁决 `TKF_DIAGNOSTIC_IDENTITY_NO_GO`，不进入 method pilot，也不自动切换 cKC-NP 或其他方法。

信息身份固定为 `REDUNDANT_BUT_POTENTIALLY_USEFUL_CONDITIONING`：TKF-CANON 只重参数化同一 PDE/IC/BC 信息，不新增标签、方程或物理约束。输出变换 `B` 必须来源兼容、`C¹` 且不显含 `|δ|`；若物理协议为 `a=a0+εδ`，允许读取的物理一侧响应探针是 `2 D_q B(q0) k / ε`，同时必须审查输出变换的局部秩与饱和；不得把 `2k` 直接写成物理导数跳跃。

未来最小比较仍须包括 strong raw、SA/direct residual-Jacobian tangent、参数量匹配 wider raw、实际计算匹配 extra-work raw、上述 smooth-quartic kill control，以及 pilot 前的新颖性刷新。任何 SOURCE、EVENT、SIDE、RAW_COMPETENCE、transport-primary bottleneck、公共 backbone/coupling、diagnostic identity 或 direct-near 碰撞门失败都关闭 TKF-CANON；若诊断显示明显 temporal blocker，也不以 TKF-CANON 救援。不得通过新增 primitive、learned knot、多块机制、视图、seed、阈值或预算救援。

准确状态为 `TKF_PINN_V0_VERDICT=DEFER_PENDING_DIAGNOSTIC_IDENTITY / TKF_CANON_STATUS=SELECTED_AS_CONDITIONAL_FULL_PLAN_DESIGN_TARGET_NOT_ADMITTED / FULL_PLAN_FINALIZATION_GATE=DIAGNOSTIC_IDENTITY_PASS_REQUIRED / METHOD_ADMISSION=NOT_ADMITTED / NOT_NOVELTY_CLEARED / NOT_AUTHORIZED`。当前 G0–G1 blocker、12-intent 计划、授权边界与 `NO_SCIENTIFIC_METHOD_CLAIMS` 均不改变；held-out microviews 不得静默加入当前 G1 预算。
