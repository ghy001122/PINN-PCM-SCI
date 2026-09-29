"""Frozen discrete joint reconstruction; training inputs contain no source states.

The physical loss is evaluated on the complete native 0.5 ns axis. Custom
history and RC VJPs preserve all selected-branch history dependencies.
"""
from __future__ import annotations
import copy,json,os,time
from pathlib import Path
from datetime import datetime,timezone
import numpy as np
import torch
from scipy.interpolate import BSpline
from .kinetics_clock import make_mlp
from .vo2_author_reproduction import P
from .vo2_joint_history import resistance_from_temperature,replay_with_history
from .vo2_joint_rc import rc_voltage,rc_forward
from .vo2_joint_lbfgs import accepted_lbfgs

ROOT=Path(__file__).resolve().parents[1]
PAPER=ROOT/'paper/paper_revision_20260929_72h'
RUN=ROOT/'outputs/runs/20260929-joint-reconstruction'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def save(p,x):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(x,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
def stamp():return datetime.now(timezone.utc).isoformat()
def cpu(x):
    if torch.is_tensor(x):return x.detach().cpu().clone()
    if isinstance(x,dict):return {k:cpu(v) for k,v in x.items()}
    if isinstance(x,list):return [cpu(v) for v in x]
    if isinstance(x,tuple):return tuple(cpu(v) for v in x)
    return copy.deepcopy(x)
def atomic_pt(path,x):
    temporary=Path(str(path)+'.tmp');torch.save(cpu(x),temporary);temporary.replace(path)
def trap(t):
    h=np.diff(t);return np.r_[h[0]/2,(h[:-1]+h[1:])/2,h[-1]/2]/(t[-1]-t[0])

class JointModel(torch.nn.Module):
    def __init__(self,role,seed,time_s,observation_time,device):
        super().__init__();self.role=role
        torch.manual_seed(seed)
        self.register_buffer('gate',torch.as_tensor(time_s/time_s[-1],dtype=torch.float64,device=device)[:,None])
        if role in ('N_dyn','F_dyn'):
            self.temperature=make_mlp(1,2,hidden_width=64,hidden_layers=4).double().to(device)
            torch.nn.init.zeros_(self.temperature[-1].weight);torch.nn.init.zeros_(self.temperature[-1].bias)
            if role=='F_dyn':
                self.voltage=make_mlp(1,2,hidden_width=64,hidden_layers=4).double().to(device)
                torch.nn.init.zeros_(self.voltage[-1].weight);torch.nn.init.zeros_(self.voltage[-1].bias)
        elif role=='S_dyn':
            nodes=np.sort(np.r_[observation_time,(observation_time[:-1]+observation_time[1:])/2])
            knots=np.r_[np.repeat(nodes[0],3),nodes,np.repeat(nodes[-1],3)]
            design=BSpline.design_matrix(time_s,knots,3,extrapolate=False).tocsr()
            assert np.all(np.diff(design.indptr)==4)
            self.register_buffer('basis_columns',torch.tensor(design.indices.reshape(-1,4).copy(),dtype=torch.long,device=device))
            self.register_buffer('basis_weights',torch.tensor(design.data.reshape(-1,4).copy(),dtype=torch.float64,device=device))
            self.coefficients=torch.nn.Parameter(torch.zeros((design.shape[1],2),dtype=torch.float64,device=device))
        else:raise ValueError(role)
    def corrections(self):
        if self.role=='S_dyn':h=(self.coefficients[self.basis_columns]*self.basis_weights[:,:,None]).sum(1)
        else:h=self.temperature(2*self.gate-1)
        voltage=self.gate*self.voltage(2*self.gate-1) if self.role=='F_dyn' else None
        return self.gate*h,voltage

class JointObjective:
    def __init__(self,role,seed=29,device='cpu',folder=RUN):
        self.config=read(folder/'config.json');self.device=torch.device(device);self.role=role
        with np.load(folder/'input.npz',allow_pickle=False) as a:self.data={k:a[k] for k in a.files}
        self.model=JointModel(role,seed,self.data['time'],self.data['observation_time'],self.device)
        self.arrays={k:torch.as_tensor(self.data[k],dtype=torch.float64,device=self.device) for k in ['T0','v0','observation_voltage','observation_weights']}
        t=self.data['time'];ot=self.data['observation_time'];idx=np.searchsorted(t,ot,side='right')-1;idx=np.clip(idx,0,len(t)-2)
        self.obs_left=torch.tensor(idx,dtype=torch.long,device=self.device)
        self.obs_frac=torch.tensor((ot-t[idx])/(t[idx+1]-t[idx]),dtype=torch.float64,device=self.device)[:,None]
        self.Vin=torch.tensor(self.config['Vin_V'],dtype=torch.float64,device=self.device)
        self.K=P.Sth*torch.tensor([[1.,-.12],[-.12,1.]],dtype=torch.float64,device=self.device)
        self.h=self.config['dt_s']
    def fields(self):
        dT,dv=self.model.corrections();T=self.arrays['T0']+dT
        R=resistance_from_temperature(T)
        v=self.arrays['v0']+dv if self.role=='F_dyn' else rc_voltage(R,self.h,P.C,P.RL,self.Vin,0.)
        return T,R,v
    def components(self,T,R,v):
        q=v[:-1]**2/R[:-1]
        rT=P.Cth*(T[1:]-T[:-1])/self.h+(T[:-1]-P.Tbase)@self.K.T-q
        rRC=P.C*(v[1:]-v[:-1])/self.h-(self.Vin-v[:-1])/P.RL+v[:-1]/R[:-1]
        obs=(1-self.obs_frac)*v[self.obs_left]+self.obs_frac*v[self.obs_left+1]
        Lobs=(self.arrays['observation_weights'][:,None]*((obs-self.arrays['observation_voltage'])/11.)**2).sum()/2
        LT=(rT/.001).square().mean();LRC=(rRC/.001).square().mean()
        loss=Lobs+LT+(LRC if self.role=='F_dyn' else 0.)
        return loss,dict(obs=Lobs,heat=LT,RC=LRC),rT,rRC
    def loss(self,backward=True):
        T,R,v=self.fields();loss,parts,_,_=self.components(T,R,v)
        if backward:loss.backward()
        return loss,parts
    def export(self,path):
        with torch.no_grad():
            T,R,v=self.fields();loss,parts,rT,rRC=self.components(T,R,v)
        arrays={k:x.detach().cpu().numpy() for k,x in dict(T=T,R=R,v=v,rT=rT,rRC=rRC).items()}
        history=replay_with_history(arrays['T'])
        arrays.update(history)
        arrays['time']=self.data['time'];arrays['native_device_current']=arrays['v']/arrays['R']
        arrays['common_voltage']=rc_forward(arrays['R'],self.h,P.C,P.RL,np.array(self.config['Vin_V']),0.)
        arrays['common_device_current']=arrays['common_voltage']/arrays['R']
        arrays['common_rT']=P.Cth*np.diff(arrays['T'],axis=0)/self.h+(arrays['T'][:-1]-P.Tbase)@self.K.cpu().numpy().T-arrays['common_voltage'][:-1]**2/arrays['R'][:-1]
        np.savez_compressed(path,**arrays)
        return dict(loss=float(loss),parts={k:float(x) for k,x in parts.items()},time=stamp())

def check_resources(device):
    # No psutil dependency on the remote scientific environment.
    if os.name=='posix':
        status=Path('/proc/self/status').read_text()
        rss=int(next(x.split()[1] for x in status.splitlines() if x.startswith('VmRSS:')))*1024
        info=Path('/proc/meminfo').read_text();free=int(next(x.split()[1] for x in info.splitlines() if x.startswith('MemAvailable:')))*1024
        limit=Path('/sys/fs/cgroup/memory.max');usage=Path('/sys/fs/cgroup/memory.current')
        if limit.exists() and limit.read_text().strip()!='max':free=min(free,int(limit.read_text())-int(usage.read_text()))
        if rss>=12*1024**3 or free<4*1024**3:raise MemoryError('Frozen host memory stop')
    if str(device).startswith('cuda'):
        free,_=torch.cuda.mem_get_info(device)
        if torch.cuda.memory_allocated(device)>=16*1024**3 or free<4*1024**3:raise MemoryError('Frozen GPU memory stop')

def train(role,seed,device='cuda:0',folder=RUN):
    cfg=read(folder/'config.json');admission=read(folder/'admission.json')
    if not admission['passed']:raise RuntimeError('Admission did not pass')
    out=folder/f'seed-{seed}'/role;out.mkdir(parents=True,exist_ok=True)
    if (out/'termination.json').exists():
        prior=read(out/'termination.json')
        if prior['status']!='RESOURCE_INTERRUPTED':raise RuntimeError('Frozen terminal result already exists')
        if datetime.now(timezone.utc)>=datetime.fromisoformat(cfg['science_deadline_utc']):raise RuntimeError('Scientific cutoff has elapsed')
        with (out/'interruptions.jsonl').open('a',encoding='utf-8') as stream:stream.write(json.dumps(prior)+'\n')
    exp=JointObjective(role,seed,device,folder);parameters=list(exp.model.parameters())
    progress=dict(adam_updates=0,lbfgs_evaluations=0,lbfgs_accepted=0,full_objective_calls=0)
    accepted=None;started=time.perf_counter();phase='adam' if role!='S_dyn' else 'lbfgs'
    def persist(opt,event):
        nonlocal accepted
        accepted=dict(model_state_dict=cpu(exp.model.state_dict()),optimizer_state_dict=cpu(opt.state_dict()),phase=phase,
            progress=copy.deepcopy(progress),torch_rng=cpu(torch.get_rng_state()),cuda_rng=cpu(torch.cuda.get_rng_state_all()) if torch.cuda.is_available() else None,
            seed=seed,role=role,event=event,accepted=True,time=stamp())
        atomic_pt(out/'accepted-state.pt',accepted)
    def resource():
        check_resources(device)
        if datetime.now(timezone.utc)>=datetime.fromisoformat(cfg['science_deadline_utc']):raise TimeoutError('36h scientific cutoff')
    opt=torch.optim.Adam(parameters,lr=.001,betas=(.9,.999),eps=1e-8)
    if (out/'accepted-state.pt').exists():
        accepted=torch.load(out/'accepted-state.pt',map_location=device,weights_only=False)
        exp.model.load_state_dict(accepted['model_state_dict']);progress=accepted['progress'];phase=accepted['phase']
        if phase=='adam':opt.load_state_dict(accepted['optimizer_state_dict'])
        torch.set_rng_state(accepted['torch_rng'].cpu())
        if accepted.get('cuda_rng') is not None:torch.cuda.set_rng_state_all([x.cpu() for x in accepted['cuda_rng']])
        if (out/'cost-journal.json').exists():
            journal=read(out/'cost-journal.json')
            for key in ['lbfgs_evaluations','full_objective_calls']:
                progress[key]=max(progress[key],journal[key])
    else:persist(opt,'initial_zero_correction')
    log=(out/'training.jsonl').open('a',encoding='utf-8')
    try:
        if phase=='adam':
            for _ in range(progress['adam_updates'],600):
                resource();opt.zero_grad(set_to_none=True);progress['full_objective_calls']+=1
                save(out/'cost-journal.json',progress)
                loss,parts=exp.loss();norm=torch.nn.utils.clip_grad_norm_(parameters,10.)
                if not torch.isfinite(loss) or not torch.isfinite(norm):raise FloatingPointError('Nonfinite full objective or gradient')
                opt.step();progress['adam_updates']+=1;persist(opt,'accepted_adam')
                if progress['adam_updates']==1 or progress['adam_updates']%25==0:
                    row=dict(stage=phase,loss=float(loss),parts={k:float(v) for k,v in parts.items()},**progress,seconds=time.perf_counter()-started)
                    log.write(json.dumps(row)+'\n');log.flush();print(json.dumps(dict(role=role,seed=seed,**row)),flush=True)
            atomic_pt(out/'adam-complete.pt',accepted);phase='lbfgs'
            opt=torch.optim.LBFGS(parameters,lr=1.,max_iter=1,max_eval=32,tolerance_grad=1e-10,tolerance_change=1e-14,history_size=50,line_search_fn='strong_wolfe')
            persist(opt,'lbfgs_initial')
        if role=='S_dyn' and accepted['event']=='initial_zero_correction':
            opt=torch.optim.LBFGS(parameters,lr=1.,max_iter=1,max_eval=32,tolerance_grad=1e-10,tolerance_change=1e-14,history_size=50,line_search_fn='strong_wolfe')
            persist(opt,'lbfgs_initial')
        base=progress['lbfgs_accepted'];baseeval=progress['lbfgs_evaluations']
        def charge():
            progress['lbfgs_evaluations']+=1;progress['full_objective_calls']+=1
            save(out/'cost-journal.json',progress)
        def objective():return exp.loss()[0]
        def report(record,optim):
            progress['lbfgs_accepted']=base+record['accepted_steps'];persist(optim,record['event'])
            if record['event']=='accepted':
                log.write(json.dumps(dict(stage='lbfgs',**record))+'\n');log.flush()
        budget=700 if role=='S_dyn' else 100
        result,opt=accepted_lbfgs(parameters,objective,budget-baseeval,optimizer_state=accepted['optimizer_state_dict'],report=report,charge=charge,resource_check=resource)
        progress['lbfgs_accepted']=base+result['accepted_steps'];persist(opt,'final_accepted')
        atomic_pt(out/'checkpoint.pt',accepted);detail=exp.export(out/'endpoint.npz')
        record=dict(status='VALID_COMPLETE',role=role,seed=seed,progress=progress,optimizer_termination=result,endpoint=detail,seconds=time.perf_counter()-started)
    except (MemoryError,TimeoutError,FloatingPointError,RuntimeError) as exc:
        # L-BFGS wrapper already rolled back; restore the durable accepted state
        # for Adam failures as well. Never expose a line-search trial endpoint.
        exp.model.load_state_dict(accepted['model_state_dict']);accepted['progress']=copy.deepcopy(progress)
        atomic_pt(out/'accepted-state.pt',accepted)
        record=dict(status='RESOURCE_INTERRUPTED' if isinstance(exc,(MemoryError,TimeoutError,torch.cuda.OutOfMemoryError)) else 'NUMERICAL_OR_EXECUTION_FAILURE',
            role=role,seed=seed,error=repr(exc),progress=progress,seconds=time.perf_counter()-started)
        save(out/'termination.json',record)
    finally:log.close()
    save(out/'termination.json',record);print(json.dumps(record),flush=True);return record
