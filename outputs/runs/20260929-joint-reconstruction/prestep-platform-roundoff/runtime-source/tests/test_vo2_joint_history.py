"""Small synthetic checks; no scientific trajectory or hidden source reads."""
import numpy as np
import torch
import unittest

from pinn_pcm_sci.vo2_author_reproduction import Hysteresis, HKEYS
from pinn_pcm_sci.vo2_joint_history import (
    replay_with_history, resistance_from_temperature, selected_event_signature,
)


def source_replay(t):
    h = Hysteresis(t.shape[1])
    out = {k: [] for k in ("resistance", "g", *HKEYS)}
    for row in t:
        h.reversal(row)
        out["resistance"].append(h.resistance(row).copy())
        out["g"].append(h.g(np.clip(row, 305., 370.)).copy())
        for key in HKEYS:
            out[key].append(getattr(h, key).copy())
    return {k: np.array(v) for k, v in out.items()}


def synthetic(n=401):
    s = np.linspace(0., 4*np.pi, n)
    return np.column_stack((334-9*np.cos(s), 334-8*np.cos(s+.2)))


def test_forward_source_same_time_history_and_joint_trigger():
    t = synthetic()
    # One companion stays almost stationary while the other triggers update;
    # this detects incorrectly replacing the source joint trigger by two gates.
    t[30:40, 1] = t[29, 1] + np.arange(1, 11)*.0007
    actual = replay_with_history(t)
    expected = source_replay(t)
    for key in expected:
        np.testing.assert_array_equal(actual[key], expected[key], err_msg=key)


def test_selected_branch_directional_derivative_includes_reversal_history():
    t = synthetic()
    rng = np.random.default_rng(912)
    direction = rng.normal(size=t.shape)
    weights = rng.normal(size=t.shape)/len(t)/1e4
    x = torch.tensor(t, dtype=torch.float64, requires_grad=True)
    loss = (resistance_from_temperature(x)*torch.tensor(weights)).sum()
    loss.backward()
    analytical = float((x.grad*torch.tensor(direction)).sum())
    epsilon = 1e-6
    assert selected_event_signature(t+epsilon*direction) == selected_event_signature(t)
    assert selected_event_signature(t-epsilon*direction) == selected_event_signature(t)
    plus = np.sum(replay_with_history(t+epsilon*direction)["resistance"]*weights)
    minus = np.sum(replay_with_history(t-epsilon*direction)["resistance"]*weights)
    finite = (plus-minus)/(2*epsilon)
    np.testing.assert_allclose(analytical, finite, rtol=2e-5, atol=1e-9)


def test_future_output_retains_gradient_to_reversal_temperature():
    t = synthetic(151)
    history = replay_with_history(t)
    event = int(history["event_rows"][1])
    device = int(np.flatnonzero(history["event_masks"][1])[0])
    stop = int(history["event_rows"][2])
    target = min(event+5, stop-1)
    x = torch.tensor(t, dtype=torch.float64, requires_grad=True)
    y = resistance_from_temperature(x)[target, device]
    y.backward()
    # A detached-history implementation gives exactly zero here.
    assert abs(float(x.grad[event, device])) > 1e-3
    eps = 1e-6
    direction = np.zeros_like(t)
    direction[event, device] = 1.
    assert selected_event_signature(t+eps*direction) == selected_event_signature(t-eps*direction)
    plus = replay_with_history(t+eps*direction)["resistance"][target, device]
    minus = replay_with_history(t-eps*direction)["resistance"][target, device]
    np.testing.assert_allclose(float(x.grad[event, device]), (plus-minus)/(2*eps),
                               rtol=2e-5, atol=1e-5)


def test_cross_reversal_change_is_not_claimed_as_same_branch_gradient():
    t = np.array([[325., 325.], [326., 326.], [325.990001, 326.], [325.98, 326.]])
    changed = t.copy()
    changed[2, 0] -= 2e-6
    assert selected_event_signature(t) != selected_event_signature(changed)
    a = replay_with_history(t)
    b = replay_with_history(changed)
    assert a["event_rows"].tolist() == [3]
    assert b["event_rows"].tolist() == [2]
    assert np.isfinite(a["resistance"]-b["resistance"]).all()


def test_constitutive_clip_only_no_state_clip_and_gradient():
    t = np.array([[300.], [325.], [375.]], dtype=np.float64)
    actual = replay_with_history(t)
    expected = source_replay(t)
    for key in expected:
        np.testing.assert_array_equal(actual[key], expected[key])
    x = torch.tensor(t, dtype=torch.float64, requires_grad=True)
    resistance_from_temperature(x).sum().backward()
    assert x.grad[0, 0] == 0.
    assert x.grad[-1, 0] == 0.
    assert t[0, 0] == 300. and t[-1, 0] == 375.


class TestJointHistory(unittest.TestCase):
    test_forward = staticmethod(test_forward_source_same_time_history_and_joint_trigger)
    test_directional = staticmethod(test_selected_branch_directional_derivative_includes_reversal_history)
    test_history_dependency = staticmethod(test_future_output_retains_gradient_to_reversal_temperature)
    test_cross_event = staticmethod(test_cross_reversal_change_is_not_claimed_as_same_branch_gradient)
    test_clip = staticmethod(test_constitutive_clip_only_no_state_clip_and_gradient)


if __name__ == "__main__":
    unittest.main()
