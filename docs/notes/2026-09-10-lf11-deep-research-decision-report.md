# PINN×PCM 独立深度调研决策报告

日期：2026-09-10

承接：PCM-20260910-LF10-RESEARCH-REVIEW-01

状态：PROPOSED_NOT_AUTHORIZED；仅调研、推导与设计
本轮直接核实的 GitHub main：918985c88f98321c96e6952c9bdd725bd958ed0e

## 0. 决策摘要与证据身份

首选仍是稀疏等观测重建，但升级为“观测锚定、边界公平、初始标度校准的物理度量归因试验”。首轮不是直接宣布新算法，而是用最少的匹配变化证明：内部 PDE 是否有独立增量；同目标的 proposal 改变是否有增量；空间时间 phase 残差度量是否比单纯增加采样或整体加大 phase loss 更有用。

对上版四臂作两项必要修订：

1. 主要非 PDE 对照改为 D_B：保留相同的观测目标、硬输出约束、软 BC/IC；只移除内部 PDE。否则原 D→P-U 同时改变 PDE、BC 和 IC，不能单独归因内部物理。
2. P-M 的 phase 目标在共同起点用一次参考盲校准乘常数 c0，与均匀 phase 目标匹配初始数值。若它显示增益，再以固定全局 phase 权重 P-S 作条件归因控制。初始损失匹配不等于梯度、Adam 更新或后续损失平衡完全匹配。

保留完整潜变量 phase residual 为唯一条件备选。电功率敏感度、非自主相态能量关系和局部线性化优先作为解释性分析。不能把状态敏感度直接乘 PDE 残差就称为 DWR；不能对外驱动模型强加自主 Allen–Cahn 的能量单调衰减。

本轮 GitHub main 没有 LF10 之后的新提交或新结果。该结论只覆盖已访问的 main，不覆盖未推送的 Windows 工作区或未检查的其他分支。LF10 及之前的数字是已保存终局证据，不是本轮重算。没有加载实际科研 checkpoint、执行 optimizer step、求解 PDE、访问 stress 或写入云端仓库。[G1–G3]

证据等级：VERIFIED=直接读到的源码/原文/终局记录，或注明前提的代数推导；SUPPORTED_INTERPRETATION=由这些证据支持但非唯一的解释；HYPOTHESIS=候选机制/方法收益；UNKNOWN=未验证的精度、稳健性、泛化、材料关联或优先权。

指定 deep-research-work 插件的可调用入口未被本轮工具发现；研究通过可用网络检索、原始论文文本与 GitHub 连接器完成。不存在对未使用插件、未访问全文或未执行实验的完成声明。

## 1. 当前研究成果与论文缺口

现有最强证据是 LF4/LF10 的匹配界面监督暴露增量，以及 LF6/LF10 的物理优化后事件遗忘。三个 sampling streams 17/23/29 不是三个独立初始化；375 个 role-grid 比较不是375个独立实验，也不是全指标优势。LF10 CTRL/PROJ 都只有25个合法安全更新，不能解释成不存在任何安全步；full/control 未达先决条件而未运行。[G2–G3]

LF6 的关键轨迹：phase 参数冻结的前550步，V/T已经漂移；phase解冻后事件迅速退化。冻结 phase 参数并不切断 phase residual 对 T 的梯度。因此现有证据排除了“全部失败由 phase 参数更新造成”，但没有确认某个唯一根因。[G3–G4]

现稿可以承载有界诊断研究。正面方法主张还缺：

- 在相同可见观测下，内部 PDE 相对强数据/插值方法有独立价值；
- 新增模块相对最近强 PINN 不是整体权重、预算或表示坐标带来的伪增量；
- 场/事件改善确实改善终端电流、功率、能量或事件时刻，其他关键量不被牺牲；
- 独立初始化、观测规则、完整案例和无事件对照支持其适用域；
- 材料、几何、本构与数值参考的身份支撑标题，不把合成 wall-cell 改名为实验氧化物器件。

旧初稿不删除，也不自动取代新正面探索目标。所有新的阳性仍须先获得匹配证据。

## 2. 最近邻方法审查

### 2.1 文献与实质差异

