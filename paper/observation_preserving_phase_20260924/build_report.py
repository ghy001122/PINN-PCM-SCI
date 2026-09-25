"""Build publication figures and tables from frozen arrays and actual records only."""
from pathlib import Path
import argparse
import csv
import json
import shutil
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
RUN=ROOT/'outputs/runs/20260924-observation-preserving-phase'
COLORS={'B0':'#4c5560','D_E':'#9b70a2','G':'#d5802c','N':'#197caa','S':'#2e8b57'}
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,
    'axes.spines.right':False,'pdf.fonttype':42,'ps.fonttype':42,'savefig.dpi':180})


def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def save(path,value):Path(path).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def csvwrite(name,rows):
    keys=list(dict.fromkeys(k for r in rows for k in r))
    with (HERE/name).open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=keys);w.writeheader()
        for row in rows:w.writerow({k:json.dumps(v) if isinstance(v,(dict,list)) else v for k,v in row.items()})
def figure(fig,name):
    (HERE/'figures').mkdir(exist_ok=True)
    for ext in ('png','pdf'):fig.savefig(HERE/'figures'/f'{name}.{ext}',bbox_inches='tight')
    plt.close(fig)


def theory():
    bound=read(RUN/'fixed-support-bound.json');d=read(RUN/'theory-diagnostics.json')
    with np.load(RUN/'fixed-support-traces.npz') as z:traces={k:z[k] for k in z.files}
    with np.load(RUN/'theory-counterexample-fields.npz') as z:f={k:z[k] for k in z.files}
    fig,ax=plt.subplots(2,3,figsize=(13,7.1),layout='constrained')
    a=ax[0,0];t=traces['time'];a.plot(t,traces['gate'],color=COLORS['N'],lw=2)
    for lo,hi in ((0,.35),(1.01,1.36)):a.axvspan(lo,hi,color=COLORS['G'],alpha=.18)
    a.axvspan(1.36,2.02,color=COLORS['N'],alpha=.12);a.axvline(2.02,color='0.6',ls=':')
    a.set(xlabel='Time',ylabel='Support gate',title='(a) Exact zero-drive / missing-phase overlap',xlim=(0,2.5))
    a.text(.03,.94,'Orange: powered',transform=a.transAxes,va='top',fontsize=9)
    a.text(1.69,.5,'D',ha='center',fontsize=13,color=COLORS['N'])
    a=ax[0,1];x=np.arange(2);fraction=[bound['metrics'][k]['mutable_fraction'] for k in ('Ephi','S')]
    a.bar(x,fraction,color=COLORS['N'],label='Within open D')
    a.bar(x,1-np.array(fraction),bottom=fraction,color='#d9dde0',label='Immutable in W')
    a.set(xticks=x,xticklabels=['Phase squared error','Set error'],ylabel='Fraction of base W error',ylim=(0,1.13),title='(b) Necessary feasibility, not attainability')
    for i,v in enumerate(fraction):a.text(i,v/2,f'{100*v:.2f}%',ha='center',va='center',color='white')
    a.legend(frameon=False,fontsize=8,loc='upper right')
    a=ax[0,2];orders=[16,32,64]
    a.plot(orders,[d['thermal'][str(n)]['mean_raw_square_lower_bound'] for n in orders],'o-',label='Fixed-endpoint lower bound',color=COLORS['N'])
    a.plot(orders,[d['thermal'][str(n)]['base_mean_raw_square'] for n in orders],'s-',label='Base thermal residual square',color=COLORS['B0'])
    a.set(xticks=orders,xlabel='Gauss points',ylabel='64-cell mean, raw units',title='(c) Fixed-temperature constraint',ylim=(0,.016))
    a.legend(frameon=False,fontsize=8)
    extent=[-1,1,0,1];shape=(len(f['z']),len(f['x']))
    a=ax[1,0];im=a.imshow(f['1.55/base'].reshape(shape),origin='lower',extent=extent,vmin=0,vmax=1,cmap='viridis',aspect='auto')
    a.set(title='(d) Actual frozen base phase, t=1.55',xlabel='x',ylabel='z');fig.colorbar(im,ax=a,label='Phase')
    for a,sign,label in ((ax[1,1],'-1','(e)'),(ax[1,2],'1','(f)')):
        delta=(f['1.55/'+sign]-f['1.55/base']).reshape(shape)
        im=a.imshow(delta,origin='lower',extent=extent,vmin=-.015,vmax=.015,cmap='RdBu_r',aspect='auto')
        a.set(title=f'{label} Finite counterexample: sign {sign}',xlabel='x',ylabel='z');fig.colorbar(im,ax=a,label='Phase change')
    figure(fig,'information-boundary')
    rows=[]
    for metric,v in bound['metrics'].items():rows.append(dict(metric=metric,**v))
    csvwrite('fixed-support-feasibility.csv',rows)
    csvwrite('thermal-integral-bound.csv',[dict(order=n,mean_lower_bound=d['thermal'][str(n)]['mean_raw_square_lower_bound'],
        base_mean_raw_square=d['thermal'][str(n)]['base_mean_raw_square'],
        max_counterexample_integral_change=max(d['thermal'][str(n)]['max_integrated_counterexample_change'].values())) for n in orders])
    print('THEORY_FIGURE_AND_TABLES_BUILT')


