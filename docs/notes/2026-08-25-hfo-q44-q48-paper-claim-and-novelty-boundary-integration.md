# HFO-NP-v1 Q44–Q48 论文主张与新颖性边界整合

- `date`: `2026-08-25`
- `document_role`: `FUTURE_PAPER_CLAIM_CONTRACT_INTEGRATION_NOT_LIVE_PLAN`
- `status`: `ACCEPTED_PLANNING_REFINEMENT_NOT_AUTHORIZED`
- `claim_status`: `NO_NEW_SCIENTIFIC_EVIDENCE`
- `input`: grill-with-docs 对 Q44–Q48 的推荐答案及用户整包接受
- `authority_relation`: 服从 `CONTEXT.md`、ADR 0031–0034、`active_phase.md` 与唯一 live plan
- `extends`: `2026-08-25-hfo-q37-q43-strong-raw-contract-integration.md`
- `extended_by`: `2026-08-25-hfo-q49-q53-causal-pilot-formal-and-collision-contract-integration.md`
- `execution_in_this_task`: `0 source search / 0 solve / 0 implementation / 0 training / 0 formal / 0 GPU`

## 1. 单一裁决

Q44–Q48 把后 G1 路线进一步收缩为一篇 **HFO 有效域内、逐案例训练、forward-only、单一 load-bearing PINN 机制** 的条件式方法论文。它没有选定具体方法，也没有产生对象、事件、raw、瓶颈或新颖性阳性证据。

| 问题 | 已接受答案 | 对未来路线的约束 |
|---|---|---|
| Q44 主要贡献身份 | `A` | 只有一个经前门与归因实验支持的 PINN 机制进入 headline；对象与治理为 supporting |
| Q45 泛化边界 | `A` | 只在来源有效的 HFO 完整案例家族内评价；逐案例重新训练，不声称跨材料 operator |
| Q46 实用价值 | `C` | 计算匹配事件保真度为主，达到目标保真度的成本为次要 Pareto 证据 |
| Q47 首篇任务范围 | `A` | 只做 forward PINN；inverse/UQ/代理不并列进入首篇主要任务 |
| Q48 新颖性刷新 | `B` | primitive 冻结后、pilot 前刷新一次；formal/论文主张冻结前再刷新一次 |

## 2. 论文故事边界

在方法尚未由证据选择前，论文继续使用中性身份：“HFO 局部缺陷事件的证据路由 PINN”。若未来有一个方法通过完整因果链，其 headline 才可改为该机制，且必须满足：

```text
诊断到的瓶颈
  → 单一 load-bearing intervention
  → 直接机制探针与 kill control
  → 完整事件主端点改善
  → 物理守卫不退化
  → formal OOD 复现
```

HFO-NP-v1 的透明派生身份、来源合同、case-pool、实际计算公平和 intent-to-run 是可信度基础，而不是用来凑成“对象创新＋框架创新＋方法创新”的三重主张。若没有方法增量，不能只凭对象和流程包装成原计划中的方法论文。

## 3. 泛化与评价边界

泛化单位必须是完整 HFO case，而不是轨迹片段、时间窗或同一器件的扰动 view。允许的候选家族包括厚度、接触/热边界、协议或初态家族，但只有 G0 来源有效域和后续事件资格支持的轴才能进入 formal；当前不预定具体轴。

每个 formal case 仍是独立 PINN 求解任务，不复用已训练权重冒充跨器件预测。跨材料、跨器件 frozen operator、inverse 参数识别和 UQ 均不在首篇主张范围。

主要裁决先问：在实际计算匹配条件下，候选是否改善按周期等权的 gap soft-mask 事件主端点，并通过 Q–V/端口、通量、温度、质量、no-flux、PDE 与能量/单位守卫。只有这些成立后，才报告达到同一预冻结保真度所需的计算成本。更快但不合格、或更准但依赖额外不可比计算，都不能靠一个综合分数变成正结果。

## 4. 两次新颖性刷新

第一次刷新位于“方法 primitive 与因果主张冻结”之后、“method pilot intent 生成”之前，目的是避免为已被同期工作直接占据的机制投入 pilot。第二次刷新位于“formal OOD/论文主张冻结”之前，覆盖从首次刷新到正式主张之间出现的同期论文、预印本、作者代码、release、许可和数据。

两次刷新都须区分 exact/direct-near/component/comparator，并回到一手来源。当前 `BROAD_CLAIM_COLLISION_CONFIRMED / NOT_NOVELTY_CLEARED` 不变；“有界搜索未发现 exact bundle”不能写成首创。直接碰撞的停止强度和组件碰撞的归因负担已由 [Q49–Q53 整合](2026-08-25-hfo-q49-q53-causal-pilot-formal-and-collision-contract-integration.md)与 [ADR 0035](../adr/0035-freeze-causal-single-primitive-pilot-and-collision-veto.md)继续冻结。

## 5. 当前不变项

- `phase_id=HFO_NP_V1_G0_G1_PLAN_REVISED_BLOCKED`
- `blocker_id=HFO_SOURCE_CONTRACT_NOT_CLOSED`
- 当前没有 SOURCE+、EVENT+、SIDE+、RAW_COMPETENT、TEMPORAL+ 或方法增量证据。
- 仍不授权来源检索、solver、object/oracle、PINN、training、formal、GPU 或付费计算。
- SRF、cKC-NP、二者组合和任何新采样/表示模块仍未选择，不得由本笔记自动入场。
