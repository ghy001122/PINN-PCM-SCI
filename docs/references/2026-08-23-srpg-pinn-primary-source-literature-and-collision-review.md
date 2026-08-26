# SRPG-PINN 一手文献与 idea 碰撞审查

> 审查截止：2026-08-23  
> 研究状态：`PROPOSED_NOT_AUTHORIZED`  
> 执行边界：本报告只做一手来源审查、语义碰撞判断与实施前门禁设计；未运行 solver、未训练网络、未生成 oracle、未重启任何历史路线。  
> 证据语料：48 篇/项一手论文记录，另核查 26 个作者或项目官方代码、数据与归档载体。公开网页、公开仓库和有明确软件许可的开源实现是三个不同概念。

> **覆盖关系（2026-08-24）**：本文件保留为 2026-08-23 的完整来源矩阵和许可账本；当前 SRPG 决策入口已更新为 [2026-08-24 综合文献、Idea 碰撞与实施前审查](2026-08-24-srpg-integrated-literature-idea-review.md)。新报告补入 history/state 充分性、双侧非对称资格、FP64 strong raw 和透明派生对象边界；不追溯改写本文件的当日审查事实。

## 1. 决策结论

### 1.1 单一裁决

| 问题 | 裁决 | 含义 |
|---|---|---|
| 是否找到与 SRPG-PINN 全机制束相同的工作？ | **`NO_EXACT_BUNDLE_COLLISION_FOUND_IN_BOUNDED_SEARCH`** | `[VERIFIED]` 截至检索截止日，在本次有界一手来源集合中，没有发现同时包含“固定同点支撑、参数双边 `p±`、同网络相律/PDE 响应并 stop-gradient、固定不可训练方向/侧别 pre-head slots、完整案例事件评价、二维电热相场氧化物器件”全部要素的论文。它不是全球优先权证明，也不能保证投稿前没有同期工作。 |
| 宽泛创新叙事是否仍然成立？ | **`BROAD_CLAIM_COLLISION_CONFIRMED`** | `[VERIFIED]` “参数敏感 PINN”“stop-gradient 物理自蒸馏”“潜空间方向约束”“相场/界面 PINN”“事件困难的因果或自适应训练”均已拥挤；任何把其中一个组件单独写成首创的叙事都不安全。 |
| 当前二维电热氧化物对象能否作为开放、独立、可复现 oracle？ | **`OPEN_INDEPENDENT_ORACLE_NO_GO`** | `[VERIFIED]` 10 个物理对象/框架家族、19 个一手载体中，没有单一对象同时闭合动态热、电流连续、局域相态、双极完整事件、绝对时间、固定开源代码与可用输入/数据。不能通过拼接不同来源把多个不完整对象“升格”为 oracle。 |
| 该 idea 是否现在进入实现？ | **`CONDITIONAL_RETAIN / NOT_NOVELTY_CLEARED`** | `[SUPPORTED_INTERPRETATION]` 只保留一个很窄、可证伪的组合假设。对象门未通过前不写 SRPG 训练代码；对象门失败即放弃这条对象路线，而不是继续堆网络、采样或损失。 |

因此，本轮不能满足“确保没有同期直接碰撞”的强要求。能给出的最强结论只是：**截至 2026-08-23 的有界一手来源检索没有发现 exact bundle，但组件级与宽叙事碰撞已经确认，而物理对象可实施性尚未闭合。**

### 1.2 当前最急需解决的问题

`[VERIFIED]` 当前首要瓶颈不是再组合网络模块，而是取得一个**单一来源、许可明确、动态电—热—相态闭合、可重放完整双极局域事件**的对象。没有这个对象：

- SRPG 的事件改善没有可信参照；
- same-network response 可能只是在自我强化同一错误解；
- onset/coverage/recovery 无法证明是物理事件而非离散、采样或尺度伪影；
- 再完整的方法消融也只能形成算法练习，不能支撑目标论文的器件主张。

## 2. 被审查的唯一机制束

本报告不把 “SRPG-PINN” 当成已成立方法，而把它拆成以下可核对指纹：

1. **固定同点支撑**：baseline 与所有参数扰动视图使用完全相同的时空坐标、IC/BC/PDE collocation masks；
2. **参数双边视图**：在同一点计算 `p`、`p+ε_p A_d e_d` 与 `p-ε_p A_d e_d`，并对两侧分别检查物理可容许性；
3. **同网络相律/PDE 响应**：从同一个 PINN 的输出构造方向与侧别响应，例如

   \[
   r_d^s(\xi)=\operatorname{sg}\!\left[
   \frac{\Phi_\eta(u_\theta(\xi;p+s\epsilon_p A_de_d))-\Phi_\eta(u_\theta(\xi;p))}{S_\Phi}
   \right],\qquad s\in\{-1,+1\},
   \]

   其中 `sg` 表示 response 分支停止梯度；
4. **固定不可训练 slots**：在 pre-head latent 中预留 `2|D|` 个固定、seed-independent 的方向/侧别槽，不允许网络学习或旋转这些 selector；
5. **只从 latent 侧匹配**：用 Huber 等有界损失把 slot displacement 与 detached response 匹配，原 PDE/IC/BC 约束仍保留；
6. **完整案例事件评价**：不按轨迹片段随机拆分，以完整器件/几何/协议/初态为实体，评价双极事件的 onset、partial coverage、recovery，以及电、热、相态、守恒和端口守卫。

`[HYPOTHESIS]` 仍可保留的唯一研究问题是：

> 在一个来源合格的二维电热氧化物相场完整事件基准上，固定同点支撑的双边 `p±`、方向/侧别分辨的相律 secant response，与固定不可训练 pre-head slots 的 detached 同网络匹配，能否在相同实际自动微分计算量下，优于 SA-PINN/Jacobian/tangent 与最强相场 causal/adaptive 基线，并稳定改善预注册的完整案例 onset/coverage/recovery？

这是一项**条件研究假设**，不是创新结论。

## 3. 审查方法、分类与边界

### 3.1 来源规则

本次只采用：出版方论文页、arXiv 原文/版本页、作者或项目官方 GitHub、Zenodo/官方数据页、官方项目文档。二手综述、聚合摘要、搜索结果片段和自动相似度分数不参与裁决。论文许可与软件许可分别核对；论文开放获取不自动授予代码许可，GitHub 可访问也不等于 licensed OSS。

### 3.2 语义碰撞分类

