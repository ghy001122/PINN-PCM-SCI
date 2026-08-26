# HFO-NP-v1 Q49–Q53 因果 pilot、formal 与碰撞合同整合

- `date`: `2026-08-25`
- `document_role`: `FUTURE_METHOD_CAUSAL_AND_FORMAL_CONTRACT_INTEGRATION_NOT_LIVE_PLAN`
- `status`: `ACCEPTED_PLANNING_REFINEMENT_NOT_AUTHORIZED`
- `claim_status`: `NO_NEW_SCIENTIFIC_EVIDENCE`
- `input`: grill-with-docs 对 Q49–Q53 的推荐答案及用户整包接受
- `authority_relation`: 服从 `CONTEXT.md`、ADR 0031–0035、`active_phase.md` 与唯一 live plan
- `extends`: `2026-08-25-hfo-q44-q48-paper-claim-and-novelty-boundary-integration.md`
- `execution_in_this_task`: `0 source search / 0 solve / 0 implementation / 0 training / 0 formal / 0 GPU`

## 1. 整合裁决

Q49–Q53 没有选择 SRF、cKC-NP 或其他具体方法，而是冻结“方法如何获得被选择资格”的合同。未来 headline 必须来自单一、可归因、能够被直接证伪的机制，不来自模块堆叠或 development 排名。

| 问题 | 已接受答案 | 约束 |
|---|---|---|
| Q49 primitive 选择 | `A` | 必须闭合瓶颈→最小干预→直接探针/kill control→事件端点→守卫的因果链 |
| Q50 首轮 pilot 包装 | `A` | 只允许一个新可训练机制；SIDE 与 TEMPORAL 两腿先分别 standalone |
| Q51 formal OOD | `A` | 一个机制对齐主家族＋一个正交稳健家族，均为 HFO 来源有效完整 case |
| Q52 Pareto 裁决 | `A` | 事件保真与守卫先通过；成本次要，候选不得在冻结上限内被严格支配 |
| Q53 碰撞否决 | `B` | direct-near 覆盖 primitive＋因果主张＋可比完整事件证据即停止/收缩；组件碰撞转为基线与消融 |

## 2. load-bearing 因果链

未来 G3/G4 计划必须先明确 strong-raw 暴露的瓶颈属于 side、temporal 或其他已获准类别，再定义只针对该瓶颈的最小干预。每个候选必须同时写出：

```text
diagnosed bottleneck
  → one trainable intervention
  → direct mechanism probe
  → mechanism-killing control
  → complete-case event endpoint
  → mass/no-flux/port/temperature/PDE guards
```

若中间任一箭头没有可执行的观测或拒绝条件，候选只可停留在 parking lot，不进入 pilot。best development loss、参数量增加、额外计算或新名称都不能补足缺失的因果箭头。

## 3. 单机制 pilot 与条件式交互

首轮 pilot 的目标候选只比公共 frozen base 多一个可训练机制。输入编码、耦合模式、backbone、固定/有界权重、support、优化器、case 角色和评价器均按前序 ADR 冻结，不得成为目标臂专属技巧。

若未来证据同时给出 `SIDE+ / TEMPORAL+`：

1. side 候选先对其最近直接基线、raw 与 kill control 做 standalone pilot；
2. cKC-NP 先对 generic/global time-coordinate comparator、raw 与 clock-rate shuffle 做 standalone pilot；
3. 只有两者各自合格，才可另批 `side off/on × clock off/on` 交互；
4. 交互增量不能倒推任一单腿独立优越。

## 4. formal OOD 与效用

formal 只使用两个完整案例家族：一个对齐机制预期失效/获益方向，另一个检验正交稳健性。具体家族必须从 G0 来源有效域和已资格事件家族中选择；当前不预定厚度、接触、热边界、协议速率或初态中的哪两个。

主裁决先比较完整事件保真和全部物理守卫。候选只有在计算匹配下超过最佳非目标臂且不被严格支配时，才可继续报告达到同一保真度的实际计算、墙钟、内存和自动微分成本。Pareto 图不能把失败臂重新包装成成功。

## 5. 新颖性碰撞处置

两次刷新均使用下列分级：

- `DIRECT_NEAR_VETO`：同期工作覆盖相同 load-bearing primitive、同一因果主张和可比完整事件证据；停止、降格或实质缩小主张后才可继续。
- `COMPONENT_COLLISION_ATTRIBUTION_REQUIRED`：只覆盖组成部件或宽泛训练思想；保留候选，但必须进入最近强基线、消融和来源归因。
- `COMPARATOR_ONLY`：任务、对象或证据近邻；作为实用竞争基线，不声称没有碰撞。
- `NO_EXACT_BUNDLE_FOUND_IN_BOUNDED_REFRESH`：只描述本次范围，不赋予优先权或 novelty clearance。

## 6. 当前状态

本整合不改变 `HFO_NP_V1_G0_G1_PLAN_REVISED_BLOCKED / HFO_SOURCE_CONTRACT_NOT_CLOSED / NO_SCIENTIFIC_METHOD_CLAIMS`。当前仍没有 SOURCE+、EVENT+、SIDE+、RAW_COMPETENT、TEMPORAL+、load-bearing primitive 或 formal OOD 轴，也没有授权来源检索、solver、PINN、training、formal、GPU 或付费计算。
