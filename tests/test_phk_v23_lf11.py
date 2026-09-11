"""New-interface checks only; no optimizer updates or reference access."""
import json
import unittest
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import torch

from pinn_pcm_sci.phk_v23_lf11 import (
    SparseData, PhysicsSampler, build_model, tensor, objective, pde_terms, axis_weights,
)
from pinn_pcm_sci.phk_v23_lf11_readout import make_grid, readout, interpolate_sparse

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT/"configs/phk_v23/lf11_sprint.json").read_text())
BUNDLE = ROOT/"paper/paper_v24/evidence/input/sparse.npz"
torch.set_num_threads(2)


def test_sparse_boundary_and_quadrature():
    d = SparseData(BUNDLE)
    assert d.coordinates.shape == (29106, 3)
    assert np.isclose(d.prob.sum(), 1)
    assert np.isclose(d.endpoint_prob.sum(), 1)
    assert np.all(d.endpoint_prob[d.coordinates[:, 2] == 0] == 0)
    assert len(d.arrays["cell_lower"]) == 337
    assert np.allclose(axis_weights(np.array([0., .2, 1.])), [.1, .5, .4])


def test_proposal_membership_and_measure():
    d = SparseData(BUNDLE); model = build_model(CONFIG)
    s = PhysicsSampler(d, CONFIG, 1702, model.physics)
    q, w, m = s.interior(True, multiplier=32)
    assert abs(np.sum(m*w)-1) < .012
    assert np.all(w > 0) and np.max(w) <= 4/3+1e-14
    sample = q[::max(1, len(q)//50)]
    brute = np.any(np.all(sample[:, None] >= d.arrays["cell_lower"], axis=2) &
                   np.all(sample[:, None] < d.arrays["cell_upper"], axis=2), axis=1)
    assert np.array_equal(s.in_B(sample), brute)
    other = PhysicsSampler(d, CONFIG, 1702, model.physics)
    assert all(np.array_equal(a, b) for a, b in zip((q,w,m), other.interior(True, multiplier=32)))


def test_four_complete_losses_backpropagate_and_control_excludes_pde():
    d = SparseData(BUNDLE); model = build_model(CONFIG)
    c = dict(CONFIG, interior_counts=[8, 8, 8, 8], boundary_counts_per_side=[2, 2, 2, 2], initial_points=8)
    s = PhysicsSampler(d, c, 7, model.physics)
    idx, ng = d.indices(np.random.default_rng(8), 64)
    batch = s.interior(True)
    pde, pq = pde_terms(model, batch, "cpu")
    c0 = float((pde["phase"]/pq).detach())
    cal = {"a0": .1, "b0": 1., "c0": c0}
    bc_ic = s.boundary_initial()
    states = {k: v.clone() for k,v in model.state_dict().items()}
    for role in ("D_B", "P_U", "P_I", "P_M"):
        model.zero_grad(set_to_none=True)
        loss, terms = objective(model, d, c, "cpu", idx, ng, batch, bc_ic, role, 200, cal)
        assert torch.isfinite(loss)
        loss.backward()
        assert all(p.grad is None or torch.isfinite(p.grad).all() for p in model.parameters())
        assert all(any(p.grad is not None and torch.any(p.grad != 0) for p in head.parameters()) for head in model.heads.values())
        if role == "D_B": assert "pde_objective" not in terms
        if role in ("P_I", "P_M"):
            expected = sum(terms["pde_"+name] for name in ("electric", "thermal", "phase"))/3
            assert torch.allclose(terms["pde_objective"], expected)
    assert all(torch.equal(states[k], v) for k,v in model.state_dict().items())


def test_face_readout_affine_solution_and_nonconservation_is_visible():
    physics = build_model(CONFIG).physics
    # A manufactured all-width electrode, constant sigma=1 problem is a
    # readout unit check, not a change to the research device.
    p = SimpleNamespace(**{**vars(physics), "heater_width_fraction": 1.0,
                            "conductivity_temperature_gain": 0., "conductivity_phase_ratio": 1.})
    grid = make_grid(np.arange(8), np.arange(6), p)
    v = grid.cell_z[None].copy(); zero = np.zeros_like(v)
    r = readout(v, zero, zero, grid, [1.], p)
    assert np.allclose(r["top_current"], 2)
    assert np.allclose(r["bottom_current"], 2)
    assert np.allclose(r["joule_power"], 2)
    assert np.max(r["electric_fv_rms"]) < 1e-12
    r_bad = readout(.5*v, zero, zero, grid, [1.], p)
    assert abs(r_bad["power_defect"][0]) > .1
    assert r_bad["top_current"][0] != r_bad["bottom_current"][0]


def test_baseline_extends_to_actual_boundaries_without_teacher_readout():
    d = SparseData(BUNDLE); p = build_model(CONFIG).physics
    x = np.array([p.x_min, 0., p.x_max]); z = np.array([p.z_min, .5, p.z_max])
    times = np.unique(np.r_[d.arrays["time"][::25], .35, .355, 1.60, 1.605])
    for kind in ("B_L", "B_P", "B_logit"):
        f = interpolate_sparse(d, x, z, times, p, kind)
        assert all(np.isfinite(v).all() for v in f.values())
        top = f["potential"].reshape(len(times), 3, 3)[:, -1]
        assert np.allclose(top, p.waveform(tensor(times)).numpy()[:, None], atol=1e-10)
        assert np.allclose(f["potential"].reshape(len(times), 3, 3)[:, 0, 1], 0)
        assert f["phase"].min() >= 0 and f["phase"].max() <= 1


def test_evaluation_uses_full_domain_pulse_support_and_separate_device_gate():
    from pinn_pcm_sci.phk_v23_lf11_evaluation import metrics, comparison
    p = build_model(CONFIG).physics
    grid = make_grid(np.arange(8), np.arange(6), p)
    time = np.linspace(0, 2.5, 501)
    voltage = p.waveform(tensor(time)).numpy()
    potential = voltage[:,None]*grid.cell_z[None,:]
    temperature = np.zeros_like(potential)
    phase = np.full_like(potential, .03)
    pulse = ((time >= .1)&(time <= .3))|((time >= 1.35)&(time <= 1.55))
    phase[np.ix_(pulse,[0,3])] = .8  # cell 0 is outside the event ROI.
    trace = readout(potential, temperature, phase, grid, voltage, p)
    reference = SimpleNamespace(time=time, grid=grid, potential=potential,
                                temperature=temperature, phase=phase,
                                top_current=trace['top_current'], joule_power=trace['joule_power'])
    predicted = phase.copy()
    predicted[:,0] = .03
    predicted[(time >= .45)&(time <= .55),0] = .8  # outside W1, excluded from W1 support.
    record, _ = metrics({'potential':potential,'temperature':temperature,'phase':predicted},reference,p,CONFIG)
    assert np.allclose([c['recall'] for c in record['cycles']], .5)
    assert np.allclose([c['precision'] for c in record['cycles']], 1)
    assert np.allclose([c['mass_ratio'] for c in record['cycles']], .5)
    assert record['valid'] and not record['strict_device_pass']
    base={'valid':True,'strict_device_pass':False,'metrics':dict(S=.1,Ephi=.1,ET=.1,EI=.1,EV=.1)}
    better={'valid':True,'strict_device_pass':False,'metrics':dict(S=.08,Ephi=.08,ET=.1,EI=.1,EV=.1)}
    assert comparison(better,base,CONFIG['decision'])['passed']
    better['metrics']['EI']=.11
    assert not comparison(better,base,CONFIG['decision'])['passed']


def test_nonfinite_endpoint_does_not_prevent_other_comparisons():
    from pinn_pcm_sci.phk_v23_lf11_evaluation import metrics, comparison
    p = build_model(CONFIG).physics
    reference=SimpleNamespace(time=np.array([0.,1.25,2.5]),grid=None)
    record,_=metrics({'phase':np.array([[np.nan]])},reference,p,CONFIG)
    assert record['valid'] is False and record['metrics'] is None
    assert comparison(record,record,CONFIG['decision'])['reason']=='numerical_validity_failure'


def load_tests(loader, tests, pattern):
    return unittest.TestSuite(unittest.FunctionTestCase(value)
        for name, value in globals().items() if name.startswith("test_") and callable(value))
