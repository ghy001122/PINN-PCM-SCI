"""Electrical-block kernels for the sole conditional follow-up.

Importing this module or checking its gradients does not run an experiment.
The main endpoint-damage gate and three-node gate must both pass before any
scientific conditional training. No main-training source is modified here.
"""
from __future__ import annotations
import numpy as np
import torch

from .phk_v23_lf11 import tensor, pde_terms
from .phk_v23_lf11_joint import full_observation, initial_loss, boundary_components
from .phk_v22r_pinn import interior_diagnostic_terms, boundary_residuals
from .phk_v22r_training import PDE_SCALES, BOUNDARY_SCALES


def normalized_pde(model,batch):
    q,w,mass=batch
    terms=interior_diagnostic_terms(model,tensor(q))
    # sigma >= 1 under the frozen legal output ranges. The quotient is the
    # exact analytic log-conductivity residual and retains its full gradient.
    residuals={'electric':terms['electric_residual']/terms['conductivity'],
               'thermal':terms['thermal_residual'],'phase':terms['phase_residual']}
    mass,w=tensor(mass),tensor(w)
    return {key:torch.sum(mass*w*(value.ravel()/PDE_SCALES[key]).square())
            for key,value in residuals.items()}


def normalized_boundary(model,batches,config):
    parts={key:next(model.parameters()).new_zeros(()) for key in
           ('bc_insulation','bc_heater','bc_phase_no_flux','bc_thermal','bc_top_potential')}
    for mass,sides in zip(config['window_masses'],batches,strict=True):
        rows=[]
        for side,coords in sides.items():
            q=tensor(coords).requires_grad_(True)
            residuals=boundary_residuals(model,q,side=side)
            if any('insulating' in name for name in residuals):
                values=model(q)
                sigma=model.physics.conductivity(values[:,1:2],values[:,2:3])
                if side=='bottom':sigma=sigma[q[:,0].abs()>model.physics.heater_half_width]
            for name,residual in residuals.items():
                if 'insulating' in name:
                    group='bc_insulation';residual=residual/sigma
                elif name=='bc_potential_heater':group='bc_heater'
                elif name=='bc_phase_no_flux':group='bc_phase_no_flux'
                elif 'temperature' in name:group='bc_thermal'
                else:group='bc_top_potential'
                rows.append((group,(residual/BOUNDARY_SCALES[name]).square().mean()))
        for group,value in rows:parts[group]=parts[group]+mass*value/len(rows)
    return parts


def variant_parts(model,config,cal,normalization,role,pb,bc_ic,lam):
    normalized=role in ('N','D_N')
    factor=normalization['N_loss_scale'] if normalized else normalization['G_gradient_scale'] if role=='G' else 1.
    b=max(cal['b_star'],1e-12)
    bc=(normalized_boundary if normalized else boundary_components)(model,bc_ic[0],config)
    parts={key:lam*5*value/b*(factor if key=='bc_insulation' else 1.) for key,value in bc.items()}
    parts['initial']=lam*initial_loss(model,bc_ic[1])/b
    if role!='D_N':
        pde=normalized_pde(model,pb) if normalized else pde_terms(model,pb,'cpu')[0]
        parts.update({key:lam*value/(3*b)*(factor if key=='electric' else 1.) for key,value in pde.items()})
    return parts


def batch_objective(model,data,config,cal,normalization,role,step,idx,ng,pb,bc_ic):
    obs=data.loss(model,idx,ng,config,'cpu')
    lam=config['lambda_max']*min(step/config['lambda_ramp'],1.)
    parts=variant_parts(model,config,cal,normalization,role,pb,bc_ic,lam)
    parts['observation']=obs['observation']/max(cal['a_star'],1e-12)
    return parts,obs


def fixed_objective(model,data,config,cal,normalization,role,pools,backward=True):
    a,b=max(cal['a_star'],1e-12),max(cal['b_star'],1e-12)
    obs=full_observation(model,data,config,backward=backward,coefficient=1/a)
    total=obs['observation']/a;lam=config['lambda_max']
    normalized=role in ('N','D_N')
    factor=normalization['N_loss_scale'] if normalized else normalization['G_gradient_scale'] if role=='G' else 1.
    bc=(normalized_boundary if normalized else boundary_components)(model,pools['bc_ic'][0],config)
    bc_value=sum(value*(factor if key=='bc_insulation' else 1.) for key,value in bc.items())
    loss=lam*(5*bc_value+initial_loss(model,pools['bc_ic'][1]))/b
    if backward:loss.backward()
    total+=float(loss.detach())
    if role!='D_N':
        for lo in range(0,len(pools['pde'][0]),config['physics_chunk']):
            pb=tuple(v[lo:lo+config['physics_chunk']] for v in pools['pde'])
            pde=normalized_pde(model,pb) if normalized else pde_terms(model,pb,'cpu')[0]
            loss=lam*sum(value*(factor if key=='electric' else 1.) for key,value in pde.items())/(3*b)
            if backward:loss.backward()
            total+=float(loss.detach())
    return torch.tensor(total,dtype=torch.float64)


def electrical_block(model,config,cal,pools,normalized,backward=True):
    b=max(cal['b_star'],1e-12);lam=config['lambda_max'];total=0.
    bc=(normalized_boundary if normalized else boundary_components)(model,pools['bc_ic'][0],config)
    loss=lam*5*bc['bc_insulation']/b
    if backward:loss.backward()
    total+=float(loss.detach())
    for lo in range(0,len(pools['pde'][0]),config['physics_chunk']):
        pb=tuple(v[lo:lo+config['physics_chunk']] for v in pools['pde'])
        pde=normalized_pde(model,pb) if normalized else pde_terms(model,pb,'cpu')[0]
        loss=lam*pde['electric']/(3*b)
        if backward:loss.backward()
        total+=float(loss.detach())
    return total


def calibrate(model,config,cal,pools):
    saved={}
    for normalized in (False,True):
        model.zero_grad(set_to_none=True)
        value=electrical_block(model,config,cal,pools,normalized)
        gradient=torch.cat([(p.grad if p.grad is not None else torch.zeros_like(p)).ravel() for p in model.parameters()])
        saved[normalized]=(value,float(gradient.norm()))
    r,gr=saved[False];n,gn=saved[True]
    floor=config['calibration_denominator_min']
    identifiable=bool(np.isfinite([r,n,gr,gn]).all() and min(r,n,gr,gn)>floor)
    result={'identifiable':identifiable,'raw_parent_block_loss':r,'normalized_parent_block_loss_unscaled':n,
            'raw_parent_block_gradient_norm':gr,'normalized_parent_block_gradient_norm_unscaled':gn,
            'N_loss_scale':r/n if identifiable else None,
            'G_gradient_scale':(r/n)*gn/gr if identifiable else None,
            'full_parameters':True,'actual_interior_and_BC_coefficients':True,'reference_read':False,
            'frozen_at_common_parent':True,'pool_seed':pools.get('seed')}
    model.zero_grad(set_to_none=True)
    return result
