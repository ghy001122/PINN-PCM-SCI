"""Independent local handoff: python -I recompute.py --scope all.

All inputs resolve below this script. An audit hook makes the original checkout
inaccessible. Saved residual aggregation is explicitly not new neural AD.
"""
from pathlib import Path
import argparse,importlib.util,json,os,runpy,subprocess,sys,time,shutil,uuid

ROOT=Path(__file__).resolve().parent
sys.dont_write_bytecode=True
sys.path.insert(0,str(ROOT))
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def save(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
INFO=read(ROOT/'handoff.json')
FORBIDDEN=Path(INFO['original_repository']).resolve()
def audit(event,args):
    if event in ('open','os.listdir','os.scandir','os.chdir') and args and isinstance(args[0],(str,bytes,os.PathLike)):
        p=Path(os.fsdecode(args[0])).resolve()
        if p.is_relative_to(FORBIDDEN):raise PermissionError('Original repository is inaccessible during handoff recomputation: '+str(p))
sys.addaudithook(audit)

def validate():
    missing=[]
    for name in read(ROOT/'input-inventory.json'):
        p=(ROOT/name).resolve()
        if Path(name).is_absolute() or not p.is_relative_to(ROOT):raise ValueError('Invalid package input path '+name)
        if not p.is_file():missing.append(name)
    if missing:raise FileNotFoundError('Missing fixed input(s); no fallback or regeneration: '+', '.join(missing))
    try:
        (FORBIDDEN/'AGENTS.md').open('rb')
    except PermissionError:denied=True
    else:raise AssertionError('Repository denial probe failed')
    return dict(all_required_inputs_present=True,original_repository_access_denied=denied)

def fresh_copy(validate_only=False):
    """Create a clean execution root using immutable local input hard links.

    Existing verification outputs never substitute for a requested fresh run.
    All executable adapters are copied; no link points outside the package.
    """
    validate();target=ROOT/'executions'/('fresh-'+uuid.uuid4().hex[:12]);target.mkdir(parents=True)
    for rel in read(ROOT/'input-inventory.json'):
        source=(ROOT/rel).resolve();dest=target/rel
        dest.parent.mkdir(parents=True,exist_ok=True);os.link(source,dest)
    for name in ('handoff.json','input-inventory.json'):
        shutil.copy2(ROOT/name,target/name)
    for p in [*ROOT.glob('*.py'),*(ROOT/'pinn_pcm_sci').glob('*.py')]:
        dest=target/p.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True)
        if dest.exists():
            # Break the hard link before copying a current storage/I/O adapter.
            if not dest.resolve().is_relative_to(target.resolve()):raise ValueError('fresh containment')
            dest.unlink()
        shutil.copy2(p,dest)
    print('FRESH_EXECUTION_ROOT',target,flush=True)
    command=[sys.executable,'-I','-u',str(target/'recompute.py')]
    command+=['--validate-only'] if validate_only else ['--scope','all']
    subprocess.run(command,cwd=target,check=True)

def install_storage():
    from array_storage import arrays
    original=importlib.util.spec_from_file_location
    class Loader:
        def __init__(self,wrapped):self.wrapped=wrapped
        def create_module(self,spec):return self.wrapped.create_module(spec)
        def exec_module(self,module):self.wrapped.exec_module(module);module.arrays=arrays
    def spec(name,location,*args,**kw):
        value=original(name,location,*args,**kw)
        if Path(location).name=='rescore.py':value.loader=Loader(value.loader)
        return value
    importlib.util.spec_from_file_location=spec

def checker():
    p=ROOT/'outputs/submission-rescore-20260921/portable/rescore.py'
    spec=importlib.util.spec_from_file_location('exact_frozen_compare',p)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m.compare_saved

def residuals():
    import numpy as np
    d=ROOT/'outputs/runs/20260924-observation-preserving-phase/diagnostic-20260925'
    compare=checker();records={};checked=0
    for pool in ('fixed-training','independent-D','common-128','common-256','spatial-256'):
        expected=read(d/(pool+'.json'))['summary'];rows=[]
        with np.load(d/(pool+'-traces.npz'),allow_pickle=False) as f:
            w=f['weight']
            for row in expected:
                state=row['state'];actual={key:float(w@np.mean(f[state+'/'+field]**2,axis=1))
                    for key,field in (('phase_raw','rphi'),('thermal_raw','rT'))}
                # Four equal-size side samples; original BC is sum(side means)/13.
                normal=f[state+'/normal'];assert normal.shape[1]%4==0
                actual['phase_BC']=float(w@(normal.reshape(len(w),4,-1)**2).mean(2).sum(1)/13)
                actual['phase_weighted']=actual['phase_raw']/75
                actual['thermal_weighted']=actual['thermal_raw']/48
                actual['boundary_weighted']=5*actual['phase_BC']
                actual['H']=sum(actual[k] for k in ('phase_weighted','thermal_weighted','boundary_weighted'))
                actual['original_variable_objective']=.1/read(d.parent/'calibration.json')['bE']*.66/2.5*actual['H']
                for key,val in actual.items():checked+=compare(val,row[key],pool+'/'+state+'/'+key)
                rows.append(dict(state=state,**actual))
        records[pool]=rows
    for order in (8,16):
        name='thermal-'+str(order);expected=read(d/(name+'.json'))
        with np.load(d/(name+'-traces.npz'),allow_pickle=False) as f:
            L=.66;w=f['weights'];C=.05*(f['phi_base_right']-f['phi_base_left']-L*(w@f['forcing']))
            actual=dict(C=C.tolist(),mean_raw_square_lower_bound=float(np.mean((C/L)**2)),
                base_mean_raw_square=float(w@np.mean(f['base_thermal_residual']**2,axis=1)))
            for key,val in actual.items():checked+=compare(val,expected[key],name+'/'+key)
            records[name]=actual
    return dict(status='PASS_SAVED_RESIDUAL_REAGGREGATION',checked_values=checked,records=records,
                neural_AD_recomputed=False,capability='saved residual records only; not a fresh physics audit')

