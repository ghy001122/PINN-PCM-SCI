"""Bounded, zero-update diagnostics of four saved phase-correction states.

No optimizer, electrical solve, reference field or altered thermal operator.
Only base coordinate derivatives are shared between the correction states.
"""
from __future__ import annotations
import argparse
import csv
import json
import platform
import time
from pathlib import Path
import numpy as np
import torch
from numpy.polynomial import legendre as leg
from .phk_v22r_pinn import _gradient
from .phk_v23_lf11 import ROOT, save_json, now
from .phk_v23_lf11_followup_fit import head_field
from .phk_v23_lf11_elimination import deserialize_pool
from .phk_v23_lf11_elimination_physics import coordinates, face_quadrature, grid_for
from .phk_v23_observation_preserving_phase import Completion, A, B, dark_gate
from .phk_v23_observation_preserving_phase_run import RUN, read

OUT = RUN/'diagnostic-20260925'
LABELS = ('B0', 'N-Adam', 'N-final', 'S-final')
COMPONENTS = ('phase_raw', 'thermal_raw', 'phase_BC', 'H')


def array(v):
    return v.detach().cpu().numpy()


def write_csv(path, rows):
    with Path(path).open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)


def gauss(order):
    x, w = leg.leggauss(order)
    edges = np.linspace(A, B, 17)
    times = np.concatenate([(a+b)/2+(b-a)*x/2 for a,b in zip(edges[:-1],edges[1:])])
    return times, np.tile(w/32,16)


def sample(grid, seed):
    rng = np.random.default_rng(seed)
    cells = rng.choice(grid.cell_count,128,replace=False)
    sides = {}
    for side in ('left','right','bottom','top'):
        if side in ('left','right'):
            sides[side] = np.column_stack([np.full(32,-1 if side=='left' else 1),rng.uniform(0,1,32)])
        else:
            sides[side] = np.column_stack([rng.uniform(-1,1,32),np.full(32,0 if side=='bottom' else 1)])
    return cells,sides


