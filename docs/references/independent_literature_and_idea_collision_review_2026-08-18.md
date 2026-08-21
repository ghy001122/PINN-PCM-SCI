# 抗高频相变器件 PINN：独立文献审查、开源资源核验与 Idea 碰撞评估

- 审查日期：2026-08-18
- 审查方式：独立原始来源检索；**未调用 Idea Skill / IdeaSpark / ResearchStudio**
- 参考输入：`E:/PINN-PCM/deep-research-report.md` 中与谱偏置、相界面、热点和 PHA-MF-PINN 有关的论证
- 对照候选：现有 **Kinetics-Clock PINN（KC-PINN）** 与参考报告提出的 **Phase-Hotspot-Aware Multi-Frequency PINN（PHA-MF-PINN）**
- 证据状态：文献与公开仓库事实为 `VERIFIED`；跨论文综合判断为 `SUPPORTED_INTERPRETATION`；尚未执行的算法收益为 `HYPOTHESIS`
- 本次边界：没有运行物理求解器、没有训练 PINN、没有产生数值或实验结果

## 1. 结论先行

### 1.1 总体判断

`SUPPORTED_INTERPRETATION`：截至 2026-08-18，在本次限定的英文论文、arXiv、出版社页面和作者/机构公开仓库检索中，**没有发现与 KC-PINN 全部承重组件同构的工作**，即没有发现同时满足下列条件的公开论文：

1. 空间局部、严格单调的时间坐标；
2. 时钟速度由相变动力学速率内生驱动；
3. 时钟是 PINN 解网络的输入表示，而非仅用于数据预处理或采样；
4. 对原电—热—相态 PDE 使用完整一、二阶时空链式拉回；
5. 面向二维 VO₂/PCM 器件中的移动相界面；
6. 以恒等时钟、一般坐标变换和同预算谱方法进行机制隔离。

但这不等于“完全无碰撞”。CT-PINN、TAL-PINN、r-adaptive DeepONet、数据驱动时间重参数化、固定/可学习坐标变换和 reaction-progress 表示已经占据了“坐标变换可缓解尖锐解或刚性”的宽泛主张。因此 KC-PINN 的新颖性只能放在**相变速率驱动的局部材料时钟 + 完整多物理拉回 + 器件级验证**这个窄交集上，不能声称“首个自适应坐标 PINN”“首个材料时间神经网络”或“首个抗刚性 PINN”。

`SUPPORTED_INTERPRETATION`：PHA-MF-PINN 也没有发现完全同构论文，即尚未发现同一个由“相变敏感性 + Joule 热点”构成的无量纲 gate 同时控制多频表示容量和 collocation 分配的电热相变器件 PINN。但是它与 2025–2026 年的多分辨率 Fourier 表示、局部专家/域分解、相场物理自适应采样、wavelet 局部容量和“Fourier + 物理指标采样”发生多处强部分碰撞。**若没有 shared-gate 对 separate-gates 的决定性消融，它很容易被审稿人判断为已有模块的 PCM 特化组合。**

### 1.2 推荐排序

| 排序 | 路线 | 当前处置 | 理由 |
|---|---|---|---|
| 1 | **Q-POP-grounded Structural Kinetics-Clock PINN for thermally dominated 2D VO₂ switching** | `CONDITIONAL_GO` | 新颖性相对更窄但更可辩护；Q-POP-IMT 已提供 MIT 许可的二维 VO₂ phase-field oracle 起点；需要缩小物理适用域并修正现有公式和 OOD 定义。 |
| 2 | **PHA-MF-PINN 作为强基线或备用主线** | `CONDITIONAL_GO_AS_FALLBACK` | 实现和消融更直观，但方法碰撞更密；只有 shared electro-phase gate 显著优于独立 gate、普通 Fourier、普通自适应采样和局部专家时，才有主贡献空间。 |
| 3 | **PHA-MF-PINN + GST wall cell** | `CONDITIONAL_GO_AFTER_ORACLE` | 器件问题很合适，但目前没有找到可直接下载、物理闭合且校准完备的 GST wall-cell MPFM 公开代码；完整论文模型含不可公开或需索取的参数。 |
| — | **KC-PINN 与 PHA-MF 同时堆叠为一个首篇方法** | `NO_GO_FOR_FIRST_PAPER` | 参数、采样、坐标和物理机制难以归因，计算预算和审稿风险都会显著上升。 |

### 1.3 推荐的最窄可发表主张

> 在预先冻结的、低场且热主导的二维 VO₂ 电—热—结构/电子相态模型中，一个由结构相变速率驱动、严格单调并保留完整 PDE 链式拉回的局部时间坐标，是否能在同参数、同采样和同训练预算下，比原始时间 PINN、一般单调坐标变换及强谱/采样基线更准确地解析重复脉冲下的结构相前沿、开关延迟和恢复过程？

该表述保留了真正可检验的算法问题，同时不承诺真实器件 GHz 泛化、实验验证、推理加速或普适抗刚性。

## 2. 检索范围、方法与不能保证的事项

### 2.1 检索轴

本次检索围绕四条彼此独立的证据轴进行：

1. **时间/空间坐标重参数化**：coordinate-transformed PINN、adaptive lifting、r-adaptive coordinate、material time、reaction-progress coordinate、stiff neural ODE time reparameterization；
2. **高频与局域多尺度表示**：Fourier features、multiresolution Fourier pyramid、wavelet PINN、local expert/domain decomposition、spectral/causal PINN；
3. **相场与界面采样**：Allen–Cahn、Stefan、multi-phase-field、interface-aware / causality-aware / residual-adaptive sampling；
4. **器件物理和开放 oracle**：VO₂ 双序参量电热相场、GHz 结构动力学、高场缺陷/Poole–Frenkel/弹性效应、GST/GGST wall-cell 多物理模型及开源代码。

