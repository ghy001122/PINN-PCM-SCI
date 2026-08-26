# Live plan：授权包 A 方法盲 clean-room 对象组合有界收口

- `phase_id`: `ONE_OBJECT_PACKAGE_A_PORTFOLIO_NO_GO`
- `lifecycle_state`: `BLOCKED`
- `blocker_id`: `PORTFOLIO_NO_GO_PACKAGE_A_FROZEN_3_FAMILIES_11_CARRIERS`
- `authorization_state`: `DOCUMENT_AND_NEGATIVE_EVIDENCE_REVIEW_ONLY`
- `plan_status`: `COMPLETED_TERMINAL_NO_GO_AWAITING_NEW_PLAN_AND_APPROVAL`
- `object_selection_status`: `NO_OBJECT_SELECTED`
- `method_selection_status`: `NOT_REACHED`
- `claim_status`: `BOUNDED_SOURCE_PORTFOLIO_NO_GO_NO_METHOD_EVIDENCE`
- `timebox`: `COMPLETED_WITHIN_48_HOURS`
- `fresh_primary_source_budget`: `USED_11_OF_12_STOPPED_ON_3_OF_3_FAMILY_EXHAUSTION`
- `deep_review_object_family_budget`: `EXHAUSTED_3_OF_3_NEW_FAMILIES`
- `compute_authorization`: `ZERO_BUILD_ZERO_SOLVE_ZERO_TRAINING_ZERO_GPU`

## 终点与当前唯一动作

[方法盲对象筛选报告](../docs/references/2026-08-26-method-blind-cleanroom-object-screen.md)已按冻结顺序完成三个家族的八门审查；三者最早决定性失败均为 Gate 3 合同完整性。最终使用 11/12 项新增一手载体，因 3/3 家族预算耗尽，终点为：

```text
PORTFOLIO_NO_GO_PACKAGE_A_FROZEN_3_FAMILIES_11_CARRIERS
OBJECT_SELECTION_STATUS=NO_OBJECT_SELECTED
METHOD_SELECTION_STATUS=NOT_REACHED
NEXT_RESEARCH_EXECUTION_AUTHORIZED=false
```

当前只允许复核本报告、[ADR 0042](../docs/adr/0042-close-package-a-with-method-blind-object-portfolio-no-go.md)与既有治理一致性。不得使用剩余 1 项载体名额继续发现、把排序较后的线索升级为第四候选，或自动进入授权包 B。新研究动作须新的 PLAN 与用户明确批准。

## 已执行合同：目的与论文去向

用最短证据链选出一个可作为 source-aligned clean-room `derived/synthetic` benchmark 的二维氧化物电—热—动态内部态对象，为后续独立 oracle、strong raw 瓶颈和唯一 PINN 方法裁决提供对象前提。当前阶段不选择 CTH 或任何 PINN 方法，不产生方法可行性、论文创新性或正向性能结论。

条件式论文故事保持唯一：

```text
方法盲锁定的 source-aligned clean-room 2D object
→ 独立 oracle/event/hinge relevance
→ strong raw 胜任但存在可归因表示瓶颈
→ 单一方法相对强控制的增量
→ sealed complete-case OOD
```

若本阶段组合 No-Go，则交付有界来源负证据并关闭当前路线；不得为了形成正向论文改对象、缩门或预选方法。

## 已执行合同：冻结的两遍筛选

### Pass 1：方法盲发现与候选冻结

只使用以下方法中立查询族；查询和排序中禁止加入 `CTH`、`hinge`、`kink`、`wrong-knot`、`PINN` 或预期方法表现：

1. `oxide memristor electrothermal oxygen vacancy 2D code data`
2. `RRAM drift diffusion heat equation open source simulation`
3. `oxide phase-field device Joule heating code data`
4. `ferroelectric oxide electrothermal phase-field device open source`

只计新增的一手论文、作者/机构官方代码、作者/期刊官方数据或档案载体；综述、聚合页和搜索摘要只能提供线索，不能通过来源门。HFO-NP-v1、TaOₓ C1、VO₂/related-oxide、Q-POP、R1、R2/FerroX 及其他已有 No-Go 家族从候选生成中排除。

在深审任何候选前，冻结最多三个新家族的名单、顺序和 tie-break。排序优先级固定为：

```text
来源身份与许可
> 二维物理闭环
> 来源响应锚点与事件可资格化概率
> clean-room 重建可行性
> 完整案例生成与 OOD 设计可行性
> 预计 CPU 成本
```

同层并列时，优先选择因果参数冲突更少、协议/history 更明确、空间/内部态锚点更多、静态资产更易审计者；仍并列则按最早公开日期、DOI/正式档案标识字典序决定。候选冻结后不得因发现 CTH 更适配或方法预试更好而改序。

### Pass 2：按序深审并在首个 PASS 停止

