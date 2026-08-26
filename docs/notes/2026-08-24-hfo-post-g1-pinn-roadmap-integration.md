# HFO-NP-v1 后 G1 PINN 研究路线整合

- `date`: `2026-08-24`
- `document_role`: `FUTURE_ROADMAP_INTEGRATION_NOT_LIVE_PLAN`
- `status`: `PLANNING_INTEGRATION_COMPLETE_NOT_AUTHORIZED`
- `claim_status`: `NO_NEW_SCIENTIFIC_EVIDENCE`
- `input`: ChatGPT 会话“深度论文审查”中的后续路线草案
- `authority_relation`: 服从 `CONTEXT.md`、ADR 0031、`active_phase.md` 和唯一 live plan
- `execution_in_this_task`: `0 source search / 0 solve / 0 implementation / 0 training / 0 formal / 0 GPU`
- `superseded_in_part_by`: `research_decisions_HFO_Q1_Q68.md` 与 ADR 0032–0039；覆盖 side 候选优先级、cKC、训练技巧、耦合模式、backbone 选优、计算公平、失败计票、论文主张、外推域、CTH 语义、热因果、身份角色、来源锚点、输出变换及双轴效用，阶段顺序与授权边界不变

> **当前阅读提示**：本文只保留 G2–G6 阶段骨架。当前 HFO Q1–Q68 的有效处置统一读 [决策总索引](../adr/research_decisions_HFO_Q1_Q68.md)；具体 CTH 设计以 [Q64–Q68 整合](2026-08-25-hfo-q64-q68-cth-identity-anchor-transform-and-pareto-integration.md)和 ADR 0039 为准。本文中的 SRF 优先、12-intent、qualification-case identity 等旧细节均不得覆盖唯一 live plan。

## 1. 整合裁决

引用会话提出的主顺序与当前项目方向一致：

```text
来源闭合
  → 局部两周期 gap 事件
  → TKB side 信息门
  → strong-raw 能力与瓶颈诊断
  → 按证据选择唯一方法
  → bounded pilot
  → one-shot formal OOD
  → 论文初稿
```

本轮将这条顺序整合为 G0–G6 的未来研究路线，但不把引用会话当作科学来源、用户授权或已接受数值合同。当前实际状态仍停在 G0–G1 计划待授权；G2–G6 每一阶段都必须另立执行包并再次获批。

当前最重要的路线修正是：**G1 的局部事件一旦合格，无论 TKB 得到 `SIDE+` 还是 `SIDE−`，都可以另行申请 strong-raw 诊断来判定 `TEMPORAL`；side 结果只决定 side 方法是否有入场资格。** 否则 `SIDE− / TEMPORAL+` 分支在逻辑上不可达。

## 2. 从引用会话吸收、修订与拒绝的内容

| 引用会话建议 | 本项目处置 | 理由 |
|---|---|---|
| 先对象、后方法 | 吸收 | 符合历史对象门失败教训和 ADR 0031 |
| HFO-NP-v1 作为唯一规划对象 | 保留 | 仍为 `SOURCE_CONTRACT_BLOCKED`，不等于已可实现 |
| fixed-slot SRPG 降级 | 保留 | same-network self-target 与 latent gauge 未闭合 |
| 物理输出响应场作为 side 候选 | 条件保留 | 统一名为 `SRF-PINN`；仅 `SIDE+` 后进入新方法设计 |
| 连续 CF 初态已冻结 | 不吸收 | G0 仍须在来源连续 CF 与精确 reset restart 中二选一 |
| SET/RESET 两轴组成首轮五视图 | 不吸收 | G1 只允许唯一轴的基准、`±ε`、`±ε/2` 五视图 |
| G1 的 2+2+8 intents | 以 live plan 版本替代 | 改为两周期 coarse/medium/fine 3、零驱动 1、thermal-feedback-off 配对 1、单轴双尺度 medium/fine 8，共 13 intents；既避免确定性第一周期重复，也保留热因果门 |
| `SIDE+` 后直接主推 SRPR/SRF | 收紧 | `SIDE+` 只打开方法 PLAN；还须比较 SA-PINN、直接响应和等容量多视图基线 |
| `SIDE−/TEMPORAL−` 自动转 PHA-MF | 拒绝 | 与 ADR 0031 的停止规则冲突；空间模块只能另立新科学 PLAN |
| 约 20% TEMPORAL 门、15% pilot 门、1.25× wall-clock 门 | 不冻结 | 必须由 oracle 数值地板、development 配对波动和实测吞吐量一次确定 |
| 9 bundles、36 formal trainings、24–96 GPU-h | 不冻结 | 当前没有吞吐量或配对方差证据，且 formal/GPU 必须另批 |
| JAX/FEniCSx/具体目录结构 | 仅作未来实现选项 | 在 G0 来源合同和实现接口冻结前不选框架、不建代码骨架 |

