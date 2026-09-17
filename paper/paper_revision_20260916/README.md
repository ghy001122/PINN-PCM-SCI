# 相态网络实验与参考补证后的完整论文修订稿

**2026-09-17 审核修订：**按 academic-research-suite 的项目适配 INLINE 全面审核形成 [Full Review](../review_20260917/Full_Review.md) 与 [Revision Roadmap](../review_20260917/Revision_Roadmap.md)，随后修改本文及补充。新增的是论证、方法说明和投稿材料改进；本次审核未训练、求解、加载 checkpoint 或操作 GPU。审阅前的正文、补充及 PDF 保存在 `../review_20260917/baseline/`。同一模型的五视角审核不是独立同行评审。

**2026-09-16 科研执行记录（VERIFIED）：六臂耦合 PINN、两条时间细化参考及一次干净数组重评分完成，当批 GPU 已回收关闭。** 这些是本次审核继承的成果，不是 2026-09-17 新运行的结果。本包保留原 `paper_submission`，未自动提交或公开上传。

主要变化是新增了可检验的网络反事实、实际参考敏感性和完整数组复现。历史四组 E/F 器件优势及全部历史 A/B 裁决经此次时间扰动保留。新增普通/门控头未在任一参考下取得原 A/B 匹配增量；门控 seed43 仅在细化参考下跨严格双周期门，旧参考仍未通过。因此核心方法保持原电学消元，门控不进入已确认创新列表。

## 阅读顺序

- [完整英文正文 PDF](manuscript.pdf) · [可检索正文](manuscript.md)
- [完整补充材料 PDF](supplement.pdf) · [可检索补充](supplement.md)
- [中文科研终局与下一步](../../docs/experiment/2026-09-16-phase-adapter-reference-closeout.md)
- [全部配对效应](tables/paired-effect-sizes.csv) · [16 个对象的两参考指标](tables/all-fixed-metrics.csv) · [完整事件](tables/all-fixed-events.csv) · [严格门逐项失败原因](tables/all-strict-failures.csv)

正文 3.1–3.3 给出核心电学消元接口，3.4/5.6 给出固定预测的参考比较，Figure 7 为历史优势裕量。相态头目的与结论保留在 4.3/5.7；完整公式、训练协议与决策移至补充 S13 和 Table S16。Figure S2 比较两父态四种角色；Figures S1/S3 保留两个 seed 的全部预声明时刻与全域 FN/FP/门图；Figure S4 并列六个新端点双周期的旧/新参考 recall 与 timing。没有删除不利结果或重选展示时刻。

## 可复现材料

- [本地可移植归档 ZIP](../../outputs/PINN-PCM-revision-20260916-array-archive.zip)
- [归档说明与独立评分命令](../../outputs/submission-archive-20260916/README.md)
- [实际独立评分结果](build/independent-rescore.json)
- [最小训练入口准备结果](build/reproduction-entry-check.json)
- [实际执行计数](../../outputs/runs/20260916-lf11-phase-adapter-reference/execution-summary.json)

解压到新目录后，用 Python 3.11 与 NumPy 2.1.1 执行：

```text
python -I portable/rescore.py --root . --output new-audit
```

这只读取数组，先重现旧主表/事件/A/B，再评分新六臂与两参考；不加载 checkpoint、运行网络或求解 PDE。原底流指标对照参考顶流的定义保留，另报 bottom-native 诊断。完整旧/新参考及预测均在归档内，不依赖私人工作区路径。

`portable/reproduce_network.py` 提供独立的 `prepare`、`train`、`infer` 入口。已验证归档可以在新目录准备并进入模块的 prepare-only 路径；本轮没有以复现之名重跑六臂，更没有重训历史父态。训练入口使用归档的已训练父态、sparse 与物理源码，不将完整参考复制进训练目录。

在当前仓库重绘修订图表与正文：

```text
python paper/paper_revision_20260916/build_revision_analysis.py
python paper/paper_revision_20260916/update_manuscript.py
python paper/paper_revision_20260916/prepare_document.py
python paper/paper_revision_20260916/build_pdf.py
```

图表和文字构建依赖已完成评分及保留的旧稿资料；PDF 构建需要记录的 Matplotlib/ReportLab 环境。图表重画、独立数组评分、神经训练是不同复现层级。

`update_manuscript.py` 自动应用 `editorial_revision.py`，因此重建不会把本次审核修订恢复成旧版正文。数学公式／图表和书目引用均从可编辑源生成；源码变化与冻结科研证据分开。

## 必须保留的主张边界

- **VERIFIED：**在所测时间细化下，历史主要器件比较稳定；短间隔 seed43 的历史 S 裕量由 4.4453125e-6 变为 7.9921875e-6。
- **VERIFIED：**新门控 seed43 的 recall 从 0.898602974 变为 0.902063024，预测并未改变；只有新参考下严格通过。新增结构的匹配 A/B 均未建立。
- **SUPPORTED_INTERPRETATION：**新头结果限制本次“只增加相态表示即可补足缺口”的解释，不证明容量普遍无关；原方法收益属于训练方法包。
- **UNKNOWN：**剩余 thermal/phase PDE 独立必要性、孤立 VJP 因果、空间收敛、具名材料标定、实验验证及零样本泛化。

材料映射、最近邻差异与来源访问边界在补充 S12、[参考文献](references.md)和[来源核验说明](source/source-verification.md)。百分数始终注明 NRMSE；B_E 使用同样可用数据包，但实际状态插值只消费 T/phase。作者、基金、利益声明和公开归档地址仍须真实补齐；当前 ZIP 是本地投稿候选包，没有虚构 DOI。

审核后的具体改动与未解决事项见 [修订响应](../review_20260917/Revision_Response.md)；作者事实与投稿决定见 [作者确认清单](../review_20260917/Author_Actions.md)。当前状态是完成辅助审核与本地修订的作者审阅稿，尚不能替代作者最终签署或目标期刊审核。
