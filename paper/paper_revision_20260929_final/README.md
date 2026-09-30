# 最终成稿：物理子问题进入学习环的位置

任务 `PCM-20260929-FINAL-MANUSCRIPT-CONSOLIDATION-01`；科学基线 `f4e6202487af65756c6fcea896dec353172a7902`。本轮将已有结果组织为完整论文，没有新增科研轨迹。正式五问裁决为 **5/5 PASS — STOP SCIENTIFIC DEVELOPMENT**；具体交付核验见[收口报告](delivery-report.md)。

## 稿件与证据

| 交付 | 文件 |
|---|---|
| 主稿，18页 | [PDF](manuscript.pdf) · [可编辑DOCX](manuscript.docx) · [展开Markdown](manuscript.md) |
| 完整补充，68页 | [PDF](supplement.pdf) · [可编辑DOCX](supplement.docx) · [展开Markdown](supplement.md) |
| 新主图 | [电学训练接口改变了什么](figures/electrical-interface-effects.pdf) · [PNG](figures/electrical-interface-effects.png) |
| 完整精度比较与原判决 | [CSV](tables/interface-effects-full.csv) · [紧凑表](tables/interface-effects-compact.md) |
| 收益与计算代价 | [主表](tables/accuracy-work-main.md) · [完整记录](tables/accuracy-work.md) · [训练计数CSV](tables/accuracy-work-full.csv) · [分阶段CSV](tables/accuracy-work-stages.csv) |
| 主张及来源 | [一页主张表](claim-evidence-table.md) · [主张—源表—图件映射](manuscript-evidence-map.md) |
| 收口与作者事项 | [五问裁决](submission-decision.md) · [数据声明](data-availability.md) · [作者清单](author-final-checklist.md) |
| 构建 | [真实依赖与步骤](manuscript-build.md) · [依赖身份](build/dependencies.json) |

正文主线为 **离散场观测 → E/F → common repair → F_cov → D_E/B_E → B1**。新图分别标出原始误差及方向，完整数值交给表与CSV；收益和实际算法工作量并列，不比较不可比的历史耗时。B1保留在主文，其他辅助诊断在正文仅一段，完整不利记录留在补充。

**VERIFIED：**保存结果及冻结判决可追溯。**SUPPORTED_INTERPRETATION：**所测试条件下，电学物理如何参与状态学习会影响学习状态及器件读出；配置证据不隔离VJP因果，也不建立普遍优势或材料验证。

全部原参考／读出敏感性条件另以精确原CSV保存：[历史比较连续指标](tables/historical-reader-all-effects.csv)、[原资格判决](tables/historical-reader-all-decisions.csv)、[F_cov连续指标](tables/historical-fcov-all-effects.csv)、[F_cov资格判决](tables/historical-fcov-all-decisions.csv)。新图的33行仅是已声明的展示子集，不替代这些完整记录；[复制来源](tables/all-condition-source-index.json)保留身份。

## 核心相态／电流／功率独立复算

稿件首次导出后完成[核心评分包](core-scoring/README.md)。十个固定候选、两个空间参考，原FP64、160×80相态网格内3872单元ROI、完整0–2.5区间的1001时刻；电学指标使用原fine读出。完整包约 **319.813 MiB**，没有另建重复ZIP。

[独立目录验证](core-scoring/independent-verification.json)在禁止读取原科研数据根的条件下通过 **30/30** 项指标，`rtol=2e-10, atol=2e-12`，最大绝对差 `7.979727989493313e-17`；缺输入测试通过，回退尝试为0。A/B为冻结记录，未从三个指标重新裁决完整资格。此能力是保存数组重评分，不是检查点推理、神经AD重算或再训练。

```powershell
python -I core-scoring/score.py --root core-scoring
```

上述命令从本目录运行，需要Python与NumPy；包可单独复制使用，具体依赖见包内说明。

## 保存、边界与唯一后续动作

权威正文为 `source/manuscript.md`，补充为 `source/supplement.md`（含其明确引用的章节源）。PDF、DOCX和根目录Markdown统一生成；冻结旧稿未覆盖。本轮文件可靠保存在本地，**待远端同步、未公开**；未专门启动GPU，不声称双端备份完成。正式图表、方程、数值输入和检查记录保留；仅本轮已检查的临时渲染副本按规范清理。

唯一后续动作是作者终审：补齐真实署名、机构、经费和利益冲突，决定期刊格式及数据获取安排。P02、P03、严格双周期、材料验证和泛化限制仍开放；它们不自动触发新实验。此次没有Git发布、数据公开、对外发送或实际投稿。
