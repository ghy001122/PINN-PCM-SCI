# paper_v25：温度拟合修复与剩余电学瓶颈

**VERIFIED：温度拟合取得实质改善，但本轮未进入新的PINN物理比较。**

- 可见温度归一化RMS：17.8233% → 1.1375%；加热/关断为1.8357%/0.7219%，均通过拟合门。
- 完整固定参考网格ROI温度误差：28.2210% → 1.7475%。相态与双周期事件指标保持原父状态。
- 可见电势误差：1.5670% → 0.8215%，未达到0.5%准入；按指令停止D_B/P_U及电学归一化后续。
- 能量误差：106.7402% → 49.2006%；底部电流仍明显失真，不能只凭顶部电流7.2178%的NRMSE宣称器件可用。

温度包络下界仅0.1504%，排除了“该输出区间足以解释主要温度拟合缺口”。改进由有界优化和一次温度适配共同获得，尚无适配器独立归因或正面PINN方法优势。

- [完整英文初稿](manuscript.md)
- [主图 PNG](figures/lf11-followup-main.png) / [PDF](figures/lf11-followup-main.pdf)
- [误差定位图 PNG](figures/lf11-followup-localization.png) / [PDF](figures/lf11-followup-localization.pdf)
- [拟合准入表](tables/fit-admission.md)、[固定端点与强基线](tables/fixed-endpoints.md)、[CSV](tables/endpoint-metrics.csv)、[双周期](tables/events.md)
- [主张矩阵](claim_evidence_matrix.md)、[复现说明](reproducibility.md)、[证据](evidence/README.md)、[来源](method_sources.md)
- [本轮终局](../../docs/experiment/2026-09-12-phk-v23-lf11-followup-terminal-closeout.md)

paper_v24保留原样。独立初始化、观测规则变化、完整案例确认与formal OOD未执行；本轮为单nominal开发。CPU训练已结束，本轮未启动GPU实例。下一优先方案为仅修复V头并保留已达标T/phase，状态PROPOSED_NOT_AUTHORIZED。
