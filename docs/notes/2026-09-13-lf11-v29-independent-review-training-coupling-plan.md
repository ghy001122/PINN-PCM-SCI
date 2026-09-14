# V29 独立复评：训练期电学耦合与事后电学重求解

- 日期：2026-09-13
- 交接：PCM-20260913-LF11-V29-CLOUD-REVIEW-01
- 依据固定版本：59e3a5a5cd4c2224f4dbaab5f16de299b0607a9d
- 状态：PROPOSED_NOT_AUTHORIZED。本文是评估与方案，不授权训练、求解、检查点前反向、stress读取或Git修改。

## 1. 本次决策变化

停止继续追求同一nominal上更大κ或周期2 timing单门。V29已证明原剩余PDE的完整一阶作用弱，增权实际降低了热主导残差，却没有带来冻结的匹配预测增量。P_F旧条件未满足的记录不变。

新提案改问一个独立的科学问题：在都保留热/相态残差的混合PINN里，训练期间消去电学自由度是否优于“同接口软电学PINN＋推理阶段相同电学重求解”？若仅后处理已解释收益，不能宣称训练期消元有独立价值。

这是改变研究排程与待证明主张，不是将P_E−D_E改判成功，也不是将D_C改名为完整PINN。未证明热/相态残差必需这一局限必须保留。

## 2. 已核对与未知

直接读取：main查询、V29终局、NEXT_ACTIONS、remaining_pde.py、manuscript.md、完整梯度/两池目标/事件数表，以及固定版本elimination.py中P_F分支。读取的是保存证据，没有重算科研指标。

VERIFIED：三个新臂完成223次完整评估；相同父态、fresh L-BFGS、零Adam；κ=92.8404908293；P1/Pκ对D_C没有原A/B增量，对B_E的优势保留。P_F未执行。

SUPPORTED_INTERPRETATION：小的剩余PDE增量与已有强电学嵌入约束并存；不断要求每个剩余方程额外带来10%改善，未必是最短的方法论证路线。

HYPOTHESIS：训练期电学耦合可以改善T/phase重建，且不仅是最后替换V带来的读出收益。

UNKNOWN：消元相对公平软电学方法的增量、严格双周期全部通过、干净独立初始化/观测/完整案例确认、材料标定。

## 3. 首选：一次模块独立性筛选

### 3.1 比较基准和父态

使用V28实验的原始E0父态、sparse、calibration、训练和审计池：
- paper/paper_v28/evidence/parent.pt
- paper/paper_v28/evidence/frozen-config.json
- paper/paper_v28/evidence/calibration.json及各pool
- paper/paper_v24/evidence/input/sparse.npz

该父态来自V27 D_I，不是V29 P1/Pκ或参考最优检查点。

E参考：优先复用已完成的V28 P_E（1500 Adam＋300评估）及同协议D_E、E0、B_E，不重训。V29 P1/Pκ/D_C仅作较长开发历史的上下文，不能替代同预算对照。

T/phase、适配器、已知物理、数据完全一致。E的初始V由求解得到，F的V来自同一父态原V头；必须披露这一结构造成的初值差异。此筛选识别训练方法包，不声称只识别VJP算法本身或已排除所有初值/优化路径解释。

### 3.2 唯一主要变化

E使用v*=A(σ)^{-1}f并完整隐式微分。

F保留V头；使用相同面电导、混合电边界和半电阻产热；以
r_e^FV=(A(σ)Vθ−f)/cell_volume
作为电学残差。热单元和原phase残差不变，V观测仍是同一可见V标签。

F的边界通过同一离散面网络进入残差，不额外恢复一组不同电BC项；其余BC/IC保留原分母13/3，不调其他块。

F目标：
L_F(η)=C_F+F_Tφ+ηE_e，
E_e=λ Eρ[(r_e^FV/1)^2]/(3b_E)。
所有数据/BC/热/phase权重、a_E/b_E、λ上限0.1及200步ramp沿用V28。

### 3.3 不让弱电学权重成为稻草人

