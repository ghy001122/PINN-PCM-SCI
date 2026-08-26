# HFO-NP-v1 TKF-CANON 方法选择与外部对抗审查整合

- `date`: `2026-08-25`
- `document_role`: `CONDITIONAL_METHOD_SELECTION_AND_EXTERNAL_REVIEW_INTEGRATION_NOT_LIVE_PLAN`
- `status`: `SELECTED_AS_CONDITIONAL_FULL_PLAN_DESIGN_TARGET_NOT_ADMITTED`
- `tkf_pinn_v0_verdict`: `DEFER_PENDING_DIAGNOSTIC_IDENTITY`
- `method_target`: `TKF_CANON_PINN`
- `full_plan_finalization_gate`: `SOURCE_MODEL_FIDELITY_FIELD_KINK_DIAGNOSTIC_IDENTITY_AND_NOVELTY_PASS_REQUIRED`
- `prior_gate_superseded_in_part`: `DIAGNOSTIC_IDENTITY_PASS_REQUIRED`
- `current_scope_forward_pointer`: Q54–Q63 已由 ADR 0037/0038 覆盖 TKF 名称与真实 kink 语义；Q64–Q68 又由 ADR 0039 分离身份案例并冻结来源锚点、联合向量、输出变换和双轴效用；当前统一读 `research_decisions_HFO_Q1_Q68.md`
- `information_status`: `REDUNDANT_BUT_POTENTIALLY_USEFUL_CONDITIONING`
- `method_admission`: `NOT_ADMITTED`
- `novelty_status`: `NOT_NOVELTY_CLEARED`
- `claim_status`: `NO_NEW_SCIENTIFIC_EVIDENCE`
- `input`: 本地方法筛选、引用 ChatGPT 会话“深度论文审查”的第三轮对抗审查及短版调整请求
- `authority_relation`: 服从 `CONTEXT.md`、ADR 0031–0036、`active_phase.md` 与唯一 live plan
- `execution_in_this_task`: `0 source search / 0 solve / 0 PINN implementation / 0 training / 0 formal / 0 GPU`

## 1. 单一裁决

> 当前角色说明：本文件只保留 TKF-v0 反例、canonical 公式和 smooth4 身份设计的形成过程。真实 kink 语义和 TKF 名称已由 ADR 0038 覆盖；当前 CTH 的身份角色、固定 `a0`、联合向量、共同输出变换与双轴效用读 [Q64–Q68 整合](2026-08-25-hfo-q64-q68-cth-identity-anchor-transform-and-pareto-integration.md)和 [ADR 0039](../adr/0039-separate-cth-identity-evidence-and-freeze-anchor-vector-transform-and-utility.md)。

原 TKF-PINN-v0 不进入 FULL_PLAN；其自由平滑分支可在现有五视图上完全吸收 `|δ|k`，使 `k` 不可辨识。经审查后的唯一具体靶标是 **TKF-CANON-PINN（Canonical Transport Kink-Field PINN）**，但状态只能是：

```text
TKF_PINN_V0_VERDICT=DEFER_PENDING_DIAGNOSTIC_IDENTITY
TKF_CANON_STATUS=SELECTED_AS_CONDITIONAL_FULL_PLAN_DESIGN_TARGET_NOT_ADMITTED
FULL_PLAN_FINALIZATION_GATE=SOURCE_MODEL_FIDELITY_FIELD_KINK_DIAGNOSTIC_IDENTITY_AND_NOVELTY_PASS_REQUIRED
METHOD_ADMISSION=NOT_ADMITTED
IMPLEMENTATION_AUTHORIZATION=NOT_AUTHORIZED
INFORMATION_STATUS=REDUNDANT_BUT_POTENTIALLY_USEFUL_CONDITIONING
NOVELTY_STATUS=NOT_NOVELTY_CLEARED
SCIENTIFIC_METHOD_CLAIMS=NONE
```

本段是 TKF 当时的形成史。当前“选定”指 CTH 条件式设计靶标；来源模型保真、热因果、`FIELD_HINGE_RELEVANCE_PLUS`、角色分离 diagnostic identity、双轴 bundle utility 与 novelty sufficiency 全部通过前不得定稿 FULL_PLAN 或实现方法。

## 2. 从 v0 到 canonical 版本的实质调整

| 项目 | TKF-PINN-v0 | TKF-CANON-PINN |
|---|---|---|
| 平滑部分 | 任意 `q_s(x,t,δ)` | 固定 `q0+δq1+δ²q2` |
| hinge 部分 | `|δ|k(x,t)` | `|δ|k(x,t)` |
| 系数网络 | 自由分支与 kink 可交换 | 一个网络联合输出 `q0,q1,q2,k`，均不读取 `δ` |
| 信息身份 | 曾被误读为可测物理 jump | `REDUNDANT_BUT_POTENTIALLY_USEFUL_CONDITIONING` |
| 方法身份 | 不可辨识，否决 | 固定规范基下的条件式表示假设 |
| FULL_PLAN | 不允许 | 先过身份诊断，之后才可定稿 |

