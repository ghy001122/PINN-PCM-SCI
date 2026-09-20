# PINN×PCM：共同读出、干净PDE消融与投稿候选稿

本目录承接[17 September稿](../paper_revision_20260917/README.md)，执行用户批准的六阶段修订。旧稿、参考和裁决保留。科学执行收口时未自动提交Git、上传完整数据或投稿。2026-09-20用户另行授权重要成果发布；本目录随`codex/paper-revision-results`发布，完整范围与反例见[发布总结](../../docs/notes/2026-09-20-readout-clean-pde-results-release.md)。

**VERIFIED：**The complete E/F device criterion remains satisfied in 4/4, 4/4 and 4/4 pairs with the finer reader under the original, time-refined and space-refined references, respectively. This supports the two tested reader levels, without certifying arbitrary-grid or continuum accuracy. The original-protocol seed-43 comparison against B_E loses its device-advantage criterion under the spatial reference with the finer reader; robustness is therefore specific to the E/F comparison.

**VERIFIED：**Neither clean pair meets either prescribed residual-increment criterion under any of the three references or two readers. D_E has lower raw phase, current and power RMS errors throughout these comparisons, with other outcomes mixed. This bounded counterexample does not prove equivalence or universal residual redundancy.

主要交付：[正文PDF](manuscript.pdf)、[补充PDF](supplement.pdf)、[可编辑正文](source/manuscript.md)、[可编辑补充](source/supplement.md)、[统一主张矩阵](claim_evidence_matrix.md)、[逐项修订回应](revision-response.md)、[复现与数据说明](data-and-reproduction.md)、[投稿附信草稿](cover-letter-draft.md)。[数表](tables/)及[证据](evidence/)保留全指标、全部事件、反例和实际计数。

本轮新增两个D_E、十对象细读出及D_E双读出。实际3000 Adam、600完整训练评估、27688正解/23596伴随，均在批准上限内；零新参考、零stress。GPU产物已回收；用户重新开启后的实例亦已再次关闭确认，随后仅做本地数组评分与写作。

完整本地数组包：`outputs/submission-archive-20260918`；分包：`outputs/submission-archive-20260918-parts`。隔离目录为`outputs/isolated-array-reproduction-20260918`，只使用NumPy。模型/读出/参考组合不计作独立重复。完整数组尚未公开；代码、数据和作者许可不能由本次本地归档推断。

文稿重建只读本目录source、tables、figures和references：先运行`prepare_document.py`，再用含ReportLab的环境运行`build_pdf.py`。数组重评分及训练复现是两个另列的入口，不会由文稿构建触发。具体命令和信息边界见[复现说明](data-and-reproduction.md)。

稿件定位为合成二维电热相变重建的计算方法论文。严格双周期稳健性、普遍泛化、具名材料与实验验证没有建立。作者/基金/利益/贡献事实、目标期刊、完整公开归档和最终作者批准仍需完成。
