"""Publication figures/tables from saved joint-protocol endpoints only."""
from __future__ import annotations
import argparse
import csv
import json
import shutil
from pathlib import Path
import numpy as np

from .phk_v23_lf11 import ROOT
from .phk_v23_lf11_joint import RUN

PAPER=ROOT/'paper/paper_v27'
NAMES=('parent','D_I','D_B','P_U','B_logit_waveform_contact')
LABELS={'parent':'V26 parent','D_I':'D_I','D_B':'D_B','P_U':'P_U','B_logit_waveform_contact':'Contact baseline'}
COLORS={'parent':'#777777','D_I':'#377eb8','D_B':'#4daf4a','P_U':'#e41a1c','B_logit_waveform_contact':'#984ea3'}


def render_mechanism(root=RUN,paper=PAPER):
    """Use existing own-field/audit evidence only; no new scientific probes."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    root,paper=Path(root),Path(paper)
    directory=paper/'figures';directory.mkdir(parents=True,exist_ok=True)
    diagnosis=json.loads((root/'equation-head-diagnosis.json').read_text())
    fig,axes=plt.subplots(2,2,figsize=(12,8),constrained_layout=True)
    keys=('bc_heater','bc_insulation','bc_phase_no_flux','bc_thermal')
    for i,role in enumerate(('D_I','D_B')):
        parts=json.loads((root/role/'boundary-subterms.json').read_text())['components']
        axes[0,0].bar(np.arange(4)+(i-.5)*.34,[parts[k] for k in keys],.34,label=role,color=COLORS[role])
    axes[0,0].set_xticks(np.arange(4),['Heater','Insulation','Phase no-flux','Thermal'])
    axes[0,0].set_yscale('log');axes[0,0].legend()
    axes[0,0].set_title('BC audit subterms: aggregate decrease hides heater increase')
    audits={r:json.loads((root/'electric_audit'/(r+'.json')).read_text()) for r in ('D_I','D_B')}
    a,b=audits['D_I'],audits['D_B']
    trace_key='heater_trace_rms'
    aggregates=[json.loads((root/r/'result.json').read_text())['fixed_physics_audit']['boundary'] for r in ('D_I','D_B')]
    heater=[json.loads((root/r/'boundary-subterms.json').read_text())['components']['bc_heater'] for r in ('D_I','D_B')]
    changes=[100*(aggregates[1]/aggregates[0]-1),100*(heater[1]/heater[0]-1),100*(b[trace_key]/a[trace_key]-1)]
    axes[0,1].bar(np.arange(3),changes,color=['#4daf4a','#e41a1c','#e69f00'])
    axes[0,1].axhline(0,color='k',lw=.7)
    axes[0,1].set_xticks(np.arange(3),['Aggregate BC','Heater BC subterm','Full heater trace RMS'])
    axes[0,1].set_ylabel('D_B relative to D_I (%)')
    axes[0,1].set_title('Same endpoints and known zero contact value')
    nodes=[r['step'] for r in diagnosis['records']]
    for head,style,color in (('temperature','o-','#d95f02'),('phase','s--','#7570b3')):
        values=[next(x['amplitude_to_full_gradient_norm'] for x in r['amplitude_tests']
                     if x['block']=='electric' and x['head']==head) for r in diagnosis['records']]
        axes[1,0].plot(nodes,values,style,label=head,color=color)
    axes[1,0].axhline(.25,color='k',ls=':',label='Frozen materiality floor')
    axes[1,0].set_xticks(nodes);axes[1,0].set_ylabel('Amplitude / full electric gradient norm')
    axes[1,0].set_title('Norm ratios are not contribution percentages');axes[1,0].legend(fontsize=8)
    for source,label,style,color in (('electric_amplitude','Electric amplitude','o-','#e41a1c'),
                                    ('observation','Observation','s-','#377eb8'),
                                    ('historical_momentum','Historical momentum','^-','#e69f00'),
                                    ('total_proposal','Total prospective update','D--','#111111')):
        values=[next(x['visible_directional_effect']['temperature'] for x in r['rows']
                     if x['source']==source and x['head']=='temperature') for r in diagnosis['records']]
        axes[1,1].plot(nodes,values,style,label=label,color=color)
    axes[1,1].set_yscale('symlog',linthresh=1e-10);axes[1,1].axhline(0,color='k',lw=.7)
    axes[1,1].set_xticks(nodes);axes[1,1].set_ylabel('Visible temperature-error directional effect')
    axes[1,1].set_title('Positive is locally harmful; total can have the opposite sign')
    axes[1,1].legend(fontsize=8)
    for ax in axes.flat:ax.grid(axis='y',alpha=.15)
    for ax in axes[1]:ax.set_xlabel('Saved Adam update')
    fig.suptitle('Constraint subterms and optimizer directions identify different limitations',fontsize=13)
    for ext in ('png','pdf'):fig.savefig(directory/('lf11-joint-mechanism.'+ext),dpi=200)
    plt.close(fig)


def parent_audit_path(root,extension):
    packaged=Path(root)/'electric_audit'/('parent.'+extension)
    return packaged if packaged.exists() else ROOT/'outputs/runs/20260912-lf11-v-pde-increment/electric_audit'/('post.'+extension)


def package_evidence(root=RUN,paper=PAPER):
    root,paper=Path(root),Path(paper)
    destination=paper/'evidence';destination.mkdir(parents=True,exist_ok=True)
    names=('campaign.json','calibration.json','frozen-config.json','training-source.json','input-identity.json',
           'fixed-pools.pt','parent.pt','parent-visible.json','parent-physics-audit.json','compute-closure.json',
           'evaluation.json','evaluation-traces.npz','field-snapshots.npz','equation-head-diagnosis.json','conditional-decision.json')
    for name in names:shutil.copy2(root/name,destination/name)
    campaign=json.loads((root/'campaign.json').read_text())
    for role,result in campaign['results'].items():
        folder=destination/role;folder.mkdir(exist_ok=True)
        for name in ('result.json','adam-telemetry.jsonl','lbfgs-telemetry.jsonl','checkpoint.pt','invalid-checkpoint.pt','boundary-subterms.json'):
            if (root/role/name).exists():shutil.copy2(root/role/name,folder/name)
        if role=='P_U':
            for step in (500,1000,1500):
                name=f'adam-{step}.pt'
                if (root/role/name).exists():shutil.copy2(root/role/name,folder/name)
    audits=destination/'electric_audit';audits.mkdir(exist_ok=True)
    for role in campaign['results']:
        for ext in ('json','npz'):
            name=role+'.'+ext
            if (root/'electric_audit'/name).exists():shutil.copy2(root/'electric_audit'/name,audits/name)
    for ext in ('json','npz'):shutil.copy2(parent_audit_path(root,ext),audits/('parent.'+ext))
    (destination/'README.md').write_text('''# Selected local evidence

- [Campaign and actual counts](campaign.json), [frozen configuration](frozen-config.json), [once-only calibration](calibration.json), and [saved fixed pools](fixed-pools.pt).
- [Common parent](parent.pt), [complete visible audit](parent-visible.json), [independent physics audit](parent-physics-audit.json), [input identity](input-identity.json), and [pre-training source identity](training-source.json).
- D_I, D_B, and P_U directories contain results, telemetry, and final accepted model/optimizer states. P_U additionally contains the three actual Adam states used for diagnosis. The other arms' intermediate states remain in the original run.
- [Evaluation](evaluation.json), [device/event traces](evaluation-traces.npz), [display field snapshots](field-snapshots.npz), [three-node direction diagnosis](equation-head-diagnosis.json), and [conditional decision](conditional-decision.json).
- The electric_audit directory preserves own-model boundary traces, AD, signed FV current/power components and summaries. Parent arrays are exact copies of the previously saved v26 post audit, not a rerun.
- [Actual compute closure](compute-closure.json) records process termination before nominal reference evaluation. No cloud instance or stress data are involved.

This is a local package. The sparse bundle remains at paper_v24/evidence/input/sparse.npz; the inherited final parent is also released in paper_v26. Full new own-field predictions and the full fixed nominal reference remain local to the original run/reference paths. Two reference peak snapshots are supplied for display only, not as a training carrier.

Figures and tables can be rebuilt directly from this selected pack without a reference read, training, or an old run tree:

```powershell
.\\.venv\\Scripts\\python.exe -m pinn_pcm_sci.phk_v23_lf11_joint_report --root paper/paper_v27/evidence --paper outputs/reproduction/lf11-joint-figures
```

The containing source files plus their saved runtime identity define the implementation. Numerical validity, matched effect, strict device capability and independent confirmation remain separate claims; consult the manuscript and claim matrix.
''',encoding='utf-8')


def render(root=RUN,paper=PAPER):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    root,paper=Path(root),Path(paper)
    result=json.loads((root/'evaluation.json').read_text())
    records=result['records']; names=[n for n in NAMES if records.get(n,{}).get('valid')]
    figure_dir=paper/'figures'; figure_dir.mkdir(parents=True,exist_ok=True)
    table_dir=paper/'tables'; table_dir.mkdir(exist_ok=True)
    plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False,
                         'font.family':'DejaVu Sans','savefig.dpi':200})
    with np.load(root/'evaluation-traces.npz',allow_pickle=False) as f:
        t=f['time']; ref_i=f['reference_current']; ref_p=f['reference_power']
        traces={n:{k:f[n+'__'+k] for k in ('roi_active_fraction','top_current','bottom_current','joule_power','input_power')} for n in names}
        native=f['native_reference_readout_check__roi_active_fraction']
    audits={}
    for name in names:
        path=parent_audit_path(root,'json') if name=='parent' else root/'electric_audit'/(name+'.json')
        if path.exists(): audits[name]=json.loads(path.read_text())
    def save(fig,stem):
        for ext in ('png','pdf'):fig.savefig(figure_dir/(stem+'.'+ext))
        plt.close(fig)
    positions=np.arange(len(names))
    fig,axes=plt.subplots(2,3,figsize=(12,7.2),constrained_layout=True)
    metrics=(('S','Phase symmetric difference'),('Ephi','Phase RMS (raw)'),('ET','Temperature RMS / 0.45'),
             ('EV','Potential RMS (raw)'),('bottom_current_NRMSE','Bottom-current NRMSE'),('power_trace_NRMSE','Joule-power trace NRMSE'))
    for ax,(metric,title) in zip(axes.flat,metrics):
        ax.bar(positions,[records[n]['metrics'][metric] for n in names],color=[COLORS[n] for n in names])
        ax.set_xticks(positions,[LABELS[n] for n in names],rotation=30,ha='right')
        ax.set_title(title); ax.set_ylim(bottom=0); ax.grid(axis='y',alpha=.18)
        ax.ticklabel_format(axis='y',style='sci',scilimits=(-3,3))
    fig.suptitle('Same-parent comparison: continuation, soft BC, and interior PDE',fontsize=13)
    save(fig,'lf11-joint-matched-main')

    fig,axes=plt.subplots(3,2,figsize=(12.5,10.4),constrained_layout=True)
    for name in names:
        tr=traces[name]; c=COLORS[name]
        axes[0,0].plot(t,tr['roi_active_fraction'],color=c,label=LABELS[name])
        cycles=records[name]['cycles']
        axes[0,1].plot([1,2],[v['recall'] for v in cycles],'o-',color=c)
        axes[0,1].plot([1,2],[v['precision'] for v in cycles],'s--',color=c,alpha=.8)
        axes[1,0].plot(t,tr['top_current'],color=c)
        axes[1,0].plot(t,tr['bottom_current'],color=c,ls='--',alpha=.8)
        axes[1,1].plot(t,tr['joule_power'],color=c)
        axes[1,1].plot(t,tr['input_power'],color=c,ls='--',alpha=.8)
    axes[0,0].plot(t,native,'k',lw=1.6,label='Fixed reference')
    axes[0,0].axhline(.02,color='k',ls=':',lw=.7)
    axes[0,0].legend(fontsize=7,ncol=3)
    axes[0,0].set_title('Two-cycle ROI active fraction')
    axes[0,1].set_title('Cycle support: recall (solid), precision (dashed)')
    axes[0,1].set_xticks([1,2]);axes[0,1].set_ylim(0,1.03)
    axes[1,0].plot(t,ref_i,'k',lw=1.6)
    axes[1,0].set_title('Top current (solid), bottom current (dashed)')
    axes[1,1].plot(t,ref_p,'k',lw=1.6)
    axes[1,1].set_title('Joule power (solid), input power (dashed)')
    anames=[n for n in names if n in audits]
    def signed_stack(ax,keys,labels,colors,title):
        positive=np.zeros(len(anames)); negative=np.zeros(len(anames)); x=np.arange(len(anames))
        for key,label,color in zip(keys,labels,colors):
            values=np.array([audits[n]['summaries'][key]['signed_integral'] for n in anames])
            bottom=np.where(values>=0,positive,negative)
            ax.bar(x,values,bottom=bottom,label=label,color=color)
            positive+=np.maximum(values,0);negative+=np.minimum(values,0)
        ax.axhline(0,color='k',lw=.6); ax.set_xticks(x,[LABELS[n] for n in anames])
        ax.set_title(title);ax.legend(fontsize=7,ncol=2)
    signed_stack(axes[2,0],['I_trace','I_drop'],['Trace term','Cell-to-boundary drop'],['#e69f00','#56b4e9'],
                 'Signed integrals of bottom-current terms')
    signed_stack(axes[2,1],['P_internal','P_top','P_trace','P_cross','P_drop'],
                 ['Internal','Top','Bottom trace squared','Bottom cross term','Bottom drop squared'],
                 ['#bbbbbb','#999933','#e69f00','#cc6677','#56b4e9'],'Signed integrals of dissipation terms')
    for ax in axes.flat:ax.grid(alpha=.15)
    for ax in axes[:2,:].flat:ax.set_xlabel('Time (dimensionless)' if ax is not axes[0,1] else 'Cycle')
    fig.suptitle('Event and device consequences; signed identities are not causal shares',fontsize=13)
    save(fig,'lf11-joint-events-device')

    fig,axes=plt.subplots(len(anames),3,figsize=(12.5,2.4*len(anames)),
                          sharex=True,sharey='col',constrained_layout=True)
    for row,name in enumerate(anames):
        path=parent_audit_path(root,'npz') if name=='parent' else root/'electric_audit'/(name+'.npz')
        with np.load(path,allow_pickle=False) as f:
            audit={k:f[k] for k in f.files}
        at=audit['time']
        axes[row,0].plot(at,np.max(np.abs(audit['heater_trace']),axis=1),color=COLORS[name])
        axes[row,0].set_ylabel(LABELS[name])
        for key,label,color,style in (
            ('bottom_current','FV bottom','#000000','-'),('I_trace','Trace','#e69f00','-'),
            ('I_drop','Drop','#56b4e9','-'),('AD_bottom_current','Own-model AD','#009e73','--')):
            axes[row,1].plot(at,audit[key],color=color,ls=style,label=label)
        for key,label,color,style in (
            ('P_internal','Internal','#666666','-'),('P_top','Top','#999933','-'),
            ('P_bottom','Bottom total','#e69f00','-'),('P_cross','Bottom cross','#cc6677','--')):
            axes[row,2].plot(at,audit[key],color=color,ls=style,label=label)
        for ax in axes[row]:ax.axhline(0,color='k',lw=.4);ax.grid(alpha=.15)
    for ax,title in zip(axes[0],('Maximum absolute heater trace','Signed bottom-current terms','Dissipation and signed cross term')):
        ax.set_title(title,fontsize=9)
    axes[0,1].legend(fontsize=7,ncol=2);axes[0,2].legend(fontsize=7,ncol=2)
    for ax in axes[-1]:ax.set_xlabel('Time (dimensionless)')
    fig.suptitle('Own-field electrical diagnostics; AD is not reference flux',fontsize=13)
    save(fig,'lf11-joint-contact-diagnostics')

    with np.load(root/'field-snapshots.npz',allow_pickle=False) as f:
        snap={k:f[k] for k in f.files}
    rows=['reference']+names
    tmax=max(float(snap[n+'__temperature'][0].max()) for n in rows)
    fig,axes=plt.subplots(len(rows),3,figsize=(10.5,2.0*len(rows)),constrained_layout=True)
    for row,name in enumerate(rows):
        label='Fixed reference' if name=='reference' else LABELS[name]
        for col,(field,index) in enumerate((('temperature',0),('phase',0),('phase',1))):
            a=axes[row,col]
            artist=a.imshow(snap[name+'__'+field][index].reshape(len(snap['z']),len(snap['x'])),
                            origin='lower',extent=(-1,1,0,1),aspect='auto',vmin=0,vmax=tmax if field=='temperature' else 1,
                            cmap='inferno' if field=='temperature' else 'viridis')
            a.set_title(f'{label}: {field}, t={snap["times"][index]:.4f}',fontsize=8)
            a.set_xlabel('x');a.set_ylabel('z')
            if row==0 and col==0:t_artist=artist
            if row==0 and col==1:p_artist=artist
    fig.colorbar(t_artist,ax=axes[:,0],shrink=.6,label='Temperature')
    fig.colorbar(p_artist,ax=axes[:,1:],shrink=.6,label='Phase')
    fig.suptitle('Fixed endpoint fields at the two reference cycle peaks',fontsize=13)
    save(fig,'lf11-joint-fields')

    all_metrics=sorted({k for r in records.values() if r.get('metrics') for k in r['metrics']})
    with (table_dir/'all-endpoint-metrics.csv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=['role','valid','strict_device_pass']+all_metrics)
        writer.writeheader()
        for name,r in records.items():writer.writerow({'role':name,'valid':r['valid'],'strict_device_pass':r.get('strict_device_pass',False),**(r.get('metrics') or {})})
    keys=['S','Ephi','ET','EV','EI','bottom_current_NRMSE','power_trace_NRMSE','energy_error']
    lines=['# Same-parent fixed endpoints','','Raw S/Ephi/EV and normalized T/current/power errors retain their original definitions.','',
           '| Role | '+' | '.join(keys)+' | Strict |','|---|'+'---:|'*len(keys)+'---|']
    for name in NAMES:
        r=records[name]
        if not r['valid']:lines.append('| '+name+' | '+' | '.join(['INVALID']*len(keys))+' | False |');continue
        lines.append('| '+LABELS[name]+' | '+' | '.join(f'{r["metrics"][k]:.9g}' for k in keys)+f' | {r["strict_device_pass"]} |')
    (table_dir/'joint-endpoints.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    lines=['# Two-cycle events','','| Role | Cycle | Recall | Precision | Mass ratio | Timing absolute | Recovery |','|---|---:|---:|---:|---:|---:|---:|']
    for name in NAMES:
        for i,c in enumerate(records[name].get('cycles',[])):
            recovery=c.get('recovery_fraction',c.get('recovery',None))
            def show(v):return 'None' if v is None else f'{v:.9g}'
            lines.append('| '+LABELS[name]+f' | {i+1} | '+' | '.join(show(v) for v in (c['recall'],c['precision'],c['mass_ratio'],c['timing_absolute'],recovery))+' |')
    (table_dir/'joint-events.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    lines=['# Matched contrasts','','Reconstruction and limited-function signals are separate outcomes, not a union success criterion.','',
           '| Contrast | Reconstruction signal | Function signal |','|---|---|---|']
    for name,pair in result['matched_pairs'].items():lines.append(f'| {name} | {pair["reconstruction"]["passed"]} | {pair["function"]["passed"]} |')
    (table_dir/'matched-contrasts.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    campaign=json.loads((root/'campaign.json').read_text())
    fit_audit={'parent':{'visible':json.loads((root/'parent-visible.json').read_text()),
                         'fixed_physics_audit':json.loads((root/'parent-physics-audit.json').read_text())},
               **campaign['results']}
    lines=['# Complete visible fitting and independent physics audit','',
           'All rows use the same complete visible measure and the same independent audit pool. Calibration-pool values are not substituted in audit ratios.','',
           '| Role | Visible V RMS / .72 | Visible T RMS / .45 | Visible raw phase RMS | Phase logit objective | Audit J_U | Audit BC |',
           '|---|---:|---:|---:|---:|---:|---:|']
    for name,r in fit_audit.items():
        if 'visible' not in r:continue
        v,a=r['visible'],r['fixed_physics_audit']
        values=(v['V_normalized_rms'],v['T_normalized_rms']['all'],v['phase_raw_visible_rms'],
                v['phase_logit_objective'],a['J_U'],a['boundary'])
        lines.append('| '+LABELS[name]+' | '+' | '.join(f'{x:.10g}' for x in values)+' |')
    (table_dir/'fitting-physics-audits.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    keys=('bc_insulation','bc_heater','bc_phase_no_flux','bc_thermal','bc_top_potential')
    lines=['# Endpoint BC subterms on the frozen audit pool','',
           'Original per-window denominator and residual scales are retained. Values sum to the existing aggregate BC audit; these are scalar evaluations, not extra gradient nodes.','',
           '| Role | '+' | '.join(keys)+' |','|---|'+'---:|'*len(keys)]
    for name in campaign['results']:
        path=root/name/'boundary-subterms.json'
        if not path.exists():continue
        row=json.loads(path.read_text())['components']
        lines.append('| '+name+' | '+' | '.join(f'{row[key]:.10g}' for key in keys)+' |')
    (table_dir/'endpoint-boundary-subterms.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')

    diagnosis=json.loads((root/'equation-head-diagnosis.json').read_text())
    lines=['# Frozen three-node amplitude tests','',
           'Positive visible-error effects are local prospective harm. A consistent material channel at all three nodes is required; these are not executed diagnostic updates.','',
           '| Adam node | Block | Head | Amplitude / full gradient norm | Effect on visible error | Direct BC dominates | Supported |',
           '|---:|---|---|---:|---:|---|---|']
    diagnostic_rows=[]
    for rec in diagnosis['records']:
        for test in rec['amplitude_tests']:
            ratio=test['amplitude_to_full_gradient_norm']
            ratio='None' if ratio is None else f'{ratio:.8g}'
            lines.append(f'| {rec["step"]} | {test["block"]} | {test["head"]} | {ratio} | '
                         f'{test["amplitude_effect_on_visible_head_error"]:.8g} | {test["direct_BC_dominates"]} | {test["directional_channel_supported"]} |')
        for row in rec['rows']:
            diagnostic_rows.append({'step':rec['step'],'source':row['source'],'head':row['head'],
                                    'raw_gradient_norm':row['raw_gradient_norm'],'adam_direction_norm':row['adam_direction_norm'],
                                    **{k+'_effect':v for k,v in row['visible_directional_effect'].items()}})
    (table_dir/'three-node-amplitude.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    if diagnostic_rows:
        with (table_dir/'equation-head-directions.csv').open('w',encoding='utf-8',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(diagnostic_rows[0]));writer.writeheader();writer.writerows(diagnostic_rows)
    render_mechanism(root,paper)
    print(json.dumps({'report_figures_and_tables_ready':True,'paper':str(paper)}),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=RUN);p.add_argument('--paper',type=Path,default=PAPER)
    a=p.parse_args();render(a.root,a.paper)
