"""Rebuild saved numerical measures, then report the locked conditional result.

This consumes recovered arrays only: no model queries, solver steps or training.
"""
from pathlib import Path
import csv,json,hashlib
from datetime import datetime,timezone
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pinn_pcm_sci.phk_benchmark import PhkGrid
from pinn_pcm_sci.phk_v23_conditional_phase import phase_rhs,time_weights,mean_square
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
RUN=ROOT/'outputs/runs/20260925-fixed-temperature-phase-probe'
def read(name):return json.loads((RUN/name).read_text(encoding='utf-8'))
def save(name,obj):(RUN/name).write_text(json.dumps(obj,indent=2,allow_nan=False),encoding='utf-8')
def fmt(v):return f'{v:.8g}' if isinstance(v,(float,np.floating)) else str(v)
def tab(headers,rows):return '| '+' | '.join(headers)+' |\n|'+'---|'*len(headers)+'\n'+'\n'.join('| '+' | '.join(map(fmt,row))+' |' for row in rows)+'\n'
r=read('result.json');cfg=read('frozen-config.json');p=read('physics.json');lock=read('trajectories-locked.json');cache=read('cache-complete.json');complete=read('run-complete.json');closure=read('compute-closure.json')
g=PhkGrid.build(nx=80,nz=40,**{k:p[k] for k in ('x_min','x_max','z_min','z_max')});volume=g.cell_volumes/g.cell_volumes.sum()
c=RUN/'cache';t=np.load(c/'time_common.npy');w=time_weights(t);T=np.load(c/'temperature_fine.npy',mmap_mode='r')
base=np.load(c/'B0_phase.npy',mmap_mode='r');Bdt=np.load(c/'B0_phase_t_AD.npy',mmap_mode='r');Tdt=np.load(c/'temperature_t_AD.npy',mmap_mode='r');flux=np.load(c/'thermal_flux.npy',mmap_mode='r')
phase={label:np.load(RUN/label/'phase.npy',mmap_mode='r') for label in ('coarse','fine')}
fields={'B0':base,'coarse':phase['coarse'],'fine':phase['fine'][::2]}
old_metrics=read('common-metrics.json')['state_metrics'];verified={};work_rows=[]
for i,label in enumerate(('coarse','fine')):
    u=phase[label];dt=cfg['dt'][i];ts=np.load(RUN/label/'time.npy');stride=2 if label=='coarse' else 1
    np.testing.assert_array_equal(u[0],base[0]);np.testing.assert_array_equal(ts,t if label=='coarse' else np.load(c/'time_fine.npy'))
    steps=list(csv.DictReader((RUN/label/'steps.csv').open()));maximum=0.;discrepancy=0.
    assert len(steps)==len(u)-1==cfg['steps'][i]
    for k in range(1,len(u)):
        norm=float(np.max(np.abs(u[k]-u[k-1]-dt*phase_rhs(u[k],T[k*stride],g,p))))
        maximum=max(maximum,norm);discrepancy=max(discrepancy,abs(norm-float(steps[k-1]['residual_inf'])))
        assert np.isfinite(u[k]).all() and (u[k]>0).all() and (u[k]<1).all()
    assert maximum<=cfg['algebraic_tolerance'] and discrepancy<1e-14
    ex=np.load(RUN/label/'export-265.npz');np.testing.assert_array_equal(ex['phase'],u[::cfg['export_every'][i]])
    counts=lock['trajectories'][label]['counts']
    work_rows.append([label,len(u)-1,counts['newton_iterations'],counts['linear_solves'],maximum,maximum/dt,lock['trajectories'][label]['seconds']])
    verified[label]=dict(internal_steps=len(u)-1,max_algebraic_defect=maximum,max_rate_defect=maximum/dt,log_discrepancy=discrepancy,export_count=len(ex['time']))
for label,u in fields.items():
    phase_ms=primary=cross=0.
    for k in range(len(t)):
        du=(-3*u[0]+4*u[1]-u[2])/(2*cfg['dt'][0]) if k==0 else (3*u[-1]-4*u[-2]+u[-3])/(2*cfg['dt'][0]) if k==len(t)-1 else (u[k+1]-u[k-1])/(2*cfg['dt'][0])
        rhs=phase_rhs(u[k],T[2*k],g,p);tr=Tdt[k]+p['volumetric_cooling']*T[2*k]-p['thermal_diffusivity']*flux[k]
        phase_ms+=w[k]*float(volume@((du-rhs)**2))
        primary+=w[k]*float(volume@((tr+p['latent_ratio']*(Bdt[k] if label=='B0' else rhs))**2))
        cross+=w[k]*float(volume@((tr+p['latent_ratio']*du)**2))
    actual=[phase_ms,primary,cross];expected=[old_metrics[label][key] for key in ('phase_common_MS','thermal_conditional_semidiscrete_MS','thermal_common_fd_MS')]
    np.testing.assert_allclose(actual,expected,rtol=2e-12,atol=2e-14)
    verified[label+'_common_metrics']=actual
