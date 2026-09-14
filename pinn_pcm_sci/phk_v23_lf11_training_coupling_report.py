"""Render saved V30 evidence; no checkpoint, reference or solver is used."""
from __future__ import annotations
import argparse,csv,json
from pathlib import Path
import numpy as np
from .phk_v23_lf11 import ROOT
from .phk_v23_lf11_training_coupling import RUN,read,save_json


def report(root=RUN):
    data=read(root/'evaluation/results.json');cfg=read(root/'frozen-config.json')
    records=data['records'];decision=data['decision'];diag=read(root/'eta-calibration.json')
    paper=ROOT/'paper/paper_v30';figures=paper/'figures';tables=paper/'tables'
    figures.mkdir(parents=True,exist_ok=True);tables.mkdir(exist_ok=True)
    ordered=['E0','D_E','P_E','B_E','F_raw/network','F_raw/projected','F_bal/network','F_bal/projected','V29_D_C','V29_P1','V29_P_kappa']
    names=[r for r in ordered if r in records]
    keys=['S','Ephi','ET','EV','EI','bottom_current_NRMSE','power_trace_NRMSE','energy_error','local_joule_NRMSE']
    def table(name,columns,rows):
        with (tables/(name+'.csv')).open('w',newline='',encoding='utf-8') as f:
            w=csv.DictWriter(f,fieldnames=columns);w.writeheader();w.writerows(rows)
        lines=['| '+' | '.join(columns)+' |','|'+'---|'*len(columns)]
        for row in rows:
            lines.append('| '+' | '.join(f'{row.get(k):.9g}' if isinstance(row.get(k),float) else str(row.get(k)) for k in columns)+' |')
        (tables/(name+'.md')).write_text('\n'.join(lines)+'\n',encoding='utf-8')
    rows=[dict(role=r,valid=records[r]['valid'],**{k:(records[r].get('metrics') or {}).get(k) for k in keys},
               strict_device_pass=records[r].get('strict_device_pass'),origin=records[r].get('origin','NEW_SAME_E0_TRAINING')) for r in names]
    table('fixed-endpoints',list(rows[0]),rows)
    defects=['electric_fv_rms','current_balance_rms','power_defect_rms','input_power_NRMSE']
    table('electrical-defects',['role',*defects],[dict(role=r,**{k:(records[r].get('metrics') or {}).get(k) for k in defects}) for r in names])
    ek=['cycle','recall','precision','mass_ratio','timing_absolute','event_time','recovery_fraction']
    table('complete-events',['role',*ek],[dict(role=r,**{k:c.get(k) for k in ek}) for r in names for c in records[r].get('cycles',[])])
    pairs=[]
    for arm in ('F_raw','F_bal'):
        for key,candidate,base in [('E_vs_network','P_E',arm+'/network'),('E_vs_projected','P_E',arm+'/projected'),
                                  ('projection_vs_network',arm+'/projected',arm+'/network')]:
            d=decision['comparisons'][arm][key]
            m=(records.get(candidate,{}) or {}).get('metrics');b=(records.get(base,{}) or {}).get('metrics')
            delta={k:100*(m[k]/b[k]-1) if m and b and m.get(k) is not None and b.get(k) not in (None,0) else None for k in keys}
            pairs.append(dict(candidate=candidate,base=base,A=d['A']['passed'],B=d['B']['passed'],**delta))
    table('matched-changes',['candidate','base','A','B',*keys],pairs)
    grad=[dict(block=k,weighted_loss=v['weighted_objective'],norm=v['norm']) for k,v in diag['blocks'].items()]
    table('weight-calibration',list(grad[0]),grad)
    if data.get('projection_energy_diagnostic'):
        erows=[dict(role=k,**{n:v for n,v in value.items() if n!='interpretation'}) for k,value in data['projection_energy_diagnostic'].items() if 'minimum_power_gap' in value]
        if erows:table('projection-energy',list(erows[0]),erows)
    counts=[]
    for arm in cfg['roles']:
        if not (root/arm/'terminal.json').exists():
            counts.append(dict(role=arm,status='NO_VALID_ENDPOINT',Adam=None,evaluations=None,accepted=None,forward=None,adjoint=None,projection=None,eta=None,full_grid_network=None,explicit_faces=None,thermal_phase_groups=None,observation_groups=None))
            continue
        t=read(root/arm/'terminal.json');e=t['statistics']['electrical']
        pred=read(root/arm/'projected/prediction.json') if (root/arm/'projected/prediction.json').exists() else {}
        work=t['statistics']['explicit_work']
        identity=read(root/arm/'paired-readout-identity.json') if (root/arm/'paired-readout-identity.json').exists() else {}
        counts.append(dict(role=arm,status=t['lbfgs']['termination'],Adam=t['adam_updates'],evaluations=t['lbfgs']['evaluations'],
            accepted=t['lbfgs']['accepted_steps'],forward=e['forward_solves'],adjoint=e['adjoint_solves'],
            projection=identity.get('total_actual_projection_forward_solves',pred.get('electrical_counts',{}).get('forward_solves')),failed_projection=identity.get('failed_cloud_forward_solves',0),eta=t['eta'],
            full_grid_network=work['full_grid_network_evaluations'],explicit_faces=work['explicit_face_evaluations'],
            thermal_phase_groups=work['thermal_phase_groups'],observation_groups=work['observation_groups']))
    table('execution-counts',list(counts[0]),counts)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.spines.top':False,'axes.spines.right':False,'savefig.dpi':180})
    colors={'F_raw':'#c77724','F_bal':'#825099','P_E':'#246c9c','D_E':'#647680','B_E':'#41845d'}
    modes=('network','projected');positions={'F_raw':np.array([0.,1.]),'F_bal':np.array([3.,4.])}
    def save(fig,name):
        for ext in ('png','pdf'):fig.savefig(figures/(name+'.'+ext))
        plt.close(fig)
    def paired(ax,key,title):
        positive=[]
        for arm in ('F_raw','F_bal'):
            vals=[(records.get(arm+'/'+m,{}).get('metrics') or {}).get(key,np.nan) for m in modes]
            positive.extend(v for v in vals if v is not None and np.isfinite(v) and v>0)
            ax.plot(positions[arm],vals,'o-',color=colors[arm],lw=2,label=arm)
        for ref,ls in [('P_E','-'),('D_E','--'),('B_E',':')]:
            value=records[ref]['metrics'].get(key)
            if value is not None:
                ax.axhline(value,color=colors[ref],ls=ls,lw=1.25,label=ref+' (fixed)')
                if value>0:positive.append(value)
        ax.set(xticks=[0,1,3,4],xticklabels=['raw\nnetwork','raw\nprojected','bal\nnetwork','bal\nprojected'],title=title,ylim=(0,None))
        if key in ('bottom_current_NRMSE','power_trace_NRMSE','energy_error') and positive:
            ax.set_yscale('log');ax.set_ylim(min(positive)*.65,max(positive)*1.6)
            ax.set_ylabel('Error (log scale)')
        ax.grid(axis='y',alpha=.2)
    def event(ax,key,title,threshold=None):
        for arm in ('F_raw','F_bal'):
            record=records.get(arm+'/network',{})
            if record.get('valid'):ax.plot([1,2],[c.get(key) for c in record['cycles']],'o-',color=colors[arm],label=arm+' (both readouts)')
        for ref,ls in [('P_E','-'),('D_E','--'),('B_E',':')]:
            ax.plot([1,2],[c.get(key) for c in records[ref]['cycles']],marker='.',ls=ls,color=colors[ref],label=ref)
        if threshold is not None:
            for value in np.atleast_1d(threshold):ax.axhline(value,color='#555',ls=':',lw=.8)
        ax.set(xticks=[1,2],title=title,xlabel='Cycle',ylim=(0,None));ax.grid(alpha=.15)
    fig,ax=plt.subplots(4,3,figsize=(15,14),constrained_layout=True)
    for a,k,title in zip(ax[0],['S','Ephi','ET'],['Space-time symmetric difference','Raw ROI phase RMS','Temperature RMS / 0.45']): paired(a,k,title)
    for a,key,title,threshold in zip(ax[1:3].flat,['recall','precision','mass_ratio','timing_absolute','event_time','recovery_fraction'],
           ['Event recall','Event precision','Event mass ratio','Event timing error','Predicted event time','Recovery fraction'],[.9,.8,[.8,1.2],.005,None,None]):event(a,key,title,threshold)
    for a,k,title in zip(ax[3],['bottom_current_NRMSE','power_trace_NRMSE','energy_error'],['Bottom-current NRMSE','Power-trajectory NRMSE','Integrated energy relative error']): paired(a,k,title)
    ax[0,0].legend(fontsize=7,loc='best')
    fig.suptitle('Training-time electrical coupling or post-hoc repair?\nLines join two readouts of the same learned T/phase state',fontsize=14)
    save(fig,'training-versus-posthoc')
    fig,ax=plt.subplots(2,3,figsize=(14,8),constrained_layout=True)
    for a,key,title,threshold in zip(ax.flat,['recall','precision','mass_ratio','timing_absolute','event_time','recovery_fraction'],
           ['Recall','Precision','Mass ratio','Absolute timing error','Predicted event time','Recovery fraction'],[.9,.8,[.8,1.2],.005,None,None]):event(a,key,title,threshold)
    ax[0,0].legend(fontsize=7);fig.suptitle('Complete two-cycle event criteria; projection leaves every event unchanged')
    save(fig,'complete-events')
    with np.load(root/'evaluation/traces.npz',allow_pickle=False) as source:tr={k:source[k] for k in source.files}
    t=tr['time'];iscale=np.sqrt(np.trapezoid(tr['reference_current']**2,t)/(t[-1]-t[0]));pscale=np.sqrt(np.trapezoid(tr['reference_power']**2,t)/(t[-1]-t[0]))
    fig,ax=plt.subplots(2,4,figsize=(19,8),constrained_layout=True)
    for i,arm in enumerate(('F_raw','F_bal')):
        for j,key,reference,scale,label in [(0,'bottom_current','reference_current',iscale,'Current'),(2,'joule_power','reference_power',pscale,'Power')]:
            for offset,view in ((0,'all readouts'),(1,'after projection')):
                a=ax[i,j+offset]
                for mode,ls in [('network','--'),('projected','-')]:
                    if offset and mode=='network':continue
                    name=arm+'/'+mode
                    if name+'__'+key in tr:
                        a.plot(t,(tr[name+'__'+key]-tr[reference])/scale,ls,color=colors[arm],label=mode)
                a.plot(t,(tr['P_E__'+key]-tr[reference])/scale,color=colors['P_E'],label='P_E (fixed)')
                a.set(title=arm+' / '+label+'\n'+view,xlabel='Time',ylabel='Signed error / reference RMS')
                a.legend(fontsize=8);a.grid(alpha=.15)
    fig.suptitle('Fixed endpoints: complete raw errors and separate views of the solved-state comparison')
    save(fig,'device-trajectories')
    summary=dict(decision=decision,execution=counts,matched_percentage_changes=pairs,eta_bal=diag['eta_bal'],
        calibration_scans=diag['full_gradient_scans'],G0=diag['G0'],electric_gradient_norm=diag['electric_gradient_norm'])
    save_json(root/'endpoint-comparison-summary.json',summary)
    print(json.dumps(dict(paper=str(paper),training_coupling_signal=decision['training_coupling_signal'])))
    return summary


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=RUN)
    report(p.parse_args().root)
