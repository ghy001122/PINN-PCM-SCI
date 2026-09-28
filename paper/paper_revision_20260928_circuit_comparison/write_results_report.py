"""Render the completed comparison from saved scores; never fit or score again."""
from pathlib import Path
import csv,json,sys

HERE=Path(__file__).resolve().parent
RESULTS=HERE/'scoring-subset/results'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def table(headers,rows):
    return '\n'.join(['| '+' | '.join(headers)+' |','|'+'|'.join(['---']*len(headers))+'|']+['| '+' | '.join(map(str,r))+' |' for r in rows])
def write(p,text):p.write_text(text.strip()+'\n',encoding='utf-8')
r=read(RESULTS/'results.json')
pairs=list(csv.DictReader((RESULTS/'paired-comparison.csv').open(encoding='utf-8')))
lock=read(HERE/'comparison/predictions-locked.json')
exec_score=read(RESULTS/'execution-score.json')
independent=read(HERE/'build/independent-reproduction.json')
assert independent['status']=='PASS'
pairtable=table(['工况 / 器件','源步长 ns','器件 PCHIP→CS，μA','器件改善 Δ，μA','负载 PCHIP→CS，μA'],[
    [x['case']+'/'+x['device'],x['step_ns'],f"{float(x['device_PCHIP_RMS_uA']):.6f} → {float(x['device_CS_RMS_uA']):.6f}",
     f"{float(x['device_absolute_change_uA']):+.6f}",f"{float(x['load_PCHIP_RMS_uA']):.6f} → {float(x['load_CS_RMS_uA']):.6f}"] for x in pairs])
energyrows=[];peakrows=[];extremarows=[];sensitivityrows=[]
for rec in r['records']:
    for j,d in enumerate(rec['devices']):
        for method in ['PCHIP','CS']:
            e=rec['energy'][method];summary=e['interval_summary'][j]
            if rec['dt_s']==.5e-9:
                full=e['windows']['full'][j]
                energyrows.append([rec['case']+'/'+d['device'],method,f"{full['reference_nJ']:.6f}",f"{full['signed_error_nJ']:+.6f}",
                    f"{summary['sum_absolute_interval_error_J']*1e9:.6f}",f"{summary['max_absolute_interval_error_J']*1e9:.6f}"])
                pk=d['methods'][method]['peaks']['full'];pp=pk['pairs']
                peakrows.append([rec['case']+'/'+d['device'],method,f"{pk['reference_count']}/{pk['prediction_count']}",
                    'N/A' if pk['timing_RMS_s'] is None else f"{pk['timing_RMS_s']*1e9:.3f}",
                    'N/A' if not pp else f"{max(abs(x['signed_height_difference_A']) for x in pp)*1e3:.6f}"])
            if method=='CS':
                ex=d['methods'][method]['native_extrema']
                extremarows.append([rec['case']+'/'+d['device'],f"{rec['dt_s']*1e9:g}",
                    f"{ex['device_current_A']['minimum']*1e6:.6f}",f"{ex['power_W']['minimum']*1e3:.6f}",
                    ex['device_current_A']['negative_sample_count'],f"{ex['voltage_V']['minimum']:.6f} / {ex['voltage_V']['maximum']:.6f}"])
for x in r['sensitivity']:
    if x['method']=='CS' and x['branch']=='device_current':
        sensitivityrows.append([x['case']+'/'+x['device'],*[f'{x[k]*1e6:.6f}' for k in
            ['source_coarse_fine_RMS_A','error_curve_difference_RMS_A','reconstruction_curve_difference_RMS_A']]])
