# 本轮交付：现稿补强、覆盖增强与 VO₂ 文献模型

任务 `PCM-20260926-CORE-REVISION-VO2-BRIDGE-01` 已完成批准范围。基线 `90508f05a6f233a485413c7589cc74420015cbea`；所有成果保存在新目录，历史终点、阈值和不利结果保持原身份。

**VERIFIED：**两条 F_cov 均完成 1500 次 Adam，seed 29／43 分别完成 300／300 次完整 L-BFGS 评价，终点有效，共同读出完成。E 相对 F_cov 在原 A/B 规则下通过 12/12、12/12 条敏感性条件；F_cov 相对旧 F 分别通过 0/12、0/12。十二条记录对应两个初始化。 完整连续效应和所有比较方向见[覆盖增强报告](coverage-report.md)及补充 S24。

**SUPPORTED_INTERPRETATION：**该比较同时改变空间覆盖和时间测度，只支持对混合测度软控制的配置比较，不能单独归因 VJP。五个作者模型工况、两个步长均完成；其定性功能描述及波形差异如实保留，定量实验复现仍为 **UNKNOWN**。

## 审阅文件

| 交付 | 文件 |
|---|---|
| 连续主稿 | [PDF](manuscript.pdf) · [DOCX](manuscript.docx) · [Markdown](manuscript.md) |
| 完整补充 | [PDF](supplement.pdf) · [DOCX](supplement.docx) · [Markdown](supplement.md) |
| 修订与证据 | [修改说明](revision-notes.md) · [主张—源表—图件映射](claim_evidence_matrix.md) · [真实构建依赖](build-dependencies.json) |
| 新对照 | [F_cov 完整报告](coverage-report.md) · [全部连续效应](tables/fcov-all-effects.csv) · [全部判决](tables/fcov-all-decisions.csv) |
| 文献模型 | [五工况报告及波形](vo2-author-reproduction.md) · [原始资产身份](literature/data-assets.json) |
| 独立复算 | [入口及能力说明](standalone-README.md) · [实际复算记录](evidence/standalone/independent-verification.json) · [外部访问方案](data-access-plan.md) |
| 下一研究 | [有限观测离线重构计划](next-research-plan.md)，`PROPOSED_NOT_AUTHORIZED` |

完整本地复算包为 `D:\Temp\PINN-PCM-Standalone-20260926`。九类保存数组／残差复算全部通过原容差与精确布尔核验，运行时拒绝访问原仓库。保存残差的聚合不等于重新计算神经 AD。尚无实际外部访问链接或 DOI，P03 保持 OPEN。

## 计算与收口

新神经训练仅两个 F_cov；作者模型合计 300,000 个系统步。没有新二维参考、第三步长、额外训练臂或参数扫描。实际训练终止原因：seed 29: EVALUATION_BUDGET_EXHAUSTED；seed 43: EVALUATION_BUDGET_EXHAUSTED_TRIAL_ROLLED_BACK。线搜索试探点与接受态分开，失败前置测量的成本另记。

GPU 结果已回收并核验；关机请求时间 `2026-09-26T13:28:49.036276+00:00`，随后确认 SSH 拒绝连接。证据见[回收关机记录](evidence/core-revision/compute-closure.json)。零更新部署故障、监测断线及盘满时的读出恢复分别保留。两条训练未中断重开；最后读出由已保存时刻恢复，另记至多一个被丢弃的在途电学求解，未增加科学臂。

P02 方法增量、严格双周期、材料验证、泛化与 P03 仍开放。下一步只建议先闭合有限观测重构的数据支路、合法历史和二维热合同，再审查有限 pilot；本轮未执行该研究。用户随后另行授权[精简成果云端提交](../../docs/notes/2026-09-26-core-revision-vo2-bridge-release.md)；完整数据公开和投稿未执行。

原始执行记录的云端副本见[紧凑证据入口](evidence/core-revision/README.md)。完整数组和检查点不在此次提交范围内。
