# HFO-NP-v1 Q59–Q63：CTH 语义、热因果、可容许性与效用整合

- `date`: `2026-08-25`
- `document_role`: `ACCEPTED_PLANNING_REVISION_DETAIL_NOT_LIVE_PLAN`
- `status`: `REVISE_BEFORE_FULL_PLAN_FINALIZATION`
- `method_target`: `CTH_PINN`
- `method_admission`: `NOT_ADMITTED`
- `implementation_authorization`: `NOT_AUTHORIZED`
- `claim_status`: `NO_NEW_SCIENTIFIC_EVIDENCE`
- `authority_relation`: 细化 ADR 0038；服从 `CONTEXT.md`、`active_phase.md` 与唯一 live plan
- `superseded_in_part_by`: Q64–Q68 身份角色分离、固定锚点、共同输出变换与双轴 Pareto 以 ADR 0039 及对应整合为准
- `execution_in_this_task`: `0 source search / 0 solve / 0 PINN implementation / 0 training / 0 formal / 0 GPU`

## 1. 单一整合

| 问题 | 用户接受的答案 | 对路线的约束 |
|---|---|---|
| Q59 方法语义 | `A` | TKF-CANON 改名 CTH-PINN；只主张有限容量/预算下的 hinge 归纳偏置，不主张真实物理 kink |
| Q60 系数可容许性 | `A` | 共享初态与协议不变边界逐系数硬满足，禁止跨视图抵消和候选专属软 penalty |
| Q61 热因果 | `A` | G1 增加一个 medium thermal-feedback-off 配对 intent；热反馈不显著即停止当前电热方法路线 |
| Q62 力学分支 | `A` | 来源保真或事件若必须依赖力学，当前三块路线停止并另立 PLAN，不静默加第四块 |
| Q63 协议束效用 | `A` | 增加 aggregate-compute-matched 独立逐协议 strong raw；联合求解无非支配价值即停止 |

## 2. CTH 的诚实身份

CTH-PINN 保留 canonical transport basis

\[
q_{\mathrm{tr}}(x,t,\delta)
=q_0(x,t)+\delta q_1(x,t)+\delta^2q_2(x,t)+|\delta|h(x,t),
\]

但 `h` 只称 **hinge coefficient field**。它和同一 PDE/IC/BC 下的其他系数共同构成有限预算参数化，不增加独立方程、标签或物理信息。有限差分、三尺度趋势、`h` 热图或模型的一侧斜率差均不能证明真实解映射不可微。允许的最窄命题是：在 `FIELD_HINGE_RELEVANCE_PLUS` 工作域中，显式 hinge 是否相对强平滑参数化和计算匹配基线改善 held-out 协议响应与完整 gap 事件。

## 3. 系数层物理可容许性

CTH 与 smooth4 必须共用同一硬变换和系数网络容量。对于所有协议共享的初态和边界：

- 参数相关浓度分量在 `t=0` 分别消失，不能只让五个组合值碰巧相同；
- blocking/no-flux 边界上的每个参数相关法向通量分量分别为零；
- 来源固定的浓度、界面或其他协议不变条件逐系数保持；
- applied electrical waveform 是唯一允许随 `a` 改变的外部条件，且继续服从 ADR 0037 的 fixed-duration waveform-scale A′。

这项合同用于消除跨视图抵消和隐藏自由度；它不是新的训练技巧或候选独占优势。

## 4. 热因果和力学止损

G0 先回源确认温度如何反馈到 vacancy transport。G1 的 thermal-off ablation 保留同一电学和准稳态热方程，只把 transport 中的温度依赖冻结在预声明参考温度，从而隔离 `T -> transport`。比较使用基础 medium case，不读取 side 或方法结果；效应必须高于 medium/fine 综合数值不确定性。失败状态为 `HFO_THERMAL_CAUSALITY_NO_GO`，预算不足为 `INCONCLUSIVE_BUDGET_EXHAUSTED`。

若完整来源模型必须含力学化学势才能同时通过端口与空间保真，当前 HFO 三块 PINN 对象不再成立。该事实只能触发停止和新的对象 PLAN，不能在同一计划内新增 mechanics block 或把力学项删除为 `ENGINEERING`。

## 5. 联合协议束的效用 kill

未来强基线增加独立逐协议 strong raw PINN：五个训练协议分别求解，其总 forward、残差点、自动微分、更新、closure、墙钟与峰值内存按完整协议束记账。CTH 的效用必须同时面对：

1. 五个已见协议的事件保真不能在相近总成本下被独立求解严格支配；
2. `delta=+/-1/4` 等未见协议上的预测无需新增训练，并相对强平滑条件化模型显示增量；
3. 所有质量、no-flux、端口、温度和 PDE 守卫不退化。

若联合模型既没有 held-out 协议能力，也没有总协议束成本的非支配价值，裁决 `CTH_BUNDLE_UTILITY_NO_GO`。不能用方法图、系数场可视化或单次推理便宜掩盖训练总成本。

## 6. 当前边界

本整合不证明 HFO 来源合同、热因果、事件、side、field hinge relevance、raw competence、CTH 身份、效用或新颖性成立。当前仍是文档/计划审查；所有科研执行权限为 `false`。