max_euler=max(abs(d['closure_error_J']) for rec in r['records'] for w in rec['Euler_energy'].values() for d in w)
max_euler_scaled=max(abs(d['closure_error_J'])/d['tolerance_J'] for rec in r['records'] for w in rec['Euler_energy'].values() for d in w)
max_pchip_scaled=max(abs(d['difference'])/d['tolerance'] for rec in r['pchip_reproduction'] for d in rec['details'])
body=f'''# 固定三次样条对照与焦耳能量时间分配：完成报告

**任务：** PCM-20260928-CUBIC-ENERGY-DISCRIMINATION-01。**状态：** 批准范围已完成；后续研究未启动。

## 1. 核心判断

**VERIFIED：**同样的197个电压观测改用固定not-a-knot三次样条，所得器件电流变化依工况而异。静息9 V的小误差进一步下降；抑制/A和B改善；12.5 V、15.8 V及激发/A和B恶化。这些角色各自的改善/恶化方向在两个保存步长一致，但不构成连续解收敛或总体成功率。负载电流的方向亦相同。没有按工况择优拼出第三种方法。

**VERIFIED：**CS在两种源步长的所有角色上都有保存时刻的负器件电流；动态角色也有负预测瞬时耗散。波形未裁剪。除静息外，全程能量绝对误差增大；196个区间的绝对误差总和却并非同步恶化。器件电流RMS、峰形、总能量与能量时间分配不能相互替代。

**SUPPORTED_INTERPRETATION：**这一个普通插值规则没有统一解决当前重构差距，且产生被动性方面的代价。它提高了后续比较的具体要求，但不代表所有传统平滑或状态估计失败，不证明二维热模型或PINN必要。总能量误差小，也不能认证温度、相态或迟滞历史。

**UNKNOWN：**绝对用途充分性、连续体精度、低阈值实验方法增量及内部热场质量。没有填入用途容差，没有执行新的PINN或条件热响应。

## 2. 固定输入和证据身份

基线为`9414c1da37cb9a101bf3ed812d248f63d4454470`，前轮科研成果为`fa475c257651c17fcfe83007ab0fe238c6c5995c`。五个作者模型工况、原1/0.5 ns保存轨迹共十个系统文件、十四个角色/步长比较；它们是已有开发记录上的追加对照，不是独立确认或真实材料实验。

CS只接收旧NPZ中的`observation_time`、`observation_voltage`、原生查询时间和已知Vin/C/RL。观测不重取，C=1.4534619293e−10 F、RL=12000 Ω，最后观测间隔32 ns。十套CS全部锁定后才打开源电流，原PCHIP预测不重新拟合。见[预测锁定](comparison/predictions-locked.json)、[固定配置](../../configs/cubic_energy_comparison_20260928.json)和[评分输入映射](scoring-subset/config.json)。无第三方法、第三步长、参数或采样扫描；实验CSV数值均未打开，4.1/3.9 V封存。

## 3. 全部配对电流结果

完整0–20 μs含两端，原生轴归一化梯形权重。Δ=E_PCHIP−E_CS，正数表示CS的该项RMS较小。固定1 mA归一值、最大差、有符号均值、两辅助窗口与双器件等权MSE联合值都保存在结果中；下表优先给绝对量。静息的极小误差变化不包装成重大实用收益。

{pairtable}

[完整精度配对表](scoring-subset/results/paired-comparison.csv) · [完整波形指标](scoring-subset/results/waveform-metrics.csv) · [全部结构化结果](scoring-subset/results/results.json)。没有新胜出门，也不把10 μA/2 μA当作本包资格线。

## 4. 峰形与异常不能被RMS或峰数掩盖

以下为0.5 ns来源的全段摘要；两步长全部峰列表、匹配差与未配对峰在JSON中。原检测器及0.25 μs匹配约定不变，无峰时序为N/A。所有有峰角色两方法保留原峰数和配对数量，但CS的峰高误差与峰时RMS在此细步来源的各动态角色均增大：抑制两器件RMS改善，并不意味着峰形同向改善。

{table(['角色','方法','原/预测峰数','配对峰时RMS ns','最大峰高绝对差 mA'],peakrows)}

以下异常只在保存查询时刻检查；没有声称连续全区间无过冲或无负值。9 V的负值很小，仍如实列出，不解释成真实器件反向导通。

{table(['角色','源步长 ns','最小器件电流 μA','最小功率 mW','负电流样本数','电压最小/最大 V'],extremarows)}

预先具名的12.5 V/A展示见[完整波形](figures/circuit-waveform-single_12p5V-A.png)及[首峰局部图](figures/circuit-waveform-single_12p5V-A-first-peak.png)。局部窗口固定为粗源第一参考峰2.612 μs附近±0.25 μs，两步长使用同一物理时间窗口；只有电压面板画观测点，窗口不改变全程评分。

## 5. 焦耳能量：总量、时间分配和相消

预测使用同一连续分段三次电压p：W=∫(Vin·p−p²)/RL dt−C[p(b)²−p(a)²]/2，逐真实多项式片段解析积分六次项p²。参考使用保存同层功率V·I_D的分段线性精确积分；非原生节点边界先在**功率**上分割。两者差同时含重构误差和原保存离散因素，不作为连续热力学误差认证。

下面的0.5 ns源结果用nJ显示。Σ|ΔW_j|衡量196个固定区间上的绝对能量差累计；它不是瞬时功率L1误差。总误差可能由正负区间相消。最后32 ns区间保留。两步长、全/前半/后半三窗口及197边界累计量完整输出。

{table(['角色','方法','参考总W nJ','总ΔW nJ','区间绝对误差之和 nJ','最大区间绝对误差 nJ'],energyrows)}

例如12.5 V细步，器件电流RMS从211.451变为217.760 μA；总能量误差从−0.010824变为−0.025929 nJ，但Σ|区间ΔW|从0.080346小幅变为0.079453 nJ。15.8 V细步器件RMS恶化明显，Σ|区间ΔW|却从0.024695降至0.020650 nJ。抑制/A细步器件RMS下降21.803 μA，Σ|区间ΔW|小降，但总误差绝对值增大。以上是目标量不同的实际表现，不进行替代成功判定。

[三个窗口能量](scoring-subset/results/energy-windows.csv) · [全部196区间](scoring-subset/results/energy-intervals.csv) · [累计能量误差](scoring-subset/results/energy-cumulative.csv) · [电荷](scoring-subset/results/charge-metrics.csv)。电荷、焦耳耗散、电容储能、源能量和负载耗散保持不同身份；本轮没有把电容储能再加为热源。

## 6. 数值资格与可分辨范围

继承成功源码的KCL、κ、A+B+X+K、原电荷、权重和峰函数保持不变；CS与PCHIP均通过对应工程检查。分解继续在非终点子网格重新归一，主RMS继续含终点。B为导数平方项，X/K带符号；完整[分解表](scoring-subset/results/error-decomposition.csv)保留。此分解描述现有误差组成，不证明热先验可消除它。

新增Euler能量左和核对保留 +CΣ(Δv)²/2 离散项和 −Σh·v·κ。它不要求梯形参考满足左和恒等式，不把离散项当真实额外热源。全部三窗口通过；最大闭合缺陷为{max_euler:.6g} J，最大缺陷/固定工程容差为{max_euler_scaled:.6g}。[Euler记账](scoring-subset/results/euler-energy.csv)。

下面三列均在共同1 ns轴上使用梯形权重，列出CS器件支路，单位μA。误差曲线差、重构曲线差与源波形差分别保存；PCHIP和负载支路完整值见[敏感性表](scoring-subset/results/step-sensitivity.csv)。

{table(['角色','原电流粗细差RMS','各自重构误差曲线差RMS','重构电流曲线差RMS'],sensitivityrows)}

当前配对差能在指定保存记录与FP64口径下复算；两步长方向一致只能支持这个有限离散范围的方向稳定。12.5 V源电流粗细差约39.72 μA，不能由重构误差变化较小宣称已达2 μA连续精度。所有步长差均不是统计置信区间或连续误差上界。

旧PCHIP波形标量与历史分数在预先固定的64ε运算尺度内一致，最大标准化差{max_pchip_scaled:.6g}；峰结果精确一致。跨平台点积最后几位差异没有修改旧科学阈值或布尔裁决。新包第一次评分与独立目录评分的完整结果JSON逐值精确一致。

## 7. 独立复算、成稿和数据处理

最小子集含十条原始time/V/三支电流、原有限观测、两种锁定预测及多项式、来源/单位和实际评分入口。原波形直接裁自保存来源，非预测反造。共享time/观测/参考数组每系统只存一次。包内没有T/R/H、低阈值实验CSV或求解器；不调用旧24.6 GB全包。

[独立运行记录](build/independent-reproduction.json)确认在工作区外目录运行一次，研究仓库文件读取被审计钩子拒绝，既有Python虚拟环境作为依赖例外保留；指定输入暂缺时立即报错，不回退旧绝对路径。38个输入/代码文件合计{independent['copied_bytes']/1024**2:.2f} MiB。见[可移交子集入口](scoring-subset/README.md)。这验证本包保存数组重评分能力，不等于神经AD重算或旧稿全场P03闭合。

实际CPU成本：CS十系统预测{lock['elapsed_seconds']:.3f} s；首次完整评分{exec_score['elapsed_seconds']:.3f} s；独立复制、受隔离评分及缺输入检查共{independent['elapsed_seconds']:.3f} s。仅十次CS拟合，旧PCHIP拟合零次；两次评分分别为正式分析与要求的独立复算。GPU未启动，无关机动作或远端计算。本地新交付待下次获准实例会话同步，不为同步启动GPU。

本轮[主稿](manuscript.pdf)只更新发布身份和真实访问状态；完整补充沿用[既有58页版本](../paper_revision_20260927_circuit_screen/supplement.pdf)。[修改说明](revision-notes.md)、[构建依赖](build-dependencies.json)和[访问方案](data-access-plan.md)记录实际能力。没有Git提交/推送、DOI、数据公开、投稿或作者联系。

## 8. 唯一优先下一动作

**SUPPORTED_INTERPRETATION／PROPOSED_NOT_AUTHORIZED：**使用本轮[测量澄清草稿](measurement-request-draft.md)，取得五条低阈值开发记录的可核验接线、通道/驱动与C/RL说明。当前尚不能把理想电路算子安全映射到这些实验，因此这项输入闭合最直接改变可执行任务，而不是继续枚举插值器或立即启动PINN。草稿尚未发送；来源缺项见[逐项状态](measurement-source-status.md)。仅C缺失时的积分校准属于另行批准的后续任务。

后续若提出热/迟滞状态估计，应让传统方法与PINN共享合法物理与观测。已知线性热模型中的无显式电压求导变量变换，仅为条件模型的代数设计线索；本轮没有运行它，不能用来声称内部场准确。动态RC训练期接口相对共同事后重放的增量仍是待检验假设，4000/800预算未启动。

## 9. 来源与完整图件

方法接口：[SciPy 1.14.1 CubicSpline官方文档](https://docs.scipy.org/doc/scipy-1.14.1/reference/generated/scipy.interpolate.CubicSpline.html)。参数与保存规则沿用[原冻结合同](../paper_revision_20260927_circuit_screen/evidence/core-revision/vo2/frozen-config.json)，作者代码固定于217d4f0ed6bfc680240021b07142a121cb4963d1；原文[Qiu et al., DOI 10.1002/adma.202306818](https://doi.org/10.1002/adma.202306818)。标准样条、能量恒等式与误差整理不作为原创原理。

新评估来源为[Review_and_Next_Plan](review-and-next-plan.md)与[补充研究方案](research-improvement-plan.md)，执行以[本轮明确指令](instructions.md)为准；旧PLAN_Review_Amendments属于上一轮PCHIP任务，不覆盖本轮明确新增一个CS的授权。
'''
for case,dev in [('single_9V','A'),('single_12p5V','A'),('single_15p8V','A'),('pair_excitation','A'),('pair_excitation','B'),('pair_inhibition','A'),('pair_inhibition','B')]:
    body+=f'\n- {case}/{dev}：[完整波形](figures/circuit-waveform-{case}-{dev}.png) · [能量分配](figures/circuit-energy-{case}-{dev}.png)\n'
