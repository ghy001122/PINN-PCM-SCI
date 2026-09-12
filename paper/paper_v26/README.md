# paper_v26：V-only 归因与接触边界读出机制

**VERIFIED：获得了可入稿的电势作用与接触读出证据；尚无新的 PINN 匹配优势。**

本轮恢复真实 V 曲率历史，200 次完整评估接受 99 步。可见 V 误差 0.8215%→0.5618%，固定目标下降53.23%；T/phase完全不变。原0.5%门仍未通过，新D_B/P_U及电学归一化依条件未运行。

固定T/phase下，能量误差49.20%→28.28%，功率NRMSE57.61%→30.76%。底流时间积分下降的99.41%来自边界迹项下降，近边界增量项变化很小；内部耗散反而略升。这是带符号恒等分解，不能当RMS贡献率。

仅补已知heater端点的新强基线不训练、不加标签：能量误差2.187%→0.644%，底流NRMSE60.79%→21.51%；T/phase和顶部电流基本不变。仍不满足完整器件可用或相态事件要求。

- [完整英文初稿](manuscript.md)
- [主图 PNG](figures/lf11-v-contact-main.png) / [PDF](figures/lf11-v-contact-main.pdf)
- [电流与耗散分解 PNG](figures/lf11-v-electric-decomposition.png) / [PDF](figures/lf11-v-electric-decomposition.pdf)
- [新端点与强基线](tables/new-endpoints.md)、[全部数表 CSV](tables/all-endpoint-metrics.csv)、[双周期](tables/new-events.md)
- [主张矩阵](claim_evidence_matrix.md)、[最小复现](reproducibility.md)、[精选证据](evidence/README.md)、[模块来源](method_sources.md)
- [本轮终局与下一决策](../../docs/experiment/2026-09-12-phk-v23-lf11-v-continuation-terminal-closeout.md)

本包按用户后续授权提交云端，实际版本以所属Git提交为准；[独立复评交接](../../docs/notes/2026-09-12-lf11-v26-results-cloud-review-handoff.md)汇总进展并请求重新权衡下一步路线。paper_v25保留原样；全程CPU，未创建云实例。当前优先候选是设计并审查heater相容、邻接绝缘通量不受不当限制的V共同表示，再申请有界拟合及同父PDE比较；该建议允许被复评推翻，不自动追加200评估。
