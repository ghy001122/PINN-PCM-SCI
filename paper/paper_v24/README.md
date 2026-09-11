# paper_v24：稀疏等观测下的物理增量与器件读出归因

本版已纳入 LF11 的实际四臂结果、必要条件诊断和五组图；[paper_v23](../paper_v23/README.md) 保留历史快照。

**VERIFIED：本轮没有建立正面 PINN 方法增量。** D_B→P_U 的独立物理目标下降80.37%，但 S、raw Ephi 分别恶化40.68%、17.74%。同目标的界面重要性采样分别改善4.49%、4.22%，改变相态残差测度只再改善0.0763%、0.00981%；均未达到预声明的双指标10%门槛。

**VERIFIED：已知波形的后验对照具有实质判别力。** 在观测、相态和温度完全相同的条件下，电势先除以已知驱动再插值，使 B_logit 的电流 NRMSE 从103.08%降至0.428%。它是后验非PINN基线诊断，不替换原始裁决，也不是独立确认。

**SUPPORTED_INTERPRETATION：下一步应优先定位电边界表示及 electric residual→phase 耦合。** 实际 Adam 状态的局部方向诊断没有显示破坏性的 phase residual→T；latent 条件未触发。四臂均数值合法但未通过严格器件门。本轮为单初始化、单nominal、固定离散参考，不含formal OOD或材料实验验证。

## 论文与证据

- [英文完整初稿](manuscript.md)：问题、物理与方法、六张结果表、五图、讨论及结论。
- [复现说明](reproducibility.md)：冻结输入、最小入口、训练与评价边界。
- [原始结果表](tables/fixed-endpoint-results.md) / [CSV](tables/metrics.csv)。
- [逐周期、独立残差及方向诊断补充表](tables/diagnostics.md)。
- [参考文献](references.bib)。
- [LF11终局记录](../../docs/experiment/2026-09-11-phk-v23-lf11-terminal-closeout.md)。
- [云端可查的关键证据](evidence/README.md)：原始裁决、完整方向诊断、参考盲校准、稀疏输入、固定endpoint与optimizer state及日志。
- 完整运行包在本地outputs/runs/20260910-lf11-sparse-metric-sprint保留；大型全场预测、历史参考和回收归档不随本次关键成果发布。

## 图稿

| 图 | 内容 | 可编辑排版用PDF | 预览PNG |
|---|---|---|---|
| 1 | 四臂与原始强基线正式指标 | [PDF](figures/lf11-matched-metrics.pdf) | [PNG](figures/lf11-matched-metrics.png) |
| 2 | 双周期事件、电流与焦耳功率 | [PDF](figures/lf11-events-and-device.pdf) | [PNG](figures/lf11-events-and-device.png) |
| 3 | 参考峰值时刻相态场与误差 | [PDF](figures/lf11-phase-fields.pdf) | [PNG](figures/lf11-phase-fields.png) |
| 4 | 后验波形对照及电守恒缺陷 | [PDF](figures/lf11-waveform-and-conservation.pdf) | [PNG](figures/lf11-waveform-and-conservation.png) |
| 5 | 实际Adam方向的方程×参数头归因 | [PDF](figures/lf11-equation-head-directions.pdf) | [PNG](figures/lf11-equation-head-directions.png) |

本版支持有边界的诊断性论文贡献，尚不支持优于强基线的PINN求解器主张。后续最优先的实验建议为PROPOSED_NOT_AUTHORIZED。本版提供云端审阅所需的关键成果；完整参考评价仍需复现说明中具名的本地参考数据。
