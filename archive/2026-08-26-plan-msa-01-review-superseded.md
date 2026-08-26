# PLAN-MSA-01：模块化来源对齐 clean-room 对象到论文初稿的最短关键路径

- `phase_id`: `PLAN_MSA_01_REVIEW`
- `lifecycle_state`: `BLOCKED`
- `blocker_id`: `PLAN_MSA_01_AWAITING_EXPLICIT_APPROVAL`
- `authorization_state`: `DOCUMENT_ALIGNMENT_AND_PLAN_REVIEW_ONLY`
- `authorization_package`: `NONE_NEW_PACKAGE_APPROVED`
- `plan_status`: `DRAFT_FOR_EXPLICIT_APPROVAL_NOT_AUTHORIZED`
- `object_selection_status`: `NO_OBJECT_SELECTED`
- `method_selection_status`: `NOT_REACHED_CONDITIONAL_CTH_PARKING_LOT`
- `claim_status`: `BOUNDED_SOURCE_PORTFOLIO_NO_GO_NO_METHOD_EVIDENCE`
- `compute_authorization`: `ZERO_BUILD_ZERO_SOLVE_ZERO_TRAINING_ZERO_GPU`
- `next_research_execution_authorized`: `false`
- `next_authorizable_package`: `MSA_A_CONTRACT_AND_METHOD_BLIND_SOURCE_SCREEN`
- `final_draft_eta`: `UNKNOWN_UNTIL_CTH_PILOT_AND_FORMAL_POWER_FREEZE`

## 1. 单一目标与终点

本路线只有一个正向目标：

~~~text
方法盲锁定一个模块化来源对齐的 clean-room 2D 氧化物电热缺陷输运对象
→ 独立 oracle 与两周期局部事件
→ strong raw 胜任但存在 transport-side 有限预算表示瓶颈
→ CTH 相对 direct/smooth/capacity/compute/wrong-knot 强控制产生可归因增量
→ sealed complete-case OOD 同时通过机制对齐 superiority 与正交 noninferiority
→ 交付证据闭合的论文初稿
~~~

终点严格分开：

- `PRIMARY_SUCCESS`：`EVIDENCE_COMPLETE_POSITIVE_CTH_MANUSCRIPT_DRAFT`，只在 formal PASS 后成立。
- `HONEST_TERMINAL`：首个硬门失败后交付有界、可复核的负证据包并关闭本论文方向。它完成研究裁决，但不冒充二区正向论文初稿。
- `NO_AUTOMATIC_FALLBACK`：不换对象、不换方法、不补机制、不追加来源、case、seed 或预算来追阳性。

历史 `PORTFOLIO_NO_GO_PACKAGE_A_FROZEN_3_FAMILIES_11_CARRIERS`、HFO-NP-v1 `WAVEFORM_TIME_NO_GO`、TaOₓ C1 及其他 No-Go 原样保留。本 PLAN 使用实质不同的“模块化来源对齐”合同，不撤销或改名任何旧失败。

## 2. 为什么这是当前最快且仍可发表的路线

上一轮三家族均在求解前因“单一来源链必须自包含全部重建量”失败。最快的可信修订不是降低物理门，也不是直接造任意 synthetic benchmark，而是：

1. 只要求一个主锚点来源闭合器件身份、二维拓扑、PDE/界面结构、IC/BC、绝对协议/history、端口与空间响应锚点及许可；
2. 最多允许两个兼容模块来源补充明确列名的材料参数或本构子合同；
3. 模块来源不得替代主锚点缺失的几何、边界、接口、绝对时间、协议顺序、响应锚点或必要机制；
4. 所有派生步骤公开登记为 `A / A_PRIME / ENGINEERING`，对象始终称 clean-room `derived/synthetic`；
5. CTH 在对象、事件、oracle 和 strong-raw bottleneck 通过前完全不可见。

这条路线直接针对已观察到的真实阻塞，又避免跨来源拼成“作者重放”的审稿致命点。

## 3. 对象合同：先冻结，再看来源

### 3.1 对象结构

对象写成：

