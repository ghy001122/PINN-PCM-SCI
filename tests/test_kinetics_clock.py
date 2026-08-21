from __future__ import annotations

import unittest

import torch
from torch import nn

from pinn_pcm_sci.kinetics_clock import (
    ClockAdmissibilitySpec,
    IdentityClock,
    PiecewisePositiveGaussianClock,
    PositiveGaussianClock,
    StructuralKineticsClockPINN,
    clock_diagnostics,
    evaluate_clock_admissibility,
    full_pullback,
    kinetics_alignment_loss,
    make_mlp,
    piecewise_strong_form_mask,
)


torch.set_default_dtype(torch.float64)


def _gradient_and_hessian(value: torch.Tensor, inputs: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    gradient = torch.autograd.grad(
        value.sum(), inputs, create_graph=True, retain_graph=True
    )[0]
    rows = []
    for index in range(inputs.shape[1]):
        rows.append(
            torch.autograd.grad(
                gradient[:, index].sum(),
                inputs,
                create_graph=True,
                retain_graph=True,
            )[0]
        )
    return gradient, torch.stack(rows, dim=1)


class ManufacturedClock(nn.Module):
    def forward(self, xyt: torch.Tensor) -> torch.Tensor:
        x, y, time = xyt[:, 0:1], xyt[:, 1:2], xyt[:, 2:3]
        return time * (1.0 + 0.2 * x) + 0.1 * y * time.square() + 0.3 * x.square()


class ManufacturedEta(nn.Module):
    def forward(self, xy_tau: torch.Tensor) -> torch.Tensor:
        x, y, tau = xy_tau[:, 0:1], xy_tau[:, 1:2], xy_tau[:, 2:3]
        return x.square() + x * y * tau + torch.sin(tau) + y * tau.square()


class KineticsClockContractTest(unittest.TestCase):
    def test_positive_gaussian_clock_rate_is_analytic_and_strictly_positive(self) -> None:
        torch.manual_seed(7)
        clock = PositiveGaussianClock(
            spatial_dim=2,
            centers=(-0.25, 0.35),
            widths=(0.4, 0.7),
            kappa_floor=0.2,
            hidden_width=5,
        ).double()
        xyt = torch.tensor(
            [
                [0.1, -0.2, 0.0],
                [0.1, -0.2, 0.2],
                [0.1, -0.2, 0.7],
                [0.1, -0.2, 1.0],
            ],
            requires_grad=True,
        )

        tau = clock(xyt)
        autograd_rate = torch.autograd.grad(tau.sum(), xyt, create_graph=True)[0][:, 2:3]

        torch.testing.assert_close(autograd_rate, clock.rate(xyt), rtol=1e-11, atol=1e-12)
        self.assertTrue(torch.all(clock.rate(xyt) >= 0.2))
        self.assertTrue(torch.all(tau[1:] > tau[:-1]))

    def test_full_pullback_matches_direct_manufactured_first_second_and_mixed_derivatives(self) -> None:
        xyt = torch.tensor(
            [
                [0.15, -0.20, 0.30],
                [-0.35, 0.25, 0.70],
                [0.40, 0.10, 1.10],
            ],
            requires_grad=True,
        )
        clock = ManufacturedClock()
        eta = ManufacturedEta()

        pullback = full_pullback(eta, clock, xyt)
        direct_tau = clock(xyt)
        direct_value = eta(torch.cat([xyt[:, :2], direct_tau], dim=1))
        direct_gradient, direct_hessian = _gradient_and_hessian(direct_value, xyt)

        torch.testing.assert_close(pullback.value, direct_value, rtol=1e-12, atol=1e-12)
        torch.testing.assert_close(
            pullback.physical_gradient, direct_gradient, rtol=1e-10, atol=1e-11
        )
        torch.testing.assert_close(
            pullback.physical_hessian, direct_hessian, rtol=1e-9, atol=1e-10
        )

    def test_identity_clock_pullback_is_raw_time_equivalent(self) -> None:
        xyt = torch.tensor(
            [[0.2, 0.3, 0.4], [-0.1, 0.5, 0.8]], requires_grad=True
        )
        eta = ManufacturedEta()

        pullback = full_pullback(eta, IdentityClock(), xyt)
        raw_value = eta(xyt)
        raw_gradient, raw_hessian = _gradient_and_hessian(raw_value, xyt)

        torch.testing.assert_close(pullback.value, raw_value)
        torch.testing.assert_close(pullback.physical_gradient, raw_gradient)
        torch.testing.assert_close(pullback.physical_hessian, raw_hessian)

    def test_clock_eta_and_physical_fields_have_disjoint_trainable_parameters(self) -> None:
        model = StructuralKineticsClockPINN(
            clock=PositiveGaussianClock(
                spatial_dim=2,
                centers=(0.25, 0.75),
                widths=(0.2, 0.2),
                kappa_floor=0.1,
                hidden_width=4,
            ),
            eta_model=make_mlp(3, 1, hidden_width=6, hidden_layers=2),
            physical_field_model=make_mlp(3, 4, hidden_width=7, hidden_layers=2),
        ).double()

        groups = model.parameter_id_sets()
        self.assertFalse(groups["clock"] & groups["eta"])
        self.assertFalse(groups["clock"] & groups["physical_fields"])
        self.assertFalse(groups["eta"] & groups["physical_fields"])
        output = model(torch.zeros((5, 3), dtype=torch.float64))
        self.assertEqual(output.tau.shape, (5, 1))
        self.assertEqual(output.eta.shape, (5, 1))
        self.assertEqual(output.physical_fields.shape, (5, 4))

    def test_piecewise_strong_form_excludes_only_breakpoint_neighbourhoods(self) -> None:
        time = torch.tensor([0.0, 0.49, 0.5, 0.51, 1.0])
        mask = piecewise_strong_form_mask(
            time,
            breakpoints=(0.5,),
            exclusion_radius=0.005,
        )

        self.assertEqual(mask.tolist(), [True, True, False, True, True])

    def test_identity_clock_has_unit_condition_and_passes_frozen_admissibility(self) -> None:
        xyt = torch.tensor(
            [[0.2, 0.3, 0.4], [-0.1, 0.5, 0.8]], requires_grad=True
        )
        pullback = full_pullback(ManufacturedEta(), IdentityClock(), xyt)

        diagnostics = clock_diagnostics(pullback)
        self.assertAlmostEqual(diagnostics.min_rate, 1.0)
        self.assertAlmostEqual(diagnostics.max_spatial_gradient, 0.0)
        self.assertAlmostEqual(diagnostics.max_coordinate_condition, 1.0)
        report = evaluate_clock_admissibility(
            pullback,
            ClockAdmissibilitySpec(
                min_rate=0.1,
                max_spatial_gradient=0.5,
                max_coordinate_condition=2.0,
                max_first_order_amplification=2.0,
                max_second_order_amplification=2.0,
            ),
        )
        self.assertTrue(report.passed)
        self.assertEqual(report.violations, ())

    def test_clock_alignment_stop_gradient_changes_only_target_gradient_route(self) -> None:
        predicted = torch.tensor([[0.5], [1.5]], requires_grad=True)
        stopped_target = torch.tensor([[1.0], [1.0]], requires_grad=True)
        kinetics_alignment_loss(
            predicted,
            stopped_target,
            stop_gradient_target=True,
        ).backward()
        self.assertIsNotNone(predicted.grad)
        self.assertIsNone(stopped_target.grad)

        full_predicted = torch.tensor([[0.5], [1.5]], requires_grad=True)
        full_target = torch.tensor([[1.0], [1.0]], requires_grad=True)
        kinetics_alignment_loss(
            full_predicted,
            full_target,
            stop_gradient_target=False,
        ).backward()
        self.assertIsNotNone(full_target.grad)

    def test_piecewise_clock_is_continuous_with_positive_one_sided_rates(self) -> None:
        left = PositiveGaussianClock(
            spatial_dim=2,
            centers=(0.2,),
            widths=(0.3,),
            kappa_floor=0.2,
            hidden_width=3,
            segment_start=0.0,
        ).double()
        right = PositiveGaussianClock(
            spatial_dim=2,
            centers=(0.8,),
            widths=(0.25,),
            kappa_floor=0.15,
            hidden_width=3,
            segment_start=0.5,
        ).double()
        clock = PiecewisePositiveGaussianClock(
            segments=(left, right), breakpoints=(0.5,)
        )
        epsilon = 1e-7
        xyt = torch.tensor(
            [
                [0.1, -0.2, 0.5 - epsilon],
                [0.1, -0.2, 0.5],
                [0.1, -0.2, 0.5 + epsilon],
            ]
        )

        tau = clock(xyt)
        self.assertLess(float(torch.abs(tau[1] - tau[0])), 1e-6)
        self.assertLess(float(torch.abs(tau[2] - tau[1])), 1e-6)
        self.assertTrue(torch.all(clock.rate(xyt) > 0.0))


if __name__ == "__main__":
    unittest.main()
