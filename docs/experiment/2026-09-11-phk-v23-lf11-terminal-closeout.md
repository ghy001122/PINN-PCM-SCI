# PHK-V2.3 LF11 稀疏等观测冲刺终局

- execution_status: COMPLETE
- scientific_outcome: LF11_VALID_FOUR_ARM_NO_MATCHED_INCREMENT
- claim_status: VALID_SPARSE_DIAGNOSTIC_EVIDENCE_NO_MATCHED_PINN_GAIN
- conditional_outcome: NO_PHASE_METRIC_TRIGGER_NO_ADDITIONAL_TRAINING
- candidate_status: NONE
- next_research_execution_authorized: false

用户明确要求执行具名 Sprint，授权了本轮有界实现、训练、分析和本地论文更新。设计来源及执行指令分别保存在[决策报告快照](../notes/2026-09-10-lf11-deep-research-decision-report.md)与[指令快照](../notes/2026-09-10-lf11-authorized-sprint-instructions.md)。本记录覆盖 LF11 执行状态，不改写 LF10 及更早实验。GitHub main 与本地继承基线均核对为918985c88f98321c96e6952c9bdd725bd958ed0e；科学收口时LF11新增代码和成果尚在本地；用户随后授权发布。后续关键证据副本见[云端证据入口](../../paper/paper_v24/evidence/README.md)，原始运行和历史身份记录保留。

## VERIFIED：正式结果

固定 medium 源在坐标索引0,4,8,…及末点选值，得到28,875个正时间位置、86,625个V/T/phase标量观测；231个初态位置单列解析供给。训练未使用旧模型权重、dense事件池、teacher电流/功率或高保真参考。

共同稀疏起点1200 updates，D_B/P_U/P_I/P_M各1200。四臂均形成数值合法的固定端点。正式合计6000，开发0，条件训练0，总计6000/10200。所有臂持续保留相同观测、BC/IC与合法表示；P_I/P_M共用proposal和随机批次。

| 因果比较 | S相对变化 | raw Ephi相对变化 | 其余质量要求 | 裁决 |
|---|---:|---:|---|---|
| D_B→P_U：加入内部PDE | +40.682% | +17.743% | EV恶化7.512%，超5% | 无匹配增量 |
| P_U→P_I：同一uniform目标改重要性proposal | −4.487% | −4.222% | ET/EI/EV非劣通过 | 未达双指标10% |
| P_I→P_M：更改phase目标测度 | −0.0763% | −0.00981% | ET/EI/EV非劣通过 | 未达双指标10% |

D_B与P_U在共同独立4096点AD积分上的内部物理目标为0.64313946、0.12621771，下降80.3748%。物理目标下降与相态误差上升同时成立。P_U两周期recall为0.458315/0.428162，绝对timing误差0.03800/0.04928。四个神经端点均未通过严格器件门，且没有相对同观测强插值的完整优势。

所有方法从各自V/T/phase计算统一面通量和边耗散；原dense LF_ONLY的teacher标量读出未沿用。native reference重算电流NRMSE为1.35e-17，说明读出本身闭合于native离散。P_U电流NRMSE为7.9319%，却有108.964%焦耳能量误差及5.3071电流不平衡RMS；电流与耗散不能相互替代作器件准确性证据。

## VERIFIED：必要条件后续已完成

无正面增量后，对共同起点及四个端点执行一次“方程×参数头”局部诊断，使用真实Adam状态、对应下一批采样和统一分母，历史momentum单列，未施加新optimizer step。方向分解重构误差最多1.53e-18（parent）和2.71e-20（端点）。

三个物理端点中，phase residual→T的局部误差方向均为负；phase方程占正向物理/边界phase-error贡献仅0%、0.4803%、0.3003%。electric与BC则指向phase误差增加。

**SUPPORTED_INTERPRETATION：** 当前局部证据指向电方程/边界路径，未满足phase度量或phase→T主要破坏的条件。因此latent与global-phase备选为NOT_RUN_TRIGGER_NOT_MET；P_S及RAD/PF-GAR为NOT_RUN_NO_MATCHED_POSITIVE_INCREMENT。它们没有被运行失败，也没有被证明普遍无效。单点方向不是全轨迹因果根因。

## VERIFIED：已知波形的后验基线诊断

原B_logit的电流平方误差中92.984%集中在已知脉冲折点±0.02内。新增一次零训练的电势表示诊断：对可见V/U做插值，再乘同一解析U，保留原相态、温度、观测和边界信息。可见V重构最大偏差5.55e-17。

| 指标 | 原B_logit | B_logit_waveform |
|---|---:|---:|
| 电流NRMSE | 103.083% | 0.427827% |
| 电势RMS | 0.00310734 | 0.000902847 |
| 焦耳能量相对误差 | 3.13202% | 2.18741% |
| S / raw Ephi / ET与相态周期指标 | 原值 | 完全相同 |

状态为POSTHOC_SAME_OBSERVATION_BASELINE_DIAGNOSTIC。不替换原三基线表，不改四臂裁决，不称独立确认或PINN创新。它排除了“相对原始插值的表面电流优势必然来自PINN内部物理”的解释；剩余电守恒缺陷和相态timing误差仍在。

## 边界、来源与完成状态

物理、几何、双脉冲、nominal参考和旧证据保持原样。仍是一个初始化、一个已被开发查看的合成无量纲二维案例。观测掩码不是实体级拆分，未建立formal OOD、材料标定、连续体真值、求解器替代或计算加速。LF10界面暴露的三采样流正向证据继续保留，不能算成本轮独立模型重复。

首次云启动因冻结物理加载器缺少已有benchmark-test依赖，在正式optimizer更新前终止；补齐该已有文件后通过零更新隔离检查，共同CPU起点复用。D_B沿用原进程，其余三臂独立调度同一run_role；原协调器的目录守卫阻止了重复P_U启动。最终完成记录来自四个真实端点。

必要产物回收并验证后，实际实例执行关机；当次连接随后被拒绝。本地nominal评价发生在该关机证据之后。[compute-closure.json](../../paper/paper_v24/evidence/compute-closure.json)保存当前证据。两份stress保持sealed/unread。图形依赖缺失仅影响最初绘图；安装到项目环境后从已保存指标绘图，没有重跑正式数值评价。

## 交付与唯一后续决策

- [paper_v24论文包](../../paper/paper_v24/README.md)：完整英文正文、五组PNG/PDF、正式与补充数表、引用和复现说明。
- [固定裁决](../../paper/paper_v24/evidence/local/results.json)、[方程方向诊断](../../paper/paper_v24/evidence/local/equation-head-diagnosis.json)、[条件决定](../../paper/paper_v24/evidence/local/conditional-decision.json)、[后验波形诊断](../../paper/paper_v24/evidence/local/waveform-diagnostic.json)。
- [冻结配置](../../configs/phk_v23/lf11_sprint.json)、[正式端点计数](../../paper/paper_v24/evidence/formal/campaign.json)、[复现入口与checkpoint/日志位置](../../paper/paper_v24/reproducibility.md)。

**HYPOTHESIS / PROPOSED_NOT_AUTHORIZED：** 下一轮最优先验证与电边界相容的V表示，并隔离electric residual→phase的作用；将本轮波形感知插值预先冻结为强基线。首先解决电势读出/边界与相态耦合的可归因性，再决定是否值得继续增加phase模块。本轮不启动该实验。