对冻结候选逐一审查以下八个来源硬门：

1. **二维器件**：论文主体或可合法派生的合同是二维及以上真实器件域，不是抽象方域、一维或单节点模型。
2. **物理闭环**：至少闭合电势/电流、温度/Joule heating、动态内部态三类 PDE 或守恒方程，并有明确反馈路径。
3. **合同完整**：几何、材料域、IC、BC、界面、单位与关键本构可追溯地冻结；未知项可枚举但不得决定核心拓扑或被结果拟合。
4. **绝对协议**：驱动、持续时间、顺序、history/state carryover 与观测窗口足以定义可重放的物理时间案例。
5. **参数对齐**：进入因果链的 paper–code–supplement 参数无未解释冲突；有限不确定性分支须事先透明列出，不能猜测归一。
6. **来源响应锚点**：至少有一个端口响应锚点和一个空间或内部态锚点，可用于后续联合来源对齐；漂亮端口曲线不能单独通过。
7. **身份与许可**：论文、代码/数据版本、固定标识、许可证与 `A/A′/ENGINEERING` 改动层级可追溯；对象始终称 clean-room `derived/synthetic`，不称作者原生重放。
8. **可重建与案例能力**：在不依赖作者私有 raw 解的前提下，可在授权包 B 中建立独立守恒 oracle、时空收敛与互斥完整 case generator；至少能设计 qualification、identity/development、formal OOD 的实体级隔离。

作者未提供嵌入 raw 全场解或作者预封案例角色，不单独构成来源失败；它们是未来独立 oracle 与案例生成器的任务。反之，若方程/BC/参数/协议或响应锚点无法唯一或有限分支闭合，则不得用 clean-room 名义掩盖缺口。

## 已执行合同：停止规则与量词

- 当前候选任一硬门失败：记录 `CANDIDATE_NO_GO`、最早决定性失败和独立次级缺口，然后审查预冻结的下一候选。
- 当前候选通过全部八门：立即记录 `OBJECT_SOURCE_PASS_AND_LOCKED` 并停止对象搜索；不测试 CTH，不回看其他候选。
- 冻结候选全部失败，或 48 小时/12 项新增一手载体/3 个新家族中任一预算耗尽且尚无 PASS：记录 `PORTFOLIO_NO_GO` 并关闭当前论文路线。
- 只允许因明确新增的一手载体、固定版本身份修正或判读错误进行一次可追溯更正；不得为结果不理想追加家族、拼接来源、换方法、补默认参数或扩大预算。
- `CANDIDATE_NO_GO ≠ PORTFOLIO_NO_GO`；`OBJECT_SOURCE_PASS ≠ ORACLE_PASS`；`GOAL_APPROVED ≠ PACKAGE_B_AUTHORIZED`。

## 未触发的对象 PASS 分支（追溯）

1. 冻结对象身份、来源合同、允许的不确定性分支、响应锚点、未来案例实体和对象锁定时间；
2. 若预算仍有余量，只开展一次有界 exact/direct-near prior-art 前门，核对是否已有同一 primitive、同一因果主张和可比完整事件证据；
3. 写出授权包 B 的 CPU-only 最小 oracle 计划，但不构建、不运行；B 必须另行明确批准。

新颖性前门若在对象锁定前没有对象可挂接，则保持 `NOT_REACHED`。发现 broad adjacency 只收窄未来表述；只有 exact/direct-near collision 覆盖拟议因果 headline 时，才关闭或按预注册规则降级路线，不能临时发明第二贡献。

## 已交付

本包已交付：

- 一份带固定链接/版本、许可、计数、候选冻结顺序、逐门证据和单一终局裁决的一手来源报告；
- 必要的 CONTEXT/ADR/实时状态同步；
- `PORTFOLIO_NO_GO_PACKAGE_A_FROZEN_3_FAMILIES_11_CARRIERS`；对象未通过，因此 novelty 前门与包 B 计划输入均为 `NOT_REACHED`。

本包不交付 oracle、代码、案例、训练、CTH Go/No-Go、formal 结果或证据闭合论文初稿。所有这些均保持 `NOT_REACHED` 或 `NOT_AUTHORIZED`。

## 当前执行边界

```text
PACKAGE_A = CONSUMED_AND_CLOSED
AUTHORIZED = READ_ONLY_REVIEW + DOCUMENT_CONSISTENCY
NOT_AUTHORIZED = BUILD + SOLVE + SMOKE + TRAINING + PINN + GPU + FORMAL
NOT_AUTHORIZED = PAID_COMPUTE + DEPENDENCY_INSTALL + AUTHOR_CONTACT + GIT_PUBLICATION
NOT_AUTHORIZED = CONTINUE_SOURCE_DISCOVERY + ADD_FOURTH_FAMILY + PACKAGE_B
```

本次收口运行文档一致性门；门禁只验证治理一致性，不构成科学证据。
