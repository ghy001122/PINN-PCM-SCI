"""Render scientific diagnostics and the completed development report from records."""
from pathlib import Path
import csv
import json
import textwrap
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
RUN=ROOT/'outputs/runs/20260923-relative-phase-moments'
FIG=HERE/'figures';FIG.mkdir(parents=True,exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.spines.top':False,
                     'axes.spines.right':False,'savefig.bbox':'tight','pdf.fonttype':42})


def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))


def save(fig,name):
    fig.savefig(FIG/(name+'.png'),dpi=180)
    fig.savefig(FIG/(name+'.pdf'))
    plt.close(fig)


def csv_file(name, rows):
    columns=list(dict.fromkeys(k for row in rows for k in row))
    with (HERE/name).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=columns);w.writeheader();w.writerows(rows)


def flatten(value, prefix=''):
    result={}
    for k,v in value.items():
        key=prefix+k
        if isinstance(v,dict):result.update(flatten(v,key+'/'))
        elif isinstance(v,(list,tuple)):result[key]=json.dumps(v,ensure_ascii=False)
        else:result[key]=v
    return result


def results():
    """Pure saved-record rendering: never read models or choose a scientific route."""
    if not (RUN/'scoring/results.json').exists():return
    scores=read(RUN/'scoring/results.json');audit=read(RUN/'endpoint-audits.json')
    arms=['D','P','L','R','I','RI','RIM','G'];metrics=['S','Ephi','ET','EI','EV','bottom_current_NRMSE','power_trace_NRMSE']
    records=scores['records'];windows=scores['windows'];pairs=scores['comparisons']
    terminal=read(RUN/'all-endpoints-locked.json')['arms']
    cost=[];quad=[];moment_rows=[]
    for arm in arms:
        v=terminal[arm];s=v['statistics'];a=audit['arms'][arm]
        cost.append(dict(arm=arm,adam_updates=v['adam_updates'],lbfgs_evaluations=v['lbfgs']['evaluations'],
            lbfgs_accepted_steps=v['lbfgs']['accepted_steps'],training_seconds=v['elapsed_seconds'],
            **s['electrical'],**s['phase_work'],**s['model_work'],
            readout_seconds=read(RUN/'predictions'/arm/'prediction.json')['elapsed_seconds']))
        for kind,q in a['quadrature_comparison'].items():quad.append(dict(arm=arm,target=kind,**q))
        value=a['quadrature']['32']['values']
        moment_rows.append(dict(arm=arm,order=32,raw_zeroth_square_over_point=(2*value['Iphi']-value['Pphi'])/value['Pphi'],
            relative_zeroth_square_over_point=(2*value['Izeta']-value['Pzeta'])/value['Pzeta'],
            relative_first_square_over_point=2*(value['Mzeta']-value['Izeta'])/value['Pzeta'],
            relative_I_over_P=value['Izeta']/value['Pzeta'],relative_M_over_P=value['Mzeta']/value['Pzeta']))
    csv_file('actual-training-cost.csv',cost)
    csv_file('endpoint-quadrature.csv',quad)
    csv_file('endpoint-moment-energy.csv',moment_rows)
    used_path=RUN/'endpoint-used-order-audit.json'
    used=read(used_path) if used_path.exists() else None
    if used:
        csv_file('endpoint-used-order.csv',[dict(arm=arm,target=kind,**q)
            for arm,d in used['arms'].items() for kind,q in d['comparison_8_to_16'].items()])
    csv_file('all-metrics.csv',[dict(arm=arm,scope=scope,**windows[arm][scope]['metrics'])
        for arm in arms for scope in ('window','outside','full')])
    csv_file('full-readout-metrics.csv',[dict(arm=arm,**r['metrics']) for arm,r in records.items()])
    csv_file('both-cycle-events.csv',[dict(arm=arm,**c) for arm,r in records.items() for c in r['cycles']])
    csv_file('all-pairwise-decisions.csv',[dict(comparison=name,**flatten(v)) for name,v in pairs.items()])
    csv_file('raw-physics-audit.csv',[dict(arm=arm,quadrature_pass=audit['arms'][arm]['quadrature_pass'],
        **audit['arms'][arm]['raw']) for arm in arms])
    colors=['#59636C','#2E6799','#BA7635','#7E63A2','#628C51','#BC638D','#087F78','#9D7658']
    x=np.arange(8)
    fig,axes=plt.subplots(3,3,figsize=(13.5,10.5),layout='constrained')
    for ax,key,title in zip(axes[0,:2],['Ephi','S'],['(a) Missing-window phase error','(b) Full-domain set error in W']):
        scale=1000 if key=='S' else 1
        vals=[scale*windows[a]['window']['metrics'][key] for a in arms]
        ax.bar(x,vals,color=colors);ax.set(xticks=x,xticklabels=arms,ylabel='1000 × S' if key=='S' else key,title=title)
        ax.set_ylim(0,max(vals)*1.18)
        for i,v in enumerate(vals):ax.text(i,v,f'{v:.3g}',ha='center',va='bottom',fontsize=7)
    ax=axes[0,2]
    ratios=[]
    for key,marker in [('ET','o'),('EI','s'),('EV','^')]:
        values=[windows[a]['window']['metrics'][key]/windows['D']['window']['metrics'][key] for a in arms]
        ratios.extend(values);ax.plot(x,values,marker=marker,label=key,lw=1)
    ax.axhline(1,color='gray',ls='--',lw=.8)
    ax.set_ylim(min(.9,min(ratios)*.98),max(1.1,max(ratios)*1.02))
    ax.set(xticks=x,xticklabels=arms,ylabel='Error / D error (ratio)',title='(c) Temperature and electrical costs in W')
    ax.legend(frameon=False,fontsize=8)
    ax=axes[1,0]
    for key,marker in [('recall','o'),('precision','s'),('mass_ratio','^')]:
        ax.plot(x,[records[a]['cycles'][1][key] for a in arms],marker=marker,label=key,lw=1)
    ax.axhline(1,color='gray',ls='--',lw=.8)
    ax.set(xticks=x,xticklabels=arms,title='(d) Cycle 2: original event support',ylabel='Fraction / ratio')
    ax.legend(frameon=False,fontsize=8)
    ax=axes[1,1]
    with np.load(RUN/'scoring/active-error-traces.npz') as f:
        t=f['time'];ax.plot(t,100*f['reference_active'],color='black',lw=1.8,label='reference')
        for arm,color in zip(arms,colors):ax.plot(t,100*f[arm+'/active'],color=color,lw=1,label=arm)
    ax.axvline(1.36,color='gray',ls='--',lw=.8)
    ax.set(xlim=(1.01,2.02),title='(e) Cycle 2 active-area trajectory',xlabel='Time',ylabel='Full-domain active fraction (%)')
    ax.legend(ncol=3,fontsize=6.5,frameon=False)
    ax=axes[1,2]
    matrix=np.array([[100*(windows[a]['outside']['metrics'][k]/windows['D']['outside']['metrics'][k]-1)
                      for k in metrics] for a in arms])
    limit=max(float(abs(matrix).max()),5.)
    im=ax.imshow(matrix,cmap='RdBu_r',vmin=-limit,vmax=limit,aspect='auto')
    for i in range(8):
        for j in range(7):ax.text(j,i,f'{matrix[i,j]:+.1f}',ha='center',va='center',fontsize=6,
            color='white' if abs(matrix[i,j])>.6*limit else 'black')
    ax.set(xticks=range(7),xticklabels=['S','phase','T','I top','V','I bot','power'],yticks=x,yticklabels=arms,
           title='(f) Outside W: change from D (%)')
    ax.tick_params(axis='x',labelrotation=45)
    fig.colorbar(im,ax=ax,shrink=.75)
    ax=axes[2,0]
    ax.bar(x,[v['training_seconds']/60 for v in cost],color=colors)
    ax.set(xticks=x,xticklabels=arms,ylabel='Actual GPU training wall time (min)',title='(g) Fixed update budget, measured cost')
    ax=axes[2,1]
    raw_ratios=[]
    for key,marker in [('thermal','o'),('phase','s')]:
        den=audit['arms']['D']['raw'][key]
        values=[audit['arms'][a]['raw'][key]/den for a in arms];raw_ratios.extend(values)
        ax.plot(x,values,marker=marker,label=key,lw=1)
    ax.axhline(1,color='gray',ls='--',lw=.8)
    ax.set_ylim(min(.9,min(raw_ratios)*.98),max(1.1,max(raw_ratios)*1.02))
    ax.set(xticks=x,xticklabels=arms,ylabel='Raw audit loss / D',title='(h) Independent original-physics audit')
    ax.legend(frameon=False,fontsize=8)
    ax=axes[2,2];ax.axis('off')
    table=[]
    for a in arms:
        table.append([a,*['—' if a==b else ('pass' if pairs[a+'_vs_'+b]['A_w']['passed'] else 'fail') for b in ('D','P')],
            'pass' if records[a]['strict_device_pass'] else 'fail',
            'pass' if audit['arms'][a]['quadrature_pass'] else 'unresolved'])
    tab=ax.table(cellText=table,colLabels=['Arm','A_W / D','A_W / P','Strict','16/32'],loc='center',cellLoc='center')
    tab.auto_set_font_size(False);tab.set_fontsize(7);tab.scale(1,1.5)
    ax.set_title('(i) Gates are separate; one initialization')
    save(fig,'eight-arm-development')
    edges=[('R','P'),('R','L'),('I','P'),('RI','R'),('RI','I'),('RIM','RI'),('RIM','G'),('G','P'),('RIM','D'),('RIM','P')]
    labels=[f'{b} → {a}' for a,b in edges]
    fig,axes=plt.subplots(1,3,figsize=(12,6),layout='constrained',gridspec_kw={'width_ratios':[1.4,1,1.5]})
    yy=np.arange(len(edges))
    for delta,key,color,label in [(-.17,'S','#367EB2','S'),(.17,'Ephi','#B45E36','phase RMSE')]:
        value=[100*pairs[a+'_vs_'+b]['continuous_effects']['window'][key]['relative_error_reduction'] for a,b in edges]
        axes[0].barh(yy+delta,value,height=.31,color=color,label=label)
        for i,v in enumerate(value):axes[0].text(v,i+delta,f' {v:+.1f}%',ha='left' if v>=0 else 'right',va='center',fontsize=7)
    axes[0].axvline(0,color='gray',lw=.8);axes[0].axvline(10,color='gray',ls=':',lw=.8)
    axes[0].set(yticks=yy,yticklabels=labels,xlabel='W error reduction (%)',title='Direct controls: continuous effects')
    axes[0].invert_yaxis();axes[0].margins(x=.25);axes[0].legend(frameon=False,fontsize=8)
    guard=np.array([[int(pairs[a+'_vs_'+b]['A_w']['noninferior'][k]) for k in ('ET','EI','EV')] for a,b in edges])
    from matplotlib.colors import ListedColormap
    axes[1].imshow(guard,cmap=ListedColormap(['#F3B5B5','#E5F1E8']),vmin=0,vmax=1,aspect='auto')
    for i in range(len(edges)):
        for j in range(3):axes[1].text(j,i,'pass' if guard[i,j] else 'fail',ha='center',va='center',fontsize=8)
    axes[1].set(xticks=range(3),xticklabels=['T','I top','V'],yticks=yy,yticklabels=[],title='Original W noninferiority')
    axes[1].set_ylim(axes[0].get_ylim())
    axes[2].axis('off')
    rows=[]
    for a,b in edges:
        p=pairs[a+'_vs_'+b]
        flags=[k for k,v in p['outside_cost_flags'].items() if v]
        short={'Ephi':'phase','ET':'T','EI':'I top','EV':'V','bottom_current_NRMSE':'I bottom','power_trace_NRMSE':'power'}
        words=', '.join(short.get(k,k) for k in flags)
        rows.append([f'{b} → {a}','pass' if p['A_w']['passed'] else 'fail',textwrap.fill(words,22) if flags else 'none'])
    tab=axes[2].table(cellText=rows,colLabels=['Control → target','A_W','Outside-W costs'],loc='center',cellLoc='left',colWidths=[.35,.15,.5])
    tab.auto_set_font_size(False);tab.set_fontsize(7);tab.scale(1,2.2)
    axes[2].set_title('All named costs remain visible')
    save(fig,'mechanism-controls')
    text='# 八臂开发试验：完整结果\n\n'
    decision_path=RUN/'decision.json'
    if decision_path.exists():
        d=read(decision_path);text+=f"**{d['claim_status']} — {d['route']}**\n\n{d['summary_zh']}\n\n"
        text+=d.get('discussion_zh','')+'\n'
    else:text+='数值结果已完成；最终路由需逐项核对原门、独立raw审计和终点求积。\n\n'
    text+='同一个合法父态／seed29、原B1相态缺测条件；八个独立优化分支不是八个独立初始化。仅用既有原参考和共同160×80读出。W=[1.01,2.02]；S在全域积分，Ephi在原ROI计算。\n\n'
    text+='| 臂 | W Ephi | W S | W ET | W EI | W EV | A_W 对D／P | 严格双周期 |\n|---|---:|---:|---:|---:|---:|---|---|\n'
    for a in arms:
        m=windows[a]['window']['metrics'];g=['—' if a==b else str(pairs[a+'_vs_'+b]['A_w']['passed']) for b in ('D','P')]
        text+=f"| {a} | {m['Ephi']:.7g} | {m['S']:.7g} | {m['ET']:.7g} | {m['EI']:.7g} | {m['EV']:.7g} | {' / '.join(g)} | {records[a]['strict_device_pass']} |\n"
    text+='\n原A_W要求S与Ephi同时达到10%及各自绝对容差，且ET／EI／EV各自非劣；连续改善或单项通过均不替代原门。窗外七项代价、全轨迹A/B和严格双周期另列，不能合并成一项胜负。\n\n'
    text+='![八臂科学结果](figures/eight-arm-development.png)\n\n'
    text+='图中窗外色块报告相对D的连续百分比变化；实际代价标志仍使用原5%或绝对容差。raw审计在独立固定原残差池上执行，未用于调整端点。所有壁钟时间为此次单次测量，不是普遍加速比。第二周期事件onset、时差、recall、precision、mass ratio、recovery均见完整事件表。\n\n'
    text+='![机制直接对照](figures/mechanism-controls.png)\n\n'
    text+='箭头表示从控制到候选，正值是较小误差；没有统计显著性含义。RI相对R/I、一阶矩RIM相对RI与固定标量G分别检查，不能用总loss大小证明方法贡献。\n\n'
    text+='## 实际工作量\n\n| 臂 | Adam | 完整LBFGS评估 | 已接受LBFGS步 | 正解／伴随 | phase导数位置 | phase端点 | 训练分钟 |\n|---|---:|---:|---:|---|---:|---:|---:|\n'
    for c in cost:text+=f"| {c['arm']} | {c['adam_updates']} | {c['lbfgs_evaluations']} | {c['lbfgs_accepted_steps']} | {c['forward_solves']} / {c['adjoint_solves']} | {c['phase_derivative_positions']} | {c['phase_endpoint_queries']} | {c['training_seconds']/60:.2f} |\n"
    text+=f"\n训练合计{sum(c['forward_solves'] for c in cost)}次正解及{sum(c['adjoint_solves'] for c in cost)}次伴随；共同读出另2224正解、0伴随；原raw审计另128正解、0伴随。求积phase审计不调用电学求解。CPU零更新校准和profile另计，不能混同科研训练预算。\n\n"
    if used:
        comparisons=[q for d in used['arms'].values() for q in d['comparison_8_to_16'].values()]
        passed=all(q['passed'] for q in comparisons)
        text+=f"**VERIFIED（实际训练阶数检查）：**16/32稳定不能单独检验实际使用的8点。回收后、读取参考评分前，在相同固定池补做每端点一次CPU FP64的8点phase目标／梯度，与已有CUDA FP64的16点结果对照。全部目标通过={passed}；最大目标相对变化{max(q['value_relative_change'] for q in comparisons):.4g}，最大梯度范数相对变化{max(q['gradient_norm_relative_change'] for q in comparisons):.4g}。沿用1%／5%数值容差；原16/32标志、训练和科学评分规则均未更改。另计{used['phase_derivative_positions']}个phase导数位置、{used['phase_endpoint_coordinate_queries']}个端点位置，零优化更新、零电学求解。见[8/16完整数表](endpoint-used-order.csv)。\n\n"
    text+='## 可复查数表与原始记录\n\n'
    for filename,label in [('all-metrics.csv','八臂×W／窗外／全轨迹的全部七项误差'),('full-readout-metrics.csv','完整端口、局部焦耳热及电学一致性'),
        ('both-cycle-events.csv','两周期原定义事件'),('all-pairwise-decisions.csv','56个有序比较的A_W、A/B和全部非劣子项'),
        ('raw-physics-audit.csv','独立原变量热／相态残差'),('endpoint-quadrature.csv','终点16/32求积的目标与梯度范数变化'),
        ('endpoint-moment-energy.csv','同一校准池终点时间矩与点残差平方的比例'),
        ('actual-training-cost.csv','实际训练与读出工作量')]:text+=f'- [{label}]({filename})。\n'
    text+='- [原始统一评分](../../outputs/runs/20260923-relative-phase-moments/scoring/results.json)、[八个锁定终点](../../outputs/runs/20260923-relative-phase-moments/all-endpoints-locked.json)、[读出目录](../../outputs/runs/20260923-relative-phase-moments/predictions)、[回收与关机记录](../../outputs/runs/20260923-relative-phase-moments/compute-closure.json)。\n'
    text+='\n旧B1的0/12、B_E连续反例、六臂负续训与原初边值限制仍保留原身份。本试验不提供跨协议／材料泛化、实验验证或严格器件可用性的额外默认背书。阶段4未执行。\n'
    (HERE/'results.md').write_text(text,encoding='utf-8')


