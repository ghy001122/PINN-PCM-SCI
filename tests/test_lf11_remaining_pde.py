"""New block-composition behavior only; no historical scientific run repeated."""
import numpy as np
import torch
from pinn_pcm_sci.phk_v23_lf11_remaining_pde import FixedExperiment, coefficients, vector
from pinn_pcm_sci.phk_v23_lf11_elimination import Experiment, TimeSampler
from pinn_pcm_sci.phk_v23_lf11_followup_fit import fit_model
from pinn_pcm_sci.phk_v23_lf11_elimination_physics import grid_for, coordinates, fields
from pinn_pcm_sci.phk_v23_lf11_electric_layer import ElectricalLayer


def test_fixed_blocks_reproduce_old_joint_functional_and_complete_gradient():
    torch.set_num_threads(2)
    config=dict(seed=17,width=8,layers=2,pde_scales=dict(thermal=4,phase=5))
    exp=object.__new__(FixedExperiment)
    exp.c,exp.role,exp.device=config,'P_E','cpu'
    exp.model=fit_model(config,adapter=True)
    for p in exp.model.heads['potential'].parameters(): p.requires_grad_(False)
    exp.parameters=[p for p in exp.model.parameters() if p.requires_grad]
    exp.grid=grid_for(exp.model.physics,8,4)
    exp.layer=ElectricalLayer(exp.grid,exp.model.physics.heater_width_fraction)
    exp.calls={'complete_objective_gradient_evaluations':0,'audit_objective_evaluations':0,'audit_objective_gradient_evaluations':0}
    class ArtificialObservations:
        def groups(self): return {.175:(0,1.)}
        def loss(self,model,group,voltage,role):
            f=fields(model,coordinates(exp.grid,.175))
            parts={'obs_V':((voltage-.3)/.72).square().mean(),
                   'obs_T':((f['temperature']-.1)/.45).square().mean(),
                   'obs_phase':(f['phase']-.3).square().mean()}
            return sum(parts.values())/3,parts
    exp.obs=ArtificialObservations()
    sampler=TimeSampler(config,exp.model.physics,exp.grid,7123)
    pool={'times':{.175:dict(mass=1.,cells=np.arange(12),sides=sampler.boundaries(.175,4))},'initial':np.array([[0.,.2]])}
    cal=dict(aE=.8,bE=1.3)
    exp.model.zero_grad(set_to_none=True)
    old,_=Experiment.objective(exp,exp.obs.groups(),pool,cal,.1,backward=True)
    g_old=vector(exp)
    exp.model.zero_grad(set_to_none=True)
    new,_=exp.fixed(pool,cal,coefficients(1.),backward=True)
    np.testing.assert_allclose(float(old),float(new),rtol=1e-13,atol=1e-14)
    np.testing.assert_allclose(g_old,vector(exp),rtol=1e-10,atol=1e-12)
    gradient=np.zeros_like(g_old)
    value=0.
    for block in ('observation','boundary','thermal','phase'):
        exp.model.zero_grad(set_to_none=True)
        loss,_=exp.fixed(pool,cal,{block:1.},backward=True)
        gradient+=vector(exp);value+=float(loss)
    np.testing.assert_allclose(gradient,g_old,rtol=1e-10,atol=1e-12)
    np.testing.assert_allclose(value,float(old),rtol=1e-13,atol=1e-14)
    print('NEW_FIXED_OBJECTIVE_AND_FULL_BLOCK_GRADIENT_COMPOSITION_PASS')


def test_reference_decision_rejects_win_over_degraded_continued_control():
    import json
    from pathlib import Path
    from pinn_pcm_sci.phk_v23_lf11_remaining_pde_evaluate import conditional_rule
    cfg=json.loads(Path('configs/phk_v23/lf11_remaining_pde_sprint.json').read_text())
    cfg['roles']=['D_C','P1','P_kappa']
    def rec(error):
        return {'valid':True,'metrics':{k:error for k in ('S','Ephi','ET','EI','EV','bottom_current_NRMSE','power_trace_NRMSE')}}
    records={r:rec(x) for r,x in dict(D_C=2.,P1=1.4,P_kappa=1.2,D_E=1.,B_E=3.).items()}
    decision=conditional_rule(records,cfg)
    assert decision['comparisons']['P1']['D_C']['A']['passed']
    assert decision['selected_simple_first'] is None
    records['P1']=rec(.9);records['P_kappa']=rec(.8)
    decision=conditional_rule(records,cfg)
    assert decision['selected_simple_first']=='P1'
    assert not decision['run_P_F']
    print('ORIGINAL_STRONG_PARENT_GUARD_AND_SIMPLE_FIRST_DECISION_PASS')


if __name__=='__main__':
    test_fixed_blocks_reproduce_old_joint_functional_and_complete_gradient()
    test_reference_decision_rejects_win_over_degraded_continued_control()
