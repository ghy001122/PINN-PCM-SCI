"""Synthetic discrete-RC and full-history gradient qualification only."""
import unittest

import numpy as np
import torch

from pinn_pcm_sci.vo2_joint_rc import rc_forward, rc_voltage


def direct_torch(R, h, C, RL, Vin, v0):
    vin = torch.as_tensor(Vin, dtype=R.dtype)
    states = [torch.as_tensor(v0, dtype=R.dtype)]
    for n in range(R.shape[0] - 1):
        states.append((1. - h / C * (1. / RL + 1. / R[n])) * states[-1] + h * vin / (C * RL))
    return torch.stack(states)


class JointRCTests(unittest.TestCase):
    def setUp(self):
        self.h = .5e-9
        self.C = 145.34619293e-12
        self.RL = 12000.
        self.Vin = np.array([11., 9.4])
        self.v0 = np.array([.3, .7])
        n = np.arange(37)
        self.R = np.column_stack((1500. + 12. * n, 2200. + 30. * np.sin(n / 4.)))

    def test_recurrence_and_same_layer_initial_final(self):
        r = torch.tensor(self.R, dtype=torch.float64, requires_grad=True)
        expected = direct_torch(r, self.h, self.C, self.RL, self.Vin, self.v0)
        got = rc_voltage(r, self.h, self.C, self.RL, self.Vin, self.v0)
        np.testing.assert_allclose(got.detach().numpy(), expected.detach().numpy(), rtol=2e-15, atol=1e-16)
        np.testing.assert_array_equal(got[0].detach().numpy(), self.v0)
        np.testing.assert_array_equal(got.detach().numpy(), rc_forward(self.R, self.h, self.C, self.RL, self.Vin, self.v0))
        residual = (self.C * np.diff(got.detach().numpy(), axis=0) / self.h
                    - (self.Vin - got.detach().numpy()[:-1]) / self.RL
                    + got.detach().numpy()[:-1] / self.R[:-1])
        # The subtraction-based defect carries the C*v/h arithmetic scale.
        rounding_scale = self.C / self.h * np.max(np.abs(got.detach().numpy()))
        self.assertLess(np.max(np.abs(residual)), 4. * np.finfo(np.float64).eps * rounding_scale)

    def test_reverse_matches_full_torch_graph_and_future_loss(self):
        weights = torch.tensor(np.sin(np.arange(74).reshape(37, 2) / 3.), dtype=torch.float64)
        custom_r = torch.tensor(self.R, dtype=torch.float64, requires_grad=True)
        direct_r = custom_r.detach().clone().requires_grad_(True)
        custom_v = rc_voltage(custom_r, self.h, self.C, self.RL, self.Vin, self.v0)
        direct_v = direct_torch(direct_r, self.h, self.C, self.RL, self.Vin, self.v0)
        (weights * custom_v.square()).sum().backward()
        (weights * direct_v.square()).sum().backward()
        np.testing.assert_allclose(custom_r.grad.numpy(), direct_r.grad.numpy(), rtol=4e-14, atol=1e-19)
        np.testing.assert_array_equal(custom_r.grad[-1].numpy(), [0., 0.])
        # Only final voltage is scored here: an early R must still receive the
        # complete path derivative, rather than a local/truncated surrogate.
        early = torch.tensor(self.R, dtype=torch.float64, requires_grad=True)
        rc_voltage(early, self.h, self.C, self.RL, self.Vin, self.v0)[-1].sum().backward()
        self.assertGreater(early.grad[0, 0].item(), 0.)

    def test_centered_finite_directional_derivative(self):
        direction = np.cos(np.arange(74).reshape(37, 2) / 5.) * 10.
        weights = np.cos(np.arange(74).reshape(37, 2) / 3.)
        r = torch.tensor(self.R, dtype=torch.float64, requires_grad=True)
        v = rc_voltage(r, self.h, self.C, self.RL, self.Vin, self.v0)
        (v.square() * torch.tensor(weights)).sum().backward()
        analytical = float(np.sum(r.grad.numpy() * direction))
        epsilon = .001
        plus = rc_forward(self.R + epsilon * direction, self.h, self.C, self.RL, self.Vin, self.v0)
        minus = rc_forward(self.R - epsilon * direction, self.h, self.C, self.RL, self.Vin, self.v0)
        finite = float(np.sum(weights * (plus**2 - minus**2)) / (2. * epsilon))
        self.assertAlmostEqual(analytical, finite, delta=1e-10)

    def test_single_node_zero_input_and_invalid_precision(self):
        R = np.full(31, 2500.)
        got = rc_forward(R, self.h, self.C, self.RL, 0., 2.)
        a = 1. - self.h / self.C * (1. / self.RL + 1. / R[0])
        np.testing.assert_allclose(got, 2. * a**np.arange(31), rtol=2e-15, atol=0.)
        with self.assertRaises(TypeError):
            rc_voltage(torch.ones(3, dtype=torch.float32), self.h, self.C, self.RL, 1.)
        with self.assertRaises(ValueError):
            rc_forward([100., 0.], self.h, self.C, self.RL, 1.)


if __name__ == '__main__':
    unittest.main()
