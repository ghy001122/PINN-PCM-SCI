# 研究笔记收录规则

`docs/notes/` 只收录尚未被项目接受的数据、方法、评价协议笔记和研究想法。这里的内容一律视为非权威草稿。

每份笔记至少写明日期、范围、当前状态和可核对来源，并清楚区分事实、解释、假设与未知。笔记不得：

- 重新定义 [`CONTEXT.md`](../../CONTEXT.md) 中的研究设定或论文口径；
- 覆盖 [`docs/adr/`](../adr/) 中已接受的决定；
- 改变 [`active_phase.md`](../../active_phase.md) 的授权边界或 [`PROJECT_STATE.md`](../../PROJECT_STATE.md) 的核验状态；
- 充当 live plan 或把未执行内容写成实验结果。

若一项笔记后来被正式接受，应在 ADR 中记录决定，并按需要更新 `CONTEXT.md`、状态或计划；原笔记可以保留并链接新决定。

当前笔记：

- [PHK-V2.3 R0B FIRST_SWITCH_175 精确执行计划](2026-08-30-phk-v23-r0b-first-switch-175-plan.md)：基于已完成的 `R0A_INCONCLUSIVE` 提出 175-step 首次切窗诊断的拟议冻结草案，覆盖 schedule、observer、A–H 时间先后与候选机制裁决、V100 回收与全局止损；全文为 `PROPOSED_NOT_AUTHORIZED`，不是 live plan、合同或执行授权。
- [PHK-V2.3 P0 只读审计与拟议合同](2026-08-30-phk-v23-p0-read-only-audit.md)：沿正式 strong-raw 调用链核验输出变换、三场残差、loss、causal sampler、checkpoint、carrier、evaluator 与 decision，分类现有和缺失的 R0 证据，并给出仍为 `PROPOSED_NOT_AUTHORIZED` 的 PHK-V2.3 合同、最小 patch 与测试计划；不启动 R0A/GPU，不改变 V2.2R 终局 No-Go 或 stress seal。
- [PHK-V2.2R 近期研究策略整合](2026-08-29-phk-v22r-recent-research-strategy-integration.md)：把实时会话中的一周冲刺、模块组合、四类结果故事和十类止损思路映射到当前冻结合同；它是非授权解释入口，不改变 blocker、预算、sealed 规则或历史 No-Go。
- [Structural Kinetics-Clock PINN 有界负面研究报告](2026-08-21-structural-clock-bounded-negative-report.md)：汇总 strong-raw、稀疏锚点与 QPOP-R3-v1 的 development-only 负证据；终局事实仍以实验 closeout 和 ledger 为准，不是 formal 方法结论。
- [HFO-NP-v1 后 G1 PINN 研究路线整合](2026-08-24-hfo-post-g1-pinn-roadmap-integration.md)：把引用会话中的 G2–G6 建议与实时权威链对齐；它是非授权 future roadmap，不是第二份 live plan。
- [HFO-NP-v1 Q30–Q36 PINN 方法与训练合同整合](2026-08-25-hfo-q30-q36-pinn-training-contract-integration.md)：记录用户经 ADR 0032 接受的 future-stage 方法与训练边界；本笔记解释具体合同，但不覆盖 ADR、live plan 或授权。
- [HFO-NP-v1 Q37–Q43 strong-raw 与公平裁决合同整合](2026-08-25-hfo-q37-q43-strong-raw-contract-integration.md)：记录用户经 ADR 0033 接受的耦合模式、backbone、计算公平、case/seed 与失败计票边界；仍是非授权 future-stage 说明。
- [HFO-NP-v1 Q44–Q48 论文主张与新颖性边界整合](2026-08-25-hfo-q44-q48-paper-claim-and-novelty-boundary-integration.md)：记录用户经 ADR 0034 接受的单一方法 headline、HFO 域内逐案例外推、forward-only、事件保真—计算 Pareto 与两次新颖性刷新；不选择方法或授权科研执行。
- [HFO-NP-v1 Q49–Q53 因果 pilot、formal 与碰撞合同整合](2026-08-25-hfo-q49-q53-causal-pilot-formal-and-collision-contract-integration.md)：记录用户经 ADR 0035 接受的因果 primitive 准入、单机制 pilot、两族 formal OOD、Pareto 非支配与 direct-near 碰撞否决；仍是非授权 future-stage 说明。
- [HFO-NP-v1 TKF-CANON 方法选择与外部对抗审查整合](2026-08-25-hfo-ctkf-method-selection-and-external-review-integration.md)：记录自由 TKF-v0 的五视图不可辨识否决、TKF-CANON 条件式选择、smooth-quartic control 与 held-out identity 前门；不是方法准入或执行授权。
- [HFO-NP-v1 Q54–Q58 pre-FULL_PLAN 对抗性修订整合](2026-08-25-hfo-q54-q58-pre-full-plan-adversarial-revision-integration.md)：记录用户经 ADR 0037 接受的来源锚定 waveform-scale 轴、来源模型保真、`FIELD_KINK_PLUS`、独立身份协议与 novelty sufficiency 复合前门；不授权 G0、求解、方法实现或训练。
- [HFO-NP-v1 Q59–Q63 CTH 语义、热因果、可容许性与效用整合](2026-08-25-hfo-q59-q63-hinge-causality-admissibility-and-utility-integration.md)：记录用户经 ADR 0038 接受的有限预算 hinge 重构、逐系数 IC/BC、thermal-feedback-off、力学止损与 independent-per-view utility kill；不授权 G0、求解、方法实现或训练。
- [HFO-NP-v1 Q64–Q68 CTH 身份、锚点、输出变换与 Pareto 效用整合](2026-08-25-hfo-q64-q68-cth-identity-anchor-transform-and-pareto-integration.md)：记录用户经 ADR 0039 接受的证据角色分离、固定 `a0`、联合向量原语、共同 `C1` 变换与双轴协议束效用；不授权 G0、求解、方法实现或训练。
