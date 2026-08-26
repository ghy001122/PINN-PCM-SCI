# HFO-NP-v1 Q30–Q36 PINN 方法与训练合同整合

- `date`: `2026-08-25`
- `document_role`: `FUTURE_PINN_CONTRACT_INTEGRATION_NOT_LIVE_PLAN`
- `status`: `ACCEPTED_PLANNING_REFINEMENT_NOT_AUTHORIZED`
- `claim_status`: `NO_NEW_SCIENTIFIC_EVIDENCE`
- `input`: ChatGPT 会话“深度论文审查”对 Q30–Q36 的对抗性回答
- `authority_relation`: 服从 `CONTEXT.md`、ADR 0031、ADR 0032、`active_phase.md` 与唯一 live plan
- `supersedes_in_part`: `2026-08-24-hfo-post-g1-pinn-roadmap-integration.md` 的 side 候选优先级、cKC 细节与训练比较假设
- `extended_by`: `2026-08-25-hfo-q37-q43-strong-raw-contract-integration.md` 与 ADR 0033；进一步冻结耦合模式、backbone 选优、计算公平、raw competence 与失败重跑
- `execution_in_this_task`: `0 source search / 0 solve / 0 implementation / 0 training / 0 formal / 0 GPU`

## 1. 整合裁决

外部回答作为规划与对抗分析输入，不自动成为一手科学证据；其中的论文、代码、release 和许可事实进入正式方法计划前仍须回到项目一手来源账本核验。用户接受的是下列方法治理与数学边界：

| 问题 | 当前决定 | 对先前推荐的影响 |
|---|---|---|
| Q30 side 方法 | `DEFER` | 撤回“SRF 为默认首选”；先定位载荷并比较简单直接近邻 |
| Q31 cKC-NP | `ACCEPT_CONDITIONAL_ON_TEMPORAL_PLUS` | 保留 A，但冻结物理时间、端点归一、低维正速率与守恒边界 |
| Q32 Fourier | `ACCEPT_AS_BACKBONE_QUALIFICATION` | 从两臂扩为 raw、wider-raw、deterministic spatial Fourier 三臂 |
| Q33 curriculum | `REVISE_NO_ATTRIBUTION_CURRICULUM` | 撤回公共 time-prefix；只把它作为 temporal comparator |
| Q34 动态权重 | `REVISE_BOUNDED_POINTWISE_COMPARATOR_ONLY` | 固定块权重；best-method 仅可组内有界变权 |
| Q35 自适应采样 | `ACCEPT_BEST_METHOD_ONLY` | attribution 固定 support；只单列一种强 adaptive baseline |
| Q36 优化与诊断 | `ACCEPT_FIXED_DIAGNOSTIC_ONLY` | 固定更新数；遥测不得在线改变证据运行 |

这些决定不改变 `SOURCE → EVENT → SIDE → RAW_COMPETENCE → TEMPORAL/SPATIAL → ONE_METHOD_PILOT` 的顺序，也不选择任何 headline 方法。

## 2. Q30：side 方法保持未选择

`SIDE+` 证明局部协议邻域含有不能由冻结 smooth null 解释的信息，但不证明该信息应由哪个网络块或架构表示。只有未来同时满足 `SOURCE+ / EVENT+ / SIDE+ / RAW_COMPETENT` 后，才运行以下候选梯级：

1. 在输运 residual 上建立 SA/Jacobian 式直接参数切线强近邻；
2. 建立 `(c_v,J_v)` 等物理输出的一侧 finite-secant control；
3. 对输运、电学、热学输出分别做一侧斜率跳跃和相对时序定位；
4. 仅当简单近邻不足且载荷主要位于输运块时，才另立 transport-only 一侧架构 PLAN。

SRF 只是第 4 步的 parking-lot 实例，不再享有优先进入权。若显著一侧响应首先或独立出现在电学/热学块，应重新设计方法，而不是自动扩大为三块 side architecture。fixed-slot latent、categorical view ID 和五个独立 heads 继续排除。

## 3. Q31：cKC-NP 的条件数学合同

只有 future strong raw 得到 `TEMPORAL+` 后才允许审查。令无量纲物理时间 `t_bar=t/T_f`，使用低维函数 `g(t_bar,p)` 构造有界正速率

```text
a(t_bar,p) = exp(beta * tanh(g(t_bar,p))) > 0
tau(t_bar,p) = integral_0^t_bar a(xi,p) dxi / integral_0^1 a(xi,p) dxi
```

因此 `tau(0,p)=0`、`tau(1,p)=1`，且 `g=0` 严格恢复 `tau=t_bar`。`beta`、基函数数目、来源 transport 参数和是否读取 `p` 必须在方法 intent 前冻结；clock 不读取 `x`、`T` 或 `c_v`。

只有 transport 网络使用 `(x,tau,p)`。守恒项完整回拉为正速率乘 `∂c_v/∂tau` 加物理通量散度；电学和热学网络继续读取 `(x,t_bar,p)`，通量本构使用同一物理时刻的 `phi`、`T` 和 `V(t_bar,p)`。禁止把外加波形写成 `V(tau,p)`，所有五视图也必须在相同物理时间配对和评价。

最小控制包括 identity clock、固定解析 clock、protocol-blind clock、协议置乱 clock 和等参数 dummy module。若 clock 长期贴住速率边界、与 mobility 同时调节、seed 间不可辨、恶化 mass/no-flux，或只改善 tau-space loss 而不改善物理时间 gap 事件，即终止 cKC 主张。

## 4. Q32：确定性空间 Fourier 只做 backbone 资格化

方法归因前，在 development 上进行一次三臂比较：

