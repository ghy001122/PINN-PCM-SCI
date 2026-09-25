"""Reference-free GPU queries and two unchanged CPU backward-Euler phase runs."""
from __future__ import annotations
import argparse
import csv
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import time
import traceback
import numpy as np
from .phk_benchmark import PhkGrid
from .phk_v21_solver import solve_phase_candidate,PhkV21PhaseAlgorithm
from .phk_v23_conditional_phase import phase_rhs

ROOT=Path(__file__).resolve().parents[1]
CONFIG=ROOT/'configs/phk_v23/fixed_temperature_phase_probe_20260925.json'

def now():return datetime.now(timezone.utc).isoformat()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def save(p,value):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(value,indent=2,allow_nan=False),encoding='utf-8');tmp.replace(p)
def digest(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

class ResourceStop(RuntimeError):pass

class Resources:
    def __init__(self,cfg,device):self.cfg=cfg;self.device=device;self.peak_rss=0;self.minimum_headroom=None
    def check(self):
        c=self.cfg;gib=1024**3
        if Path('/proc/self/statm').exists():
            rss=int(Path('/proc/self/statm').read_text().split()[1])*os.sysconf('SC_PAGE_SIZE')
            self.peak_rss=max(self.peak_rss,rss)
            if rss>=c['process_rss_limit_gib']*gib:raise ResourceStop('PROCESS_RSS_LIMIT')
        p=Path('/sys/fs/cgroup/memory/memory.limit_in_bytes');u=p.with_name('memory.usage_in_bytes')
        if p.exists() and u.exists():
            headroom=int(p.read_text())-int(u.read_text())
            self.minimum_headroom=headroom if self.minimum_headroom is None else min(self.minimum_headroom,headroom)
            if headroom<c['minimum_container_headroom_gib']*gib:raise ResourceStop('CONTAINER_MEMORY_HEADROOM')
        if self.device.startswith('cuda'):
            import torch
            free,_=torch.cuda.mem_get_info()
            if free<c['minimum_gpu_headroom_gib']*gib:raise ResourceStop('GPU_MEMORY_HEADROOM')
            if torch.cuda.memory_allocated()>=c['gpu_allocation_limit_gib']*gib:raise ResourceStop('GPU_ALLOCATION_LIMIT')
    def record(self):return dict(peak_rss_bytes=self.peak_rss,minimum_container_headroom_bytes=self.minimum_headroom)


def model_identity(model):
    h=hashlib.sha256()
    for key,value in sorted(model.state_dict().items()):
        h.update(key.encode());h.update(value.detach().cpu().contiguous().numpy().tobytes())
    return h.hexdigest()


def cached_queries(cfg,out,device,resources):
    """Materialize numeric cache only. No reference or observation loader is called."""
    import torch
    from .phk_v23_lf11_followup_fit import fit_model,head_field
    from .phk_v23_lf11_elimination_physics import fields,face_quadrature
    from .phk_v22r_pinn import _gradient
    if (out/'cache-complete.json').exists():return read(out/'cache-complete.json')
    cache=out/'cache'
    if cache.exists():raise FileExistsError('Incomplete query cache exists; inspect instead of replaying')
    cache.mkdir()
    torch.set_num_threads(cfg['cpu_threads'])
    state=torch.load(ROOT/cfg['parent'],map_location='cpu',weights_only=False)['model_state_dict']
    model=fit_model(read(ROOT/cfg['parent_config']),state,adapter=True).to(device).eval()
    model.requires_grad_(False);del state
    identity=model_identity(model);p=model.physics
    keys=('x_min','x_max','z_min','z_max','interface_width','barrier_scale','thermal_drive','theta_transition',
          'mobility_cold','mobility_hot','mobility_width','thermal_diffusivity','volumetric_cooling','latent_ratio','thermal_robin_biot')
    physics={k:float(getattr(p,k)) for k in keys}
    save(out/'physics.json',physics)
    grid=PhkGrid.build(nx=cfg['grid'][0],nz=cfg['grid'][1],**{k:physics[k] for k in ('x_min','x_max','z_min','z_max')})
    a,b=cfg['interval'];fine=a+np.arange(cfg['steps'][1]+1)*cfg['dt'][1];fine[-1]=b
    common=fine[::2]
    with torch.no_grad():
        drive=p.waveform(torch.tensor(fine,dtype=torch.float64,device=device))
        if float(drive.abs().max())>1e-14:raise ValueError('Conditional interval is not zero drive')
    np.save(cache/'time_fine.npy',fine);np.save(cache/'time_common.npy',common)
    np.savez(cache/'grid.npz',x=grid.cell_x,z=grid.cell_z,volumes=grid.cell_volumes)
    def mem(name,shape):return np.lib.format.open_memmap(cache/(name+'.npy'),mode='w+',dtype='float64',shape=shape)
    temps=mem('temperature_fine',(len(fine),grid.cell_count))
    base=mem('B0_phase',(len(common),grid.cell_count));base_dt=mem('B0_phase_t_AD',base.shape)
    temp_dt=mem('temperature_t_AD',base.shape);flux=mem('thermal_flux',base.shape)
    xy=np.column_stack((grid.cell_x,grid.cell_z));faces,incidence=face_quadrature(grid,np.arange(grid.cell_count))
    bx=np.vstack((np.column_stack((np.full(grid.nz,p.x_min),grid.z_centers)),
        np.column_stack((np.full(grid.nz,p.x_max),grid.z_centers)),
        np.column_stack((grid.x_centers,np.full(grid.nx,p.z_min))),
        np.column_stack((grid.x_centers,np.full(grid.nx,p.z_max)))))
    normals=np.vstack((np.tile([-1.,0.],(grid.nz,1)),np.tile([1.,0.],(grid.nz,1)),
                       np.tile([0.,-1.],(grid.nx,1)),np.tile([0.,1.],(grid.nx,1))))
    bc=mem('B0_boundary_normal_AD',(len(common),len(bx)))
    np.savez(cache/'boundary-grid.npz',xy=bx,normal=normals,side_counts=[grid.nz,grid.nz,grid.nx,grid.nx])
    work=dict(temperature_head_positions=0,phase_head_positions=0,first_derivative_positions=0,
              second_derivative_components=0,head_query_batches=0,thermal_face_positions=0,boundary_positions=0)
    endpoint={};started=time.perf_counter();chunk=cfg['coordinate_chunk']
    def query(points,t,mode,endpoint_query=False):
        arrays={}
        for first in range(0,len(points),chunk):
            q=torch.tensor(np.column_stack((points[first:first+chunk],np.full(min(chunk,len(points)-first),t))),
                           dtype=torch.float64,device=device,requires_grad=mode!='value')
            n=len(q);work['head_query_batches']+=1
            if mode=='value':
                with torch.no_grad():result={'temperature':head_field(model,'temperature',q)}
                work['temperature_head_positions']+=n
            elif mode=='face':
                tt=head_field(model,'temperature',q);grad=_gradient(tt,q)
                result={'x':grad[:,0],'z':grad[:,1]};work['temperature_head_positions']+=n
                work['thermal_face_positions']+=n;work['first_derivative_positions']+=n
            else:
                f=fields(model,q);dp=_gradient(f['phase'],q)
                work['phase_head_positions']+=n;work['temperature_head_positions']+=n
                work['first_derivative_positions']+=n
                if mode=='boundary':
                    result={'x':dp[:,0],'z':dp[:,1]};work['boundary_positions']+=n
                else:
                    dt=_gradient(f['temperature'],q);work['first_derivative_positions']+=n
                    result={'temperature':f['temperature'],'phase':f['phase'],'temperature_t':dt[:,2],'phase_t':dp[:,2]}
                    if endpoint_query:
                        result['phase_tt']=_gradient(dp[:,2],q)[:,2]
                        result['phase_laplacian_AD']=_gradient(dp[:,0],q)[:,0]+_gradient(dp[:,1],q)[:,1]
                        work['second_derivative_components']+=3*n
            for key,v in result.items():arrays.setdefault(key,[]).append(v.detach().cpu().numpy().copy())
            # No torch objects survive this chunk in a scientific cache.
            del q,result
        return {k:np.concatenate(v) for k,v in arrays.items()}
    for i,t in enumerate(fine):
        if i%2:
            vals=query(xy,t,'value');temps[i]=vals['temperature']
        else:
            k=i//2;end=i in (0,len(fine)-1)
            vals=query(xy,t,'cell',end)
            temps[i]=vals['temperature'];base[k]=vals['phase'];base_dt[k]=vals['phase_t'];temp_dt[k]=vals['temperature_t']
            if end:
                for name,value in vals.items():endpoint[('left' if i==0 else 'right')+'_'+name]=value
            face=query(faces,t,'face')
            flux[k]=(grid.dz*(face['x'][incidence[:,1]]-face['x'][incidence[:,0]])+
                     grid.dx*(face['z'][incidence[:,3]]-face['z'][incidence[:,2]]))/(grid.dx*grid.dz)
            boundary=query(bx,t,'boundary');bc[k]=normals[:,0]*boundary['x']+normals[:,1]*boundary['z']
        if i%32==0 or i==len(fine)-1:
            resources.check()
            for ar in (temps,base,base_dt,temp_dt,flux,bc):ar.flush()
            save(out/'query-progress.json',dict(fine_time_index=i,completed_common_nodes=i//2+1,work=work,utc=now()))
            print(json.dumps(dict(stage='query',node=i,total=len(fine),seconds=time.perf_counter()-started)),flush=True)
    for ar in (temps,base,base_dt,temp_dt,flux,bc):ar.flush()
    np.savez(cache/'endpoint-AD.npz',**endpoint)
    after=model_identity(model)
    if after!=identity:raise RuntimeError('Frozen base model identity changed')
    record=dict(status='COMPLETE_NUMERIC_CACHE',seconds=time.perf_counter()-started,work=work,
                base_model_sha256_before=identity,base_model_sha256_after=after,
                model_parameters_unchanged=True,reference_read=False,training_updates=0,
                electrical_forward=0,electrical_adjoint=0,query_device=device,utc=now(),
                mobility_argument_range=[float((temps.min()-p.theta_transition)/p.mobility_width),float((temps.max()-p.theta_transition)/p.mobility_width)])
    save(out/'cache-complete.json',record)
    del model
    if device.startswith('cuda'):torch.cuda.empty_cache()
    return record


def propagate(cfg,out,resources):
    p=read(out/'physics.json');g=PhkGrid.build(nx=80,nz=40,**{k:p[k] for k in ('x_min','x_max','z_min','z_max')})
    c=out/'cache';temps=np.load(c/'temperature_fine.npy',mmap_mode='r');initial=np.load(c/'B0_phase.npy',mmap_mode='r')[0].copy()
    fine_time=np.load(c/'time_fine.npy');records={}
    for index,label in enumerate(('coarse','fine')):
        path=out/label
        if path.exists():raise FileExistsError('Scientific trajectory already exists: '+str(path))
        path.mkdir();dt=cfg['dt'][index];n=cfg['steps'][index];stride=2 if index==0 else 1
        values=np.lib.format.open_memmap(path/'phase.npy',mode='w+',dtype='float64',shape=(n+1,g.cell_count))
        values[0]=initial;values.flush();times=fine_time[::stride];np.save(path/'time.npy',times)
        old=initial.copy();counters=dict(accepted_main_steps=0,newton_iterations=0,linear_solves=0,residual_evaluations=0,
            jacobian_evaluations=0,decrease_rejections=0,output_clipping_count=0)
        started=time.perf_counter();record=dict(status='RUNNING',dt=dt,expected_steps=n,initial_guess='own_previous_accepted',counts=counters)
        save(path/'summary.json',record)
        columns=['step','time','residual_inf','residual_rate_inf','iterations','linear_solves','residual_evaluations','jacobian_evaluations','decrease_rejections','phase_min','phase_max']
        try:
            with (path/'steps.csv').open('x',newline='',encoding='utf-8') as stream:
                writer=csv.DictWriter(stream,fieldnames=columns);writer.writeheader()
                for step in range(1,n+1):
                    result=solve_phase_candidate(algorithm=PhkV21PhaseAlgorithm.LOGIT_NEWTON_ANALYTIC_JACOBIAN,
                        phase_old=old,initial_guess=old,temperature=np.asarray(temps[step*stride]),grid=g,dt=dt,
                        coefficients=p,interface_width=p['interface_width'],solver={'transport_newton_residual_tolerance':cfg['algebraic_tolerance']},lower_bound=0.,upper_bound=1.)
                    phase=result.phase
                    if not np.isfinite(phase).all() or np.any(phase<0) or np.any(phase>1):raise RuntimeError('INVALID_ACCEPTED_STATE')
                    residual=phase-old-dt*phase_rhs(phase,np.asarray(temps[step*stride]),g,p)
                    norm=float(np.max(np.abs(residual)))
                    if norm>cfg['algebraic_tolerance']:raise RuntimeError('POSTSOLVE_ALGEBRAIC_TOLERANCE')
                    values[step]=phase;old=phase.copy();counters['accepted_main_steps']=step
                    for target,attr in [('newton_iterations','iterations'),('linear_solves','linear_solves'),('residual_evaluations','residual_evaluations'),('jacobian_evaluations','jacobian_evaluations'),('decrease_rejections','decrease_rejections'),('output_clipping_count','output_clipping_count')]:counters[target]+=getattr(result,attr)
                    writer.writerow(dict(step=step,time=times[step],residual_inf=norm,residual_rate_inf=norm/dt,
                        **{k:getattr(result,k) for k in ['iterations','linear_solves','residual_evaluations','jacobian_evaluations','decrease_rejections']},phase_min=float(phase.min()),phase_max=float(phase.max())))
                    if step%16==0 or step==n:
                        values.flush();stream.flush();record.update(seconds=time.perf_counter()-started,last_time=float(times[step]));save(path/'summary.json',record);resources.check()
                    if step%128==0 or step==n:print(json.dumps(dict(stage=label,step=step,total=n,seconds=time.perf_counter()-started)),flush=True)
            record.update(status='COMPLETE',seconds=time.perf_counter()-started,all_algebraic_tolerances_passed=True,phase_sha256=digest(path/'phase.npy'))
            np.savez_compressed(path/'export-265.npz',time=times[::cfg['export_every'][index]],phase=np.asarray(values[::cfg['export_every'][index]]))
            save(path/'summary.json',record);records[label]=record
        except Exception as exc:
            values.flush();record.update(status='RESOURCE_STOPPED' if isinstance(exc,ResourceStop) else 'NUMERICAL_FAILURE',
                error=str(exc),seconds=time.perf_counter()-started,failed_attempt_step=counters['accepted_main_steps']+1,
                failed_attempt_internal_counts='not returned by unchanged solver; unknown, not zero')
            save(path/'summary.json',record);raise
    save(out/'trajectories-locked.json',dict(status='BOTH_TRAJECTORIES_LOCKED',utc=now(),trajectories=records,
        total_accepted_main_steps=sum(r['counts']['accepted_main_steps'] for r in records.values()),reference_read=False))


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--config',type=Path,default=CONFIG);parser.add_argument('--device',default='cuda:0')
    args=parser.parse_args();cfg=read(args.config);out=ROOT/cfg['run']
    if not cfg['execution_authorized']:raise RuntimeError('Execution authorization absent')
    out.mkdir(parents=True,exist_ok=True)
    if (out/'run-started.json').exists():raise FileExistsError('This bounded run has already started')
    save(out/'frozen-config.json',cfg)
    if read(out/'engineering-tests.json')['passed'] is not True:raise RuntimeError('Engineering checks not passed')
    resources=Resources(cfg,args.device);started=time.perf_counter()
    save(out/'run-started.json',dict(task_id=cfg['task_id'],utc=now(),device=args.device,parent_sha256=digest(ROOT/cfg['parent']),reference_read=False))
    try:
        resources.check();cached_queries(cfg,out,args.device,resources);propagate(cfg,out,resources)
        save(out/'run-complete.json',dict(status='TRAJECTORIES_COMPLETE',seconds=time.perf_counter()-started,resources=resources.record(),utc=now(),reference_read=False))
    except Exception as exc:
        save(out/'run-stop.json',dict(status='RESOURCE_STOPPED' if isinstance(exc,ResourceStop) else 'STOPPED',
            error=str(exc),traceback=traceback.format_exc(),utc=now(),seconds=time.perf_counter()-started,resources=resources.record(),reference_read=False,
            scientific_exit='NUMERICAL_UNRESOLVED'))
        raise

if __name__=='__main__':main()