reference=np.load(RUN/'reference-diagnostic-265.npz');truth=reference['phase_restricted'];tw=time_weights(reference['time']);masks={'full':np.ones(g.cell_count,dtype=bool),'roi':(abs(g.cell_x)<=.55)&(g.cell_z<=.55)}
active_rows=[]
for scope,mask in masks.items():
    v=volume[mask];v=v/v.sum()
    for label,u in fields.items():
        phi=u[::4,mask];err=phi-truth[:,mask];score=float(np.sqrt(tw@(err*err@v)))
        np.testing.assert_allclose(score,r['reference']['records'][scope][label]['Ephi_D_80'],rtol=2e-12,atol=2e-14)
        pred=(phi>=.5).astype(float)
        for key in ('restricted_native_indicator','threshold_after_restriction'):
            active=reference[key][:,mask];pm=float(tw@(pred@v));am=float(tw@(active@v));tp=float(tw@((pred*active)@v));fp=pm-tp;fn=am-tp
            active_rows.append(dict(scope=scope,state=label,reference_semantics=key,predicted_mass=pm,reference_mass=am,true_positive_mass=tp,false_positive_mass=fp,false_negative_mass=fn,symmetric_difference_mass=fp+fn,recall=tp/am if am else None,precision=tp/pm if pm else None))
with (RUN/'active-support-diagnostics.csv').open('w',newline='',encoding='utf-8') as f:
    writer=csv.DictWriter(f,fieldnames=list(active_rows[0]));writer.writeheader();writer.writerows(active_rows)
save('saved-array-verification.json',dict(passed=True,verified=verified,reference_error_rebuilt=True,model_queries=0,phase_solver_calls=0,training_updates=0,comparison_tolerance=dict(rtol=2e-12,atol=2e-14)))
save('environment-observation.json',dict(source='Direct SSH prelaunch hardware and interpreter output, recorded in this task; transcribed locally after verified shutdown',gpu='Tesla V100-PCIE-32GB',gpu_memory_class_gb=32,cpu_quota_cores=6,container_memory_bytes=26843545600,python='3.11.9',torch='2.5.1+cu118',numpy='2.1.1',scipy='1.14.1',cpu_threads=4,coordinate_chunk=1024,gpu_peak_allocated_bytes=None,gpu_peak_note='GPU limits were checked during execution; peak allocation was not persisted. No peak value is inferred.'))

plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False})
fig,axs=plt.subplots(3,3,figsize=(9.2,6.6),layout='constrained')
for row,(label,values) in enumerate([('B0',base[::4]),('Conditional fine',fields['fine'][::4]),('Restricted reference',truth)]):
    for col,k in enumerate((0,132,264)):
        ax=axs[row,col];im=ax.imshow(values[k].reshape(40,80),origin='lower',extent=[-1,1,0,1],vmin=0,vmax=1,cmap='viridis',aspect='equal')
        ax.set_title(f'{label}, t={reference["time"][k]:.3f}');ax.set_xlabel('x');ax.set_ylabel('z')
fig.colorbar(im,ax=axs,shrink=.72,label='Phase fraction');fig.savefig(HERE/'figures/conditional-phase-fields.png',dpi=210);plt.close(fig)
rows=list(csv.DictReader((RUN/'common-components.csv').open()))
fig,axs=plt.subplots(1,3,figsize=(10.5,3.3),layout='constrained')
for label,color in [('B0','#555555'),('coarse','#C7781D'),('fine','#176B87')]:
    rr=[x for x in rows if x['state']==label]
    for j,key in enumerate(('phase_common_MS','thermal_conditional_semidiscrete_MS','thermal_common_fd_MS')):
        axs[j].plot(t,[float(x[key]) for x in rr],label=label,color=color,lw=1.2,ls='--' if label=='coarse' else '-')
        axs[j].set_xlabel('t');axs[j].set_yscale('log');axs[j].grid(alpha=.2)
for ax,title in zip(axs,['Common phase residual MS','Conditional heat residual MS','Common-difference heat MS']):ax.set_title(title)
axs[0].legend();fig.savefig(HERE/'figures/conditional-residuals.png',dpi=210);plt.close(fig)