def results():
    score=read(RUN/'scoring/results.json');audit=read(RUN/'endpoint-audits.json')
    locked=read(RUN/'all-endpoints-locked.json');closure=read(RUN/'compute-closure.json')
    assert closure['recovery_verified'] and closure['instance_shutdown_confirmed']
    arms=('B0','D_E','G','N','S');new=('G','N','S');metrics=[];events=[];cost=[]
    for arm in arms:
        for scope,item in score['windows'][arm].items():metrics.append(dict(arm=arm,scope=scope,**item['metrics']))
        for c in score['records'][arm]['cycles']:events.append(dict(arm=arm,strict_device_pass=score['records'][arm]['strict_device_pass'],**c))
    csvwrite('all-metrics.csv',metrics);csvwrite('both-cycle-events.csv',events)
    csvwrite('full-readout-metrics.csv',[dict(arm=a,**score['records'][a]['metrics']) for a in arms])
    pairs=[]
    for label,p in score['pairs'].items():
        candidate,control=label.split('_vs_')
        pairs.append(dict(candidate=candidate,control=control,A_w=p['A_w']['passed'],gain=p['A_w'].get('gain'),
            noninferior=p['A_w'].get('noninferior'),full_A=p['full']['A']['passed'],full_B=p['full']['B']['passed'],
            outside_cost=p['outside_cost'],window_reductions=p['relative_reduction']['window']))
    csvwrite('all-pairwise-decisions.csv',pairs)
    csvwrite('raw-physics-audit.csv',[dict(arm=a,**v['D'],physical_completion=v.get('physical_completion'),
        full_raw=v['full_raw']) for a,v in audit['arms'].items()])
    csvwrite('full-raw-physics-audit.csv',[dict(arm=a,**v['full_raw']) for a,v in audit['arms'].items()])
    shutil.copyfile(RUN/'scoring/phase-error-decomposition.csv',HERE/'phase-error-decomposition.csv')
    for a in new:
        terminal=read(RUN/a/'terminal.json');stats=terminal['statistics'];profile=read(RUN/f'profile-{a}.json')
        native=read(RUN/'predictions'/a/'prediction.json')
        cost.append(dict(arm=a,device='CPU',torch_threads=4,parameters=profile['parameters'],
            adam_updates=terminal['adam_updates'],lbfgs_evaluations=terminal['lbfgs']['evaluations'],
            lbfgs_termination=terminal['lbfgs']['termination'],training_seconds=terminal['elapsed_seconds'],
            forward_solves=stats['electrical']['forward_solves'],adjoint_solves=stats['electrical']['adjoint_solves'],
            electrical_counts=stats['electrical'],coordinate_work=stats['coordinate_work'],
            objectives=stats['objectives'],profile_seconds=profile['elapsed_seconds'],profile_memory=profile['memory'],
            native_reader_seconds=native['elapsed_seconds'],native_reader_device='cuda:0',native_reader_counts=native['electrical_counts']))
    csvwrite('actual-training-cost.csv',cost)
    csvwrite('zero-update-profiles.csv',[read(RUN/f'profile-{a}.json') for a in new])
    fig,ax=plt.subplots(2,2,figsize=(11.7,7.5),layout='constrained')
    x=np.arange(len(arms))
    for a,key,title,scale in ((ax[0,0],'Ephi','(a) Missing-window phase RMS',1),(ax[0,1],'S','(b) Missing-window set error',1000)):
        vals=[score['windows'][k]['window']['metrics'][key]*scale for k in arms]
        a.bar(x,vals,color=[COLORS[k] for k in arms]);a.set(xticks=x,xticklabels=arms,title=title,ylabel='Error' if scale==1 else '1000 × set error')
        a.axhline(.9*vals[0],ls='--',lw=1,color='0.4',label='90% of base error')
        for i,v in enumerate(vals):a.text(i,v,f'{v:.4g}',ha='center',va='bottom',fontsize=9)
        a.set_ylim(0,max(vals)*1.22);a.legend(frameon=False,fontsize=8)
    a=ax[1,0]
    with np.load(RUN/'scoring/active-traces.npz') as z:
        a.plot(z['time'],z['reference'],color='black',lw=1.8,label='Reference')
        for arm in ('B0','G','N','S'):a.plot(z['time'],z[arm],color=COLORS[arm],lw=1.4,label=arm)
    a.axvspan(1.36,2.02,color=COLORS['N'],alpha=.08);a.set(xlim=(1.01,2.02),xlabel='Time',ylabel='Full-domain active fraction',title='(c) Second-cycle support, complete W')
    a.legend(frameon=False,ncol=3,fontsize=8)
    a=ax[1,1];keys=('phase_raw_mean_square','thermal_raw_mean_square','phase_BC_mean_square_original_denominator');base=audit['arms']['B0']['D']
    for i,arm in enumerate(new):
        ratios=[audit['arms'][arm]['D'][k]/base[k] for k in keys]
        a.bar(np.arange(3)+(i-1)*.24,ratios,width=.23,color=COLORS[arm],label=arm)
    a.scatter(np.arange(3),[.9,1.05,1.05],marker='_',s=420,c='black',label='Required upper limit',zorder=4)
    a.set(xticks=np.arange(3),xticklabels=['Raw phase','Raw thermal','Phase BC'],ylabel='Independent D audit / base (log)',title='(d) Physical qualification is separate',yscale='log',ylim=(.08,18))
    a.legend(frameon=False,fontsize=8)
    figure(fig,'three-arm-development')
    evidence=HERE/'evidence';evidence.mkdir(exist_ok=True)
    names=['frozen-config.json','input-manifest.json','fixed-support-bound.json','theory-diagnostics.json',
        'finite-intervention.json','qualification.json','device-deviation.json','all-endpoints-locked.json',
        'endpoint-audits.json','readout-manifest.json','invariance-array-checks.json','scoring-memory-recovery.json']
    for name in names:shutil.copyfile(RUN/name,evidence/name)
    shutil.copyfile(RUN/'scoring/results.json',evidence/'results.json')
    save(evidence/'compute-closure-public.json',{k:closure[k] for k in ('job_exit_code','recovery_verified','recovery_sha256',
        'gpu_work_ended_observed_utc','recovered_utc','shutdown_requested_utc','instance_shutdown_confirmed','completed_utc')})
    summary=dict(adam_updates=sum(r['adam_updates'] for r in cost),complete_lbfgs_evaluations=sum(r['lbfgs_evaluations'] for r in cost),
        training_seconds=sum(r['training_seconds'] for r in cost),training_device='CPU (entrypoint deviation)',
        training_forward=sum(r['forward_solves'] for r in cost),training_adjoint=sum(r['adjoint_solves'] for r in cost),
        raw_audit_forward=64,native_reader_forward=282,profile_complete_forward=100,profile_complete_adjoint=100,
        profile_partial_local_oom_cost='not fully instrumented; preserved failure record, no optimizer updates',
        theoretical_counterexample_forward=6,local_spot_tests='diagnostic work separately preserved; no science optimizer steps',
        results={a:score['windows'][a]['window']['metrics'] for a in arms},
        physical={a:audit['arms'][a]['physical_completion'] for a in new},cost=cost)
    save(HERE/'evidence/actual-work-summary.json',summary)
    print(json.dumps({k:v for k,v in summary.items() if k!='cost'},indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['theory','results']);a=p.parse_args()
    (theory if a.action=='theory' else results)()