| 原始工作 | 本轮核查的实质内容 | 本项目可能的区别及所需证据 |
|---|---|---|
| Nabian–Gladstone–Meidani 2021 importance sampling [R1] | Eq.(10)–(17)和Algorithm 2显式使用 f/q 权重；用损失/分片常数近似 proposal，服务于更有效估计原目标。 | P-I属于此谱系。观察支持的界面 proposal 是适配，不是重要性采样本身的原创；须证明同目标、同计算下的增量。 |
| Wu等 RAD/RAR-D 2023 [R2] | 官方 Allen–Cahn RAD 示例按 residual^k 分布更换点，没有 rho/q 损失校正；RAR-D是增加而非整体替换点。 | 原始 RAD 是必须面对的强比较，不能改成无偏 IS 后仍叫完全复现。需分开“同目标归因”与“原方法最强表现”轨道。 |
| PF-PINNs 2025 / PF-GAR [R3] | 归一化、随机batch NTK加权、动态采样；官方 GAR 遍历预测 phase 对全部 geotime 坐标的梯度，包括时间。 | 它不需要 dense 事件真值。稀疏 teacher-supported proposal 的潜在区别是初始自预测漏检时的可见观测支撑，不是声称对手使用更多标签。 |
| Sharp-PINNs 2025 [R4] | Eq.(17)(18)交替AC与CH残差，BC/IC两阶段保留；搭配Fourier、modified MLP、hard constraints。 | 当前方程为V/T/非守恒phase，不是腐蚀AC/CH。此前LF9参数头路由失败不等于该交错算法被否定；来源适配必须写清。 |
| Buck–Kim Auto-Adaptive PINNs [R5] | v4 Eq.(13)–(17)明确用正的启发式密度改变加权残差目标，等权样本隐式实现；自主AC中利用能量与误差放大线索。 | P-M最接近该类工作。“界面加权”不是空白。当前外驱电热phase的能量结构、跨头耦合与有限观测边界可形成适配问题，但必须证明其必要性。 |
| De Ryck等 ICLR2024 [R6] | 在明确的线性化/算子条件下研究PINN训练与算子条件数，讨论预条件化。 | 不证明任意logit残差能降低本系统条件数；A首先是状态依赖非线性残差度量，不能未经验证冠以“可证明优良预条件器”。 |
| Liu等 PC-PINNs 2024 [R7] | 离散算子及近似逆/ILU型预条件处理，非线性/时间情形另有构造。 | 与 r_phi/s 是不同机制；若引入离散逆，需接受新的离散接口和成本，不冒称仍是完全相同的AD强式方法。 |
| Govoeyi–Richter 2026 DWR [R8] | Poisson/Laplace的PINN/Deep Ritz；利用伴随与局部化估计器。Eq.(4.9)(4.10)改采样而无逆概率权重；文中明确估计器非严格上界。 | 不能把它描述成保持uniform目标的IS；也不能把本项目瞬时状态敏感度当作完整多物理DWR。借用需要完整残差到功能量的伴随映射。 |
| causal PINNs / pseudo-time [R9–R10] | 时间权重/推进和经验残差伪解问题的不同解决路径。 | 四窗分层不是causal；固定配置点的伪解定理也不直接解释全部重采样轨迹。FP64已是当前底座，不需为“强基线”再引入FP32主比较。 |

Auto-Adaptive已于2026-05-07正式发表在NMTMA 19(2),510–534，DOI 10.4208/nmtma.OA-2026-0014；不能继续仅以“未发表的新预印本”评价竞争关系。[R5]

2026年的Feynman–Kac监督预条件化工作也说明，加入数据保真项改善训练条件并不是天然新颖性。其问题和假设与本模型不同，不能把其理论直接移植为“稀疏anchor保证有效”。[R11]

### 2.2 可争取的贡献与不可争取的口号

不再作为独立创新：标准data+PDE、logit监督本身、普通Fourier、正背景的界面采样、同目标IS、一般残差加权、常见hard BC、泛化的“低残差不等于正确解”。

可以争取但尚为HYPOTHESIS：

1. 对外驱电热相变，在相同可见观测和共同训练目标底座上，明确分离 proposal、空间残差度量和全局phase压力，并找到超过强基线的必要接口。
2. 证明误差关键区不只等于已出现的phi=.5界面，还受温度驱动的局部误差放大及上游电热状态控制。
3. 将经验证的局部机制连接到电流/能量，而不把状态敏感度误写为残差误差估计。

四臂设计本身是识别工具，不自动是算法创新。若只剩标准PINN在稀疏数据下优于插值，尚不足以证明新增算法/架构主贡献。

## 3. 一项新的物理边界：外驱phase不是自主能量衰减问题

源码本构为：

\[
\sigma(T,\phi)=\exp[\beta T+\log R\,h(\phi)],\quad h(\phi)=\phi^2(3-2\phi),
\]
\[
r_\phi=\phi_t-M(T)[\epsilon^2\Delta\phi-F_\phi(T,\phi)],
\]
\[
F_\phi=2B\phi(1-\phi)(1-2\phi)+6D(T_c-T)\phi(1-\phi).
\]

这些来自当前源码[G4]。以下是本轮分析推导，不是已测得的轨迹机制。

取一个与该相态导数相符的势函数：
\[
F(T,\phi)=B\phi^2(1-\phi)^2+D(T_c-T)h(\phi).
\]
令
\[
\mathcal E_\phi=\int_\Omega\left[\frac{\epsilon^2}{2}|\nabla\phi|^2+F(T,\phi)\right]dx.
\]
在足够光滑、M(T)>0、无相态法向通量、相态PDE精确满足时：
\[
\boxed{\frac{d\mathcal E_\phi}{dt}=-\int_\Omega\frac{\phi_t^2}{M(T)}dx-D\int_\Omega h(\phi)T_tdx.}
\]

第二项没有固定符号。该选定相态势能不必单调下降，其密度也不必非负。它不是已标定的整个器件热力学自由能；相态势中热倾斜系数D与热方程latent系数之间也没有由当前材料标定保证的热力学关系。

