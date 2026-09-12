import unittest
from types import SimpleNamespace

import numpy as np
import torch

from pinn_pcm_sci.phk_v23_lf11 import build_model, tensor
from pinn_pcm_sci.phk_v23_lf11_followup import interval_distance, temperature_envelope, weighted_rms
from pinn_pcm_sci.phk_v23_lf11_followup_fit import (
    TemperatureAdapter, bounded_lbfgs, full_head_objective, head_field,
)


class FollowupTests(unittest.TestCase):
    def setUp(self):
        torch.set_num_threads(2)

    def test_pointwise_bound_and_zero_envelope(self):
        q = np.array([[0, .5, 0], [0, 1, .2], [0, .5, .35]])
        upper = temperature_envelope(q)
        np.testing.assert_array_equal(upper[:2], [0, 0])
        gap = interval_distance(np.array([-.1, .2, upper[2]+.3]), upper)
        np.testing.assert_allclose(gap, [.1, .2, .3])
        self.assertAlmostEqual(weighted_rms(gap, [.2, .3, .5], [True, False, True]),
                               np.sqrt((.2*.01+.5*.09)/.7))

    def test_chunked_full_objective_and_gradient_match_actual_model(self):
        model = build_model({"seed": 17, "width": 8, "layers": 2})
        rng = np.random.default_rng(51)
        q = rng.uniform([-1, 0, 0], [1, 1, 2.5], (19, 3))
        targets = rng.uniform(0, .3, (19, 3))
        weight = rng.uniform(.1, 1, 19)
        weight /= weight.sum()
        data = SimpleNamespace(coordinates=q, targets=targets, prob=weight)
        for name, col, scale in (("potential", 0, .72), ("temperature", 1, .45)):
            model.zero_grad(set_to_none=True)
            full = model(tensor(q))[:, col]
            direct = head_field(model, name, tensor(q))
            torch.testing.assert_close(full, direct, rtol=0, atol=0)
            objective = torch.dot(tensor(weight), ((full-tensor(targets[:, col]))/scale).square())/3
            objective.backward()
            reference = [p.grad.clone() for p in model.heads[name].parameters()]
            model.zero_grad(set_to_none=True)
            chunked = full_head_objective(model, data, name, chunk=4)
            torch.testing.assert_close(objective.detach(), chunked, rtol=1e-13, atol=1e-14)
            for p, expected in zip(model.heads[name].parameters(), reference):
                torch.testing.assert_close(p.grad, expected, rtol=1e-12, atol=1e-14)

    def test_budget_exhaustion_restores_pretrial_parameters_and_state(self):
        parameter = torch.nn.Parameter(torch.tensor([4.], dtype=torch.float64))
        def closure():
            loss = (parameter-1).square().sum()
            loss.backward()
            return loss
        result, optimizer = bounded_lbfgs([parameter], closure, 1)
        self.assertEqual(result["evaluations"], 1)
        self.assertEqual(result["accepted_steps"], 0)
        self.assertIn("ROLLED_BACK", result["termination"])
        self.assertEqual(float(parameter.detach()), 4.)
        self.assertFalse(optimizer.state_dict()["state"])

    def test_lbfgs_retains_evaluated_accepted_endpoint(self):
        parameter = torch.nn.Parameter(torch.tensor([4.], dtype=torch.float64))
        def closure():
            loss = (parameter-1).square().sum()
            loss.backward()
            return loss
        result, _ = bounded_lbfgs([parameter], closure, 10)
        self.assertLessEqual(result["evaluations"], 10)
        self.assertGreater(result["accepted_steps"], 0)
        self.assertAlmostEqual(float(parameter.detach()), 1., places=12)

    def test_adapter_insertion_preserves_all_outputs(self):
        model = build_model({"seed": 17, "width": 8, "layers": 2})
        q = tensor(np.array([[0, .5, .2], [.9, .95, 1.4], [-.3, .1, 2.5]]))
        before = model(q).detach()
        model.heads["temperature"] = TemperatureAdapter(model.heads["temperature"])
        torch.testing.assert_close(model(q).detach(), before, rtol=0, atol=0)


if __name__ == "__main__":
    unittest.main()
