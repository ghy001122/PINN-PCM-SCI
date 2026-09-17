"""Figures and complete tables from the independently rescored fixed arrays."""
from __future__ import annotations
import argparse
import csv
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap,BoundaryNorm

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]


def read(path):return json.loads(path.read_text(encoding='utf-8'))


def table(name,columns,rows):
    with (HERE/'tables'/f'{name}.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.writer(f);w.writerow(columns);w.writerows(rows)
    def fmt(x):
        if x is None:return 'not defined'
        if isinstance(x,(bool,np.bool_)):return 'yes' if x else 'no'
        if isinstance(x,(float,np.floating)):return f'{x:.8g}'
        return str(x)
    lines=['| '+' | '.join(columns)+' |','| '+' | '.join(['---']*len(columns))+' |']
    lines += ['| '+' | '.join(fmt(x) for x in row)+' |' for row in rows]
    (HERE/'tables'/f'{name}.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')


def finish(fig,name):
    for ext in ('png','pdf'):fig.savefig(HERE/'figures'/f'{name}.{ext}',dpi=210,bbox_inches='tight')
    plt.close(fig)


def strict_failures(record):
    """Describe the already frozen strict rule; never replace its verdict."""
    reasons=list(record['event_failures'])
    if not record['valid']:reasons.append('numerical field validity')
    if record['metrics']['phase_max']<.9:reasons.append(f"maximum phase {record['metrics']['phase_max']:.8g} < 0.9")
    for c in record['cycles']:
        label=f"cycle {c['cycle']}: "
        for key,limit in [('recall',.9),('precision',.8)]:
            if c[key]<limit:reasons.append(label+f'{key} {c[key]:.8g} < {limit}')
        if not .8<=c['mass_ratio']<=1.2:reasons.append(label+f"mass ratio {c['mass_ratio']:.8g} outside [0.8,1.2]")
        if c['timing_absolute'] is None:reasons.append(label+'onset error undefined')
        elif c['timing_absolute']>.005:reasons.append(label+f"onset error {c['timing_absolute']:.8g} > 0.005")
    if record['strict_device_pass'] and reasons:raise AssertionError('Failure description disagrees with frozen strict success')
    return reasons


def main():
    p=argparse.ArgumentParser();p.add_argument('--archive',type=Path,default=ROOT/'outputs/submission-archive-20260916')
    p.add_argument('--scores',default='rescore-output');a=p.parse_args();score=a.archive/a.scores
    data=read(score/'results.json');old=data['records']['old'];new=data['records']['refined']
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11.5,'axes.spines.top':False,'axes.spines.right':False})
    roles=['E','E_C','E_R','E_I'];colors=['#657889','#263c50','#26998d','#d77c35']
    rows=[];events=[];secondary=[]
    for refname,records in data['records'].items():
        for seed in (29,43):
            for role in roles+['F']:
                r=records[f'shorter/{seed}/{role}'];m=r['metrics']
                rows.append([refname,seed,role,m['S'],m['Ephi'],100*m['ET'],100*m['EI'],100*m['power_trace_NRMSE'],r['strict_device_pass']])
                secondary.append([refname,seed,role,m['EV'],100*m['bottom_current_NRMSE'],100*m['energy_error'],100*m['local_joule_NRMSE']])
                for c in r['cycles']:
                    events.append([refname,seed,role,c['cycle'],c['recall'],c['precision'],c['mass_ratio'],c['timing_absolute'],c['recovery_fraction'],c['false_negative_target_mass'],c['false_positive_target_mass']])
        # One deterministic same-solver interpolant per protocol/reference,
        # never two seed-level repetitions of the same baseline.
        r=records['shorter/B_E'];m=r['metrics']
        rows.append([refname,'shared','B_E',m['S'],m['Ephi'],100*m['ET'],100*m['EI'],100*m['power_trace_NRMSE'],r['strict_device_pass']])
        secondary.append([refname,'shared','B_E',m['EV'],100*m['bottom_current_NRMSE'],100*m['energy_error'],100*m['local_joule_NRMSE']])
        for c in r['cycles']:
            events.append([refname,'shared','B_E',c['cycle'],c['recall'],c['precision'],c['mass_ratio'],c['timing_absolute'],c['recovery_fraction'],c['false_negative_target_mass'],c['false_positive_target_mass']])
    table('phase-adapter-metrics',['Reference','Seed','Role','S','Raw phase RMS','T %','Current %','Power %','Strict'],rows)
    table('phase-adapter-secondary',['Reference','Seed','Role','Potential RMS','Bottom current %','Energy %','Local q %'],secondary)
    table('phase-adapter-events',['Reference','Seed','Role','Cycle','Recall','Precision','Mass ratio','Timing','Recovery','FN mass','FP mass'],events)
    effects=[]
    percent_metrics={'ET','EI','bottom_current_NRMSE','power_trace_NRMSE','energy_error','local_joule_NRMSE'}
    effect_metrics=('S','Ephi','ET','EV','EI','bottom_current_NRMSE','power_trace_NRMSE','energy_error','local_joule_NRMSE')
    for refname,records in data['records'].items():
        for protocol in ('original','shorter'):
            for seed in (29,43):
                prefix=f'{protocol}/{seed}/'
                pairs=[(prefix+'E',prefix+'F','historical matched method'),
                       (prefix+'E',protocol+'/B_E','historical available-data baseline')]
                if protocol=='shorter':
                    pairs += [(prefix+'E_C',prefix+'E','continued optimization')]
                    pairs += [(prefix+role,prefix+'E_C','matched phase-head development') for role in ('E_R','E_I')]
                    pairs += [(prefix+role,prefix+'E','parent-state retention') for role in ('E_R','E_I')]
                    pairs += [(prefix+'E_I',prefix+'E_R','equal-trainable-parameter gate')]
                for candidate,baseline,scope in pairs:
                    for key in effect_metrics:
                        value=records[candidate]['metrics'][key]
                        base=records[baseline]['metrics'][key]
                        difference=value-base
                        improvement=None if base==0 else 100*(base-value)/base
                        effects.append([refname,candidate,baseline,scope,key,value,base,difference,
                                        100*difference if key in percent_metrics else None,improvement])
    table('paired-effect-sizes',['Reference','Candidate','Baseline','Comparison scope','Metric','Candidate error',
          'Baseline error','Signed error difference','Difference in percentage points','Relative error reduction %'],effects)
    verdicts=[]
    for refname,d in data['decisions'].items():
        for seed in (29,43):
            dec=d['shorter'][str(seed)]
            for role in ('E_R','E_I'):
                r=dec[role];g=dec['gate_independence']
                verdicts.append([refname,seed,role,r['matched_A'],r['matched_B'],r['strict_increment'],
                    (g['A'] or g['B'] or g['strict']) if role=='E_I' else 'not a gate'])
    table('phase-adapter-decisions',['Reference','Seed','Role','Matched phase','Matched device','Strict increment','Gate independent'],verdicts)
    fig,axes=plt.subplots(6,2,figsize=(10.4,11.6),layout='constrained')
    for col,seed in enumerate((29,43)):
        rr=[old[f'shorter/{seed}/{r}'] for r in roles]
        for row,(key,title,scale) in enumerate([('S','Active-set error S',1000),('Ephi','ROI phase RMS',1),
            ('EI','Current NRMSE (%)',100),('power_trace_NRMSE','Power NRMSE (%)',100)]):
            ax=axes[row,col];ax.bar(roles,[r['metrics'][key]*scale for r in rr],color=colors)
            ax.set_title(f'Seed {seed}: '+title+(' (×1000)' if key=='S' else ''));ax.grid(axis='y',alpha=.2)
        for row,(key,title,gate) in enumerate([('recall','Support recall',.9),('timing_absolute','Onset-time error',.005)],4):
            ax=axes[row,col]
            for c,style in ((0,'o-'),(1,'s--')):
                ax.plot(roles,[r['cycles'][c][key] for r in rr],style,label=f'Cycle {c+1}',lw=1.3)
            ax.axhline(gate,color='k',ls=':',lw=1);ax.set_title(title);ax.grid(alpha=.2)
            if row==4:ax.legend(fontsize=10.5,ncol=2)
    finish(fig,'fig07-phase-adapter')
    # All four predeclared times for each seed, with identical visual semantics.
    for seed in (29,43):
        fig,axes=plt.subplots(4,5,figsize=(11,6.6),layout='constrained')
        display=[np.load(score/'old'/f'shorter_{seed}_{r}-display.npz',allow_pickle=False) for r in roles]
        gate=np.load(a.archive/f'data/shorter/{seed}/E_I/fixed-display.npz',allow_pickle=False)
        cmap=ListedColormap(['#356e9e','#f7f9fa','#b93c24']);norm=BoundaryNorm([-1.5,-.5,.5,1.5],3)
        for j,t in enumerate(display[0]['time']):
            for col,dd in enumerate(display):
                err=dd['false_positive'][j].astype(int)-dd['false_negative'][j].astype(int)
                artist=axes[j,col].imshow(err.reshape(80,160),origin='lower',extent=(-1,1,0,1),cmap=cmap,norm=norm,aspect='equal')
                axes[j,col].set_title(f'{roles[col]}, t={t:.2f}',fontsize=11.5)
            gg=gate[f'gate_{j}'].reshape(80,160)
            gart=axes[j,4].imshow(gg,origin='lower',extent=(-1,1,0,1),cmap='viridis',vmin=0,vmax=4,aspect='equal')
            axes[j,4].set_title('Parent gate',fontsize=11.5)
        for ax in axes.flat:ax.set_xlabel('x',fontsize=11.5);ax.set_ylabel('z',fontsize=11.5)
        fig.colorbar(artist,ax=axes[:,:4],shrink=.6,ticks=[-1,0,1],label='−1 missed; 0 correct; +1 false active')
        fig.colorbar(gart,ax=axes[:,4],shrink=.6,label='Gate multiplier')
        finish(fig,f'fig08-support-gate-seed{seed}')
        for d in display:d.close()
        gate.close()
    margins=[r for v in data['reference_sensitivity'].values() for r in v['margins']]
    if margins:
        table('reference-margins',list(margins[0]),[list(r.values()) for r in margins])
        fig,axes=plt.subplots(4,2,figsize=(10.4,10.4),layout='constrained')
        for col,protocol in enumerate(('original','shorter')):
            for row,key in enumerate(('S','Ephi','bottom_current_NRMSE','power_trace_NRMSE')):
                subset=[r for r in margins if r['protocol']==protocol and r['metric']==key and r['candidate'].endswith('/E')]
                labels=[f"{r['seed']} vs "+('B_E' if r['baseline'].endswith('B_E') else 'F') for r in subset]
                x=np.arange(len(subset));scale=1e6 if key=='S' else (1000 if key=='Ephi' else 100)
                axes[row,col].bar(x-.17,[r['old_margin']*scale for r in subset],.34,label='Original reference',color='#536e83')
                axes[row,col].bar(x+.17,[r['new_margin']*scale for r in subset],.34,label='Refined reference',color='#d28d43')
                axes[row,col].axhline(0,color='k',lw=.7);axes[row,col].set_xticks(x,labels,rotation=20)
                title={'S':'S margin (×10⁶)','Ephi':'Phase RMS margin (×1000)',
                    'bottom_current_NRMSE':'Current margin (percentage points)',
                    'power_trace_NRMSE':'Power margin (percentage points)'}[key]
                axes[row,col].set_title(protocol+': '+title)
                axes[row,col].grid(axis='y',alpha=.2)
        axes[0,0].legend(fontsize=10.5)
        finish(fig,'fig09-reference-margins')
    # Both cycles of every new endpoint, not only the endpoint that crosses a gate.
    event_items=[(seed,role,cycle) for seed in (29,43) for role in ('E_C','E_R','E_I') for cycle in (0,1)]
    labels=[f'{seed}/{role[-1]}/{cycle+1}' for seed,role,cycle in event_items]
    x=np.arange(len(event_items))
    fig,axes=plt.subplots(2,1,figsize=(10.4,6.4),layout='constrained')
    for ax,key,label,threshold in zip(axes,('recall','timing_absolute'),
                                      ('Support recall','Onset-time error'),(.9,.005),strict=True):
        ov=[old[f'shorter/{s}/{r}']['cycles'][c][key] for s,r,c in event_items]
        nv=[new[f'shorter/{s}/{r}']['cycles'][c][key] for s,r,c in event_items]
        for j,(aold,anew) in enumerate(zip(ov,nv,strict=True)):
            if aold is not None and anew is not None:
                ax.plot([j-.10,j+.10],[aold,anew],color='#a4acb3',lw=1.2,zorder=1)
        ax.scatter(x-.10,ov,label='Original reference',color='#536e83',s=30,zorder=2)
        ax.scatter(x+.10,nv,label='Refined reference',color='#d28d43',marker='s',s=27,zorder=2)
        ax.axhline(threshold,color='k',ls=':',lw=1)
        ax.set_xticks(x,labels,rotation=30);ax.set_ylabel(label);ax.grid(axis='y',alpha=.2)
        ax.set_xlabel('Parent seed / continuation C, residual R or gated I / cycle')
    axes[0].legend(fontsize=10.5,ncol=2)
    finish(fig,'fig10-event-reference-sensitivity')
    deltas=[];refevents=[]
    for protocol,v in data['reference_sensitivity'].items():
        deltas.append([protocol]+[v['delta'][k] for k in ('S','Ephi','ET','EV','EI_rms','power_rms','q_rms')])
        for c,(o,n) in enumerate(zip(v['old_reference_events']['cycles'],v['new_reference_events']['cycles']),1):
            refevents.append([protocol,c,o['event_time'],n['event_time'],None if o['event_time'] is None or n['event_time'] is None else n['event_time']-o['event_time'],o['recovery_fraction'],n['recovery_fraction']])
    table('reference-deltas',['Protocol','delta S','delta phase','delta T/0.45','delta V','delta I RMS','delta power RMS','delta q RMS'],deltas)
    table('reference-events',['Protocol','Cycle','Old onset','Refined onset','Shift','Old recovery','Refined recovery'],refevents)
    # Full CSVs retain every field and cycle for all sixteen objects.
    allmetric=[];allevents=[];strictrows=[]
    for refname,records in data['records'].items():
        for name,r in records.items():
            allmetric.append([refname,name]+[r['metrics'][k] for k in ('S','Ephi','ET','EV','EI','bottom_current_NRMSE','power_trace_NRMSE','energy_error','local_joule_NRMSE')]+[r['strict_device_pass']])
            strictrows.append([refname,name,r['strict_device_pass'],r['metrics']['phase_max'],'; '.join(map(str,strict_failures(r))) or 'none'])
            for c in r['cycles']:allevents.append([refname,name,c['cycle']]+[c[k] for k in ('event_time','reference_event_time','recall','precision','mass_ratio','timing_absolute','recovery_fraction','false_negative_target_mass','false_positive_target_mass')])
    table('all-fixed-metrics',['Reference','Object','S','Ephi','ET','EV','EI','Bottom I','Power','Energy','Local q','Strict'],allmetric)
    table('all-fixed-events',['Reference','Object','Cycle','Onset','Ref onset','Recall','Precision','Mass','Timing','Recovery','FN mass','FP mass'],allevents)
    table('all-strict-failures',['Reference','Object','Strict','Maximum phase','Failed original requirements'],strictrows)
    (HERE/'build/revision-analysis.json').write_text(json.dumps({'scores':str(score.relative_to(ROOT)),
        'all_fixed_objects':len(old),'refined_objects':len(new),'model_executions':0,'linear_solves':0,
        'figure_times_selected_by_reference':False},indent=2),encoding='utf-8')
    print('Revision figures and complete tables generated from saved array scores')


if __name__=='__main__':main()
