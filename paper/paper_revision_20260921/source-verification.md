# P06 指定来源核验：Allen–Cahn 与 L01–L09

Task: `PCM-20260921-FINAL-SPRINT-B1-01`

核验日期：2026-09-21

范围：按用户冲刺指令及评审第 11–13 页核对指定文献；仅书目、原文定位与可复用写作建议。没有运行训练、推理、求解、压力测试或科学重评分，没有修改论文、参考文献或阶段文件。

## 结论与需要修正的地方

- **VERIFIED — Allen–Cahn 的 DOI 是 `10.1016/0001-6160(79)90196-2`。** 现有 `paper/paper_revision_20260918/references.md`、`references.bib` 和生成的 `manuscript.md` 中这个 DOI 均正确。评审所指的重复字符串应在成稿渲染中定位；本次没有将“源码 DOI 错误”当作已证实事实，也没有独立检查该 PDF 的视觉输出。
- **VERIFIED — L08 不能作为 2026 年新期刊论文引用。** arXiv 上传日期是 2026-01-09，记录说明是 ParCFD2024 已报告论文的接受稿；关联 DOI `10.34734/FZJ-2025-02453` 的发布者注册记录给出 2025 年、`Conference Paper`。会议举行年份、出版记录年份和 arXiv 上传年份应分别保留。
- **VERIFIED — L09 已正式出版。** arXiv 中仍显示的“submitted”不能覆盖正式出版记录。JAP 136(14), 145102，在线日期 2024-10-08，纸本期号日期 2024-10-14。
- **VERIFIED / UNKNOWN — L06 与 L07 的指定 arXiv 版本已核实；本次没有核实其后续正式接收记录。** 可以引用这些预印本，不应添加未验证的期刊或会议接收信息。L06 的一个 OpenReview PDF 标为 ICLR2026 在审稿件，但论坛及公开 API 都返回访问验证；这不足以判定最终接收或拒稿。
- **SUPPORTED_INTERPRETATION — 近邻文献支持将本稿定位为成熟约束学习方法在特定电—热—相态重建接口中的适配和受控比较。** 此次有界核验不支持“首次可微 PDE 层”“新隐式微分算法”“硬约束普遍更优”或排除所有先行工作的优先权声明。

## Allen–Cahn：正式元数据与本地源码

**VERIFIED** — Samuel M. Allen and John W. Cahn, *A microscopic theory for antiphase boundary motion and its application to antiphase domain coarsening*, **Acta Metallurgica 27(6), 1085–1095, June 1979**, DOI **10.1016/0001-6160(79)90196-2**。