固定规范基是对候选机制的定义，不是额外的科学阳性证据。它使系数分解在五节点设计矩阵下具有唯一规范，但不能证明真实 HFO 协议解映射存在数学 cusp，也不能证明基准协议就是正确结点。

## 3. 不可辨识反例与最小身份诊断

在 `δ={-1,-1/2,0,1/2,1}` 上，`P(δ)=7δ²/3-4δ⁴/3` 与 `|δ|` 同值。因此自由 `q_s` 可用 `P(δ)h` 精确交换任意 `h(x,t)`，五视图的所有物理输出和损失均不变。这个反例关闭 v0，也说明仅比较现有五视图无法区分 hinge 与普通光滑四次曲率。

未来身份门必须把下式作为参数量和计算匹配的 mechanism-killing control：

\[
q_{\mathrm{smooth4}}=q_0+\delta q_1+\delta^2q_2+
\delta^4h.
\]

该 control 与 TKF-CANON 使用相同数量的系数场；其 `δ²q2+δ⁴h` 可在原五节点实现前述 `P(δ)k` 的精确光滑吸收。最小额外诊断是在不参与训练、调参或配置选择的 `δ=±1/4` microviews 上评价真实 hinge 与 smooth-quartic control。该第三扰动尺度属于未来 diagnostic-identity 计划增量，不进入当前 G1；ADR 0038 后当前 G1 仍只生成原五视图，但总预算因 thermal-feedback-off 配对增为 13 intents。

## 4. 允许的最窄假设与禁止表述

允许的规划假设：

> 若来源合格的 HFO 局部 gap 事件通过 SIDE 门，strong raw 胜任且诊断出 transport-primary 的局部协议表示瓶颈，那么固定 canonical hinge 基是否能相对 smooth-quartic control 和强参数敏感基线，提高 held-out 局部协议响应与完整器件事件保真度？

禁止写成：

- `k` 是新增的独立物理约束、oracle 标签或真实导数跳跃场；
- 阈值事件已经证明 `c_v/J_v` 对协议幅度不可微；
- `2k` 是非线性输出变换后的物理 jump；
- `|δ|`、hinge 或 spline 基本身具有首创性；
- 五视图 loss 更低即可证明机制；
- 未发现 exact bundle 等于 novelty clearance、世界首创或 SOTA；
- 该方法已普适适用于忆阻器或 PCM。

## 5. 后续 FULL_PLAN 前门

```text
SOURCE+
  → EVENT+
  → SIDE+
  → qualified oracle and complete-case pools
  → RAW_COMPETENT and not NO_BOTTLENECK
  → TRANSPORT_SIDE_REPRESENTATION_BOTTLENECK+
  → unique common backbone/coupling mode
  → TKF_DIAGNOSTIC_IDENTITY_PASS at held-out microview
  → no DIRECT_NEAR_VETO
  → TKF-CANON FULL_PLAN may be finalized for user review
```

最小基线为 strong raw、SA/direct residual-Jacobian tangent、parameter-matched wider raw、compute-matched extra-work raw 和 smooth-quartic control。输出变换 `B` 必须 `C¹`、不显含 `|δ|` 且来源兼容；直接探针读取经输出变换和物理幅度换算后的 `2D_qB(q0)k/ε`，并与 `ε, ε/2, ε/4` 的 oracle 一侧 finite-secant jump 比较方向、空间定位与幅值，同时检查输出变换饱和/秩、gap ROI、`c_v/J_v`、固定截面 vacancy flux、端口响应及 seed/尺度稳定性。

任何前门失败、真实 hinge 与 smooth-quartic control 在盲 microviews 上不可区分、`k` 塌缩/不稳定、强基线在冻结等价带内追平、守卫退化、载荷不在 transport、出现明显 temporal blocker 或 direct-near 覆盖，都关闭 TKF-CANON 主张。负结果后不追加第二 kink、learned knot、多块机制，也不自动启动 cKC、PHA、IRAC、自适应采样或新材料。

## 6. 外部审查的证据身份

引用会话的 verdict、反例和调整建议是对抗性规划输入，不是一手论文或数值证据。本地仅把可直接复核的代数关系和由其推出的设计约束记为 `VERIFIED_ANALYTICAL_REVIEW`；其碰撞清单仍须在未来获批的 pilot 前 novelty refresh 中回到一手来源。当前没有新增 SOURCE、EVENT、SIDE、RAW、PINN、方法或 formal 阳性证据。
