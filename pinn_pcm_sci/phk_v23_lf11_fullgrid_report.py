"""Publication figures from completed V31 scores only; no model or solver calls."""
from __future__ import annotations
import argparse,csv,json
from pathlib import Path
import numpy as np
from .phk_v23_lf11 import ROOT,save_json
from .phk_v23_lf11_fullgrid import RUN
from .phk_v23_lf11_training_coupling import read

PAPER=ROOT/'paper/paper_v31'


def table(directory,name,columns,rows):
    with (directory/(name+'.csv')).open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=columns);w.writeheader();w.writerows(rows)
    lines=['| '+' | '.join(columns)+' |','|'+'---|'*len(columns)]
    for row in rows:
        lines.append('| '+' | '.join(f'{row[k]:.10g}' if isinstance(row.get(k),float) else str(row.get(k)) for k in columns)+' |')
    (directory/(name+'.md')).write_text('\n'.join(lines)+'\n',encoding='utf-8')


def report(root=RUN,confirmation=None):
    data=read(root/'evaluation/results.json');r=data['records'];cfg=read(root/'frozen-config.json')
    tables=PAPER/'tables';figures=PAPER/'figures'
    tables.mkdir(parents=True,exist_ok=True);figures.mkdir(exist_ok=True)
    refs=['P_E','D_E','B_E'];soft=['F_raw','F_full','F_bal']
    names=refs+[s+'/'+m for s in soft for m in ('network','projected')]
    keys=['S','Ephi','ET','EV','EI','bottom_current_NRMSE','power_trace_NRMSE','energy_error','local_joule_NRMSE']
    rows=[dict(role=n,valid=r[n]['valid'],**{k:(r[n].get('metrics') or {}).get(k) for k in keys},strict=r[n].get('strict_device_pass')) for n in names]
    table(tables,'fixed-endpoints',list(rows[0]),rows)
    ek=['cycle','recall','precision','mass_ratio','timing_absolute','event_time','recovery_fraction']
    table(tables,'complete-events',['role',*ek],[dict(role=n,**{k:c.get(k) for k in ek}) for n in names for c in r[n].get('cycles',[])])
    pairs=[]
    for name,decision in data['decision']['comparisons'].items():
        candidate,base=name.split('_vs_',1)
        if candidate=='E':candidate='P_E'
        if base=='E':base='P_E'
        if name.endswith('_projection_vs_network'):
            s=name.split('_projection_vs_network')[0];candidate=s+'/projected';base=s+'/network'
        if candidate not in r or base not in r:continue
        c,b=r[candidate].get('metrics'),r[base].get('metrics')
        pairs.append(dict(candidate=candidate,base=base,A=decision['A']['passed'],B=decision['B']['passed'],
            **{k+'_relative_percent':100*(c[k]/b[k]-1) if c and b and b.get(k) not in (None,0) and c.get(k) is not None else None for k in keys},
            current_percentage_point_change=100*(c['bottom_current_NRMSE']-b['bottom_current_NRMSE']) if c and b else None,
            power_percentage_point_change=100*(c['power_trace_NRMSE']-b['power_trace_NRMSE']) if c and b else None))
    if pairs:table(tables,'matched-changes',list(pairs[0]),pairs)
    # Time aggregation of saved traces only: no new prediction, solve or labels.
    with np.load(root/'evaluation/traces.npz',allow_pickle=False) as trace:
        time=trace['time'];power_ref=trace['reference_power']
        reference_energy=np.trapezoid(power_ref,time)
        integration=[]
        for name in ('P_E','F_raw/projected','F_full/projected','F_bal/projected','D_E','B_E'):
            error=trace[name+'__joule_power']-power_ref
            signed=np.trapezoid(error,time);absolute=np.trapezoid(np.abs(error),time)
            integration.append(dict(role=name,signed_relative_energy_error=signed/reference_energy,
                absolute_relative_energy_error=abs(signed)/reference_energy,
                normalized_integrated_absolute_power_error=absolute/reference_energy,
                signed_error_cancellation=1-abs(signed)/absolute if absolute>1e-15 else None))
    table(tables,'power-time-aggregation',list(integration[0]),integration)
    terminal=read(root/'F_full/terminal.json');stats=terminal['statistics'];lb=terminal['lbfgs']
    pred=read(root/'F_full/projected/prediction.json')
    counts=dict(role='F_full',Adam=terminal['adam_updates'],complete_evaluations=lb['evaluations'],
        accepted_steps=lb['accepted_steps'],termination=lb['termination'],eta=terminal['eta'],
        training_forward=stats['electrical']['forward_solves'],training_adjoint=stats['electrical']['adjoint_solves'],
        inference_forward=pred['electrical_counts']['forward_solves'],**stats['explicit_work'])
    table(tables,'execution-counts',list(counts),[counts])
    diag=read(root/'F_full/spatial-electric-diagnostic.json')
    dr=[dict(time=v['time'],mass=v['mass'],sampled=v['sampled'],full=v['full'],
        **{k+'_mean':d['mean'] for k,d in v['bins'].items()},
        **{k+'_full_volume_contribution':d['full_volume_contribution'] for k,d in v['bins'].items()}) for v in diag['rows']]
    table(tables,'electric-spatial-diagnostic',list(dr[0]),dr)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.spines.top':False,'axes.spines.right':False,'savefig.dpi':180})
    colors={'P_E':'#216b9b','D_E':'#7c8994','B_E':'#31845c','F_raw':'#c8892b','F_full':'#ab4056','F_bal':'#80569c'}
    shown=['P_E','F_raw/projected','F_full/projected','F_bal/projected','D_E','B_E']
    labels=['E','F raw\nproj.','F full\nproj.','F bal\nproj.','D E','B E']
    def save(fig,name):
        for ext in ('png','pdf'):fig.savefig(figures/(name+'.'+ext))
        plt.close(fig)
    def values(key):return [(r[n].get('metrics') or {}).get(key,np.nan) for n in shown]
    def bar(ax,key,title,factor=1.):
        vals=np.array(values(key))*factor
        ax.bar(np.arange(len(shown)),vals,color=[colors[n.split('/')[0]] for n in shown])
        ax.set(xticks=np.arange(len(shown)),xticklabels=labels,title=title,ylim=(0,None));ax.grid(axis='y',alpha=.18)
        for i,v in enumerate(vals):
            if np.isfinite(v):ax.text(i,v,f'{v:.3g}',ha='center',va='bottom',fontsize=8)
    def paired(ax,key,title):
        pos=0
        for s in soft:
            vals=[(r[s+'/'+m].get('metrics') or {}).get(key,np.nan)*100 for m in ('network','projected')]
            ax.plot([pos,pos+1],vals,'o-',color=colors[s],label=s);pos+=3
        for ref in refs:
            ax.axhline(r[ref]['metrics'][key]*100,color=colors[ref],ls='--',label=ref)
        ax.set(yscale='log',title=title,ylabel='NRMSE (%) / log scale',xticks=[0,1,3,4,6,7],
            xticklabels=['raw\nnet','raw\nproj','full\nnet','full\nproj','bal\nnet','bal\nproj'])
        ax.grid(axis='y',alpha=.18)
    fig,ax=plt.subplots(2,3,figsize=(15,8.5),constrained_layout=True)
    bar(ax[0,0],'bottom_current_NRMSE','Common projection: current NRMSE (%)',100)
    bar(ax[0,1],'power_trace_NRMSE','Common projection: power NRMSE (%)',100)
    bar(ax[0,2],'S','Phase-region symmetric difference (x 1e-3)',1000)
    bar(ax[1,0],'Ephi','Raw ROI phase RMS',1)
    paired(ax[1,1],'bottom_current_NRMSE','Same learned state: current repair')
    paired(ax[1,2],'power_trace_NRMSE','Same learned state: power repair')
    ax[1,2].legend(fontsize=7,ncol=2)
    fig.suptitle('Full spatial electric integration: one changed training term\nFixed endpoints; shared fine-grid electrical readout',fontsize=14)
    save(fig,'fullgrid-counterfactual')
    fig,ax=plt.subplots(2,3,figsize=(14,8),constrained_layout=True)
    for a,key,title,threshold in zip(ax.flat,ek[1:],['Recall','Precision','Mass ratio','Absolute event-time error','Event time','Recovery fraction'],[.9,.8,[.8,1.2],.005,None,None]):
        for n,label in zip(shown,labels):
            if r[n].get('valid'):
                a.plot([1,2],[c.get(key) for c in r[n]['cycles']],marker='o',lw=1.2,color=colors[n.split('/')[0]],label=label.replace('\n',' '))
        if threshold is not None:
            for v in np.atleast_1d(threshold):a.axhline(v,ls=':',color='#666',lw=.8)
        a.set(title=title,xticks=[1,2],xlabel='Cycle',ylim=(0,None));a.grid(alpha=.15)
    ax[0,0].legend(fontsize=7);fig.suptitle('Complete two-cycle criteria; paired projection cannot change events')
    save(fig,'complete-events')
    fig,ax=plt.subplots(1,2,figsize=(12,4.5),constrained_layout=True)
    for k,label in [('sampled','128 sampled cells'),('full','3200-cell volume mean')]:
        ax[0].plot([v['time'] for v in dr],np.maximum([v[k] for v in dr],1e-15),'o-',label=label,ms=3)
    for k in ('heater_adjacent','other_boundary','interior'):
        ax[1].plot([v['time'] for v in dr],np.maximum([v[k+'_full_volume_contribution'] for v in dr],1e-15),'o-',label=k,ms=3)
    for a in ax:a.set(xlabel='Original fixed physics time',yscale='log',ylabel='Electric residual squared');a.legend(fontsize=8);a.grid(alpha=.15)
    ax[0].set_title('F_full endpoint: two spatial integration rules')
    ax[1].set_title('Disjoint region contributions to full mean')
    fig.suptitle('Reporting diagnostic; zero-drive zeros displayed at 1e-15')
    save(fig,'electric-spatial-diagnostic')
    # Saved peak snapshots only: display times never select an endpoint.
    snapshots={}
    figure_input=root/'phase-figure-input.npz'
    sources=([figure_input] if figure_input.exists() else
             [ROOT/cfg['historical_root']/'evaluation/snapshots.npz',
              ROOT/cfg['training_coupling_root']/'evaluation/snapshots.npz',
              root/'evaluation/snapshots.npz'])
    for source in sources:
        with np.load(source,allow_pickle=False) as archive:
            snapshots.update({k:archive[k].copy() for k in archive.files})
    spatial=['reference','P_E','F_raw/projected','F_full/projected','D_E','B_E']
    if not figure_input.exists():
        np.savez_compressed(figure_input,**{k:snapshots[k] for k in
            ['x','z','phase_times',*[name+'__phase' for name in spatial]]})
    nx,nz=len(snapshots['x']),len(snapshots['z'])
    fig,ax=plt.subplots(len(spatial),2,figsize=(10,11),constrained_layout=True)
    for i,name in enumerate(spatial):
        for cycle in range(2):
            a=ax[i,cycle];key=name+'__phase'
            if key not in snapshots:a.axis('off');continue
            artist=a.imshow(snapshots[key][cycle].reshape(nz,nx),origin='lower',extent=(-1,1,0,1),
                vmin=0,vmax=1,cmap='viridis',aspect='auto')
            a.plot([-.35,.35],[0,0],color='black',lw=3,clip_on=False)
            a.set(title=name.replace('/projected',' + projection')+f" / t={snapshots['phase_times'][cycle]:.4f}",xlabel='x',ylabel='z')
    fig.colorbar(artist,ax=ax,shrink=.6,label='Phase fraction')
    fig.suptitle('Two-dimensional phase structure at common reference peak times\nHeater footprint marked at the bottom boundary; display only')
    save(fig,'phase-fields')
    clean=[];clean_events=[];clean_effects=[];clean_fit=[];clean_execution=[];clean_decisions=[]
    if confirmation:
        for seed in cfg['confirmation']['seeds']:
            file=confirmation/f'seed-{seed}/evaluation/results.json'
            if not file.exists():continue
            data_b=read(file);cr=data_b['records'];soft_b=data_b['decision']['selected_soft']
            for comparison_name in ('E_vs_soft','soft_vs_E','E_vs_B_E','soft_vs_B_E'):
                compared=data_b['decision'][comparison_name]
                for layer in ('A','B'):
                    decision_item=compared[layer]
                    clean_decisions.append(dict(seed=seed,comparison=comparison_name,layer=layer,
                        passed=decision_item['passed'],
                        unmet_gain=','.join(k for k,v in decision_item.get('gain',{}).items() if not v),
                        failed_noninferiority=','.join(k for k,v in decision_item.get('noninferior',{}).items() if not v),
                        invalid_reason=decision_item.get('reason','')))
            seed_root=file.parent.parent
            fit=read(seed_root/'common-fit/fit-summary.json')
            cal=read(seed_root/'calibration.json')
            clean_fit.append(dict(seed=seed,Adam=fit['adam_updates'],complete_evaluations=fit['complete_evaluations'],
                initial_complete_observation_objective=fit['original_complete_objective'],
                final_complete_observation_objective=fit['final_complete_objective'],
                visible_V_RMS_over_072=np.sqrt(fit['final_components']['obs_V']),
                visible_T_RMS_over_045=np.sqrt(fit['final_components']['obs_T']),
                phase_logit_loss=fit['final_components']['obs_phase'],a_s=cal['aE'],b_s=cal['bE'],
                old_V_gate=fit['old_V_gate_applied'],seed_rescue=fit['seed_rescue']))
            for arm in ('E',soft_b):
                endpoint=read(seed_root/arm/'terminal.json');lc=endpoint['lbfgs'];sc=endpoint['statistics']['electrical']
                pc=read(seed_root/arm/'projected/prediction.json')['electrical_counts']
                clean_execution.append(dict(seed=seed,role=arm,Adam=endpoint['adam_updates'],
                    complete_evaluations=lc['evaluations'],accepted_steps=lc['accepted_steps'],termination=lc['termination'],
                    training_forward=sc['forward_solves'],training_adjoint=sc['adjoint_solves'],inference_forward=pc['forward_solves']))
            for role in ('E/projected',soft_b+'/network',soft_b+'/projected','B_E'):
                rr=cr[role]
                clean.append(dict(seed=seed,role=role,valid=rr['valid'],**{k:(rr.get('metrics') or {}).get(k) for k in keys},strict=rr.get('strict_device_pass')))
                clean_events.extend(dict(seed=seed,role=role,**{k:c.get(k) for k in ek}) for c in rr.get('cycles',[]))
            ce,cs=cr['E/projected'].get('metrics'),cr[soft_b+'/projected'].get('metrics')
            clean_effects.append(dict(seed=seed,comparator=soft_b,
                A=data_b['decision']['E_vs_soft']['A']['passed'],B=data_b['decision']['E_vs_soft']['B']['passed'],
                **{k+'_relative_percent':100*(ce[k]/cs[k]-1) if ce and cs and cs.get(k) not in (None,0) and ce.get(k) is not None else None for k in keys},
                current_percentage_point_change=100*(ce['bottom_current_NRMSE']-cs['bottom_current_NRMSE']) if ce and cs else None,
                power_percentage_point_change=100*(ce['power_trace_NRMSE']-cs['power_trace_NRMSE']) if ce and cs else None))
        if clean:
            table(tables,'clean-initializations',list(clean[0]),clean)
            table(tables,'clean-complete-events',['seed','role',*ek],clean_events)
            table(tables,'clean-paired-effects',list(clean_effects[0]),clean_effects)
            table(tables,'clean-common-fit',list(clean_fit[0]),clean_fit)
            table(tables,'clean-execution',list(clean_execution[0]),clean_execution)
            table(tables,'clean-adjudication',list(clean_decisions[0]),clean_decisions)
            fig,ax=plt.subplots(1,3,figsize=(13,4.5),constrained_layout=True)
            for a,key,title in zip(ax,['Ephi','bottom_current_NRMSE','power_trace_NRMSE'],['Raw phase RMS','Current NRMSE (%)','Power NRMSE (%)']):
                display_scale=1 if key=='Ephi' else 100
                for seed in cfg['confirmation']['seeds']:
                    rows=[v for v in clean if v['seed']==seed and v['role'].endswith('/projected')]
                    if len(rows)==2:a.plot([0,1],[display_scale*v[key] for v in rows],'o-',label=f'seed {seed}')
                baseline=next(v for v in clean if v['role']=='B_E')
                a.axhline(display_scale*baseline[key],ls='--',color='0.45',label='B_E (same projection)')
                a.set(xticks=[0,1],xticklabels=['E','Locked soft + projection'],title=title,ylim=(0,None));a.legend();a.grid(alpha=.15)
            fig.suptitle('Clean initialization pairs shown separately; historical seed 17 excluded')
            save(fig,'clean-pairs')
    summary=dict(stage_A_counts=counts,decision=data['decision'],clean_rows=clean,
        spatial_integrals={k:diag[k] for k in ('sampled_integral','full_integral')})
    save_json(PAPER/'report-summary.json',summary)
    print(json.dumps(dict(report=str(PAPER),selection=data['decision']['selection'],clean_rows=len(clean))))
    return summary


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=RUN);p.add_argument('--confirmation',type=Path)
    a=p.parse_args();report(a.root,a.confirmation)