核验来源为 [Elsevier / ScienceDirect 出版者条目](https://www.sciencedirect.com/science/article/pii/0001616079901962) 的索引元数据及实时读取的 [Crossref 发布者注册元数据](https://api.crossref.org/works/10.1016%2F0001-6160%2879%2990196-2)。二者的标题、期刊、卷期、页码、1979 年 6 月和 DOI 一致。Crossref 登记创建时间不是出版日期。

访问覆盖：出版者元数据和摘要级信息；ScienceDirect 页面及 PDF 的直接访问返回 403，**未读出版者全文**。本项只核对书目，不据此重新解释本稿动力学或提出热力学定理。

本地定位：旧版本 `references.md` 第 13 行、`references.bib` 的 `allen1979phase` 项（第 37–42 行）及 `manuscript.md` 第 421 行。单一可用引用形式为：

Allen, S. M., and Cahn, J. W. (1979). A microscopic theory for antiphase boundary motion and its application to antiphase domain coarsening. *Acta Metallurgica*, 27(6), 1085–1095. https://doi.org/10.1016/0001-6160(79)90196-2

## L01–L09：版本、发表类型和实际阅读范围

下列 arXiv DOI 标识预印本存档，不应误作会议或期刊出版 DOI。日期采用原始记录中的日期；只查到年份时不补造月日。标题链接指向指定版本或正式出版来源，方法链接指向实际访问的原文。

| 评审编号与文献 | VERIFIED：版本、类型和 DOI | 实际访问与范围 |
| --- | --- | --- |
| **L01** Négiar, Mahoney & Krishnapriyan, [Learning differentiable solvers for systems with hard constraints](https://arxiv.org/abs/2207.08675v2) | **ICLR 2023 会议论文**；arXiv v1：2022-07-18；指定/latest v2：2023-04-18。存档 DOI：`10.48550/arXiv.2207.08675`。 | [ICLR / OpenReview 正式论文](https://openreview.net/pdf?id=vdv6CmGksr0) 核实会议身份；[作者全文 §3.1–3.2](https://arxiv.org/html/2207.08675v2) 核读约束层和可微求解。未复现实验、未逐条审计全部证明。 |
| **L02** Um et al., [Solver-in-the-Loop: Learning from Differentiable Physics to Interact with Iterative PDE-Solvers](https://arxiv.org/abs/2007.00016v2) | **NeurIPS 2020 会议论文**；v1：2020-06-30；latest v2：2021-01-05。存档 DOI：`10.48550/arXiv.2007.00016`。2021 是修订上传年份，不改为 NeurIPS 2021。 | [NeurIPS 官方记录](https://proceedings.neurips.cc/paper/2020/hash/43e4e6a6f341e00671e123714de019a8-Abstract.html)；[作者全文](https://arxiv.org/html/2007.00016v2) 的 NON / PRE / SOL 方法设计。未复现实验。 |
| **L03** Mitusch, Funke & Kuchta, [Hybrid FEM-NN models: Combining artificial neural networks with the finite element method](https://arxiv.org/abs/2101.00962v2) | **Journal of Computational Physics 446 (2021), 110651**；出版 DOI：`10.1016/j.jcp.2021.110651`。v1：2021-01-04；v2：2021-09-03；期刊出版记录为 2021 年 12 月。 | [Elsevier 出版者记录](https://www.sciencedirect.com/science/article/pii/S0021999121005465) 的索引信息与 [Crossref 注册元数据](https://api.crossref.org/works/10.1016%2Fj.jcp.2021.110651)；[作者全文](https://arxiv.org/html/2101.00962v2) 的混合建模、伴随和实现部分。未将作者稿等同于逐页校对过的出版定稿。 |
| **L04** Blondel et al., [Efficient and Modular Implicit Differentiation](https://arxiv.org/abs/2105.15183v5) | **NeurIPS 2022 会议论文**；v1：2021-05-31；指定/latest v5：**2022-10-12**。存档 DOI：`10.48550/arXiv.2105.15183`。 | [NeurIPS 官方记录](https://proceedings.neurips.cc/paper_files/paper/2022/hash/228b9279ecf9bbafe582406850c57115-Abstract-Conference.html) 与 arXiv 版本记录；**摘要与书目级核验**，没有逐项核读完整理论证明。 |
| **L05** Lu et al., [Physics-informed neural networks with hard constraints for inverse design](https://epubs.siam.org/doi/10.1137/21M1397908) | **SIAM Journal on Scientific Computing 43(6) (2021), B1105–B1132**；出版 DOI：`10.1137/21M1397908`。官方 History：2021-02-09 投稿，2021-08-11 接受，**2021-11-11 在线发表**；[arXiv v1](https://arxiv.org/abs/2102.04626v1)：2021-02-09。 | SIAM 正式书目、摘要和 History；本次成功访问 [作者全文](https://arxiv.org/html/2102.04626v1)，核读 §2.3 硬边界、§2.6 增广拉格朗日及结论相关段落。比评审原有“未成功展开 HTML”覆盖更深，但不声称完成复现或全部证明审计。 |
| **L06** Baez et al., [Guaranteeing Conservation of Integrals with Projection in Physics-Informed Neural Networks](https://arxiv.org/abs/2511.09048v2) | **指定引用身份：预印本**；v1：2025-11-12；指定/latest v2：**2026-05-23**。存档 DOI：`10.48550/arXiv.2511.09048`。最终同行评审接收状态 **UNKNOWN**。 | [作者全文 §3.3–3.8](https://arxiv.org/html/2511.09048v2) 的已知积分目标与线性、二次、联合投影构造；[OpenReview PDF](https://openreview.net/pdf?id=qJSQHSaRQA) 的索引页首仅表明曾在 ICLR2026 审稿。论坛和 API 访问受限，不能升级为已接受会议论文。 |
| **L07** Golder, Roy & Hasan, [DAE-HardNet: A Physics Constrained Neural Network Enforcing Differential-Algebraic Hard Constraints](https://arxiv.org/abs/2512.05881v1) | **指定引用身份：预印本**；目前记录为 v1：**2025-12-05**。存档 DOI：`10.48550/arXiv.2512.05881`。没有核实独立期刊或会议出版 DOI。 | [作者全文 §3.1 与架构说明](https://arxiv.org/html/2512.05881v1)；核读约束距离最小化、KKT 描述、导数变量及局部 Taylor 近似。没有复现实验或核验所有数值“精确”表述；不要与名称相似的其他 HardNet 论文合并。 |
| **L08** Horne, Jimack, Khan & Wang, [Hard Constraint Projection in a Physics Informed Neural Network](https://arxiv.org/abs/2601.06244v1) | **ParCFD2024 论文接受稿**；arXiv v1：**2026-01-09**，存档 DOI：`10.48550/arXiv.2601.06244`。相关出版 DOI：**`10.34734/FZJ-2025-02453`**；注册发布年份 **2025**，明确类型 **Conference Paper**。 | [作者全文 §3–4](https://arxiv.org/html/2601.06244v1) 及 [DataCite 发布者元数据](https://api.datacite.org/dois/10.34734/FZJ-2025-02453)。注册记录指向 [Jülich 官方存档](https://juser.fz-juelich.de/record/1041821)，其页面本次未成功打开，因此未核实正式文集卷页。记录的通用 BibTeX/citeproc 类型自动映射为 article，不应覆盖其明确 Conference Paper 字段和作者说明。 |
| **L09** Miquel et al., [Multi-physics modeling of phase change memory operations in Ge-rich Ge2Sb2Te5 alloys](https://arxiv.org/abs/2409.06463v1) | **Journal of Applied Physics 136(14) (2024), 145102**；出版 DOI：**`10.1063/5.0222379`**。arXiv v1：2024-09-10；正式在线：**2024-10-08**；纸本期号：**2024-10-14**。 | 实时读取 [Crossref 发布者注册元数据](https://api.crossref.org/works/10.1063%2F5.0222379)；[作者全文 §II.1–II.4](https://arxiv.org/html/2409.06463v1) 的几何、组分/多相、电热耦合。AIP 定稿页面未成功读取；不以此声称逐页校验出版定稿。 |

## 各来源只支持哪些窄主张

以下为 **SUPPORTED_INTERPRETATION**，用于控制定位，而不是新的性能结果。

| 来源 | 可以支持的具体比较 | 本稿不能顺势声称的内容 |
| --- | --- | --- |
| L01 | 学习基函数后通过 PDE 约束求组合系数，是可微约束求解参与学习的直接先例。 | 不能把“存在一个可微 PDE 层”作为本稿独创；其具体约束空间与全网格电学消元不同。 |
| L02 | 数值演化中的神经修正可以在可微求解器内训练。 | 本稿离线状态重建没有变成迭代轨迹修正，也不能沿用该文性能数字。 |
| L03 | 未知神经关系/算子可以嵌入 PDE 约束 FEM，并通过伴随训练。 | 本稿学习 T/φ 状态且仅消去电学变量；没有据此识别未知本构。 |
| L04 | 从最优性或根条件实施隐式微分已有通用方法。 | 本稿一阶电学伴随与显式 Joule 导数的正确实现不构成新微分定理。 |
| L05 | 硬边界参数化、罚函数与增广拉格朗日属于已有约束实现路线。 | 有限电学罚权的 F 不代表全部软约束或约束优化方法。硬边界精确性也不等于内部 PDE 处处精确。 |
| L06 | 给定目标的离散线性/二次积分可以通过投影满足。 | 积分一致不能替代场准确度；本稿不能把参考端口真值改作电学层已知目标。 |
| L07 | 对函数、导数和代数约束实施可微校正已有近邻。 | 对增广变量满足约束与原神经函数导数自洽有区别；本稿不能将全部 HardNet 方法概括为简单电势事后修复。 |
| L08 | 局部离散约束投影层已有流动问题先例；其结果文字报告相近预测表现及并非持续更低的物理误差。 | 该短文不是“硬约束普遍更好”的证据，也不等价于完整接地电学边值求解。 |
| L09 | 壁式 PCM 的几何和电—热—相反馈具有直接器件建模来源。 | 其 Ge-rich GST 多相、组分和材料接口不能替本稿单标量无量纲 φ 提供晶化率、金属分数或氧化物材料标定。 |

## 可直接改写进 Introduction 的英文段落

下列方括号沿用本报告 L 编号，整合时替换为论文实际引文序号；不是新增结果声明。

Differentiable constrained learning has established precedents in solver-in-the-loop correction [L02], hybrid FEM–NN models [L03], PDE-constrained layers [L01], and modular implicit differentiation [L04]. Hard-constraint PINNs and projection methods further distinguish boundary parameterizations, constrained optimization, prescribed integral conservation, and differential-algebraic or local discrete constraints [L05–L08]. Our contribution is a specific partial-elimination interface for electrothermal phase reconstruction: temperature and phase remain neural states, whereas potential follows a grounded finite-volume electrical solve whose face resistances also determine local Joule deposition. Providing the same final electrical solve to the soft and interpolation controls tests whether the observed differences are explained by electrical repair alone. This comparison supports a bounded application of existing constrained-learning principles; it does not establish general superiority of hard constraints or an independent benefit from the remaining thermal and phase residuals.

## 与本轮 B1 和版本叙述的边界

**VERIFIED（当前指令内容）** — 本轮 B1 为第二周期闭区间 `W=[1.01,2.02]` 的 φ 缺测；V/T 保留，区间外 φ（包括 2.02 之后）仍可见。因此任务是离线缺测段重建，不是全程无相态观测、在线预测或材料参数辨识。完整 PDE、参数、初边值已知时，传统正向求解仍可直接运行；文献定位不能将 B1 自动改写为“必须使用 PINN”的应用需求。

**UNKNOWN** — B1 的 E/D_E/F 与合规 B_E 比较能否证明独立动态残差增量。本报告未执行该实验；预期改善仍只能标记为 **HYPOTHESIS**，不得进入已完成结果。阶段 0–2 的用户授权不等于阶段 3 新训练已获执行确认。

成稿应把 2026-09-18 科学证据收口与 2026-09-20 整理发布分开标注；不要用“preceding revision”模糊替代具体证据版本。本次未读取全部版本发布记录，该条是遵循本轮用户指令的写作要求，不是新核验出的 Git 或科学结果。

访问限制收口：Allen–Cahn 出版者全文、L09 AIP 定稿页面和 L08 Jülich 存档页未成功展开；L06 最终会议决定未核实。已用可访问的发布者注册元数据和作者版本完成对应的窄核验，没有依据二手摘要补造状态，也没有为这些访问限制扩大文献搜索范围。
