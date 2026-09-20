"""Create tables and scientific figures from the completed array-only scores."""
from pathlib import Path
import csv
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
ARCH=ROOT/'outputs/submission-archive-20260918'
SCORE=ARCH/'isolated-rescore'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def dump(name,rows):
    p=HERE/'tables'/f'{name}.csv'
    with p.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def md(name,headers,rows):
    body=['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']
    body+=['| '+' | '.join(str(x) for x in r)+' |' for r in rows]
    (HERE/'tables'/f'{name}.md').write_text('\n'.join(body)+'\n',encoding='utf-8')
def fnum(x):return '-' if x is None else f'{x:.6g}'
def pf(x):return 'Pass' if x else 'Fail'
def plot_save(fig,name):
    fig.savefig(HERE/'figures'/f'{name}.png',dpi=220,bbox_inches='tight')
    fig.savefig(HERE/'figures'/f'{name}.pdf',bbox_inches='tight');plt.close(fig)

def main():
    result=read(SCORE/'results.json');assert result['status']=='COMPLETE_ARRAY_ONLY_REPRODUCTION'
    rr=result['records'];dec=result['decisions'];allrows=[];effects=[];events=[];gates=[]
    metrics=['S','Ephi','ET','EV','EI','bottom_current_NRMSE','power_trace_NRMSE','energy_error','local_joule_NRMSE']
    for reference,levels in rr.items():
        for level,items in levels.items():
            for oid,r in items.items():
                allrows.append(dict(reference=reference,reader=level,id=oid,protocol=r['protocol'],seed=r['seed'],
                    role=r['role'],**{k:r['metrics'][k] for k in metrics},
                    native_240_local_q_NRMSE=r.get('native_240_local_q_NRMSE'),strict=r['strict_device_pass']))
                for c in r['cycles']:events.append(dict(reference=reference,reader=level,id=oid,**c))
            for case,seeds in dec[reference][level].items():
                for seed,pairs in seeds.items():
                    for comparison,d in pairs.items():
                        candidate,control=comparison.split('_vs_')
                        idc=f'{case}/{seed}/{candidate}';idb=case+'/B_E' if control=='B_E' else f'{case}/{seed}/{control}'
                        a=items[idc]['metrics'];b=items[idb]['metrics']
                        gates.append(dict(reference=reference,reader=level,protocol=case,seed=seed,comparison=comparison,
                            A=d['A']['passed'],B=d['B']['passed']))
                        for key in metrics:
                            av,bv=a[key],b[key]
                            effects.append(dict(reference=reference,reader=level,protocol=case,seed=seed,comparison=comparison,
                                metric=key,candidate_error=av,control_error=bv,signed_candidate_minus_control=av-bv,
                                difference_percentage_points=100*(av-bv) if key in ('ET','EI','bottom_current_NRMSE','power_trace_NRMSE','energy_error') else None,
                                relative_error_reduction=(bv-av)/bv if bv else None))
    dump('reader-all-metrics',allrows);dump('reader-all-events',events)
    dump('reader-all-effects',effects);dump('reader-all-decisions',gates)
    compact=[]
    for case in ('original','shorter'):
        for seed in (29,43):
            for role in ('E','F','B_E'):
                oid=case+'/B_E' if role=='B_E' else f'{case}/{seed}/{role}'
                a=rr['spatial']['coarse'][oid]['metrics'];b=rr['spatial']['fine'][oid]['metrics']
                compact.append([case,str(seed),role,*[fnum(100*x) for x in
                    (a['EI'],b['EI'],a['power_trace_NRMSE'],b['power_trace_NRMSE'])]])
    md('reader-spatial-primary',['Case','Seed','Method','I 160 (%)','I 240 (%)','P 160 (%)','P 240 (%)'],compact)
    md('reader-gates',['Reference','Reader','Case','Seed','Control','A','B'],
       [[g['reference'],g['reader'],g['protocol'],g['seed'],g['comparison'],pf(g['A']),pf(g['B'])]
        for g in gates if g['comparison'] in ('E_vs_F','E_vs_B_E','E_vs_D_E')])
    clean=[]
    for seed in (29,43):
        for level in ('coarse','fine'):
            for role in ('E','D_E'):
                r=rr['spatial'][level][f'shorter/{seed}/{role}'];m=r['metrics']
                clean.append([str(seed),role,level,fnum(m['Ephi']),fnum(100*m['ET']),fnum(100*m['EI']),
                              fnum(100*m['power_trace_NRMSE']),fnum(100*m['energy_error']),pf(r['strict_device_pass'])])
    md('clean-pde-primary',['Seed','Role','Reader','Raw phase RMS','T (%)','I (%)','P (%)','Energy (%)','Strict'],clean)
    audits=read(ARCH/'fixed-residual-audits.json')['records'];ar=[]
    for seed in (29,43):
        for role in ('E','D_E'):
            a=audits[f'{seed}/{role}']['components'];ar.append(dict(seed=seed,role=role,**a))
    dump('clean-pde-audits',ar)
    md('clean-pde-audits',['Seed','Role','Observation','Thermal','Phase','Boundary'],
       [[a['seed'],a['role'],*[fnum(a[k]) for k in ('observation','thermal','phase','boundary')]] for a in ar])
    # Four panels, all competitors and both port measures, same spatial reference.
    plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False})
    colors={'E':'#1675a9','F':'#d78124','B_E':'#777777','D_E':'#9b449b'}
    fig,axes=plt.subplots(2,2,figsize=(10.4,8.3),constrained_layout=True)
    for ax,(case,seed) in zip(axes.flat,[(c,s) for c in ('original','shorter') for s in (29,43)]):
        for role in ('E','F','B_E'):
            oid=case+'/B_E' if role=='B_E' else f'{case}/{seed}/{role}'
            for key,style,label in [('EI','-','I'),('power_trace_NRMSE','--','P')]:
                ax.plot([0,1],[100*rr['spatial'][l][oid]['metrics'][key] for l in ('coarse','fine')],
                    style+'o',color=colors[role],label=role+' '+label,lw=1.4,markersize=4)
        ip=[];pp=[];ig=[];pg=[]
        for l in ('coarse','fine'):
            e=rr['spatial'][l][f'{case}/{seed}/E']['metrics'];f=rr['spatial'][l][f'{case}/{seed}/F']['metrics']
            ip.append(100*(e['EI']-f['EI']))
            pp.append(100*(e['power_trace_NRMSE']-f['power_trace_NRMSE']))
            ig.append(100*(1-e['EI']/f['EI']))
            pg.append(100*(1-e['power_trace_NRMSE']/f['power_trace_NRMSE']))
        ax.set_title(f'{case}, seed {seed}\n'
            f'E-F current: {ip[0]:+.3f} to {ip[1]:+.3f} pp; reduction {ig[0]:.1f} to {ig[1]:.1f}%\n'
            f'E-F power: {pp[0]:+.3f} to {pp[1]:+.3f} pp; reduction {pg[0]:.1f} to {pg[1]:.1f}%',fontsize=8.8)
        ax.set_xticks([0,1],['160 x 80','240 x 120']);ax.set_ylabel('NRMSE (%)');ax.grid(alpha=.18)
    handles,labels=axes[0,0].get_legend_handles_labels();fig.legend(handles,labels,ncol=6,loc='outside lower center')
    plot_save(fig,'fig15-common-reader')
    fig,axes=plt.subplots(1,3,figsize=(10.7,3.8),constrained_layout=True)
    for ax,key,label in zip(axes,('Ephi','EI','power_trace_NRMSE'),('Phase RMS','Current NRMSE (%)','Power NRMSE (%)')):
        for seed,marker in ((29,'o'),(43,'s')):
            for role in ('E','D_E'):
                values=[rr['spatial'][l][f'shorter/{seed}/{role}']['metrics'][key] for l in ('coarse','fine')]
                if key!='Ephi':values=np.array(values)*100
                ax.plot([0,1],values,'-'+marker,color=colors[role],label=f'{role}, {seed}',alpha=1 if seed==29 else .65)
        ax.set_xticks([0,1],['160 x 80','240 x 120']);ax.set_ylabel(label);ax.grid(alpha=.18)
    fig.legend(*axes[0].get_legend_handles_labels(),ncol=4,loc='outside lower center')
    plot_save(fig,'fig16-clean-pde')
    mechanism=[]
    for p in (SCORE/'mechanisms').rglob('*.json'):
        a=read(p);reference=p.parent.name;case,seed,role=p.stem.split('_')
        for scope,v in a['regions'].items():
            mechanism.append(dict(reference=reference,protocol=case,seed=int(seed),role=role,region=scope,
                **{k:x for k,x in v.items() if not isinstance(x,list)}))
    dump('threshold-neighborhood',mechanism)
    conductivity=[]
    for p in (SCORE/'mechanisms').rglob('*.json'):
        a=read(p);case,seed,role=p.stem.split('_')
        conductivity.append(dict(reference=p.parent.name,protocol=case,seed=int(seed),role=role,**a['log_conductivity']))
    dump('conductivity-decomposition',conductivity)
    fig,axes=plt.subplots(2,2,figsize=(10.3,6.8),constrained_layout=True)
    for ax,(case,seed) in zip(axes.flat,[(c,s) for c in ('original','shorter') for s in (29,43)]):
        selected=[v for v in mechanism if v['reference']=='spatial' and v['protocol']==case and v['seed']==seed and v['region'].startswith('heating_windows')]
        for j,role in enumerate(('E','F')):
            values=[]
            for region in ('near_threshold','outside_threshold'):
                r=next(x for x in selected if x['role']==role and x['region'].endswith('/'+region))
                values.extend([r['FN'],r['FP']])
            ax.bar(np.arange(4)+(j-.5)*.34,values,width=.34,color=colors[role],label=role)
        ax.set_xticks(np.arange(4),['Near FN','Near FP','Outside FN','Outside FP'])
        ax.set_title(f'{case}, seed {seed}');ax.set_ylabel('Weighted mass');ax.grid(axis='y',alpha=.18)
    fig.legend(*axes[0,0].get_legend_handles_labels(),ncol=2,loc='outside lower center')
    plot_save(fig,'fig17-threshold-errors')
    fig,axes=plt.subplots(2,2,figsize=(10.4,6.5),constrained_layout=True)
    for ax,(case,seed) in zip(axes.flat,[(c,s) for c in ('original','shorter') for s in (29,43)]):
        small=[]
        for role in ('E','F'):
            row=next(r for r in conductivity if r['reference']=='spatial' and r['protocol']==case and r['seed']==seed and r['role']==role)
            ax.plot(range(4),[row[k] for k in ('temperature_MSE','phase_MSE','signed_cross','total_MSE')],'-o',color=colors[role],label=role)
            small.append(f"{role}: T={row['temperature_MSE']:.2e}, cross={row['signed_cross']:+.2e}")
        ax.axhline(0,color='#444',lw=.6);ax.set_xticks(range(4),['T term','Phase term','Cross term','Total'])
        ax.set_title(f'{case}, seed {seed}\n'+'\n'.join(small),fontsize=8.5)
        ax.set_ylabel('Mean squared log-conductivity error terms');ax.grid(alpha=.18)
    fig.legend(*axes[0,0].get_legend_handles_labels(),ncol=2,loc='outside lower center')
    plot_save(fig,'fig18-conductivity-errors')
    fig,axes=plt.subplots(4,2,figsize=(10.4,10.2),constrained_layout=True)
    for row,(case,seed) in enumerate([(c,s) for c in ('original','shorter') for s in (29,43)]):
        for role in ('E','F'):
            with np.load(SCORE/'traces/spatial/fine'/f'{case}_{seed}_{role}.npz') as v:
                axes[row,0].plot(v['time'],v['signed_power_error'],color=colors[role],label=role)
                axes[row,0].plot(v['time'],v['absolute_power_error'],'--',color=colors[role],alpha=.45)
                axes[row,1].plot(v['time'],v['cumulative_signed_energy_error'],color=colors[role],label=role)
        for ax in axes[row]:ax.axhline(0,color='#444',lw=.6);ax.grid(alpha=.18);ax.set_title(f'{case}, seed {seed}')
        axes[row,0].set_ylabel('Power error');axes[row,1].set_ylabel('Cumulative signed energy error')
    axes[-1,0].set_xlabel('Time');axes[-1,1].set_xlabel('Time')
    fig.legend(*axes[0,0].get_legend_handles_labels(),ncol=2,loc='outside lower center')
    plot_save(fig,'fig19-power-cancellation')
    summary={'historical_E_F_B':{},'clean_E_D_E':{},'strict_D_E':{},'case_effects':[]}
    for ref in rr:
        for level in ('coarse','fine'):
            summary['historical_E_F_B'][ref+'/'+level]=[dec[ref][level][c][str(seed)]['E_vs_F']['B']['passed']
                for c in ('original','shorter') for seed in (29,43)]
            summary['clean_E_D_E'][ref+'/'+level]={str(seed):{k:dec[ref][level]['shorter'][str(seed)]['E_vs_D_E'][k]['passed'] for k in ('A','B')} for seed in (29,43)}
            summary['strict_D_E'][ref+'/'+level]={str(seed):rr[ref][level][f'shorter/{seed}/D_E']['strict_device_pass'] for seed in (29,43)}
    summary['case_effects']=[r for r in effects if r['reference']=='spatial' and r['reader']=='fine' and r['comparison'] in ('E_vs_F','E_vs_D_E') and r['metric'] in ('S','Ephi','EI','power_trace_NRMSE','energy_error')]
    (HERE/'results-summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps({'status':'TABLES_AND_FIGURES_COMPLETE','historical_E_F_B':summary['historical_E_F_B'],
                      'clean_E_D_E':summary['clean_E_D_E']}))

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--archive-root',type=Path,default=ARCH)
    p.add_argument('--score-dir',type=Path)
    args=p.parse_args();ARCH=args.archive_root
    SCORE=args.score_dir or ARCH/'isolated-rescore'
    main()