| 分类 | 判定标准 |
|---|---|
| `exact` | 同时覆盖本报告第 2 节的完整机制束，且应用/评价语义实质相同。 |
| `direct-near` | 覆盖两个以上核心机制，并会直接削弱 SRPG 的主要因果叙事，但仍缺少至少一个决定性结构。 |
| `component` | 已公开某个关键组件，使该组件不能被单独宣称为创新。 |
| `comparator` | 机制不近似，但构成必须超越的强基线、物理对象或实现检查。 |
| `non-voting lead` | 只能提示拥挤方向；因撤稿、无可核正文或身份不足，不进入正面证据投票。 |

### 3.3 有界性

`[VERIFIED]` 检索重点覆盖 2023-01-01 至 2026-08-23，并纳入必要的奠基性旧文。`[UNKNOWN]` 仍可能存在尚未索引的预印本、正在审稿的工作、私有代码、其他语言材料或截止日之后公开的论文。因此：

- “没有发现 exact”不能写成“世界首创”或“没有同期工作”；
- 投稿前必须再做一次标题—摘要—方程—代码四层 refresh；
- 任何新近 direct-near work 都可能要求缩窄主张或终止路线。

## 4. 最接近工作的语义碰撞矩阵

### 4.1 参数导数、同点响应与 stop-gradient