write(HERE/'results-report.md',body)
write(HERE/'scoring-subset/README.md',r'''# 固定CS/PCHIP与能量评分子集

本目录可整体复制到独立位置；已经实际完成一次隔离评分。评分入口只对保存数组重评分，不重新拟合；包内附固定CS预测及合成测试代码，无ODE/PDE或神经推理/AD能力。输入是本项目已有作者模型数值复算数据，不是第三方实验CSV。P03外部访问仍开放，当前未公开。

在本目录运行（Python3.11、NumPy2.1.1、SciPy1.14.1）：

```powershell
python scripts/run_cubic_energy_comparison.py --root . --config config.json --mode score
python -m unittest discover -s tests -p "test_cubic_energy_comparison.py" -v
python -m unittest discover -s tests -p "test_circuit_energy_tools.py" -v
```

`inputs/`每个系统保存一次time、voltage、device/load/capacitor_current与observation_time/voltage；角色在同一数组的列上。`predictions/PCHIP`和`predictions/CS`分别保存锁定预测、电压导数、三支电流、多项式系数/断点/时间变换；运行时与共享输入合并字段，不重新拟合。config逐个声明十个系统的设备角色、SI单位、C/RL/Vin及身份。缺输入报错，无历史绝对路径回退。provenance原路径是来源说明，不作可执行回退。

`results/`含全部波形、峰、分解、电荷、能量和敏感性；undefined值用null。`expected-pchip-results.json`用于核对历史标量及峰。两方法全段/两个辅助窗口均报告，能量另含196个固定观测区间。不生成温度或迟滞，不评价实验CSV。基线1/0.5ns是保存来源步长，不是重复实验。

代码来源为本项目现有评分函数及明确新增能量函数；原参数/离散实现来自Qiu论文和作者仓库217d4f0ed6bfc680240021b07142a121cb4963d1。代码许可见所附LICENSE（若分发时改变代码集合，须随同保留相应来源）。第三方实验数据和出版社图片未包含；代码许可不自动授权这些第三方资产。数值子集的外部发布/接收及相应数据许可由项目作者另行确认。

本目录中的预测和源数组保持FP64及全部原生时间点；不应为节省空间降精度或删点。实际输入和代码传输清单见transfer-manifest.json；它记录独立评分时复制的输入集合，后来追加的报告/结果不冒称已经包含在那次输入传输中。
''')
write(HERE/'README.md',f'''# 固定样条对照、焦耳能量辨别与现稿收口

**PCM-20260928-CUBIC-ENERGY-DISCRIMINATION-01 已完成批准范围。**十套CS预测锁定一次，十四条角色/步长与PCHIP比较完成；没有新系统轨迹、神经训练、实验CSV读取、GPU或外部发布。

**VERIFIED：**CS对抑制两个角色的器件RMS较小，对12.5V、15.8V和激发两个角色较大；静息极小误差改善。各角色方向在两来源步长一致，CS产生保存时刻负电流/负耗散；电流RMS、总能量及区间能量不能互相认证。**UNKNOWN：**绝对用途充分性、连续真解与实验/内部状态增量。

| 交付 | 入口 |
|---|---|
| 完整结果、14行配对及唯一下一动作 | [研究报告](results-report.md) |
| 全精度指标与预测 | [配对CSV](scoring-subset/results/paired-comparison.csv) · [JSON](scoring-subset/results/results.json) · [CS锁定记录](comparison/predictions-locked.json) |
| 最小可移交评分子集 | [运行说明](scoring-subset/README.md) · [独立验证](build/independent-reproduction.json) |
| 实际预测、测试、评分命令 | [执行与复算](run-and-reproduce.md) |
| 新主稿，17页 | [PDF](manuscript.pdf) · [DOCX](manuscript.docx) · [Markdown](manuscript.md) |
| 未改动的完整补充，58页 | [已有PDF](../paper_revision_20260927_circuit_screen/supplement.pdf) · [已有DOCX](../paper_revision_20260927_circuit_screen/supplement.docx) |
| 测量澄清准备，未发送 | [英文草稿](measurement-request-draft.md) · [来源缺项](measurement-source-status.md) |
| 实际交付边界 | [修改说明](revision-notes.md) · [构建](build-and-reproduction-manuscript.md) · [访问方案](data-access-plan.md) · [数据处理](data-handling-record.json) |

独立目录评分与首次完整结果精确一致；旧PCHIP与历史标量保持FP64运算尺度一致，峰精确一致。研究仓库输入访问被实际拒绝，缺输入会报错。唯一建议是先取得具名实验记录的测量接线与参数说明；任何校准、物理状态估计或PINN pilot仍需另行批准。P02、严格双周期、材料/泛化及P03未因本轮关闭。
''')
print('Wrote reports and transferable subset usage from saved results only')