def diagnostics():
    rows=read(RUN/'saved-array-analysis.json')['rows']
    with np.load(RUN/'saved-array-traces.npz') as f:traces={k:f[k] for k in f.files}
    t=traces['time'];fig,ax=plt.subplots(2,2,figsize=(10,6.7),layout='constrained')
    for col,seed in enumerate((29,43)):
        a=ax[0,col]
        for ref,ls in [('old','-'),('refined','--'),('spatial',':')]:
            a.plot(t,100*traces[ref+'/reference_active'],color='#202020',ls=ls,lw=1,label='reference: '+ref)
        for role,color in [('E','#007F79'),('D_E','#DB7B18'),('F','#898989')]:
            a.plot(t,100*traces[f'old/shorter/{seed}/{role}/predicted_active'],color=color,lw=1.5,label=role if role!='F' else 'F / B_E')
        a.axvspan(1.01,1.36,color='#F5DCA9',alpha=.4)
        a.axvspan(1.36,2.02,color='#DDD9ED',alpha=.35)
        a.set(xlim=(1.,2.03),ylabel='Active fraction of full domain (%)',xlabel='Time',title=f'B1 fixed endpoints, seed {seed}')
        a.legend(ncol=2,fontsize=7,frameon=False)
    selected=[r for r in rows if r['reference']=='old']
    labels=[r['id'].replace('shorter/','').replace('/',' ') for r in selected]
    x=np.arange(len(selected));bottom=np.zeros(len(x))
    for key,label,color in [('heating_FN_integral','Heating FN','#3B609B'),('heating_FP_integral','Heating FP','#D39B32'),
                            ('subsequent_FN_integral','After-pulse FN','#729BCD'),('subsequent_FP_integral','After-pulse FP','#B95B50')]:
        v=np.array([r[key] for r in selected])*100
        ax[1,0].bar(x,v,bottom=bottom,color=color,label=label);bottom+=v
    ax[1,0].set(xticks=x,xticklabels=labels,ylabel='100 x unnormalized time integral',title='Full-domain set error in W = [1.01, 2.02]')
    ax[1,0].set_ylim(0,1.2)
    ax[1,0].tick_params(axis='x',labelrotation=35);ax[1,0].legend(fontsize=7,frameon=False)
    d=read(RUN/'checkpoint-diagnostics.json')['records']['parent29']['residual_distribution']
    keys=['rphi','rpsi','rzeta'];pure=np.array([d[k]['near_pure_share'] for k in keys])*100
    ax[1,1].bar(keys,pure,color='#759DAA',label='Near pure: phase < .01 or > .99')
    ax[1,1].bar(keys,100-pure,bottom=pure,color='#D0A057',label='Transition region')
    ax[1,1].set(ylim=(0,100),ylabel='Fraction of weighted squared residual (%)',title='Same legal parent; diagnostic regions only')
    ax[1,1].legend(fontsize=7,frameon=False)
    save(fig,'existing-evidence-diagnostics')
    diagnostic=read(RUN/'checkpoint-diagnostics.json')['records']
    fig,axes=plt.subplots(1,3,figsize=(10.8,3),layout='constrained')
    names=list(diagnostic)
    time_rows=[]
    for ax,k,title in zip(axes,('rphi','rpsi','rzeta'),('Raw phase','Full logit','Finite logit')):
        matrix=[]
        for name,d in diagnostic.items():
            total=d['residual_distribution'][k]['weighted_square']
            values=[]
            for window in d['residual_distribution_by_physics_window']:
                contribution=window['residual_square_contribution'][k]
                values.append(100*contribution/total)
                time_rows.append(dict(model=name,residual=k,start=window['interval'][0],end=window['interval'][1],
                    sample_mass=window['sample_mass'],weighted_square_contribution=contribution,
                    conditional_mean_square=contribution/window['sample_mass'],fraction_of_residual_square=contribution/total))
            matrix.append(values)
        matrix=np.asarray(matrix)
        im=ax.imshow(matrix,cmap='Blues',vmin=0,vmax=100,aspect='auto')
        for i in range(3):
            for j in range(4):
                ax.text(j,i,f'{matrix[i,j]:.1f}%',ha='center',va='center',fontsize=8,color='white' if matrix[i,j]>60 else 'black')
        ax.set(xticks=range(4),xticklabels=['Heat 1','Off 1','Heat 2','Off 2'],yticks=range(3),yticklabels=names,title=title)
        ax.tick_params(axis='x',labelrotation=35)
    fig.colorbar(im,ax=axes,shrink=.8,label='Share of squared residual (%)')
    save(fig,'residual-time-distribution')
    with (HERE/'residual-time-distribution.csv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(time_rows[0]));writer.writeheader();writer.writerows(time_rows)
    q=read(RUN/'quadrature.json');cal=read(RUN/'phase-calibration.json');profile=read(RUN/'profile.json')
    ratios=[r['subsequent_FP_integral']/(r['W_FN_integral']+r['W_FP_integral']) for r in rows if r['id'].endswith(('/E','/D_E'))]
    text=f'''# 相态目标开发：本地证据与执行状态

任务 `PCM-20260922-RELATIVE-PHASE-MOMENTS-01`，执行日期 2026-09-23。新实验独立于已收口B1，不覆盖其0/12结论。

## 已有数组事后分析

**VERIFIED：**七个B1对象 × 三参考，共21组160×80全域相态数组，按原阈值0.5分解缺测窗 W=[1.01,2.02] 的 S=FN+FP。加热[1.01,1.36]与随后[1.36,2.02]使用未归一化时间贡献，公共节点的梯形半权分别归属两段；总和逐组恢复原S，无新场推理或参考求解。

**VERIFIED：**E／D_E的加热后FP贡献占W总集合误差的{100*min(ratios):.2f}%—{100*max(ratios):.2f}%。原参考E29的贡献为：加热FN 0.00051758、加热FP 0.00029697、随后FN 0.00014102、随后FP 0.00803330；总和0.00898887，除以W长度1.01后恢复S=0.00889987。F与B_E的S可能更低，但来自整次事件漏检，不能解释为更好的相变重建。

**SUPPORTED_INTERPRETATION：**误差定位偏向加热结束后的多余活跃区域。原恢复指标仍通过，所以这里不能改写为“恢复门失败”，也不能仅凭分解认定梯度冲突或唯一训练根因。全部onset、recall、precision、mass ratio与recovery继续沿用既有事件表。

## 固定模型零更新诊断

诊断仅读取合法B1父态29与旧E／D_E29；使用由已知驱动划分、与参考无关的同一个panel池。分区阈值0.01／0.99只用于解释，不参与训练权重或采样。

| 模型 | raw残差能量近纯相份额 | 完整logit近纯相份额 | 有限logit近纯相份额 | 完整logit低于clip尺度的份额 |
|---|---:|---:|---:|---:|
'''
    if (RUN/'decision.json').exists():
        decision=read(RUN/'decision.json')
        lead=f"**{decision['claim_status']} — {decision['route']}。** {decision['summary_zh']} 见[完整结果、科学图和机制对照](results.md)。\n\n"
        text=text.replace('## 已有数组事后分析',lead+'## 已有数组事后分析',1)
    for name,d in diagnostic.items():
        rd=d['residual_distribution']
        text+=f"| {name} | {100*rd['rphi']['near_pure_share']:.3f}% | {100*rd['rpsi']['near_pure_share']:.3f}% | {100*rd['rzeta']['near_pure_share']:.3f}% | {100*rd['rpsi']['below_clip_share']:.3f}% |\n"
    d=diagnostic['parent29']['visible_clip']
    text+=f'''
**VERIFIED：**可见φ标签中{d['count']}/{d['total']}（{100*d['fraction']:.2f}%）需要原logit数值裁剪；这些标签承担父态相态观测损失的{100*d['fraction_of_phase_loss']:.2f}%。这是无噪数值标签的变换处理，不是真实传感器噪声。

**VERIFIED（数学与数值）：**完整ψ包括空间初态及startup；rφ=s rψ和有限logit链式关系的值、参数梯度及饱和尾部导数均核验。保持潜热、T耦合、M(T)及原热面通量。局部点残差保留；零／一阶矩不能检测所有时间模式。21项聚焦与继承测试通过。

真实父态与固定制造场的8／16／32点求积均通过，保留{q['selected_order']}点。父态8→16最大目标相对变化{max(v['value_relative_change'] for v in q['comparisons']['8_to_16'].values()):.3g}，最大梯度范数相对变化{max(v['gradient_norm_relative_change'] for v in q['comparisons']['8_to_16'].values()):.3g}，均显著低于预声明1%与5%门。一次32点检查在本地中断，无Python异常栈；小分块回归通过后复用8／16结果补齐，未改变点集或优化器轨迹。

## 冻结开发试验

共同B1父态29、可见标签、网络、物理与原a/b保持。D、P、L、R、I、RI、RIM、G各600 Adam + 最多100完整L-BFGS评估；P明确为新共享phase点集上的E_Q。八臂只有一个初始化，不是确认或formal OOD。

| 臂 | phase目标 | 父态固定系数 | 一次CPU完整目标/梯度耗时(s) | 正解/伴随 |
|---|---|---:|---:|---:|
'''
    kinds={'D':'无内部热/相态项','P':'raw点式','L':'完整logit点式','R':'有限logit点式','I':'raw点式+零阶矩','RI':'有限logit+零阶矩','RIM':'有限logit+零/一阶矩','G':'raw全局标量'}
    for arm,r in profile['arms'].items():
        k=cal['factors'].get(arm)
        scalar='—' if k is None else f'{k:.9g}'
        counts=r['statistics']['electrical']
        text+=f"| {arm} | {kinds[arm]} | {scalar} | {r['elapsed_seconds']:.2f} | {counts['forward_solves']}/{counts['adjoint_solves']} |\n"
    text+='''
以上是每臂首次CPU零更新测量，不是稳定速度比较。GPU训练成本另据实际日志报告。G只匹配一个指定的初始phase梯度范数；其系数约0.508，不能泛称“增大物理权重”，也不代表Adam更新等价。

'''
    memory_paths=[RUN/f'profile-memory-{a}.json' for a in profile['arms']]
    if all(p.exists() for p in memory_paths):
        memory=[read(p) for p in memory_paths]
        text+='首次测量因psutil未安装而缺少内存记录。采用系统自带计数，每臂在独立新进程中补做第二次且最后一次同父态完整目标／梯度计算；没有优化更新。两个profile共768正解和768伴随，第二次目标值逐臂与首次完全相同。峰值含进程导入、模型和完整梯度，不是孤立算子或GPU显存。\n\n'
        text+='| 臂 | CPU进程峰值工作集 MiB | 计算后私有内存 MiB | 第二次耗时 s |\n|---|---:|---:|---:|\n'
        for m in memory:text+=f"| {m['arm']} | {m['after']['PeakWorkingSetSize']/2**20:.2f} | {m['after']['PrivateUsage']/2**20:.2f} | {m['elapsed_seconds']:.2f} |\n"
        text+='\n内存原始记录位于运行目录的profile-memory-各臂.json；两个profile的phase导数位置合计114688、phase空间二阶AD分量229376、phase端点查询12288。\n\n'
    common=read(RUN/'calibration.json');components=[]
    for arm,v in profile['arms'].items():
        c=v['components'];weighted=.1*c['phase']/(3*common['bE'])
        components.append(dict(arm=arm,total=v['objective'],observation=c['observation']/common['aE'],
            boundary=.5*c['boundary']/common['bE'],initial=.1*c['initial']/common['bE'],
            thermal=.1*c['thermal']/(3*common['bE']),phase=weighted,phase_fraction_of_total=weighted/v['objective']))
    csv_file('parent-objective-components.csv',components)
    text+='**VERIFIED（初始尺度）：**在完整固定优化池、λ=0.1的零更新测量中，P的加权phase项为5.4308×10⁻⁵，占总目标0.00510%；RIM为2.1918×10⁻⁵，占0.00206%。[完整初始分量](parent-objective-components.csv)保留全部八臂。这一固定池独立于一次性校准池，因此不要求两池的loss配平完全相同。loss占比不等于梯度占比，也不能单凭此值认定优化无效或事后追加调权。\n\n'
    value=cal['phase_values'];z0=(2*value['Izeta']-value['Pzeta'])/value['Pzeta'];z1=2*(value['Mzeta']-value['Izeta'])/value['Pzeta']
    text+=f'**VERIFIED（父态时间矩）：**同一校准池中，有限logit的零阶矩平方占点残差平方{100*z0:.4f}%，一阶矩平方占{100*z1:.4f}%；未校准Mζ/Pζ={value["Mzeta"]/value["Pzeta"]:.8f}，Iζ/Pζ={value["Izeta"]/value["Pzeta"]:.8f}。这是离散Gauss量的数值分解，显示初始目标接近；不证明梯度方向相同、训练全程等价或时间矩普遍无效。\n\n'
    if (RUN/'scoring/results.json').exists():
        text+='八个终点、共同原生读出及原参考评分均已完成，见[完整结果与机制对照](results.md)。另两参考、第二读出层和新seed未执行；后续安排依完整结果路由，不自动进入确认。\n\n'
    else:
        text+='GPU前置检查已通过，科学筛选运行中。全部终点锁定之后统一原参考评分；另两参考、第二读出层和新seed仅属于未授权确认阶段。\n\n'
    text+='''## 证据和来源

- [数组分解](../../outputs/runs/20260923-relative-phase-moments/saved-array-decomposition.csv)、[既有事件](../../outputs/runs/20260923-relative-phase-moments/saved-array-events.json)、[固定模型诊断](../../outputs/runs/20260923-relative-phase-moments/checkpoint-diagnostics.json)。
- [求积检查](../../outputs/runs/20260923-relative-phase-moments/quadrature.json)、[校准](../../outputs/runs/20260923-relative-phase-moments/phase-calibration.json)、[零更新工作量](../../outputs/runs/20260923-relative-phase-moments/profile.json)、[测试记录](../../outputs/runs/20260923-relative-phase-moments/tests.log)。
- [相态目标源码](../../pinn_pcm_sci/phk_v23_phase_moments.py)、[执行器](../../pinn_pcm_sci/phk_v23_phase_moments_run.py)、[冻结配置](../../outputs/runs/20260923-relative-phase-moments/frozen-config.json)。
- [授权、三文档取舍与历史来源](../../docs/notes/2026-09-23-relative-phase-moments-authorized.md)。完整latent residual已见9月10日历史规划；不得主张本轮首次提出。
- Feng et al., *Integral Regularization PINNs for Evolution Equations*, Commun. Comput. Phys. 39(2):356–386 (2026), DOI [10.4208/cicp.OA-2025-0082](https://www.global-sci.com/cicp/article/download/23347/36216/37901)；定点阅读[预印本§3.1、式10—20](https://arxiv.org/html/2503.23729v1)。I为原变量区间残差的匹配适配，非原方法完整复现。
- Kharazmi et al., [VPINNs](https://arxiv.org/abs/1912.00873)，只核对摘要与元数据的Legendre测试／分部积分先例；Saleh et al., [ICML2024原始记录](https://proceedings.mlr.press/v235/saleh24a.html)，核对积分估计平方的偏差；De Ryck et al., [算子预条件化v2](https://arxiv.org/abs/2310.05801)，不作为当前非线性目标的现成保证。

## 已验证执行入口

项目Python 3.11／FP64，未升级依赖。以下四个模块按顺序执行并合计通过21项测试：

```powershell
.\\.venv\\Scripts\\python.exe -m tests.test_phk_v23_phase_moments
.\\.venv\\Scripts\\python.exe -m tests.test_phk_v23_b1
.\\.venv\\Scripts\\python.exe -m tests.test_lf11_electrical_elimination
.\\.venv\\Scripts\\python.exe -m tests.test_phk_v23_lf11_v_continue
```

数值准备与首次profile入口为 `python -m pinn_pcm_sci.phk_v23_phase_moments_run prepare`／`profile`；第二次内存profile为 `python -m cloud.phk_v23_phase_moments.profile_memory <arm>`。实际输出各自有防覆盖保护，不需为审阅重复运行。

GPU部署包固定源码及输入，见运行目录deployment-manifest.json与deployment-archive.json。`cloud/phk_v23_phase_moments/run_cloud.py`只按train→audit→readout执行同一任务；原生结果回收后，本地统一评分入口为 `python -m pinn_pcm_sci.phk_v23_phase_moments_evaluate`。本报告及图表由 `python paper/phase_moments_20260923/build_report.py`只读记录再生。新一轮科研复现须复制到另一个明确命名的运行目录并另行取得相应授权，不能覆盖当前终点。

![既有证据的时间定位与残差分布](figures/existing-evidence-diagnostics.png)

四窗残差份额均按各模型／残差自己的平方积分归一化；不同坐标的绝对损失不可直接比较。可加的原始贡献和条件均值见[时间分布表](residual-time-distribution.csv)。为补齐此时间定位图，对相同三个固定模型与同一panel池补做了一次零更新导数读取，没有重采样、改权或优化器更新。

![残差在原四窗内的分布](figures/residual-time-distribution.png)

[可复用的方法段落及主张边界](method-and-claim-boundaries.md)同时给出下一工作稿的数据可用性更新措辞。
'''
    (HERE/'README.md').write_text(text,encoding='utf-8')


if __name__=='__main__':
    diagnostics()
    results()
