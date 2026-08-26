# HFO-NP-v1 Q54–Q58：TKF-CANON 前置门对抗性修订整合

> **当前角色**：本文件保留 waveform-scale、来源模型保真、time-shift、smooth4/错结点和 novelty 前门的形成史。`FIELD_KINK_PLUS` 已由 ADR 0038 改为有限尺度 `FIELD_HINGE_RELEVANCE_PLUS`；当前 CTH identity 与效用以 [Q64–Q68 整合](2026-08-25-hfo-q64-q68-cth-identity-anchor-transform-and-pareto-integration.md)和 ADR 0039 为准。

- `date`: `2026-08-25`
- `document_role`: `ACCEPTED_PLANNING_REVISION_DETAIL_NOT_LIVE_PLAN`
- `status`: `REVISE_BEFORE_FULL_PLAN_FINALIZATION`
- `full_plan_status`: `CONDITIONAL_DRAFT_NOT_FINALIZED`
- `method_target`: `TKF_CANON_PINN`
- `method_admission`: `NOT_ADMITTED`
- `implementation_authorization`: `NOT_AUTHORIZED`
- `claim_status`: `NO_NEW_SCIENTIFIC_EVIDENCE`
- `authority_relation`: 细化 ADR 0037；服从 `CONTEXT.md`、`active_phase.md` 与唯一 live plan
- `execution_in_this_task`: `0 source search / 0 solve / 0 PINN implementation / 0 training / 0 formal / 0 GPU`

## 1. 证据身份

引用 ChatGPT 会话对 Q54–Q58 的回答是用户已接受的规划输入，不是一手来源、数值结果或 novelty clearance。回答中的来源波形、论文图像、许可和同期工作陈述只有在未来 G0 或获批的新颖性审查回到论文、Supplement、作者资产与固定版本后，才可升级为外部科学事实。本轮只把可直接审计的数学混淆、案例隔离和停止逻辑写入计划。

## 2. Q54–Q58 单一整合

| 问题 | 接受的修订 | 对路线的改变 |
|---|---|---|
| Q54 协议轴 | `REVISE A` | 从“幅值轴”改为来源锚定、固定时长事件段波形缩放轴；禁止纯幅值/纯速率因果措辞 |
| Q55 来源保真 | `REVISE A` | 单端口量或单空间图不够；来源对齐单周期须同时通过端口轨迹与跨事件空位空间状态 |
| Q56 身份门 | `REVISE A` | 身份试验从 FULL_PLAN 拆出为单独、先审后批的 pre-pilot protocol；qualification 数据不回流 pilot/formal |
| Q57 场 kink | `REVISE A` | 在 `SIDE+` 之外增加 `FIELD_KINK_PLUS`，排除事件时间平移、detector 与错结点解释 |
| Q58 新颖性 | `REVISE A` | 在 FULL_PLAN 前增加 `NOVELTY_SUFFICIENCY_GATE`；标准 hinge、复杂对象或五点拟合均不足以支撑方法主张 |

## 3. 来源锚定的派生波形缩放轴

G0 选定初态分支后，唯一轴写为

\[
V(t;a)=V_{\mathrm{fixed}}(t)+a\,\hat v_E(t),
\]

其中 `E=RESET` 用于连续 CF 分支；只有 exact finite-gap restart 分支才允许 `E=SET`。`v_hat_E` 的起止时间、转折点、极性与形状冻结；其他波段和完整两周期总时长不随 `a` 改变。公共身份为：

```text
SOURCE_ANCHORED_DERIVED_WAVEFORM_SCALE_AXIS
```

分支名称分别为 `fixed-duration reset-waveform-scale axis` 与 `fixed-duration set-waveform-scale axis`。`a0` 必须精确恢复 G0 资格化的来源波形；`epsilon=rho*a0`，`rho, rho/2, rho/4`、双侧 admissible envelope 与无 clipping 合同均在结果前冻结。所有视图按同一 physical time 配对。

允许的论文措辞仅是“对固定时长事件段 waveform scaling 的局部响应”。如果未来一手核验显示来源的固定扫描语义使该 A′ 家族不可容许，或论文故事必须把它拆成纯幅值或纯 ramp-rate 因果效应，则当前 TKF 路线停止；不得改用时间归一化掩盖不同 history，也不得加入第二速率轴救援。

