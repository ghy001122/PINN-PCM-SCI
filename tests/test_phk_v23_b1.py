"""B1 validity tests on synthetic CPU fixtures; no scientific optimizer states."""
import copy
import json
from pathlib import Path
import numpy as np
import unittest
import torch

from pinn_pcm_sci.phk_v23_lf11 import axis_weights
from pinn_pcm_sci.phk_v23_b1_observations import visible_bundle,VisibleData,VisibleTimes,visible_baseline
from pinn_pcm_sci.phk_v23_b1 import B1Electric,B1Soft,validate,require_resource
from pinn_pcm_sci.phk_v23_lf11_elimination import ObservationTimes,TimeSampler
from pinn_pcm_sci.phk_v23_lf11_clean_confirmation import full_observation_head
from pinn_pcm_sci.phk_v23_lf11_followup_fit import fit_model
from pinn_pcm_sci.phk_v23_lf11_elimination_physics import grid_for,thermal_phase_residual
from pinn_pcm_sci.phk_v23_lf11_elimination_predict import baseline
from pinn_pcm_sci.phk_v23_lf11_v_continue import continued_lbfgs


def fixture():
    torch.set_num_threads(2)
    cfg=json.loads(Path('configs/phk_v23/lf11_b1_sprint.json').read_text())
    cfg.update(width=8,layers=2,grid=[8,4],adam_physics_cells=8,fixed_physics_cells=8,
               fixed_times_per_window=1,initial_points=4,boundary_counts_per_side=[2]*4)
    model=fit_model(cfg,adapter=True);grid=grid_for(model.physics,8,4)
    x=grid.x_centers[::2];z=grid.z_centers[::2]
    t=np.array([0.,.175,.34,1.,1.175,2.02,2.125,2.5])
    tt,zz,xx=np.meshgrid(t,z,x,indexing='ij');q=np.column_stack([xx.ravel(),zz.ravel(),tt.ravel()])
    a=np.random.default_rng(842).uniform(.1,.9,(len(q),3))
    a[:,0]*=.4;a[:,1]*=.3
    ns=len(x)*len(z);a[:ns,:2]=0
    a[:ns,2]=model.physics.initial_phase(torch.tensor(q[:ns])).numpy().ravel()
    p=(axis_weights(t)[:,None,None]*axis_weights(z,0.,1.)[None,:,None]*axis_weights(x,-1.,1.)[None,None,:]).ravel()
    raw=dict(x=x,z=z,time=t,coordinates=q,targets=a,global_probability=p)
    return cfg,model,grid,raw


def vector(model):
    return torch.cat([(p.grad if p.grad is not None else torch.zeros_like(p)).ravel() for p in model.parameters()])


def test_hidden_labels_cannot_change_export_sampling_calibration_or_baseline():
    cfg,model,grid,raw=fixture()
    hidden=(raw['coordinates'][:,2]>=1.01)&(raw['coordinates'][:,2]<=2.02)
    original=visible_bundle(raw)
    for replacement in (-971.,.99999999,np.nan):
        mutated=copy.deepcopy(raw);mutated['targets'][hidden,2]=replacement
        candidate=visible_bundle(mutated)
        for k in original:np.testing.assert_array_equal(candidate[k],original[k])
        da,db=VisibleData(arrays=original),VisibleData(arrays=candidate)
        oa=VisibleTimes(da,grid,model.physics,cfg,'cpu');ob=VisibleTimes(db,grid,model.physics,cfg,'cpu')
        assert oa.groups(np.random.default_rng(91),4)==ob.groups(np.random.default_rng(91),4)
        ba=visible_baseline(da,grid,np.array([0.,1.28,2.5]),model.physics)
        bb=visible_baseline(db,grid,np.array([0.,1.28,2.5]),model.physics)
        for k in ba:np.testing.assert_array_equal(ba[k],bb[k])
    # Actual common calibration computation on one untrained toy state/pool.
    state=model.state_dict();pool=TimeSampler(cfg,model.physics,grid,37).sample(fixed=True)
    left=B1Electric(cfg,state,da,'cpu','P_E');right=B1Electric(cfg,state,db,'cpu','P_E')
    va,pa=left.objective(left.obs.groups(),pool,dict(aE=1.,bE=1.),1.,backward=True)
    vb,pb=right.objective(right.obs.groups(),pool,dict(aE=1.,bE=1.),1.,backward=True)
    assert pa==pb and float(va)==float(vb)
    torch.testing.assert_close(vector(left.model),vector(right.model),rtol=0,atol=0)