class Diagnostic:
    def __init__(self, device):
        self.device=device; self.cfg=read(RUN/'frozen-config.json')
        base=torch.load(ROOT/self.cfg['parent'],map_location='cpu',weights_only=False)['model_state_dict']
        self.models={}
        for label,arm,checkpoint in [('B0','N',None),('N-Adam','N','N/adam-600.pt'),
                                     ('N-final','N','N/checkpoint.pt'),('S-final','S','S/checkpoint.pt')]:
            m=Completion(self.cfg,base,arm,device).eval()
            if checkpoint:
                ck=torch.load(RUN/checkpoint,map_location=device,weights_only=False)
                assert ck['base_sha256']==read(RUN/'input-manifest.json')['parent_sha256']
                m.correction.load_state_dict(ck['correction_state_dict'])
            m.requires_grad_(False); self.models[label]=m
        self.base=self.models['B0']; self.p=self.base.physics
        self.grid=grid_for(self.p,*self.cfg['grid']); self.rows=[]; self.summaries=[]
        self.face_positions=0; self.base_extra_positions=0

    def tensor(self,q):
        return torch.tensor(q,dtype=torch.float64,device=self.device,requires_grad=True)

    def flux(self,t,cells):
        xy,incidence=face_quadrature(self.grid,cells)
        q=self.tensor(np.column_stack([xy,np.full(len(xy),t)]))
        grad=_gradient(head_field(self.base.base,'temperature',q),q)
        i=torch.as_tensor(incidence,device=self.device)
        self.face_positions+=len(xy)
        flux=self.grid.dz*(grad[i[:,1],0]-grad[i[:,0],0])+self.grid.dx*(grad[i[:,3],1]-grad[i[:,2],1])
        return (flux/(self.grid.dx*self.grid.dz)).detach()

    def evaluate_pool(self,name,times,weights,cells_at,sides_at):
        path=OUT/(name+'.json')
        if path.exists():
            rec=read(path); self.rows.extend(rec['time_rows']); self.summaries.extend(rec['summary']); return rec['summary']
        started=time.perf_counter(); rows=[]; raw={k:[] for k in ('time','weight','cells','boundary_xy')}
        for label in LABELS:
            for key in ('rphi','rT','phi_t','psi','delta_psi','normal'):
                raw[label+'/'+key]=[]
        for j,(t,w) in enumerate(zip(times,weights)):
            cells=cells_at(j); sides=sides_at(j)
            q=coordinates(self.grid,float(t),cells=cells,device=self.device,requires_grad=True)
            cache=self.base.base_cache(q,2); flux=self.flux(float(t),cells)
            bqs={s:self.tensor(np.column_stack([xy[:,:2],np.full(len(xy),t)])) for s,xy in sides.items()}
            bcaches={s:self.base.base_cache(v,1) for s,v in bqs.items()}
            raw['time'].append(t); raw['weight'].append(w); raw['cells'].append(cells)
            raw['boundary_xy'].append(np.concatenate([array(v[:,:2]) for v in bqs.values()]))
            for label,m in self.models.items():
                f=m.fields(q,order=2,cache=cache); p=self.p; phi=f['phase']; u=phi*(1-phi)
                rt=f['temperature_grad'][:,2]+p.latent_ratio*f['phase_grad'][:,2]+p.volumetric_cooling*f['temperature']-p.thermal_diffusivity*flux
                rp=f['phase_grad'][:,2]-p.mobility(f['temperature'])*(p.interface_width**2*f['phase_lap']-2*p.barrier_scale*u*(1-2*phi)-6*p.thermal_drive*(p.theta_transition-f['temperature'])*u)
                normals=[]; side_ms={}
                for s,bq in bqs.items():
                    bf=m.fields(bq,order=1,cache=bcaches[s]); axis=0 if s in ('left','right') else 1
                    v=array(bf['phase_grad'][:,axis]); normals.append(v); side_ms[s]=float(np.mean(v*v))
                v={k:array(f[k]) for k in ('phase_latent','phase_grad','phase_lap','phase')}
                d=array(f['phase_latent']-cache['phase_latent']); rp=array(rp); rt=array(rt); normal=np.concatenate(normals)
                row=dict(pool=name,state=label,time=float(t),weight=float(w),original_time_mass=float(w*(B-A)/2.5),
                         phase_raw=float(np.mean(rp*rp)),thermal_raw=float(np.mean(rt*rt)),phase_BC=sum(side_ms.values())/13)
                row.update(H=row['phase_raw']/75+row['thermal_raw']/48+5*row['phase_BC'],gate=float(dark_gate(q[:1,2]).detach()),
                    psi_min=float(v['phase_latent'].min()),psi_max=float(v['phase_latent'].max()),delta_psi_min=float(d.min()),delta_psi_max=float(d.max()),
                    phi_t_abs_max=float(abs(v['phase_grad'][:,2]).max()),phase_grad_abs_max=float(np.linalg.norm(v['phase_grad'][:,:2],axis=1).max()),
                    phase_laplacian_abs_max=float(abs(v['phase_lap']).max()),rphi_abs_max=float(abs(rp).max()),rT_abs_max=float(abs(rt).max()),
                    bc_normal_abs_max=float(abs(normal).max()),**{'bc_'+s:x for s,x in side_ms.items()})
                for key,z in [('phase_hot',rp),('thermal_hot',rt)]:
                    k=int(np.argmax(z*z)); row[key+'_cell']=int(cells[k]); row[key+'_x']=float(self.grid.cell_x[cells[k]]); row[key+'_z']=float(self.grid.cell_z[cells[k]])
                k=int(np.argmax(normal*normal)); xy=raw['boundary_xy'][-1][k]; row.update(bc_hot_x=float(xy[0]),bc_hot_z=float(xy[1]))
                rows.append(row)
                for key,z in [('rphi',rp),('rT',rt),('phi_t',v['phase_grad'][:,2]),('psi',v['phase_latent']),('delta_psi',d),('normal',normal)]:raw[label+'/'+key].append(z)
            if j%64==0:print(json.dumps(dict(pool=name,times_done=j+1,total=len(times))),flush=True)
        summary=[]
        for label in LABELS:
            rr=[r for r in rows if r['state']==label]
            row=dict(pool=name,state=label,n_times=len(times),**{k:float(sum(r['weight']*r[k] for r in rr)) for k in COMPONENTS})
            row.update(phase_weighted=row['phase_raw']/75,thermal_weighted=row['thermal_raw']/48,boundary_weighted=5*row['phase_BC'],
                original_variable_objective=.1/read(RUN/'calibration.json')['bE']*(B-A)/2.5*row['H'])
            summary.append(row)
        np.savez_compressed(OUT/(name+'-traces.npz'),**{k:np.asarray(v) for k,v in raw.items()})
        save_json(path,dict(summary=summary,time_rows=rows,seconds=time.perf_counter()-started))
        self.rows.extend(rows);self.summaries.extend(summary)
        print(json.dumps(dict(completed=name,summary=summary)),flush=True)
        return summary

    def common(self,order,seed,name):
        cells,sides=sample(self.grid,seed);t,w=gauss(order)
        return self.evaluate_pool(name,t,w,lambda _:cells,lambda _:sides)

    def original(self,name,file):
        pool=deserialize_pool(read(RUN/file));items=[(t,v) for t,v in sorted(pool['times'].items()) if A<t<B]
        mass=sum(v['mass'] for t,v in items)
        return self.evaluate_pool(name,np.array([t for t,v in items]),np.array([v['mass']/mass for t,v in items]),
                                  lambda j:items[j][1]['cells'],lambda j:items[j][1]['sides'])


