"""The new finite protocol preserves the causal prefix and cannot add a pulse."""
import numpy as np
import torch
from pinn_pcm_sci.phk_v23_lf11_protocol import CASE, case_physics, waveform, powered_count
from pinn_pcm_sci.phk_v22r_training import load_case_physics
from pinn_pcm_sci.phk_v23_lf11_protocol_reference import FiniteOracle
from pinn_pcm_sci.phk_benchmark import PhkResolution


def test_finite_protocol_prefix_shift_and_tail():
    old,_,_=load_case_physics();new=case_physics(old,CASE)
    prefix=torch.linspace(0,1.0,401,dtype=torch.float64)
    torch.testing.assert_close(new.waveform(prefix),old.waveform(prefix),atol=1e-15,rtol=1e-14)
    local=torch.linspace(.0025,.3475,139,dtype=torch.float64)
    torch.testing.assert_close(new.waveform(local+1.01),old.waveform(local+1.25),atol=3e-15,rtol=1e-12)
    tail=torch.linspace(2.02,2.5,193,dtype=torch.float64)
    assert torch.count_nonzero(new.waveform(tail))==0
    assert torch.count_nonzero(old.waveform(tail))==0
    assert powered_count(CASE)==278
    lengths=np.diff(CASE['windows'],axis=1).ravel()
    np.testing.assert_allclose(lengths/2.5,CASE['window_masses'],atol=1e-15)
    assert sum(CASE['window_masses'])==1.0


def test_reference_and_model_consume_same_finite_spec():
    resolution=PhkResolution('new',80,40,.0025,2.5,2,'LF11_FINITE_PROTOCOL_AUTHORIZED_RESOLUTION')
    oracle=FiniteOracle(CASE,resolution)
    old,_,_=load_case_physics();new=case_physics(old,CASE)
    times=torch.tensor([0,.05,.27,.35,1.,1.01,1.035,1.06,1.28,1.36,2.045,2.5],dtype=torch.float64)
    np.testing.assert_array_equal([oracle.waveform(float(t)) for t in times],new.waveform(times).numpy())
    assert new.period==1.01 and new.time_end==2.5
    # Known physical IC and all non-waveform coefficients remain unchanged.
    q=torch.tensor([[0.,.1,0.],[.3,.2,1.2]],dtype=torch.float64)
    torch.testing.assert_close(new.initial_phase(q),old.initial_phase(q),atol=0,rtol=0)
    torch.testing.assert_close(new.normalize(q),old.normalize(q),atol=0,rtol=0)


def test_tail_cannot_create_a_second_cycle_event():
    from pinn_pcm_sci.phk_v22r_evaluator import _event_summary
    time=np.linspace(0,2.5,1001)
    phase=np.zeros((len(time),2));phase[time>2.1,0]=.9
    result=_event_summary(phase,time=time,roi=np.array([True,False]),period=1.01,
                          phase_threshold=.5,event_fraction=.02)
    assert all(c['event_time'] is None for c in result['cycles'])
    assert max(result['roi_fraction'])==1.0


def test_history_reports_keep_signed_energy_and_state_errors():
    from types import SimpleNamespace
    from pinn_pcm_sci.phk_v23_lf11_protocol_evaluate import history_diagnostics
    old,_,_=load_case_physics();physics=case_physics(old,CASE)
    time=np.linspace(0,2.5,1001);shape=(len(time),2)
    truth=np.zeros(shape);fields={'temperature':truth+.02,'phase':truth+.03}
    drive=physics.waveform(torch.tensor(time,dtype=torch.float64)).numpy()
    ref=SimpleNamespace(time=time,temperature=truth,phase=truth,
                        top_current=drive,joule_power=drive**2)
    result=history_diagnostics(fields,ref,{'joule_power':1.1*drive**2,'top_current':drive},
                              physics,{'case_spec':CASE},np.array([True,False]))
    assert result['tail_does_not_extend_recovery']
    for pulse in result['per_pulse']:
        np.testing.assert_allclose(pulse['power_NRMSE'],.1,atol=1e-14)
        np.testing.assert_allclose(pulse['relative_signed_energy_error'],.1,atol=1e-14)
    np.testing.assert_allclose(result['prepulse']['temperature']['ROI_RMS_error'],.02)
    assert result['tail_max_absolute_drive']==0.


def test_new_case_keeps_random_state_and_T_phase_parameterization():
    from pinn_pcm_sci.phk_v23_lf11_followup_fit import fit_model
    cfg={'seed':29,'width':64,'layers':4}
    old=fit_model(cfg,adapter=True)
    new=fit_model({**cfg,'case_spec':CASE},adapter=True)
    assert all(torch.equal(old.state_dict()[k],v) for k,v in new.state_dict().items())
    q=torch.tensor([[0.,.1,t] for t in (0.,.1,1.01,1.185,1.9,2.045)],dtype=torch.float64)
    with torch.no_grad():
        a,b=old(q),new(q)
    torch.testing.assert_close(a[:,1:],b[:,1:],atol=0,rtol=0)
    assert not torch.equal(a[:,0],b[:,0])