def test_measure_normalization_and_exact_enumerated_importance_estimator():
    cfg,model,grid,raw=fixture();data=VisibleData(arrays=visible_bundle(raw))
    obs=VisibleTimes(data,grid,model.physics,cfg,'cpu')
    assert np.all(obs.proposal>0)
    np.testing.assert_allclose([obs.global_weight.sum(),obs.phase_weight.sum(),obs.proposal.sum()],1,rtol=1e-14)
    assert not np.any(obs.phase_weight[~obs.visible])
    q=raw['coordinates'];p=raw['global_probability'];m=data.visible&(q[:,2]>0)
    np.testing.assert_allclose(data.arrays['phase_global_probability'],p*m/(p*m).sum(),rtol=1e-14)
    # No interface cell spans either missing time boundary or the missing window.
    lo,hi=data.arrays['cell_lower'][:,2],data.arrays['cell_upper'][:,2]
    assert not np.any((lo<2.02)&(hi>1.01))
    full=np.zeros(3);expected=np.zeros(3)
    with torch.no_grad():
        for i in range(obs.nt):
            _,a=obs.loss(model,(i,1.),None,'P_F')
            _,b=obs.loss(model,(i,1/obs.proposal[i]),None,'P_F')
            full+=np.array([float(v) for v in a.values()])
            expected+=obs.proposal[i]*np.array([float(v) for v in b.values()])
    np.testing.assert_allclose(expected,full,rtol=1e-13,atol=1e-14)


def test_full_visible_compatibility_and_per_head_parent_loss():
    cfg,model,grid,raw=fixture();data=VisibleData(arrays=visible_bundle(raw,window=None))
    obs=VisibleTimes(data,grid,model.physics,cfg,'cpu')
    # Legacy data surface, with precisely the same original full visibility.
    old=copy.copy(data);old.arrays={**raw,'interface_probability':data.endpoint_prob}
    oldobs=ObservationTimes(old,grid,model.physics,cfg,'cpu')
    np.testing.assert_allclose(obs.proposal,oldobs.proposal,rtol=1e-14,atol=1e-15)
    for i in range(obs.nt):
        a,ap=obs.loss(model,(i,1.),None,'P_F');b,bp=oldobs.loss(model,(i,1.),None,'P_F')
        torch.testing.assert_close(a,b,rtol=1e-13,atol=1e-14)
    for head in ('potential','temperature','phase'):
        model.zero_grad(set_to_none=True);v=full_observation_head(model,obs,head);g=vector(model).clone()
        model.zero_grad(set_to_none=True);oldv=full_observation_head(model,oldobs,head);oldg=vector(model)
        torch.testing.assert_close(v,oldv,rtol=1e-13,atol=1e-14)
        torch.testing.assert_close(g,oldg,rtol=1e-12,atol=1e-13)
    original=baseline(old,grid,np.array([0.,.27,1.28,2.5]),model.physics)
    new=visible_baseline(data,grid,np.array([0.,.27,1.28,2.5]),model.physics)
    for k in new:np.testing.assert_allclose(new[k],original[k],rtol=2e-13,atol=2e-14)


def test_e_minus_de_is_exact_interior_value_and_gradient_with_voltage_feedback():
    cfg,model,grid,raw=fixture();data=VisibleData(arrays=visible_bundle(raw))
    e=B1Electric(cfg,model.state_dict(),data,'cpu','P_E')
    d=B1Electric(cfg,model.state_dict(),data,'cpu','D_E')
    sampler=TimeSampler(cfg,model.physics,grid,41)
    pool={'times':{1.175:dict(mass=1.,cells=np.arange(8),sides=sampler.boundaries(1.175,2))},'initial':np.array([[0.,.2]])}
    groups={1.175:(4,1.)};cal=dict(aE=.8,bE=1.3)
    ve,pe=e.objective(groups,pool,cal,.1,backward=True,counter='adam');ge=vector(e.model).clone()
    vd,pd=d.objective(groups,pool,cal,.1,backward=True,counter='complete');gd=vector(d.model).clone()
    for k in ('observation','obs_V','obs_T','obs_phase','boundary','initial'):assert pe[k]==pd[k]
    e.model.zero_grad(set_to_none=True);_,q,_=e.electric(1.175,True)
    res=thermal_phase_residual(e.model,grid,1.175,pool['times'][1.175]['cells'],q)
    interior=.1*sum((res[k]/cfg['pde_scales'][k]).square().mean() for k in ('thermal','phase'))/(3*cal['bE'])
    interior.backward();gi=vector(e.model)
    np.testing.assert_allclose(float(ve-vd),float(interior.detach()),rtol=1e-8,atol=1e-12)
    assert float(torch.linalg.vector_norm(ge-gd-gi)/torch.linalg.vector_norm(gi))<1e-7
    d.model.zero_grad(set_to_none=True);v,_,_=d.electric(1.175,True)
    _,parts=d.obs.loss(d.model,(4,1.),v,'D_E');parts['obs_V'].backward()
    for head in ('temperature','phase'):
        assert sum(float(p.grad.square().sum()) for p in d.model.heads[head].parameters() if p.grad is not None)>1e-24
    assert e.calls['adam_objective_gradient_evaluations']==1 and e.calls['complete_objective_gradient_evaluations']==0
    assert d.calls['complete_objective_gradient_evaluations']==1 and d.calls['adam_objective_gradient_evaluations']==0
    # F receives exactly the same visible loss and finite eta=1, without solves.
    soft=B1Soft(cfg,model.state_dict(),data,'cpu',1.)
    soft.objective(groups,pool,cal,.1,backward=True)
    assert soft.statistics()['electrical']['forward_solves']==0
    assert soft.eta==1. and soft.obs.groups()==e.obs.groups()


