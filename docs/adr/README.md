# 架构与研究决策索引

本目录只解释“为什么接受某项决定”。当前能否执行由 [`active_phase.md`](../../active_phase.md) 决定，已运行事实由 [`docs/experiment/`](../experiment/) 保存。

## 冻结的 Kinetics-Clock 政策合同

- [Q1–Q23 决策总表](research_decisions_Q1_Q23.md)
- [0001：限定高频主张](0001-bound-high-frequency-claim-to-thermal-vo2-time-stiffness.md)
- [0002：采用逐案例 PINN 求解评价](0002-use-post-lock-per-case-pinn-solver-evaluation.md)
- [0003：冻结经核对的 Q‑POP PhysicalContract](0003-freeze-a-reconciled-qpop-physical-contract.md)
- [0004：采用场选择性的结构动力学时钟](0004-use-a-field-selective-structural-kinetics-clock.md)
- [0005：唯一正向干预为构造单调时钟](0005-use-a-constructively-monotone-clock-as-the-sole-positive-intervention.md)
- [0006：主训练不读取 Q‑POP 内部场标签](0006-separate-qpop-labels-from-primary-training-and-use-layered-adjudication.md)
- [0007：物理断点采用分段强形式](0007-use-piecewise-strong-form-at-physical-breakpoints.md)
- [0008：显式治理 KC 止损与 PHA 转换](0008-govern-kc-stop-and-pha-transition-with-explicit-dispositions.md)
- [0009：使用两个独立端点和角色隔离 case pool](0009-use-two-independent-endpoints-and-role-isolated-case-pools.md)
- [0010：完整 case 是统计单位并冻结预算政策](0010-treat-complete-cases-as-units-and-freeze-budget-policy.md)
- [0011：隔离结构时钟计算图](0011-isolate-the-structural-clock-computation-graph.md)
- [0012：用有界 pilot 冻结时钟优化与可容许性](0012-freeze-clock-optimization-and-admissibility-by-bounded-pilot.md)
- [0013：intent-to-run 与有序 KC 裁决](0013-use-intent-to-run-and-ordered-kc-adjudication.md)

## 后续有界实现决定

- [0014：在 reduced oracle 中恢复动态电子序参量](0014-restore-dynamic-electronic-order-in-the-bounded-reduced-oracle.md) — 历史 R4 路线决定；执行结果已由 [R4/raw-v3 收口](../experiment/2026-08-21-r4-and-raw-v3-closeout.md) 关闭。
- [0015：初值精确结构残差与非初始 checkpoint](0015-use-initial-condition-exact-structural-residuals-and-noninitial-checkpoints.md) — 当前保留的实现合同。