同时预声明两个soft配置：F_raw(η=1)和F_bal。

F_bal在原E0校准池对其自身实际目标计算：
G0=sqrt(||g_obs||²+||g_BC/IC||²+||g_T||²+||g_φ||²)，
η_bal=G0/||g_e||。
梯度均含真实目标系数，作用于全部F训练参数。只校准一次并冻结；不按reference选值，不动态调权。比例不可辨则不伪造系数；若η_bal与1数值上相同，省略重复臂。

该校准是对强比较者的合理加强，不是新的算法贡献，也不声称已找到最优软权重。两配置全部报告；消元收益不能只相对更弱者成立。

### 3.4 训练预算

每个F配置：1500 Adam＋最多300次完整固定目标/梯度评估，与V28 P_E计数对齐。
Adam学习率、betas/eps/clipping、观测/物理时间流保持V28；L-BFGS固定原完整目标，试探全计数，最后接受态回滚规则不变。fresh optimizer，无新的V拟合门，不先重训S0/S1。

主线新增最多3000 Adam＋600次完整评估；两配置总量明确，不能说与单个E参考等总算力。F训练使用显式面运算，不调用电学正反求解；仍记录全网格评价/AD工作量，等step不叫等算力。实际部署优先GPU，回收并关闭后再读参考，不报告价格、费用或时长。

### 3.5 同一F终点的两个读出

1. F_raw-readout：原Vθ/Tθ/φθ，按共同FV读出。必须保留。
2. F_projected：固定F的Tθ/φθ，160×80上重求电学得到V†，用同一读出计算。每个终点最多278个非零时刻线性正解，两配置556；零驱动跳过。

投影仅用自身σ、已知U和BC；不训练、不新增标签。它改变电势和q，不是重新求得完整自洽热/相态轨迹，也不叫独立模型重复。T/phase/S/Ephi/事件必须与对应未投影终点一致。

比较：
- E对F原读出：总训练＋推断方法差异；
- F投影前后：固定T/phase下推断电学替换的作用；
- E对F_projected：双方同样使用推断电学求解后，是否仍有学习状态差异。

只有第三类也有可重复的预测优势，才支持“收益不只是事后电学修复”。它仍不是单独VJP的因果证明。

### 3.6 评价、停止和首图

保留正式S/raw Ephi/ET/EV/EI、两周期recall/precision/mass/timing/recovery、功率轨迹/能量/局部q。相关电学守恒量不当独立验证。

旧V28/V29 A/B和严格门全部保留。在新方法比较中，预声明沿用10%增益/5%非劣作为实用信号；E必须面对两种F_projected，而不只击败未投影F。全表呈现D_E、B_E及V29开发端点，不将不同预算比较冒充因果。

- E只胜F原读出、不能胜F_projected：不能建立训练期消元独立价值。
- F原读出已同样好或更好：优先较简单有效方法；不宣称消元必要。
- E对F_projected也有清楚A/B增量：进入独立确认，停止加模块。
- 各臂近似持平或无联合优势：有界否定该方法包的必要性，不无界调权。
- 数值无效/预算不完整：不算胜利，不按参考挑中间checkpoint。

首图：每个F配置投影前后连线；同图列E参考、D_E、B_E。上部S/Ephi和完整事件，下部真实电流/功率/能量。它直接回答准确性来自训练期耦合还是最终电学修复，不以机器精度守恒作为主胜点。

## 4. 唯一条件备选：缩小并修正数值敏感性试验

不把NEXT_ACTIONS的四函数256正解审计作为新主线或前置资格。仅当主方法比较无可辨增量，且下一决策确实取决于是否要修改热数值接口时，才执行一次：

冻结V29 P1和Pκ两个函数，原32个audit时刻、80×40热控制体和相态点；比较中点/两点高斯面＋2×2单元均值，以及80×40/160×80电学源。细q体积保守聚合；缓存每个函数/时刻/电网的电学解。最多128次电学正解，零训练、零参数梯度、零伴随；关断时刻跳过。

