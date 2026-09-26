"""Integrate locked coverage scores, preserving every original comparison."""
from pathlib import Path
import csv,json,re,importlib.util
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
RUN=ROOT/'outputs/runs/20260926-core-revision-vo2-bridge'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def table(head,rows):
    def fmt(x):return f'{x:.7g}' if isinstance(x,float) else str(x)
    return '\n'.join(['| '+' | '.join(head)+' |','| '+' | '.join(['---']*len(head))+' |']+['| '+' | '.join(fmt(x) for x in row)+' |' for row in rows])
def csv_save(p,rows):
    with p.open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def main():
    score=read(RUN/'fcov-scoring/results.json');assert score['record_count']==12
    old=read(ROOT/'outputs/submission-rescore-20260921/primary-rescore/results.json')
    rows=[];decision=[];effects=[];counts={k:0 for k in ('E_vs_F_cov_A','E_vs_F_cov_B','F_cov_vs_F_A','F_cov_vs_F_B')}
    for ref in ('old','refined','spatial'):
        for level in ('coarse','fine'):
            for seed in (29,43):
                pairs=score['comparisons'][ref][level][str(seed)]
                decision.append(dict(reference=ref,reader=level,seed=seed,**{name+'_'+rule:pair[rule]['passed'] for name,pair in pairs.items() for rule in ('A','B')}))
                for name in counts:counts[name]+=int(decision[-1][name])
                for role in ('E','F','F_cov'):
                    rec=(score if role=='F_cov' else old)['records'][ref][level][f'shorter/{seed}/{role}']
                    rows.append(dict(reference=ref,reader=level,seed=seed,role=role,**rec['metrics'],strict_device_pass=rec['strict_device_pass']))
                for pair,metrics in score['effects'][ref][level][str(seed)].items():
                    for metric,value in metrics.items():effects.append(dict(reference=ref,reader=level,seed=seed,comparison=pair,metric=metric,**value))
    counts['F_cov_strict_passes']=sum(int(r['strict_device_pass']) for r in rows if r['role']=='F_cov')
    csv_save(HERE/'tables/fcov-all-metrics.csv',rows);csv_save(HERE/'tables/fcov-all-decisions.csv',decision);csv_save(HERE/'tables/fcov-all-effects.csv',effects)
    view=[[r[k] for k in ('reference','reader','seed','role','S','Ephi','EI','power_trace_NRMSE','local_joule_NRMSE','strict_device_pass')] for r in rows]
    (HERE/'tables/fcov-metrics.md').write_text(table(['Reference','Reader','Seed','State','Set error S','Phase RMS','I NRMSE','P NRMSE','Local q NRMSE','Strict'],view)+'\n',encoding='utf-8')
    view=[[r[k] for k in ('reference','reader','seed','E_vs_F_cov_A','E_vs_F_cov_B','F_cov_vs_F_A','F_cov_vs_F_B')] for r in decision]
    (HERE/'tables/fcov-decisions.md').write_text(table(['Reference','Reader','Seed','E/Fcov A','E/Fcov B','Fcov/F A','Fcov/F B'],view)+'\n',encoding='utf-8')
    costs=[]
    for seed in (29,43):
        base=RUN/f'fcov/seed-{seed}';term=read(base/'F_cov/terminal.json');prof=read(base/'zero-update-profile.json')
        costs.append(dict(seed=seed,status=term['status'],**term['progress'],training_seconds=term['current_session_seconds'],
            termination=term['lbfgs']['termination'],profile_seconds=prof['seconds'],profile_GPU_peak_GiB=prof['gpu_peak_allocated']/2**30,
            full_grid_network_evaluations=term['statistics']['explicit_work']['full_grid_network_evaluations'],
            readout_electrical_solves=sum(read(base/f'F_cov/{level}/readers-complete.json')['forward_solves'] for level in ('coarse','fine')),
            discarded_readout_solve_upper_bound=sum(read(base/f'F_cov/{level}/readers-complete.json').get('discarded_inflight_upper_bound',0) for level in ('coarse','fine'))))
    csv_save(HERE/'tables/fcov-work.csv',costs)
    (HERE/'tables/fcov-work.md').write_text(table(['Seed','Adam updates','Full evaluations','Accepted L-BFGS steps','Training seconds','Readout solves'],
        [[c[k] for k in ('seed','adam_updates','lbfgs_charged','lbfgs_accepted','training_seconds','readout_electrical_solves')] for c in costs])+'\n',encoding='utf-8')
    if counts['E_vs_F_cov_B']==12:direction='retained in all twelve sensitivity conditions'
    elif counts['E_vs_F_cov_B']==0:direction='not retained in any of the twelve sensitivity conditions'
    else:direction='condition-dependent'
    conclusion=f"Against the mixed-measure coverage control F_cov, E satisfies the original whole-history A/B criteria in {counts['E_vs_F_cov_A']}/12 and {counts['E_vs_F_cov_B']}/12 reference/reader/initialization conditions. The device-criterion advantage is {direction}. F_cov satisfies A/B against its historical F in {counts['F_cov_vs_F_A']}/12 and {counts['F_cov_vs_F_B']}/12 conditions, and satisfies the unchanged strict rule in {counts['F_cov_strict_passes']}/12. These are twelve sensitivity records for two new continuations, not twelve independent runs."
    def span(seed,metric,sign=1):
        values=[sign*100*score['effects'][ref][level][str(seed)]['F_cov_vs_F'][metric]['relative_error_reduction']
                for ref in ('old','refined','spatial') for level in ('coarse','fine')]
        return f'{min(values):.2f}-{max(values):.2f}%'
    tradeoff=(f"F_cov nevertheless reduces current and power error relative to F by {span(29,'EI')} and {span(29,'power_trace_NRMSE')} for seed 29, "
        f"and {span(43,'EI')} and {span(43,'power_trace_NRMSE')} for seed 43. Its phase-set error S increases by {span(29,'S',-1)} and {span(43,'S',-1)}, respectively, "
        "violating the set-error noninferiority component in every condition. Thus the failed complete criteria coexist with continuous port improvements.")
    local_tradeoff=(f"The phase RMS change also depends on initialization: seed 29 improves by {span(29,'Ephi')}, while seed 43 worsens by {span(43,'Ephi',-1)}. "
        f"Local Joule-density error worsens by {span(29,'local_joule_NRMSE',-1)} for seed 29 and improves by {span(43,'local_joule_NRMSE')} for seed 43. "
        "All ranges use the six reference/reader conditions of the same endpoint, without combining training histories.")
    paragraphs='''### 4.3 Mixed-measure coverage enhancement

Two additional soft-PINN continuations retain the short-interval full-label parents, observation streams, non-electrical objectives, calibration and soft-network Joule source. Their electrical penalty replaces the original term with equal normalized physical-time and powered-observation-time measures over all 3200 cells. This changes spatial coverage and temporal measure together; it is not a pure coverage or isolated VJP experiment.

'''+conclusion+'\n\n'+tradeoff+''' Continuous metrics, all criterion failures and original network readouts are retained in Supplement S24. The result tests robustness to this stronger soft configuration; initialization, active-variable and enforcement differences still prevent single-mechanism attribution.

'''
    p=HERE/'source/manuscript.md';text=p.read_text(encoding='utf-8')
    abstract_sentence=f" Against an additional soft control with mixed-measure coverage enhancement, E meets the complete device criterion in {counts['E_vs_F_cov_B']}/12 shorter-protocol sensitivity conditions on the same two parents."
    text=re.sub(r' Against an additional soft control with mixed-measure coverage enhancement, E meets the complete device criterion in \d+/12 shorter-protocol sensitivity conditions on the same two parents\.','',text)
    text=text.replace('Strong interpolation supplies a ranking counterexample,',abstract_sentence.strip()+' Strong interpolation supplies a ranking counterexample,',1)
    text=re.sub(r'### 4\.3 Mixed-measure coverage enhancement.*?(?=## 5\.)','',text,flags=re.S)
    text=text.replace('## 5. Dynamic residual increments and failure diagnostics',paragraphs+'## 5. Dynamic residual increments and failure diagnostics')
    marker='Strong interpolation supplies a continuous reversal and a reader-sensitive advantage decision, limiting the scope of that benefit.'
    text=re.sub(r' The stronger mixed-measure F_cov comparison retains the E device criterion in \d+/12 shorter-protocol sensitivity conditions; this outcome further bounds the configuration-level claim\.','',text)
    text=text.replace(marker,marker+f" The stronger mixed-measure F_cov comparison retains the E device criterion in {counts['E_vs_F_cov_B']}/12 shorter-protocol sensitivity conditions; this outcome further bounds the configuration-level claim.")
    p.write_text(text,encoding='utf-8')
    section=r'''## S24. Mixed-measure coverage enhancement

### S24.1 Frozen target and information boundary

F_cov starts from the original short-interval full-label observation-only parents for seeds 29 and 43. It does not start from E or from the later B1 phase-gap parent. The original network, observations, calibration a/b, lambda schedule, soft-network Joule source and all non-electrical losses remain fixed. At each time, ell_e is the all-3200-cell volume mean of the squared scaled electrical residual. The two normalized time measures give

$$ J_{e,cov}=\frac{1}{2}\int\ell_e\,d\rho_{physics}+\frac{1}{2}\sum_{k\in\mathcal T_{powered}}p_k\ell_e(t_k). $$

$$ L_{cov}=L_{original\ without\ electric}+\frac{\lambda\eta}{3b}J_{e,cov},\qquad\eta=1. $$

The frozen calibration pairs (a,b) are (9.046665007474575e-5, 0.4278354366241891) for seed 29 and (8.733967722147966e-5, 0.5222233032660305) for seed 43. The new term replaces the original electrical term once; it is not added on top of it. Powered-observation probabilities are the voltage-observation time marginal restricted and renormalized to driven times. Repeated times merge their weights. Adam draws four times with replacement using a separate stream 960000+seed and estimates that component by their mean; multiplicities count, with no extra probability or inverse-probability factor. Original observation, physical, boundary and initial-condition streams do not change. All group gradients accumulate before one original norm-10 clip and one update.

The complete L-BFGS support is the union of 32 original fixed physical times and 34 powered observation times. It uses full gradients and the original strong-Wolfe rule, with at most 300 full evaluations after 1500 Adam updates per parent. Both parents passed a zero-update full-objective/gradient measurement. Focused checks confirmed normalization, repeated-draw counting, unchanged non-electrical gradients at shared parameters and batches, unchanged original random streams, and accepted-parameter/optimizer-history recovery. Saved arrays are read only after both endpoints lock; references never enter this training entry or its deployment inputs. Reference results were already used in the broader development history, so no blanket reference-blind claim is made.

### S24.2 Complete endpoint comparison

'''+conclusion+'\n\n'+tradeoff+'\n\n'+local_tradeoff+r'''

Table S24a. E, original F and F_cov on each same reference and reader. NRMSE definitions and denominators are unchanged. Complete errors, cycles, normalizers and exact comparisons accompany the compact table; adverse outcomes are not omitted.

{{TABLE:fcov-metrics}}

Table S24b. Original A/B decisions. F_cov/E, F_cov/B_E and F_cov/D_E directions are also retained in the complete CSV/JSON; no practical threshold is relaxed.

{{TABLE:fcov-decisions}}

This is mixed-measure coverage enhancement. A gain, loss or mixed result does not identify coverage as the sole cause of the original E/F difference. It also does not erase the B_E counterexample, the matched D_E limitation, B1 failures or subsequent phase-correction outcomes. Complete network and repaired readouts each retain 1001 times; the twelve formal rows above use the common repaired reader only. Network arrays remain a separate saved readout, not another independent initialization.

### S24.3 Work, interruption and reproducibility

Table S24c. Actual work; full evaluations include charged line-search trials. Different costs do not establish a speedup.

{{TABLE:fcov-work}}

Accepted state files retain parameters, complete optimizer history, random streams, fixed-support identity and cumulative update/evaluation counters. Budget exhaustion at a trial rolls back both parameters and optimizer to the last accepted state; charged evaluations are retained. Resource interruption, numerical failure, budget exhaustion and optimizer convergence are separately named. No incomplete F_cov was admitted to these comparisons.

The first remote attempt omitted a memory-monitoring dependency and stopped after one zero-update full gradient, before any scientific update. It was replaced by native system measurements; the failed attempt and its cost remain archived. The same parents and budgets continued after the user restarted the instance. Native monitoring enforces the 12 GiB RSS, 16 GiB allocation and 4 GiB available-memory limits. Runtime source identities, environment, zero-update profiles, accepted-state records, complete costs and recovery/shutdown evidence accompany the run. The final common readout requires 1112 committed powered electrical solves for the two objects and two grids; no extra training arm, reference generation or new pilot is included.

After both training endpoints were locked, the last fine-grid readout exited without its completion marker. The persistent volume was full; container memory records showed no OOM kill, and the exact exit signal was unavailable. Already completed numerical caches were released only after exact equality with their retained NPZ arrays. The missing readout resumed at its committed time boundary with unchanged checkpoint weights, no optimizer call and at most one discarded in-flight powered solve, recorded separately from the 1112 committed solves. Short SSH-monitor disconnections did not restart scientific computation. Recovery and verified shutdown followed the completed readout.

'''
    for seed in (29,43):
        section+=f'![Phase, temperature and local Joule density for seed {seed}](figures/fcov-physics-{seed}.png)\n\nFigure S{26 if seed==29 else 27}. Saved fields at t=1.28 for the original reference, E, F and F_cov, on the same 160 by 80 grid. Each row uses a common scale across states. The selected time was fixed before F_cov scores; it is a spatial diagnostic, not a separate evaluation criterion.\n\n'
    p=HERE/'source/supplement.md';text=p.read_text(encoding='utf-8')
    text=re.sub(r'## S24\. Mixed-measure coverage enhancement.*?(?=## References)','',text,flags=re.S)
    text=text.replace('## References',section+'## References');p.write_text(text,encoding='utf-8')
    (HERE/'coverage-report.md').write_text('# 混合测度下的覆盖增强\n\nVERIFIED: '+conclusion+'\n\n'+tradeoff+'\n\n'+local_tradeoff+'\n\n'+table(['Seed','Adam','Complete evaluations','Termination'],[[c['seed'],c['adam_updates'],c['lbfgs_charged'],c['termination']] for c in costs])+'\n\n完整合同与表格见补充 S24；数值事实为 VERIFIED，配置鲁棒性解释为 SUPPORTED_INTERPRETATION。P02、严格双周期及材料／泛化主张仍未闭合。\n',encoding='utf-8')
    (HERE/'coverage-summary.json').write_text(json.dumps(dict(counts=counts,conclusion=conclusion,costs=costs),indent=2)+'\n')
    m=read(ROOT/'outputs/submission-rescore-20260921/manifest.json');archive=ROOT/'outputs/submission-rescore-20260921'
    spec=importlib.util.spec_from_file_location('coverage_plot_reader',archive/'portable/readout_rescore.py')
    reader=importlib.util.module_from_spec(spec);spec.loader.exec_module(reader)
    grid=reader.s.geometry(archive,m);physics=reader.s.Physics(protocol='shorter',**m['protocols']['shorter']['physics'])
    for seed in (29,43):
        paths=[archive/m['protocols']['shorter']['references']['old']]+[archive/next(x for x in m['objects'] if x['id']==f'shorter/{seed}/{role}')['prediction'] for role in ('E','F')]+[RUN/f'fcov/seed-{seed}/F_cov/coarse/projected/prediction.npz']
        snapshots=[]
        for path in paths:
            with np.load(path,allow_pickle=False) as f:
                k=int(np.argmin(abs(f['time']-1.28)));assert abs(f['time'][k]-1.28)<1e-12
                small={key:f[key][k:k+1] for key in ('potential','temperature','phase')};small['time']=f['time'][k:k+1]
                q=f['joule_density'][k] if 'joule_density' in f.files else reader.s.deposition(small,grid,physics)[0]
                snapshots.append(dict(phase=small['phase'][0].reshape(80,160),temperature=small['temperature'][0].reshape(80,160),joule_density=q.reshape(80,160)))
        fig,axes=plt.subplots(3,4,figsize=(10,5.6),layout='constrained')
        for row,key in enumerate(('phase','temperature','joule_density')):
            lo=min(0.,min(float(s[key].min()) for s in snapshots)) if key=='temperature' else 0.
            hi=1. if key=='phase' else max(float(s[key].max()) for s in snapshots)
            for col,snap in enumerate(snapshots):
                ax=axes[row,col];im=ax.imshow(snap[key],origin='lower',extent=(-1,1,0,1),vmin=lo,vmax=hi,cmap='viridis',aspect='equal')
                if row==0:ax.set_title(('Reference','E','F','F_cov')[col])
                if col==0:ax.set_ylabel(key+' / z')
                if row==2:ax.set_xlabel('x')
            fig.colorbar(im,ax=axes[row,:].tolist(),shrink=.85)
        fig.savefig(HERE/f'figures/fcov-physics-{seed}.png',dpi=180);plt.close(fig)
    print(json.dumps(dict(counts=counts,conclusion=conclusion)),flush=True)
if __name__=='__main__':main()
