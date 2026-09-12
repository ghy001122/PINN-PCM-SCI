# LF11 / paper_v26 独立复评与新协议 PLAN

交接编号：PCM-20260912-LF11-V26-CLOUD-REVIEW-01

固定版本：4c16ba2ece84d4dd0c561f22ff91fe5b4932cfc6
状态：PROPOSED_NOT_AUTHORIZED。仅来源核查、推理与设计；未训练、求解、加载科研检查点前反向、读取 stress 或修改 Git。

## 1. 决策摘要

本轮支持“接触迹显著影响当前离散器件读出”，不支持“必须先发明新的 hard lift，才能检验内部 PDE”。

建议停止纯数据 V 拟合的连续追加，也暂缓重构 V 输出表示。另立一个新实验身份，从当前 V_continued 完整模型直接启动三个匹配臂：
D_I（观测＋共同 IC）、D_B（再加原软 BC）、P_U（再加完整原内部 PDE）。

三个臂都恢复三头及 T adapter 联合训练。D_I→D_B识别软BC包的增量；D_B→P_U识别内部PDE增量；父状态→D_B不再被错误解释成纯BC效应。

这是必须经用户批准的新协议，不是对原 V≤0.5% 准入的追溯放宽。原协议仍记录未过门，原D_B/P_U仍是未运行。新实验不设0.6%等替代门，不把当前状态叫“已过原门”，只研究这一明确、数值合法且已显著修复的共同起点。

建议在这个新实验的共同父状态一次性参考盲校准 a*、b*；三臂共享，不逐臂重校准。不修改旧a0/b0或旧冻结文件，不能据新旧实验差异单独归因“拟合修复”。

唯一条件备选仍为完整可微电学残差块归一化R/G/N，N阳性后必要D_N。它需要新P_U轨迹证据，不能由大底流或既有代数恒等式自动触发。

## 2. 核查范围

已独立读取固定版本：
- main分支响应；LF11 V continuation terminal closeout；
- v_continue与electric_trace_audit、v_evaluate源码；
- paper_v26摘要/问题设置、新增结果、讨论、主张矩阵；
- evidence说明、electric-post.json、V接受日志后段、全14行endpoint数表；
- 冻结配置的停止条件、归一化身份及未消费元数据。

数值主要是已保存证据的读审，不是本轮重算。仅对已公开标量作了透明算术整理。未打开二进制科学检查点或NPZ数组，未重新生成模型预测，完整own-model预测及nominal原参考仍在本地，不可声称本轮独立复现。
文献方面核查官方会议/原论文条目；部分全文入口被阻挡或返回错配模板，未将其作为已核实全文，更未引用未查看图表的性能值。

## 3. 已成立的成果和解释边界

VERIFIED（已保存结果与实现）：
- V固定目标下降53.23%，200评估/99接受步，终点可见V RMS为0.561839%；不是收敛证明。
- T、phase、T adapter及sigma不变，器件量的前后变化来自V函数变化。
- 底流有符号积分下降中99.4058%对应迹项变化；不是RMS解释率、全轨迹根因或独立操纵迹项的因果效应。
- 接触端点补齐基线保持原观测和T/phase，不训练、不求解，改善底流和功率；不是PINN创新。
- 新内部PDE比较未执行，不能否定改善后父状态上的PDE。

SUPPORTED_INTERPRETATION：
- 现有迹误差对当前FV读出重要，且并非只集中于接触端点。
- 纯观测拟合没有直接加入缺失的软BC目标；继续逼近体积拟合门未必最能回答当前科学问题。
- 接触精确不等于绝缘通量、内部电方程或完整器件已经正确。

UNKNOWN：
- 新父状态上软BC与内部PDE各自收益；
- 新hard表示或电学归一化独立优势；
- 独立初始化、观测规则、完整案例、材料定量有效性。

## 4. 新的判别性算术与物理解释

post.json有：
积分I_b=3.7215075374；
积分I_trace=3.3798469367；
积分I_drop=0.3416606007；
积分I_top=0.6082083554；
积分I_AD,bottom=0.3411611275。

1) 迹项占底流积分90.8193%，但迹项中约73.3993%来自代码定义的contact-interior，只有26.6007%来自首末各两面。不能据此把全部问题归为端点奇异性。

2) I_drop积分仅约为I_top积分的56.1749%；两者相差-0.2665477547。AD底流积分同样仅约为模型顶流积分的56.0928%。这是同模型内部电学比较，不是参考误差率。即便“迹项很大”成立，底部电压增量/内部电学也尚未闭合。

3) 不允许把I_drop作为“扣除错误后的正式电流”。改变实际边界表示或训练时，v_i和梯度会同时改变。

