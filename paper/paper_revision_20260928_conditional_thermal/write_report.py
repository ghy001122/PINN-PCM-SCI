"""Write the complete report from saved scores, with no scientific propagation."""
from pathlib import Path
import csv,json
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
def rows(name):return list(csv.DictReader((HERE/'results'/name).open(encoding='utf-8')))
def table(headers,data):
    return '\n'.join(['| '+' | '.join(headers)+' |','|'+'|'.join(['---']*len(headers))+'|']+['| '+' | '.join(map(str,r))+' |' for r in data])
def number(x):
    value=float(x)
    return f'{value:.6f}' if abs(value)>=.001 else f'{value:.3e}'
T=rows('temperature.csv');C=rows('closure.csv');D=rows('decomposition.csv');S=rows('source-step-sensitivity.csv')
execution=json.loads((HERE/'execution.json').read_text());summary=json.loads((HERE/'results/summary.json').read_text())
hist=json.loads((HERE/'results/history-diagnostics.json').read_text())
labels={'single_9V':'9 V/A','single_12p5V':'12.5 V/A','single_15p8V':'15.8 V/A','pair_excitation':'激发','pair_inhibition':'抑制'}
def label(x):return labels[x['case']]+('/'+x['device'] if x['case'].startswith('pair') else '')
full=[x for x in T if x['window']=='full' and x['dt_s']=='5e-10']
def find(data,ident,dev,method):return next(x for x in data if x['id']==ident and x['device']==dev and x['method']==method and x.get('window','full')=='full')
temp=[];decomp=[];clos=[];oldenergy=[];alltemp=[]
energy=list(csv.DictReader((ROOT/'paper/paper_revision_20260928_circuit_comparison/scoring-subset/results/energy-windows.csv').open()))
for x in [x for x in full if x['method']=='P']:
    ident,dev=x['id'],x['device'];cs=find(full,ident,dev,'CS');q=find(full,ident,dev,'Q_ref');v=find(full,ident,dev,'V_ref')
    temp.append([label(x),number(q['rms_K']),number(v['rms_K']),number(x['rms_K']),number(cs['rms_K']),number(x['max_abs_K']),number(cs['max_abs_K'])])
    dp=find(D,ident,dev,'P');dc=find(D,ident,dev,'CS')
    decomp.append([label(x),number(dp['interpolation_rms_K']),number(dc['interpolation_rms_K']),number(dp['voltage_power_representation_rms_K']),number(dp['continuous_vs_saved_Euler_rms_K'])])
    for m in ['P','CS']:
        r=find(C,ident,dev,m)
        clos.append([label(x),m,number(float(r['I_KCL_rms_A'])*1e6),number(float(r['I_R_rms_A'])*1e6),number(float(r['closure_rms_A'])*1e6),number(r['R_rms_ohm']),number(r['g_rms_fraction']),number(float(r['I_KCL_min_A'])*1e6)])
        e=find(energy,ident,dev,'PCHIP' if m=='P' else m)
        oldenergy.append([label(x),m,number(e['reference_nJ']),number(e['signed_error_nJ']),number(float(r['power_min_W'])*1e3)])
for x in T:
    if x['window']=='full' and x['method'] in ['P','CS']:
        alltemp.append([label(x),float(x['dt_s'])*1e9,x['method'],number(x['rms_K']),number(x['max_abs_K']),number(x['signed_mean_K']),number(x['end_difference_K']),f"{float(x['candidate_min_K']):.6f}–{float(x['candidate_max_K']):.6f}"])
hrows=[]
for x in hist:
    if not x['id'].endswith('0p5ns'):continue
    for r in x['diagnostics']['rows']:
        if r['window']!='full':continue
        out=x['diagnostics']['outside_constitutive_temperature'][r['device']]
        hrows.append([x['id'].replace('-0p5ns','')+'/'+ 'AB'[r['device']],x['method'],r['reversals']['source_count'],r['reversals']['candidate_count'],number(r['delta_mismatch_time_fraction']*100),number(r['g_half_branch_mismatch_time_fraction']*100),number(out['outside_time_fraction']*100)])
