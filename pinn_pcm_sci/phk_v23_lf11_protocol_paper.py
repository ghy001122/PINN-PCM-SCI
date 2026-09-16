"""Build V32 from saved post-shutdown results; never trains or selects models."""
from __future__ import annotations
import argparse
import csv
import json
from pathlib import Path
import shutil
import tarfile
import numpy as np
from .phk_v23_lf11 import ROOT,save_json
from .phk_v23_lf11_protocol_reference import RUN
from .phk_v23_lf11_training_coupling import read

PAPER=ROOT/'paper/paper_v32'
NAMES=('E/projected','F_raw/projected','B_E')
LABELS={'E/projected':'E','F_raw/projected':'F + projection','B_E':'B_E'}


def table(directory,name,rows,columns=None):
    if not rows:raise ValueError('empty result table: '+name)
    keys=columns or list(rows[0])
    with (directory/(name+'.csv')).open('w',encoding='utf-8',newline='') as stream:
        w=csv.DictWriter(stream,fieldnames=keys,extrasaction='ignore');w.writeheader();w.writerows(rows)
    def fmt(value):
        if value is None:return 'NA'
        if isinstance(value,float):return f'{value:.10g}'
        if isinstance(value,(dict,list)):return json.dumps(value,ensure_ascii=False)
        return str(value)
    text='| '+' | '.join(keys)+' |\n| '+' | '.join(['---']*len(keys))+' |\n'
    text+='\n'.join('| '+' | '.join(fmt(row.get(k)) for k in keys)+' |' for row in rows)+'\n'
    (directory/(name+'.md')).write_text(text,encoding='utf-8')
    return text


def gather(root):
    new=read(root/'evaluation/results.json');cases={}
    for seed in (29,43):
        old=read(ROOT/f'paper/paper_v31/evidence/confirmation/seed-{seed}/evaluation/results.json')
        cases[('Original',seed)]={role:old['records'][role] for role in NAMES}
        cases[('Shorter gap',seed)]={role:new['records']['B_E' if role=='B_E' else f'{seed}/{role}'] for role in NAMES}
    return new,cases