## 4. 来源模型保真门

G0 须冻结一个来源对齐单周期案例、可比较变量、数字化方法与联合不确定性；G1 的基础 coarse/medium/fine 案例承载实际比较，不新增 intent。最低同时通过：

1. 可数字化的完整 I–V 或 G–V 区段、事件极性与来源可支持的阈值区间；来源只给离散点时只比较这些点；
2. 至少两个与冻结初态分支相容、跨越同一来源支持事件的空位空间状态；连续 CF 分支最低为 gap 形成前与 RESET gap 形成后，exact restart 分支必须含精确来源 snapshot 及其下一来源状态；来源若给 SET 后状态则一并比较；
3. 预冻结 ROI、gap 位置、耗尽区面积、最小 gap 厚度与 vacancy contour；`T`、`phi` 只作守卫；
4. 保守合并图像数字化、像素/色标、来源状态定位、网格/时间/非线性容差与 detector 不确定性；
5. 端口与空间变量全部同时通过，不用加权总分掩盖任一错误。

决定 gap 拓扑或绝对时间的 mobility、初态 gap、热边界、力学或其他物理量不得按结果拟合；缺失即 No-Go。若只能得到定性趋势，身份降为：

```text
LITERATURE_INSPIRED_SYNTHETIC_BENCHMARK_UNVALIDATED
```

它可以保留为内部资产，但不能支撑当前 HFO 来源对齐方法论文，也不自动转为 benchmark/resource paper。

## 5. `FIELD_KINK_PLUS`

固定物理时间下的 apparent kink 可能只来自事件时间随协议变化。若

\[
y(x,t;a)=\bar y(x,t-t_e(a);a),
\]

则 `partial_a y` 含 `-t_e'(a) partial_t y_bar`。因此 future oracle/diagnostic 阶段只允许训练外单一时间平移

\[
\tilde y(x,\tau;a)=y(x,\tau+t_e(a);a),
\]

其中 `t_e` 由 G1 冻结的连续 gap progress variable 和固定阈值产生。窗口、插值、公共有效区间、阈值扰动与对齐不确定性须先冻结；禁止 DTW、相关性最优或非线性时间扭曲。对齐结果只作身份诊断，headline 仍报告 physical-time 事件误差。

`FIELD_KINK_PLUS` 要求对齐后的连续 `c_v/J_v` 在 `epsilon, epsilon/2, epsilon/4` 上同时满足：超过数值与对齐不确定性；不按光滑曲率坍缩；中细网格与 detector 扰动方向稳定；出现在冻结 gap ROI 和固定 flux 截面；与 gap vacancy mass 和端口方向一致；载荷主要位于 transport，而非只在 `T/phi`、hard connectivity 或 I–V threshold 中出现。

错结点控制冻结为

\[
q_\eta=q_0+\delta q_1+\delta^2q_2+\psi_\eta(\delta)k,\qquad
\psi_\eta(\delta)=|\delta-\eta|-|\eta|,
\]

并使用镜像 `eta=+1/2` 与 `eta=-1/2`。中心结点若不能同时胜过两者，或对齐后 jump 落入不确定性、被纯时间位移解释、依赖对齐阈值/窗口、只存在于 hard detector/port，裁决 `TKF_FIELD_IDENTITY_NO_GO`。

## 6. 独立身份协议与数据隔离

未来须单独形成并由用户审查、授权：

```text
TKF_DIAGNOSTIC_IDENTITY_PROTOCOL
```

其前提为 `SOURCE+ / EVENT+ / SIDE+ / RAW_COMPETENT / NOT_NO_BOTTLENECK / TRANSPORT_SIDE_REPRESENTATION_BOTTLENECK+ / FIELD_KINK_PLUS / PUBLIC_BACKBONE_UNIQUE`。最小臂只含公共冻结 base、TKF-CANON、smooth4、`k=0` 代数检查及中心/镜像错结点身份控制；五个训练视图不变，`delta=±1/4` 仅作盲评价。不得加入完整 SA pilot、formal、adaptive sampling/weighting、clock 或额外方法模块。

qualification case IDs 与 `delta=±1/4` oracle 轨迹不得用于 loss、checkpoint、epsilon/阈值/结点选择，也不得在后续 pilot/formal 中再次作为效应估计或测试数据。通过只记：

