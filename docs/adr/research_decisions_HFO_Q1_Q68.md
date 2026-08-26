# HFO-NP-v1 研究规划决策总索引（Q1–Q68）

- `status`: `ACCEPTED_PLANNING_CONTRACT_INDEX`
- `effective_at`: `2026-08-25`
- `scope`: `HFO_NP_V1_CURRENT_Q1_Q68`
- `claim_status`: `GOVERNANCE_FACT_NO_SCIENTIFIC_EVIDENCE`
- `authorization`: `NONE`

本索引把当前 HFO-NP-v1 grill-with-docs Q1–Q68 的**有效处置**路由到已接受 ADR 和整合笔记。它不是新的 live plan，也不把计划升级为来源、数值或方法证据。这里的 Q1–Q68 与历史 [KC-PINN Q1–Q23](research_decisions_Q1_Q23.md)及已终止 R1 的 [FULL_DESIGN Q1–Q24](research_decisions_R1_FULL_DESIGN_GRILL_2026-08-22.md)是三个独立编号空间。

项目没有保存一个可逐字恢复 Q13–Q29 原始问句的单一权威表；本索引不补造问题文本，只汇总它们已经写入 `CONTEXT.md`、ADR 0031 和后-G1路线的有效合同。任何逐题原话需要回到相应会话记录，不能由本文件反向编造。

## 当前有效决策链

| 问题范围 | 当前有效处置 | 权威理由与细节 |
|---|---|---|
| Q1–Q12 | 选择透明 `derived/synthetic` HFO-NP-v1 作为唯一规划对象；先来源、后事件、再 side/temporal。连续 CF 与 exact restart 待 G0 二选一，G1 只用一个来源锚定波形缩放轴；`5x` 不是充分 side 门。 | [ADR 0030](0030-select-hfo-np-v1-and-evidence-routed-kc-srpg.md)、[ADR 0031](0031-revise-hfo-source-side-gate-and-method-routing.md)、[对抗性整合](../references/2026-08-24-hfo-np-v1-srpg-kc-adversarial-integration.md) |
| Q13–Q29 | 冻结 source->event->side->strong-raw->one-method 的证据顺序、逐 bundle 完整案例隔离、混合一阶三物理块 PINN、选择性硬 IC/BC、局部+全局空位守恒、实际计算公平与无自动 fallback；具体实施量仍待前门后另立 PLAN。 | [CONTEXT.md](../../CONTEXT.md)、[ADR 0031](0031-revise-hfo-source-side-gate-and-method-routing.md)、[后 G1 路线](../notes/2026-08-24-hfo-post-g1-pinn-roadmap-integration.md) |
| Q30–Q36 | side 方法延后到载荷定位；cKC 仅在 `TEMPORAL+` 后；只做一次 backbone 资格比较；归因轨不用 curriculum、固定支持与固定块权重；动态 weighting/adaptive sampling 只作分轨强基线；统一 FP64 两阶段优化。 | [ADR 0032](0032-defer-side-method-and-bound-hfo-pinn-training-comparators.md)、[Q30–Q36 整合](../notes/2026-08-25-hfo-q30-q36-pinn-training-contract-integration.md) |
| Q37–Q43 | strong raw 先比较 joint 与对称 staggered coupling；backbone 可 `INDETERMINATE`；公平须含 wider-raw 与 extra-work raw；method-vote case/seed 事前冻结；失败按四类且只允许一次有证据 supersede。 | [ADR 0033](0033-qualify-coupling-mode-and-freeze-strong-raw-adjudication.md)、[Q37–Q43 整合](../notes/2026-08-25-hfo-q37-q43-strong-raw-contract-integration.md) |
| Q44–Q48 | 只允许一个 load-bearing PINN headline；范围为 HFO 来源有效域内逐案例 forward solve；事件保真优先、成本作 Pareto；pilot 前及 formal/claim 冻结前各刷新一次新颖性。 | [ADR 0034](0034-freeze-single-method-headline-and-hfo-scoped-forward-claim.md)、[Q44–Q48 整合](../notes/2026-08-25-hfo-q44-q48-paper-claim-and-novelty-boundary-integration.md) |
| Q49–Q53 | 方法须闭合瓶颈->单一 primitive->直接 probe/kill control->完整事件->物理守卫；首轮只准一个新可训练机制；formal 限机制对齐与正交稳健两族；direct-near 碰撞触发停止或收缩。 | [ADR 0035](0035-freeze-causal-single-primitive-pilot-and-collision-veto.md)、[Q49–Q53 整合](../notes/2026-08-25-hfo-q49-q53-causal-pilot-formal-and-collision-contract-integration.md) |
| 方法选择中间裁决 | 自由 TKF-v0 因五视图光滑吸收不可辨识而退出；TKF-CANON 只保留形成史，当前方法名和真实 kink 语义已被 CTH 覆盖。 | [ADR 0036](0036-select-canonical-tkf-as-diagnostic-gated-full-plan-target.md)、[方法选择整合](../notes/2026-08-25-hfo-ctkf-method-selection-and-external-review-integration.md) |
| Q54–Q58 | 协议轴改为来源锚定固定时长事件段 waveform-scale A-prime；增加来源模型保真、训练外 time-shift 排除、smooth4/错结点 identity 与 novelty sufficiency 前门。历史 `FIELD_KINK_PLUS` 已由下一范围重命名。 | [ADR 0037](0037-require-waveform-fidelity-field-kink-identity-and-novelty-gates.md)、[Q54–Q58 整合](../notes/2026-08-25-hfo-q54-q58-pre-full-plan-adversarial-revision-integration.md) |
| Q59–Q63 | 将 TKF 重构为 CTH，只主张有限容量/预算 hinge 归纳偏置；增加逐系数 IC/BC、thermal-feedback-off、力学必要即止损和 independent-per-view utility kill；G1 上限改为 13 intents，CPU/墙钟不扩张。 | [ADR 0038](0038-reframe-tkf-as-cth-and-require-thermal-causality-admissibility-and-utility.md)、[Q59–Q63 整合](../notes/2026-08-25-hfo-q59-q63-hinge-causality-admissibility-and-utility-integration.md) |
| Q64–Q68 | 分离 field-hinge qualification 与 blind identity-development 完整案例；hinge knot 固定 `a0`；`h=(h_c,h_J)` 为一个联合向量原语；共享 `C1` 输出变换及 Jacobian-action guard；效用使用 `IND-5`/blind bundle/`IND-7` 双轴 Pareto。 | [ADR 0039](0039-separate-cth-identity-evidence-and-freeze-anchor-vector-transform-and-utility.md)、[Q64–Q68 整合](../notes/2026-08-25-hfo-q64-q68-cth-identity-anchor-transform-and-pareto-integration.md) |

## 单一现役证据顺序

```text
SOURCE_CONTRACT
  -> SOURCE_MODEL_FIDELITY
  -> THERMAL_CAUSALITY
  -> EVENT
  -> SIDE
  -> RAW_COMPETENCE
  -> TEMPORAL/SPATIAL_DIAGNOSIS
  -> FIELD_HINGE_RELEVANCE_PLUS
  -> ROLE_SEPARATED_CTH_DIAGNOSTIC_IDENTITY
  -> DUAL_AXIS_BUNDLE_UTILITY
  -> NOVELTY_SUFFICIENCY
  -> FULL_PLAN 可提交用户审查
```

任一前门失败均按其冻结状态收口，不自动换材料、方法、协议、knot、物理块、seed、阈值或预算。即使全部通过，也只允许提交 FULL_PLAN；method pilot、formal、GPU、付费计算、Git 发布仍须新的明确授权。
