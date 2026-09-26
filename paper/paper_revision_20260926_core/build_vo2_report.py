"""Report saved author-model trajectories and header-only literature inventory."""
from pathlib import Path
import csv,io,json,re,zipfile
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
RUN=ROOT/'outputs/runs/20260926-core-revision-vo2-bridge/vo2'
def save(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
def table(headers,rows):return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+['| '+' | '.join(map(str,row))+' |' for row in rows])

def assets():
    rows=[]
    with zipfile.ZipFile(HERE/'literature/data.zip') as z:
        for name in z.namelist():
            if not name.endswith('.csv'):continue
            with z.open(name) as source:
                stream=io.TextIOWrapper(source,encoding='utf-8-sig');meta=[]
                for line in stream:
                    row=next(csv.reader([line]))
                    if row and row[0]=='TIME':raw_header=row;break
                    meta.append(row)
                actual_rows=sum(1 for line in stream if line.strip())
            channels=[label.strip() for label in raw_header if label.strip()]
            channel_columns={label.strip():i for i,label in enumerate(raw_header) if label.strip()}
            header={row[0]:row[1:] for row in meta if len(row)>1 and row[0]}
            dt=float(header['Sample Interval'][0]);n=int(header['Record Length'][0]);assert n==actual_rows
            devices=re.findall(r'(1[A-Z][0-9])_12[kK]_([0-9.]+)V',name)
            pair='thermal_coupling' in name
            mapping={'CH1':'device_A_voltage','CH2':'A_50ohm_shunt_voltage','CH3':'B_50ohm_shunt_voltage','CH4':'device_B_voltage'} if pair else {'CH3':'50ohm_shunt_voltage','CH4':'device_voltage'}
            voltages=tuple(float(v[1]) for v in devices)
            panel={(2.6,2.6):'5a',(4.,2.6):'5b',(5.,2.6):'5c',(4.1,3.7):'5d',(4.1,3.9):'5e',(4.1,4.):'5f'}.get(voltages) if pair else '1c'
            rows.append(dict(archive_member=name,evidence='EXPERIMENTAL_OSCILLOSCOPE_RECORD',
                source_work='Collective dynamics and long-range order in thermal neuristor networks',
                source_version='arXiv:2312.12899v1, as linked by the pinned repository README',
                figure='Fig.5 group' if pair else 'Fig.1c group',possible_panel_by_protocol=panel,
                exact_trace_linkage='UNKNOWN; repository figure group and protocol metadata only, no waveform matching',
                paper_device_label_alignment='UNRESOLVED: fixed-4.1-V files name 1E3 first; paper Fig.5d-f labels the fixed-4.1-V device B' if pair and voltages[0]==4.1 else 'protocol metadata compatible; individual figure device IDs not supplied',
                sample='Ben012_1',devices=[v[0] for v in devices],source_voltages_V=[float(v[1]) for v in devices],
                source_voltage_provenance='original filename; not a measured complete Vin waveform',
                base_temperature_K=325,load_resistance_ohm=[12000]*len(devices),
                capacitance='UNKNOWN for this record; 145.34619293 pF is an author fitted model parameter, not a per-file measurement',
                sample_interval_s=dt,record_length=n,verified_data_rows=actual_rows,channels=channels,
                original_header=raw_header,zero_based_columns=channel_columns,
                channel_meaning=mapping,raw_vertical_units='V',current_branch_relative_to_capacitor='UNKNOWN',
                current_conversion_author_instruction='shunt voltage / 50 ohm',device_current_scoring_eligible=False,
                data_use_this_round='header, channel and provenance qualification only; no fitting or waveform scoring',
                proposed_split='COMPLETE_PROTOCOL_HOLDOUT_NOT_SCORED' if pair and [float(v[1]) for v in devices]==[4.1,3.9] else 'development/source qualification',
                license='code MIT retained; experimental-data redistribution rights not established'))
    save(HERE/'literature/data-assets.json',dict(records=rows,code_commit='217d4f0ed6bfc680240021b07142a121cb4963d1',
        field_blindness='No held-out waveform metric or parameter fit in this round',publicly_released=False))
    return rows