```text
TKF_DIAGNOSTIC_IDENTITY_STATUS=PASS
TKF_CANON_STATUS=ELIGIBLE_FOR_FULL_PLAN_FINALIZATION_NOT_PILOT_AUTHORIZED
```

失败只记：

```text
TKF_DIAGNOSTIC_IDENTITY_STATUS=FAIL
TKF_CANON_STATUS=METHOD_VETO_IDENTITY_FAILED
```

## 7. 新颖性充分性门

FULL_PLAN 前的 bounded primary-source refresh 必须覆盖 parameter/sensitivity/gPINN/Sobolev/DC-PINN、hinge/spline/piecewise bases、branch/continuation/bifurcation、nonsmooth/contact/active-set、derivative-enhanced operators、phase-field/NP/memristor PINNs，以及同期 one-sided/cusp/hinge 工作。

pre-FULL_PLAN 的 novelty gate 只做两件事：以 bounded primary-source refresh 排除 direct-near 等价；确认 FULL_PLAN 可以用非循环的强基线/负控检验一个窄主张。它不把尚未运行的基线写成已胜出证据。未来只有在 field-kink-qualified 工作域内，TKF-CANON 实际相对 SA/direct residual-Jacobian、平滑参数化 PINN、smooth4、镜像错结点、wider raw 与 extra-work raw 显示 held-out microview 和完整两周期事件能力，才可能保留该主张。`|delta|` 输入、新增 coefficient field、HFO 对象、架构图、证据路由、五视图拟合、`k` 热图或只胜 vanilla raw 均只是工程成分。

若 direct-near 工作覆盖 load-bearing primitive、相同因果主张与可比完整事件证据，或最终只剩“标准 hinge feature 用于 HFO”，则：

```text
NOVELTY_SUFFICIENCY_GATE=FAIL
TKF_CANON_STATUS=METHOD_VETO_NOVELTY_INSUFFICIENT
```

关闭当前方法论文；不自动追加 learned knot、第二 kink、多块机制、clock、adaptive 模块、新对象或另一论文类型。

## 8. 更新后的证据链与当前状态

```text
SOURCE_CONTRACT
  -> SOURCE_MODEL_FIDELITY
  -> EVENT
  -> SIDE
  -> RAW_COMPETENCE
  -> TEMPORAL/SPATIAL_DIAGNOSIS
  -> FIELD_KINK_PLUS
  -> TKF_DIAGNOSTIC_IDENTITY
  -> NOVELTY_SUFFICIENCY
  -> FULL_PLAN may be finalized for user review
  -> separate approval still required before pilot
```

当前准确状态：

```text
TKF_ROUTE_VERDICT=REVISE_BEFORE_FULL_PLAN_FINALIZATION
FULL_PLAN_STATUS=CONDITIONAL_DRAFT_NOT_FINALIZED
FULL_PLAN_FINALIZATION_GATE=SOURCE_MODEL_FIDELITY_FIELD_KINK_DIAGNOSTIC_IDENTITY_AND_NOVELTY_PASS_REQUIRED
PROTOCOL_AXIS_STATUS=SOURCE_ANCHORED_DERIVED_WAVEFORM_SCALE_AXIS_PENDING_G0
SOURCE_MODEL_FIDELITY_STATUS=REQUIRED_NOT_RUN
FIELD_KINK_STATUS=FIELD_KINK_PLUS_REQUIRED_NOT_RUN
TKF_DIAGNOSTIC_IDENTITY_STATUS=SEPARATE_PROTOCOL_REQUIRED_NOT_AUTHORIZED
NOVELTY_SUFFICIENCY_STATUS=REQUIRED_NOT_RUN
METHOD_ADMISSION=NOT_ADMITTED
IMPLEMENTATION_AUTHORIZATION=NOT_AUTHORIZED
SCIENTIFIC_METHOD_CLAIMS=NONE
```

当前 G0–G1 live plan 的上限为 `13 intents / <=48 h wall / <=64 CPU-core-h / 0 PINN`；第 13 个 intent 是 ADR 0038 增加的 thermal-feedback-off 配对。`delta=±1/4`、错结点控制、身份 MVE 和 novelty refresh 均属于未来另批工作。