\[
O^*=(A_{\mathrm{anchor}}, A'_{\mathrm{transparent}}, E_{\mathrm{core}})
\]

- `A_anchor`：主锚点来源中可直接核验的器件、方程、几何、IC/BC、接口、协议/history、参数或范围、响应锚点和许可事实。
- `A_prime_transparent`：仅允许二维/轴对称约化、无量纲化、守恒离散、单周期到多周期的状态连续携带、固定协议邻域缩放、表格插值和预声明有限分支枚举。
- `ENGINEERING`：网格、时间步、容差、稳定化、求解器、输出频率、文件格式和已验证不改变物理的域截断。
- `UNKNOWN_FATAL`：无法给出可信有限范围，或缺项决定器件拓扑、必要 BC/interface、绝对时间、主要电/热/输运本构、协议顺序、必要机制或来源响应对齐。
- `UNKNOWN_BRANCHABLE`：来源支持有限范围、对象身份不变、求解前可冻结为有限分支且不得事后删枝。

为压缩成本，优先零分支；最多允许一个二值 `UNKNOWN_BRANCHABLE` 轴。第二个不确定轴或任何拓扑分支直接使该 bundle No-Go。两分支以后都必须通过对象、oracle、事件、raw、development 和 formal 门。

### 3.2 来源组合边界

每个候选 bundle 只能包含：

- 1 个主锚点来源；
- 最多 2 个模块来源；
- 最多 1 个二值不确定性轴。

模块来源只可补：

- 与主锚点同材料体系、量纲和温度/场强范围兼容的 transport 参数；
- 热物性参数；
- 主锚点已明确采用但未完整数值化的本构子函数。

模块来源不可补：

- 器件几何或材料域拓扑；
- vacancy/内部态的决定性边界与接口；
- 驱动波形、绝对持续时间、history 或状态顺序；
- 主锚点没有的物理机制；
- 端口或空间响应锚点；
- 为匹配结果而反演的自由参数。

已关闭候选不能作为“重新通过”的主锚点。其已核验且许可允许的事实只能作为模块线索，并须在新 bundle 中重新通过兼容性审查；这不撤销旧 No-Go。

## 4. 最短关键路径

### S0 — 合同冻结

当前文件已给出完整草案；只有用户明确批准 `MSA-A` 后才转为冻结执行合同。

交付：

- 对象 bundle 模板；
- `A/A_prime/ENGINEERING/UNKNOWN` 判定表；
- 方法盲查询与排序规则；
- 两个候选 bundle 上限、八个新增一手载体上限和三日 timebox；
- 单候选与组合级停止量词。

PASS：

~~~text
MSA_CONTRACT_FROZEN
METHOD_BLIND_MODULAR_OBJECT_SCREEN_PROTOCOL_FROZEN
~~~

FAIL：

~~~text
MODULAR_CONTRACT_NOT_DEFENSIBLE
ABANDON_CURRENT_CTH_DEFECT_TRANSPORT_PAPER_DIRECTION
~~~

### S1 — 方法盲 bundle 筛选与唯一对象锁定

授权包：`MSA-A`。仅静态一手来源、许可、版本与 prior-art 核验；零构建、零求解、零训练。

预算：

- 最多 8 个新增一手载体；
- 最多 2 个候选 bundle；
- 最长 3 个日历日；
- 已核验来源可复用，不重复计作“新增”，但必须重新登记其 bundle 角色。

排序只看：

~~~text
主锚点完整性与许可
> 二维电—热—动态内部态闭环
> 绝对协议/history 与端口+空间锚点
> 模块兼容性与分支数
> clean-room 重建和完整 case 能力
> 预计 CPU 成本
~~~

CTH、hinge、kink、wrong-knot、PINN 表现或任何方法偏好不得参与生成、排序或换对象。

单 bundle 八门：

1. 主锚点身份、固定版本和许可；
2. 二维及以上真实器件域；
3. 电流/电势—Joule 热—动态守恒内部态闭环；
4. 主锚点自包含几何、域、IC/BC/interface；
5. 绝对驱动、持续时间、顺序、history 和观测窗；
6. 端口轨迹加至少两个跨事件空间/内部态锚点；
7. 模块来源物理、量纲、条件范围和许可兼容；
8. 零或单一二值分支下可建立独立守恒 oracle 与互斥完整 case pools。

第一个全 PASS bundle 立即锁定；不再审查第二个。

PASS：

~~~text
MODULAR_OBJECT_BUNDLE_SELECTED
OBJECT_SELECTION_METHOD_BLIND_PASS
~~~

单候选失败：

~~~text
MODULAR_BUNDLE_CANDIDATE_NO_GO
~~~

两个 bundle 全失败或任一预算耗尽：

~~~text
MODULAR_SOURCE_SCREEN_NO_GO
ABANDON_CURRENT_CTH_DEFECT_TRANSPORT_PAPER_DIRECTION
~~~

### S2 — CPU micro-oracle：一天内先杀掉无信号对象

授权包：`MSA-B1`。

预算：

- 最多 10 个 solver intents；
- 最多 32 CPU core-hours；
- 最长 24 小时；
- 不搭完整生产训练框架。

每个允许分支只做：

- coarse 与 medium 两级；
- zero-drive 守恒/范围；
- source-alignment case；
- 预冻结事件 bracket；
- 中心 case 的 thermal-feedback-off 配对。

必须同时看到：

- 有限、守恒、范围合格的数值场；
- 端口与至少一个空间响应在预冻结联合不确定性内方向和量级相符；
- 热反馈对输运或事件的效应可分离于离散误差；
- 至少一个局部、部分覆盖、可恢复事件信号候选。

PASS：

~~~text
OBJECT_MICRO_ORACLE_SIGNAL_PASS
~~~

任一失败：

~~~text
OBJECT_MICRO_ORACLE_NO_GO
SOURCE_RESPONSE_ALIGNMENT_NO_GO
THERMAL_FEEDBACK_EFFECT_NOT_RESOLVED
CORE_BRANCH_ROBUSTNESS_NO_GO
CURRENT_PAPER_ROUTE_CLOSED
~~~

### S3 — 完整 oracle、事件与案例池资格化

授权包：`MSA-B2`。

预算：

- 最多 24 个 solver intents；
- 最多 96 CPU core-hours；
- 最长 72 小时。

硬门：

1. 独立空间与时间收敛；不能用 medium/fine“看起来接近”代替；
2. charge/current、内部态质量、no-flux、范围、温度和端口守卫；
3. 来源端口轨迹与至少两个跨事件空间状态的联合对齐；
4. thermal-on/off 因果效应高于两分支各自数值不确定性；
5. 至少两个连续周期的局部、部分覆盖、空间可辨且可恢复事件；
6. detector、ROI、事件时间、误差地板和 evaluator 在 PINN 前冻结；
7. qualification、development、formal-aligned、formal-orthogonal 四类完整 case 互斥；
8. 所有允许来源分支都通过，不事后删枝。

PASS：

~~~text
OBJECT_LOCKED_ORACLE_QUALIFIED
EVENT_QUALIFIED
CASE_POOLS_SEALED
~~~

FAIL：

~~~text
ORACLE_CONVERGENCE_NO_GO
SOURCE_MODEL_ALIGNMENT_NO_GO
EVENT_QUALIFICATION_NO_GO
MODULAR_OBJECT_BRANCH_ROBUSTNESS_NO_GO
CURRENT_PAPER_ROUTE_CLOSED
~~~

### S4 — strong raw 能力与 CTH 非循环准入

授权包：`MSA-C1`。GPU 必须在批准中写明；未写明即 `GPU=false`。

预算：

- 1 次不投票的吞吐 smoke；
- 最多 32 exclusive GPU-hours；
- 最长 48 小时；
- 只使用 development cases，formal 不可见。

先裁决 strong raw：

~~~text
RAW_INCOMPETENT_ROUTE_NO_TEST
NO_BOTTLENECK
BOTTLENECK_INDETERMINATE
RAW_COMPETENT_ONE_BOTTLENECK_IDENTIFIED
~~~

只有最后一项且瓶颈为下列身份才允许继续：

~~~text
TRANSPORT_SIDE_FINITE_BUDGET_REPRESENTATION_BOTTLENECK_PLUS
~~~

然后只用 oracle 做 CTH 前门，不训练 CTH：

- 来源锚定的标量协议坐标、中心点 a0 与尺度 epsilon 在看方法结果前冻结；
- 三尺度一侧响应相关性成立；
- 排除纯事件时间平移、smooth curvature、detector/ROI 伪影和 history 不足；
- 瓶颈定位到 transport state/flux，而不是通用优化、sampling、capacity 或端口头；
- bounded exact/direct-near novelty 搜索未覆盖同一 primitive、因果主张和可比完整事件证据。

PASS：

~~~text
CTH_PRENEURAL_ADMISSION_PASS
~~~

否则：

~~~text
CTH_NOT_ADMITTED
NON_CTH_BOTTLENECK
METHOD_VETO_NOVELTY_INSUFFICIENT
CURRENT_METHOD_PAPER_ROUTE_CLOSED
~~~

### S5 — CTH development funnel 与强控制

授权包：`MSA-C2`。

CTH 只允许以下诚实身份：

\[
\delta=(a-a_0)/\epsilon
\]

\[
q_{\mathrm{tr}}=q_0+\delta q_1+\delta^2 q_2+|\delta|h_\theta,
\qquad (c_v,J_v)=B(q_{\mathrm{tr}})
\]

约束：

- a0 固定为来源锚点，不学习、不重定位；
- q0、q1、q2、h 不读取 delta、side 或 view ID；
- B 为共享、C1、hinge-blind 且来源兼容的输出变换；
- CTH 只是有限容量/预算下的 canonical hinge 归纳偏置，不声称真实物理 kink。

预算：

- 最多 64 exclusive GPU-hours；
- 最长 7 日；
- 所有失败 intent 计入 gross compute。

第一阶段四臂：

1. frozen strong raw；
2. SA/direct residual-Jacobian；
3. same-complexity smooth6；
4. CTH。

CTH 未同时优于 direct 与 smooth6，立即 `CTH_PILOT_NO_GO`。只有四臂 PASS 后才补齐正向结论必需控制：

- parameter-matched wider raw；
- compute-matched extra-work raw；
- mirrored wrong-knot；
- smooth-absolute control；
- aggregate-compute-matched independent-per-view raw；
- IND-5/blind microviews/IND-7 协议束效用。

统计单位是完整 case。对方法 m、case i、seed s：

\[
Z_{m,i,s}=\frac{1}{2}\sum_{k=1}^{2} E_{m,i,k,s}
\]

\[
\widetilde Z_{m,i}=\operatorname{median}_{s} Z_{m,i,s},
\qquad
D_{i,c}=\widetilde Z_{c,i}-\widetilde Z_{\mathrm{CTH},i}
\]

seed 只作 case 内算法重复。S3 在任何 PINN 结果前冻结来源/事件物理实用阈值 `M_phys` 与 paired evaluator uncertainty `U_pair`；若 `M_phys <= 2 U_pair`，该 case 记 `CASE_METHOD_EFFECT_NOT_RESOLVABLE`，不得用于阳性投票。

CTH positive pilot 必须同时满足：

- 相对 direct 与 smooth6 的 case-level 改善超过 `M_phys`；
- wider raw 与 extra-work raw 不在等价带内追平；
- wrong-knot 明确退化，smooth-absolute 不吸收收益；
- independent-per-view raw 不以可比总计算获得同等效用；
- c_v、J_v、T、phi、mass/no-flux 和 port 守卫不劣；
- CTH 不被任一合格控制在计算—误差 Pareto 上严格支配；
- 所有允许来源分支同向通过。

PASS：

~~~text
CTH_PILOT_SUPPORTED
~~~

FAIL：

~~~text
CTH_PILOT_NO_GO
CTH_BASIS_SPECIFICITY_NO_GO
CTH_BUNDLE_UTILITY_NO_GO
COMPUTE_PARETO_DOMINATED
CURRENT_METHOD_PAPER_ROUTE_CLOSED
~~~

### S6 — sealed formal OOD

授权包：`MSA-D`，必须单独批准。Development PASS 不自动打开 formal。

formal 只保留三臂：

1. strong raw；
2. development 中最强非 CTH challenger；
3. CTH。

统计合同：

- 完整 case 为独立单位；
- 两周期等权，seed 先在 case 内聚合；
- pilot 的 case-level paired 方差用于 power/precision；
- alpha=0.05，power 至少 0.80；
- 样本数、seed、失败计票、margin、CI 方法和总预算在开封前冻结；
- 规划硬上限 128 exclusive GPU-hours；预算不足则不打开 formal，pilot 不得改名 formal。

对 aligned family 的 paired improvement D：

\[
L_{0.95}(D^{\mathrm{aligned}})>M_{\mathrm{aligned}}
\]

必须同时相对 strong raw 与最强 challenger 成立。随后才检验 orthogonal family：

\[
L_{0.95}(D^{\mathrm{orthogonal}})>-M_{\mathrm{harm}}
\]

并要求全部物理守卫非劣。采用 aligned-first gatekeeping。

PASS：

~~~text
FORMAL_CTH_CLAIM_SUPPORTED
~~~

FAIL：

~~~text
FORMAL_SUPERIORITY_NO_GO
FORMAL_NONINFERIORITY_NO_GO
FORMAL_POWER_BUDGET_INSUFFICIENT
POSITIVE_MANUSCRIPT_CLAIM_NO_GO
~~~

不得重封、改 margin、换 case、筛失败 intent、补 seed 或追加预算。

### S7 — 论文初稿并行写作与终稿冻结

授权包：

- `MSA-E0`：从 S1 起并行写本地 skeleton；只写来源边界、方法公式、实验合同、图表占位和已成立负证据，不写结果阳性。
- `MSA-E1`：S6 裁决后写证据闭合初稿、图表、补充材料和复现说明。
- `MSA-F`：Git、云端、作者联系、投稿和外部发布，永远单独批准。

唯一允许的正向故事：

~~~text
透明模块化来源对齐对象
→ 非神经事件与 transport-side hinge relevance
→ strong raw 胜任但存在特定有限预算瓶颈
→ CTH 相对 direct/smooth/capacity/compute/wrong-knot 的可归因增量
→ sealed aligned superiority + orthogonal noninferiority
~~~

禁止表述：

- 实验验证、作者原生重放或 source-native oracle；
- 真实物理 kink 或数学不可微；
- 世界首创、普适性、SOTA 或期刊接收保证；
- 用端口曲线替代空间事件、守恒与收敛；
- 把模块拼接隐藏为单一作者模型。

## 5. 论文七图与主表

1. 主锚点、模块来源、A/A_prime/ENGINEERING 与不确定性分支；
2. solver 收敛、来源对齐、热反馈和两周期局部事件；
3. strong raw competence 与瓶颈定位；
4. oracle-only 一侧相关性及 shift/smooth/detector 排除；
5. development 四臂与完整控制漏斗；
6. 参数量、实际计算、gross failed compute 与 IND Pareto；
7. sealed formal aligned superiority 与 orthogonal noninferiority。

主表只放 complete-case formal 结果、95% 区间、物理守卫和实际计算；全部 development 超参数、失败 intents、分支结果、wrong-knot、smooth/capacity/compute 消融和负结果进入补充材料。

## 6. 授权包与资源上限

| 包 | 内容 | 上限 | 当前状态 |
|---|---|---:|---|
| MSA-A | 合同冻结、方法盲来源/许可/兼容性与 bounded prior-art | 8 新载体、2 bundles、3 日 | NOT_AUTHORIZED |
| MSA-B1 | CPU micro-oracle | 10 intents、32 core-h、24 h | NOT_AUTHORIZED |
| MSA-B2 | 完整 oracle/event/case pools | 24 intents、96 core-h、72 h | NOT_AUTHORIZED |
| MSA-C1 | strong raw 与非神经 CTH 准入 | 32 GPU-h、48 h | NOT_AUTHORIZED |
| MSA-C2 | CTH development 与全部正向控制 | 64 GPU-h、7 日 | NOT_AUTHORIZED |
| MSA-D | sealed formal | power-derived，硬上限 128 GPU-h | NOT_AUTHORIZED |
| MSA-E0 | 本地无结果 skeleton | 可与 S1–S6 并行 | NOT_AUTHORIZED |
| MSA-E1 | 证据闭合本地初稿 | formal 裁决后 | NOT_AUTHORIZED |
| MSA-F | Git、外部发布、投稿或联系 | 单独批准 | NOT_AUTHORIZED |

`PLAN_APPROVED != EXECUTION_AUTHORIZED`。预算不跨包转移，上一包 PASS 也不自动批准下一包。最快的下一授权只能是 `MSA-A`；如用户希望同步节省写作时间，可同时明确批准 `MSA-E0`，但这仍不开放任何计算。

## 7. 时间预期

- MSA-A：1–3 日得到对象合同 Go/No-Go；
- MSA-B1 + B2：顺利时 4–7 日得到 oracle/event 决定性裁决；
- MSA-C1 + C2：顺利时 7–14 日得到 idea development Go/No-Go；
- MSA-D：5–10 日，前提是 power 与硬件预算足够；
- MSA-E1：因 E0 并行，formal 后 2–4 日收口。

最早的条件式正向初稿窗口约 20–35 日，不是承诺。若首个对象、solver、事件、raw、CTH 或 formal 任一门失败，会更早得到可信 No-Go。日历不得降低来源、事件、收敛、控制、统计或新颖性门。

## 8. 当前唯一下一动作

当前没有科研执行授权。用户若决定启动本路线，必须明确写出：

~~~text
批准授权包 MSA-A，按 PLAN-MSA-01 执行；不包含 build、solve、training、GPU、formal、Git 或外部发布。
~~~

在此之前：

~~~text
NEXT_RESEARCH_EXECUTION_AUTHORIZED=false
OBJECT_SELECTION_STATUS=NO_OBJECT_SELECTED
METHOD_SELECTION_STATUS=NOT_REACHED_CONDITIONAL_CTH_PARKING_LOT
~~~
