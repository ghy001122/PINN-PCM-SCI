"""Focused artificial-model tests for the newly exposed soft comparison."""
import numpy as np
import torch
from pinn_pcm_sci.phk_v23_lf11_training_coupling import SoftExperiment,BLOCKS,gradient_vector
from pinn_pcm_sci.phk_v23_lf11_elimination import Experiment,TimeSampler
from pinn_pcm_sci.phk_v23_lf11_followup_fit import fit_model
from pinn_pcm_sci.phk_v23_lf11_elimination_physics import grid_for,coordinates,fields
from pinn_pcm_sci.phk_v23_lf11_electric_layer import ElectricalLayer


def test_soft_weight_one_and_complete_gradient_match_existing_interface():
    torch.set_num_threads(2)
    cfg=dict(seed=17,width=8,layers=2,pde_scales=dict(electric=1,thermal=4,phase=5))
    exp=object.__new__(SoftExperiment)
    exp.c,exp.role,exp.device,exp.eta=cfg,'P_F','cpu',1.
    exp.model=fit_model(cfg,adapter=True)
    exp.parameters=list(exp.model.parameters())
    exp.grid=grid_for(exp.model.physics,8,4)
    exp.layer=ElectricalLayer(exp.grid,exp.model.physics.heater_width_fraction)
    exp.calls={k:0 for k in ('audit_objective_gradient_evaluations','audit_objective_evaluations')}
    exp.work={k:0 for k in ('full_grid_network_evaluations','explicit_face_evaluations','thermal_phase_groups','boundary_groups','observation_groups')}
    class Observations:
        def groups(self): return {.175:(0,1.)}
        def loss(self,model,group,voltage,role):
            f=fields(model,coordinates(exp.grid,.175),potential=True)
            parts={'obs_V':((f['potential']-.3)/.72).square().mean(),
                   'obs_T':((f['temperature']-.1)/.45).square().mean(),
                   'obs_phase':(f['phase']-.3).square().mean()}
            return sum(parts.values())/3,parts
    exp.obs=Observations()
    sampler=TimeSampler(cfg,exp.model.physics,exp.grid,7123)
    pool={'times':{.175:dict(mass=1.,cells=np.arange(12),sides=sampler.boundaries(.175,4))},
          'initial':np.array([[0.,.2]])}
    cal=dict(aE=.8,bE=1.3)
    exp.model.zero_grad(set_to_none=True)
    old,_=Experiment.objective(exp,exp.obs.groups(),pool,cal,.1,backward=True)
    gold=gradient_vector(exp)
    exp.model.zero_grad(set_to_none=True)
    new,_=exp.objective(exp.obs.groups(),pool,cal,.1,backward=True)
    np.testing.assert_allclose(float(new),float(old),rtol=1e-13,atol=1e-14)
    np.testing.assert_allclose(gradient_vector(exp),gold,rtol=1e-10,atol=1e-11)
    total=np.zeros_like(gold);loss=0.
    for block in BLOCKS:
        exp.model.zero_grad(set_to_none=True)
        value,_=exp.objective(exp.obs.groups(),pool,cal,.1,backward=True,blocks={block:1.})
        total+=gradient_vector(exp);loss+=float(value)
    np.testing.assert_allclose(total,gold,rtol=1e-10,atol=1e-11)
    np.testing.assert_allclose(loss,float(old),rtol=1e-13)
    # Full parameter direction tests the explicit sigma and q paths as well.
    direction=np.random.default_rng(33).normal(size=len(gold));direction/=np.linalg.norm(direction)
    originals=[p.detach().clone() for p in exp.parameters]
    def shifted(amount):
        offset=0
        with torch.no_grad():
            for p,initial in zip(exp.parameters,originals):
                d=torch.tensor(direction[offset:offset+p.numel()].reshape(p.shape))
                p.copy_(initial+amount*d);offset+=p.numel()
        return float(exp.objective(exp.obs.groups(),pool,cal,.1)[0])
    eps=1e-5
    finite=(shifted(eps)-shifted(-eps))/(2*eps)
    shifted(0.)
    np.testing.assert_allclose(finite,np.dot(gold,direction),rtol=2e-5,atol=1e-7)
    assert exp.statistics()['electrical']['forward_solves']==0
    assert exp.statistics()['electrical']['adjoint_solves']==0
    print('SOFT_INTERFACE_FIVE_BLOCK_AND_EXPLICIT_GRADIENT_PASS')


def test_two_projected_controls_must_pass_the_same_layer():
    import json
    from pathlib import Path
    from pinn_pcm_sci.phk_v23_lf11_training_coupling_evaluate import comparisons
    cfg=json.loads(Path('configs/phk_v23/lf11_training_coupling_sprint.json').read_text())
    def record(phase=1.,device=1.):
        m={k:1. for k in ('S','Ephi','ET','EV','EI','bottom_current_NRMSE','power_trace_NRMSE')}
        m.update(S=phase,Ephi=phase,EI=device,bottom_current_NRMSE=device,power_trace_NRMSE=device)
        return dict(valid=True,metrics=m,training_budget_complete=True)
    records={'P_E':record(),'F_raw/projected':record(phase=1.2),'F_bal/projected':record(device=1.2)}
    assert not comparisons(records,cfg)['training_coupling_signal']
    records['F_bal/projected']=record(phase=1.2,device=1.2)
    assert comparisons(records,cfg)['training_coupling_supported_layers']['A']
    records['F_bal/projected']['training_budget_complete']=False
    assert not comparisons(records,cfg)['training_coupling_signal']
    print('TWO_VALID_COMPLETE_CONTROLS_SAME_LAYER_REQUIRED_PASS')


if __name__=='__main__':
    test_soft_weight_one_and_complete_gradient_match_existing_interface()
    test_two_projected_controls_must_pass_the_same_layer()