def test_lbfgs_trials_count_and_restore_last_accepted_state():
    p=torch.nn.Parameter(torch.tensor([4.],dtype=torch.float64));calls=0
    def objective():
        nonlocal calls
        calls+=1;loss=(p-1).square().sum();loss.backward();return loss
    result,_=continued_lbfgs([p],objective,1)
    assert result['evaluations']==calls==1 and result['accepted_steps']==0
    assert result['termination']=='EVALUATION_BUDGET_EXHAUSTED_TRIAL_ROLLED_BACK'
    assert float(p.detach())==4.


def test_scientific_config_and_resource_boundary():
    cfg=validate(json.loads(Path('configs/phk_v23/lf11_b1_sprint.json').read_text()))
    assert cfg['execution_order']==[[s,k] for s in (29,43) for k in ('E','D_E','F_raw')]
    assert cfg['budgets']['total_adam']==13800 and cfg['budgets']['total_complete_evaluations']==3000
    with unittest.TestCase().assertRaises(PermissionError):require_resource(None,'cpu',cfg)
    from unittest.mock import patch
    approved=dict(task_id=cfg['task_id'],authorized=True,instance_enabled=True,
        instance_id='authorized-instance',gpu_model='V100',staging_path='/tmp/b1',
        recovery_path='local-b1',shutdown_policy='recover then shut down',
        approval_record='user approved frozen work without cost budget',
        cost_policy='USER_NO_COST_LIMIT',wallclock_policy='FROZEN_WORK_ONLY')
    with patch('pinn_pcm_sci.phk_v23_b1.read',return_value=approved), patch('torch.cuda.is_available',return_value=True):
        assert require_resource('fixture.json','cuda:0',cfg) is approved
        approved['authorized']=False
        with unittest.TestCase().assertRaises(PermissionError):require_resource('fixture.json','cuda:0',cfg)


def test_masked_parent_phase_objective_never_transforms_missing_values():
    cfg,model,grid,raw=fixture();data=VisibleData(arrays=visible_bundle(raw))
    obs=VisibleTimes(data,grid,model.physics,cfg,'cpu')
    assert np.isnan(obs.target[:,:,2]).any()
    value=full_observation_head(model,obs,'phase',backward=True)
    assert torch.isfinite(value) and torch.isfinite(vector(model)).all()
    with torch.no_grad():
        complete=sum(obs.loss(model,group,None,'P_F')[1]['obs_phase']/3 for group in obs.groups().values())
    torch.testing.assert_close(value,complete,rtol=1e-13,atol=1e-14)


def test_window_quadrature_decomposes_history_and_uses_own_denominators():
    from types import SimpleNamespace
    from pinn_pcm_sci.phk_v23_b1_metrics import interval_weights,window_records
    t=np.linspace(0,2.5,1001)
    w=interval_weights(t,[(1.01,2.02)]);o=interval_weights(t,[(0,1.01),(2.02,2.5)])
    np.testing.assert_allclose(w+o,interval_weights(t,[(0,2.5)]),rtol=0,atol=1e-15)
    assert abs(w.sum()-1.01)<1e-14 and abs(o.sum()-1.49)<1e-14
    # Unequal reference amplitude inside/outside detects accidental global RMS.
    current=1+t
    zeros=np.zeros((1001,4));g=SimpleNamespace(cell_x=np.array([-.7,-.1,.1,.7]),cell_z=np.full(4,.2))
    ref=SimpleNamespace(time=t,grid=g,potential=zeros,temperature=zeros,phase=zeros,top_current=current,joule_power=current**2)
    fields=dict(potential=zeros+.01,temperature=zeros+.045,phase=zeros+.1)
    device=dict(top_current=current+.2,bottom_current=current+.3,joule_power=current**2+.4)
    cfg={'qualification_event':dict(roi=dict(abs_x_max=.35,z_min=0.,z_max=.4),phase_threshold=.5)}
    result=window_records(fields,ref,device,cfg)
    assert result['window']['normalizers']['top_current']!=result['full']['normalizers']['top_current']
    np.testing.assert_allclose(result['window']['metrics']['EI'],.2/np.sqrt(w@(current**2)/1.01),rtol=1e-13)
    assert abs(result['outside']['metrics']['Ephi']-.1)<1e-14


if __name__=='__main__':
    for name,function in list(globals().items()):
        if name.startswith('test_') and callable(function):
            function();print(name+': PASS',flush=True)
