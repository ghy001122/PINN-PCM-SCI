# PHK-PINN 一手来源与主 baseline 审查（R0）

**审查日期：** 2026-08-27  
**状态：** `R0_PRIMARY_SOURCE_AUDIT_COMPLETE`  
**证据类型：** 文献、作者官方代码仓库与许可文件的来源核验；不是复现、求解、训练或科学验证  
**作用边界：** 本文只约束后续 R1 复现与 baseline 选择，不提高本项目既有 oracle、事件或 PINN 方法证据上限。

## 1. 执行结论

### 1.1 主判定

`SUPPORTED_INTERPRETATION`：**Sharp-PINNs 是当前候选中最合适的 phase-field 主方法锚点，但不适合作为唯一证据 baseline，也不适合把其 GPL 源码直接作为拟公开主库的实现底座。**

理由如下。

1. `VERIFIED`：Sharp-PINNs 与目标问题最接近的部分是耦合 Allen–Cahn/Cahn–Hilliard、弥散界面和多场竞争优化；其正式论文方法由 staggered AC/CH 训练、random Fourier features、modified MLP、hard output constraint 和 gradient-norm loss weighting 组成，并有逐模块消融。[正式论文](https://doi.org/10.1016/j.cma.2025.118346) [arXiv 原文](https://arxiv.org/html/2502.11942)
2. `VERIFIED`：正式论文没有把 causal weighting 或 RAR 列入 Sharp-PINNs 核心方法，但当前官方仓库配置同时出现 `CAUSAL_WEIGHTING`、`RAR_BASE_SHAPE`、`RAR_SHAPE`，且部分 2D 配置写为 800,000 epochs；论文关键 2D 消融则报告 1,000 Adam steps。因此“论文版 Sharp”与“当前仓库 recipe”不是可静默混用的同一实验身份。[论文方法与实验](https://arxiv.org/html/2502.11942) [固定仓库 README](https://github.com/NanxiiChen/sharp-pinns/blob/4b7029e3e1e0b82482d245ba12e3ec0945d87ed9/README.md)
3. `VERIFIED`：Sharp 官方仓库为 GPL-3.0；可独立运行 comparator，或按论文公式 clean-room 重实现，但若复制、修改并分发其代码，需要按 GPL 处理，不能预设与主项目的发布许可天然兼容。[固定仓库](https://github.com/NanxiiChen/sharp-pinns/tree/4b7029e3e1e0b82482d245ba12e3ec0945d87ed9) [许可文件](https://github.com/NanxiiChen/sharp-pinns/blob/4b7029e3e1e0b82482d245ba12e3ec0945d87ed9/LICENSE)
4. `VERIFIED`：Sharp 的 3D “5–10 倍更快”比较使用 A40 GPU 训练 PINN、CPU 运行 FEniCS；这支持该论文特定硬件与算例下的时间结果，不支持对本项目 CPU/GPU、不同精度或不同 oracle 的普遍速度结论。[正式论文](https://doi.org/10.1016/j.cma.2025.118346)
5. `UNKNOWN`：Sharp 论文没有给出足以评价随机训练方差的多 seed 统计；单次消融的排序不能直接当作本项目上的稳定增益。

### 1.2 推荐 baseline 结构

后续应把“一个工程起点”和“多条证据基线”分开：

- **工程起点：** 项目内 clean-room 的 PHK 基础框架；参考 Sharp 的公开公式和模块边界，但不复制 GPL 源码。
- **主 domain anchor：** 固定为 **Sharp-PINNs paper-replication identity**，即只复现论文明确声明的模块与预算；当前仓库的 causal/RAR recipe 另列为 `Sharp-repo-best-method`，不能替代 paper replication。
- **通用 strong anchor：** 至少加入 jaxpi2 中的强通用训练/架构配方和 adaptive pseudo-time control；否则无法区分“PCM 定向模块有效”与“只是用了更现代的通用 PINN 训练系统”。[jaxpi2 论文](https://arxiv.org/html/2604.23528) [固定代码](https://github.com/sifanexisted/jaxpi2/tree/77a5c1315a056388271822c35ad512a5a192b60d)
- **支持型 comparator：** PF-PINNs 用于 NTK/random-batch 与界面采样；Causality-RBAR 用于因果采样/支持集扩张；phase-change heat PINN 与 re-spacing layer 用于时间刚性和相变热基准。
- **物理来源锚点：** Miquel 等 GGST 工作只用于电—热—相态因果链和 wall-cell 几何启发，不作为开放 oracle，也不称为作者模型复现。

## 2. 固定来源、代码与许可

| 对象 | 正式身份与一手论文 | 2026-08-27 核验的官方代码固定点 | 代码许可/可用性判定 |
|---|---|---|---|
| Sharp-PINNs | CMAME 447 (2025), 118346；[DOI](https://doi.org/10.1016/j.cma.2025.118346)，[arXiv 2502.11942](https://arxiv.org/html/2502.11942) | [`4b7029e`](https://github.com/NanxiiChen/sharp-pinns/tree/4b7029e3e1e0b82482d245ba12e3ec0945d87ed9) | [GPL-3.0](https://github.com/NanxiiChen/sharp-pinns/blob/4b7029e3e1e0b82482d245ba12e3ec0945d87ed9/LICENSE)；可独立比较，复制分发受 GPL 约束 |
| PF-PINNs | JCP 529 (2025), 113843；[DOI](https://doi.org/10.1016/j.jcp.2025.113843) | ChuanjieCui [`a25f75b`](https://github.com/ChuanjieCui/PF-PINNs/tree/a25f75b5fd40657e5ce98467d7afd0d0052464d1)；NanxiiChen [`f8a4980`](https://github.com/NanxiiChen/PF-PINNs/tree/f8a4980108504a984695b75d2665b27d5f26cc0b) | 两仓均为 [GPL-3.0](https://github.com/ChuanjieCui/PF-PINNs/blob/a25f75b5fd40657e5ce98467d7afd0d0052464d1/LICENSE) |
| Causality-RBAR | arXiv:2410.20212v2；[原文](https://arxiv.org/html/2410.20212) | 论文给出的[官方仓库地址](https://github.com/Centrum-IntelliPhysics/PINNs-Causality-based-Adaptive-Refinement)在核验时返回 404 | 代码与代码许可均 `UNKNOWN`；现阶段只能做 R0 论文复述，不能声称作者代码复现 |
| PirateNet / jaxpi | JMLR 25(402), 1–51 (2024)；[论文页](https://www.jmlr.org/papers/v25/24-0313.html)，[PDF](https://jmlr.org/papers/volume25/24-0313/24-0313.pdf) | jaxpi `pirate` 分支 [`9b5196b`](https://github.com/PredictiveIntelligenceLab/jaxpi/tree/9b5196b846285c32a8f2e337982d19699de85956) | **不是 Apache/MIT**；[Penn 定制许可](https://github.com/PredictiveIntelligenceLab/jaxpi/blob/9b5196b846285c32a8f2e337982d19699de85956/LICENSE)仅允许非营利研究使用，且未经 Penn 书面批准不得向第三方分发原软件或修改版 |
| jaxpi2 / adaptive pseudo-time | arXiv:2604.23528v1；[原文](https://arxiv.org/html/2604.23528) | [`77a5c13`](https://github.com/sifanexisted/jaxpi2/tree/77a5c1315a056388271822c35ad512a5a192b60d) | 仓库为 [Apache-2.0](https://github.com/sifanexisted/jaxpi2/blob/77a5c1315a056388271822c35ad512a5a192b60d/LICENSE)；论文正文为 CC BY-NC-SA 4.0，且当前是预印本 |
| Re-spacing layer | CMAM 200 (2025), 167–179；[出版社页/正确 DOI](https://doi.org/10.1016/j.camwa.2025.09.014)，[IBM Research 条目](https://research.ibm.com/publications/stabilize-physics-informed-neural-networks-for-stiff-differential-equations-re-spacing-layer) | 未在论文出版社页或 IBM 条目发现作者官方代码链接 | 代码与许可 `UNKNOWN` |
| Phase-change heat PINN | IJHMT 252 (2025), 127430；[DOI](https://doi.org/10.1016/j.ijheatmasstransfer.2025.127430)，[arXiv 2410.14216](https://arxiv.org/abs/2410.14216) | 未在论文一手载体中发现作者官方代码仓库 | 代码与许可 `UNKNOWN` |
| Miquel 等 PCM multiphysics | Journal of Applied Physics 136, 145102 (2024)；[DOI](https://doi.org/10.1063/5.0222379)，[arXiv 原文](https://arxiv.org/html/2409.06463) | 论文未给出作者代码仓库 | 代码许可 `UNKNOWN`；而且若干关键物性并未公开，不能形成开放复现闭环 |

> 许可判定只用于本项目的采用边界，不构成法律意见。任何准备分发的外来代码仍需逐文件 provenance 检查。

## 3. 逐项方法剖析

### 3.1 Sharp-PINNs

**原始想法与场景。** `VERIFIED`：作者针对腐蚀 phase-field 中耦合 AC/CH 方程的竞争优化，交替最小化两类 PDE 残差；网络同时使用 RFF、modified MLP 与基于 KKS 关系的 hard output constraint，并使用 gradient-norm loss balancing。[论文第 3 节](https://arxiv.org/html/2502.11942)

**真实增益。** `VERIFIED`：2D 双坑算例在相同表中，完整 Sharp 的平均绝对 L2 error 为 `6.066e-4`；去掉 stagger、hard constraint、modified MLP、Fourier embedding 和全部增强后分别为 `3.974e-2`、`8.494e-3`、`1.554e-2`、`1.671e-2`、`2.006e-1`。论文还报告 3D 单坑/双坑的 PINN 时间 17.05/18.40 min，对应 FEniCS 107.70/197.23 min，但硬件不对等。[论文结果与消融](https://arxiv.org/html/2502.11942)

**oracle、预算与归因。** `VERIFIED`：参考解来自 FEniCS；关键 2D 消融报告 1,000 Adam steps。`UNKNOWN`：没有足够的多 seed 结果来判断排序稳定性；网络容量、采样支持和 wall time 是否在所有消融中完全等价，需要 R1 从固定代码和实验配置重新核对。[正式论文](https://doi.org/10.1016/j.cma.2025.118346)

**潜在漏洞。**

- `VERIFIED`：paper identity 与 repo recipe 漂移，尤其是 causal/RAR 与 epochs；后续必须保存源码 SHA、配置、预算和模块 manifest。[固定仓库 README](https://github.com/NanxiiChen/sharp-pinns/blob/4b7029e3e1e0b82482d245ba12e3ec0945d87ed9/README.md)
- `SUPPORTED_INTERPRETATION`：其 hard constraint 依赖原腐蚀 KKS 代数关系，不能原样搬到电—热—相态模型。
- `SUPPORTED_INTERPRETATION`：staggered AC/CH 交替训练解决的是耦合残差竞争，不自动解决 Joule hotspot 欠分辨、脉冲时间刚性或完整器件 OOD。

**迁移边界。**

- `A`：staggered residual scheduling、RFF、modified MLP、逐模块消融设计。
- `A′`：按电、热、相态方程块定义的 block schedule；满足 PCM 初边值与相分数范围的 hard output；phase/hotspot 路由的多频容量。
- **最小 kill test：** 在同一 oracle、同一 collocation support、同一参数量与梯度预算下，先比较 simultaneous 与 block schedule；若仅增加预算才涨点，不算 staggered 增益。

### 3.2 PF-PINNs

**原始想法与场景。** `VERIFIED`：PF-PINNs 用 min–max normalization、初态/移动界面附近的自适应采样，以及 random-batch NTK trace 权重处理耦合 AC/CH corrosion；参考解与数据来自 FEniCS。[正式论文](https://doi.org/10.1016/j.jcp.2025.113843) [固定代码与数据](https://github.com/ChuanjieCui/PF-PINNs/tree/a25f75b5fd40657e5ce98467d7afd0d0052464d1)

**真实证据。** `VERIFIED`：官方代码给出 1D/2D 配置、FEniCS 数据、RAR 和 random-batch NTK 实现；不同公开配置从 4,000 到 800,000 epochs，RAR candidate/support 也随算例变化。[固定 README](https://github.com/ChuanjieCui/PF-PINNs/blob/a25f75b5fd40657e5ce98467d7afd0d0052464d1/README.md) `UNKNOWN`：论文没有给出可直接迁移为本项目阈值的跨 seed、等 wall-time 增益统计。

**潜在漏洞与迁移。**

- `SUPPORTED_INTERPRETATION`：跟踪界面的采样规则利用相场结构先验；用于 PCM 时，必须只由训练期可得的相分数/温度/Joule 指标生成，不能读取 formal oracle。
- `SUPPORTED_INTERPRETATION`：改变 support size 的 RAR 会同时改变优化预算，不能与固定支持集的 PHA-MF/KC 架构消融混在一个 attribution 表中。
- `A`：normalization、random-batch NTK、界面局部采样；`A′`：phase–hotspot 联合采样和多物理残差块权重。
- **定位：** 支持型强基线，不是唯一主底座。

### 3.3 Causality-RBAR

**原始想法与证据。** `VERIFIED`：方法循环执行 causal training、基于残差排序的自适应 refinement、再 causal training；在 Allen–Cahn 固定参数算例中，普通 PINN 即使总 loss 很低也可能得到静止假解，而 RBAR 增加界面附近支持后恢复运动界面。[arXiv 原文](https://arxiv.org/html/2410.20212)

**预算事实。** `VERIFIED`：复杂 hump 案例先做 300k causal 训练，再做三轮 refinement 和 300k causal retraining；每个时间步约 4,000 点，约为原始 400 点的十倍。论文报告该 PINN 约 3 h，而 COMSOL 约 20 s。[复杂案例与成本](https://arxiv.org/html/2410.20212)

**局限与迁移。**

- `VERIFIED`：这是单 Allen–Cahn、固定参数 proof-of-concept，不是电—热—相态器件模型；公开代码当前不可取得。[原文 Data availability](https://arxiv.org/html/2410.20212) [失效官方仓库地址](https://github.com/Centrum-IntelliPhysics/PINNs-Causality-based-Adaptive-Refinement)
- `SUPPORTED_INTERPRETATION`：其主要增益可能来自支持集扩张，而非一个可独立归因的网络模块。
- `A`：causal ordering 与 residual-ranked support refinement；`A′`：按脉冲阶段和 phase/hotspot 指标分层 refinement。
- **定位：** best-method sampling track；不进入固定支持集的主架构消融。

### 3.4 PirateNet / jaxpi

**原始想法。** `VERIFIED`：PirateNet 将 RFF、gated residual blocks 与可训练残差系数结合，残差系数从零初始化，使网络从浅层表示逐渐“长深”；还测试 physics-informed least-squares output initialization。[JMLR 论文](https://www.jmlr.org/papers/v25/24-0313.html)

**真实增益与实验质量。** `VERIFIED`：论文在多项 PDE 上做 5 random seeds 与架构消融；Allen–Cahn 中 PirateNet 相对 L2 error `2.24e-5`，JAX-PI 为 `5.37e-5`，该算例使用谱参考解、300k steps、8192 batch、NTK weighting 与 causal chunks。[论文 PDF](https://jmlr.org/papers/volume25/24-0313/24-0313.pdf) [官方代码分支](https://github.com/PredictiveIntelligenceLab/jaxpi/tree/9b5196b846285c32a8f2e337982d19699de85956)

**决定性许可与可复现性边界。** `VERIFIED`：官方代码是 GPU-only 的旧 JAX 栈，并默认关联 W&B；更重要的是许可证只允许非营利研究使用，且禁止未经 Penn 书面批准向第三方分发软件或修改版。[官方 README](https://github.com/PredictiveIntelligenceLab/jaxpi/tree/9b5196b846285c32a8f2e337982d19699de85956) [Penn 许可](https://github.com/PredictiveIntelligenceLab/jaxpi/blob/9b5196b846285c32a8f2e337982d19699de85956/LICENSE)

**迁移边界。**

- `A`：论文公式层面的 adaptive residual coefficient、gating、PI output initialization 作为 comparator 思路。
- `A′`：对电/热/相态不同分支设置独立深度成长或仅对高频专家使用 adaptive residual blocks。
- **禁止项：** 不把 jaxpi/PirateNet 官方源码或修改版提交进公开主库；若只按论文 clean-room 重实现，也要保留来源并再次做许可/专利边界复核。
- **定位：** 强通用架构 comparator，不是可直接并库的底座。

### 3.5 jaxpi2 与 adaptive pseudo-time

**原始想法。** `VERIFIED`：论文把 PINN 的低 loss 假解解释为有限 collocation 下的 spurious solution，并通过 pseudo-time residual 与重采样形成 homotopy；adaptive pseudo-time 用残差方向上的局部 Jacobian 尺度估计自动调整步长，而不是把物理时间坐标做单调变换。[arXiv 原文](https://arxiv.org/html/2604.23528)

**真实增益。** `VERIFIED`：10 个 benchmark 中，Allen–Cahn 从 baseline `5.17e-6` 改善到 best fixed `3.26e-6`、adaptive `3.05e-6`，提升较小；Gray–Scott 从 `0.414` 到 `0.107`、`0.0152`，Ginzburg–Landau 从 `0.174` 到 `0.0546`、`0.00775`，Rayleigh–Taylor 从 `0.398` 到 `0.00561`、`0.00382`。论文提供 5-seed 更新频率/收缩消融，并指出更新过频会变差。[结果与消融](https://arxiv.org/html/2604.23528)

**局限与迁移。**

- `VERIFIED`：结果运行于 H200，且论文仍为预印本；Allen–Cahn 已接近 float32 floor，不能把小数点差异当作 PCM 上必然的实质收益。[论文实验](https://arxiv.org/html/2604.23528)
- `SUPPORTED_INTERPRETATION`：它与 KC 的机制正交，是最有价值的反事实 control：若 adaptive pseudo-time 已消除所谓“时间刚性”误差，KC 的独立价值必须在事件时间、路径误差或跨协议 OOD 上另证。
- `A`：adaptive pseudo-time、重采样和强训练栈；`A′`：对电—热—相态残差块分别估计 pseudo-time 尺度。
- **定位：** mandatory strong control；代码仓库 Apache-2.0，但复制前仍需核对仓库内第三方组件的逐文件 provenance。[固定代码](https://github.com/sifanexisted/jaxpi2/tree/77a5c1315a056388271822c35ad512a5a192b60d)

### 3.6 Re-spacing layer

**原始想法与证据。** `VERIFIED`：RS-layer 是预训练编码层，把为捕捉陡变而形成的偏斜采样分布映射为更均匀的表示，借此正则化变换空间中的梯度；论文在 1D 奇异摄动方程、ROBER 和 Akzo Nobel stiff ODE 上报告相对 naive PINN 低 2–3 个数量级的相对 L2 error。[出版社页](https://doi.org/10.1016/j.camwa.2025.09.014) [IBM Research](https://research.ibm.com/publications/stabilize-physics-informed-neural-networks-for-stiff-differential-equations-re-spacing-layer)

**局限与迁移。**

- `VERIFIED`：该方法需要独立预训练，实验对象不是 2D multiphysics PCM；作者一手页面未给出代码，因此 R1 成本和复现许可 `UNKNOWN`。
- `SUPPORTED_INTERPRETATION`：它依赖可识别的陡变区域与非均匀样本，是 coordinate/sample re-spacing，不等价于场选择性 kinetics clock；但它是 KC “首次用时间坐标变换处理刚性”类宽泛表述的直接近邻，必须讨论。
- `A`：预训练 re-spacing encoder；`A′`：只作用于相态动力学分支、由训练期相变指标确定的严格单调映射。
- **kill test：** KC 必须在同一采样分布下优于 RS-like mapping，或在跨脉冲 OOD/事件时间上给出 RS-layer 没有的增益。

### 3.7 Phase-change heat PINN

**原始想法与设置。** `VERIFIED`：Madir 等研究 enthalpy-regularized Stefan heat problem；参考解是 Crank–Nicolson/中心差分有限差分。PINN 为 6 层、每层 20 neurons、tanh，使用 1,024 IC、256 BC、10,000 residual points 和 100k Adam steps。[正式论文](https://doi.org/10.1016/j.ijheatmasstransfer.2025.127430) [arXiv](https://arxiv.org/abs/2410.14216)

**真实增益。** `VERIFIED`：低 Stefan 数难例中，equal weighting、IC weight 100、dynamic gradient weighting 的 L2 errors 分别约为 `0.1341±0.005`、`0.0359±0.01`、`0.02565±0.004`；soft attention 为 `0.02484±0.007`，sequence-in-time 加 dynamic weighting 为 `0.01887±0.003`。[作者正式稿](https://ionut.danaila.perso.math.cnrs.fr/zdownload/papers/2025_PINNS_final.pdf)

**局限与迁移。** `VERIFIED`：作者指出权重受采样点数影响，attention mask 需要先验选择，sequential training 可能传播误差，且网络规模、学习率和点数没有系统研究。[作者正式稿](https://ionut.danaila.perso.math.cnrs.fr/zdownload/papers/2025_PINNS_final.pdf) `UNKNOWN`：独立重复的确切 seed 数与官方代码许可。

- `A`：enthalpy phase-change、dynamic gradient weighting、time sequence comparator。
- `A′`：把热相变与电场/Joule heating/相态动力学闭环，而不是把单热方程结果称为器件 PINN。
- **定位：** 机制基准和 related-work 锚点，不是主 device baseline。

### 3.8 Miquel 等 PCM multiphysics

**原始物理对象。** `VERIFIED`：论文构建二维 wall-type GGST PCM 横截面，耦合 multi-phase-field、相依电热传输、Joule heating、latent heat、thermal boundary resistance、quasi-static electrical field，以及 ovonic threshold switching/Poole–Frenkel 电导机制；用自研 C++ 有限差分与显式时间推进。[JAP 正式论文](https://doi.org/10.1063/5.0222379) [arXiv 原文](https://arxiv.org/html/2409.06463)

**决定性的开放性边界。** `VERIFIED`：论文说明若干电导率来自未公开的内部测量，GGST 精确成分保密，只给范围；部分 threshold/heater/TBR 参数是经验校准、借用或估计，且没有开放源码链接。[材料与参数说明](https://arxiv.org/html/2409.06463)

**迁移边界。**

- `A`：wall-cell 拓扑、电—热—相态因果链、Joule/latent/TBR/threshold-switching 的建模清单。
- `A′`：任何使用公开参数、简化单相分数、不同本构或不同几何的项目模型。
- **禁止表述：** 不得称项目的 reduced wall-cell 为 “Miquel model reproduction”、GGST calibrated model 或 experimental validation；不能把该论文当作开放 oracle。

## 4. 需要从《后续研究总规划》纠正的关键项

1. **Sharp 身份纠正。** 不能再把 causal weighting 与 RAR 无条件写成 Sharp 正式论文的核心模块；它们属于当前 repo recipe，需另立版本身份。[论文](https://arxiv.org/html/2502.11942) [repo](https://github.com/NanxiiChen/sharp-pinns/blob/4b7029e3e1e0b82482d245ba12e3ec0945d87ed9/README.md)
2. **Sharp baseline 纠正。** 可称“唯一主 phase-field anchor”，不可称“唯一 baseline”；至少保留 strong general anchor 和 pseudo-time control。
3. **许可纠正。** Sharp/PF 是 GPL-3.0；PirateNet/jaxpi 更严格，是非营利研究、禁止未经批准再分发的 Penn 许可；只有 jaxpi2 仓库核验为 Apache-2.0。[Sharp license](https://github.com/NanxiiChen/sharp-pinns/blob/4b7029e3e1e0b82482d245ba12e3ec0945d87ed9/LICENSE) [PF license](https://github.com/ChuanjieCui/PF-PINNs/blob/a25f75b5fd40657e5ce98467d7afd0d0052464d1/LICENSE) [jaxpi license](https://github.com/PredictiveIntelligenceLab/jaxpi/blob/9b5196b846285c32a8f2e337982d19699de85956/LICENSE) [jaxpi2 license](https://github.com/sifanexisted/jaxpi2/blob/77a5c1315a056388271822c35ad512a5a192b60d/LICENSE)
4. **Re-spacing DOI 纠正。** 正确 DOI 是 `10.1016/j.camwa.2025.09.014`，不是规划中出现过的 `...2025.07.029`。[出版社 DOI](https://doi.org/10.1016/j.camwa.2025.09.014)
5. **Causality-RBAR 可复现性纠正。** 论文里的作者代码链接目前 404，不能列为“有可运行开源代码”的 R1 基线。[论文](https://arxiv.org/html/2410.20212) [仓库地址](https://github.com/Centrum-IntelliPhysics/PINNs-Causality-based-Adaptive-Refinement)
6. **Miquel 身份纠正。** 只能作为 literature-inspired physics topology；未公开物性、保密成分和无代码使其不能成为公开参考求解器。[原文](https://arxiv.org/html/2409.06463)
7. **速度主张纠正。** Sharp 的 3D speedup 与 Causality-RBAR 的约 3 h 对 COMSOL 20 s 同时说明 wall time 强依赖问题、硬件和实现；本项目只能报告等硬件、等精度、等求解目标下的本地测量。[Sharp](https://doi.org/10.1016/j.cma.2025.118346) [Causality-RBAR](https://arxiv.org/html/2410.20212)

## 5. A / A′ 模块边界与分层验证建议

| 层 | 只回答的问题 | 必须固定 | 进入下一层条件 |
|---|---|---|---|
| R0 来源闭合 | 论文、代码、许可和模块身份是否真实 | 本报告中的 DOI、SHA、许可、`UNKNOWN` | 已完成；不代表任何方法可运行 |
| R1 原域 reproduction | 作者原始场景下 paper identity 是否可复现 | oracle、预算、hardware、seed、paper/repo identity | 至少复现 Sharp 一个低成本原域案例；失败则保留失败，不迁移 |
| R2 PCM feasibility | 单个 A′ 模块是否在合格 reduced PCM 对象上有信号 | 同一 support、参数量、梯度预算、训练协议 | 预声明核心指标不劣且至少一个目标指标稳定改善 |
| R3 组合 attribution | PHA-MF、KC、block schedule 是否各自 load-bearing | 完整 factorial/最小充分消融，多 seed | 增益不能仅由采样扩张或更多 steps 解释 |
| R4 formal OOD | 对新几何/脉冲/材料参数的实体级泛化是否成立 | sealed complete-case split、合格 oracle、冻结代码 | 达到预注册阈值才允许写正面方法主张 |

建议的模块身份：

- `A` 直接迁移：RFF、modified MLP、staggered scheduling、random-batch NTK、RAR、causal ordering、adaptive residual coefficient、pseudo-time、RS-layer。
- `A′` PCM 适配：phase–hotspot 路由、field-selective strictly monotone kinetics clock、电/热/相态 block schedule、PCM hard constraints、phase/hotspot sampling、blockwise pseudo-time。
- sampling/RAR、causal training、loss balancing、continuation 只作为公共强训练协议或 supporting controls，不与 PHA-MF/KC 并列包装成多项主创新。

## 6. Remaining `UNKNOWN`

以下未知项在 R1 前必须保持未知，不能用二手综述或仓库存在性补齐：

- Sharp-PINNs 正式结果的随机 seed 数、方差与当前 repo recipe 对 paper table 的精确映射。
- PF-PINNs 各消融是否在完全等 wall-time、等支持集和多 seed 下比较。
- Causality-RBAR 作者代码何时公开、固定版本和许可。
- Re-spacing layer 与 phase-change heat PINN 的作者官方代码、依赖和许可。
- PirateNet 论文公式 clean-room 重实现后对 Penn 许可、潜在专利或其他权利的完整影响。
- jaxpi2 仓库内所有第三方来源是否都可按 Apache-2.0 直接再分发。
- Miquel 模型未公开电导率、保密成分与自研求解器细节；这些信息缺失时，不存在 exact reproduction 路线。
- 上述任一模块在本项目尚未资格化的 electrothermal PCM oracle 上是否能涨点。

## 7. 最终边界自检

- `VERIFIED`：本报告完成了来源、方法、结果、代码固定点和许可的 R0 核验。
- `SUPPORTED_INTERPRETATION`：Sharp 是最佳 phase-field anchor，但多锚点证据设计比“唯一 baseline”更可辩护。
- `UNKNOWN`：任何候选模块是否能在本项目 PCM 对象上成功复现、迁移、组合或超过 baseline。
- 本报告未运行 solver、PINN、训练或 GPU，未生成实验 ledger，未接触 formal/OOD 数据，也未证明 PHK-PINN、PHA-MF 或 KC 有效。