| 一手工作 | 已覆盖的关键机制 | 与 SRPG 的决定性差异 | 分类与裁决 | 代码/数据状态 |
|---|---|---|---|---|
| [SA-PINN, arXiv:2301.02428](https://arxiv.org/abs/2301.02428)，EAAI 2024，[DOI 10.1016/j.engappai.2024.108764](https://doi.org/10.1016/j.engappai.2024.108764) | 在参数化 PINN 中对 PDE、IC、BC 残差加入相对于 PDE 参数的导数约束；目标正是局部参数邻域的敏感性和移动/尖锐界面。 | 不使用 same-network `p±` 相律 secant、detached response、固定方向/侧别 latent slots 或器件事件指标。 | **`direct-near`**；`[VERIFIED]` 是 SRPG 必须面对的最强邻近基线，不能只与普通 PINN 比。 | arXiv 许可 CC BY 4.0；本次有界检索未确认作者官方代码，软件许可 `UNKNOWN`。 |
| [NPSolver, arXiv:2605.25786](https://arxiv.org/abs/2605.25786)，KDD 2026，[DOI 10.1145/3770855.3818906](https://doi.org/10.1145/3770855.3818906) | 同一输出先经 `K` 步 PCG physics refinement，再把 `sg(F_K(û))` 作为伪目标，与原预测做 response matching。 | response 来自显式数值 refinement，不是参数双边相律响应；不固定 latent slots，也不做双极相场事件。 | **`direct-near`**；`[VERIFIED]` same-output→physics response→stop-gradient 叙事已经存在。 | [官方仓库](https://github.com/intell-sci-comput/NPSolver)公开但截至截止日未见 LICENSE；[数据](https://huggingface.co/datasets/bochengz/NPSolver_datasets/tree/main)与[模型](https://huggingface.co/bochengz/NPSolver_models/tree/main)的可再利用许可仍 `UNKNOWN`。 |
| [When PINNs Go Wrong, arXiv:2604.23528](https://arxiv.org/abs/2604.23528) | 使用固定上一迭代预测作为 stop-gradient 目标，并以相邻两次预测/残差的两点有限差分估计局部残差 Jacobian 尺度；同时直接展示固定 collocation 可能收敛到伪解。 | 不是参数 `p±` 双边视图，也不把响应绑定到方向/侧别 latent slots。 | **`direct-near`**；`[VERIFIED]` stop-gradient、两点局部响应和 fixed-support 风险均直接碰撞。 | [官方 jaxpi2](https://github.com/sifanexisted/jaxpi2)，Apache-2.0。 |
| [PIDO, arXiv:2411.19125](https://arxiv.org/abs/2411.19125)，[DOI 10.1109/TNNLS.2025.3598617](https://doi.org/10.1109/TNNLS.2025.3598617) | 参数系数条件化的 latent dynamics；将解码预测重新编码为 pseudo-label，对 latent dynamics 做同模型一致性对齐。 | 未核到显式 stop-gradient；不是固定同点 `p±` secant、固定 slots 或事件评价。 | **`direct-near`**；`[SUPPORTED_INTERPRETATION]` latent self-alignment 主张已拥挤。 | 官方实现/软件许可 `UNKNOWN`。 |
| [DE-DeepONet, arXiv:2402.19242](https://arxiv.org/abs/2402.19242) | 用 FEM 生成 Gâteaux derivative 标签；沿 KLE、active-subspace、正交或随机方向施加 derivative-enhanced loss。 | 导数目标来自外部高保真计算，不是同网络自响应；属于 operator learning。 | **`direct-near/comparator`**；`[VERIFIED]` 是有外部导数真值时的强方向导数基线。 | [官方代码](https://github.com/qy849/DE-DeepONet)，MIT。 |
| [DINO, arXiv:2206.10745](https://arxiv.org/abs/2206.10745) | 用输入函数—解算子 Jacobian 的 derivative information 训练神经算子。 | 非 PINN 内部 `p±` self-target，也无 slots/事件。 | **`component/comparator`**；导数增强 operator learning 并非新概念。 | [官方代码](https://github.com/tomoleary/dino)，LGPL-2.1。 |
| [Derivative computation in PINNs, arXiv:2608.11020](https://arxiv.org/abs/2608.11020) | 系统比较 AD 与校准 FD 的准确度、速度和显存，并指出含 batch 内样本耦合的架构可能使常规逐样本导数语义出错。 | 研究导数计算，不提出 SRPG 训练机制。 | **`comparator`**；`[VERIFIED]` SRPG 的额外 `p±` 与高阶 AD 成本、导数正确性必须实测。 | 官方代码/许可 `UNKNOWN`。 |
| [DC-PINNs, Phys. Rev. E 2026](https://doi.org/10.1103/5bbf-p6zk)，[arXiv:2604.13723](https://arxiv.org/abs/2604.13723) | 对导数不等式施加单边 penalty，并配合类别/样本自适应权重。 | 约束的是已知导数符号/界，不是双边参数响应和固定 latent 方向。 | **`component`**；方向性/单边导数约束不可称首创。 | 论文 CC BY 4.0；官方软件许可 `UNKNOWN`。 |
| [gPINN, arXiv:2111.02801](https://arxiv.org/abs/2111.02801) | 在损失中加入 PDE residual 的梯度信息。 | 不做参数双边视图、self-response 或 latent slots。 | **`component/comparator`**；奠基性梯度增强基线。 | [官方代码](https://github.com/lu-group/gpinn)，Apache-2.0。 |

### 4.2 参数化潜空间、固定/正交基与表示可辨识性

| 一手工作 | 已覆盖的关键机制 | 与 SRPG 的决定性差异 | 分类与裁决 | 代码/数据状态 |
|---|---|---|---|---|
| [P²INNs, arXiv:2408.09446](https://arxiv.org/abs/2408.09446) | 把 PDE 参数编码到 latent representation，并用 modulation 构成参数化 PINN。 | 不做同点双边 secant、stop-gradient 响应或固定方向/侧别 slots。 | **`direct-near`**；参数进入潜空间不是新颖点。 | [官方仓库](https://github.com/WooJin-Cho/Parameterized-Physics-informed-Neural-Networks)公开但未见 LICENSE，不能称 licensed OSS。 |
| [Multihead PINN with unimodular regularization, Commun. Phys. 2025](https://doi.org/10.1038/s42005-025-02248-1)，[arXiv:2501.12116](https://arxiv.org/abs/2501.12116) | 共享 body、多 heads；从 latent 对输入的导数构造诱导度量，并用 determinant 约束平滑参数变化下的 latent 响应。 | 不用不可训练 side/direction slots、双边 self-response 或事件合同。 | **`direct-near`**；`[VERIFIED]` “让潜空间结构化承载参数响应”已经直接拥挤。 | [官方仓库](https://github.com/pedrota2000/Unimodular_regularization)公开但未见 LICENSE；论文 CC BY 4.0。 |
| [Physics-Informed Neural Embeddings of PDE Solution Families, arXiv:2607.06348](https://arxiv.org/abs/2607.06348) | 共享 body/多线性 heads；用 head orthogonalization 消除表示退化，并在潜空间做 solution-family 分析。 | 不使用 `p±` detached phase-law secant；依赖多头解族。 | **`direct-near`**；`[VERIFIED]` 固定/正交潜空间、表示 gauge 与可解释性叙事已拥挤。 | [官方仓库](https://github.com/pedrota2000/PDE_embeddings)公开但未见 LICENSE。 |
| [Pi-PINN, arXiv:2604.21761](https://arxiv.org/abs/2604.21761) | 共享 physics-informed embedding，以闭式 pseudoinverse 适配线性 head。 | 无 side/direction slots、双边 self-target 与相场事件。 | **`component`**；共享物理 embedding 与固定形式 head 已存在。 | 代码/许可 `UNKNOWN`。 |
| [PICL, arXiv:2401.16327](https://arxiv.org/abs/2401.16327) | 用 PDE 系数定义样本关系，以 physics update/latent anchoring 做物理信息对比预训练。 | 是 FNO 预训练，不是 PINN 内部 `p±` response slots。 | **`direct-near/component`**；物理系数驱动 latent 对齐已存在。 | [官方仓库](https://github.com/CoopLo/PICL)公开但未见 LICENSE。 |
| [DisentangO, arXiv:2410.02136](https://arxiv.org/abs/2410.02136) | 面向跨 PDE 系统的 task-wise adaptive/lifting 与 latent factor disentanglement/identifiability。 | 非固定 selector、非 PINN 双边 response。 | **`component`**；不能把“方向解耦潜变量”作为独立首创。 | 官方代码/软件许可 `UNKNOWN`。 |
| [Latent Neural Operator, arXiv:2406.03923](https://arxiv.org/abs/2406.03923) | 在低维 latent 中学习 PDE solution operator。 | 无 PINN residual、双边参数响应和事件评价。 | **`component/comparator`**。 | [官方仓库](https://github.com/L-I-M-I-T/LatentNeuralOperator)；软件许可本轮未闭合，`UNKNOWN`。 |
| [PI-Latent-NO, arXiv:2501.08428](https://arxiv.org/abs/2501.08428) | 在 coupled DeepONet latent 中加入 physics-informed 约束。 | 非固定 slots，也不构造 same-network detached secant。 | **`component`**。 | 官方代码/许可 `UNKNOWN`。 |
| [E-PINNs, DOI 10.1007/s44379-026-00086-8](https://doi.org/10.1007/s44379-026-00086-8) | 冻结 base PINN；对坐标与倒数第二层 feature 做 `sg`，训练 epinet，并叠加固定不可训练 prior epinet。 | 用途是 epistemic UQ；固定的是 prior 网络，不是参数方向/侧别 slots，也无 `p±` 事件机制。 | **`direct-near`**；`[VERIFIED]` “stop-gradient penultimate feature + frozen nontrainable component”已出现。 | 论文 2026-08-13 OA，CC BY-NC-ND 4.0；论文称发表时释放代码/模型/数据，但截至截止日出版页未见可核官方链接，`AVAILABILITY_MISMATCH/UNKNOWN`。 |
| [PI-JEPA, arXiv:2604.01349](https://arxiv.org/abs/2604.01349) | v3 曾描述 EMA target encoder、stop-gradient latent predictive target 与按 suboperator 的 PDE residual。 | 不是参数双边 slot response；且当前记录已撤回。 | **`non-voting lead`**；`[VERIFIED]` v4 于 2026-06-04 以 “Substantial Revision Required” 撤稿且当前无 PDF，因此不得进入强矩阵、基线或正面证据计票。 | 当前许可/可用正文/代码均不足，`UNKNOWN`。 |

### 4.3 相场、界面、能量与动态困难

| 一手工作 | 已覆盖的关键机制 | 与 SRPG 的决定性差异 | 分类与裁决 | 代码/数据状态 |
|---|---|---|---|---|
| [PF-PINO, arXiv:2603.09693](https://arxiv.org/abs/2603.09693) | 参数化 phase-field operator；含 Allen–Cahn—热扩散耦合、界面 Hausdorff/面积指标和参数 OOD。 | 是监督/物理约束 operator，不用 `p±` latent slots；训练的一步样本在同一轨迹内随机 75/25 拆分，弱于完整案例隔离。 | **`direct-near/comparator`**；`[VERIFIED]` “参数化相场+热+界面指标+OOD”宽主张已碰撞。 | arXiv CC BY-NC-ND 4.0；[官方仓库](https://github.com/NanxiiChen/PF-PINO)公开但未见 LICENSE。 |
| [PFNet, arXiv:2605.07279](https://arxiv.org/abs/2605.07279) | 可迁移、能量耗散的微结构 operator，并以熵/热力学参数调制。 | 非 PINN、无器件双极事件或固定 slots。 | **`direct-near/component`**；热力学条件化潜表示已拥挤。 | 官方代码/许可 `UNKNOWN`。 |
| [DPINN, arXiv:2511.23102](https://arxiv.org/abs/2511.23102) | 面向相场流的 discontinuity-aware residual adaptation、局部黏性、time marching 与 loss balance。 | 不使用参数 response；聚焦界面数值困难。 | **`direct-near/comparator`**；事件/尖锐界面失败不能只和普通 PINN 比。 | 官方代码/许可 `UNKNOWN`。 |
| [Sharp-PINNs, arXiv:2502.11942](https://arxiv.org/abs/2502.11942) | staggered Allen–Cahn/Cahn–Hilliard、RFF、modified MLP、hard constraints、causal/RAR，覆盖 2D/3D corrosion。 | 无 `p±` response slots 和氧化物器件双极评价。 | **`direct-near/comparator`**；相场强基线。 | [官方仓库](https://github.com/NanxiiChen/sharp-pinns)，GPL-3.0。 |
| [PF-PINNs, JCP 2025, DOI 10.1016/j.jcp.2025.113843](https://doi.org/10.1016/j.jcp.2025.113843) | Allen–Cahn/Cahn–Hilliard；初值局部 refinement、mini-batch NTK weighting 与 RAR。 | 无参数双边或固定潜槽。 | **`direct-near/comparator`**；相场采样/加权强基线。 | [官方仓库](https://github.com/NanxiiChen/PF-PINNs)，GPL-3.0。 |
| [PINNs-MPF, arXiv:2407.02230](https://arxiv.org/abs/2407.02230)，[DOI 10.1016/j.enganabound.2025.106200](https://doi.org/10.1016/j.enganabound.2025.106200) | 多相场网络、时空分解、界面采样和 transfer。 | 不做参数响应或器件事件，但直接处理 multi-phase interface。 | **`component/comparator`**。 | [官方仓库](https://github.com/SFETNI/PINNs_MPF--a-Physics-Informed-Neural-Network-for-Multi-Phase-Field-problems)，MIT。 |
| [Phase-Field DeepONet, arXiv:2302.13368](https://arxiv.org/abs/2302.13368)，[DOI 10.1016/j.cma.2023.116299](https://doi.org/10.1016/j.cma.2023.116299) | 学习相场演化 operator。 | 非 PINN 内部 response，不是电热器件事件。 | **`comparator`**。 | [官方仓库](https://github.com/weili101/Phase-Field_DeepONet)公开但未见 LICENSE。 |
| [Causal + RBAR for Allen–Cahn, arXiv:2410.20212](https://arxiv.org/abs/2410.20212) | 把 causal training 与 residual-based adaptive refinement 用于相场动态。 | 无参数 slots。 | **`direct-near/comparator`**；SRPG 必须证明不是一般 causal/adaptive 训练收益。 | 官方软件许可 `UNKNOWN`。 |
| [Energy Dissipation Preserving PINN, arXiv:2411.08760](https://arxiv.org/abs/2411.08760) | 对 Allen–Cahn 动力学加入能量耗散保持。 | 无参数 response 与器件协议。 | **`direct-near/comparator`**；能量耗散约束不是新颖点。 | 代码/许可 `UNKNOWN`。 |
| [Ferroelectric phase-field PINN, arXiv:2409.02959](https://arxiv.org/abs/2409.02959) | 用能量耗散约束学习铁电相场平衡微结构。 | 作者明确把动态演化列为不能直接处理的范围；无电热双极事件。 | **`direct-near`**；禁止“首个 PINN 用于铁电相场”及“首次能量约束铁电 PINN”叙事。 | 官方代码/许可本轮未确认，`UNKNOWN`。 |
| [Quantification of gradient energy coefficients using PINNs, IJMS 2024](https://doi.org/10.1016/j.ijmecsci.2024.109210) | 用仿真/原子尺度测量标签进行铁电相场 inverse PINN，反演梯度能系数。 | 是带标签的材料参数反演，不是动态协议双边 latent 机制。 | **`direct-near`**；`[VERIFIED]` 进一步排除“首个 PINN 用于铁电相场”的主张。 | 官方代码与软件许可 `UNKNOWN`。 |
| [Local balance for energy-based PINNs, DOI 10.1016/j.ijmecsci.2026.111790](https://doi.org/10.1016/j.ijmecsci.2026.111790) | mpc-PINN 在非凸多物理铁电微结构中施加局部平衡。 | 研究稳态微结构，不是动态完整事件，也无 `p±` slots。 | **`direct-near`**；多物理铁电局部平衡 PINN 叙事已碰撞。 | 2026-08-15 出版；官方代码/许可 `UNKNOWN`。 |
| [IRR-PINNs, arXiv:2511.14348](https://arxiv.org/abs/2511.14348)，[Commun. Phys. DOI 10.1038/s42005-026-02743-z](https://doi.org/10.1038/s42005-026-02743-z) | 用不可逆性/第二律方向约束学习 hidden physics，强调热力学可容许的演化方向。 | 不使用双边参数 response 或固定 slots，但事件方向/不可逆物理叙事相近。 | **`direct-near`**；事件和 directional physics narrative 必须正面对照。 | [官方代码](https://github.com/NanxiiChen/irr-pinns)与[Zenodo 归档](https://doi.org/10.5281/zenodo.20627993)存在；具体复用应服从归档内许可，不能只由论文 CC BY 4.0 推断软件许可。 |

### 4.4 因果、自适应采样与强通用 PINN 基线

| 一手工作 | 对本路线的意义 | 分类 |
|---|---|---|
| [Causal PINNs, arXiv:2203.07404](https://arxiv.org/abs/2203.07404)，[CMAME 421, 116813](https://doi.org/10.1016/j.cma.2024.116813) | causal weights 本身使用 stop-gradient；说明 stop-gradient 与时间困难的组合已有强先例。 | `direct-near/comparator` |
| [PirateNets, JMLR 2024](https://www.jmlr.org/papers/v25/24-0313.html) | 面向复杂多尺度 PDE 的强架构/训练基线；不能用弱 MLP raw 制造 SRPG 增益。 | `comparator` |
| [PINNacle, NeurIPS 2024](https://openreview.net/forum?id=aekfb95slj) | 提供复杂 PDE 的统一 PINN benchmark 视角；提醒必须报告跨问题、预算和失败模式。 | `comparator` |
| [ProPINN, arXiv:2502.00803](https://arxiv.org/abs/2502.00803) | 处理传播失败的通用 PINN 方法；事件信息传播困难不能未经对照归因于参数方向结构。 | `comparator` |
| [Residual-based sampling comparison, DOI 10.1016/j.cma.2022.115671](https://doi.org/10.1016/j.cma.2022.115671) | 系统残差自适应采样；必须作为 fixed-support 的相反强策略。 | `comparator` |
| [R3 sampling, ICML 2023](https://proceedings.mlr.press/v202/daw23a.html) | retain–resample–release 动态采样；用于排除“只因更多关注高残差区”这一解释。 | `comparator` |
| [CL-PINN, arXiv:2608.04778](https://arxiv.org/abs/2608.04778) | 参数任务持续学习、主动参数选择与稀疏 physics replay；参数 family 学习的效率主张已拥挤。 | `component/comparator` |

## 5. 碰撞后的可主张边界

### 5.1 仍可条件保留的组合

`[SUPPORTED_INTERPRETATION]` 只有下列**整体组合**尚未在本次有界来源中发现 exact：

> fixed support + bilateral `p±` + side/direction-resolved phase-law response + detached same-network target + fixed nontrainable pre-head slots + complete-case onset/coverage/recovery on a 2D electrothermal oxide phase-field event.

它的潜在论文价值不来自某个单独模块，而来自三件事能否同时成立：

1. 双边同点 secant 确实捕获事件邻域中有物理意义的方向/侧别非对称，而非有限差分噪声；
2. 固定 slots 相对 learned/rotated/generic embeddings 提供稳定、可检验的结构，而不是任意坐标系偏好；
3. 这种结构在**完整实体级 OOD**和强基线下改善局域事件，且守恒、电热端口量与计算成本不退化。

### 5.2 禁止主张清单

以下表述已被一手来源直接否定或证据不足，后续摘要、标题和引言不得使用：

- “首个参数敏感/参数化 PINN”；
- “首个把参数变化编码进 PINN latent 的方法”；
- “首个 stop-gradient/self-distillation physics response”；
- “首个固定或解耦潜空间物理方向”；
- “首个导数/Jacobian/tangent 正则化的 PINN/算子”；
- “首个相场 PINN”“首个铁电相场 PINN”或“首个能量耗散铁电 PINN”；
- “首个相场热耦合 operator/PINN”；
- “首次面向尖锐界面/事件的 causal 或 adaptive PINN”；
- “开源二维电热氧化物双极 oracle 已存在”；
- “没有同期碰撞”“已完成 novelty clearance”或“世界首创”；
- 把 public repo、论文 OA 或 data-on-request 写成 licensed OSS；
- 把不同论文的 PDE、参数、代码和数据拼接后称为“来源原生 oracle”；
- 把 Q-POP、FerroX 或历史 No-Go 自动重启为当前对象；
- 把合成数值结果称作实验真值或 HZO/RRAM 定量验证。

## 6. 二维电热氧化物对象：开放 oracle 审查

### 6.1 资格合同

一个可进入 SRPG 方法研究的对象必须由**同一可追溯来源链**至少闭合：

1. 固定论文版本、代码 commit/release、软件许可和输入 deck；
2. 二维局域相态或连续内部状态，不是单个全局 filament radius/gap；
3. 电流连续/导电律、动态热方程、相态动力学之间双向闭合；
4. 绝对时间和全部决定事件尺度的参数可追溯；
5. 来源原生双极协议，可形成 onset—partial coverage—recovery 完整事件；
6. 参考数据、网格/时间收敛和守恒量足以独立重放；
7. 许可允许本项目复现、修改和分发必要产物。

`[VERIFIED]` “方程相似”“论文图像漂亮”“代码公开”或“框架能实现”均不足以通过该合同。

### 6.2 10 个对象/框架家族的裁决

| 家族与一手载体 | 已闭合内容 | 缺失/冲突 | 裁决 |
|---|---|---|---|
| **HfO₂₋ₓ RRAM 2020**：[npj Comput. Mater. DOI 10.1038/s41524-020-00455-8](https://doi.org/10.1038/s41524-020-00455-8) | `[VERIFIED]` COMSOL 5.4；2D 轴对称 35×20 nm、0.5 nm 网格；Nernst–Planck 氧空位、电流连续、稳态 Joule 热；预置 filament；0.1 V/s 三角波，约 `+0.4 V RESET/-0.57 V SET`；形成完整双极物理比较。 | 热方程没有 `ρc_p∂T/∂t`；raw data only on request；无固定代码、输入 deck、软件许可或 release。论文 CC BY 不等于 COMSOL 模型开放。 | **强物理 comparator；非开放 oracle。** |
| **TaOₓ 2025**：[Sci. Rep. DOI 10.1038/s41598-025-02909-9](https://doi.org/10.1038/s41598-025-02909-9)，[arXiv:2412.12450](https://arxiv.org/abs/2412.12450) | `[VERIFIED]` 动态热、空位 drift/diffusion/Soret、电流连续，报告 forming/reset 的绝对时间。 | 数据声明称 simulation files 在 supplement，但公开附件实际只有 PDF；无 repo、release 或软件许可。论文为 CC BY-NC-ND，仍不是软件许可。 | **`AVAILABILITY_MISMATCH / NO_GO_OPEN_ORACLE`。** |
| **RRAM-COMSOL-Model 历史仓库**：[GitHub](https://github.com/DipeshNiraula/RRAM-COMSOL-Model)，固定 master commit `68f84a752a56918cc1180985e3208546079ca1bc` | `[VERIFIED]` 可见 COMSOL/MATLAB/LiveLink 模型文件。 | 无 tag、release、LICENSE 或独立归档；依赖专有 COMSOL；物理状态是低维全局 filament radius/gap，不是局域 phase-field。不得暗示它是上行 TaOₓ 2025 论文的官方附件。 | **仅历史 comparator；非局域 oracle。** |
| **Sevic–Kobayashi 忆阻相场**：[APL 2023 DOI 10.1063/5.0151532](https://doi.org/10.1063/5.0151532)，[arXiv:2307.14582](https://arxiv.org/abs/2307.14582)；[APL 2025 follow-up DOI 10.1063/5.0290458](https://doi.org/10.1063/5.0290458)，[arXiv:2506.17421](https://arxiv.org/abs/2506.17421) | `[VERIFIED]` 自洽 phase field、连续热与电荷守恒，随机 diffuse interface；后续工作加入形貌和 I–V 比较；实现基于 MOOSE。 | 未找到作者发布的 app、input deck、固定数据或软件归档。使用通用 MOOSE 不等于论文模型开放。 | **方程最近邻；`NO_GO_OPEN_REPLAY`。** |
| **Q-POP-IMT**：[CPC DOI 10.1016/j.cpc.2025.109751](https://doi.org/10.1016/j.cpc.2025.109751)，[官方仓库](https://github.com/DOE-COMMS/Q-POP-Modules)，[固定归档](https://doi.org/10.17632/p3395559s6.1) | `[VERIFIED]` MIT、固定 release/归档、开放 FEniCS；二维电—热—相态闭合，可出现局域周期振荡。 | 物理是 IMT/局域振荡而非双极 SET/RESET；既有项目证据已经对相应路线作有界终止。 | **仅历史/条件 comparator；不得自动重启、改写或绕过既有 No-Go。** |
| **Roy ECM 模型**：[arXiv:2201.12304](https://arxiv.org/abs/2201.12304) | `[VERIFIED]` 报告 SET/RESET 10 cycles。 | 无动态热闭合、无公开实现/输入/许可。 | **事件 comparator；非 oracle。** |
| **HZO 90° domain-wall 2026**：[npj Comput. Mater. DOI 10.1038/s41524-026-02028-7](https://doi.org/10.1038/s41524-026-02028-7) | `[VERIFIED]` HZO 90°/180° domain-wall phase-field 物理较接近目标材料。 | 使用专有 Mu-PRO；无动态热、绝对时间闭合或开放代码。 | **材料/畴壁 comparator；非电热事件 oracle。** |
| **PCM 全耦合相场**：[ACS Appl. Electron. Mater. DOI 10.1021/acsaelm.2c01327](https://doi.org/10.1021/acsaelm.2c01327)；[Solid-State Electron. DOI 10.1016/j.sse.2022.108542](https://doi.org/10.1016/j.sse.2022.108542) | `[VERIFIED]` 论文层面形成 electrical–thermal–phase 耦合。 | 本次未确认公开、固定、许可明确的实现与 reference deck；材料/协议也不自动等同双极氧化物忆阻事件。 | **方程 comparator；`NO_GO_OPEN_REPLAY`。** |
| **FerroX**：[CPC DOI 10.1016/j.cpc.2023.108757](https://doi.org/10.1016/j.cpc.2023.108757)，[arXiv:2210.15668](https://arxiv.org/abs/2210.15668)，[官方仓库](https://github.com/AMReX-Microelectronics/FerroX)，[Zenodo data](https://doi.org/10.5281/zenodo.7221895) | `[VERIFIED]` TDGL 极化、Poisson 和平衡载流子，公开仓库与论文数据。 | 原模型无热方程、无动态电流连续；本项目对论文固定提交的许可身份审查已以 `R2_P0_TERMINAL_SOURCE_IDENTITY_NO_GO` 收口。当前 development 许可不能追溯性替代旧提交许可。 | **历史来源；R2 不可用，不得以兼容移植偷偷重启。** |
| **通用开源框架/通用相场代码**：[MOOSE](https://github.com/idaholab/moose)、[PRISMS-PF](https://github.com/prisms-center/phaseField)、[OpenFerro](https://github.com/salinelake/OpenFerro)、[Ferret](https://github.com/mangerij/ferret)、[JAX phase-field models](https://github.com/ajvetturini/phase-field-models)、[Ferroelectric-Phasefield](https://github.com/ruher/Ferroelectric-Phasefield) | `[VERIFIED]` 分别提供通用多物理/相场/铁电计算能力；其中 JAX phase-field models 有 [Zenodo 归档](https://doi.org/10.5281/zenodo.18713642)，部分仓库有明确 OSS 许可。 | 通用框架没有自动提供目标材料参数、绝对时间、动态电热闭合、双极事件、参考 deck 和资格证据；部分代码是无量纲 AC/CH 或 BaTiO₃/PZT，不是 HZO/RRAM。 | **实现基础设施；不能拼接升格为 oracle。** |

补充核查的 [HfO₂ 原子尺度数据 Zenodo 记录](https://doi.org/10.5281/zenodo.18322818)可支持原子/机器学习势研究，但不是连续器件模型，也不闭合上述事件合同；其在本路线中最多是未来参数线索，不能用作 oracle。

### 6.3 对象结论

`[VERIFIED]` 当前没有同时满足资格合同的开放独立对象，故裁决为：

> **`OPEN_INDEPENDENT_ORACLE_NO_GO`**

这不是“氧化物电热相场不可建模”的全局结论。它只表示：**本次一手来源集合没有提供可直接进入 SRPG 方法实验的单一、开放、可复现 oracle**。闭源 COMSOL/Mu-PRO 论文可以证明物理可行性，却不能提供独立开放 oracle；开放框架可以提供代码基础，却不能替代材料、协议、绝对时间和事件资格。

## 7. 方法可行性：主要风险与可证伪检查

| 风险 | 为什么是实质风险 | 必须改变哪项行动 |
|---|---|---|
| **self-target 没有新增信息** | response 完全来自同一网络；错误预测也可能生成自洽伪目标，形成移动目标、collapse 或 self-confirmation。 | 与外部 tangent/高保真 derivative、NPSolver-style refinement、上一迭代 target 比较；若 response 只降低自身 loss 而不改善独立事件/守恒指标，终止。 |
| **latent gauge 不可辨识** | pre-head latent 可被可逆旋转/缩放而保持输出；固定 identity slots 可能只是任意坐标选择。 | 必须运行固定 seed 正交旋转、slot permutation、learned slots 和多 seed；若结论随基旋转而翻转，不能主张物理方向表示。 |
| **尺度退化** | `S_Φ`、latent 幅值、head 权重和 Huber transition 可共同吸收误差。 | 预先冻结规范化；报告 raw 与 normalized response；做尺度等价检查。 |
| **有限差分误差/跨分支** | `ε_p` 过小受数值噪声支配，过大则越过非线性事件分支；`p+`/`p-` 可能不再同一局部邻域。 | 做 `ε_p` 收敛与双边 admissibility；若没有稳定区间，停止方向响应主张。 |
| **容量/正则化混淆** | 预留 slots、额外 forward 和损失改变有效容量与优化几何。 | 所有臂使用同一网络族/参数量或明确匹配；加入等参数 generic regularizer、learned-slot 与 rotated-slot 对照。 |
| **计算量失配** | 一次 baseline 加“方向数的两倍”个扰动视图及更高阶导数，实际 forward/backward 与显存开销可能远高于 raw。 | 按实际 F/B、AD primitive、墙钟和峰值内存匹配，不按 update 数匹配。 |
| **导数实现错误** | BatchNorm、attention 或其他跨样本耦合会破坏逐样本 AD 语义；fixed support 也可能掩盖缺陷。 | 禁止未经验证的跨样本层；用有限差分对 AD pullback；另设 dense holdout/resampling 审计。 |
| **事件指标后定** | onset/coverage/recovery 的阈值、连通性和时间窗若看结果再选，会制造增益。 | 在看正式结果前冻结阈值、帧连续性、网格/时间收敛和完整案例聚合。 |
| **相律 circularity** | 若 `Φ_η` 只从网络预测的相态重算，网络可忽略电/热场仍获得一致性。 | response 必须显式测试对温度、电势/电流和相态的依赖；用 field-shuffle、thermal-off 和 phase-only 负控。 |
| **没有合格对象** | 无法分辨算法改善和错误 oracle 的一致性。 | G0 不通过即不实现 SRPG，不用网络搜索救援对象。 |

`[SUPPORTED_INTERPRETATION]` 计算上该方法可以实现，但科学可辨识性远比代码可行性更难。最危险的失败不是 loss 不下降，而是 loss 下降、事件图更平滑，却没有独立物理信息增量。

## 8. 必选强基线与负控

### 8.1 强基线

若未来获得新的明确授权并且对象 G0 通过，最小可投票比较集必须包括：

1. **strong raw PINN**：同网络族、硬初边值、相同完整案例和实际计算预算；
2. **SA-PINN**：对 PDE/IC/BC residual 做参数导数，使用同一 fixed support；
3. **exact tangent/Jacobian baseline**：直接约束输出或 residual 对参数的 Jacobian，不经过固定 latent slots；
4. **DE-DeepONet-like Gâteaux baseline**：仅在能取得独立 derivative 标签时纳入，否则明确记不适用；
5. **physics-response stop-gradient baseline**：NPSolver-style numerical refinement 或 previous-iterate frozen response，比较 self-target 的信息来源；
6. **causal/time-adaptive baseline**：至少 Causal PINNs 级别；
7. **相场强基线**：在 PF-PINNs/Sharp-PINNs/DPINN 可兼容组件中预先选择一个，不得事后挑弱者；
8. **generic latent baseline**：learned slots 或多头正交 embedding，检验固定 identity slots 是否真正必要。

### 8.2 机制负控

- 去掉 stop-gradient，让两侧共同反向传播；
- 关闭双边配对，保持相同额外 forward 预算；
- `p+` only 与 `p-` only；
- 固定 side-balanced label permutation；
- response 在 case 内/跨方向 shuffle；
- 固定 slots 乘以 seed-frozen 正交旋转；
- trainable slots 对 fixed slots；
- head-only response 对 phase-law/PDE response；
- 无 latent loss 的 strong raw；
- 至少三档 `ε_p` 的稳定区间检查；
- fixed support 对 resampled support，并在独立 dense holdout 上评估；
- thermal-off、phase-only、field-shuffle，检验电—热—相态因果链。

`[VERIFIED]` 若 shuffle 不退化、旋转会翻转结论、full-gradient 与 stop-gradient 持平、或 generic learned embedding 同样有效，则不能把效果归因于“方向/侧别相律响应绑定到固定 slots”。

## 9. 实施前停止门

当前状态保持 `PROPOSED_NOT_AUTHORIZED`。以下门是未来计划的必要条件，不构成执行授权。

### G0：单一来源对象资格

必须同时得到固定 SHA/release、软件许可、输入 deck、参考数据、绝对时间、动态热、电流连续、局域相态和来源原生双极事件。任一关键项仍需跨来源拼接即判：

> **`OBJECT_SOURCE_QUALIFICATION_NO_GO` → 放弃当前对象路线，不写 SRPG 代码。**

### G1：可信完整事件 MVE

在任何训练前，由 oracle 单独证明局域双极 onset—partial coverage—recovery，且中/细网格、两级时间步、能量/电荷守恒和端口量收敛。整域瞬翻、单网格事件、无局域 partial coverage 或周期残留均停止。

### G2：strong-raw competence 与瓶颈定位

低/高两个实际计算预算下，raw 必须能解析事件，同时存在明确的参数方向/时间瓶颈。若 raw 已到 oracle 不确定性地板，记 `NO_BOTTLENECK`；若 raw 连事件都不能解析，记 `RAW_INCOMPETENT_ROUTE_NO_TEST`。两者都不允许用 SRPG 救援。

### G3：机制可辨识性

冻结 `ε_p`、归一化、slots、事件阈值和计算匹配；先跑 rotation/scale/shuffle/stop-gradient/fixed-vs-resampled checks。任一关键负控不符合因果预期即终止，不进入 OOD。

### G4：投稿前 novelty refresh

在 formal 之前重新检索截止当日的标题、摘要、关键方程和作者代码；对 SA-PINN、NPSolver、jaxpi2、E-PINNs、PDE embeddings、PF-PINO、IRR-PINNs 及其引用/被引链做定向刷新。仍只能给有界证据，不得升级为 novelty guarantee。

## 10. 第一张可信研究图的唯一可行路径

`[HYPOTHESIS]` 只有 G0–G3 依次通过，第一张可信图才应生成；它必须在**同一个完整案例**中同时呈现：

1. 配对的温度 `T(x,t)`、相态/极化 `P或η(x,t)`、电流/电压或 `Q–V/R–V`；
2. onset、10%–90% partial coverage、recovery 三个预注册事件阶段的空间形貌；
3. strong raw、SA-PINN、一个最强 causal/adaptive phase-field baseline 与 SRPG 的配对曲线；
4. 事件时间、覆盖面积、界面位置/连通域和 recovery 的完整案例误差及配对不确定性；
5. PDE/本构 residual、能量与电荷守恒、端口量守卫；
6. oracle 的网格/时间收敛证据；
7. 每臂实际 forward/backward、AD 操作、墙钟、峰值内存和参数量。

正式 OOD 必须按完整器件/几何/热接触/协议速率/初态 family 隔离，不能把同一轨迹的一步样本或时间窗随机分到 train/test。PF-PINO 的同轨迹 75/25 one-step 拆分可作为一个明确的比较弱点，但不能因此贬低其独立参数 OOD 结果。

若只能画出 loss 曲线、平均场或单一终态截图，而没有局域事件、收敛与因果负控，这不构成可信 first figure。

## 11. 关键一手来源与许可/可用性账本

下表补充前述矩阵未展开但参与范围判断的工作。`UNKNOWN` 是审查结果，不应用推测填补。

| 来源 | 作用 | 代码/数据与许可结论 |
|---|---|---|
| [Energy-based sequential PINN, Applied Mathematics and Computation 2024](https://doi.org/10.1016/j.amc.2024.128890) | 时间分段/能量式相场训练 comparator。 | 官方软件许可 `UNKNOWN`。 |
| [AdaI-PINN, arXiv:2406.04626](https://arxiv.org/abs/2406.04626) | 自适应界面处理 component/comparator。 | 官方软件许可 `UNKNOWN`。 |
| [Coupled Allen–Cahn/Cahn–Hilliard PINO, arXiv:2507.18731](https://arxiv.org/abs/2507.18731) | 耦合相场 operator comparator。 | 官方软件许可 `UNKNOWN`。 |
| [bc-PINN, DOI 10.1016/j.cma.2021.114474](https://doi.org/10.1016/j.cma.2021.114474) | backward-compatible sequential time training 的奠基 comparator。 | [官方仓库](https://github.com/vmattey/bc-PINN)公开；本轮未确认 LICENSE。 |
| [PICL 官方仓库](https://github.com/CoopLo/PICL) | 核对 physics-informed contrastive 实现是否公开。 | public repo，未见 LICENSE；不能称 licensed OSS。 |
| [P²INNs 官方仓库](https://github.com/WooJin-Cho/Parameterized-Physics-informed-Neural-Networks) | 核对 parameter latent modulation 实现。 | public repo，未见 LICENSE。 |
| [NPSolver 官方仓库](https://github.com/intell-sci-comput/NPSolver) | 核对 PCG refinement 与 stop-gradient target。 | public repo，未见 LICENSE；数据/模型平台页面不能自动补足软件许可。 |
| [jaxpi2](https://github.com/sifanexisted/jaxpi2) | 核对 pseudo-time frozen target 与 FD Jacobian。 | Apache-2.0，可作为实现参考，但不能直接把不同物理对象结果迁移为证据。 |
| [DE-DeepONet](https://github.com/qy849/DE-DeepONet) | 核对外部 Gâteaux derivative 标签和方向构造。 | MIT。 |
| [Sharp-PINNs](https://github.com/NanxiiChen/sharp-pinns) / [PF-PINNs](https://github.com/NanxiiChen/PF-PINNs) | 相场强实现基线。 | 均为 GPL-3.0；若复用代码需遵守 copyleft，论文比较可独立重实现并保留来源。 |
| [PINNs-MPF](https://github.com/SFETNI/PINNs_MPF--a-Physics-Informed-Neural-Network-for-Multi-Phase-Field-problems) | 多相场网络/界面采样实现。 | MIT。 |
| [PF-PINO](https://github.com/NanxiiChen/PF-PINO) | 参数相场、热耦合与界面指标参考。 | public repo，未见 LICENSE；论文/arXiv 的 CC BY-NC-ND 不授予代码复用权。 |
| [Unimodular regularization](https://github.com/pedrota2000/Unimodular_regularization) / [PDE embeddings](https://github.com/pedrota2000/PDE_embeddings) | latent geometry/orthogonalization 的直接邻域。 | public repo，未见 LICENSE。 |
| [IRR-PINNs code](https://github.com/NanxiiChen/irr-pinns) / [Zenodo](https://doi.org/10.5281/zenodo.20627993) | 不可逆/第二律方向约束实现与固定归档。 | 存在官方固定载体；具体软件许可应以归档内文件为准。 |
| [Q-POP-Modules](https://github.com/DOE-COMMS/Q-POP-Modules) / [archive](https://doi.org/10.17632/p3395559s6.1) | 开放 2D 电热相态历史 comparator。 | MIT、固定归档；不改变其非双极对象和项目既有终止裁决。 |
| [FerroX](https://github.com/AMReX-Microelectronics/FerroX) / [data](https://doi.org/10.5281/zenodo.7221895) | 铁电 TDGL/Poisson 来源。 | 当前仓库许可可见，但不能追溯性证明论文提交当时 commit 的许可；本项目已终止该来源路线。 |

## 12. 最终建议

### 12.1 方法路线

`[SUPPORTED_INTERPRETATION]` SRPG-PINN 仍有一个窄组合值得**保留为候选**，但只有在对象先闭合、strong raw 确认存在方向/时间瓶颈、并且 SA-PINN/stop-gradient/latent-basis/causal-phase baselines 全部进入比较时，才值得写代码。其论文主张应限于“固定支撑双边相律响应与不可训练方向/侧别 slots 对完整局域事件学习的增量”，而不能扩展为通用参数 PINN、通用物理潜空间或首个相场 PINN。

### 12.2 物理对象路线

`[VERIFIED]` 当前对象门失败。最接近的闭源论文提供物理闭环却不开放，最接近的开放项目不是目标双极对象或已被项目有界终止；通用框架不能经来源拼接变成独立 oracle。**下一步若没有新的单一来源对象证据，就应直接放弃 SRPG 在该对象上的实现，而不是继续“魔改加排列组合”。**

### 12.3 状态保持

最终状态保持：

```text
PROPOSED_NOT_AUTHORIZED
METHOD: BROAD_CLAIM_COLLISION_CONFIRMED
EXACT BUNDLE: NO_EXACT_BUNDLE_COLLISION_FOUND_IN_BOUNDED_SEARCH
NOVELTY: NOT_NOVELTY_CLEARED
OBJECT: OPEN_INDEPENDENT_ORACLE_NO_GO
ROUTE: CONDITIONAL_RETAIN; DO_NOT IMPLEMENT BEFORE NEW PLAN AND G0 PASS
```

Q-POP 只保留为历史/条件比较对象；FerroX/R2 的来源身份终止结论不变。本文没有授权重启 Q-POP、R2、任何新对象、solver、training、formal OOD、GPU 或外部计算。