def s23_extras(run,compare):
    import csv,numpy as np
    from pinn_pcm_sci.phk_benchmark import PhkGrid
    from pinn_pcm_sci.phk_v23_conditional_phase import phase_rhs,time_weights
    p=read(run/'physics.json');g=PhkGrid.build(nx=80,nz=40,**{k:p[k] for k in ('x_min','x_max','z_min','z_max')})
    T=np.load(run/'cache/temperature_fine.npy',mmap_mode='r');count=0;steps={}
    for label,dt,stride in [('coarse',.000625,2),('fine',.0003125,1)]:
        phi=np.load(run/label/'phase.npy',mmap_mode='r')
        rows=list(csv.DictReader((run/label/'steps.csv').open(encoding='utf-8')));values=[]
        for k,row in enumerate(rows,1):
            defect=phi[k]-phi[k-1]-dt*phase_rhs(phi[k],T[k*stride],g,p)
            val=float(np.max(abs(defect)));values.append(val)
            count+=compare(val,float(row['residual_inf']),label+'/step/'+str(k))
            if val>1e-10:raise AssertionError('Original algebraic acceptance failed on saved arrays')
        steps[label]=dict(checked_steps=len(values),max_residual_inf=max(values),max_residual_rate=max(values)/dt)
    grid=np.load(run/'cache/grid.npz');w=time_weights(np.load(run/'cache/time_common.npy')[::4]);vol=grid['volumes']
    fields={'B0':np.load(run/'cache/B0_phase.npy',mmap_mode='r')[::4],
            'coarse':np.load(run/'coarse/phase.npy',mmap_mode='r')[::4],
            'fine':np.load(run/'fine/phase.npy',mmap_mode='r')[::8]}
    truth=np.load(run/'reference-diagnostic-265.npz');expected=list(csv.DictReader((run/'expected/active-support-diagnostics.csv').open(encoding='utf-8')));records=[]
    for row in expected:
        mask=np.ones(len(vol),bool) if row['scope']=='full' else ((abs(grid['x'])<=.55)&(grid['z']>=0)&(grid['z']<=.55))
        v=vol[mask]/sum(vol[mask]);pred=(fields[row['state']][:,mask]>=.5).astype(float)
        key='restricted_native_indicator' if row['reference_semantics']=='restricted_native_indicator' else 'threshold_after_restriction'
        a=truth[key][:,mask];pm=float(w@(pred@v));am=float(w@(a@v));tp=float(w@((pred*a)@v));fp=pm-tp;fn=am-tp
        actual=dict(predicted_mass=pm,reference_mass=am,true_positive_mass=tp,false_positive_mass=fp,false_negative_mass=fn,
            symmetric_difference_mass=fp+fn,recall=tp/am if am else None,precision=tp/pm if pm else None)
        count+=compare(actual,{k:float(row[k]) for k in actual},'active/'+row['scope']+'/'+row['state']+'/'+key)
        records.append(dict(scope=row['scope'],state=row['state'],reference_semantics=key,**actual))
    return dict(checked_values=count,algebraic=steps,active_support=records,trajectory_steps_executed=0)

