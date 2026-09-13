"""Render the completed V29 fixed-endpoint evidence, without numerical research."""
from __future__ import annotations
import argparse
import csv
import json
from pathlib import Path
import numpy as np
from .phk_v23_lf11 import ROOT
from .phk_v23_lf11_remaining_pde import RUN


def read(path): return json.loads(Path(path).read_text(encoding='utf-8'))


def report(root=RUN):
    result=read(root/'evaluation/results.json')
    config=read(root/'frozen-config.json')
    diag=read(root/'diagnosis.json')
    audit=read(root/'fixed-endpoint-common-audit.json')
    records=result['records']
    names=['E0','D_E','P_E','B_E']+config['roles']
    if not all(records[r]['valid'] for r in names): raise ValueError('invalid role requires explicit failure report')
    directory=ROOT/'paper/paper_v29'
    figures,tables=directory/'figures',directory/'tables'
    figures.mkdir(parents=True,exist_ok=True);tables.mkdir(exist_ok=True)
    metrics=['S','Ephi','ET','EV','EI','bottom_current_NRMSE','power_trace_NRMSE','energy_error','local_joule_NRMSE']
    def table(filename, columns, rows):
        with (tables/(filename+'.csv')).open('w',newline='',encoding='utf-8') as stream:
            writer=csv.DictWriter(stream,fieldnames=columns);writer.writeheader();writer.writerows(rows)
        lines=['| '+' | '.join(columns)+' |','|'+'---|'*len(columns)]
        for row in rows:
            lines.append('| '+' | '.join(f'{row[k]:.9g}' if isinstance(row[k],float) else str(row[k]) for k in columns)+' |')
        (tables/(filename+'.md')).write_text('\n'.join(lines)+'\n',encoding='utf-8')
    table('fixed-endpoints',['role',*metrics,'strict_device_pass'],[
        dict(role=r,**{k:records[r]['metrics'][k] for k in metrics},strict_device_pass=records[r]['strict_device_pass']) for r in names])
    eventkeys=['cycle','recall','precision','mass_ratio','timing_absolute','event_time','recovery_fraction']
    table('cycle-events',['role',*eventkeys],[dict(role=r,**{k:c.get(k) for k in eventkeys}) for r in names for c in records[r]['cycles']])
    comparisonrows=[]
    for role,baselines in result['conditional_decision']['comparisons'].items():
        for baseline,decisions in baselines.items():
            c,b=records[role]['metrics'],records[baseline]['metrics']
            comparisonrows.append(dict(candidate=role,baseline=baseline,A=decisions['A']['passed'],B=decisions['B']['passed'],
                **{k:100*(c[k]/b[k]-1) for k in metrics}))
    table('matched-changes',['candidate','baseline','A','B',*metrics],comparisonrows)
    oldnames=['E0','D_E','P_E']
    allpool={}
    for r in oldnames:
        allpool[r]={'lbfgs':diag['fixed_train_pool'][r]['values'],'audit':diag['inherited_audit']['records'][r]['values']}
    for r in config['roles']: allpool[r]=audit['records'][r]
    a,b=read(root/'calibration.json')['aE'],read(root/'calibration.json')['bE']
    poolrows=[]
    for role,ds in allpool.items():
        for pool in ('lbfgs','audit'):
            v=ds[pool]
            C=v['observation']/a+.1*(5*v['boundary']+v['initial'])/b
            J=(v['thermal']+v['phase'])/3
            F=.1*J/b
            k={'D_C':0.,'D_E':0.,'P_kappa':config['kappa']}.get(role,1.)
            poolrows.append(dict(role=role,pool=pool,Lobs=v['observation'],LBC=v['boundary'],
                thermal=v['thermal'],phase=v['phase'],J_Tphi=J,C=C,F=F,common_C_plus_F=C+F,
                role_functional=C+k*F if role!='E0' else None))
    table('common-objectives',list(poolrows[0]),poolrows)
    gradrows=[]
    for role,entry in diag['block_gradients'].items():
        for head,h in entry['by_head'].items():
            for block,norm in h['norms'].items():
                gradrows.append(dict(role=role,head=head,block=block,norm=norm,
                    cosine_with_C=h['cosines'][block]['C'],cosine_with_F=h['cosines'][block]['F']))
    table('reduced-gradients',list(gradrows[0]),gradrows)
    countrows=[]
    for r in config['roles']:
        t=read(root/r/'terminal.json');s=t['statistics']['electrical'];p=read(root/r/'prediction.json')['electrical_counts']
        countrows.append(dict(role=r,Adam=t['adam_updates'],evaluations=t['lbfgs']['evaluations'],accepted=t['lbfgs']['accepted_steps'],
            termination=t['lbfgs']['termination'],forward=s['forward_solves'],adjoint=s['adjoint_solves'],inference=p['forward_solves']))
    table('execution-counts',list(countrows[0]),countrows)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.size':9,'font.family':'DejaVu Sans','axes.spines.top':False,'axes.spines.right':False,'savefig.dpi':180})
    colors={'E0':'#89929c','D_E':'#407baf','P_E':'#daa65a','B_E':'#579473','D_C':'#274c77','P1':'#d77a1f','P_kappa':'#8e4a9d'}
    labels={r:r.replace('P_kappa',r'$P_{\kappa}$') for r in names}
    def save(fig,name):
        for suffix in ('png','pdf'): fig.savefig(figures/(name+'.'+suffix))
        plt.close(fig)
    def bars(axis,key,title):
        axis.bar([labels[n] for n in names],[records[n]['metrics'][key] for n in names],color=[colors[n] for n in names])
        axis.set_title(title);axis.set_ylim(bottom=0);axis.grid(axis='y',alpha=.2)
        contrasts=[f"{labels[r]} / D_C: {100*(records[r]['metrics'][key]/records['D_C']['metrics'][key]-1):+.2f}%" for r in ('P1','P_kappa')]
        axis.text(.97,.96,'\n'.join(contrasts),transform=axis.transAxes,ha='right',va='top',fontsize=8,
                  bbox=dict(facecolor='white',edgecolor='none',alpha=.9))
    # First headline figure explicitly joins mechanism, objectives and consequences.
    fig,ax=plt.subplots(2,3,figsize=(14,8),constrained_layout=True)
    h=diag['block_gradients']['D_E']['by_head']['all']
    blocknames=['observation','boundary','thermal','phase','F']
    ax[0,0].bar(['Obs','BC','Thermal','Phase','F'],[h['norms'][k] for k in blocknames],color=['#274c77','#579473','#d77a1f','#8e4a9d','#a25377'])
    ax[0,0].set(yscale='log',title='D_E parent: weighted complete gradients',ylabel='Euclidean norm (log scale)')
    ax[0,0].text(.97,.96,f"|gF| / G = {diag['selection']['ratio']:.5f}\nkappa = {config['kappa']:.4f}",transform=ax[0,0].transAxes,ha='right',va='top',bbox=dict(facecolor='white',edgecolor='none',alpha=.9))
    nr=oldnames+config['roles'];x=np.arange(len(nr))
    for pool,offset,style in [('lbfgs',-.17,'solid'),('audit',.17,'dashed')]:
        values=[next(v for v in poolrows if v['role']==r and v['pool']==pool)['J_Tphi'] for r in nr]
        ax[0,1].bar(x+offset,values,width=.32,label='Fixed training pool' if pool=='lbfgs' else 'Independent unlabeled pool',alpha=.8 if pool=='lbfgs' else .4)
    ax[0,1].set(xticks=x,xticklabels=[labels[n] for n in nr],title='Common original remaining-PDE residual',ylabel='J_Tphi')
    ax[0,1].set_ylim(0,1.23*max(v['J_Tphi'] for v in poolrows))
    ax[0,1].legend(fontsize=8)
    bars(ax[0,2],'Ephi','Raw ROI phase RMS')
    for r in names:
        ax[1,0].scatter(records[r]['cycles'][0]['recall'],records[r]['cycles'][1]['timing_absolute'],color=colors[r],label=labels[r],s=42)
    ax[1,0].axvline(.9,color='#555',ls=':');ax[1,0].axhline(.005,color='#555',ls=':')
    ax[1,0].set(xlabel='Cycle 1 recall (higher is better)',ylabel='Cycle 2 timing error (lower is better)',title='Separate strict event requirements')
    ax[1,0].legend(fontsize=7,ncol=2)
    bars(ax[1,1],'bottom_current_NRMSE','Bottom-current NRMSE')
    bars(ax[1,2],'power_trace_NRMSE','Power-trajectory NRMSE')
    fig.suptitle('Fixed-parent counterfactual: measured physics influence to device consequences',fontsize=14)
    save(fig,'mechanism-to-device')
    fig,ax=plt.subplots(2,3,figsize=(14,8),constrained_layout=True)
    for axis,key in zip(ax.flat,['C','F','common_C_plus_F','thermal','phase','J_Tphi']):
        for pool,offset in [('lbfgs',-.17),('audit',.17)]:
            axis.bar(x+offset,[next(v for v in poolrows if v['role']==r and v['pool']==pool)[key] for r in nr],width=.32,label=pool,alpha=.8 if pool=='lbfgs' else .4)
        axis.set(xticks=x,xticklabels=[labels[n] for n in nr],title=key,ylim=(0,None));axis.grid(axis='y',alpha=.2)
    ax[0,0].legend();fig.suptitle('Same functional and original-scale residual blocks on both frozen pools')
    save(fig,'common-objectives')
    fig,ax=plt.subplots(2,2,figsize=(12,8),constrained_layout=True)
    keys=['observation','boundary','thermal','phase','C','F']
    for i,role in enumerate(('E0','D_E')):
        for j,head in enumerate(('T_including_adapter','phase')):
            cs=diag['block_gradients'][role]['by_head'][head]['cosines']
            arr=np.array([[cs[k][q] if cs[k][q] is not None else np.nan for q in keys] for k in keys])
            im=ax[i,j].imshow(arr,vmin=-1,vmax=1,cmap='coolwarm')
            ax[i,j].set(xticks=np.arange(6),yticks=np.arange(6),xticklabels=['Obs','BC','Thermal','Phase','C','F'],yticklabels=['Obs','BC','Thermal','Phase','C','F'],title=role+' / '+head)
            for row in range(6):
                for col in range(6): ax[i,j].text(col,row,f'{arr[row,col]:.2f}',ha='center',va='center',fontsize=8)
    fig.colorbar(im,ax=ax,shrink=.7,label='Gradient cosine; local only')
    fig.suptitle('Complete first-order parameter gradients; no Hessian or inherited Adam state')
    save(fig,'gradient-directions')
    with np.load(root/'evaluation/traces.npz',allow_pickle=False) as f: tr={k:f[k] for k in f.files}
    t=tr['time']
    iscale=np.sqrt(np.trapezoid(tr['reference_current']**2,t)/(t[-1]-t[0]))
    pscale=np.sqrt(np.trapezoid(tr['reference_power']**2,t)/(t[-1]-t[0]))
    fig,ax=plt.subplots(2,2,figsize=(13,8),constrained_layout=True)
    for r in names:
        ax[0,0].plot(t,(tr[r+'__bottom_current']-tr['reference_current'])/iscale,color=colors[r],label=labels[r],lw=1.1)
        ax[0,1].plot(t,(tr[r+'__joule_power']-tr['reference_power'])/pscale,color=colors[r],lw=1.1)
        ax[1,0].plot([1,2],[c['recall'] for c in records[r]['cycles']],'o-',color=colors[r],label=labels[r])
        ax[1,1].plot([1,2],[c['timing_absolute'] for c in records[r]['cycles']],'o-',color=colors[r])
    ax[0,0].set(title='Signed bottom-current error',xlabel='Time',ylabel='Error / reference RMS')
    ax[0,1].set(title='Signed power error',xlabel='Time',ylabel='Error / reference RMS')
    ax[0,0].legend(ncol=2,fontsize=8)
    ax[1,0].axhline(.9,ls=':',color='#555');ax[1,1].axhline(.005,ls=':',color='#555')
    ax[1,0].set(title='Event-support recall',xticks=[1,2],ylim=(0,1.04))
    ax[1,1].set(title='Event timing absolute error',xticks=[1,2],ylim=(0,None))
    fig.suptitle('Both cycles and electrical trajectories; fixed endpoints only')
    save(fig,'event-device-trajectories')
    summary={'selection':result['conditional_decision'],'execution':countrows,
             'diagnostic_counts':audit['diagnostic_counts_including_pretraining'],
             'matched_percentage_changes':comparisonrows,'common_objectives':poolrows,
             'diagnostic_gradient_scans':diag['gradient_scans'],'kappa':config['kappa']}
    (root/'endpoint-comparison-summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'paper':str(directory),'figures':4,'fixed_roles':names,'selected':result['conditional_decision']['selected_simple_first']}))
    return summary


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=RUN)
    report(p.parse_args().root)