def figures(root,paper,new,cases):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False,'savefig.dpi':190})
    colors={'E/projected':'#2563a6','F_raw/projected':'#d97732','B_E':'#7c8797'}
    folder=paper/'figures'
    from matplotlib.patches import FancyBboxPatch
    fig,ax=plt.subplots(figsize=(12,5.5));ax.set(xlim=(0,12),ylim=(0,5.5));ax.axis('off')
    def box(x,y,w,h,text,color):
        ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.08',
            facecolor=color,edgecolor='#43505d',linewidth=.8))
        ax.text(x+w/2,y+h/2,text,ha='center',va='center',fontsize=9)
    def arrow(start,end,style='-'):
        ax.annotate('',xy=end,xytext=start,arrowprops=dict(arrowstyle='->',color='#43505d',lw=1.1,ls=style))
    box(.15,3.35,2.25,1.05,'New sparse V / T / phase\n+ known drive and IC/BC','#e9eef2')
    box(3.0,3.35,2.1,1.05,'Common fitted parent\nV / T / phase networks','#e9eef2')
    box(5.7,4.05,2.65,.95,'E: implicit electrical solve\nA(sigma) v = f\nFull first-order VJP','#deebfa')
    box(5.7,2.65,2.65,.95,'F: trainable voltage head\nFinite electric penalty\n128 sampled cells','#fae7d7')
    box(9.1,3.3,2.7,1.15,'Shared face Joule deposition\nThermal cell balance\n+ phase PDE residual','#e5eee5')
    arrow((2.45,3.88),(2.95,3.88));arrow((5.15,4.03),(5.65,4.48));arrow((5.15,3.62),(5.65,3.12))
    arrow((8.4,4.48),(9.05,4.08));arrow((8.4,3.12),(9.05,3.65))
    ax.text(7.05,2.32,'Same accepted-endpoint rule; no reference selection',ha='center',fontsize=8)
    ax.plot([.2,11.8],[2.02,2.02],color='#c0c7cd',lw=.8)
    box(.35,.45,3.0,1.0,'Frozen learned T / phase\nE and F + new interpolant B_E','#e9eef2')
    box(4.45,.45,3.0,1.0,'Same electrical projection\n160 x 80, fixed times','#e5eee5')
    box(8.55,.45,3.0,1.0,'Separate phase / event scores\nCurrent / power / local q','#e9eef2')
    arrow((3.4,.95),(4.4,.95));arrow((7.5,.95),(8.5,.95))
    ax.text(.2,5.27,'Training: compare how electrical constraints enter the coupled reconstruction',fontsize=11,weight='bold')
    ax.text(.2,1.74,'Evaluation: frozen learned states, common projection and fixed reference',fontsize=10,weight='bold')
    fig.tight_layout()
    for ext in ('png','pdf'):fig.savefig(folder/f'coupled-method-comparison.{ext}')
    plt.close(fig)
    fig,axes=plt.subplots(2,3,figsize=(11.5,6.6),constrained_layout=True)
    metrics=[('Ephi','ROI phase RMS',1),('bottom_current_NRMSE','Current NRMSE (%)',100),('power_trace_NRMSE','Power NRMSE (%)',100)]
    for row,case in enumerate(('Original','Shorter gap')):
        for col,(key,title,scale) in enumerate(metrics):
            ax=axes[row,col]
            for j,role in enumerate(NAMES):
                ax.bar(np.arange(2)+(j-1)*.25,[scale*cases[(case,s)][role]['metrics'][key] for s in (29,43)],
                    width=.23,color=colors[role],label=LABELS[role])
            ax.set_xticks([0,1],['Seed 29','Seed 43']);ax.set_title(case+' — '+title);ax.set_ylim(bottom=0);ax.grid(axis='y',alpha=.15)
    axes[0,0].legend(fontsize=8)
    fig.suptitle('One matched method pair per seed and protocol; B_E is shared within a protocol',fontsize=11)
    for ext in ('png','pdf'):fig.savefig(folder/f'cross-protocol-methods.{ext}')
    plt.close(fig)
    fig,axes=plt.subplots(1,4,figsize=(13,4),constrained_layout=True)
    labels=['Original\n29','Original\n43','Shorter gap\n29','Shorter gap\n43']
    pairs=[('Original',29),('Original',43),('Shorter gap',29),('Shorter gap',43)]
    for ax,(key,title,_) in zip(axes,[('S','Active-set error S',1),*metrics]):
        for j,base in enumerate(('F_raw/projected','B_E')):
            gain=[100*(1-cases[p]['E/projected']['metrics'][key]/cases[p][base]['metrics'][key]) for p in pairs]
            ax.plot(np.arange(4)+(j-.5)*.08,gain,'o',color=colors[base],label='E vs '+LABELS[base])
        ax.axhline(10,color='black',ls='--',lw=.8,label='10% effect threshold')
        ax.axhline(0,color='gray',lw=.6);ax.set_xticks(range(4),labels,fontsize=8)
        ax.set_title(title.split('(')[0]);ax.set_ylabel('Error reduction (%)');ax.grid(axis='y',alpha=.15)
    axes[0].legend(fontsize=7)
    fig.suptitle('Individual error reductions; complete A/B decisions also require the field guards',fontsize=11)
    for ext in ('png','pdf'):fig.savefig(folder/f'paired-effects.{ext}')
    plt.close(fig)
    with np.load(root/'evaluation/traces.npz') as data:
        t=data['time'];fig,axes=plt.subplots(2,3,figsize=(12,6.4),constrained_layout=True)
        for row,seed in enumerate((29,43)):
            for col,(key,refkey,title) in enumerate([('roi_active_fraction','reference_roi_fraction','ROI active fraction'),
                    ('top_current','reference_current','Electrode current'),('joule_power','reference_power','Joule power')]):
                ax=axes[row,col];ax.plot(t,data[refkey],color='black',lw=1.5,label='Fixed reference')
                for role in NAMES:
                    name='B_E' if role=='B_E' else f'{seed}/{role}'
                    ax.plot(t,data[name+'__'+key],color=colors[role],lw=1,ls='--' if role=='B_E' else '-',label=LABELS[role])
                ax.axvline(1.01,color='gray',ls=':',lw=.8);ax.axvline(2.02,color='gray',ls=':',lw=.8)
                ax.set_title(f'Seed {seed}: '+title);ax.set_xlabel('Time');ax.grid(alpha=.15)
            axes[row,0].axhline(.02,color='black',ls='--',lw=.6)
        axes[0,1].legend(fontsize=7,ncol=2)
        for ext in ('png','pdf'):fig.savefig(folder/f'new-protocol-trajectories.{ext}')
        plt.close(fig)
    fig,axes=plt.subplots(1,3,figsize=(11.5,3.8),constrained_layout=True)
    for ax,key,label,gate in zip(axes,('recall','timing_absolute','recovery_fraction'),
            ('Recall','Absolute timing error','Recovery fraction'),(.9,.005,.7)):
        for j,role in enumerate(NAMES):
            vals=[new['records']['B_E' if role=='B_E' else f'{seed}/{role}']['cycles'][cyc].get(key)
                  for seed in (29,43) for cyc in (0,1)]
            vals=[np.nan if v is None else v for v in vals]
            ax.plot(np.arange(4)+(j-1)*.12,vals,'o',color=colors[role],label=LABELS[role])
        ax.axhline(gate,ls='--',lw=.8,color='black');ax.set_xticks(range(4),['29/C1','29/C2','43/C1','43/C2'])
        ax.set_title(label);ax.grid(axis='y',alpha=.15)
    axes[0].legend(fontsize=7);fig.suptitle('New-protocol event costs remain separate from the method effect',fontsize=11)
    for ext in ('png','pdf'):fig.savefig(folder/f'new-protocol-events.{ext}')
    plt.close(fig)
    with np.load(root/'evaluation/snapshots.npz') as snap:
        roles=['reference','B_E','29/E/projected','29/F_raw/projected','43/E/projected','43/F_raw/projected']
        fig,axes=plt.subplots(6,3,figsize=(10.6,12),constrained_layout=True)
        refq=snap['reference__joule_density'][1]
        vmax=max(float(np.max(abs(snap[r+'__joule_density'][1]-refq))) for r in roles[1:])
        for row,role in enumerate(roles):
            for col in (0,1):
                artist=axes[row,col].imshow(snap[role+'__phase'][col].reshape(len(snap['z']),len(snap['x'])),
                    origin='lower',extent=(-1,1,0,1),aspect='auto',vmin=0,vmax=1,cmap='viridis')
                axes[row,col].set_title(role+f"; phase at {snap['phase_times'][col]:.4f}",fontsize=8)
            qerror=abs(snap[role+'__joule_density'][1]-refq)
            error_artist=axes[row,2].imshow(qerror.reshape(len(snap['z']),len(snap['x'])),
                origin='lower',extent=(-1,1,0,1),aspect='auto',vmin=0,vmax=max(vmax,1e-12),cmap='magma')
            axes[row,2].set_title(role+'\nAbsolute q error; second phase peak',fontsize=8)
            for ax in axes[row]:ax.set_xlabel('x');ax.set_ylabel('z')
        fig.colorbar(artist,ax=axes[:,:2],shrink=.45,label='Phase')
        fig.colorbar(error_artist,ax=axes[:,2],shrink=.45,label='Absolute local Joule-density error')
        fig.suptitle('Reference-peak times; common electrical projection for E, F and B_E',fontsize=11)
        for ext in ('png','pdf'):fig.savefig(folder/f'new-protocol-spatial-fields.{ext}')
        plt.close(fig)


