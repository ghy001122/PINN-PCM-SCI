# paper_v29：剩余 PDE 实际影响与固定目标反事实

VERIFIED：本轮已完成，未取得通过冻结判据的剩余 PDE 独立预测增量。保留 [V28](../paper_v28/README.md) 的同层强基线收益；本轮从其 D_E 父态完成 D_C、P1、固定 kappa=92.84049 的 P_kappa。全部新结果为同一已见 nominal 对象上的有界开发证据。GPU 已回收、关闭并确认；用户已明确授权本包发布及[云端独立复评交接](../../docs/notes/2026-09-13-lf11-v29-results-cloud-review-handoff.md)。

VERIFIED：P1/P_kappa 对同层 B_E 的 raw phase RMS 改善39.99%/40.03%，第一周期 recall 达到0.90243/0.90288。相对同父继续拟合 D_C，额外 phase RMS 改善仅0.65%/0.73%；第二周期 timing 仍高于0.005，所有严格器件标记仍为 false。

VERIFIED：P_kappa 相对 D_C 的原尺度 J 在训练/审计池降低6.59%/2.35%，主要来自热项，功率误差却上升5.71%。SUPPORTED_INTERPRETATION：已测到实际物理作用与事件分量收益，仍未形成所需的共同预测收益；这不是只记录一次门失败，也不是所有 PINN 的结论。

- [完整英文初稿](manuscript.md)
- [关键机制—预测后果图](figures/mechanism-to-device.png)
- [共同训练／审计目标](figures/common-objectives.png)
- [完整一阶梯度方向](figures/gradient-directions.png)
- [双周期事件与电学轨迹](figures/event-device-trajectories.png)
- [固定端点数表](tables/fixed-endpoints.md)、[匹配变化](tables/matched-changes.md)、[完整周期事件](tables/cycle-events.md)
- [主张矩阵](claim_evidence_matrix.md)、[复现](reproducibility.md)、[精选证据](evidence/README.md)

每幅图均有同名独立 PDF。新增 669 次完整 L-BFGS 评估、零 Adam，正解／伴随分别 29882/29882；每臂223次上限同时满足原300次与总30000正反解上限。P_F 本轮未运行，不是失败方法；初始化、干净新观测、完整新协议及材料标定仍未确认。

当前最优先问题与一次有界数值适配提案见[下一研究计划](../../docs/plans/NEXT_ACTIONS.md)，状态为 PROPOSED_NOT_AUTHORIZED；现有训练配方已结束。
