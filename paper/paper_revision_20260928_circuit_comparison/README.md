# 固定样条对照、焦耳能量辨别与现稿收口

**PCM-20260928-CUBIC-ENERGY-DISCRIMINATION-01 已完成批准范围。**十套CS预测锁定一次，十四条角色/步长与PCHIP比较完成；没有新系统轨迹、神经训练、实验CSV读取或GPU作业。科研执行收口时未做外部发布；用户随后另行批准本轮精选成果Git发布，范围与核验见[发布记录](../../docs/notes/2026-09-28-cubic-energy-comparison-release.md)。

**VERIFIED：**CS对抑制两个角色的器件RMS较小，对12.5V、15.8V和激发两个角色较大；静息极小误差改善。各角色方向在两来源步长一致，CS产生保存时刻负电流/负耗散；电流RMS、总能量及区间能量不能互相认证。**UNKNOWN：**绝对用途充分性、连续真解与实验/内部状态增量。

| 交付 | 入口 |
|---|---|
| 完整结果、14行配对及唯一下一动作 | [研究报告](results-report.md) |
| 全精度指标与预测 | [配对CSV](scoring-subset/results/paired-comparison.csv) · [JSON](scoring-subset/results/results.json) · [CS锁定记录](comparison/predictions-locked.json) |
| 最小可移交评分子集 | [运行说明](scoring-subset/README.md) · [独立验证](build/independent-reproduction.json) |
| 实际预测、测试、评分命令 | [执行与复算](run-and-reproduce.md) |
| 新主稿，17页 | [PDF](manuscript.pdf) · [DOCX](manuscript.docx) · [Markdown](manuscript.md) |
| 未改动的完整补充，58页 | [已有PDF](../paper_revision_20260927_circuit_screen/supplement.pdf) · [已有DOCX](../paper_revision_20260927_circuit_screen/supplement.docx) |
| 测量澄清准备，未发送 | [英文草稿](measurement-request-draft.md) · [来源缺项](measurement-source-status.md) |
| 实际交付边界 | [修改说明](revision-notes.md) · [构建](build-and-reproduction-manuscript.md) · [访问方案](data-access-plan.md) · [数据处理](data-handling-record.json) |

独立目录评分与首次完整结果精确一致；旧PCHIP与历史标量保持FP64运算尺度一致，峰精确一致。研究仓库输入访问被实际拒绝，缺输入会报错。唯一建议是先取得具名实验记录的测量接线与参数说明；任何校准、物理状态估计或PINN pilot仍需另行批准。P02、严格双周期、材料/泛化及P03未因本轮关闭。
