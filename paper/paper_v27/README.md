# paper_v27：同父软边界与内部 PDE 的匹配证据

本版继承已发布的 paper_v26，保留旧 V 拟合门未通过的历史裁决。当前新协议直接使用指定父状态，未另设拟合或通量准入门。本稿与精选证据按用户后续授权纳入云端发布；实际版本以所属 Git 提交为准。[本轮交接](../../docs/notes/2026-09-12-lf11-v27-results-cloud-review-handoff.md)请求独立评估与下一步规划，不授权新研究执行。

## 已完成的主线结论

**VERIFIED：D_I / D_B / P_U 三臂均完成并形成有效固定终点。** 实际共 4500 Adam updates、900 次完整固定目标/梯度评估；三臂分别保留 147/146/145 个 L-BFGS 接受步，均为预算结束。原始稀疏观测、二维方程、本构和网络保持不变。

- D_B 相对 D_I：raw Ephi 改善 3.10%、顶流误差改善 15.71%，但 S、底流和功率误差上升，两层匹配门均未通过。
- P_U 相对 D_B：独立 AD 物理目标下降 55.75%，raw Ephi 仅改善 2.81%、顶流改善 13.84%；底流误差上升 5.87%、功率轨迹误差上升 9.14%、能量误差上升 13.72%，两层门均未通过。
- 汇总 BC 下降并未修复 heater：D_B 的总 BC 比 D_I 下降 61.44%，heater 子项却上升 20.92%，完整 heater trace RMS 上升 9.02%。三臂的双端电流变化方向相反。
- 三个预定 Adam 节点均支持同一 electric-amplitude→T 局部通道；历史动量和总更新方向单列，因此不把局部有害分量写成整段轨迹的唯一根因。

**VERIFIED：条件 R/G/N 已全部完成。** N 对 R 的顶流误差下降 46.41%，底流/功率误差却上升 12.75%/15.64%，raw Ephi 上升 5.20%；对 G 的底流/功率误差上升 17.09%/22.39%。G 对 R 的底流/功率误差仅改善 3.71%/5.52%。三个条件差分的 A、B 均未通过，D_N 未触发、未运行，不能记为失败。

本轮合计六个合法固定终点、6500 次新增 Adam updates、1500 次完整固定目标/梯度评估。R 重用的 1000 次 Adam 已计入主线，未重复计数。所有训练进程已结束，CPU-only，未启动云实例；stress 未读，未新增观测。六个终点不是六个独立初始化。

## 论文与证据

- [完整正文](manuscript.md)、[主张矩阵](claim_evidence_matrix.md)、[方法出处及针对性来源核对](method_sources.md)。
- [主线全部数表](tables/joint-endpoints.md)、[两条匹配差分](tables/matched-contrasts.md)、[双周期事件](tables/joint-events.md)。
- [所有新旧终点指标](tables/all-endpoint-metrics.csv)、[完整可见拟合/独立物理审计](tables/fitting-physics-audits.md)、[BC 子项](tables/endpoint-boundary-subterms.md)。
- [三个节点的幅值判别](tables/three-node-amplitude.md)、[完整方程×参数头方向](tables/equation-head-directions.csv)。
- [条件匹配差分](tables/conditional-contrasts.md)、[R/G/N 完整指标](tables/conditional-endpoints.csv)、[条件事件代价](tables/conditional-events.md)。
- [精选原始证据](evidence/README.md)、[复现入口与数据边界](reproducibility.md)。

## 图稿

1. [同父匹配主图](figures/lf11-joint-matched-main.png)：场误差与器件误差并列。
2. [双周期事件、双端电流与功率](figures/lf11-joint-events-device.png)：同时保留改善与代价。
3. [接触迹、增量与耗散分解](figures/lf11-joint-contact-diagnostics.png)：带符号恒等式，不扣除后评分。
4. [共同尺度的二维场图](figures/lf11-joint-fields.png)：包含父态与 contact 强基线。
5. [边界子项与优化方向机制图](figures/lf11-joint-mechanism.png)：区分汇总目标、子条件与总更新。
6. [归一化与全局调权反事实](figures/lf11-joint-normalization.png)：顶部电流改善与底流/功率恶化并存。

每张图同时提供同名 PDF。六图已直接从精选证据包重建并逐张查看；该过程未重新训练或读取完整参考场。

## 当前贡献与限制

可写入的主体是有界的约束归因实验、接触读出诊断、局部 FV 残差与双端电流/功率一致性的代数关系，以及“局部幅值通道存在并不足以使归一化有效”的实际反事实。通用拟合技巧和已知守恒恒等式不单独包装成算法创新。本轮未建立竞争性的正面 PINN 方法优势。

**HYPOTHESIS：下一优先方案**为电学子问题消元的耦合重建。D_E/P_E 与强化后的 B_E 共用同一电学求解与耗散读出，P_E 保留明确的热/相态 PDE 残差；先证明独立增量，再补软电学 PINN 反事实及独立确认。详见[唯一下一计划](../../docs/plans/NEXT_ACTIONS.md)。该方法尚未实现或执行，不能把离散守恒保证当作相态或器件精度保证。

全部结果限于一个继承初始化、一个已见观测 mask、一个已多次查看的 nominal 数值对象。新初始化、新 mask、完整新协议、formal OOD、连续体精度及材料标定均未建立。对象仍为合成、无量纲、PCM-inspired 二维电—热—相态 wall-cell。
