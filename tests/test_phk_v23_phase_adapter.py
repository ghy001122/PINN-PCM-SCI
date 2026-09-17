"""Focused checks for the one new phase representation interface."""
import copy
import io
import json
from pathlib import Path
import numpy as np
import torch
from pinn_pcm_sci.phk_v23_phase_adapter import install, load_model
from pinn_pcm_sci.phk_v23_lf11_followup_fit import fit_model
from pinn_pcm_sci.phk_v23_lf11_elimination_physics import fields, grid_for, coordinates, thermal_phase_residual
from pinn_pcm_sci.phk_v23_lf11_electric_layer import ElectricalLayer
from pinn_pcm_sci.phk_v22r_pinn import _gradient


def config():
    cfg=json.loads(Path('configs/phk_v23/lf11_phase_adapter_sprint.json').read_text())
    return dict(cfg,seed=29,phase_gate_cg=.35)


def test_zero_insertion_and_serialized_full_field_interface():
    cfg=config();base=fit_model(cfg,adapter=True)
    q=torch.tensor([[-.31,.03,0.],[.12,.16,.19],[.07,.35,1.24],[.21,.82,2.2]],dtype=torch.float64)
    original=fields(base,q,potential=True)
    residuals=[]
    for role in ('E_C','E_R','E_I'):
        m=install(copy.deepcopy(base),role,cfg)
        f=fields(m,q,potential=True)
        for key in original:torch.testing.assert_close(f[key],original[key],rtol=0,atol=0)
        torch.testing.assert_close(m(q),torch.column_stack([f[k] for k in ('potential','temperature','phase')]),rtol=0,atol=0)
        if role!='E_C':
            residuals.append(copy.deepcopy(m.heads['phase'].residual.state_dict()))
            assert sum(p.numel() for p in m.heads['phase'].residual.parameters())==1217
            with torch.no_grad():m.heads['phase'].residual[-1].weight.fill_(.007)
        store=io.BytesIO();torch.save(m.state_dict(),store);store.seek(0)
        reloaded=load_model(cfg,torch.load(store,weights_only=False),role,'cpu')
        torch.testing.assert_close(m(q),reloaded(q),rtol=0,atol=0)
        f=fields(m,q)
        assert bool(((f['phase']>=0)&(f['phase']<=1)).all())
        torch.testing.assert_close(f['phase'][0],base.physics.initial_phase(q)[0,0],rtol=1e-12,atol=1e-15)
        initial=m.physics.initial_phase(q).clamp(1e-8,1-1e-8).ravel()
        torch.testing.assert_close(f['phase'],torch.sigmoid(torch.logit(initial)+f['delta_logit']),rtol=0,atol=0)
    assert all(torch.equal(residuals[0][k],residuals[1][k]) for k in residuals[0])


def test_gate_coordinate_derivatives_and_complete_electrothermal_vjp():
    cfg=config();m=install(fit_model(cfg,adapter=True),'E_I',cfg)
    with torch.no_grad():m.heads['phase'].residual[-1].weight.fill_(.004)
    assert not any(p.requires_grad for p in m.heads['phase'].frozen_parent.parameters())
    q=torch.tensor([[.037,.14,.19],[-.19,.12,1.17]],dtype=torch.float64,requires_grad=True)
    y=fields(m,q)['phase'];first=_gradient(y,q);second=_gradient(first[:,0],q)[:,0]
    eps=1e-4;plus=q.detach().clone();minus=plus.clone();plus[:,0]+=eps;minus[:,0]-=eps
    finite=(fields(m,plus)['phase']-2*y.detach()+fields(m,minus)['phase'])/eps**2
    torch.testing.assert_close(second,finite,rtol=2e-4,atol=2e-7)
    gate=m.heads['phase'].gate(m.physics.normalize(q))
    assert torch.isfinite(_gradient(gate,q)).all() and float(_gradient(gate,q).abs().max())>1e-10
    grid=grid_for(m.physics,8,4);layer=ElectricalLayer(grid,m.physics.heater_width_fraction)
    def objective():
        f=fields(m,coordinates(grid,.19));sigma=m.physics.conductivity(f['temperature'],f['phase'])
        v,heat=layer(sigma,.72)
        r=thermal_phase_residual(m,grid,.19,np.array([0,3,11,19]),heat)
        return v.square().mean()+.003*heat.square().mean()+1e-4*r['thermal'].square().mean()+1e-4*r['phase'].square().mean()
    p=m.heads['phase'].residual[-1].weight
    m.zero_grad(set_to_none=True);value=objective();value.backward();grad=p.grad.clone()
    direction=torch.linspace(-.2,.3,p.numel(),dtype=torch.float64).reshape_as(p)
    analytic=float((grad*direction).sum());saved=p.detach().clone();h=1e-5
    with torch.no_grad():p.copy_(saved+h*direction)
    plus=float(objective().detach())
    with torch.no_grad():p.copy_(saved-h*direction)
    minus=float(objective().detach())
    with torch.no_grad():p.copy_(saved)
    numeric=(plus-minus)/(2*h)
    np.testing.assert_allclose(analytic,numeric,rtol=1e-5,atol=1e-8)
    assert layer.backend.counts.forward_solves==3 and layer.backend.counts.adjoint_solves==1
    assert all(p.grad is None for p in m.heads['phase'].frozen_parent.parameters())