1. raw-coordinate mixed first-order PINN；
2. 参数量匹配的 wider raw MLP；
3. 由器件长度和可解析局部空间尺度确定的 spatial Fourier PINN。

频率不是逐方法超参数，不随机、不学习，也不对协议轴 `p` 进行任意周期编码。比较须同时检查 gap soft-mask 主端点、守恒/端口守卫、梯度稳定性和实际计算；若 wider raw 达到相同效果、收益只存在于 loss、频率超过 support 可解析范围或必须逐方法调频，则 Fourier 不准入。胜者冻结后不再作为方法变量或创新点。

## 5. Q33：归因轨无 curriculum

任何改变 diffusion、mobility、activation energy、reaction 或其他决定绝对时间和 gap 拓扑的 coefficient homotopy 都不得进入 evidence-producing run。residual-block activation continuation 也只可用于实现调试，不能进入科学比较。

累计 time-prefix 只是一种 temporal comparator。若未来纳入，必须满足：

- `0<T_1<...<T_K=T_f` 由冻结波形转折或周期边界决定；
- support 从 `t=0` 起嵌套累积，旧点不删除；
- 只在真实 `t=0` 施加 IC，不在 `T_k` 创建 pseudo-IC，也不重置内部态；
- 最终阶段覆盖完整两周期；
- 与 full-horizon 控制匹配总 residual-point evaluations、PDE AD、optimizer closure、wall-clock 和各周期有效暴露量。

若它只改善第一周期、发生 backward forgetting、依赖 stage 数或 loss/event 触发时点，或 compute-matched full-horizon 达到同等结果，则判 temporal comparator 无增量。

## 6. Q34：动态权重仅作组内有界对照

方程块级 `lambda_transport / lambda_electric / lambda_thermal / lambda_ICBC / lambda_mass` 继续由无量纲化和初始梯度审计冻结。best-method 轨最多选择一种有一手来源的 pointwise residual-decay/balancing 方法，并满足：

- 权重只在同一 residual group 内变化，组内均值归一且有上下界；
- 只在 Adam 阶段按预声明周期更新，进入确定性二阶段前冻结；
- IC/BC、no-flux、global mass、port guard 和 hard constraints 不动态降权；
- 权重计算及附加梯度成本计入实际计算。

当前不冻结 BRDR、ReLoBRaLo 或其他具体实现为赢家；外部回答对它们的比较是检索线索，须在 future method PLAN 中回源后再选唯一 comparator。

## 7. Q35：自适应采样仅在 best-method 轨单列

attribution track 始终复用固定分层 support。其通过后，best-method track 最多纳入一种来源透明的 residual/causal adaptive baseline；候选池残差评估、排序、刷新、额外前向和自动微分全部计入预算，并保留预冻结的固定背景 support，防止只追逐当前高残差区域。

`top 20%`、`30% random` 或每若干步刷新都只是经验线索，不直接成为 HFO 合同。采样比例、刷新周期和候选池大小只能在 development 中一次冻结，不能按方法或 formal case 调整。

## 8. Q36：优化调度固定，遥测只诊断

所有证据臂使用 FP64、相同嵌套预算与固定更新数的 Adam→确定性二阶段调度。默认二阶段仍为 L-BFGS；若公共预检证明不可行，必须在生成任何正式 intent 前统一替换。不得按每次 loss 平台、事件误差或 oracle 指标决定切换或早停。

每个 run 记录各 residual group、梯度、IC/BC、质量、no-flux、端口、温度、非负/有界与事件守卫。只有 NaN/Inf、单位或边界实现错误等预声明的实现有效性失败可以终止无效 run；诊断曲线不能在线触发临时调权、重采样、加预算或方法救援。

## 9. 对未来 G3–G4 的具体影响

> Q37–Q43 已在 [后续 strong-raw 合同整合](2026-08-25-hfo-q37-q43-strong-raw-contract-integration.md)与 [ADR 0033](../adr/0033-qualify-coupling-mode-and-freeze-strong-raw-adjudication.md)中进一步细化；涉及耦合训练、backbone winner、有效公平控制、case/seed 与重跑时以后者为准。

- G3 strong-raw 前增加一次三臂 backbone 资格比较，但其案例数、seed 和预算必须依据 G2 吞吐量另立 PLAN；
- G3 temporal comparator 候选池可含累计 time-prefix，但不再是所有方法的公共训练流程；
- G4 `SIDE+` 路线先走直接参数切线和物理割线控制，不再默认实现 SRF；
- dynamic weighting 与 adaptive sampling 都属于 best-method 竞争力轨，不能进入 fixed-support 机制归因；
- 首轮仍采用 strong raw、最强直接近邻、唯一候选和关键 kill control 的顺序式四臂 MVE；不得把本文件列出的全部技巧堆成组合方法；
- 未获 `SIDE+` 或 `TEMPORAL+` 的模块不投票，未获 raw competence 的对象不以技巧救援。

## 10. 当前状态与下一动作

本整合只更新 future roadmap，不改变实时阶段：`HFO_NP_V1_G0_G1_PLAN_REVISED_BLOCKED / HFO_SOURCE_CONTRACT_NOT_CLOSED / NO_SCIENTIFIC_METHOD_CLAIMS`。网络规模、Fourier 频率、time-prefix 数、pointwise 权重边界、自适应采样比例、方法预算与效应门仍为 `UNKNOWN`，必须等前置证据后另行冻结。

当前唯一可申请的科学执行动作仍是 live plan 的授权包 A：G0。未经明确批准，不运行来源检索、solver、PINN、training、formal、GPU 或付费计算。