优先核验 arXiv 论文页面、期刊出版社页面、作者/机构 GitHub、DOI 数据归档和论文中明确的数据/代码声明；综述和搜索摘要只用于发现线索，不作为关键结论的唯一依据。

### 2.2 检索限制

`UNKNOWN`：任何检索都不能证明“世界上不存在碰撞”。本次仍存在以下盲区：

- 尚未对所有近邻论文进行完整前向/后向引用图遍历；
- 专利、非英语论文、未索引预印本、私有仓库和会议在投稿稿件可能未覆盖；
- 2026 年预印本可能继续修订、补代码或更改题名；
- GitHub 的“公开”不自动意味着可复现，且无许可证的公开代码不应直接复用；
- “未发现全机制同构工作”是截至日期和检索范围内的结论，不是绝对首创声明。

因此，论文中应使用“据限定检索，尚未发现……”而不是“首次”“唯一”或“从未有人研究”。正式投稿前还应做一次基于最终题名、摘要和公式槽位的更新检索。

## 3. 对 deep-research-report.md 的复核

### 3.1 得到支持的核心判断

`SUPPORTED_INTERPRETATION`：参考报告把问题从单一 spectral bias 升级为“局域多尺度 + 尖锐界面 + 多物理刚性 + 小测度采样不足”，这一定位比“PINN 只会低频”更稳健。近年工作分别从不同方向支持这一点：

