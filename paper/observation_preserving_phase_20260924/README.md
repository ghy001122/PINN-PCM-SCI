# 2026-09-24观测保持相态补全交付

2026-09-25 后续[定向诊断结果与图表](physics-objective-diagnostic.md)：确认目标取舍、空间采样敏感和严格固定温度约束；没有新训练，旧裁决保持。用户随后授权[诊断成果发布](../../docs/notes/2026-09-25-physics-objective-diagnostic-release.md)。

**VERIFIED：NO_COMPLETION_INCREMENT。** 阶段0—3完成，三臂1800 Adam/600完整L-BFGS；N/G/S对基础的原A_w和独立物理资格均未通过。N集合误差降低34.21%，但相态RMS增加7.95%。不触发阶段4。

先读[完整结果与裁决](results.md)和[可直接入稿的短段落](manuscript-revision-blocks.md)。[方法/信息边界](method-and-information-boundary.md)、[来源](SOURCES.md)、[主稿整合位置](integration-guide.md)、[验证及偏差](validation-and-deviations.md)、[数据与复现](data-and-reproduction.md)说明可复用部分与未闭合问题。

| 内容 | 入口 |
|---|---|
| 三范围全部连续指标、完整读出 | [all-metrics.csv](all-metrics.csv)、[full-readout-metrics.csv](full-readout-metrics.csv) |
| 全20对裁定及连续变化 | [all-pairwise-decisions.csv](all-pairwise-decisions.csv)、[完整JSON](evidence/results.json) |
| 两周期完整事件 | [both-cycle-events.csv](both-cycle-events.csv) |
| 独立D与全程原物理审计 | [raw-physics-audit.csv](raw-physics-audit.csv)、[full-raw-physics-audit.csv](full-raw-physics-audit.csv) |
| FN/FP、相态平方误差与浮点饱和 | [phase-error-decomposition.csv](phase-error-decomposition.csv) |
| 真实profile及训练成本 | [zero-update-profiles.csv](zero-update-profiles.csv)、[actual-training-cost.csv](actual-training-cost.csv) |
| 必要可行性及热下界 | [fixed-support-feasibility.csv](fixed-support-feasibility.csv)、[thermal-integral-bound.csv](thermal-integral-bound.csv) |
| 论文图件 | [信息边界](figures/information-boundary.png)、[三臂结果](figures/three-arm-development.png)，同名PDF可导出 |
| 结果路由与计算收口 | [decision.json](evidence/decision.json)、[关机摘录](evidence/compute-closure-public.json) |

新实现见../../pinn_pcm_sci/phk_v23_observation_preserving_phase.py及对应runner/readout/evaluate模块；实际运行目录为../../outputs/runs/20260924-observation-preserving-phase/。原始完整输入、全部复合场、端口、锁定检查点、独立池、日志与执行源码身份均保留本地。训练实际在CPU，读出/审计使用GPU；设备错误已透明记录并修复后续入口。本轮已回收并关闭实例，完整数组仍本地保存；用户已另行授权精简成果发布，见[发布记录](../../docs/notes/2026-09-25-observation-preserving-phase-results-release.md)。

P02的合格方法增量与P03的外部完整数据访问仍未闭合。旧完整主稿保留，本文交付为可入稿模块和完整证据，不宣称二区竞争力或投稿完成。