def main():
    report=json.loads((RUN/'report.json').read_text());asset=assets();(HERE/'figures').mkdir(exist_ok=True)
    rows=[];wave=[];end=[];event=[]
    plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False,'savefig.dpi':180})
    for c in report['cases']:
        name=c['case']['id'];a=np.load(RUN/(name+'-1ns.npz'));b=np.load(RUN/(name+'-0p5ns.npz'))
        fig,axes=plt.subplots(4,1,figsize=(8.2,8.7),sharex=True,constrained_layout=True)
        for j,d in enumerate(c['devices']):
            label='AB'[j];color=('#1565c0','#bf360c')[j]
            for ax,key,scale,title in zip(axes,('voltage','device_current','temperature','resistance'),(1,1e3,1,1e-3),('Device voltage (V)','Device current (mA)','Temperature (K)','Resistance (kOhm)')):
                ax.plot(b['time']*1e6,b[key][:,j]*scale,color=color,label=label+' / 0.5 ns',lw=1.1)
                ax.plot(a['time']*1e6,a[key][:,j]*scale,color=color,linestyle='--',alpha=.7,label=label+' / 1 ns',lw=.8)
                ax.axvline(10,color='.65',ls=':',lw=.8);ax.set_ylabel(title);ax.grid(alpha=.15)
            e=d['events']['full'];tail=d['events']['tail'];wi=d['waveforms']['device_current']
            peakdiff=e['paired_peak_time_differences_s']
            rows.append([name,label,c['case']['figure'],f"{e['coarse']['count']} / {e['fine']['count']}",
                f"{tail['coarse']['count']} / {tail['fine']['count']}",tail['fine']['functional_description'],
                f"{wi['unaligned_rms']*1e3:.6g}",f"{100*wi['relative_rms']:.6g}",
                f"{max(map(abs,peakdiff))*1e9:.6g}" if peakdiff else 'N/A'])
            for key,v in d['waveforms'].items():wave.append(dict(case=name,device=label,field=key,**v))
            for key,v in d['end_state'].items():end.append(dict(case=name,device=label,field=key,**v))
            for interval,values in d['events'].items():
                for step in ('coarse','fine'):
                    for k,(t,h) in enumerate(zip(values[step]['times_s'],values[step]['heights_A'])):
                        event.append(dict(case=name,device=label,interval=interval,step=step,ordinal=k+1,time_s=t,height_A=h))
        axes[0].legend(ncol=4,fontsize=8);axes[-1].set_xlabel('Time (microseconds)')
        axes[0].set_title(name+' | original time axis; no peak alignment')
        fig.savefig(HERE/'figures'/('vo2-'+name+'.png'));plt.close(fig)
    for name,values in [('vo2-waveform-differences',wave),('vo2-end-states',end),('vo2-peak-records',event)]:
        with (HERE/'tables'/(name+'.csv')).open('w',newline='',encoding='utf-8') as f:
            w=csv.DictWriter(f,fieldnames=list(values[0]));w.writeheader();w.writerows(values)
    summary=table(['Case','Device','Source figure','Full peaks 1/0.5 ns','Tail peaks 1/0.5 ns','Tail description','I RMS difference (mA)','I relative RMS (%)','Maximum paired peak-time difference (ns)'],rows)
    (HERE/'tables/vo2-summary.md').write_text(summary+'\n',encoding='utf-8')
    inventory=table(['Record','Devices','Source voltage (V)','Channels','Samples','Use'],[[Path(v['archive_member']).name,','.join(v['devices']),str(v['source_voltages_V']),','.join(v['channels'][1:]),v['record_length'],v['proposed_split']] for v in asset])
    max_energy=max(v['max_corrected_energy_defect_J'] for v in report['step_records'])
    max_kcl=max(v['max_KCL_defect_A'] for v in report['step_records'])
    text='''# VO₂ 作者模型五工况复现报告

任务：`PCM-20260926-CORE-REVISION-VO2-BRIDGE-01`。本报告属于文献模型桥接，独立于旧合成 PINN 的材料身份。

**VERIFIED：**五工况各运行 1 ns 和 0.5 ns 两步长，共 300,000 个系统步，无第三步长、追图拟合或参数扫描。十条记录均保存同层 V/T/R、器件／负载／电容电流、绝缘分数和完整滞回历史。两步长末段标签一致；数值敏感性不能替代定量复现容差或实验验证。

## 来源与模型合同

物理工况采用 Qiu 等发表主文、[预印本 v2 及其补充](https://arxiv.org/pdf/2307.11256v2)，实现绑定[固定作者代码](https://github.com/yuanhangzhang98/collective_dynamics_neuristor/tree/217d4f0ed6bfc680240021b07142a121cb4963d1)。该代码仓库的 README 对应 Zhang 等后续论文 [Collective dynamics and long-range order in thermal neuristor networks](https://arxiv.org/abs/2312.12899v1)，将 Qiu 论文列为相关前作；它不是专属 Qiu 图件的复现仓库。此次按已批准合同采用其中的滞回实现，同时保留 Qiu 补充的双节点热拓扑，不引入后续阵列或噪声设置。已保存源文件、下载身份与 MIT 代码许可。Qiu 预印本补充 S3 印刷表达式缺少代码中的 atanh；此次明确遵循代码，未默改公式。出版方最终补充文件未单独取得，不能声称其与预印本补充完全相同。

RC 方程为 C dv/dt=(Vin−v)/RL−v/R；器件热源为 v²/R。单节点 Cth dT/dt=v²/R−Sth(T−Tb)。双节点 Cth dTi/dt=vi²/Ri−(1−η)Sth(Ti−Tb)−ηSth(Ti−Tj)，采用补充 S8/S9 的双节点定义，未混用阵列邻居数形式。g 为模型**绝缘分数**，不等同旧 PINN 的相态变量。

全部内部量使用 SI：R0=0.00535882879 Ω，Ea=5220.47417 K，β=0.252796285 K⁻¹，w=7.19357064 K，Tc=332.805839 K，γ=0.956269682；静态 Rm0=262.5 Ω，动态乘 k=4.90025335。C=145.34619293 pF，Cth=49.62776831 pJ/K，Sth=0.20558726 mW/K，RL=12 kΩ。ns、kΩ、pF 到 SI 分别乘 10⁻⁹、10³、10⁻¹²；宽度与热容倍率 1，噪声 0。

每一工况独立初始化 v=0、T=325 K；滞回对象从 324.9 K 的升温支路、未反转状态按作者公式生成。保留 305–370 K 的本构／历史计算裁剪、0.01 K 状态向量触发、Tpr+10⁻⁶ K 分母和作者向量历史顺序。每步先在 tn 更新历史，再计算 Rn/电流/RHS、保存同层量，最后同步 Euler 推进；终点只读出。实际温度状态不被裁剪。

## 结果与数值限制

检测器只作用于器件电流：阈值 1.5 mA，最小间隔 0.5 μs，近峰保留较高者、同高留较早者；无平滑、峰对齐或时间扭曲。完整 0–20 μs 与固定瞬态 0–10 μs、末段 10–20 μs 分开保存。无峰时结合 g/R/T 描述所在分支；标签不认证严格平衡。

'''+summary+'''

**SUPPORTED_INTERPRETATION：**单器件绝缘／金属分支占据和振荡，以及双器件的阈上激发／抑制行为与相应作者模型用途定性相容。表中的 NO_DETECTED_PEAKS_* 仅描述“未检测到峰及所在分支”，不能作为锁定或静息已收敛的认证。**UNKNOWN：**缺少可靠统一的波形／实验容差，故不宣布定量复现成功。正式论文 Fig.2C 的图注描述两个初始尖峰；15.8 V 在本轮冻结检测规则下产生三个瞬态峰，该差异明确保留，未通过改变初态、阈值或参数消除。公开原始包中另有标为单尖峰的 17 V 文件，它不是这一 15.8 V 工况。振荡曲线对纳秒尺度位相差敏感，未对齐电流 RMS 差仍达百分数量级。

抑制工况的 B 器件在末段虽无 1.5 mA 检测峰、且始终处于金属分支，细步电流峰峰值仍为 0.105775 mA、温度范围约 3.08121 K，并有低幅调制；其静息／锁定功能分类保留为 **TRANSITION_OR_UNRESOLVED**，只支持“阈上尖峰受抑制”。9 V 与 15.8 V 的细步末段温度峰峰值分别约 5.374e-5 K、2.895e-5 K，实际变化照报，不虚设平衡容差。该解释收紧来自已保存数组，未改变检测器、参数或轨迹。

9 V 最高温度约 331.11 K；其余工况计算温度峰值约 377.6–398.9 K，超过作者本构计算的 370 K 裁剪上界。此处保留作者代码的“温度继续演化、本构输入裁剪”行为，不把该温区当作材料模型已验证范围。

完整 V/I/T/R 波形 RMS、最大差、相对差，以及全段／末段峰时、频率、峰高和未配对峰在运行 `report.json` 中；表格文件保留逐峰记录和包括 Tr/gr/Tpr/T_last 的末态差。相对 RMS 的分母是细步原始波形 RMS。缺峰频率和峰时为 null/N/A。

工程检查通过：常电导 RC、零输入放电、作者反转处理和双节点热交换抵消。最大 KCL 差为 '''+f'{max_kcl:.4g} A'+'''。显式 Euler 的电容离散能量项 ½C(Δv)² 单列后，最大每步能量闭合差 '''+f'{max_energy:.4g} J'+'''；这验证离散记账，不认证连续误差。运行成本及每步长温度范围详见原始报告。

## 数据证据资格

Fig.2A/B/C 是实验及其作者拟合模拟；本轮在其 9/12.5/15.8 V 模拟设置上复算，不能称盲验证。Fig.S11D 的 11/9.4 V、η=0.12 和 Fig.S13D 的 11/14 V、η=0.1 均为作者模拟，不能冒充 Fig.5 不同低电压器件的实验复现。

固定仓库 README 将 `data.zip` 明确归于**后续 Collective dynamics 论文的 Fig.1 与 Fig.5**。其单器件 9/11/13/15/17 V 记录与该文 Fig.1c 的协议集合一致，不是 Qiu Fig.2 的 12.5/15.8 V 原始记录。双器件属于后续论文 Fig.5 的低阈值实验，不能直接套用高阈值拟合参数。下表仅按原始文件名、通道头及作者 data conventions 建立资产身份，未对未来完整留出波形评分。

后续论文 Fig.5d–f 把固定 4.1 V 的器件标为 B，而原文件把 1E3/4.1 V 列在前、1E2/3.7–4.0 V 列在后；图件字母与原文件／通道身份尚需闭合。仅按电压集合可关联候选图版，不因此认证同一条原始曲线，也不静默交换设备。留出继续固定原文件的 1E3=4.1 V、1E2=3.9 V。[来源图注及附录 B](https://arxiv.org/pdf/2312.12899v1)

'''+inventory+'''

所有通道原始单位均为 V，采样间隔 3.2 ns。作者说明 50 Ω 两端压降应除以 50；但测量支路相对并联电容的位置尚未从可得材料确认，因此支路为 **UNKNOWN**，本轮不把它直接作为 Idevice 评分。模型始终区分 Iload=(Vin−v)/RL、Idevice=v/R、IC=C dv/dt，且 Iload=Idevice+IC。每文件器件、电源、负载、通道、样本数和适用性见 `literature/data-assets.json`。原始第三方实验资产留在研究副本；MIT 代码许可不自动覆盖实验数据再发布。

## 对下一研究的具体约束

作者 Cth 是 VO₂、金属和衬底共同贡献的有效拟合热容；补充材料给出的裸 VO₂ 热容仅约其 1/3000。不能将该有效值直接当作 100 nm 薄膜的本征体积热容。器件几何、500 nm 热耦合间距、衬底与电极信息可支持未来二维合同，但不足以自动闭合热边界或低阈值器件参数。

唯一后续建议：先完成有限观测重构 pilot 的输入资格——测量支路、器件参数适用性、初始历史及二维热合同；资格闭合后再审查候选与强基线的有限预算。当前不运行该 pilot、不新增二维求解，不以本轮集总复现替代新 PINN 方法证据。

## 未对齐物理波形

'''
    for c in report['cases']:
        name=c['case']['id'];text+=f'![{name}: two fixed Euler steps on the same time axis.](figures/vo2-{name}.png)\n\n'
    (HERE/'vo2-author-reproduction.md').write_text(text,encoding='utf-8')
    print('VO2_REPORT_AND_ASSET_HEADERS_COMPLETE')
if __name__=='__main__':main()