关键不是绝对J变动是否大于2.19%，而是同规则下的方法差值：
Δ_{q,h}=J_{q,h}(Pκ)−J_{q,h}(P1)。
比较Δ是否换号及|Δ_alt−Δ_base|相对|Δ_base|。大的共同偏移可在方法差值中抵消，不能据此宣布原排序无效。

若r_{q,h}=A_q−Qq_h，令a=r_G,c−r_M,c、b=r_M,f−r_M,c，则平方范数的2×2交互为2<a,b>（保留同一尺度和积分权重）。所以loss层交互可以仅来自平方及误差抵消，不代表发现新的物理耦合。

稳定只支持这些设置间的敏感性边界，不证明连续体收敛；不稳只支持数值规则依赖，不证明高斯/细网格必然是真值或预测更好。任何后续接口训练修正另批，不能在该审计内继续调参。

## 5. 论文与后续确认

可以保留：电学接口修复、同层强插值收益、V29完整弱梯度事实和实际热残差—事件—器件取舍。κ和适配器不独立计创新。

主贡献候选转为：在保留可记录热/相态残差的混合PINN中，训练期约化电学约束相对强同接口soft PINN及其同等推断修复是否提供增量。不能据此把D_C改名为完整PINN；剩余热/相态残差未证明必需仍需正文披露。

若方法比较阳性：先两个从头独立初始化并配对最近控制，再一个干净平移mask，再一个完整新协议；预算另批。新mask不能复用见过被删除观测的权重，案例自有support重训不叫zero-shot。

真正缺失信息任务值得未来考虑，但必须有明确未知物理量、激励/可辨识性及同信息传统逆问题基线；本轮不通过隐藏phase标签或第二周期来制造新优势。当前合成二维对象不是标定氧化物器件，不能自动更换材料身份。

## 6. 原始来源与访问范围

- 固定仓库：https://github.com/ghy001122/PINN-PCM-SCI/tree/59e3a5a5cd4c2224f4dbaab5f16de299b0607a9d
- V29 NEXT_ACTIONS：https://github.com/ghy001122/PINN-PCM-SCI/blob/59e3a5a5cd4c2224f4dbaab5f16de299b0607a9d/docs/plans/NEXT_ACTIONS.md
- Solver-in-the-Loop, NeurIPS2020：https://proceedings.neurips.cc/paper/2020/hash/43e4e6a6f341e00671e123714de019a8-Abstract.html
  作者详细项目页：https://ge.in.tum.de/publications/2020-um-solver-in-the-loop/
  官方代码：https://github.com/tum-pbs/Solver-in-the-Loop
  本轮核对官方项目方法说明及README；论文HTML入口不可用，未声称核验全部全文/实验。
- Blondel等，Efficient and Modular Implicit Differentiation，NeurIPS2022：https://proceedings.neurips.cc/paper_files/paper/2022/hash/228b9279ecf9bbafe582406850c57115-Abstract.html
  仅用于成熟隐式微分范式，不借其理论证明本模型有效。
- Baez等，Guaranteeing Conservation of Integrals with Projection in PINNs：https://arxiv.org/html/2511.09048v1
  本轮读取方法与信息前提。该文投影依赖守恒量目标；非守恒情形的c(t)由离散解推算，不可直接引入本项目为额外全场标签。
- Berrone等，VPINNs: Role of Quadratures and Test Functions，JSC2022：https://doi.org/10.1007/s10915-022-01950-4
  本轮核对出版全文页面；其椭圆Petrov–Galerkin/inf-sup分析不能直接认证当前非线性热相变界面。
- Kaltenbacher，Regularization Based on All-At-Once Formulations for Inverse Problems，SINUM2016：https://doi.org/10.1137/16M1060984
  消元与全空间是已有思想；本文应用的必要性仍需新对照，而不是概念命名。

本文件仅作调研与规划，没有科研训练、求解、checkpoint实验或Git写入。所有未来预算和新协议必须经用户后续批准。