精确恒等式：
I_b = Σc_i b_i + Σc_i(v_i-b_i)；
P_b = Σc_i b_i² + 2Σc_i b_i(v_i-b_i) + Σc_i(v_i-b_i)²。
交叉项保留符号，RMS分量不能相加成贡献率。
当前节点缺陷还满足Σd_i=I_bottom-I_top及P_J-U I_top=Vᵀd；它们是相关而不等价的诊断，不是独立物理发现。

4) V接受日志在评估161→200仍有约8.8055%的目标下降。因此不能说优化已到极限；但也没有证据保证再一次预算能通过任何门或修好通量。

## 5. 为什么不优先新hard lift

非零heater trace值得解决，但来源可能是没有直接训练软BC、有限优化、有限表示或混合边界结构。现有证据没有排除最便宜的“原表示＋软BC”解释。

原四次方lift：
d_h=z+(x-a)_+^4+(-x-a)_+^4，d_t=1-z，
b=d_h e^h/(d_h e^h+d_t)。
在绝缘底边x=a+s,z=0，零法向导数要求h_z=-1-s^-4。这是此前条件解析反证，不能恢复为默认候选。

新的hard映射必须另外处理D/N接点、有限法向通量、热源正则性及表示效率。通用hard BC有先例，SEPINN已有混合边界奇异富集；直接写一个hard lift不自动具有新颖性。
本轮不追加新hard/奇异富集、Nitsche、通量网络或全局solver层。它们不是自动备用队列。

## 6. 新主线：D_I / D_B / P_U因果阶梯

### 6.1 问题和新身份

要回答：
- 继续联合观测训练会怎样改变phase及器件量？
- 软BC包相对同预算观测训练是否修复迹与器件读出？
- 内部PDE在共同BC底座之上是否有额外价值？

原0.5%是工程准入，不是同父匹配实验公平性的数学必要条件。新协议直接使用指定V26完整父状态，保留0.5%为报告性的原门状态；不改历史，不宣布通过，不另设事后放宽门。新结果只支持“当前明确起点和新配方下”的结论，不能称充分优化上限或普适PINN结论。

### 6.2 输入

- paper/paper_v26/evidence/endpoint-with-V-optimizer.pt：仅加载完整模型，含最终T adapter。
- paper/paper_v24/evidence/input/sparse.npz：同一稀疏观测。
- 原物理合同、IC/BC、脉冲、空间/时间坐标。
- 强基线采用已冻结B_logit_waveform_contact，并保留原B系列、dense LF_ONLY及native参照。

禁止额外dense监督、teacher电流/功率、sealed stress、新增观测或旧dense初始化进入训练。所有旧观测均已见，不能再叫未见验证。

### 6.3 损失和共同归一化

令theta*为当前V26完整父状态：
a*=Lobs(theta*)，使用完整可见观测精确既有测度；
b*=[J_U+5 L_BC+L_IC](theta*)，使用一个固定参考盲积分池；
两者一次计算后冻结，三个臂共享。

根据已发布完整观测分量算术推算a*约1.63998e-4；旧a0=0.0111884，a*/a0约0.0146578。本轮未进行前向校准，执行值仍由实际模型精确计算。此数只说明旧归一化已不是当前父态的“单位初始损失”，不证明旧尺度必然有害。

C_I = Lobs/max(a*,1e-12) + λ L_IC/max(b*,1e-12)；
L_D_I = C_I；
L_D_B = C_I + λ·5 L_BC/max(b*,1e-12)；
L_P_U = L_D_B + λ J_U/max(b*,1e-12)。

λ(k)=0.1 min(k/200,1)。
保留原electric/thermal/phase尺度1/4/5及所有BC/IC尺度、子项、平均分母、时间窗积分。IC在当前表示下近零也仍共同保留。
不逐臂/逐头/逐阶段重校准，不动态改变lambda上限。新共同校准是基础配置，不计为创新。

D_I→D_B仅增加软BC包；D_B→P_U仅增加内部PDE。三个臂同时开放phase参数，避免把phase解冻混入BC对照。D_I、D_B是无内部PDE控制，不将其宣称为完整耦合PINN。

### 6.4 实现和预算

三臂同一完整父权重、同一网络结构和T adapter；fresh Adam，不复用V-only L-BFGS历史。
每臂1000 Adam updates（lr1e-4，原betas/eps/clipping）＋最多200次固定目标/梯度L-BFGS评估。
主线上限3000 Adam＋600评估。

数据批次/BC批次同步；P_U按原uniform内部目标采样。固定时间分层，不改成新的课程。L-BFGS前冻结lambda和完整目标：完整sparse观测、预声明BC/IC池和内部池；固定4096内部点及原配置数量级BC池，独立审计池另设。
分块只为内存，累计真实权重；closure不随机重采样、不动态加权、不用裁剪梯度代替真实导数。
保存0、500、1000及L-BFGS最终接受状态；正式终点为固定预算终点或优化器内在停止，不按参考曲线选checkpoint。
个别数值无效不取消其他有效计划臂；缺失必要对照时阻塞相应主张，而非算作方法赢。