def convergence(low,high):
    changes={a['state']:{k:abs(a[k]-b[k])/max(abs(b[k]),1e-12) for k in COMPONENTS} for a,b in zip(low,high)}
    ranks=lambda rows,k:[r['state'] for r in sorted(rows,key=lambda r:r[k])]
    changed={k:ranks(low,k)!=ranks(high,k) for k in COMPONENTS}
    return dict(relative_changes=changes,ranking_changed=changed,requires_higher_order=any(v>.01 for row in changes.values() for v in row.values()) or any(changed.values()))


def cumulative_gauss(values,order):
    """Integrate the nodal Legendre interpolant on each of 16 fixed segments."""
    x,w=leg.leggauss(order);vander=leg.legvander(x,order-1)
    basis=leg.legint(np.eye(order),axis=0)
    integ=leg.legval(x,basis,tensor=True).T-leg.legval(-1.,basis)
    mat=integ@np.linalg.inv(vander)*(B-A)/32
    parts=values.reshape(16,order,-1);out=[];running=np.zeros(parts.shape[-1])
    for part in parts:
        out.append(running+mat@part);running=running+(B-A)/32*(w@part)
    return np.concatenate(out),running


def thermal(d,order):
    path=OUT/f'thermal-{order}.json'
    if path.exists():return read(path)
    cells=np.array(read(RUN/'theory-diagnostics.json')['cells']);p=d.p;t,w=gauss(order)
    ends=[d.base.base_cache(coordinates(d.grid,v,cells=cells,device=d.device),0) for v in (A,B)]
    endpoint=array(ends[1]['temperature']-ends[0]['temperature']+p.latent_ratio*(ends[1]['phase']-ends[0]['phase']))
    forcing=[];stationary=[];res=[]
    for v in t:
        q=coordinates(d.grid,float(v),cells=cells,device=d.device,requires_grad=True)
        c=d.base.base_cache(q,1);f=d.base.fields(q,order=1,cache=c)
        st=p.volumetric_cooling*f['temperature']-p.thermal_diffusivity*d.flux(float(v),cells)
        forcing.append(array((-st-f['temperature_grad'][:,2])/p.latent_ratio));stationary.append(array(st))
        res.append(array(f['temperature_grad'][:,2]+p.latent_ratio*f['phase_grad'][:,2]+st))
    forcing=np.asarray(forcing);integral,end=cumulative_gauss(forcing,order)
    left=array(ends[0]['phase']);right=array(ends[1]['phase']);phi=left+integral
    C=endpoint+(B-A)*(w@np.asarray(stationary));mismatch=left+end-right;lower=(C/(B-A))**2
    base_ms=w@np.asarray(res)**2;overshoot=np.maximum(-phi,0)+np.maximum(phi-1,0)
    out=dict(order=order,n_times=len(t),C=C.tolist(),endpoint_offset=mismatch.tolist(),phi_min=float(phi.min()),phi_max=float(phi.max()),
        outside_time_cell_fraction=float(w@((phi<0)|(phi>1)).mean(1)),cells_ever_outside_fraction=float(np.mean((overshoot>0).any(0))),
        max_undershoot=float(max(0,-phi.min())),max_overshoot=float(max(0,phi.max()-1)),
        endpoint_identity_max_absolute=float(abs(mismatch+C/p.latent_ratio).max()),
        endpoint_absolute_quantiles=np.quantile(abs(mismatch),[0,.25,.5,.75,.9,1]).tolist(),
        mean_raw_square_lower_bound=float(lower.mean()),base_mean_raw_square=float(base_ms.mean()),
        lower_to_base=float(lower.mean()/base_ms.mean()),C_vs_historical64_max_absolute=float(abs(C-np.array(read(RUN/'theory-diagnostics.json')['thermal']['64']['C'])).max()),
        latent_ratio=p.latent_ratio,not_a_phase_solution=True)
    np.savez_compressed(OUT/f'thermal-{order}-traces.npz',time=t,weights=w,cells=cells,phi_H=phi,forcing=forcing,
        phi_base_left=left,phi_base_right=right,phi_H_right=left+end,C=C,base_thermal_residual=np.asarray(res))
    save_json(path,out);print(json.dumps(dict(thermal=order,**{k:out[k] for k in ('phi_min','phi_max','endpoint_identity_max_absolute','lower_to_base')})),flush=True)
    return out


