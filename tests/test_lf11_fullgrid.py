"""Only the new electric spatial integral and unchanged sampler are tested."""
import copy
import json
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import torch
from pinn_pcm_sci.phk_v23_lf11_training_coupling import SoftExperiment
from pinn_pcm_sci.phk_v23_lf11_elimination import TimeSampler,serialize_pool
from pinn_pcm_sci.phk_v23_lf11_followup_fit import fit_model
from pinn_pcm_sci.phk_v23_lf11_elimination_physics import grid_for


def test_full_volume_mean_and_complete_gradient_not_factor_25():
    e=object.__new__(SoftExperiment)
    e.device='cpu';e.grid=SimpleNamespace(cell_count=3200)
    e.c={'electric_spatial_reduction':'full','pde_scales':{'electric':1.}}
    r=torch.linspace(-.3,2.,3200,dtype=torch.float64,requires_grad=True)
    indices=np.arange(128)
    value=e.electric_square_mean(r,indices)
    volume=torch.full_like(r,2./3200)
    expected=(volume*r.square()).sum()/volume.sum()
    g=torch.autograd.grad(value,r)[0]
    torch.testing.assert_close(value,expected,rtol=1e-14,atol=1e-14)
    torch.testing.assert_close(g,2*r.detach()/3200,rtol=1e-14,atol=1e-14)
    # The same precomputed global operator gives the old result by default.
    del e.c['electric_spatial_reduction']
    torch.testing.assert_close(e.electric_square_mean(r,indices),r[indices].square().mean())


def test_incomplete_training_cannot_be_a_successful_comparison():
    from pinn_pcm_sci.phk_v23_lf11_fullgrid_evaluate import pair
    incomplete={'training_budget_complete':False}
    assert all(not v['passed'] for v in pair(incomplete,{},{}).values())
    assert all(not v['passed'] for v in pair({},incomplete,{}).values())


def test_thermal_phase_samples_and_rng_are_identical():
    cfg=json.loads(Path('configs/phk_v23/lf11_training_coupling_sprint.json').read_text())
    new=copy.deepcopy(cfg);new['electric_spatial_reduction']='full'
    model=fit_model(dict(seed=17,width=8,layers=2),adapter=True)
    grid=grid_for(model.physics,80,40)
    old=TimeSampler(cfg,model.physics,grid,cfg['sampling_seed'])
    full=TimeSampler(new,model.physics,grid,cfg['sampling_seed'])
    for fixed in (False,False,True,False):
        p,q=old.sample(fixed),full.sample(fixed)
        assert serialize_pool(p)==serialize_pool(q)
        assert old.rng.bit_generator.state==full.rng.bit_generator.state
        assert all(len(v['cells'])==128 for v in q['times'].values())


def test_selector_preserves_device_and_field_tradeoffs():
    from pinn_pcm_sci.phk_v23_lf11_fullgrid_evaluate import select_soft
    cfg=json.loads(Path('configs/phk_v23/lf11_fullgrid_sprint.json').read_text())
    def record(current,power,phase=1.):
        metrics={k:1. for k in ('S','Ephi','ET','EV','EI')}
        metrics.update(bottom_current_NRMSE=current,power_trace_NRMSE=power,Ephi=phase)
        return dict(valid=True,training_budget_complete=True,metrics=metrics)
    records={'F_raw/projected':record(1.,1.),'F_bal/projected':record(2.,2.),
             'F_full/projected':record(.8,1.1)}
    decision=select_soft(records,cfg)
    assert decision['selected'] is None
    assert set(decision['nondominated'])=={'F_raw','F_full'}
    records['F_full/projected']=record(.8,.8)
    assert select_soft(records,cfg)['selected']=='F_full'
    records['F_full/projected']=record(.8,.8,phase=1.3)
    assert select_soft(records,cfg)['selected'] is None
    records['F_full/projected']['training_budget_complete']=False
    assert select_soft(records,cfg)['selected']=='F_raw'


def test_clean_observation_head_gradients_add_to_original_full_target():
    from pinn_pcm_sci.phk_v23_lf11_elimination import ObservationTimes
    from pinn_pcm_sci.phk_v23_lf11_clean_confirmation import observation_objective,full_observation_head
    torch.set_num_threads(2)
    cfg=dict(seed=29,width=8,layers=2,phase_logit_divisor=36.84136146790473,phase_logit_epsilon=1e-8)
    model=fit_model(cfg,adapter=True);grid=grid_for(model.physics,8,4)
    times=np.array([0.,.175,.8])
    q=np.concatenate([np.column_stack([grid.cell_x,grid.cell_z,np.full(grid.cell_count,t)]) for t in times])
    targets=np.broadcast_to([.2,.1,.2],q.shape).copy()
    data=SimpleNamespace(arrays={'time':times},coordinates=q,targets=targets,
        prob=np.ones(len(q))/len(q),has_interface=False)
    obs=ObservationTimes(data,grid,model.physics,cfg,'cpu')
    def grad():
        return torch.cat([(p.grad if p.grad is not None else torch.zeros_like(p)).reshape(-1) for p in model.parameters()]).detach().clone()
    model.zero_grad(set_to_none=True)
    total,_=observation_objective(model,obs,obs.groups(),backward=True);full=grad()
    parts=0.;accum=torch.zeros_like(full)
    for head in ('potential','temperature','phase'):
        model.zero_grad(set_to_none=True)
        value,_=observation_objective(model,obs,obs.groups(),head,True)
        parts+=float(value);ghead=grad();accum+=ghead
        model.zero_grad(set_to_none=True)
        chunked=full_observation_head(model,obs,head,chunk=17)
        torch.testing.assert_close(grad(),ghead,rtol=1e-10,atol=1e-12)
        np.testing.assert_allclose(float(chunked),float(value),rtol=1e-13)
    torch.testing.assert_close(accum,full,rtol=1e-10,atol=1e-12)
    np.testing.assert_allclose(parts,float(total),rtol=1e-14)