`SRPR-PINN` 在引用会话中指“分侧物理响应场”时，本文统一使用当前项目术语 `SRF-PINN`。这只是术语归一，不代表方法已选定。

## 3. 论文问题与条件式主张链

在方法尚未选择前，使用中性工作题目：

> **Evidence-Routed PINNs for Local Electrothermal Defect-Transport Events in HfO₂₋ₓ Memristors**

中文暂定为：

> **面向 HfO₂₋ₓ 忆阻器局部电热缺陷输运事件的证据路由 PINN**

论文主张必须逐门生成：

| 条件式主张 | 前置证据 | 若失败 |
|---|---|---|
| C0：透明 HFO-NP-v1 能形成收敛、守恒、局域的连续两周期 gap 事件 | G0 来源合同 + G1 事件资格 | 关闭 HFO，不进入 PINN |
| C1：bulk/PDE 指标不足以代表 gap event fidelity | G3 strong raw 在完整案例上的配对诊断 | 若二者一致或 raw 无能力，停止诊断 claim |
| C2-S：side 方法相对强参数敏感基线有增量 | `SIDE+` + G4 side pilot + G5 formal | 若不超过不确定性与实用效应门，停止 side claim |
| C2-T：cKC-NP 相对强 temporal 基线有增量 | `TEMPORAL+` + G4 temporal pilot + G5 formal | 若只降 loss、不改善物理时间事件，停止 clock claim |
| C3：方法在完整留出 bundle 上保持效应且物理守卫非劣 | one-shot formal OOD | 不形成正式方法主张 |

不得把 C0 的传统求解器输出称为实验真值，也不得在 C2/C3 前把论文题目锁成 SRF 或 cKC 方法论文。

## 4. 当前阶段：G0–G1 保持唯一 live plan

### G0：来源与对象合同

完全沿用授权包 A：`≤8 primary sources / 0 solve / 0 training`。初态、方程、本构、边界、慢双极波形、绝对时间、资产与许可任一关键项不能闭合，即按最早来源原因终止。

### G1：事件与 TKB side 预资格

完全服从唯一 live plan：当前授权包 B 为最多 `13 CPU intents / ≤48 h wall / ≤64 CPU-core-h / 0 PINN`，在三层两周期基础案例、零驱动和唯一轴双尺度 TKB 之外增加一个 medium thermal-feedback-off 配对 intent。该包仍未授权。

G1 需要区分两类可继续规划的结果：

- `EVENT+ / SIDE+`：对象事件和 side 信息均预资格，可另立 G2–G3 计划；
- `EVENT+ / SIDE−`：对象事件预资格，但 side 方法关闭；仍可另立 strong-raw 计划判 `TEMPORAL`。

`EVENT−`、守恒/边界失败或来源身份失败均立即停止，不自动换对象或模块。

## 5. G2：development oracle 与案例池冻结（未来授权包 C）

### 目标

把单一 G1 qualification case 扩展为可供 strong raw 和方法比较使用的完整案例体系，而不是先训练再补测试集。

### 进入条件

- G0 已记 `HFO_G0_PASS_SOURCE_CONTRACT`；
- G1 的基础对象在三层离散上获得 `EVENT+`；
- G1 产生可审计的误差地板、事件 evaluator 和实际 solver 吞吐量；
- 无论 `SIDE+` 或 `SIDE−` 均可进入，但 side 状态必须随案例元数据冻结。

### 具体任务

1. 把完整案例定义为“几何 × 热边界/接触 × 完整双极波形 × 初始缺陷场 × 连续 history”；禁止拆时间窗或把同一 bundle 的视图分池。
2. 冻结四个互斥角色：oracle qualification、joint development、one-shot formal OOD、reserve。
3. 只生成 development 需要的 oracle；formal/reserve 仅冻结清单，不读取结果。
4. 依据 G1 实测成本决定 development 数量和后续预算；引用会话的 `1/3/3/2` bundle 仅作容量估算，不是当前合同。
5. 冻结 artifact、单位、mesh identity、物理时间、协议 descriptor、事件指标和端口/守恒守卫。
6. 选择 formal OOD 轴时只在 G0 来源有效域内考虑厚度、热接触或协议速率；不得把缺失物理参数伪装成 OOD。