def run_scope(scope):
    checks=validate();install_storage();archive=ROOT/'outputs/submission-rescore-20260921';compare=checker()
    out=ROOT/'recomputed'/scope
    if out.exists():raise FileExistsError('Completed/partial output exists; review before repeating: '+str(out))
    started=time.perf_counter()
    if scope in ('core','extension'):
        sys.argv=['scope_rescore.py','--root',str(archive),'--scope',scope,'--out','independent-'+scope]
        runpy.run_path(str(archive/'portable/scope_rescore.py'),run_name='__main__')
        r=read(archive/('independent-'+scope)/'results.json');result={k:r[k] for k in ('status','record_count','comparison')}
    elif scope in ('b1','s21','s22'):
        if scope=='b1':
            from pinn_pcm_sci import phk_v23_b1_evaluate as m
            run=ROOT/'outputs/runs/20260921-b1-second-cycle-phase-gap'
            sys.argv=['b1','--run',str(run),'--archive',str(archive),'--out',str(run/'scoring')];m.main()
            keys=('records','windows','comparisons','scientific_route')
        elif scope=='s21':
            from pinn_pcm_sci import phk_v23_phase_moments_evaluate as m
            run=ROOT/'outputs/runs/20260923-relative-phase-moments'
            sys.argv=['s21','--run',str(run),'--archive',str(archive)];m.main()
            keys=('records','windows','comparisons')
        else:
            from pinn_pcm_sci import phk_v23_observation_preserving_phase_evaluate as m
            from array_storage import arrays
            m.mapped_arrays=arrays;m.score();run=m.RUN
            keys=('records','windows','pairs','decomposition','invariance')
        actual=read(run/'scoring/results.json');expected=read(run/'expected/results.json')
        count=compare({k:actual[k] for k in keys},{k:expected[k] for k in keys},scope)
        result=dict(status='PASS_FROZEN_ARRAY_RESCORING',checked_values=count,keys=list(keys))
    elif scope=='s23':
        from pinn_pcm_sci import phk_v23_conditional_phase_evaluate as m
        run=ROOT/'outputs/runs/20260925-fixed-temperature-phase-probe';cfg=read(run/'frozen-config.json')
        m.numerical(cfg,run);m.score_reference(cfg,run);count=0
        fields={'common-metrics.json':('state_metrics',),
            'numerical-evaluation.json':('numerical_qualification_passed','qualification','thermal','seams','boundaries','left_step_difference','left_decomposition'),
            'reference-evaluation.json':('records','grid','interval','time_count','formal_A_w','formal_ood'),
            'result.json':('status','original_C2_family_feasibility')}
        for name,keys in fields.items():
            a=read(run/name);b=read(run/'expected'/name)
            count+=compare({k:a[k] for k in keys},{k:b[k] for k in keys},scope+'/'+name)
        result=dict(status='PASS_SAVED_S23_ARRAY_REBUILD',checked_values=count,trajectory_steps=0,
                    neural_AD_recomputed=False,cached_AD_values_used=True,additional=s23_extras(run,compare))
    elif scope=='residuals':result=residuals()
    elif scope=='vo2':
        from pinn_pcm_sci.vo2_author_reproduction import CASES,compare as author_compare
        run=ROOT/'outputs/runs/20260926-core-revision-vo2-bridge/vo2'
        actual=[author_compare(c,run) for c in CASES]
        expected=read(run/'report.json')['cases']
        result=dict(status='PASS_SAVED_AUTHOR_MODEL_REANALYSIS',checked_values=compare(actual,expected,'vo2'),
            system_steps_executed=0,case_count=5,step_sizes=[1e-9,5e-10],quantitative_experimental_reproduction=False)
    elif scope=='fcov':
        import score_fcov
        sys.argv=['score_fcov','--out','fcov-recomputed','--expected','outputs/runs/20260926-core-revision-vo2-bridge/fcov-scoring/results.json']
        score_fcov.main();r=read(ROOT/'fcov-recomputed/results.json')
        result=dict(status='PASS_F_COV_ARRAY_RESCORING',record_count=12,verification=r['verification'])
    else:raise ValueError(scope)
    result.update(checks,seconds=time.perf_counter()-started,python=sys.version,isolated_python=bool(sys.flags.isolated),
        rtol=2e-10,atol=2e-12,booleans='exact',checkpoint_inference_executed=False)
    save(out/'verification.json',result);print(json.dumps({'scope':scope,**{k:v for k,v in result.items() if k!='records'}}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--scope',choices=('all','core','extension','b1','s21','s22','s23','residuals','vo2','fcov'),default='all');p.add_argument('--validate-only',action='store_true');p.add_argument('--fresh',action='store_true');a=p.parse_args()
    if a.fresh:fresh_copy(a.validate_only)
    elif a.validate_only:print(json.dumps(validate()))
    elif a.scope!='all':run_scope(a.scope)
    else:
        scopes=('core','extension','b1','s21','s22','s23','residuals','vo2')
        if (ROOT/'outputs/runs/20260926-core-revision-vo2-bridge/fcov-scoring/results.json').is_file():scopes+=('fcov',)
        for scope in scopes:
            q=ROOT/'recomputed'/scope/'verification.json'
            if q.exists():print('ALREADY_VERIFIED',scope,flush=True);continue
            subprocess.run([sys.executable,'-I','-u',str(Path(__file__)),'--scope',scope],cwd=ROOT,check=True)
        save(ROOT/'independent-verification.json',dict(status='COMPLETE_FOR_INCLUDED_INPUTS',scopes={s:read(ROOT/'recomputed'/s/'verification.json')
            for s in scopes},external_access=False,P03='OPEN'))