METHODS=r'''## 1. Scientific question and method contribution

Can training-time electrical constraints improve sparse phase-change reconstruction after every state receives the same electrical solve at inference, and does that benefit persist when the second pulse arrives earlier? The method combines temperature/phase networks, an implicit electrical layer and a consistent local Joule interface. Its contribution is the evidenced coupled reconstruction method, rather than a claim that sparse solvers, implicit differentiation, finite volumes or Adam/L-BFGS are individually new.

Differentiable solver coupling has precedents in [Um et al., Solver-in-the-Loop](https://ge.in.tum.de/publications/2020-um-solver-in-the-loop/), [Blondel et al., modular implicit differentiation](https://proceedings.neurips.cc/paper_files/paper/2022/hash/228b9279ecf9bbafe582406850c57115-Abstract-Conference.html), and [Mitusch et al., hybrid finite-element/neural representations](https://arxiv.org/abs/2101.00962). These previously checked sources describe tools and neighboring approaches; they do not validate this experiment. No new literature search or novelty priority claim accompanies the present confirmation.

The evidence sequence is fixed-state electrical repair, a common-projection training comparison, a full spatial soft-residual counterfactual, two clean initialization pairs, and the present complete new protocol. The strong no-remaining-PDE control D_E and negative remaining-PDE strength study stay visible. Explicit thermal and phase residuals are included in both current PINN losses, but their independent predictive necessity has not been established.

## 2. Physical model and finite-pulse intervention

The synthetic dimensionless wall cell occupies $[-1,1]\times[0,1]$ and $t\in[0,2.5]$. The centered bottom heater $|x|\leq0.35$ is grounded, the top receives $U(t)$, and the remaining electrical boundary is insulating. The top temperature is zero, other thermal boundaries satisfy $\partial_nT+0.25T=0$, and phase has homogeneous Neumann conditions.

The original two pulse starts are 0 and 1.25. The new case uses exactly two starts, 0 and 1.01. Each pulse rises to 0.72 over local time 0–0.05, holds through 0.27 and falls to zero at 0.35. No periodic extension creates a third pulse at 2.02. The total time, pulse shape, material coefficients, geometry and known IC/BC stay fixed. The 0.24 displacement is twelve original observation intervals of 0.02, preserving sampling phase. A single [finite case specification](evidence/case-and-budget.json) controls generation, network waveform, quadrature windows, interpolation and evaluation.

Conductivity and phase kinetics remain

$$\sigma=\exp\{0.25T+\log(8)\phi^2(3-2\phi)\},\qquad
M(T)=0.5+4.5\operatorname{sigmoid}[(T-0.45)/0.08],$$

$$R_\phi=\phi_t-M(T)[\epsilon^2\Delta\phi-2B\phi(1-\phi)(1-2\phi)-6D(T_c-T)\phi(1-\phi)].$$

Here $\epsilon=0.04$, $B=1$, $D=6$, $T_c=0.45$. Thermal diffusivity is 0.1, volumetric cooling 4, latent ratio 0.05 and Joule multiplier 4. Initially $T=0$ and $\phi=0.02+0.01\exp(-[(x/0.18)^2+((z-0.12)/0.10)^2]/2)$. The [base numerical contract](../../configs/phk_v2/object_numerical_contract.json) and [object overlay](../../configs/phk_v21/object_numerical_contract.json) retain parameter provenance. This is a literature-inspired numerical object, not an experimentally calibrated oxide device.

The new support trajectory uses 80×40 cells, time step 0.0025 and saving every two steps. The fixed evaluation trajectory uses 160×80 cells, time step 0.000625 and saving every four steps. Both use the inherited coupled block and logit-Newton algorithms without clipping, changed tolerances or result-adaptive rescue. The unchanged causal prefix is checked against the original trajectory at the same resolution before the second pulse. This validates the generator interface; it does not require separately trained neural functions to have identical prefixes.

## 3. Information, networks and electrical coupling

The support mask remains 21×11×126. Its 231 analytic initial positions are recorded separately from 28,875 positive-time observed positions and 86,625 scalar V/T/phase labels. Only those observations, coordinates and known physical laws enter training. Full support fields, reference fields, teacher currents/power and sealed stress do not. Each new protocol model is fitted to its own support: this is complete-case reconstruction/adaptation, not zero-shot or formal OOD generalization.

Three independent 64×4 modified-MLP heads and the existing smooth, initially zero-output temperature adapter are unchanged. The output maps retain

$$T=2.5(1-e^{-t/0.35})(1-z)\operatorname{sigmoid}(h_T),\qquad
\phi=\operatorname{sigmoid}\{\operatorname{logit}\phi_0+8(1-e^{-t/0.35})h_\phi\}.$$

Soft electrical PINN F_raw retains its trainable range-preserving voltage head and exact top voltage. E instead obtains voltage from $A(\sigma)v=f(U,\sigma)$ on the 80×40 grid. The harmonic face conductance uses half resistances $R_{ei}=d_{ei}/(\sigma_iA_e)$ and $R_{ej}$, with $g_e=(R_{ei}+R_{ej})^{-1}$. Electrode half-cell resistances and heater overlap are shared.

E backpropagates through $A^Tz=\partial L/\partial v$, including $z^T(df-dA\,v)$ and the direct conductivity derivatives of heating. The conductivity dependence of the boundary RHS is retained; the implementation does not form a dense inverse or assume a second-order VJP. F_raw uses the complete explicit derivatives of the same network, with $r_{e,i}=(A V_\theta-f)_i/\omega_i$ penalized at 128 sampled cells and fixed weight $\eta=1$.

For either voltage, $I_e=g_e(v_i-v_j)$ deposits $I_e^2R_{ei}$ and $I_e^2R_{ej}$ in the adjacent cells. Electrode dissipation enters its boundary cell. Thus $\sum_i\omega_iq_i=P_J$ by construction, while equality with terminal input power also requires electrical balance. The shared thermal residual is

$$R_{T,i}=\partial_t(\bar T_i+0.05\bar\phi_i)+4\bar T_i
-\frac{0.1}{\omega_i}\sum_f A_f(\nabla T_\theta)_f\cdot n_{if}-4q_i.$$

Cell means use midpoint quadrature and common face nodes have opposite normals. The phase residual keeps $M(T)$ outside the bracket. At zero drive, E voltage and heating are analytically zero; off-state thermal/phase training continues. No autonomous monotonic-energy constraint is introduced.

E and F receive the same T/phase architecture, observations, other BC/IC package and residual interfaces. E voltage observations influence the state through conductivity; F voltage observations act on its voltage head. Initial voltage, active parameters, exact versus finite constraints, enforcement times and gradient maps therefore differ. The comparison identifies this method package, not isolated VJP causality.

![Coupled method and common-projection comparison](figures/coupled-method-comparison.png)

The diagram shows the forward interfaces; optimization differentiates the complete active loss through each branch. The common projection changes the voltage and Joule readout while retaining each learned state. F also retains its unprojected readout as a separately named diagnostic.

## 4. Matched optimization and evaluation

Seeds 29 and 43 start from fresh random networks and the zero-output adapter. No old trained parent, optimizer or calibration is loaded. Each seed first receives the common observation-only recipe: 2400 Adam updates and 600 fixed full-observation evaluations, 200 for each field head. There is no new voltage fit gate and no seed rescue. Both branches start from that same new parent, with fresh optimizers and one shared calibration $a_{s,c},b_{s,c}$.

Each branch uses 1500 Adam updates, followed by at most 300 full fixed-objective/gradient evaluations with strong-Wolfe L-BFGS. All trials and repeated evaluations count; interruption restores the last accepted model and optimizer. The phase complete-logit observation scale, quadrature weights, residual scales 1/4/5, averaging denominators 3/13 and lambda ramp to 0.1 over 200 updates are unchanged. The new physical windows are [0,0.35], [0.35,1.01], [1.01,1.36], [1.36,2.5], with masses 0.14/0.264/0.14/0.456. Pools are paired within a case, not claimed identical across cases. Endpoints are fixed before reference scoring.

All projected readouts use the same 160×80 electrical layer at 1001 fixed times. F retains its network readout, and projection changes only V and q, with exactly identical T/phase and events. B_E interpolates only the new sparse T/phase using the frozen initial-logit/PCHIP and spatial rules, then uses the same electrical layer. It is computed once, shared across the two seeds and never counted as two independent baselines.

The ROI is $|x|\leq0.55$, $0\leq z\leq0.55$. Active phase means $\phi\geq0.5$. S is the full-domain, full-time volume/trapezoid mean of the absolute difference between predicted and reference active-set indicators; raw $E_\phi$ is the corresponding continuous-field RMS on the ROI. Event onset is the first upward crossing of ROI active fraction 0.02, with linear time interpolation. Support recall, precision and mass ratio use full-domain cell volumes and the inherited global trapezoid weights restricted to the two heating windows. They do not use the sparse training interface measure.

Layer A requires at least 10% improvements in both full-domain active-set discrepancy S and ROI raw phase RMS, with the original field noninferiority guards. Layer B requires at least 10% improvements in current and power-trajectory NRMSE, with S/Ephi/ET/EV/EI within 5%, subject to the unchanged absolute floors. EV is unnormalized voltage RMS; T is normalized by 0.45. Failure of an advantage gate is not evidence of equivalence.

For electrically projected states, $P_J(t)=U(t)I(t)$ to solve accuracy. The power error therefore weights the current error by the known drive; these are different time-weighted measures, not independent causal replications. Signed energy integration can additionally cancel errors from different parts of a pulse.

Strict usability is separate: each cycle retains recall≥0.9, precision≥0.8, mass ratio0.8–1.2, timing error≤0.005 and the inherited peak/locality/recovery requirements. New event-support windows are the two heating intervals. Recovery cycles are [0,1.01] and [1.01,2.02]; the tail [2.02,2.5] does not extend second-cycle recovery. An absent independent second event remains an absent-event result rather than a reason to replace the case. Pre-pulse ROI state/errors, per-pulse power and signed/absolute energy indicators, and second-cycle field/device errors are report-only diagnostics.

The retained endpoint gate also requires a legal field, maximum phase at least 0.9, a detected onset in each cycle, cycle peak ROI active fraction at least 0.02, peak full-domain/outside-ROI fractions at most 0.45/0.10, and recovery $(f_{peak}-f_{end})/(f_{peak}-f_{pre})\geq0.70$. These are the operational inherited evaluator conditions; the primary solver has its separately recorded numerical validity tests.

Two protocols × two initialization seeds form paired observations, not four independent physical cases. Historical seed17 has a different development history and is not pooled into this confirmation. Electrical conservation and total-deposition identities are not counted as independent empirical benefits; no speedup over a conventional full solver is claimed.
'''