### 停止条件

- 事件只在 qualification case 存在，无法构成来源允许的案例族；
- formal OOD 轴依赖未闭合本构或结果导向参数；
- evaluator 对离散层、阈值或 history 身份不稳定；
- 所需 solver 预算无法在另批上限内形成最小 development 池。

## 6. G3：FP64 strong-raw 能力与瓶颈诊断（未来授权包 D）

### 目标

先回答 raw PINN 是否胜任，再区分时间、空间或混合瓶颈。`SIDE` 是对象信息属性，`TEMPORAL` 是 strong-raw 训练瓶颈属性，两者不得互相代替。

### G3a：raw 能力门

- 使用同一网络族、相同 PDE/BC/IC、FP64、冻结无量纲化与实际计算计量；
- 在至少两个 development 完整案例上运行两个嵌套预算、两个嵌套 seed；
- 先评价 base 完整协议的局部 gap 事件，再评价已资格化 bundle；
- 不用 test/formal oracle 选择权重、停止轮次或网络宽度。

互斥裁决：

- 高预算仍不能解析 gap 事件：`RAW_INCOMPETENT_ROUTE_NO_TEST`；
- 低预算已达到 oracle 数值地板：`NO_BOTTLENECK`；
- raw 能解析事件但明显高于误差地板：进入 G3b。

### G3b：瓶颈轴诊断

用最小、实际计算匹配的诊断臂比较：

1. strong raw；
2. 一个预冻结 causal/SI/pseudo-time temporal comparator；
3. 一个不移动 collocation、只增强固定 support 表达能力的 spatial comparator；
4. 仅在前两种诊断均显示增量时才考虑组合臂。

主要依据是完整 gap event error 在物理时间上的变化；PDE loss、bulk L₂ 或训练速度只能作辅助。方法效应必须超过 `max(oracle uncertainty, paired seed variation, predeclared practical floor)`。实际倍率在 G3 计划中根据 G1/G2 证据冻结，不能直接继承引用会话的 20%。

可能输出为 `TEMPORAL+`、`SPATIAL+`、`MIXED+` 或 `NO_ACTIONABLE_BOTTLENECK`。`SPATIAL+` 不自动授权 PHA、IRAC 或新采样模块。

## 7. G4：按证据选择唯一方法并做 bounded pilot（未来授权包 E）

### 7.1 路由

```text
EVENT−                              → HFO STOP
EVENT+ + RAW_INCOMPETENT            → 方法路线 STOP，不以模块救 raw
EVENT+ + NO_BOTTLENECK              → 方法路线 STOP
EVENT+ + SIDE− + TEMPORAL−          → STOP
EVENT+ + SIDE+ + TEMPORAL−          → 只设计并筛选一个 side 方法
EVENT+ + SIDE− + TEMPORAL+          → 只设计并筛选 cKC-NP
EVENT+ + SIDE+ + TEMPORAL+          → 两腿先分别通过，再申请 2×2
EVENT+ + SPATIAL+ only               → 当前 idea 收口；空间方法须另立 PLAN
```

### 7.2 SIDE+ 路线

SRF 优先级已由 ADR 0032–0039 覆盖。当前唯一条件式设计靶标是 CTH-PINN，但 `SIDE+` 仍不准入它：必须先通过 raw competence、transport-primary load、`FIELD_HINGE_RELEVANCE_PLUS`、qualification/identity-development 角色分离、固定来源 `a0`、联合 transport vector、共同输出变换守卫、smooth4/错结点身份、`IND-5`/blind bundle 双轴效用及 novelty sufficiency。任一门失败即关闭当前 side 方法，不自动返回 SRF、SRPG 或其他候选。

### 7.3 TEMPORAL+ 路线

`cKC-NP` 只允许全局、空间无关、严格正速率的 `τ=τ(t,p)`。它必须保持 NP 守恒、blocking no-flux 和总质量，所有事件按物理时间 `t` 评价，并与 identity clock、固定解析 clock、causal/SI/pseudo-time 强基线比较。若只改善优化 loss、不能改善物理时间 gap 事件，立即 No-Go。

### 7.4 Pilot 规模与通过原则

首轮只使用 2 个 development bundles、2 个嵌套 seed 和“strong raw + 最强近邻 + 候选 + 关键 kill control”的最小四臂，建议上限 16 training intents。该数字只是下一 PLAN 的预算上界候选，仍需依据 G3 吞吐量重新冻结。

通过必须同时满足：