不新建V-only预拟合，不先要求heater trace、通量或严格器件门通过。现有建模/字段正确加载与有限目标检查足够；不重复全仓资格审计。
CPU或GPU采用实际可行环境；不报告GPU价格费用时长。使用GPU后回收、关闭并确认，再做本地参考评价。

### 6.5 只保留会改变选择的诊断

- 父态与最终端点：完整可见误差、heater trace、I_trace/I_drop/AD、内/顶/底耗散，用已有模块，不重造评价器。
- P_U在Adam500/1000：仅必要的electric、绝缘、heater-Dirichlet、phase-no-flux、thermal项×T/phase/V头的更新分解。
- 原始梯度、共同Adam分母中的分量、历史momentum、总方向分开；L-BFGS后不能套用旧Adam状态。
- 这些诊断不选最终checkpoint。涉及参考探针的计算只在训练结束后本地进行；优先使用可见目标判断训练方向。
- I_drop/AD相近不是真值认证；当前全域和接触端点均保留，不删难点。

## 7. 评价与Go/No-Go

保持正式S、raw Ephi、ET/.45、EV、top EI以及双周期原事件语义；同时报告bottom EI、power-trace、energy、current balance、power defect。全部从自身字段生成，不复制trace、不用P/U修读出。

分层结论：
1) 重建增量：继承S/Ephi双10%改善、ET/EI/EV非劣5%及原近零容差；器件代价另行检查，严格门单列。
2) 功能性线索：即使未过双相态改善门，若预声明bottom EI和power-trace各改善至少10%、场与top EI非劣5%，可记录为“有限器件功能增量待确认”，不是原完整成功，更不能合并成胜率。事件退化完整披露，不能以功能量替代事件。
3) 接触/BC增量仅由D_B相对D_I判定；不是网络或PDE创新。
4) P_U胜D_B仍需面对B_logit_waveform_contact及最近强PINN；不自动宣布优于求解器或具备算法新颖性。

结果路由：
- D_B已显著修复迹/底流，P_U无额外价值：表明软BC在该配方下足以带来这部分收益；不自动上hard lift或归一化。
- P_U有重建及器件联合信号：停止加模块，先最近强对照和确认。
- 只有功能信号：保留准确层级，不抹去也不包装成完整相变态方法。
- P_U原J下降却损害phase/器件：只按下一节条件判断归一化，不根据大底流自动触发。
- 全部无实用增量或数值阻塞：结束本轮，将可归因层级和具体瓶颈写清；不继续自动追加优化或更换网络队列。

## 8. 唯一条件备选：电学块归一化

触发需要新P_U相对D_B的损害，以及至少两个预声明节点上的electric/绝缘导电率幅值通道证据。若主要证据仍是heater Dirichlet迹或phase no-flux，不启动。不能由归一化数学恒等式或本轮大底流直接触发。

sigma=exp(s)，s=beta T+logR h(phi)。
rV=sigma[Delta V+grad s·grad V]；
rN=sigma ∂nV。
N改为解析RV和∂nV；Dirichlet、thermal、phase不变。

完整参数梯度：
grad(rV²)=2sigma² RV grad RV +2sigma² RV² grad s；
grad(RV²)=2 RV grad RV。
因此停止梯度的1/sigma²权重并不等价。保留完整T/phase坐标与参数梯度，不除以驱动U。
当前sigma有正下界，但归一化相对降低高sigma区域压力，故不能自动认定有利于器件功能，也不能借一般预条件理论保证本系统条件数改善。

从同一个新共同父状态建立：
R=新P_U，身份一致可直接复用；
N=归一化内部及绝缘块，父态一次匹配原电学块loss标度；
G=原块乘冻结标量，父态匹配N全参数梯度范数；
N阳性后D_N=相同归一化绝缘BC，但无内部PDE。
保持a*/b*、其他损失、目标测度、optimizer和预算。校准包括真实内部/BC系数与分母，不可靠时不动态救援。

G、N各1000 Adam＋200评估；仅N阳性才增加同预算D_N。
含全部条件路径上限6000 Adam＋1200评估。无需用满。
G或D_N解释收益、只降新loss、原始物理/功能恶化、梯度实现不等价均否决相应主张。不自动增加第二备选。

## 9. 论文与最低确认

当前可以作为论文核心诊断链：
已知场支持不足/残差与事件错位 → 可修复温度与V拟合 → 固定sigma的V作用分离 → 接触迹和内部电学缺陷不同 → 两端电流与耗散共同检查。