text=f'''# 条件热响应与迟滞本构闭合：实际结果

任务 **PCM-20260928-CONDITIONAL-THERMAL-CLOSURE-01**；批准基线 `390ca72aee60a0f483697d52b72674bf07dd7297`。计算于2026-09-29（北京时间）完成，沿用批准任务ID。执行合同、评审和提案分别保存在[指令](instructions.md)、[评估](review.md)、[提案](proposal.md)。本报告记录已执行的有界新条件响应，不把它称为零新增计算。

## 1. 结论与唯一下一动作

**VERIFIED：**40条系统级主热响应、40条同输入8点求积复核、10条来源历史核对和20条无反馈预测历史重放完成。最大4/8点温差为 **{summary['max_quadrature_K']:.6e} K**，低于预定1e-6 K；10套源R/g/H均逐位复现。全部三层温差分解在保存FP64数值上逐点闭合。五工况两来源步长及三窗口全部保留。

**SUPPORTED_INTERPRETATION：唯一下一动作选择第三类——聚焦热输入时序／合法状态估计。**动态工况的重构误差已经进入温度、历史与本构闭合，不能只作为端口尖峰导数误差解释。12.5 V细步P/CS温度RMS为0.654351/0.761025 K，最大为6.472258/9.257625 K；同一来源的V_ref RMS仅0.018898 K。原生表示差和Euler差不能解释掉主要温度缺陷。

该选择是后续问题定位，不是新增计算授权，也不是PINN必要性证明。若提出下一方案，应让同信息的传统物理状态估计作为强基线，并处理完整合法历史与联立约束；本轮不执行该方案。保存源模型初态已知，不能人为改为未知以制造神经优势。未启动4000/800训练、第三种插值或救援扫描。

**UNKNOWN：**用途容差tau_task、连续真实解误差界、实验温度真值、二维空间增量、PINN方法增量及材料验证。小的总能量偏差、相同峰数或数值求积通过均不闭合这些问题。两来源步长是敏感性检查，不是独立重复或统计置信区间。

## 2. 固定输入与信息边界

复用五工况的1/0.5 ns、0–20 μs保存记录及已锁定197点PCHIP/CS多项式，未重新拟合。P/CS预测函数只接收各自有限电压多项式、固定参数、325 K初温；原T/R/g/H在控制和评分入口使用。每次迟滞重放独立从作者324.9 K合法历史开始，保留0.01 K联合向量触发、动态电阻因子、305–370 K本构裁剪以及同层读出。状态温度不裁剪。

Q_ref由保存功率V·I_device的分段线性函数驱动；V_ref由原生电压的分段线性表示驱动。P和CS使用保存多项式。各分段为实际函数折点与原生输出时刻的并集，分段间连续传递状态。使用固定线性热算子及y=Cth(T−Tb)+Cp²/2变换；电容能量在读出时扣除，不作为额外热源。CS负输入完整保留。双器件联合求解，每系统仍算一条响应。

完整参数、单位与限额见[配置](config.json)；实际源文件身份、分项求积节点数和耗时见[执行记录](execution.json)。未读取实验CSV或4.1/3.9 V留出，无参数拟合、神经训练、RC反馈、热迭代、源轨迹重跑或GPU工作。

## 3. 全角色温度结果

下表为0.5 ns来源、全0–20 μs、归一化梯形时间权重。绝对单位K，未用325 K分母稀释误差。Q/V是解释控制，不替代保存温度或旧能量参考。

{table(['角色','Q_ref RMS K','V_ref RMS K','P RMS K','CS RMS K','P最大差 K','CS最大差 K'],temp)}

9 V处于近静息情形，温差极小且主要受原生表示差影响，不能用其相对百分比宣称显著物理收益。动态角色P/CS温度RMS为0.147–0.761 K；CS在抑制两角色改善RMS，在12.5 V、15.8 V和激发两角色恶化。各角色温度RMS改善方向在两来源步长相同，但并非统一优势。

## 4. 三层温差与来源敏感性

逐点保存 T_m−T_saved=(T_m−T_Vref)+(T_Vref−T_Qref)+(T_Qref−T_saved)。以下各列是分别计算的RMS，**不能直接相加**；相关交叉项隐含在逐点和中。全部差分数组位于各系统的decomposition.npz。最大逐点代数差为{summary['max_decomposition_closure_K']:.1e} K。

{table(['角色','P−V_ref RMS K','CS−V_ref RMS K','V_ref−Q_ref RMS K','Q_ref−saved RMS K'],decomp)}

动态角色有限观测项大于本轮同来源表示项；但对极小静息效应和细微方法排序不扩大结论。12.5 V的0.5 ns来源两控制项RMS为0.021813和0.016209 K，相比P/CS有限观测项0.649993和0.758883 K更小。旧能量总量差−0.029316 nJ的提醒有效：能量定义不能代替此处温度评价。

原始两来源步长保存温度在共同原生节点的未对齐敏感性如下。它同时包含非线性原轨迹的时序变化，不能当作本条件求积误差，更不能当作连续误差上界。12.5 V源温度RMS差0.194610 K，超过两方法RMS之差0.106674 K；因此本包只描述每一冻结来源上的比较，不宣称P对连续物理解有这一精确优势。

{table(['角色','saved粗−细 RMS K','saved粗−细最大 K'],[[label(x),number(x['rms_K']),number(x['max_abs_K'])] for x in S if x['method']=='saved'])}

数值求积差与每项温度效应的比例见[numerical.csv](results/numerical.csv)，全角色和所有控制均报告。4/8点差是本实现分辨指标，不是严格积分误差界；此处没有基于它发明物理通过线。

## 5. 本构电流与电路闭合并不等价

I_R=p/R(T_cond,H_cond)仅是无反馈诊断。原I_KCL、旧峰/能量评分和原稿结果不变。下表把原电流代价与新增诊断相邻呈现，0.5 ns来源全程。

{table(['角色','方法','原I_KCL RMS μA','I_R RMS μA','闭合RMS μA','R RMS Ω','g RMS','原I_KCL最小 μA'],clos)}

例如抑制B的CS，I_R误差降到26.427 μA，但闭合RMS仍为103.940 μA；不能因辅助读出更接近源电流就称为自洽电热解。12.5 V P/CS闭合RMS为223.271/243.731 μA。静息9 V的所有绝对电流误差较小，应按原量级报告。

下表**直接引用旧评分CSV**，没有重算、更换能量基准或更改旧判决。负功率为本次沿用的保存时刻预测值，不声称连续时间全局最小值。

{table(['角色','方法','旧W_Q nJ','旧总能量有符号差 nJ','保存点最小功率 mW'],oldenergy)}

## 6. 历史、分支与本构温区

十套来源R/g/H在合法初态重放下逐位一致，来源时序没有未闭合项。下面反转计数来自delta真实符号改变，而非首次置1后不再清零的reversed标志。分支差按时间权重报告。完整按序反转时差、未配对反转、全部历史量误差与三窗口结果见[history-diagnostics.json](results/history-diagnostics.json)。按事件顺序比较没有逐峰平移；新增反转使后续序号失配时，不把其时差解释为单个物理事件的精确延迟。

{table(['角色','方法','源反转数','候选反转数','delta不同时间%','g半阈分支不同%','超305–370K时间%'],hrows)}

12.5 V源反转13次，P为13次、CS为25次；CS在其余动态角色同样出现更多反转。保留这些不利证据，同时保留抑制角色RMS改善。原始源轨迹本身也会超出370 K，本轮采用原作者内部裁剪，未将高温输出解释为该材料本构在更高温区已获验证。超区间表仅定位原生样本区间，不虚构离网格穿越时刻。所有低于环境温度的微小数值值也保留，未裁剪。

## 7. 展示、现稿与测量请求

固定12.5 V展示和全工况入口见[图件索引](figures-index.md)。完整结果表包含168条温度、84条三层分解、84条本构/电流窗口记录、56条数值资格和35条来源步长敏感性；完整原生数组保留FP64精度，双器件不拆作独立实验。

新对外稿只更新[访问声明](access-change.md)，[17页PDF](manuscript/manuscript.pdf)和[DOCX](manuscript/manuscript.docx)科学正文未改。已公开的旧电路V/I最小子集和仍未完成外部访问的旧二维全场分开说明；本轮新热数组只在本地交付，不假称已公开，P03仍开放。

[既有英文请求稿](../paper_revision_20260928_circuit_comparison/measurement-request-draft.md)可交作者发送；[收件人与发送确认项](author-contact-status.md)已给出，收件人尚未核实、未发送。未获回复不阻塞本包，也不自动启动实验校准。这是行政交付，不是另一条后续科研路线。

## 8. 成本、复算和终止

实际主计算共{execution['seconds']:.3f}秒，本地FP64、4线程环境。分项数量40主响应+40求积核对+10源历史+20预测历史，没有额外物理时间步或重复科学运行。每输入分段数、求积节点数、热/历史耗时分别记录，不将总响应数混同为线性求解次数。必要合成检查共9项通过。

[复算说明](reproduction.md)区分“保存数组评分”和“新增条件求积/历史重放”。现有结果无需再次推进即可重建表格与图；原作者模型实现仅复用其迟滞类，未调用simulate/run。

所有新数组与运行身份本地保留；少量新交付待下一已授权实例会话同步，未为同步启动GPU。旧源数组、锁定插值、历史负面结果未修改。无Git发布、数据上传、作者邮件或投稿。任务完成即关闭；任何下一研究须另行明确授权。

## 附表：两来源步长的完整温度主结果

完整全程、前半、后半窗口均在[temperature.csv](results/temperature.csv)；下表给出两来源步长全程的均值、末值和温区，避免只展示较好的细步结果。

{table(['角色','来源步长ns','方法','RMS K','最大差 K','有符号均差 K','末值差 K','候选温区 K'],alltemp)}
'''
(HERE/'results-report.md').write_text(text,encoding='utf-8')
decision=dict(task_id=execution['task_id'],claim_status='SUPPORTED_INTERPRETATION',
    selected_exit='TEMPERATURE_DEFECTS_FOCUS_HEAT_INPUT_TIMING_AND_LEGAL_STATE_ESTIMATION',
    unique_next_action='聚焦热输入时序与合法状态估计；下一方案须以同信息传统物理估计为强基线，本轮不执行',
    not_authorized=['new_training','new_interpolation','closed_loop_feedback','PDE','experiment_calibration','publication'],
    numerical_facts_status='VERIFIED',tau_task=None,scientific_execution_complete=True,
    continuum_error_bounds=False,experimental_validation=False,PINN_increment=False,source_history_closed=True,
    source_step_sensitivity_not_confidence_interval=True)
(HERE/'decision.json').write_text(json.dumps(decision,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Wrote complete evidence report and one bounded next-action decision')