def endpoint_traces(d,seed):
    path=OUT/'endpoint-traces.npz'
    if path.exists():return
    cells,_=sample(d.grid,seed);dist=np.geomspace(1e-9,(B-A)/16,64)
    ts=np.unique(np.r_[A,A+dist,B-dist,B]);m=d.models['N-final'];raw={k:[] for k in ('psi','delta_psi','phi_t','phase')}
    for t in ts:
        q=coordinates(d.grid,float(t),cells=cells,device=d.device,requires_grad=True)
        c=d.base.base_cache(q,1);f=m.fields(q,order=1,cache=c)
        for k,v in [('psi',f['phase_latent']),('delta_psi',f['phase_latent']-c['phase_latent']),('phi_t',f['phase_grad'][:,2]),('phase',f['phase'])]:raw[k].append(array(v))
    np.savez_compressed(path,time=ts,cells=cells,gate=array(dark_gate(torch.tensor(ts))),**{k:np.asarray(v) for k,v in raw.items()})


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--device',default='cpu');args=parser.parse_args()
    torch.set_num_threads(4);started=time.perf_counter();OUT.mkdir(exist_ok=True)
    contract=read(OUT/'contract.json');assert contract['optimizer_updates']==contract['electrical_solves']==0
    if (OUT/'execution.json').exists():raise FileExistsError('Completed diagnostic must not be rerun')
    save_json(OUT/'started.json',dict(started_utc=now(),device=args.device,python=platform.python_version(),torch=torch.__version__))
    d=Diagnostic(args.device)
    d.original('fixed-training','fixed-pool.json');d.original('independent-D','D-audit-pool.json')
    c128=d.common(8,contract['spatial_seeds'][0],'common-128')
    c256=d.common(16,contract['spatial_seeds'][0],'common-256')
    change=convergence(c128,c256);convs={'128_to_256':change};order=16
    if change['requires_higher_order']:
        c512=d.common(32,contract['spatial_seeds'][0],'common-512');convs['256_to_512']=convergence(c256,c512);order=32
    d.common(16,contract['spatial_seeds'][1],'spatial-256')
    endpoint_traces(d,contract['spatial_seeds'][0])
    thermal(d,8);thermal(d,16)
    if order==32:thermal(d,32)
    write_csv(OUT/'components.csv',d.summaries);write_csv(OUT/'time-components.csv',d.rows)
    save_json(OUT/'quadrature.json',convs)
    save_json(OUT/'execution.json',dict(status='BOUNDED_ZERO_UPDATE_DIAGNOSTIC_COMPLETE',finished_utc=now(),
        seconds=time.perf_counter()-started,device=args.device,gpu=torch.cuda.get_device_name(0) if args.device.startswith('cuda') else None,
        python=platform.python_version(),torch=torch.__version__,numpy=np.__version__,optimizer_updates=0,electrical_solves=0,
        model_parameter_backward_calls=0,reference_field_reads=0,phase_pde_advances=0,
        state_work={k:m.work for k,m in d.models.items()},shared_thermal_face_AD_positions=d.face_positions,
        maximum_time_nodes=order*16,conditioned_phi_is_not_teacher=True))
    print('DIAGNOSTIC_COMPLETE',flush=True)


if __name__=='__main__':main()