- 主 event endpoint 相对最佳非目标臂的配对改善超过数值地板、seed 波动和预声明实用效应门；
- 完整 bundle/seed 的改善方向具有一致性；
- 端口、温度、守恒、PDE 和非负/有界守卫不劣；
- 收益定位在 TKB 或 temporal 诊断指定的负载区域；
- 参数量、PDE residual evaluation、AD 阶数、view 数、optimizer updates、wall-clock 和峰值内存均透明报告。

外部方案中的 `15%`、`5%`、`1.25×` 只保留为待估建议，不能在看到 G1/G3 误差与吞吐量前固定。

## 8. G5：one-shot formal OOD（未来授权包 F）

只有 G4 pilot 通过后才设计并授权 formal：

1. 根据 development 的配对方差、效应量和实测吞吐量一次冻结 formal case 数、seed、预算和实用效应门；
2. 方法、超参数、训练日程、事件 evaluator 和失败计票全部锁定；
3. 一次打开此前未读取的完整 formal bundles；reserve 只处理方法外执行故障；
4. 主结论要求 95% 配对置信下界高于零、点估计达到预冻结实用效应，同时全部物理守卫通过；
5. 任何 GPU、付费计算、formal 运行或额外 seed 都需新的明确授权。

引用会话建议的 3 formal bundles × 3 seeds × 4 methods 可作为资源估算情景，但当前没有方差和吞吐量证据，不能冻结为 36 次训练合同。

## 9. G6：论文证据包与初稿（未来授权包 G）

### 主图建议

1. HFO-NP-v1 来源、方程、几何、协议与 derived/synthetic 身份；
2. 两周期 `c_v–T–I/V`、gap opening/closing 与三层收敛；
3. TKB 两尺度、smooth-quadratic null 与 side verdict；
4. strong raw 的事件能力和 temporal/spatial 瓶颈图；
5. 目标方法、强基线与关键消融；
6. 完整事件端点、端口/守恒/温度守卫和实际计算 Pareto；
7. one-shot formal OOD 的配对效应与不确定性。

### 主表建议

- 对象参数、单位、来源和适配身份；
- 各方法实际计算账本；
- 完整案例事件指标与守卫；
- formal 效应、置信区间和失败计票。

### 论文边界

- HFO-NP-v1 是透明派生数值对象，不是实验验证；
- “未发现精确碰撞”不写成世界首创；
- 若只有对象/事件通过而方法失败，可形成负面方法就绪性报告，不强行包装正稿；
- 只有相应 formal 门通过后，题目才可改成 SRF、cKC 或二者交互的具体方法标题。

## 10. 高效推进的相对节奏

以下仅是每次授权后的理想关键路径，不是当前承诺或并行执行许可：

| 阶段 | 建议工作窗 | 决策价值 |
|---|---:|---|
| G0 | 1–2 天 | 能否形成来源闭合对象 |
| G1 | 3–7 天 | 是否有合格局部事件及 side 信息 |
| G2 | 2–4 天 | 能否形成无泄漏的 development/oracle 池 |
| G3 | 4–6 天 | raw 是否胜任、瓶颈属于哪一轴 |
| G4 | 5–7 天 | 唯一方法是否有神经特异增量 |
| G5–G6 | 7–10 天 | formal 主张与初稿能否成立 |

所有工作窗在对应授权后才开始计时。任一停止条件触发即收口；不把剩余预算转给临时新增材料、网络、协议、阈值或 fallback。

## 11. 当前仍未冻结的作者决策

以下事项必须等待前置证据，本文不替用户决定：

- G0 的初态、波形、力学分支和 clean-room 实现身份；
- G1 的 `ε`、联合离散层与误差协方差合同；
- G2 的 development/formal/reserve 数量和 OOD 轴；
- G3 网络族、两个计算预算、temporal/spatial comparator 与实用效应门；
- CTH 的 identity-development 案例数、blind microview 预算、公共输出变换具体形式和双轴 Pareto 不确定性带；方法名与 knot 不再开放选择；
- pilot/formal 的最终 arms、seed、统计规则与 CPU/GPU 预算；
- 实现框架、代码目录和论文具体标题。

## 12. 当前唯一下一动作

本路线已经完成规划整合，但没有改变当前授权。唯一可申请的下一执行动作仍是 live plan 的 **授权包 A：G0 来源与对象合同**。在用户明确批准前，项目保持 `HFO_NP_V1_G0_G1_PLAN_REVISED_BLOCKED / HFO_SOURCE_CONTRACT_NOT_CLOSED / NO_SCIENTIFIC_METHOD_CLAIMS`。