不能把下列内容单独计为原创算法：L-BFGS、T适配器、PCHIP、contact endpoint补齐、Cauchy/离散电路恒等式、通用硬边界或残差重权。
当前稿已经比v25更有机制内容，但仍缺强基线上的独立方法增量和确认；完成初稿不等于达到目标期刊要求。

若只有标准强PINN的PDE增量，说明底座有效，不代表新算法成立。新颖性仍需一个有机制和匹配控制的适配（例如若N被验证），并比较适用最近强方法。
不为追求新意提前同时增加两个模块。

首图：D_I、D_B、P_U同父箭头对照；正式S/Ephi与two-cycle事件；top/bottom I和P_input/P_J；trace/drop及底部/内部耗散。包含B_logit_waveform_contact与父态，不用loss曲线替代。

首次可信信号之后的顺序：
1. 最近强对照与关键反事实；
2. 两个新独立模型初始化，重做相同父态构建流程，不能从相同旧父权重换采样流冒充；
3. 一个预声明同密度平移mask，fresh训练，不复用看过额外观测的权重；
4. 一个完整新协议case，随后一个几何case/第二密度/无事件对照按主张补齐。
每case使用自身sparse support重训称case reconstruction/adaptation，不称zero-shot。
新数值case需另批求解和参考资格；当前不读stress、不自动生成数据。
current synthetic dimensionless PCM-inspired对象尚无氧化物材料定量标定。材料关联需单一来源、完整电热相态链及独立数值资格，不能改名或混用GST/oxide参数。

## 10. 机制到主张映射

|机制问题|设计|匹配差分|器件后果|允许主张|
|---|---|---|---|---|
|继续优化/phase解冻会改变什么|D_I|相对共同父态，只有流程效应|读出及事件是否变化|背景优化效应，不叫BC效果|
|软BC是否修复接触迹|D_B|D_B−D_I|I_trace、bottom I、power变化|原表示下BC包的有界增量|
|内部PDE是否必要|P_U|P_U−D_B|相态/事件与电学共同改善|该配方同信息内部物理增量|
|导电率幅值通道是否不合意|R/G/N与D_N|N超过R/G且非仅BC|原始电流/能量而非新loss|条件成立的电学度量适配|
|效果是否可重复|独立seed/mask/完整case|候选对最近强对照|完整失败案例保留|有界稳健性，非泛化口号|

## 11. 原始来源及访问边界

固定仓库：
https://github.com/ghy001122/PINN-PCM-SCI/tree/4c16ba2ece84d4dd0c561f22ff91fe5b4932cfc6
重点路径：
docs/experiment/2026-09-12-phk-v23-lf11-v-continuation-terminal-closeout.md
paper/paper_v26/manuscript.md
paper/paper_v26/claim_evidence_matrix.md
paper/paper_v26/evidence/electric-post.json
paper/paper_v26/evidence/v-telemetry.jsonl
paper/paper_v26/tables/all-endpoint-metrics.csv
pinn_pcm_sci/phk_v23_lf11_v_continue.py
pinn_pcm_sci/phk_v23_lf11_electric_trace_audit.py
pinn_pcm_sci/phk_v23_lf11_v_evaluate.py

外部原始来源（本轮不复用其数值性能为本项目证据）：
[R1] Rathore et al., Challenges in Training PINNs: A Loss Landscape Perspective, ICML2024.
https://proceedings.mlr.press/v235/rathore24a.html
支持强优化/欠优化需被考虑，不保证200次或任何本项目预算成功。

[R2] Berrone et al., Enforcing Dirichlet boundary conditions in physics-informed neural networks and variational physics-informed neural networks, Heliyon9(8),e18820,2023.
https://arxiv.org/abs/2210.14795
https://doi.org/10.1016/j.heliyon.2023.e18820
原论文比较soft、hard和Nitsche等；hard约束已有方法基础，不能推断本mixed electrothermal对象一定受益。全文入口本轮部分受限，仅使用核实的条目/摘要层结论。

[R3] Hu, Jin, Zhou, Solving Poisson Problems in Polygonal Domains with Singularity Enriched Physics Informed Neural Networks.
https://arxiv.org/abs/2308.16429
明确研究混合边界/角点奇异性；不是当前电热模型的奇异指数或性能证明。

[R4] De Ryck et al., An operator preconditioning perspective on training in physics-informed machine learning, ICLR2024.
https://proceedings.iclr.cc/paper_files/paper/2024/hash/f122a6778999d1d2b25cdc6927930f1a-Abstract-Conference.html
一般算子预条件原理不能为这里的非线性归一化直接背书。

[R5] Liu et al., Preconditioning for Physics-Informed Neural Networks,2024.
https://arxiv.org/abs/2402.00531
作为方法谱系核对，不声称本归一化首次提出或已有相同系统验证。

某些arXiv HTML请求返回模板或非正式理论文件，未作为主论文全文证据。没有新作者代码运行、scientific checkpoint运行或新的科学结果。