因此不能不加说明移植自主AC能量衰减loss，也不能直接把可能为负的完整密度作为概率。正背景或平移可定义一个启发式，但不能恢复不存在的能量定理。

在相态残差不为零时，还应保留对应残差功项；不能先假设PDE成立，再用缺失项的“能量定律”证明PINN成立。

相态局部线性化为：
\[
\delta\phi_t=M\epsilon^2\Delta\delta\phi-MF_{\phi\phi}\delta\phi+
\big[M'(T)K+6DM\phi(1-\phi)\big]\delta T,
\quad K=\epsilon^2\Delta\phi-F_\phi.
\]
\[
F_{\phi\phi}=2B(1-6\phi+6\phi^2)+6D(T_c-T)(1-2\phi).
\]

若B,D>0，在phi接近0时，局部反应线性项可在T>Tc+B/(3D)时表现为放大。此条件不是完整耦合PDE不稳定性的充分判据，扩散、边界和电热反馈不能被省略。它指出一个值得验证的候选：已观测straddling界面可能遗漏“高温、近纯相、尚未跨阈值”的启动区域。

建议只在共同起点/固定终点记录[-M F_phiphi]_+、M'K+6DMs与事件/温度误差的关系。当前不为它自动增加训练臂；若所有有效场都没有显示相关现象，该机制应降级。

## 4. 竞争解释与最小判别

| 假设 | 当前证据与反证 | 最小有区分力动作 | 如何改变后续行动 |
|---|---|---|---|
| 撤除观测anchor导致遗忘 | LF6无anchor且遗忘；旧LF1有replay也无完整优势，所以anchor不是充分条件。 | 新任务统一保留anchor；只有要主张anchor的因果贡献才加同任务anchor-off。 | 不能用旧dense与新 sparse差异归因anchor。 |
| phase残差度量压低关键动力学 | r_phi=s r_psi成立，但Adam可能补偿原始范数。 | 真实共同起点上的残差×参数头梯度及实际预条件方向分解。 | 相态相关更新证据成立才允许A备选。 |
| V/T漂移主导 | phase冻结时V/T已漂移；phase residual仍对T反传。 | 区分electric/thermal/phase/BC对T和V的方向贡献。 | 来自phase→T时A仍可能相关；来自电极/热项时不能硬推A。 |
| 离散参考与强式差异 | 旧Oracle No-Go；局部相态兼容不等于全系统连续体验证。 | 只补与本轮结论有关的算子、边界和读出差异，不重做全库。 | 明显不一致时暂停连续物理优胜主张，而非强行调权重追参考。 |
| 界面支持/测度不足 | LF4监督界面正证据，不是PDE proposal有效的证明。 | P-U/P-I/P-M的匹配比较。 | 分别定位采样或度量；无增量不宣称相应机制。 |
| 时间传播/表示结构问题 | 仍未知；现网络曾表达局部事件，不支持绝对容量不足。 | 只有主线显示稳定的早窗/边界局部剩余误差才形成新结构计划。 | 不自动增加causal、专家或焓。 |

诊断细节：令j遍历观测、电、热、相态、BC、IC，h遍历V/T/phase参数头，计算g_(j,h)=grad_(theta_h)L_j。记录范数不足以归因，需报告对观测误差/功能量的一阶方向影响。

Adam二阶矩取决于总梯度。不能把每个loss独立“过一次Adam”再相加，声称是实际更新分解。若checkpoint真有moments，应先用总梯度构造实际下一步分母，再在这个共同分母下拆分当前各项和历史动量。若没有moments，只能报告参考盲的新fresh-Adam局部提议，不重建不存在的历史状态。全局clipping也使用实际共同裁剪系数。

共同起点上的观测梯度可能接近零；这不意味着anchor没有曲率约束作用。局部方向诊断可剪枝，但不能单独证明长期训练因果。建议仅在共同起点和固定终点做，避免每步高成本Jacobian审计。

## 5. 首选主线：修订四臂，避免两个归因混杂

### 5.1 D_B替代主要D控制

原D只含Lobs，P-U还新增BC/IC，所以原差分识别的是physics package，不是内部PDE。

建议首轮主要对照D_B保留相同的软BC/IC与硬输出表示，不含内部PDE；称“边界/初值约束数据网络”，不称内部物理PINN，也不再称完全data-only。纯数据warm-start固定端点可以展示，但其更新预算不同，不充当1200分支的等预算终点。

### 5.2 统一符号和目标

rho为预声明的归一化均匀时空目标；Bcal为只由可见稀疏角点跨phi=.5构造的时空单元并集。每窗按相交体积处理，pB=rho(Bcal)。
\[
q=(1-\alpha)\rho+\alpha\rho(\cdot\mid\mathcal B),\quad\alpha=0.25,
\quad a=\frac q\rho=0.75+0.25\frac{1_\mathcal B}{p_B},\quad w=\frac1a.
\]

q在本轮由可见观测冻结，不在线依赖参数theta。空窗回退uniform；整窗B也等同uniform。B为空不证明真实场无事件，不移动mask补点。

ell_e、ell_T、ell_phi表示原规范尺度下的残差平方。公共的1/3因子在全部臂保留，以下省略：
\[
J_U=E_\rho(\ell_e+\ell_T+\ell_\phi),
\]
\[
J_I=E_q[w\ell_e+w\ell_T+w\ell_\phi],
\]
\[
\boxed{J_M=E_q[w\ell_e+w\ell_T+c_0\ell_\phi].}
\]

共同warm-start为theta0，c0仅在预声明参考盲积分规则上计算一次：
\[
c_0=\frac{E_\rho[\ell_\phi(\theta_0)]}{E_q[\ell_\phi(\theta_0)]}.
\]
实际实现使用固定积分估计量，所以“匹配”指同一校准积分规则上的匹配。近零分母、非有限值或无法可靠识别的比例必须报告，不通过动态clip或按结果调c0挽救。

设a0为共同起点Lobs，b0为同一起点uniform物理总目标（含BC/IC）。定义公共项：
\[
C_k=\frac{L_{obs}}{\max(a_0,10^{-12})}
+\lambda_k\frac{5L_{BC}+L_{IC}}{\max(b_0,10^{-12})}.
\]
\[
L_{D_B}=C_k,\qquad L_{P-a}=C_k+\lambda_k\frac{J_a}{\max(b_0,10^{-12})},
\quad a\in\{U,I,M\}.
\]
\[
\lambda_k=0.1\min(k/200,1).
\]

各臂不能使用自己的J_a0重新归一化。那会把不同的PDE/anchor相对压力混入proposal/metric比较。

### 5.3 四臂实际能识别什么

D_B→P-U：同边界/初值底座上，内部PDE的增量。
P-U→P-I：相同期望目标、相同点数但不同proposal下的有限预算训练差异，不保证方差更小或Adam平均方向完全相同。
P-I→P-M：相同proposal、同起点和初始phase损失数值校准后的空间时间度量差异；尚不能排除后续整体phase更新强度不同。

若P-M有增量，条件控制P-S用同一proposal、uniform phase目标乘固定kappa0。建议在参考盲theta0将其全参数phase梯度范数匹配到P-M；常数冻结，不每步自适应：
\[
\kappa_0=\frac{\|\nabla_\vartheta(c_0E_q\ell_\phi)\|_2}{\|\nabla_\vartheta E_\rho\ell_\phi\|_2}.
\]

这是一个特定、预声明的全局加权反事实，不足以排除所有可能的标量调度。若P-S复现P-M全部主要收益，就不能称为已证明的界面空间特异性。

连续积分下正权重不改变零残差集合，但有限点、有限网络与有限训练仍允许伪解。P-I无偏的是损失/梯度估计，不是Adam轨迹或最终精度。固定配额分层采样也不能直接套独立混合抽样的简单方差判据。

## 6. 场—事件—器件：可保留的数学链与不能越过的界限

### 6.1 阈值区域误差

同一归一化测度mu下，A={phi>=c}、Ahat={phihat>=c}、e=phihat-phi：
\[
\mu(A\triangle\widehat A)\le\mu(|\phi-c|\le\delta)+\frac{\|e\|_{L^2(\mu)}^2}{\delta^2},\quad\delta>0.
\]

这是直接的集合分解与平方误差界，离散非负权重也成立，不是原创定理。正式S是全域时空measure，不能直接以ROI Ephi替换；该式也不控制连通性、Hausdorff或导电瓶颈。

用途：解释为什么全域误差下降仍可能错过稀有事件，并检查误差是否聚集阈值带。不把它直接变成新loss；若变成loss，threshold BCE/界面监督等现有近邻必须比较。

### 6.2 事件时刻稳定性

若活跃率a(t)有唯一、局部单调且横截的穿越，邻域内a'(t)>=m>0，预测sup误差<=epsilon，且没有更早的假穿越和括区失败，则可得到局部|Delta t|<=epsilon/m。

离散active count是阶梯函数；必须在当前保存时刻与既定插值定义下解释斜率，不能随意把它当光滑连续函数。切向接触、平台、重复穿越或观测未解析时刻都会使简单界失效。此分析解释难度，不用于事后放宽0.005门。

### 6.3 电功率敏感度

固定几何、正且有界的sigma(T,phi)、两电极固定Dirichlet电压U与0、其余边界绝缘、电方程精确满足时：
\[
P=\int\sigma|\nabla V|^2 dx,
\]
\[
\boxed{\delta P=\int Q_J[\beta\,\delta T+6\log(R)\phi(1-\phi)\delta\phi]dx.}
\]

一般近似V还包含：
\[
2\int_{\partial\Omega}\delta V\sigma\partial_nV\,dS-2\int_\Omega\delta V r_e\,dx.
\]

这是固定时刻约化电问题的状态敏感度，不是对完整脉冲控制的动态总导数，不是phase residual到功率误差的伴随。电流I=P/U仅在上述精确条件和U非零时成立；评价器必须独立计算电极电流和体Joule功率，不能用P/U补出电流来隐藏不守恒。

Wphi=6|logR|QJ phi(1-phi)、WT=|beta|QJ有解释价值，但它们未乘未知真实状态误差，并忽略动态误差传播与符号抵消，不能称误差估计器。Wphi还可能忽略尚未跨阈值却会放大的高温近纯相启动区。

需要真正的residual→QoI映射时，应解耦合线性化伴随F'(u)^*z=Q'(u)，包括IC/BC贡献、非线性余项、近似伴随误差。Govoeyi–Richter本身也未给当前系统的严格上界。[R8]

因此功率敏感度本轮仅建议做固定终点解释；不直接加入Wphi*r_phi²主loss。若后续要成为模块，需另做局部扰动/约化电问题的敏感度验证，并比较普通interface、Joule与其组合，不能同时改采样、权重和网络。

## 7. 唯一条件备选与暂缓模块

完整潜变量：
\[
\psi=\operatorname{logit}\phi_0+8[1-e^{-(t-t_0)/0.35}]h_\vartheta,
\quad s=\phi(1-\phi),
\]
\[
r_\psi=\psi_t-M(T)\{\epsilon^2[\Delta\psi+(1-2\phi)|\nabla\psi|^2]-2B(1-2\phi)-6D(T_c-T)\},
\quad r_\phi=s r_\psi.
\]

关系限于有限psi、0<phi<1，M位于括号外；不改为div(M grad phi)。解析构造完整psi，不从饱和sigmoid输出反求，不直接除以极小s。全可微inverse-Jacobian权重和r_psi²为同一目标，不分算创新；stop-gradient版本不同。

在近纯相的局部反应近似下，phi_t≈lambda(T)phi而psi_t≈lambda(T)，这提供“相对启动速率”解释；仍未证明实际训练增量、condition number改善或当前失败因果。噪声和无关纯相尾部也可能被放大。

触发条件：主线结果有phase/事件困难，且实际残差×头方向证据支持phase度量；或T虽先漂移但破坏方向主要来自phase方程。若主要来自electric/thermal/BC或参考语义，A不启动。

获批后仅原phase residual／固定全局phase权重／完整latent residual三臂，共同sparse anchor与起点，每臂建议1200固定更新（总3600，不含需要新建起点的成本）。初始标度同样必须校准。回顾性的零更新诊断可读取合法DEV-R、LF8prefix，不使用无效LF7端点；这些dense诊断必须与新训练输入隔离。三个科学训练臂必须使用新稀疏任务的冻结共同起点，不能以dense DEV-R/LF8初始化稀疏实验。旧checkpoint在Windows本地的实际moments本轮未核查。

暂缓：双电极完整hard lift需要边界瓶颈证据；焓/通量需要完整IC/BC和读出改造；causal/time-slab需要时间传播证据；局部专家需要表示局部性/预算证据；参数化网络与反问题需要完整案例/历史/可辨识性。它们不是本轮自动备用队列。

## 8. 公平比较、正式指标与信息边界

### 8.1 基线分工

B-L、B-P、B-logit共享相同可见观测。B-logit插值初态精确的完整logit增量，避免把变量坐标优势错误算给PINN。边界延拓、PCHIP端点和clip规则在结果前冻结。D_B是隔离内部PDE的强控制；纯data-only端点如另跑需单独预算。

RAD/RAR-D、PF-GAR及适用的强耦合训练属于最强方法轨道。保留其原始采样/权重/重采样语义，统计候选池、权重更新和导数开销；若适配为IS，则另名RAD-IS，不称原始复现。当前模型不是AC/CH，移植须称方法适配。

native solver知道完整物理，原则上不需要内部观测；它必须作为同物理数值比较存在。dense LF_ONLY是更多观测参考，不写入同信息胜率。不能将多次坐标查询当作solver每次都重跑整场，也不能声称无已测证据的数据效率或加速。

### 8.2 共同器件读出与物理审计

每个方法必须从自身V/T/phi与已知本构计算I和Joule功率，不复制teacher保存trace。基于已知离散算子和制造解，在正式结果前固定共同face-flux/edge-dissipation读出；神经AD读出作为并列敏感性，不选择对proposed有利者。

电极电流与体Joule功率独立生成，报告其与输入功率的缺陷。共同读出保留独立角色标签，不追溯替换旧结果；正式evaluator的指标公式不改。

piecewise-linear/PCHIP插值并不适合直接用NN同款AD二阶强残差作公平物理评分：分片接缝可能被a.e.导数遗漏。所有方法的共同物理比较使用合适离散/弱式审计；NN间另报相同固定AD强式J。

### 8.3 指标尺度

正式S：time_averaged_phase_region_symmetric_difference；不是375-grid辅助predicate。
Ephi：raw phase ROI RMS。
ET：temperature ROI NRMSE by0.45。
EI：terminal current trace NRMSE。
另报EV、逐周期recall/precision/mass/timing/recovery、能量与成本。

源码显示旧V2.1 phase floor为RMS/0.5口径，故对应raw Ephi的历史尺度应为0.0022958271323946142；US=0.000145，UT=0.0017839022220207273已按0.45归一化，UI依赖当时参考电流分母。[G5]

这些只是旧网格/时间步/交叉求解差异，不是continuous不确定度、噪声或统计置信界。新计划中建议主效应用预声明相对改善与数值可分辨性判据；旧U只作敏感性/解释尺度，不直接用max(5%,旧U)允许本来很准的器件量大幅恶化。旧实验冻结门不追溯修改。

层次必须分开：合法性→匹配算法效应→严格器件合取门→确认。合法但漏事件的baseline是科学负例，不是无效；数值/信息适配器错误则不能算PINN赢。无事件case不强制双周期recall或phase_max>=.9；用假事件、活跃量和绝对current误差，零参考RMS不滥用NRMSE。

## 9. 分阶段可执行方案（均待批准）

### S0：一次聚焦的输入与公式冻结

具名训练数据：outputs/runs/20260828T-phk-v21-s1-q-04-nominal-medium/result-intent-04.npz。
各轴0,4,8,…加末点、去重；实际数量从允许的文件头和mask统计，不假装已读raw。t=0解析IC单独计数。

训练包仅含选中V/T/phi、坐标、known IC/BC/params。无旧dense权重、14类partition、rank/interface/audit池、全场统计、导数、fine/extra/evaluator/stress或teacher电流/功率。

观测损失：V/T稀疏空间对偶体积×时间梯形测度；phase完整logit增量一半global、一半可见straddling端点测度，重复顶点合并。数据采样带来的非均匀性不能无校正用于V/T。

检查仅四项：信息导出边界；measure/proposal估计；完整新loss反传；基线延拓/读出。数学或工程检查不算新方法结果。校准分母与比值不可辨时标注，不能暗调初始权重。

### S1：固定起点四臂筛选

三头64×4 modified-MLP、FP64、重新seed17；沿用合法表示。共同data-only warm-start1200，Adam lr1e-3。D_B/P-U/P-I/P-M各freshAdam lr1e-4，各1200固定更新；共6000。betas、epsilon、clipping共同冻结。

data1024，interior512，BC128，IC128。四窗按原波形划分并同时分层（72/184/72/184），按窗时长权重.14/.36/.14/.36计算，不叫causal training。PINN全程保留anchor，三头联合，不引入旧550phase-freeze、filter、projection或新架构。

只在共同起点、固定中期报告点和终点记录必要分解；不按报告值调参或选checkpoint。若全部窗q=rho，省略P-I/P-M，D_B/P-U完成，合计3600。

GPU时间上限必须由获批后的目标机器profile给出，不能从更新数、旧V100价格或旧shutdown记录推算。因预算停止但未到固定终点，记BUDGET_INCOMPLETE，不取最佳中途结果。

### S2：条件归因与最近强基线

若P-M出现有界增量，先运行预声明P-S，建议1200同起点更新；该额外预算须纳入后续批准，不默认包含在6000中。若P-S解释全部收益，否定已证明的空间特异性主张。

若P-I优于P-U，优先做实际墙钟与原始RAD/PF-GAR比较，而非增加新metric。若仅P-U有效，保留内部物理价值，不强写新采样创新。

若要声称anchor抑制遗忘，加同任务anchor-off；若不做，就将anchor写为标准底座。若要声称两模块协同，做2×2并预声明交互尺度；完整方法最好不等于超加性。

强方法轨道至少保留一个residual-adaptive和一个预测phase-gradient近邻；针对metric主张再选AA式明确适配。不要为了数量运行所有文献全组合。

### S3：器件后果和有限确认

I(t)、积分功率/能量、双周期时刻必须与场指标一起报告。Wphi/WT先在固定终点作解释，不自动新增敏感度加权臂。

初始化：至少3个独立模型seed；按完整训练重复报告配对效应，不把采样流当新模型。
观测：第二预声明密度；一个同密度平移mask，保持数量/边界规则可比并在看场值前固定。
实体：至少2个新协议+2个新几何完整case，并加入合适的无事件对照。物理reference资格和新split在看方法结果前明确。
每case用自己的sparse support重训称held-out-case reconstruction/adaptation，不称zero-shot。
只用3seeds时报告个体效应、范围和失败；不靠时空点或25阈值网格制造大样本显著性。较大统计主张需相称样本设计。

### S4：论文同步收口

S1产生第一张正式表/图后就写问题、方法与信息边界；S2决定核心claim；S3填入器件与确认结果。保留paper_v23终局快照，不按LF0→LF10逐轮扩写摘要。

## 10. Go/No-Go与首张关键图

推荐预声明效应目标为相对强同信息比较者，正式S/Ephi至少10%改善，其他电热/器件指标最多5%恶化；这些是待批准的实用效应建议，不是已验证物理标准。近零分母用预先给出的绝对精度尺度，不以结果后挑选历史U替代。严格双周期器件合取门单独保持原语义，包括逐周期absolute timing0.005而非period-normalized RMS。

首轮允许结局：INVALID；BUDGET_INCOMPLETE；NO_INCREMENT_WITHIN_SCREEN_BUDGET；PDE_INCREMENT_ONLY；SAME_TARGET_SAMPLING_INCREMENT；SCALE_CALIBRATED_METRIC_SIGNAL_PENDING_SCALAR_CONTROL；NOT_TESTABLE。首轮信号不是paper-ready candidate。所有臂固定终点本地评估前完成获批云任务回收/关闭；stress不自动解封。

首张关键图不是loss曲线，而是同一张配对比较板：

- D_B/P-U/P-I/P-M相对共同起点及强插值的S、Ephi、ET、EI变化；
- 两周期recall/timing及事件存在性，不隐藏不通过者；
- 小图展示相同P-I/P-M proposal、初始phase损失/梯度标度及实际计算成本。

这张图首先区分PDE价值、proposal价值和metric线索。实际制作可采用独立子图文件再排版，不预生成虚构曲线。

## 11. 机制—论文映射

| 机制假设 | 方法设计 | 必需匹配增量 | 器件后果 | 确认 | 允许的论文主张 |
|---|---|---|---|---|---|
| 内部PDE补充未观测约束 | 相同anchor/BC/IC下加入PDE | D_B→P-U | I/能量/时刻非劣或改善 | seed、密度、完整case | 同观测任务中的内部物理增量 |
| proposal改善关键位置覆盖 | frozen sparse B+IS | P-U→P-I，同期望目标 | 不牺牲电热/器件量 | wall-clock、RAD/GAR、mask | 有界采样效率与适用域 |
| phase空间残差度量更适合事件 | calibrated P-M | P-I→P-M及P-S反事实 | event收益转化为功能量 | global weight、强metric基线 | 超出已测试全局标量的度量适配 |
| 局部状态误差具有不同功率影响 | 约化电敏感度，仅diagnostic | 条件/扰动检查与误差位置对应 | 解释I/能量改善或差距 | 电残差/边界缺陷、读出敏感性 | 状态敏感度解释，不是DWR上界 |
| 相对phase启动动力学被压低 | 条件A完整latent residual | 原始/全局权重/latent三臂 | phase与T均检验 | 数值范围、梯度方向、实体 | 特定度量增量，非通用预条件保证 |

如果只有通用sparse PINN有效、新接口不胜最近强基线，不能声称新增算法。若模块无必要，移到辅助/补充材料而不是为了“创新点数量”强留主结构。

## 12. 氧化物定位与来源访问边界

当前对象足以作为合成器件启发的方法benchmark，不能单独支撑VO2/特定氧化物材料定量预测。Miquel等的原始对象是Ge-rich GST，含多相/成分、TBR和部分电场相关导电率，既非氧化物也非当前简化本构。[R12]

Sevic–Kobayashi2023为电热阻变相场，采用另一类守恒状态动力学；Sevic–Juston–Kobayashi2025文中脚注明确本研究固定300K、isothermal。后者不能直接担当当前完整电热耦合的来源。[R13–R14]

如果最终标题必须强调氧化物器件，应在方法信号成立后增加一个单一来源、具备2D因果链和必要数值资格的应用对象；不混用GST/氧化物参数，不用另一仓库的结果补证。若来源尚不能闭合，只写synthetic electrothermal phase-transition benchmark；这也意味着当前氧化物器件论文定位尚未完成。

本轮原文覆盖：Nabian的理论/算法正文；AA与Sharp的关键全文方法段；DWR、算子预条件化和PC-PINN的可解析关键段；RAD与PF-GAR官方源码；材料原文。PF文章部分正文和官方实现可读，未独立核查所有公式图片/补充数据。部分PDF下载、图像截图或全文入口失败，没有因此虚构图表数值。没有实际运行作者代码或本项目scientific checkpoint。文献检索不是全球优先权证明。

## 来源（正式链接，不包含会话引用标记）

### 仓库固定证据

[G1] main分支读查询： https://api.github.com/repos/ghy001122/PINN-PCM-SCI/branches/main 。本轮所得固定树： https://github.com/ghy001122/PINN-PCM-SCI/tree/918985c88f98321c96e6952c9bdd725bd958ed0e 。

[G2] PROJECT_STATE： https://github.com/ghy001122/PINN-PCM-SCI/blob/918985c88f98321c96e6952c9bdd725bd958ed0e/PROJECT_STATE.md 。LF10 terminal artifact： https://github.com/ghy001122/PINN-PCM-SCI/blob/918985c88f98321c96e6952c9bdd725bd958ed0e/docs/experiment/artifacts/20260909T101615Z-phk-v23-lf10-terminal.json 。

[G3] LF6 closeout： https://github.com/ghy001122/PINN-PCM-SCI/blob/918985c88f98321c96e6952c9bdd725bd958ed0e/docs/experiment/2026-09-06-phk-v23-lf6-terminal-closeout.md 。论文与主张矩阵目录： https://github.com/ghy001122/PINN-PCM-SCI/tree/918985c88f98321c96e6952c9bdd725bd958ed0e/paper/paper_v23 。

[G4] 当前本构与strong-form： https://github.com/ghy001122/PINN-PCM-SCI/blob/918985c88f98321c96e6952c9bdd725bd958ed0e/pinn_pcm_sci/phk_v22r_pinn.py 。

[G5] 旧比较归一化： https://github.com/ghy001122/PINN-PCM-SCI/blob/918985c88f98321c96e6952c9bdd725bd958ed0e/pinn_pcm_sci/phk_v21_benchmark.py 。正式evaluator： https://github.com/ghy001122/PINN-PCM-SCI/blob/918985c88f98321c96e6952c9bdd725bd958ed0e/pinn_pcm_sci/phk_v22r_evaluator.py 。历史floor： https://github.com/ghy001122/PINN-PCM-SCI/blob/918985c88f98321c96e6952c9bdd725bd958ed0e/outputs/runs/20260828T-phk-v21-s1-q-terminal-summary-001/oracle-floor-seal.json 。

### 原始研究

[R1] Nabian MA, Gladstone RJ, Meidani H. Efficient training of physics-informed neural networks via importance sampling. Computer-Aided Civil and Infrastructure Engineering 36(8),962–977 (2021). DOI: https://doi.org/10.1111/mice.12685 。作者预印本： https://arxiv.org/abs/2104.12325 。重点：Eq.(10)–(17),Algorithm2。

[R2] Wu C, Zhu M, Tan Q, Kartha Y, Lu L. A comprehensive study of non-adaptive and residual-based adaptive sampling for physics-informed neural networks. CMAME403,115671 (2023). https://doi.org/10.1016/j.cma.2022.115671 ; https://arxiv.org/abs/2207.10289 。官方实现： https://github.com/lu-group/pinn-sampling/blob/main/src/allen_cahn/RAD.py 。本轮所读该文件blob SHA83752469f844f209e649e57123af176ce67aaed9。

[R3] Chen N, Lucarini S, Ma R, Chen A, Cui C. PF-PINNs: Physics-informed neural networks for solving coupled Allen-Cahn and Cahn-Hilliard phase field equations. JCP529,113843 (2025). https://doi.org/10.1016/j.jcp.2025.113843 。固定官方实现： https://github.com/NanxiiChen/PF-PINNs/blob/f8a4980108504a984695b75d2665b27d5f26cc0b/pf_pinn/model.py ，adaptive_sampling函数。

[R4] Chen N et al. Sharp-PINNs: staggered hard-constrained physics-informed neural networks for phase field modelling of corrosion. https://arxiv.org/html/2502.11942v1 。重点：§3，Eq.(17)(18)，Algorithm1。

[R5] Buck K, Kim W. Auto-Adaptive PINNs with Applications to Phase Transitions. NMTMA19(2),510–534 (2026),正式出版2026-05-07. https://doi.org/10.4208/nmtma.OA-2026-0014 ; https://www.global-sci.com/nmtma/article/view/24100 ; https://arxiv.org/html/2510.23999v4 。重点：§1.2.3，Eq.(13)–(17)。

[R6] De Ryck T, Bonnet F, Mishra S, de Bézenac E. An operator preconditioning perspective on training in physics-informed neural networks. ICLR2024. https://arxiv.org/pdf/2310.05801 。重点：算子/切空间与线性化条件。

[R7] Liu S et al. Preconditioning for Physics-Informed Neural Networks. 2024. https://arxiv.org/abs/2402.00531 ; https://arxiv.org/pdf/2402.00531 。重点：离散算子、预条件残差和非线性扩展。

[R8] Govoeyi M, Richter T. Goal oriented error estimation for adaptive sampling of PINNS. 2026-04-02. https://arxiv.org/pdf/2604.01835 。重点：Eq.(3.4)、§4.3、Eq.(4.9)(4.10)，printed pp.10–12；正文明确非严格上界。

[R9] Wang S, Sankaran S, Perdikaris P. Respecting causality for training physics-informed neural networks. https://arxiv.org/abs/2203.07404 ; https://doi.org/10.1016/j.cma.2024.116813 。

[R10] Wang S, Koohy S, Lu Y, Perdikaris P. When PINNs Go Wrong: Pseudo-Time Stepping Against Spurious Solutions. https://arxiv.org/html/2604.23528v1 。固定配置点的存在性论证不自动解释所有重采样模型。

[R11] Tepakbong N, Hu H, Liu C, Zhou X. Taming the Loss Landscape of PINNs with Noisy Feynman–Kac Supervision: Operator Preconditioning and Non-Asymptotic Error Bounds. 2026. https://arxiv.org/html/2606.00643v1 。数据监督预条件化的近邻线索，不是当前模型的已适用定理。

[R12] Miquel R et al. Multi-Physics Modeling Of Phase Change Memory Operations in Ge-rich Ge2Sb2Te5 Alloys. 2024. https://arxiv.org/html/2409.06463v1 ; https://doi.org/10.1063/5.0222379 。

[R13] Sevic JF, Kobayashi NP. Resistive Switching Conducting Filament Electroformation with an Electrothermal Phase Field Method. 2023. https://arxiv.org/pdf/2307.14582 。

[R14] Sevic JF, Juston A, Kobayashi NP. A Morphologically Self-Consistent Phase Field Model for the Computational Study of Memristive Thin Film Current-Voltage Hysteresis. 2025. https://arxiv.org/html/2506.17421v1 。重点：脚注2的300K isothermal限制。

## 最终行动建议

先提交D_B/P-U/P-I/初始标度校准P-M的6000-step有界方案。将完整latent residual保留为一个由真实跨头机制证据触发的备选；能量与器件敏感度先作为解释，不抢先升级为训练模块。第一次可靠方法增量出现后，优先补最近强基线、标量反事实、器件后果与完整实体确认，而不是继续扩大组件数量。