- [Fourier Feature Pyramids / beignet](https://arxiv.org/abs/2605.24278) 表明多分辨率 Fourier 表示和可控 bandlimit 能显著提高困难 PDE 的精度；
- [AW-PINN](https://arxiv.org/abs/2604.28180) 直接针对局部高幅源造成的谱偏置与损失失衡，自适应 wavelet 的尺度和位置；
- [AB-PINNs](https://arxiv.org/abs/2510.08924) 用全局低频网络、局部网络和残差驱动子域增加处理多尺度解；
- [Auto-Adaptive PINNs for Phase Transitions](https://arxiv.org/abs/2510.23999) 允许由问题特定、可依赖网络梯度的启发式直接控制 Allen–Cahn 界面采样，并报告优于 residual-adaptive 方法；
- [PINNs-MPF](https://arxiv.org/abs/2407.02230) 以空间—时间分解处理多相场界面演化，并有公开的 [MIT 代码](https://github.com/SFETNI/PINNs_MPF--a-Physics-Informed-Neural-Network-for-Multi-Phase-Field-problems)。

因此，应继续把“高频”视作可观测结果或一个失败机制，而不是唯一根因。

### 3.2 需要收窄的部分

参考报告中“phase/hotspot-aware routing + phase/hotspot-aware sampling”的组合在写作时看起来新，但 2025–2026 年的新工作已经分别占据其主要组成：

- 表示侧：beignet、AW-PINN、AB-PINNs、PINN Balls；
- 采样侧：Auto-Adaptive PINNs、causality-guided sampling、phase-field residual refinement；
- 组合结构侧：[2026 Fourier-feature elasto-plastic PINN](https://arxiv.org/abs/2607.25150) 已把 Fourier 输入映射与 strain-adaptive sampling 放在同一 PINN 中。

这不构成 PHA-MF 的精确碰撞，但把创新门槛提高为：**必须证明一个共享且可解释的电—相局部刚性场，同时控制表示和采样，比两个独立 gate、任一单模块和通用组合更好。** 否则贡献更像应用工程组合。

### 3.3 参考报告中的引用可移植性问题

`VERIFIED`：参考文件包含会话内部引用占位符，脱离生成会话后不能供论文或项目审计使用。本报告重新给出可点击的原始来源链接；后续文献库应保存 DOI/arXiv ID、版本、访问日期、代码链接和许可证，而不是沿用这些占位符。

## 4. KC-PINN 的近邻谱系与碰撞矩阵

### 4.1 最强近邻

| 近邻工作 | 已占据的机制 | 与 KC-PINN 的差异 | 碰撞风险 |
|---|---|---|---|
| [CT-PINN, JCP 2025](https://www.sciencedirect.com/science/article/pii/S0021999125004449) | 沿特征曲线学习坐标变换，并同时训练变换后的 PDE 与特征方程，用于激波/双曲守恒律 | 非相变器件；不是由局部相变速率定义的单调时间时钟；目标是特征曲线和子域规则化 | **高家族碰撞 / 中直接碰撞** |
| [TAL-PINN, 2025](https://arxiv.org/abs/2511.04490) | 通过 r-adaptive coordinate 生成学习型辅助场，缓解小黏性冲击、谱偏置和条件问题 | 面向黏性双曲方程；不是电—热—相态闭环，也不是内生 kinetics-clock | **高家族碰撞 / 中直接碰撞** |
| [Caldana & Hesthaven, 2024/2025](https://arxiv.org/abs/2408.06073) | 从隐式求解器的自适应步长学习时间重参数化，使 stiff neural ODE 在新时间中更易积分 | 数据驱动、依赖参考轨迹；是 neural ODE/ROM，不是 PINN PDE 残差中的局部空间时钟 | **中** |
| [TOTR, 2026](https://arxiv.org/abs/2603.16583) | 严格递增、轨迹优化的时间映射缓解 stiff reduced dynamics | 不是 PINN，也不含相变器件空间前沿 | **中语义碰撞** |
| [R-adaptive DeepONet](https://arxiv.org/abs/2408.04157) | 通过自适应坐标处理含尖锐梯度/移动结构的算子学习 | 算子学习而非单案例 PINN；没有 kinetics-specific clock | **中** |
| [PAS-Net, 2025](https://arxiv.org/abs/2511.14925) | 在 physics-informed DeepONet 的 trunk 输入中加入预设或可学习的局部缩放坐标，改善局部、刚性和多尺度动力学 | 是算子学习与空间局部尺度嵌入，不是相变速率驱动的时间时钟 | **中** |
| [Adaptive Coordinate Transforms for Neural Operators, 2026](https://arxiv.org/abs/2605.06203) | 学习数据依赖坐标以跟踪演化结构、减少固定 Euler 坐标的错位和平滑偏好 | 非 PINN；通过可微采样表示同一信号，不执行 KC 的多物理 PDE pullback | **中家族碰撞** |
| [JacobiNet, 2025/2026](https://arxiv.org/abs/2508.02537) | 端到端可微坐标映射和 autograd Jacobian，用于不规则几何的 PINN | 几何域映射而非局部时间重参数化 | **中宽泛 / 低直接** |
| [SDD-PINN / moving-boundary drying, 2026](https://www.sciencedirect.com/science/article/pii/S2772508126000190) | 对 stiff moving-boundary 问题采用时间/状态变换 | 应用层接近，但不是相变速率驱动的空间局部时钟 | **中低** |
| [VLT-PINN, JCP 2024](https://www.sciencedirect.com/science/article/pii/S002199912400010X) | 通过变量线性变换改善薄层流 PINN；有 [MIT 代码](https://github.com/CAME-THU/VLT-PINN) | 线性尺度变换，不是内生局部时间坐标 | **低直接 / 中宽泛** |
| [RF-PINNs / reaction-progress representation, JCP 2025](https://www.sciencedirect.com/science/article/pii/S002199912400946X) | 使用反应进度变量组织高刚性反应流 | “进度变量”概念与相变时钟相近，但未发现其把 PCM 相态速率作为局部 PINN 时间坐标 | **中语义碰撞** |
| [Narayanaswamy material time, 1971](https://ceramics.onlinelibrary.wiley.com/doi/10.1111/j.1151-2916.1971.tb12186.x) | 玻璃结构松弛中的材料时间/非线性热历史概念 | 说明“材料时间”不是新概念；KC 的潜在新意只能是 PINN 表示和多物理实现 | **历史术语碰撞** |

### 4.2 可辩护的新颖性槽位

`SUPPORTED_INTERPRETATION`：KC-PINN 仍有一个合理的新颖性窗口，但应精确写成：

> 据截至 2026-08-18 的限定原始来源检索，尚未发现把局部相变动力学速率驱动的严格单调时间坐标，与保持原电—热—相态方程的完整空间—时间链式 PINN 残差结合，用于二维 VO₂ 器件移动相界面的公开工作。

这句话不把“坐标变换”“时间重参数化”“材料时间”本身据为己有，只声明其在一个具体物理—算法交集中的缺口。

### 4.3 现有 KC 公式必须修正

当前方案令解头显式读取脉冲：

$$
\xi=h_\theta(\mathbf{x},\tau(\mathbf{x},t),p(t)).
$$

于是物理时间导数为

$$
\partial_t\xi
=\xi_\tau\,\tau_t+\xi_p\cdot\dot p.
$$

若相态残差为零，$\partial_t\xi=K_\xi$；若时钟残差也为零，$\tau_t=\sqrt{K_\xi^2+k_{\rm floor}^2}$。因此一般只能推出

$$
\xi_\tau
=\frac{K_\xi-\xi_p\cdot\dot p}
{\sqrt{K_\xi^2+k_{\rm floor}^2}},
$$

而不能无条件推出当前卡片中的 $|\xi_\tau|<1$。

建议采用以下二选一修复，并在论文中只保留一种：

1. **推荐：改成沿实际脉冲路径的全导数。** 在脉冲光滑区间内，

   $$
   \frac{d\xi}{d\tau}
   =\frac{d\xi/dt}{d\tau/dt}
   =\frac{K_\xi}{\sqrt{K_\xi^2+k_{\rm floor}^2}},
   $$

   因而其绝对值小于 1。必须明确这是沿 $p(t)$ 的 path derivative，不是保持 $p$ 不变的偏导数。

2. **较窄：只在分段常值脉冲的开区间声明偏导性质。** 此时 $\dot p=0$；脉冲跳变作为一侧界面处理，不在跳变处求导。

该修复是进入实现前的硬条件；否则 KC 的主要机制解释与它自己的完整 pullback 不一致。

### 4.4 局部时钟可能转移而非消除刚性

对空间相关的 $\tau(\mathbf{x},t)$，任一场 $f(\mathbf{x},\tau)$ 的物理空间 Hessian 含

$$
D_{\mathbf{x}}^2f
=f_{\mathbf{x}\mathbf{x}}
+f_{\mathbf{x}\tau}\otimes\nabla\tau
+\nabla\tau\otimes f_{\tau\mathbf{x}}
+f_{\tau\tau}\nabla\tau\otimes\nabla\tau
+f_\tau D_{\mathbf{x}}^2\tau.
$$

因此降低时间方向斜率并不自动降低整体训练难度；它可能把难度转移到 $\nabla\tau$、$D^2\tau$ 和混合项。必须报告：

- 每一项的幅值分布和梯度范数；
- 原始时间与时钟坐标下的经验 NTK/梯度条件代理；
- 最坏物理残差，而不只看平均损失；
- 时钟正则是否把前沿过度平滑；
- 自动微分的峰值内存和墙钟时间。

若场误差改善但混合拉回项或物理残差恶化，不能解释为“representation stiffness 已解决”。

## 5. PHA-MF-PINN 的碰撞矩阵

PHA-MF 的核心是低/中/高频分支，由相变敏感性和 Joule 热点构成的 gate 控制高频容量，并用同一 gate 增加 collocation 密度。

| 近邻工作 | 与 PHA-MF 重叠 | 尚未覆盖的窄差异 | 碰撞风险 |
|---|---|---|---|
| [beignet / Fourier Feature Pyramids, 2026](https://arxiv.org/abs/2605.24278) | 可训练多分辨率 Fourier pyramid、可控 bandlimit、较高计算效率 | 不用 PCM 相态/Joule gate，也不联合控制采样 | **高表示侧碰撞** |
| [AW-PINN, 2026](https://arxiv.org/abs/2604.28180) | 根据残差和监督损失调整 wavelet 尺度/位置，把容量集中到局部高幅源 | 不是相变器件共享物理 gate | **高局部容量碰撞** |
| [AB-PINNs, 2025](https://arxiv.org/abs/2510.08924) | 全局低频网络 + 局部网络；窗口可移动/变形；高残差区增子域；有 [AGPL-3.0 代码](https://github.com/merlresearch/ab-pinns) | gate 来自残差/可学习窗口，不是统一 electro-phase stiffness 指标 | **高局部专家碰撞** |
| [PINN Balls, 2025](https://arxiv.org/abs/2510.21262) | 局部 mixture-of-experts、可学习域分解和自适应采样 | 不针对 PCM 物理共享 gate | **中高** |
| [Auto-Adaptive PINNs, 2025/2026](https://arxiv.org/abs/2510.23999) | 任意问题特定启发式可驱动采样；示范 Allen–Cahn 相界面 | 不同时路由频率容量 | **高采样侧碰撞** |
| [Causality-respecting RBAR for phase field, 2024](https://arxiv.org/abs/2410.20212) | 针对相场演化的因果与残差自适应 refinement | 不控制多频表示 | **中高** |
| [Causality-guided adaptive sampling, 2024](https://arxiv.org/abs/2409.01536) | 时间因果权重和自适应点分配 | 非 PCM-specific gate | **中** |
| [EEMS-PINN, 2025](https://arxiv.org/abs/2508.19561) | 以能量密度为 monitor function 的移动采样/mesh PDE，跟踪守恒系统的能量演化 | 只分配采样，不路由 PCM 高频容量；但直接占据“物理能量指标驱动点移动” | **中高采样碰撞** |
| [PINNs-MPF, 2024/2025](https://arxiv.org/abs/2407.02230) | 多相场、空间—时间分解和界面动力学 | 不含 Joule 热和共享频率 gate | **中应用碰撞** |
| [FM-tfPINN, 2026](https://arxiv.org/abs/2606.22191) | 耦合相场、界面感知 + 残差自适应 collocation，并把分数记忆引入表示 | 不是电热 PCM 或多频共享 gate，但进一步压缩“phase-field adaptive sampling”空间 | **中高应用碰撞** |
| [RA-PINN electrothermal systems, 2026](https://arxiv.org/abs/2603.23578) | 残差连接与 attention 解析局部电热耦合和陡峭梯度 | 稳态、无相态门控或高频采样；是电热架构强邻接基线 | **中应用碰撞** |
| [FF-PINN elasto-plasticity, 2026](https://arxiv.org/abs/2607.25150) | 在同一 PINN 中组合 Fourier features 与物理指标驱动的自适应采样 | 指标是应变而非相态/Joule，且不一定共享 gate 路由容量 | **高组合结构碰撞** |
| [NeuSA, 2025](https://arxiv.org/abs/2509.04966) | 谱/因果机制应对高频动力学 | 不做局部相—热点共享门控 | **中** |

### 5.1 PHA-MF 若作为主贡献必须满足的条件

`HYPOTHESIS`：PHA-MF 的可发表贡献不能是“用了 Fourier + adaptive sampling”，而必须是下列可证伪命题：

> 一个由模型预测和已知输入计算、无 oracle 泄漏的局部 electro-phase stiffness field，在同一位置同时分配频率表示预算和 collocation 预算时，比等预算的两个独立 gate、随机 gate、单一模块和通用 residual gate 更准确地解析 PCM 前沿和热点。

必做消融：

- shared gate；
- capacity-only；
- sampling-only；
- separate learned gates；
- phase-only；
- Joule-only；
- residual-only；
- 随机置换 gate；
- 全局统一高频容量；
- beignet/Fourier 基线；
- Auto-Adaptive/RBAR 基线；
- AB-PINN 或同等级局部专家基线。

只有 shared gate 在同参数、同点数和同更新预算下持续优于这些对照，才能支持“共同物理调度”而不是模块叠加。

### 5.2 采样目标与泄漏风险

如果 collocation 从非均匀分布 $q(z)$ 采样而直接平均 $|R(z)|^2$，优化的其实是 $q$ 加权残差，而不是原先的均匀物理域积分。应当二选一：

- 用重要性权重恢复预先声明的目标测度，并设置权重裁剪；或
- 明确承认优化的是加权物理目标，同时保留固定比例的均匀点并在独立均匀审计网格上评分。

此外：

- gate 只能来自当前模型预测、训练域固定常数和已知输入，不能读取测试 oracle；
- Joule gate 的 $q_{\rm ref}$ 必须由训练数据/物理尺度预先冻结，不能用每条测试轨迹的最大值归一化；
- 采样分支宜 stop-gradient，并限制更新频率，防止 gate—采样—残差正反馈；
- 始终保留均匀采样下限，防止成核前区域和非局部电势响应被饿死；
- $4\phi(1-\phi)$ 只在已有界面处发亮，可能漏掉成核前过热区，需以预声明的 susceptibility 或 superheat 指标补充，而不能事后调 gate。

## 6. 物理可执行性与开放 oracle 审查

### 6.1 VO₂：开放起点已出现，但适用域必须收窄

[Q-POP-IMT 论文](https://doi.org/10.1016/j.cpc.2025.109751)、[CPC 程序归档](https://doi.org/10.17632/p3395559s6.1) 与 [DOE-COMMS GitHub](https://github.com/DOE-COMMS/Q-POP-Modules) 提供了当前最有价值的开放起点：

- `VERIFIED`：仓库为 MIT 许可；公开 IMT 模块使用 FEniCS 2019.1 和 OpenMPI 3.1 或更旧版本；
- `VERIFIED`：当前实现包含一个结构序参量 $\eta$、一个电子序参量 $\psi$、电势、温度、电子和空穴密度；默认参数面向 VO₂；
- `VERIFIED`：公开示例支持串联电阻/电容，输出 $\eta,\psi,\phi,T,n,p$，并展示自振荡；README 报告示例在 16 个 AMD EPYC 7742 CPU 进程上约 2 小时；
- `SUPPORTED_INTERPRETATION`：它足以作为低场、热主导、二维 VO₂ 数值 oracle 的复现起点，但旧软件栈、无 release、低社区使用度意味着仍须做环境和数值复验。

这直接改善了 KC-PINN 的可行性，但并没有验证当前三场 $V,T,\xi$ 简化模型。Q-POP 是**结构/电子双序参量 + 载流子**模型；把它直接压缩成未定义的单一 $\xi$ 会改变物理合同。

### 6.2 高频 VO₂ 的机会与适用域负证据

[Nature Communications 2026 的 VO₂ 结构开关研究](https://www.nature.com/articles/s41467-026-69904-0) 直接成像了电驱动的成核、增长、并合和消解，报告约 5 nm/ns 的结构前沿速度，并指出高于 GHz 范围时结构恢复可能被材料本身抑制。这支持“高频脉冲下结构前沿/恢复是有真实物理意义的问题”，但也说明“频率越高越适合结构相态 PINN”并不成立。

[Huang et al. 2026](https://arxiv.org/abs/2604.19329) 进一步报告：高场短脉冲下，氧空位局域的 Poole–Frenkel 发射、热—弹耦合和域拓扑重构可能是关键机制，并预测亚 100 ps 动力学。公开 Q-POP-IMT 模块没有显示完整的氧空位/PF/力学位移闭合。因此：

- 可以研究低场或中等场、热主导、结构前沿和恢复；
- 不应把 Q-POP-grounded 结果外推为高场缺陷驱动拓扑；
- 不应以“通用 GHz VO₂ 开关”作为首篇主张；
- 高频实验论文可作为外部时间尺度与现象 benchmark，不能替代数值 oracle 的方程和参数一致性。

### 6.3 GST/GGST：模型成熟，开放器件 oracle 不成熟

[Miquel et al. 2024](https://arxiv.org/abs/2409.06463) 构建了 Ge-rich GST 的二维 wall-cell 多物理模型，把多相场和 phase-aware electrothermal solver 结合，并复现实验观察与校准曲线。它是很强的物理规格参考，但论文的代码/数据需向作者请求，且部分材料参数来自 in-house 数据或保密组成范围。类似地，[Cueto et al. 2023](https://doi.org/10.1016/j.sse.2022.108542) 的 GST225 相场—有限元电热研究并未提供可直接复用的完整开放器件 oracle。

通用开源框架如 [PRISMS-PF](https://github.com/prisms-center/phaseField)、MOOSE、OpenPhase 或 FEniCSx 能降低开发成本，却不等价于已校准、包含阈值导电、潜热、TBR、相态动力学和器件边界的 GST wall-cell oracle。

因此 PHA-MF-GST 的主要障碍不是神经网络实现，而是独立 oracle 的科学闭合与公开参数。若将来选择该路线，建议先用化学计量 GST225，而不是首篇就引入 Ge-rich GGST 的 Ge 扩散、析出、多相和晶粒取向复杂度。

### 6.4 物理路线对比

| 维度 | VO₂ + Q-POP + KC | GST225 wall + PHA-MF |
|---|---|---|
| 可下载器件级 oracle | **有起点**：Q-POP-IMT | **未找到完整公开版本** |
| 物理字段复杂度 | 高：$\eta,\psi,\phi,T,n,p$ | 中高：电热、相分数、潜热、阈值导电、TBR、随机成核/晶粒 |
| 方法碰撞 | 中 | 中高到高 |
| 第一篇最小范围 | 低场热主导 2D VO₂ 结构前沿 | 需先闭合/获得 GST225 oracle |
| 最大物理风险 | 高场缺陷/PF/弹性缺失；双序参量压缩 | 参数不可公开；oracle 自建成本 |
| 最短日历路径 | **较优** | 较慢 |

## 7. 推荐修订后的主 idea

### 7.1 暂定题名

**Q-POP-Grounded Structural Kinetics-Clock PINNs for Repeat-Pulsed, Thermally Dominated VO₂ Switching Fronts**

中文：**面向重复脉冲热主导 VO₂ 结构相前沿的 Q-POP 约束动力学时钟 PINN**。

### 7.2 物理与方法合同

1. 固定 Q-POP-IMT 的具体 commit、环境、输入参数、几何、网格、时间步误差阈值和边界/外电路设置；先复现作者示例和守恒/收敛诊断。
2. 首篇保留 Q-POP 的结构序参量 $\eta$ 与电子序参量 $\psi$；不要未经证据合并成单一 $\xi$。时钟首先绑定结构速率 $K_\eta$，主指标也聚焦结构前沿、延迟和恢复。
3. 使用解析正基函数累积确保 $\tau_t>0$；对所有受影响的时间和空间导数保留完整 pullback，不替换原电—热—相态 PDE。
4. 机制主张使用沿脉冲路径的 $d\eta/d\tau$，或严格限定在分段常值脉冲开区间；脉冲跳变单独作为界面处理。
5. 如果电子序参量 $\psi$ 的时间尺度成为独立主瓶颈，先触发预声明停止/分支门，再评估双时钟；不要在首版默认叠加双时钟。
6. 把 KC 解释为表示重参数化，不宣称它修正缺失物理。若 Q-POP 与目标高场现象失配，停止方法比较而不是让时钟拟合模型误差。

### 7.3 formal OOD 的可执行定义

当前模型没有几何/材料输入，因此不能把一个冻结检查点直接施用于未见器件并称为 zero-shot whole-device OOD。首篇应采用更诚实的定义：

> 架构、损失、超参数、预算和停止规则在开发集上锁定；随后对每个完整留出几何/脉冲案例独立重新训练求解器，只比较锁定算法在新案例上的稳定性、误差和成本。

这属于**算法级 post-lock solver robustness**，不是冻结网络的跨器件代理泛化。若未来要做零样本代理，必须显式输入几何、材料和边界/协议表示，并重新设计防泄漏实体拆分。

## 8. 最小判别性证据计划

本节是建议的实验合同，不构成执行授权。

### Gate A：oracle 可复现性

必须先满足：

- 复现 Q-POP 指定示例的主要场和电路曲线；
- 网格、时间步和 nonlinear solver 容差收敛；
- 电荷/能量或论文定义的守恒诊断在可接受范围；
- 固定 commit、环境和参数来源；
- 明确低场热主导的适用域。

失败即停止，不进入 PINN 训练。

### Gate B：瓶颈真实性

用等预算 raw-time PINN 证明问题确实出现：

- 结构界面被平滑；
- 开关延迟/恢复错误；
- 局部 Joule 热点或温度峰值错位；
- 稠密审计网格上的相态/热残差恶化。

若现代强基线已经稳定高精度解决，KC 缺乏必要性，应停止而不是扩大问题规模制造失败。

### Gate C：机制归因

最小强基线集合：

1. 原始时间、同参数/同预算 MLP-PINN；
2. 加宽原始时间 PINN；
3. 恒等时钟 $\tau=t$ 且关闭 clock loss；
4. 同架构的一般单调时钟，但不使用 $K_\eta$ 耦合；
5. 固定 log/analytic time warp；
6. CT/TAL 风格学习坐标基线；
7. beignet/Fourier 或同级多频基线；
8. Auto-Adaptive/RBAR 采样基线；
9. AB-PINN/FBPINN 或同级局部专家基线；
10. 因果/时间推进基线。

报告总参数量、活动参数量、collocation 数、更新数、峰值内存、墙钟上限和选模规则。不能只匹配 epoch。

### Gate D：机制诊断

除场误差外，至少报告：

- 开关时间和恢复时间误差；
- 结构相前沿 Hausdorff 距离与拓扑事件；
- 峰值温度、热点位置和总能量/能量闭合；
- 各耦合残差在独立均匀稠密点集上的分位数和最坏值；
- $\tau_t$、$\nabla\tau$、$D^2\tau$ 及所有混合 pullback 项；
- 时间高频和空间高波数误差谱，仅作为诊断而非额外真值泄漏 loss；
- 训练稳定性、随机种子差异和失败率。

### Gate E：锁定后的整案例评估

拆分单位必须是完整几何、完整脉冲协议和完整轨迹/时间窗，不能把同一轨迹的时空点随机拆到训练和测试。方法锁定后，对留出案例独立训练并评分；留出结果不得反向调节架构、$M_\tau$、权重或停止阈值。

### 建议的预声明停止条件

- Q-POP 环境或参考案例无法可重复复现；
- $\eta/\psi$ 双序参量不能与单时钟形成可解释合同；
- 完整 pullback 后，KC 不优于一般单调坐标或强 Fourier/自适应采样基线；
- 收益只来自更多活动参数、更多点或更多墙钟时间；
- 时间斜率减小但空间时钟导数导致残差/条件恶化；
- KC 只改善训练 loss，不改善独立稠密网格的物理误差和事件指标；
- 目标现象进入氧空位/PF/弹性主导域，而 oracle 未闭合这些物理。

可在正式计划中预先规定一个最小科学效应阈值，例如“多随机种子中位数关键前沿误差至少降低 20%，且最坏耦合残差不退化”；该数值需结合 raw baseline pilot 和数值误差底线后冻结，不能事后选择。

## 9. PHA-MF 的保留方式

建议把 PHA-MF 保留为两种角色，而不是与 KC 同时成为 headline：

1. **KC 的强对照**：检验“直接把容量和点放到界面/热点”是否已经足够。如果 PHA-MF 明显胜过 KC，说明主要瓶颈可能是采样/局部容量，而非时间表示。
2. **预声明备用路线**：若 KC 在 Gate C/D 失败，而 capacity-only 或 sampling-only 已显示大收益，再转入 shared-gate 研究；此时重新冻结独立的贡献、baseline 和停止条件。

PHA-MF 作为备用主线时，最小题名应突出 shared gate，而不是泛化的 multi-frequency：

> **Shared Electro-Phase Stiffness Gating for Joint Spectral-Capacity and Collocation Allocation in Phase-Change Device PINNs**

其成功条件是 shared gate 优于 separate gates；如果两者相当，所谓“同一物理场统一调度”没有获得证据，路线应降级为工程组合。

## 10. 开源资源清单与复用注意事项

| 资源 | 用途 | 当前开放状态 | 注意事项 |
|---|---|---|---|
| [Q-POP-Modules](https://github.com/DOE-COMMS/Q-POP-Modules) | VO₂/IMT 二维 phase-field oracle 起点 | MIT；116 commits；无 release（访问日状态） | legacy FEniCS/OpenMPI；需 pin commit 和容器化复现；不能把通用文档能力当作已实现模块能力 |
| [Q-POP CPC package](https://doi.org/10.17632/p3395559s6.1) | 论文配套程序归档 | DOI 归档 | 与 GitHub commit 做文件/版本比对 |
| [AB-PINNs](https://github.com/merlresearch/ab-pinns) | 局部专家与残差驱动域分解强基线 | AGPL-3.0-or-later | 直接复用会带来 copyleft 义务；可按论文独立实现算法对照并保留来源 |
| [PINNs-MPF](https://github.com/SFETNI/PINNs_MPF--a-Physics-Informed-Neural-Network-for-Multi-Phase-Field-problems) | 多相场 PINN 与 space-time decomposition 参考 | MIT | 不是电热 VO₂/GST 器件 oracle |
| [VLT-PINN](https://github.com/CAME-THU/VLT-PINN) | 变量变换基线 | MIT | 需核对论文 corrigendum 和具体基准 |
| [Auto-Adaptive PINNs](https://github.com/kevmbuck/Auto-Adaptive-PINNs) | 相变启发式自适应采样 | 公开；本次页面未确认许可证 | 许可证确认前只读参考，不复制代码 |
| [FBPINNs](https://github.com/benmoseley/FBPINNs) | 域分解/局部网络基线 | 需在采用前重新核验 commit 与许可证 | 与 AB-PINN 选一个最能覆盖瓶颈的强实现，避免基线无界扩张 |
| [PRISMS-PF](https://github.com/prisms-center/phaseField) | 通用相场求解框架 | 公开 | 不是已校准 PCM 器件模型；不能以框架存在代替 oracle 验证 |

公开仓库的 star、commit 或 license 只反映可访问性与法律边界，不证明数值正确性。所有外来代码在集成前仍需 pin commit、许可证归档、依赖审计和最小复现实验。

## 11. 论文写作边界

### 11.1 可以写

- `VERIFIED`：公开 Q-POP-IMT 实现提供 VO₂ 默认参数的结构/电子双序参量电热 phase-field 起点。
- `SUPPORTED_INTERPRETATION`：局域尖锐界面、热点、多尺度和多物理优化共同构成 PINN 欠分辨问题；spectral bias 只是其中一部分。
- `HYPOTHESIS`：kinetics-specific monotone time coordinate 可能改善同预算 PINN 对结构前沿和恢复的解析。
- `SUPPORTED_INTERPRETATION`：限定检索未发现与完整 KC 组件同构的工作，但存在多项坐标变换和时间重参数化近邻。

### 11.2 不能写

- “首次提出自适应坐标 PINN / 材料时间 PINN”；
- “解决了 PINN spectral bias”或“普适抗刚性”；
- “达到 GHz VO₂ 器件预测”而未闭合高场缺陷/PF/弹性机制；
- “比传统数值求解器更快”，除非在相同误差目标、包含训练与 oracle 成本的端到端预算下验证；
- “formal OOD 零样本跨器件”，除非模型显式参数化几何/材料且冻结检查点直接预测；
- “实验验证”，因为当前计划只有合成数值证据；
- “无同期工作”，只能写限定检索中的未发现。

## 12. 关键原始来源索引

### 坐标、时间重参数化与刚性

1. [CT-PINN, Journal of Computational Physics 538 (2025) 114161](https://www.sciencedirect.com/science/article/pii/S0021999125004449)
2. [TAL-PINN, arXiv:2511.04490](https://arxiv.org/abs/2511.04490)
3. [Neural ODEs for Model Order Reduction of Stiff Systems, arXiv:2408.06073](https://arxiv.org/abs/2408.06073)
4. [Trajectory-Optimized Time Reparameterization, arXiv:2603.16583](https://arxiv.org/abs/2603.16583)
5. [R-adaptive DeepONet, arXiv:2408.04157](https://arxiv.org/abs/2408.04157)
6. [SDD-PINN moving-boundary drying](https://www.sciencedirect.com/science/article/pii/S2772508126000190)
7. [Transformed PINN for convection-diffusion, arXiv:2409.07671](https://arxiv.org/abs/2409.07671)
8. [VLT-PINN, JCP 500 (2024) 112761](https://www.sciencedirect.com/science/article/pii/S002199912400010X)
9. [RF-PINNs / reaction-progress representation](https://www.sciencedirect.com/science/article/pii/S002199912400946X)
10. [Narayanaswamy material time](https://ceramics.onlinelibrary.wiley.com/doi/10.1111/j.1151-2916.1971.tb12186.x)

### 多频、局部容量、采样和相场 PINN

11. [Fourier Feature Pyramids / beignet, arXiv:2605.24278](https://arxiv.org/abs/2605.24278)
12. [AW-PINN, arXiv:2604.28180](https://arxiv.org/abs/2604.28180)
13. [AB-PINNs, arXiv:2510.08924](https://arxiv.org/abs/2510.08924)
14. [PINN Balls, arXiv:2510.21262](https://arxiv.org/abs/2510.21262)
15. [Auto-Adaptive PINNs with Applications to Phase Transitions, arXiv:2510.23999](https://arxiv.org/abs/2510.23999)
16. [Causality-respecting RBAR for phase-field equations, arXiv:2410.20212](https://arxiv.org/abs/2410.20212)
17. [Causality-guided adaptive sampling, arXiv:2409.01536](https://arxiv.org/abs/2409.01536)
18. [PINNs-MPF, arXiv:2407.02230](https://arxiv.org/abs/2407.02230)
19. [Fourier Feature PINN with strain-adaptive sampling, arXiv:2607.25150](https://arxiv.org/abs/2607.25150)
20. [NeuSA, arXiv:2509.04966](https://arxiv.org/abs/2509.04966)
21. [Meta-LRPINN, arXiv:2502.00897](https://arxiv.org/abs/2502.00897)
22. [Discontinuity-aware phase-field PINN, arXiv:2511.23102](https://arxiv.org/abs/2511.23102)
23. [Two-phase Stefan moving interface, arXiv:2512.14010](https://arxiv.org/abs/2512.14010)
24. [Moving-interface level-set PINN, arXiv:2502.02440](https://arxiv.org/abs/2502.02440)
25. [PAS-Net, arXiv:2511.14925](https://arxiv.org/abs/2511.14925)
26. [Adaptive Coordinate Transforms for Neural Operators, arXiv:2605.06203](https://arxiv.org/abs/2605.06203)
27. [JacobiNet, arXiv:2508.02537](https://arxiv.org/abs/2508.02537)
28. [EEMS-PINN, arXiv:2508.19561](https://arxiv.org/abs/2508.19561)
29. [Electrothermal RA-PINN, arXiv:2603.23578](https://arxiv.org/abs/2603.23578)
30. [FM-tfPINN coupled phase-field systems, arXiv:2606.22191](https://arxiv.org/abs/2606.22191)
31. [PirateNets, arXiv:2402.00326](https://arxiv.org/abs/2402.00326)
32. [Physics-informed hard constraints with mixture-of-experts, arXiv:2402.13412](https://arxiv.org/abs/2402.13412)

### VO₂、GST 与开放物理资源

33. [Q-POP-IMT, Computer Physics Communications (2025), DOI 10.1016/j.cpc.2025.109751](https://doi.org/10.1016/j.cpc.2025.109751)
34. [Q-POP-Modules GitHub](https://github.com/DOE-COMMS/Q-POP-Modules)
35. [Q-POP program archive, DOI 10.17632/p3395559s6.1](https://doi.org/10.17632/p3395559s6.1)
36. [Switching speed limits in electrically driven VO₂ structural Mott–Peierls transition, Nature Communications 2026](https://www.nature.com/articles/s41467-026-69904-0)
37. [Electrically steered conduction topologies and period-doubling phase dynamics in VO₂, arXiv:2604.19329](https://arxiv.org/abs/2604.19329)
38. [Current-driven VO₂ phase-field model, arXiv:1809.05549](https://arxiv.org/abs/1809.05549)
39. [Miquel et al., Ge-rich GST multiphysics wall-cell model, arXiv:2409.06463](https://arxiv.org/abs/2409.06463)
40. [Cueto et al., GST225 phase-field/electrothermal model](https://doi.org/10.1016/j.sse.2022.108542)
41. [GST-GAP-22 data and potentials](https://doi.org/10.5281/zenodo.8208202)
42. [Large-scale GST225 crystallization data/model, DOI 10.1038/s41524-024-01217-6](https://doi.org/10.1038/s41524-024-01217-6)
43. [Classic 2D electrothermal PCM model, arXiv:1810.07764](https://arxiv.org/abs/1810.07764)

## 13. 最终处置

`SUPPORTED_INTERPRETATION`：**保留 KC-PINN，但重命名并缩域为 Q-POP-grounded structural kinetics-clock；修复 path-derivative 公式和 OOD 语义后再进入正式实施计划。**

`SUPPORTED_INTERPRETATION`：**PHA-MF 不删除，但降为强基线/预声明备用路线。** 如果 KC 失败且 PHA 的 shared gate 通过严格归因消融，再把它提升为主线。

`UNKNOWN`：当前没有任何训练或物理复现实证，因此还不能称该 idea “可行已证实”。能确认的是：它现在有一个真实、公开、可着手复现的 VO₂ oracle 起点；没有发现完全同构同期工作；同时已有清晰的近邻、公式修订、适用域、强基线和停止条件。下一步最有信息量的动作不是继续扩展文献数量，而是先做 Q-POP 的环境复现与数值合同冻结，再以最小 raw-time baseline 判断瓶颈是否真实存在。
