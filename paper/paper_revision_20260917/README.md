# Revision Roadmap 修订稿：空间参考补证已完成

2026-09-17。按[原Revision Roadmap](../review_20260917/Revision_Roadmap.md)及用户批准的[实施方案](../review_20260917/Implementation_Plan.md)，完成论文修订、两协议固定预测空间参考及完整评分。旧稿和历史判定保留；本页描述当前21页正文、35页补充，不再沿用补证前“待批准/运行中”状态。

## 阅读入口

- [正文PDF](manuscript.pdf) · [正文Markdown](manuscript.md)
- [补充PDF](supplement.pdf) · [补充Markdown](supplement.md)
- [逐项Revision响应](../review_20260917/Roadmap_Execution_Report.md) · [科研终局](../../docs/experiment/2026-09-17-fixed-prediction-spatial-reference-closeout.md)
- [三参考完整指标](tables/spatial-all-fixed-metrics.csv) · [完整事件](tables/spatial-all-fixed-events.csv) · [结果汇总](spatial-summary.json)
- [空间证据核验](spatial-verification.json) · [逐页检查](visual-qa.json)

## 论文新增证据

**VERIFIED：**在保留16套预测和原160×80电学读出的条件下，两条240×120、dt=0.0003125参考完成。四组E/F的完整器件判据在原、时间细化、空间参考下均保持；空间参考电流/功率相对改善范围分别48.82%–77.42%和49.82%–78.56%。这是所测数值对象和参考下的结果。

三项历史A/B随空间参考改变：original/29对B_E及shorter/43对F的相态判据从通过变为未过；original/43对B_E的器件判据从未过变为通过。没有改阈值、换模型或追溯替换旧判定。空间参考下16对象均未严格双周期通过；原时间细化下的shorter/43/E_I阳性不稳定，第一周期recall降至0.897527。

正文5.8、Figure8及补充S15完整呈现以上结果。细参考场作精确交叠体积限制，参考电流/功率保持原生细网格；阈值映射另列诊断，不替换主评价。本轮16000主步、170979内部线性解均在批准预算内；零新训练、零模型前反向、零新预测电学求解，未启GPU、未读stress、未发布Git。

**SUPPORTED_INTERPRETATION：**器件层优势比部分阈值相态/事件主张更稳定。**UNKNOWN / 未建立：**空间收敛阶、连续体真值、预测电学读出网格独立性、稳定严格事件、剩余PDE独立必要性、孤立VJP因果和材料验证。

先前补充S14的完整参考扰动充分条件、[数表](tables/reference-certificates.csv)与[逐分量记录](tables/reference-certificate-components.csv)保留。其r=1是观察到的时间参考差所设假定预算，不是连续体误差界、空间证据或统计置信度；充分认证与本次实际评分分开。

## 文档与数据身份

原[19/27页首次审核修订稿](../paper_revision_20260916/README.md)保留；空间计算前20/30页版本位于`../review_20260917/pre-spatial-revision/`。新空间运行、执行时配置和源码快照、native/mapped参考、阈值指示量及评分位于仓库根下的`outputs/runs/20260917-lf11-spatial-reference/`。原`outputs/submission-archive-20260916`不改写。本地完整数组不是已公开归档，也不等于第三方复现。

当前正文和补充全部页面已检查；新增Figures8/S6/S7、Tables S18–S24及限制/阈值公式另作原尺寸复核。验证覆盖原判据重现、固定预测不变量、数据表、公式和渲染边界。academic-research-suite审核采用同一助手INLINE模式，不是独立同行评审。

## 从已完成数据重建文档

在仓库根目录，用项目Python依次运行本目录的`spatial_report.py`、`update_manuscript.py`、`update_spatial_manuscript.py`、`prepare_document.py`；用已有ReportLab/PyMuPDF文档环境运行`build_pdf.py`、`render_review.py`；最后用项目Python运行`verify_spatial_revision.py`。脚本只消费保存数据和文稿，不训练或重新生成参考。`update_spatial_manuscript.py`须在`update_manuscript.py`之后执行，防止最终稿漏掉S15。

参考生成和一次性空间评分入口单独保留，不属于文档重建；不得为了重建PDF重复启动。实际冻结配置在运行快照中，工作配置已关闭执行权限。

作者、机构、基金、利益、最终责任、目标期刊和公开发布决定仍见[作者确认清单](../review_20260917/Author_Actions.md)。当前为完整作者审阅稿，未代填事实，未代作者提交。
