# 最终稿主张—保存记录—图表映射

任务：`PCM-20260929-FINAL-MANUSCRIPT-CONSOLIDATION-01`。科学基线为 `f4e6202487af65756c6fcea896dec353172a7902`；`79542a0`只记录发布状态。本次重新组织文字和已有记录，不新增训练、推理、电学求解或参考轨迹，不改变历史接受终点或判据。

正文权威源为 [source/manuscript.md](source/manuscript.md)，完整补充源为 [source/supplement.md](source/supplement.md)及其明确包含的辅助节。根目录 Markdown、DOCX 和 PDF 均为构建件。下列位置使用章节题名；图号、表号以最终源中的实际编号为准，不沿用旧稿编号。

## 主文证据链

| ID／正文位置 | 可支持的主张与固定选择 | 完整精度来源／本次展示 | 必须相邻保留的限制 |
|---|---|---|---|
| E1：§4.1 Four paired full-label comparisons | **VERIFIED：**两协议、各 seed29/43 的E/F，在共同修复后仍有相态、端口差异。主图采用 spatial reference／fine reader 的四对。 | [reader-all-metrics.csv](../paper_revision_20260918/tables/reader-all-metrics.csv)、[reader-all-effects.csv](../paper_revision_20260918/tables/reader-all-effects.csv)、[reader-all-decisions.csv](../paper_revision_20260918/tables/reader-all-decisions.csv)；展示于 [interface-effects-compact.md](tables/interface-effects-compact.md)与[配置效应图](figures/electrical-interface-effects.png)。 | 两协议分别拟合；reference／reader是敏感性维度，不是独立重复。完整器件判据不等于全部相态、严格事件判据均通过。 |
| E2：§4.1共同修复比较；§6.3 What the experiment identifies | **VERIFIED：**共同末端solve固定各自T/φ，只重算电势、端口及同口径热源；仍保留的差异不能只由末端读出待遇解释。 | 同上完整读出记录；[S4历史后处理对照](source/supplement.md#s4-necessary-development-counterfactuals)保留开发父态身份；[full-label-main.md](tables/full-label-main.md)和[reader-spatial-primary.md](tables/reader-spatial-primary.md)保留完整角色。 | **SUPPORTED_INTERPRETATION：**训练配置留下状态差异。初始V、参数、强制程度、时间支持和梯度映射仍不同，不能孤立归因VJP；后处理不是完整动力学重积分。 |
| E3：§4.2 Coverage-enhanced soft electrical control | **VERIFIED：**shorter协议、seed29/43、spatial/fine下，E相对F_cov电流误差下降约52.68%／66.55%；相态变化及原A/B同列。 | [fcov-all-metrics.csv](../paper_revision_20260926_core/tables/fcov-all-metrics.csv)、[fcov-all-effects.csv](../paper_revision_20260926_core/tables/fcov-all-effects.csv)、[fcov-all-decisions.csv](../paper_revision_20260926_core/tables/fcov-all-decisions.csv)；[连续主表](tables/fcov-continuous-primary.md)及配置效应图。 | 新项替换原电学项；空间覆盖与时间测度一起变化。不是纯覆盖、严格覆盖匹配或VJP因果实验。12条敏感性记录来自两个新终点；F_cov对F原A/B未过，不能笼统宣称全面改善F。 |
| E4：§4.3 Matched removal of the interior residual package；§4.4 The strong interpolation counterexample | **VERIFIED：**E/D_E采用shorter、两seed、spatial/fine；E/B_E固定original/43、fine reader，并列old/refined/spatial三参考，refined指时间细化。 | [reader-all-effects.csv](../paper_revision_20260918/tables/reader-all-effects.csv)及对应metrics/decisions；[D_E独立残差审计](../paper_revision_20260918/tables/clean-pde-audits.csv)；[B_E连续反例源表](tables/P04-original43-fine-continuous-effects.csv)。 | D_E保留电学solve及反馈，仅去除内部热／相残差包；B_E采用其声明的可见T/φ信息利用方式。负面方向与原判据同时保留；不把D_E称data-only，也不把B_E当同信息使用的单因素消融。 |
| E5：§5.1 Phase reconstruction with a complete second-cycle observation gap；§5.2 Port improvements, phase support and strict events | **VERIFIED：**B1端口改善／第二事件恢复与内部相态及严格双周期通过不等价。 | [b1-all-comparisons.csv](../paper_revision_20260921/tables/b1-all-comparisons.csv)、[b1-all-window-outside-full.csv](../paper_revision_20260921/tables/b1-all-window-outside-full.csv)、[b1-all-events.csv](../paper_revision_20260921/tables/b1-all-events.csv)；[连续效应](tables/b1-continuous-ranges.md)、[空间参考支持](tables/b1-event-support-spatial.md)。 | W内仅缺相态标签，V/T和W后相态仍可用；是离线补全，非预测／formal OOD。两seed、三参考、两读出不是12次独立实验；主文不隐藏严格事件失败。 |
| E6：§4.5 Accuracy and actual numerical work；§3.5 Common parents, fixed endpoints and readouts；§6.3；S26 Accuracy and actual work for the primary comparison | **VERIFIED：**并列精度和已有工作计数，区分父态、校准、训练、读出与试探回滚。 | [original-clean-execution.csv](../paper_revision_20260918/tables/original-clean-execution.csv)、[F_cov工作记录](../paper_revision_20260926_core/tables/fcov-work.csv)、[B1训练与校准](../paper_revision_20260921/tables/b1-training-and-calibration-work.csv)、[B1读出](../paper_revision_20260921/tables/b1-readout-work.csv)；本次[主文十臂成本表](tables/accuracy-work-main.md)及[完整阶段表](tables/accuracy-work.md)。 | 相同更新上限不等于相同计算量；稀疏solve、adjoint、网络查询和完整目标评价不是同单位。不同环境墙钟时间不得组成加速比，缺失计数标未记录。 |

这些来源中的 `Ephi` 保持原160×80 ROI、1001时刻测度；fine reader只对应电学读出。电流与功率必须保留原归一化及完整协议／seed／reference／reader键。显示小数不参与重新裁决。已有A/B完整布尔记录与新核心三指标展示各有范围，不得以只复算Ephi、I、P声称重现所有A/B子项。

本轮派生图表的完整精度接口为 [interface-effects-full.csv](tables/interface-effects-full.csv)（候选／比较者原值、完整条件键、原资格、来源与行号）、[accuracy-work-full.csv](tables/accuracy-work-full.csv)（分臂训练记录）和[accuracy-work-stages.csv](tables/accuracy-work-stages.csv)（父态、校准、读出及丢弃工作）。生成入口为 [build_interface_evidence.py](build_interface_evidence.py)，输入选择与数值核对记录为 [interface-evidence-sources.json](tables/interface-evidence-sources.json)。这些文件的生成与复核状态以实际记录为准，不把文件名预留等同检查通过。

## 补充材料与诊断定位

| 补充位置 | 直接来源 | 证据作用与边界 |
|---|---|---|
| S1—S3、S6—S9、S14—S17 | 完整[补充稿](source/supplement.md)及上述reader记录；[参考／读出范围表](tables/claim-reference-scope.md) | 物理合同、训练实现、原评分、参考敏感性及D_E细节；不把数值参照称实验真值或连续误差界。 |
| S10—S13：六臂历史续训 | [历史六臂指标](tables/phase-adapter-metrics.md)、[判决](tables/phase-adapter-decisions.md)、[完整事件](tables/phase-adapter-events.md) | 冻结的不利结果完整保留；不跨轮拼接学习曲线。 |
| S20：B1完整范围与物理图 | 上述B1 CSV；[物理图组](figures/b1-phase-t2.png)、[局部热源](figures/b1-joule_density-t2.png)及全部同组T/φ/q与误差图 | 不以判据热图替代空间物理；保留窗外代价、两事件及所有比较者。 |
| S21—S22：八臂、N/G/S与失效诊断 | [相态矩指标](tables/moments-metrics.md)、[完成性指标](tables/completion-metrics.md)、[逐分量诊断](tables/diagnostic-components.md)；[原完整诊断](../observation_preserving_phase_20260924/physics-objective-diagnostic.md) | 目标补偿有直接证据；完整训练的唯一因果机制没有被隔离。正文仅作范围总结。 |
| S23：条件相态演化 | [原W+A交付](../paper_revision_20260925_integrated/README.md)、[条件相态物理图](figures/conditional-phase-fields.png) | D_80 RMS收益、召回代价、两热口径及接缝并列；不是原C²族可行性证明或神经增量。 |
| S24：F_cov完整对照 | 上述fcov三份完整CSV与[工作记录](tables/fcov-work.md) | 完整三参考／两读出、不利结果和真实终点保留；不放宽原门槛。 |
| S25：P/CS、条件热及联合原型 | [全角色温度／电流／闭合CSV](tables/neuristor-all-roles.csv)、[条件热原结果](../paper_revision_20260928_conditional_thermal/results-report.md)、[已锁定联合结果](../paper_revision_20260929_72h/results-report.md)、[已发布保存数组评分包](../paper_revision_20260929_72h/scoring-subset/README.md) | 独立的拟合VO₂集总数值模型。N/F/S共同读出116.823/102.533/171.691 μA；联合门失败，S回滚至第75接受步，不称收敛，不续训。二维正向证据不因辅助阴性而改写。 |

S25固定12.5 V图及储能分解／闭合恒等式仅作机制说明，不分配因果百分比，不混用不同电压或热残差口径。有关测量接线的未知不被替换为实验温度、相态或历史真值。

## 访问、构建与检查状态

**已核验历史公开范围：**基线精选稿件、源码及具名辅助联合评分子集与紧凑运行证据已由 [f4e6202](https://github.com/ghy001122/PINN-PCM-SCI/commit/f4e6202487af65756c6fcea896dec353172a7902) 发布；[发布记录](../../docs/notes/2026-09-29-joint-reconstruction-manuscript-release.md)说明排除项。这不表示完整二维保存数组评分包已经公开。电路V/I及条件热包的既有公开身份不变。历史隔离复算只证明其各自声明范围，不自动覆盖本轮重构稿或拟新增数据。

**VERIFIED：本轮核心保存数组包已完成本地隔离复算，尚未公开。**[隔离核验记录](core-scoring/independent-verification.json)与[实际复算结果](core-scoring/recomputed/results.json)覆盖十个候选、分别对应两协议的spatial参考，共30/30项指标通过。输入保留0–2.5的全部1001时刻；相态采用原160×80网格中的3872个ROI单元，电流／功率采用fine电学读出。容差为 `rtol=2e-10, atol=2e-12`，最大绝对差为 `7.979727989493313e-17`。

独立目录运行禁止读取原科研仓库及旧bundle数据根，仅现成Python环境保留运行例外；缺输入测试通过，历史来源回退尝试为0。有效输入共335323643字节（319.790 MiB）。这些是本地可移交、可重评分能力的证据，不等于外部访问已落实。

本包重算的范围仅为保存ROI相态与I/P数组指标；全文A/B资格仅冻结复制，没有重新裁决，也没有重算神经AD残差、检查点推理或再训练。完整二维场、检查点与完整再训练能力仍未外部闭合，**P03保持开放**。

本轮唯一正式[五问审阅](submission-decision.md)已完成，五问均通过，裁决为 `STOP_SCIENTIFIC_DEVELOPMENT`。它只关闭本次科学扩展，不替代DOCX/PDF视觉核验或作者批准；保存数组复算依据上列独立记录，不重新开展五问审阅。最终图表源CSV、构建依赖与核验状态由[交付入口](README.md)指向实际生成文件。稿件交付不等于作者批准或投稿。
