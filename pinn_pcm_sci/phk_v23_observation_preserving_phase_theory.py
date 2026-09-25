"""Finite observation-equivalent examples and frozen-temperature integral bound."""
import json
import numpy as np
import torch
from .phk_v22r_pinn import _gradient
from .phk_v23_lf11 import save_json
from .phk_v23_lf11_elimination_physics import fields,coordinates,thermal_phase_residual,face_quadrature
from .phk_v23_lf11_followup_fit import head_field
from .phk_v23_lf11_electric_layer import ElectricalLayer
from .phk_v23_observation_preserving_phase import dark_gate,A,B
from .phk_v23_observation_preserving_phase_run import RUN,read,inputs


def modified(base,q,sign):
    f=fields(base,q,phase_latent=True)
    bump=((1-q[:,0]**2)*4*q[:,1]*(1-q[:,1]))**3
    f['phase']=torch.sigmoid(f['phase_latent']+sign*dark_gate(q[:,2])*bump)
    return f


def main():
    torch.set_num_threads(4)
    if (RUN/'theory-diagnostics.json').exists():raise FileExistsError('Theory diagnostics already complete')
    cfg=read(RUN/'frozen-config.json');exp,_=inputs(cfg,'N');base=exp.model.base;grid=exp.grid;p=base.physics
    records={};snapshots={};layer=ElectricalLayer(grid,p.heater_width_fraction,cfg['linear_tolerance'])
    for t in (.27,1.28,1.55,1.8):
        q=coordinates(grid,t);f0=modified(base,q,0);row={}
        u=float(p.waveform(torch.tensor(t,dtype=torch.float64)))
        v0,h0=layer(p.conductivity(f0['temperature'],f0['phase']),u)
        ports0=layer.deposition(v0,p.conductivity(f0['temperature'],f0['phase']),u)
        snapshots[str(t)+'/base']=f0['phase'].detach().numpy()
        for sign in (-1,1):
            f=modified(base,q,sign);sigma=p.conductivity(f['temperature'],f['phase']);v,h=layer(sigma,u)
            ports=layer.deposition(v,sigma,u)
            row[str(sign)]=dict(max_phase_change=float((f['phase']-f0['phase']).abs().max()),
                max_temperature_change=float((f['temperature']-f0['temperature']).abs().max()),
                max_voltage_change=float((v-v0).abs().max()),max_joule_change=float((h-h0).abs().max()),
                port_changes={k:abs(float(ports[k])-float(ports0[k])) for k in ('top_current','bottom_current','joule_power')})
            snapshots[str(t)+'/'+str(sign)]=f['phase'].detach().numpy()
        records[str(t)]=row
    # All actual visible phase locations, and the original boundary/IC traces.
    visible=torch.tensor(exp.obs.data.coordinates[exp.obs.data.visible],dtype=torch.float64)
    obs_change=max(float((modified(base,visible,s)['phase']-modified(base,visible,0)['phase']).abs().max()) for s in (-1,1))
    boundary=[]
    for side in ('left','right','bottom','top'):
        for t in (0.,A,1.55,1.8,B,2.5):
            xy=np.column_stack([np.linspace(-1,1,17),np.linspace(0,1,17)])
            if side in ('left','right'):xy[:,0]=-1 if side=='left' else 1;axis=0
            else:xy[:,1]=0 if side=='bottom' else 1;axis=1
            q=torch.tensor(np.column_stack([xy,np.full(len(xy),t)]),dtype=torch.float64,requires_grad=True)
            f0=modified(base,q,0);dp0=_gradient(f0['phase'],q)
            for sign in (-1,1):
                f=modified(base,q,sign);dp=_gradient(f['phase'],q)
                boundary.append(float((f['phase']-f0['phase']).abs().max()))
                boundary.append(float((dp[:,axis]-dp0[:,axis]).abs().max()))
    cells=np.random.default_rng(740329).choice(grid.cell_count,64,replace=False)
    ends=[fields(base,coordinates(grid,t,cells=cells)) for t in (A,B)]
    endpoint=(ends[1]['temperature']-ends[0]['temperature']+p.latent_ratio*(ends[1]['phase']-ends[0]['phase'])).detach().numpy()
    thermal={};jensen={};identity=[]
    for order in (16,32,64):
        nodes,weights=np.polynomial.legendre.leggauss(order);times=A+(B-A)*(nodes+1)/2;weights=weights/2
        integral=np.zeros(64);r2=np.zeros(64);delta_integrals={-1:np.zeros(64),1:np.zeros(64)}
        for t,w in zip(times,weights):
            q=coordinates(grid,float(t),cells=cells,requires_grad=True)
            f0=modified(base,q,0);dt=_gradient(f0['temperature'],q);dp=_gradient(f0['phase'],q)
            xy,incidence=face_quadrature(grid,cells)
            face=torch.tensor(np.column_stack([xy,np.full(len(xy),t)]),dtype=torch.float64,requires_grad=True)
            ft=_gradient(head_field(base,'temperature',face),face);idx=torch.tensor(incidence)
            flux=grid.dz*(ft[idx[:,1],0]-ft[idx[:,0],0])+grid.dx*(ft[idx[:,3],1]-ft[idx[:,2],1])
            stationary=p.volumetric_cooling*f0['temperature']-p.thermal_diffusivity*flux/(grid.dx*grid.dz)
            r=dt[:,2]+p.latent_ratio*dp[:,2]+stationary
            integral+=(B-A)*w*stationary.detach().numpy();r2+=w*r.detach().numpy()**2
            for sign in (-1,1):
                f=modified(base,q,sign);dpnew=_gradient(f['phase'],q)
                rn=dt[:,2]+p.latent_ratio*dpnew[:,2]+stationary
                expected=p.latent_ratio*(dpnew[:,2]-dp[:,2])
                identity.append(float((rn-r-expected).abs().max()))
                delta_integrals[sign]+=(B-A)*w*(rn-r).detach().numpy()
        c=endpoint+integral;bound=(c/(B-A))**2
        thermal[str(order)]=dict(C=c.tolist(),raw_square_lower_bound=bound.tolist(),
            mean_raw_square_lower_bound=float(bound.mean()),mean_scaled_lower_bound=float(bound.mean()/16),
            base_time_mean_raw_square=r2.tolist(),base_mean_raw_square=float(r2.mean()),
            max_integrated_counterexample_change={str(k):float(abs(v).max()) for k,v in delta_integrals.items()})
    changes={}
    for n,m in ((16,32),(32,64)):
        x=np.array(thermal[str(n)]['C']);y=np.array(thermal[str(m)]['C'])
        changes[f'{n}_to_{m}']=dict(max_absolute=float(abs(x-y).max()),
            relative_L2=float(np.linalg.norm(x-y)/max(np.linalg.norm(y),1e-12)))
    record=dict(status='REAL_BASE_ZERO_UPDATE_THEORY_DIAGNOSTICS',reference_read=False,optimizer_updates=0,
        counterexamples=records,visible_phase_max_change=obs_change,boundary_value_or_normal_derivative_max_change=max(boundary),
        electrical_counts=layer.backend.snapshot(),cell_seed=740329,cells=cells.tolist(),thermal=thermal,
        quadrature_changes=changes,latent_heat_difference_identity_max_error=max(identity),
        interpretation='finite observation/electric equivalence; not full PDE nonuniqueness or prediction improvement')
    assert obs_change==0 and max(boundary)<1e-12
    assert all(v['max_voltage_change']<1e-12 and v['max_joule_change']<1e-12 for row in records.values() for v in row.values())
    assert records['1.55']['1']['max_phase_change']>0
    save_json(RUN/'theory-diagnostics.json',record)
    np.savez_compressed(RUN/'theory-counterexample-fields.npz',x=grid.x_centers,z=grid.z_centers,**snapshots)
    print(json.dumps(dict(status=record['status'],thermal_mean_bound=thermal['64']['mean_raw_square_lower_bound'],
        quadrature_changes=changes,identity_error=max(identity),electrical=record['electrical_counts'])),flush=True)


if __name__=='__main__':main()