heatrows=[]
for q,name in [('conditional_semidiscrete','Conditional'),('common_fd','Common FD')]:
    v=r['thermal'][q]
    for label in ('coarse','fine'):heatrows.append([name,label,v['base'],v[label],v['upper'],v['margins'][label],v['observed_step_difference']])
refrows=[]
for scope,record in r['reference']['records'].items():
    for label in ('B0','coarse','fine'):refrows.append([scope,label,record[label]['Ephi_D_80'],record['direction']['gains'].get(label,'not applicable'),record['direction']['observed_step_difference']])
seamrows=[]
for label in ('coarse','fine'):
    for side in ('left','right'):
        for order,stats in r['seams'][label][side].items():seamrows.append([label,side,order,stats['rms'],stats['max_absolute'],stats['scaled_rms'],f"({stats['x']:.4f}, {stats['z']:.4f})"])
active_display=[[x['scope'],x['state'],'native indicator' if x['reference_semantics']=='restricted_native_indicator' else 'threshold after restriction',x['reference_mass'],x['symmetric_difference_mass'],x['recall']] for x in active_rows]
q=r['qualification'];err=r['reference']['records'];improvement=100*(1-err['full']['fine']['Ephi_D_80']/err['full']['B0']['Ephi_D_80'])
body=f'''## S23. Fixed-temperature conditional phase evolution

### S23.1 Question and frozen numerical contract

This supplementary development diagnostic asks whether phase evolution under the frozen B1 E/29 temperature can reduce the remaining uncertainty enough to justify searching the original correction family. It is not a neural training arm or an original-family feasibility certificate. The grid is 80 by 40, D=[1.36,2.02], and the exact initial network phase is used without clipping or smoothing. The original zero-flux operator and all B0 coefficients are retained: interface width 0.04, barrier scale 1, thermal drive 6, transition temperature 0.45, cold/hot mobility 0.5/5 and mobility width 0.08. The thermal diffusivity, cooling and latent ratio are 0.1, 4 and 0.05. Temperature is fixed; the whole interval has zero electrical drive.

The unchanged logit Newton solver uses backward Euler, FP64, its analytic Jacobian, at most 30 iterations and halving line search down to 2^-20. Each step takes its own previous accepted phase as both old state and initial guess. The bounds are 0 and 1 with a strictly interior initial guess. Acceptance is the unscaled defect norm at most 1e-10; its divided-by-dt upper limits are 1.6e-7 and 3.2e-7. No other trajectory or future/reference phase initializes a step. Two fixed step sizes, 0.000625 and 0.0003125, provide 1056 and 2112 steps. No third trajectory, refinement, rescue, electrical solve, reference generation or optimizer update was performed.

Both trajectories and all 1057/2113 internal states were saved and locked before reference access. Numerical qualification passed: the 265-node phase difference RMS is {q['phase_difference_RMS']:.8g} (limit 1e-4), the right-end maximum difference is {q['endpoint_max_absolute']:.8g} (limit 1e-3), and the main heat difference is {q['primary_thermal_difference']:.8g} (limit {q['primary_thermal_difference_limit']:.8g}). These are two-step sensitivity checks at a fixed spatial discretization, not continuum error bounds.

Table S23a. Actual accepted work and maximum unscaled/divided algebraic defects. Main steps and linear solves are distinct. Zero clipping and zero line-search rejections were recorded.

{tab(['Trajectory','Steps','Newton','Linear solves','Max defect','Max defect/dt','Solve s'],work_rows)}
### S23.2 Three residual layers and paired thermal budgets

The algebraic layer is recorded for every internal step. Independently, the common phase residual is D_h0(phi)-F_h(t,phi) on 1057 common nodes, with h0=0.000625. D_h0 is second-order centered in the interior and (-3u0+4u1-u2)/(2h0) and (3uK-4uK-1+uK-2)/(2h0) at the endpoints. Fine values are sampled at nested nodes. The full 3200-cell volume measure and normalized trapezoidal time weights are shared. Conditional arrays have no neural AD residual; no continuous reconstruction is introduced. In particular, RHS minus itself is not used as evidence of phase accuracy.

Table S23b. Common discrete phase-residual mean square and the separate network-AD layer.

{tab(['State','Common phase MS','Network AD layer'],[[label,old_metrics[label]['phase_common_MS'],'B0 endpoint derivatives only' if label=='B0' else 'Not applicable'] for label in ('B0','coarse','fine')])}
The primary heat residual uses the conditional F_h phase rate and the B0 network AD phase rate. The cross-check uses D_h0 for all three states. Both use the same frozen T, AD temperature rate and shared face heat flux. Each convention recomputes its own B0 baseline and tau=max(1.05 J_B0,J_B0+1e-12), without historical pool values. Both are resolved within budget: no step-size pass/fail flip occurs and each fine-step margin exceeds its observed step difference. The conventions agree. This does not replace the original 5% qualification or establish continuous physical truth.

Table S23c. Full-support paired heat budgets. Margin is tau minus candidate J; delta is the absolute coarse/fine difference, not an error bound or confidence interval.

{tab(['Convention','State','B0 J','Candidate J','Upper tau','Margin','Delta'],heatrows)}
![Common residual and heat diagnostics](figures/conditional-residuals.png)

Figure S24. Residual mean squares in time on the common full-cell measure. The phase curve uses an independent time difference. The two heat panels use the separately paired conventions; near overlap of coarse and fine does not prove spatial or continuum convergence.

### S23.3 Endpoint seams and boundary interpretation

All seams compare the conditional a+ or b- evolution to B0 network AD. Velocity is F_h; acceleration is the fixed-phase partial time derivative plus the sparse Jacobian-vector product D_phi F_h F_h. Temperature and mobility time derivatives enter the partial derivative once. No dense 3200 by 3200 Jacobian or reference derivatives are used. The table includes RMS, maximum and the location of that maximum. Scaled RMS multiplies by (b-a)^order; full scaled maxima and vectors are retained in endpoint-seams.csv and endpoint-seam-vectors.npz.

Table S23d. The nonzero endpoint mismatches remain part of the result; no physical seam pass threshold is introduced.

{tab(['State','Side','Order','RMS','Max abs.','Scaled RMS','Max at (x,z)'],seamrows)}
The left input is identical for both step sizes. Accordingly, their left RHS jets agree exactly while the left first-derivative mismatch to B0 has RMS 0.49770263 and maximum 5.2604247. This mismatch cannot be removed by temporal refinement. The endpoint identity Delta phi_t = M epsilon^2 (L_h phi_B0 - L_AD phi_B0) - r_phi,AD has maximum reconstruction discrepancy {r['left_decomposition']['max_absolute']:.4g}. It separates the spatial/boundary implementation difference from the original dynamic defect at that endpoint, without a global causal claim. Nonzero seams do not by themselves rule out a correction with residual tolerances; they also prevent treating this IVP as an exact C2-gated witness.

Table S23e. All boundary sides, including the full bottom. IVP boundary flux is imposed as zero by the discrete operator, whereas B0 quantities are network normal derivatives. These are distinct layers, so the zero is not a superiority claim.

{tab(['Side','Faces','B0 normal MS','B0 max abs.'],[[side,v['face_count'],v['B0_AD_normal_MS'],v['B0_AD_max_absolute']] for side,v in r['boundaries'].items()])}
### S23.4 Locked development-reference analysis

Only after locking and numerical qualification were the saved original 160 by 80 reference values volume-restricted to the same 80 by 40 cells and scored at 265 D nodes. B0 uses the same frozen network's cached values. The ROI is |x|<=0.55 and 0<=z<=0.55. Ephi_D_80 is a raw phase-fraction RMS with separately normalized spatial/time weights, not the historical 160 by 80 W-window error. Both trajectories improve in both scopes by more than their observed step differences; the fine full-domain reduction is {improvement:.4f}%. This is development evidence on an already examined numerical reference, not a new formal A_w, independent confirmation or statistical significance claim.

Table S23f. The required B0 row and both trajectories on the same restricted reference. Gain is E_B0 minus E_IVP.

{tab(['Scope','State','Ephi_D_80','Gain','Delta E'],refrows)}
The support diagnostics show a tradeoff rather than uniform improvement. With the restricted native indicator, fine-step recall falls from 0.974612 to 0.763383 while precision rises from 0.410817 to 0.890215 and symmetric-difference mass decreases. Thresholding after restriction gives the same tradeoff (recall 0.982021 to 0.776968; precision 0.410832 to 0.899253). The ROI agrees. These descriptive D-window measures do not establish the original strict event criteria.

Table S23g. Active-support diagnostics retain both noncommuting reference semantics separately. Masses use normalized D time and the indicated spatial scope; symmetric difference uses fractional overlap for the restricted native indicator. These descriptive values do not replace original event or A_w decisions. The companion CSV includes all predicted, reference, overlap, false-positive and false-negative masses and precision.

{tab(['Scope','State','Reference semantics','Reference mass','Sym. diff. mass','Recall'],active_display)}
![Conditional phase and restricted reference fields](figures/conditional-phase-fields.png)

Figure S25. B0, the fine conditional trajectory and the volume-restricted development reference at the initial, middle and final D times. The common [0,1] phase scale makes the spatial support visible. The fine trajectory is displayed as the smaller-step result, alongside the complete coarse/fine numerical and reference tables. The coarse trajectory remains available in full.

### S23.5 Outcome, actual work and limits

The numerical facts above are VERIFIED. The route output is CONDITIONAL_IVP_SUPPORTS_FURTHER_WITNESS_SEARCH, a SUPPORTED_INTERPRETATION: paired thermal and reference evidence now supports considering a bounded witness search in the original correction family, with the observed seams explicitly addressed. The original C2-family feasibility is UNKNOWN. This is the sole follow-on research recommendation; it requires a separate approved design. No A+, new optimization or independent confirmation has started.

Network queries took {cache['seconds']:.3f} s; the two phase solves took {sum(lock['trajectories'][k]['seconds'] for k in ('coarse','fine')):.3f} s. The query/propagation process took {complete['seconds']:.3f} s, followed by {r['seconds']:.3f} s numerical evaluation and {r['reference']['seconds']:.3f} s reference evaluation. These measured stages are not an equal-work speedup comparison. Work was {lock['total_accepted_main_steps']} main steps, {sum(lock['trajectories'][k]['counts']['newton_iterations'] for k in ('coarse','fine'))} Newton iterations/linear solves and {cache['work']['head_query_batches']} coordinate-query batches. The cache records separate temperature/phase head positions, first/second derivatives, shared-face and boundary queries. Model identity is unchanged, with zero training, electrical forwards, electrical adjoints or reference generation.

The instance was a V100 32 GB with a six-core CPU quota and 25 GiB container memory; four CPU threads and at most 1024 coordinates per query were used. The sampled process RSS peak was {complete['resources']['peak_rss_bytes']/1024**3:.3f} GiB. The resource guards did not trigger. GPU peak allocation was not persisted and no value is inferred. The first deployment preflight omitted one original contract-identity fixture; it failed before any model query or scientific step. The unchanged fixture was included, six targeted checks and model loading passed, and the same frozen task ran once. Both preflight records remain available.

Results were recovered and archive integrity verified before shutdown was requested at {closure['shutdown_requested_utc']}. The shutdown command returned zero; subsequent SSH connection refusal was recorded at closure {closure['closed_utc']}. A later local saved-array reconstruction reproduced the defects, exports, common residuals, both heat conventions and reference RMS scores without another model query or propagation. Complete runtime source identities, B0 path, physical coefficients, environment, work counters, numerical vectors and shutdown evidence accompany the run. P02 method value, strict two-cycle use, material validation and P03 full-array external access remain open.

'''
source=HERE/'source/supplement.md';text=source.read_text(encoding='utf-8');start=text.index('## S23. Fixed-temperature conditional phase evolution');end=text.index('## References',start);source.write_text(text[:start]+body+text[end:],encoding='utf-8')
source=HERE/'source/manuscript.md';text=source.read_text(encoding='utf-8');note='A supplementary fixed-temperature conditional evolution'
if note not in text:
    marker='![Scalar objective and separate physical components]'
    paragraph=f'''A supplementary fixed-temperature conditional evolution passes the two-step numerical checks and both paired thermal budgets. On the same 80 by 40 D-only development measure, phase RMS falls from {err['full']['B0']['Ephi_D_80']:.6f} to {err['full']['fine']['Ephi_D_80']:.6f}, with the same direction in the original ROI. Its endpoint derivative and value mismatches remain substantial, so the result supports considering a bounded search within the original correction family without establishing that family's feasibility or a neural-specific increment (Supplement S23).

'''
    text=text.replace(marker,paragraph+marker)
source.write_text(text,encoding='utf-8')
(HERE/'conditional-evolution-report.md').write_text('# Conditional evolution report\n\nTask '+cfg['task_id']+'\n\n'+body,encoding='utf-8')
pmap=HERE/'claim_evidence_matrix.md';text=pmap.read_text(encoding='utf-8').replace('pending actual bounded run; no claim during preparation','[conditional report](conditional-evolution-report.md), [locked result](../../outputs/runs/20260925-fixed-temperature-phase-probe/result.json), [reconstruction check](../../outputs/runs/20260925-fixed-temperature-phase-probe/saved-array-verification.json); supplementary development evidence, no original-family certification');pmap.write_text(text,encoding='utf-8')
print(json.dumps(dict(status=r['status'],saved_array_verification=True,full_phase_RMS_reduction_percent=improvement),indent=2))