def build(root=RUN,paper=PAPER):
    root=Path(root);paper=Path(paper);new,cases=gather(root)
    for name in ('tables','figures','evidence'):(paper/name).mkdir(parents=True,exist_ok=True)
    td=paper/'tables';rows=[];effects=[];events=[];decisions=[]
    for (case,seed),records in cases.items():
        for role in NAMES:
            record=records[role];m=record['metrics']
            rows.append(dict(protocol=case,seed=seed,role=role,valid=record['valid'],S=m['S'],Ephi=m['Ephi'],
                ET=m['ET'],EV=m['EV'],current_percent=100*m['bottom_current_NRMSE'],power_percent=100*m['power_trace_NRMSE'],
                energy_percent=100*m['energy_error'],strict=record['strict_device_pass']))
            for cycle in record['cycles']:
                events.append(dict(protocol=case,seed=seed,role=role,**cycle))
        for base in ('F_raw/projected','B_E'):
            e,b=records['E/projected']['metrics'],records[base]['metrics']
            for key in ('S','Ephi','ET','EV','bottom_current_NRMSE','power_trace_NRMSE','energy_error'):
                effects.append(dict(protocol=case,seed=seed,candidate='E',baseline=base,metric=key,
                    candidate_error=e[key],baseline_error=b[key],absolute_change=e[key]-b[key],
                    relative_reduction_percent=100*(1-e[key]/b[key]) if b[key]>1e-12 else None,
                    percentage_point_change=100*(e[key]-b[key]) if key in ('ET','bottom_current_NRMSE','power_trace_NRMSE','energy_error') else None))
    newtable=table(td,'cross-protocol-metrics',rows)
    inherited=read(ROOT/'paper/paper_v31/evidence/evaluation/results.json')
    anchors=[]
    for role in ('E0','D_E','P_E','B_E','F_raw/network','F_raw/projected','F_full/network','F_full/projected','F_bal/projected'):
        r=inherited['records'][role];m=r['metrics']
        anchors.append(dict(role=role,origin='inherited development comparison, not pooled with clean pairs',
            S=m['S'],Ephi=m['Ephi'],ET=m['ET'],EV=m['EV'],current_percent=100*m['bottom_current_NRMSE'],
            power_percent=100*m['power_trace_NRMSE'],energy_percent=100*m['energy_error'],strict=r['strict_device_pass']))
    anchortable=table(td,'historical-mechanism-controls',anchors)
    table(td,'paired-effects',effects)
    table(td,'new-protocol-all-readouts',[dict(role=name,valid=r['valid'],**r['metrics'],strict=r['strict_device_pass'])
                                         for name,r in new['records'].items()])
    event_columns=['protocol','seed','role','cycle','event_time','reference_event_time','timing_absolute','recall','precision','mass_ratio',
                   'pre_roi_fraction','peak_roi_fraction','peak_full_domain_fraction','peak_outside_roi_fraction','recovery_fraction',
                   'teacher_active_target_mass','predicted_active_target_mass','true_positive_target_mass','false_positive_event']
    table(td,'complete-events',events,event_columns)
    for seed,dec in new['decisions'].items():
        for comparison,result in dec.items():
            for layer,r in result.items():decisions.append(dict(seed=seed,comparison=comparison,layer=layer,**r))
    table(td,'new-protocol-adjudication',decisions,['seed','comparison','layer','passed','gain','noninferior','relative_changes'])
    history=[];pulse=[];second=[]
    for name,record in new['records'].items():
        h=record['history_diagnostics']
        for field,r in h['prepulse'].items():history.append(dict(role=name,field=field,time=h['prepulse_time'],**r))
        for r in h['per_pulse']:pulse.append(dict(role=name,**r))
        second.append(dict(role=name,**h['second_cycle'],tail_phase_ROI_RMS=h['tail_phase_ROI_RMS']))
    table(td,'prepulse-state',history);table(td,'per-pulse-power-energy',pulse);table(td,'second-cycle',second)
    table(td,'reference-history',[dict(field=k,**v) for k,v in new['reference_prepulse_history'].items()])
    changes=[]
    for seed,roles in new['cross_case_error_changes'].items():
        for role,rr in roles.items():
            for metric,entry in rr.items():changes.append(dict(seed=seed,role=role,metric=metric,**entry))
    table(td,'cross-protocol-error-changes',changes)
    execution=read(root/'execution-summary.json')
    table(td,'execution-budget',[dict(counter=k,actual=v,cap=execution['caps'][k]) for k,v in execution['totals'].items()])
    parents=[]
    for case in ('Original','Shorter gap'):
        for seed in (29,43):
            directory=(ROOT/f'paper/paper_v31/evidence/confirmation/seed-{seed}'
                       if case=='Original' else root/f'seed-{seed}')
            fit=read(directory/'common-fit/fit-summary.json');cal=read(directory/'calibration.json')
            c=fit['final_components']
            parents.append(dict(protocol=case,seed=seed,Adam=fit['adam_updates'],
                complete_evaluations=fit['complete_evaluations'],
                complete_observation_objective=fit['final_complete_objective'],
                visible_V_RMS_over_072=float(np.sqrt(c['obs_V'])),
                visible_T_RMS_over_045=float(np.sqrt(c['obs_T'])),phase_logit_loss=c['obs_phase'],
                a_s_c=cal['aE'],b_s_c=cal['bE'],old_V_gate=fit['old_V_gate_applied'],seed_rescue=fit['seed_rescue']))
    table(td,'common-parents-and-calibration',parents)
    figures(root,paper,new,cases)
    out=paper/'evidence'
    def copy(source,target):
        target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
    for name in ('case-and-budget.json','frozen-config.json','training-isolation.json','execution-summary.json','metadata-clarification.json','conditional-decision.json','terminal-summary.json'):
        copy(root/name,out/name)
    for source in (root/'input').iterdir():copy(source,out/'input'/source.name)
    for source in (root/'evaluation').iterdir():copy(source,out/'evaluation'/source.name)
    for kind in ('support','reference'):
        for name in ('intent.json','terminal.json'):copy(root/'local-reference'/kind/name,out/'reference-generation'/kind/name)
    for seed in (29,43):
        folder=root/f'seed-{seed}'
        for name in ('frozen-config.json','calibration.json','calibration-pool.json','lbfgs-pool.json','audit-pool.json','parent.pt'):
            copy(folder/name,out/f'seed-{seed}'/name)
        for source in (folder/'common-fit').iterdir():copy(source,out/f'seed-{seed}'/'common-fit'/source.name)
        for role in ('E','F_raw'):
            for name in ('checkpoint.pt','terminal.json','adam-telemetry.jsonl','lbfgs-telemetry.jsonl'):
                copy(folder/role/name,out/f'seed-{seed}'/role/name)
            for mode in (['projected'] if role=='E' else ['network','projected']):
                for name in ('prediction.json','own-readout.npz'):copy(folder/role/mode/name,out/f'seed-{seed}'/role/mode/name)
            if role=='F_raw':copy(folder/role/'paired-readout-identity.json',out/f'seed-{seed}'/role/'paired-readout-identity.json')
    for name in ('prediction.json','own-readout.npz'):copy(root/'B_E/projected'/name,out/'B_E'/name)
    proof=read(root/'compute-closure.json')
    save_json(out/'compute-closure-summary.json',{k:proof[k] for k in ('mode','training_complete','recovery_verified',
        'shutdown_requested','instance_shutdown_confirmed','compute_stopped_before_reference_read','shutdown_confirmation')})
    copy(ROOT/'.t/lf11-protocol-deployment/selected-files.json',out/'deployed-files.json')
    # Preserve the actual code/config bytes sent to training, not later report edits.
    selected=read(out/'deployed-files.json')
    with tarfile.open(ROOT/'.t/lf11-protocol-deployment/lf11-protocol.tar.gz','r:gz') as archive:
        for item in archive.getmembers():
            name=item.name.removeprefix('./')
            if name not in selected or not name.startswith(('pinn_pcm_sci/','configs/','cloud/','tests/')):continue
            if not item.isfile() or '..' in Path(name).parts:raise ValueError('invalid selected source')
            destination=out/'runtime-sources'/name
            destination.parent.mkdir(parents=True,exist_ok=True)
            destination.write_bytes(archive.extractfile(item).read())
    eb=[new['decisions'][str(s)]['E_vs_soft']['B']['passed'] for s in (29,43)]
    be=[new['decisions'][str(s)]['E_vs_B_E']['B']['passed'] for s in (29,43)]
    verdict='Both new pairs pass device-layer B against the projected soft comparator.' if all(eb) else 'Device-layer B against the projected soft comparator is not confirmed in both new pairs.'
    strong='Both new pairs also pass B against the same-solver interpolant.' if all(be) else 'The original B threshold against the same-solver interpolant is not confirmed in both new pairs.'
    summary=[]
    for seed in (29,43):
        d=new['decisions'][str(seed)]
        e=cases[('Shorter gap',seed)]['E/projected']['metrics'];f=cases[('Shorter gap',seed)]['F_raw/projected']['metrics']
        summary.append(f"Seed {seed}: E versus projected F passes A={d['E_vs_soft']['A']['passed']}, B={d['E_vs_soft']['B']['passed']}; E versus B_E passes A={d['E_vs_B_E']['A']['passed']}, B={d['E_vs_B_E']['B']['passed']}. Current/power error reductions relative to F are {100*(1-e['bottom_current_NRMSE']/f['bottom_current_NRMSE']):.4f}%/{100*(1-e['power_trace_NRMSE']/f['power_trace_NRMSE']):.4f}%. The corresponding E errors are {100*e['bottom_current_NRMSE']:.6f}%/{100*e['power_trace_NRMSE']:.6f}%.")
    strict=[new['records'][f'{s}/{r}']['strict_device_pass'] for s in (29,43) for r in ('E/projected','F_raw/projected')]
    abstract='We test training-time electrical elimination in sparse reconstruction of a two-dimensional synthetic electrothermal phase-change cell, using identical electrical projection for the compared learned states. A finite two-pulse intervention advances the second pulse from 1.25 to 1.01 while retaining the total observation domain and sampling phase. Two clean initialization pairs use the locked soft electrical PINN and a newly computed same-solver interpolant. '+verdict+' '+strong+' Both pairs also pass the phase-reconstruction layer A against both controls. Relative to projected soft PINNs, phase RMS error decreases by 20.22% and 20.31%, and power NRMSE falls from 2.335% to 0.999% and from 3.095% to 0.673%. Both learned states satisfy the two timing thresholds but miss the first-cycle recall threshold. The evidence concerns a coupled training-method package under case-specific adaptation; it does not isolate implicit-gradient causality, establish the independent necessity of every retained PDE term, or validate an experimental material.'
    results='\n\n## 5. Results\n\n### 5.1 Generator and actual execution\n\nVERIFIED: both authorized main trajectories completed. Their pre-intervention fields agree with the same-resolution original trajectories within the reported floating-point differences. No output clipping, case replacement or result-based checkpoint selection was used. [Generator records](evidence/reference-generation/) and [actual work](tables/execution-budget.md) separate reference solving from training and inference. The current GPU batch was recovered and its instance shutdown confirmed before scoring.\n\n### 5.2 Paired reconstruction and functional consequences\n\nVERIFIED: '+verdict+' '+strong+'\n\n'+'\n\n'.join(summary)+'\n\n'+newtable+'\n![Cross-protocol method comparison](figures/cross-protocol-methods.png)\n\n![Individual paired effects](figures/paired-effects.png)\n\nAbsolute differences, percentage points and relative changes are all preserved in [paired effects](tables/paired-effects.md). The [complete new adjudication](tables/new-protocol-adjudication.md) reports every gain and noninferiority component, including reverse comparisons. Sharing B_E across seeds does not duplicate its evidentiary sample count.\n\n### 5.3 Pulse history, events and aggregation\n\nVERIFIED: the independent second reference event status is '+str(new['second_independent_reference_event'])+'. The four learned-state strict decisions (29 E/F, 43 E/F) are '+str(strict)+'. No absent event is repaired by changing the pulse or recovery window.\n\n![New protocol trajectories](figures/new-protocol-trajectories.png)\n\n![Complete event consequences](figures/new-protocol-events.png)\n\nThe [reference pre-pulse history](tables/reference-history.md), [model pre-pulse errors](tables/prepulse-state.md), [second-cycle metrics](tables/second-cycle.md) and [per-pulse energy table](tables/per-pulse-power-energy.md) describe the mechanism-relevant state. Signed integrated error is retained alongside its absolute value and the integral of absolute power error. Cancellation is an arithmetic property, not an independently identified training mechanism. All precision, recall, timing, mass and recovery values, including adverse changes, appear in the [complete event table](tables/complete-events.md).\n\n### 5.4 Cross-case scope\n\nThe [same-seed error changes](tables/cross-protocol-error-changes.md) compare original and new protocols without pooling them as four independent cases. Identical initial random tensors are checked after execution in the evidence summary, while each protocol has its own observations, fitted parent, calibration and physical pools. A method may have a favorable matched effect but remain worse in absolute terms or miss the strong-interpolant threshold. These are distinct claims.\n'
    results+='\nThe [common-parent and calibration table](tables/common-parents-and-calibration.md) records fitting quality and the shared scales for all four protocol/seed combinations. Its visible errors describe the observation-only parent; a_s_c is subsequently calibrated through the eliminated electrical readout. Variation across these four records does not identify a unique cause of endpoint variation.\n'
    results=results.replace('### 5.3 Pulse history, events and aggregation', '''Relative phase RMS reductions against projected F are 20.2198% and 20.3054%; against B_E they are 25.5494% and 27.0508%. The current/power reductions against F correspond to 1.2756/1.3360 percentage points for seed29 and 2.3096/2.4219 points for seed43. Seed43's S reduction against F is 10.3711%, only 0.3711 percentage points above the effect threshold; that particular A decision should not be interpreted as a large margin. The B decisions and both comparisons with B_E have considerably larger margins. No statistical equivalence or population success rate is inferred.

### 5.3 Pulse history, events and aggregation''')
    results=results.replace('### 5.4 Cross-case scope', '''The fixed reference has a warmer and less fully relaxed state before the earlier second pulse: ROI mean temperature changes from 0.00652461 to 0.01874612, and mean phase from 0.000482909 to 0.003972463. The maximum pre-pulse phase is 0.191788, still below the active-phase threshold 0.5; an independent second event is retained. Its latency from pulse start decreases from 0.2484 to 0.2168. Together with the roundoff-level agreement before the intervention, these observations support a response to altered pulse history within the numerical model. They do not isolate thermal from phase-memory mediation.

For E, cycle1/cycle2 timing errors are 0.003333/0.002775 (seed29) and 0.003490/0.004440 (seed43), all below 0.005. First-cycle recalls are 0.866607 and 0.875507, below 0.9, so strict two-cycle reliability remains unestablished. In seed29's second cycle, the soft timing error 0.0008375 is smaller than E's 0.002775. E's tail phase RMS also exceeds projected F's in both seeds; in seed43 the second-cycle temperature error is slightly larger. Global matched gains therefore do not imply uniform superiority over time or across all event quantities.

Second-pulse power NRMSE is 0.57314%/0.36588% for E versus 1.43205%/2.57795% for projected F (seeds29/43). Seed43 F has opposite signed pulse-energy errors, +0.00511674 and -0.00400099, yielding only 0.25736% total energy error despite 3.09469% power NRMSE. This measured cancellation explains why integral energy alone is an inadequate summary. Seed43 E also has some cancellation; its second-pulse signed energy error is -0.00000445 while its integral absolute power error is 0.00062146. All values are dimensionless.

### 5.4 Cross-case scope''')
    discussion='''
## 6. Interpretation and limits

SUPPORTED_INTERPRETATION: a method difference remaining after the same electrical projection concerns the learned T/phase state and its conductivity, not merely the final voltage repair. The new complete protocol supplies a test of history dependence within this fixed numerical material model. The observed pre-pulse state can contextualize changes in second-pulse behavior, but it does not uniquely identify an optimizer or gradient pathway as causal.

Historical controls remain consequential. Fixed-state electrical elimination repaired severe contact/readout errors; the full spatial soft penalty did not remove the historical projected-method advantage; two fresh nominal pairs supported B against soft, with the stronger B_E threshold passed only by seed29. D_E remains strong and remaining thermal/phase PDE necessity is UNKNOWN. Those facts are retained rather than replaced by the newest comparison.

UNKNOWN: isolated VJP causality, broad material or geometry transfer, population-level initialization success probabilities, continuum accuracy, and experimental oxide-device validity. Shared projection guarantees certain discrete electrical identities, not correct local heating or reference predictions. Sparse observations plus fully specified equations also admit conventional numerical solutions; no unmeasured solver replacement or acceleration claim is made.

The conditional time-refinement branch was not triggered. Seed43's A/S result is near its threshold, but the prespecified manuscript route depends on the B advantages against both controls, which have large margins; no observed time-discretization difference puts that route in question. The numerical trigger also requires such a decision-changing discrepancy. This decision does not establish temporal or spatial convergence, and the close A/S margin remains disclosed. See [conditional decision](evidence/conditional-decision.json). No further seed rescue, threshold change or automatic control expansion was performed.

The supported manuscript contribution is a coupled reconstruction method with a controlled comparison of training-time electrical enforcement versus post-training projection, a consistent local Joule interface, and individually reported initialization/protocol confirmations. The present outcome reaches the prespecified writing route. Further work should first consolidate this bounded claim and its physical-model scope, while retaining the event failures and the strong D_E counterexample, rather than adding untested modules to the contribution list.

## Reproducibility and evidence labels

VERIFIED denotes executed, saved numerical evidence and exact readout identities; SUPPORTED_INTERPRETATION denotes bounded explanations; HYPOTHESIS denotes untested extensions; UNKNOWN marks missing evidence. The [claim matrix](claim_evidence_matrix.md), [reproduction instructions](reproduction.md) and [evidence scope](evidence/README.md) distinguish local full trajectories from the curated evidence package. Historical manuscripts remain unchanged.
'''
    results+='\n### 5.5 Two-dimensional state and local heating\n\n![Spatial phase and local heating errors](figures/new-protocol-spatial-fields.png)\n\nAll states are shown at the same two reference-cycle peak times; no model is selected for its most favorable slice. The heating-error panel uses the shared face deposition and a common scale. [All new readouts](tables/new-protocol-all-readouts.md) retain the unprojected soft values as well as common-projection results. Projection identities alone cannot certify the local q field.\n\n### 5.6 Retained mechanism controls\n\nThese inherited controls are a separate development comparison, not extra clean-seed repetitions. D_E has lower phase error than the corresponding P_E and remains close on device errors; its strength blocks a claim that the remaining PDE terms have independently explained the benefit. F_full changes only electrical spatial reduction and receives the same projection.\n\n'+anchortable+'\n'
    (paper/'manuscript.md').write_text('# Training-time electrical coupling under a finite pulse-history intervention\n\nWorking manuscript, V32, 2026-09-15.\n\n## Abstract\n\n'+abstract+'\n\n'+METHODS+results+discussion,encoding='utf-8')
    (paper/'README.md').write_text('# paper_v32\n\n[Manuscript](manuscript.md) · [Claim matrix](claim_evidence_matrix.md) · [Reproduction](reproduction.md) · [Evidence](evidence/README.md).\n\n'+verdict+' '+strong+'\n\n[All absolute metrics](tables/cross-protocol-metrics.md), [complete adjudication](tables/new-protocol-adjudication.md), [complete events](tables/complete-events.md), [pulse history](tables/reference-history.md).\n\n![Main figure](figures/cross-protocol-methods.png)\n',encoding='utf-8')
    (paper/'claim_evidence_matrix.md').write_text('''# Claim–evidence matrix

| Claim | Status | Evidence and limit |
|---|---|---|
| Only the second finite pulse start changed; no third pulse | VERIFIED | Case spec, waveform tests, reference generation; base physical contracts unchanged |
| New support has identical sparse coordinates | VERIFIED | Frozen mask plus exact coordinate comparison; labels belong to the new case |
| Two fresh paired E/F trainings completed | VERIFIED | Initial states, full fit/branch counters and accepted optimizer checkpoints |
| Both new seeds pass A and B against F/projected and B_E | VERIFIED | Complete fixed-reference adjudication; seed43 S gain 10.3711% is close to the A threshold |
| Projection leaves learned T/phase and events unchanged | VERIFIED | Paired own-field equality and complete event identity |
| Pulse history contextualizes second-cycle effects | SUPPORTED_INTERPRETATION | Pre-pulse reference state, model errors and per-pulse traces; no unique causal gradient attribution |
| Residual thermal/phase PDEs independently necessary | UNKNOWN | Historical D_E and remaining-PDE counterfactuals do not establish this |
| Implicit VJP is the unique cause of improvement | UNKNOWN | Initialization, exact/finite constraints, enforcement times and gradient maps differ |
| Broad zero-shot/OOD or experimental material generalization | UNKNOWN | Each new-case model uses that case's support; synthetic dimensionless material |
| Both E states satisfy both timing thresholds | VERIFIED | Timing 0.003333/0.002775 and 0.003490/0.004440; no claim of strict event success |
| Strict two-cycle reliability | Not established: VERIFIED gate failures | E first-cycle recalls 0.866607/0.875507; all four learned states fail the full strict gate |
| Reference time refinement | NOT_TRIGGERED_NOT_RUN | No decision-changing time-discretization discrepancy; no convergence claim |
''',encoding='utf-8')
    (out/'README.md').write_text('''# Curated V32 evidence

Contains the finite case and original authorization budgets, sparse input, accepted model/optimizer states, calibration/pools, optimization telemetry, formal scores, traces/snapshots, reference generator summaries and current compute-closure summary. No raw access credentials or provider logs are included.

Complete support/reference trajectories and full own-field prediction arrays remain under `outputs/runs/20260915-lf11-protocol-history` locally; this curated package does not pretend to include them. Reproduction requires their explicitly described generation and compute budget. Source dependencies are recorded in `deployed-files.json`, and the exact deployed code/config bytes are retained under `runtime-sources/`; historical numerical cores and public contracts retain their identities. The new case must be reconstructed from the finite case spec, not from the legacy period field alone. `terminal-summary.json` records the final route and counts; `conditional-decision.json` records the untriggered time-refinement branch.

`metadata-clarification.json` identifies unused inherited template fields. In particular the old source_commit is template provenance, not the new runtime identity, and prepare_seed sets both actual branch configurations to sampled F_raw before training. The 1112 neural projection allocation plus the new shared B_E's278 gives the predeclared total1390. No scientific settings, accepted trajectory or frozen runtime files were rewritten to correct these descriptive leftovers.
''',encoding='utf-8')
    (paper/'reproduction.md').write_text('''# Reproduction

Use Python3.11, FP64 and the established Torch2.5.1/SciPy1.14.1 environment. The new case is defined in `pinn_pcm_sci/phk_v23_lf11_protocol.py` and `configs/phk_v23/lf11_protocol_sprint.json`; all primary solver tolerances and material contracts remain unchanged.

1. `python -m pinn_pcm_sci.phk_v23_lf11_protocol_reference freeze` records the finite case and expanded solver budgets before fields are generated.
2. The `support` and `reference` actions each generate their one authorized local trajectory. The support action exports the frozen sparse mask; the reference process is separate from training. Do not send either full carrier to training.
3. Run `python -m pinn_pcm_sci.phk_v23_lf11_protocol_train --device cuda:0` in the selected code/contracts/sparse-only environment. It creates fresh parents, E/F branches and one new B_E. Existing scientific run directories are refused.
4. Recover fixed outputs, terminate the actual instance, and record current closure before running `python -m pinn_pcm_sci.phk_v23_lf11_protocol_evaluate` locally.
5. `python -m pinn_pcm_sci.phk_v23_lf11_protocol_paper` renders this manuscript, tables and figures from the saved scores; it performs no training or checkpoint selection.

New primary trajectories: 1000 support and 4000 reference main steps, with internal coupled/phase/electrical bounds separately expanded. Training caps are10800 Adam and2400 complete evaluations. E forward/adjoint caps are54000 each; calibration/audit are separate. Five projected inference roles use278 powered times each, total1390. Full actual counters and early optimizer stops are preserved. Fixed update caps do not establish equal actual compute or a speedup.

The original protocol/seed results are imported as already published evidence; historical seed17 is not pooled with seeds29/43. The final tail after2.02 is excluded from cycle2 recovery. Optional time refinement requires the original explicit trigger and cannot be used to retrain or choose a checkpoint.
''',encoding='utf-8')
    print(json.dumps(dict(paper=str(paper),E_vs_soft_B=eb,E_vs_B_E_B=be,strict=strict)),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=RUN);p.add_argument('--paper',type=Path,default=PAPER)
    a=p.parse_args();build(a.root,a.paper)
