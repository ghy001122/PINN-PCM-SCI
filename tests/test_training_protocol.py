from __future__ import annotations

import math
from pathlib import Path
import unittest

import torch
import numpy as np

from pinn_pcm_sci.qpop_physics import QPopParameters
from pinn_pcm_sci.qpop_pinn import QPopPINN
from pinn_pcm_sci.training_protocol import (
    AnchorDiagnosticReport,
    AnchorSet,
    EventCompetenceReport,
    QPopTrainingSession,
    TrainingProtocol,
    phase_fraction_dynamic_range,
    select_anchor_checkpoint,
    select_sparse_anchor_indices,
    select_screen_protocol,
)


class TrainingProtocolTests(unittest.TestCase):
    def test_protocol_aggregates_grouped_mean_and_smooth_max_from_frozen_scales(self) -> None:
        residuals = {
            "interior/a": torch.tensor([[0.0], [0.0]], dtype=torch.float64),
            "interior/b": torch.tensor([[math.sqrt(0.2)]], dtype=torch.float64),
            "initial/a": torch.tensor([[0.0]], dtype=torch.float64),
            "boundary/left/a": torch.tensor([[0.0]], dtype=torch.float64),
        }
        scales = {name: 1.0 for name in residuals}

        grouped = TrainingProtocol(
            protocol_id="grouped",
            aggregation="grouped_mean",
            temporal_schedule="joint",
        )
        smooth = TrainingProtocol(
            protocol_id="smooth",
            aggregation="smooth_max",
            temporal_schedule="joint",
            smooth_max_tau=0.1,
        )

        self.assertAlmostEqual(float(grouped.objective(residuals, scales)), 0.1)
        self.assertAlmostEqual(
            float(smooth.objective(residuals, scales)),
            0.1 * math.log((3.0 + math.exp(2.0)) / 4.0),
            places=12,
        )

    def test_four_prefix_warmup_exposes_only_the_registered_time_support(self) -> None:
        protocol = TrainingProtocol(
            protocol_id="causal",
            aggregation="smooth_max",
            temporal_schedule="four_prefix_warmup",
        )

        observed = [
            protocol.time_ceiling_ns(step)
            for step in (0, 49, 50, 99, 100, 149, 150, 199, 200, 999)
        ]
        self.assertEqual(
            observed,
            [130.0, 130.0, 260.0, 260.0, 390.0, 390.0, 494.0, 494.0, 494.0, 494.0],
        )

        joint = TrainingProtocol(
            protocol_id="joint",
            aggregation="grouped_mean",
            temporal_schedule="joint",
        )
        self.assertEqual(joint.time_ceiling_ns(0), 494.0)

    def test_checkpoint_selection_is_physics_only_and_breaks_ties_by_earliest_step(self) -> None:
        protocol = TrainingProtocol(
            protocol_id="selector",
            aggregation="smooth_max",
            temporal_schedule="joint",
        )
        records = (
            {"step": 0, "physics_audit_max": 1.0, "physics_audit_sum": 20.0, "event_range": 0.9},
            {"step": 40, "physics_audit_max": 0.8, "physics_audit_sum": 12.0, "event_range": 0.0},
            {"step": 80, "physics_audit_max": 0.8, "physics_audit_sum": 12.0, "event_range": 0.7},
            {"step": 120, "physics_audit_max": 0.8, "physics_audit_sum": 13.0, "event_range": 1.0},
        )

        self.assertEqual(protocol.select_checkpoint(records)["step"], 40)
        self.assertEqual(
            protocol.select_checkpoint(
                (
                    {"step": 0, "physics_audit_max": 1.0, "physics_audit_sum": 20.0},
                    {"step": 40, "physics_audit_max": 1.2, "physics_audit_sum": 21.0},
                )
            )["step"],
            40,
        )

    def test_event_competence_requires_every_preregistered_raw_gate(self) -> None:
        passing = EventCompetenceReport.adjudicate(
            selected_step=400,
            phase_fraction_range=0.06,
            structure_error=0.21,
            device_nrmse=1.0,
            physics_audit_max=1.01,
        )
        static = EventCompetenceReport.adjudicate(
            selected_step=400,
            phase_fraction_range=0.0,
            structure_error=0.20,
            device_nrmse=1.0,
            physics_audit_max=1.01,
        )

        self.assertEqual(passing.gate_outcome, "RAW_EVENT_RESOLVED")
        self.assertTrue(passing.passed)
        self.assertEqual(static.gate_outcome, "RAW_EVENT_NOT_RESOLVED")
        self.assertFalse(static.passed)
        self.assertIn("PHASE_FRACTION_RANGE_BELOW_MINIMUM", static.failure_reasons)

    def test_protocol_reuses_paired_coordinates_and_only_remaps_time_support(self) -> None:
        protocol = TrainingProtocol(
            protocol_id="causal",
            aggregation="smooth_max",
            temporal_schedule="four_prefix_warmup",
        )
        base = torch.tensor([[0.2, 0.3, 0.8]], dtype=torch.float64)

        limited = protocol.apply_time_support(
            base, update_index=0, model_horizon_ns=512.0793
        )

        self.assertTrue(torch.equal(limited[:, :2], base[:, :2]))
        self.assertAlmostEqual(float(limited[0, 2]), 0.8 * 130.0 / 512.0793)
        self.assertEqual(float(base[0, 2]), 0.8)

    def test_training_session_pairs_sampling_and_reports_exact_optimizer_work(self) -> None:
        parameters = QPopParameters.from_input(
            Path("configs/qpop/cpc-v1-imt-intrinsic-voltage-osc-author-case/canonical_input.xml")
        )
        grouped = TrainingProtocol(
            protocol_id="grouped",
            aggregation="grouped_mean",
            temporal_schedule="joint",
            interior_points=3,
            initial_points=2,
            boundary_points_per_side=2,
            audit_interior_points=3,
            audit_initial_points=2,
            audit_boundary_points_per_side=2,
        )
        smooth = TrainingProtocol(
            protocol_id="smooth",
            aggregation="smooth_max",
            temporal_schedule="joint",
            interior_points=3,
            initial_points=2,
            boundary_points_per_side=2,
            audit_interior_points=3,
            audit_initial_points=2,
            audit_boundary_points_per_side=2,
        )
        torch.manual_seed(17)
        first = QPopPINN(
            parameters=parameters,
            horizon_ns=512.0793,
            method="raw",
            hidden_width=8,
            hidden_layers=2,
        ).double()
        torch.manual_seed(17)
        second = QPopPINN(
            parameters=parameters,
            horizon_ns=512.0793,
            method="raw",
            hidden_width=8,
            hidden_layers=2,
        ).double()
        session = QPopTrainingSession.freeze(first, grouped, seed=17)

        first_result = session.train(first, grouped, seed=17, updates=1)
        second_result = session.train(second, smooth, seed=17, updates=1)

        self.assertEqual(first_result.actual_updates, 1)
        self.assertEqual(first_result.selected_step, 1)
        self.assertEqual([row["step"] for row in first_result.history], [0, 1])
        self.assertEqual(first_result.sampling_digest, second_result.sampling_digest)

    def test_training_continuation_matches_the_registered_sampling_stream(self) -> None:
        parameters = QPopParameters.from_input(
            Path("configs/qpop/cpc-v1-imt-intrinsic-voltage-osc-author-case/canonical_input.xml")
        )
        protocol = TrainingProtocol(
            protocol_id="continuation",
            aggregation="smooth_max",
            temporal_schedule="four_prefix_warmup",
            interior_points=2,
            initial_points=2,
            boundary_points_per_side=1,
            audit_interior_points=2,
            audit_initial_points=2,
            audit_boundary_points_per_side=1,
        )

        def model() -> QPopPINN:
            torch.manual_seed(17)
            return QPopPINN(
                parameters=parameters,
                horizon_ns=512.0793,
                method="raw",
                hidden_width=8,
                hidden_layers=2,
            ).double()

        direct_model = model()
        staged_model = model()
        session = QPopTrainingSession.freeze(direct_model, protocol, seed=17)
        direct = session.train(direct_model, protocol, seed=17, updates=2)
        first = session.train(staged_model, protocol, seed=17, updates=1)
        continued = session.train(
            staged_model,
            protocol,
            seed=17,
            updates=1,
            continuation=first.continuation,
        )

        self.assertEqual(continued.actual_updates, 2)
        self.assertEqual(continued.sampling_digest, direct.sampling_digest)
        self.assertEqual([row["step"] for row in continued.history], [0, 1, 2])

    def test_screen_selection_uses_structure_error_and_the_registered_tie_default(self) -> None:
        tied = {
            "r1-grouped-joint": {"valid": True, "structure_error": 0.2100},
            "r2-smooth-joint": {"valid": True, "structure_error": 0.2105},
            "r3-grouped-causal": {"valid": True, "structure_error": 0.2102},
            "r4-smooth-causal": {"valid": True, "structure_error": 0.2109},
        }
        clear = dict(tied)
        clear["r1-grouped-joint"] = {"valid": True, "structure_error": 0.19}

        self.assertEqual(select_screen_protocol(tied), "r4-smooth-causal")
        self.assertEqual(select_screen_protocol(clear), "r1-grouped-joint")

    def test_phase_fraction_diagnostic_uses_only_the_registered_analysis_window(self) -> None:
        eta = np.asarray(
            [
                [0.0, 0.0, 1.0, 1.0],
                [1.0, 1.0, 1.0, 1.0],
                [0.0, 0.0, 0.0, 0.0],
            ]
        )
        time = np.asarray([0.0, 494.0, 500.0])

        self.assertEqual(
            phase_fraction_dynamic_range(
                eta, time, threshold=0.5, analysis_end_ns=494.0
            ),
            0.5,
        )

    def test_anchor_checkpoint_uses_labels_only_inside_the_physics_admissible_set(self) -> None:
        records = (
            {"step": 0, "physics_audit_max": 1.0, "physics_audit_sum": 40.0, "anchor_loss": 0.4},
            {"step": 100, "physics_audit_max": 1.3, "physics_audit_sum": 10.0, "anchor_loss": 0.01},
            {"step": 200, "physics_audit_max": 1.2, "physics_audit_sum": 12.0, "anchor_loss": 0.1},
            {"step": 300, "physics_audit_max": 1.1, "physics_audit_sum": 11.0, "anchor_loss": 0.1},
        )

        self.assertEqual(select_anchor_checkpoint(records)["step"], 300)

    def test_anchor_diagnostic_reports_label_loss_without_changing_the_main_checkpoint_rule(self) -> None:
        parameters = QPopParameters.from_input(
            Path("configs/qpop/cpc-v1-imt-intrinsic-voltage-osc-author-case/canonical_input.xml")
        )
        protocol = TrainingProtocol(
            protocol_id="anchor",
            aggregation="grouped_mean",
            temporal_schedule="joint",
            interior_points=2,
            initial_points=2,
            boundary_points_per_side=1,
            audit_interior_points=2,
            audit_initial_points=2,
            audit_boundary_points_per_side=1,
        )
        torch.manual_seed(17)
        model = QPopPINN(
            parameters=parameters,
            horizon_ns=512.0793,
            method="raw",
            hidden_width=8,
            hidden_layers=2,
        ).double()
        session = QPopTrainingSession.freeze(model, protocol, seed=17)
        anchors = AnchorSet(
            coordinates=torch.tensor(
                [[0.2, 0.3, 0.25], [0.7, 0.8, 0.75]], dtype=torch.float64
            ),
            eta_targets=torch.tensor([[0.2], [0.4]], dtype=torch.float64),
        )

        result = session.train_anchor_diagnostic(
            model, protocol, anchors=anchors, seed=17, updates=1
        )

        self.assertEqual(result.actual_updates, 1)
        self.assertEqual([row["step"] for row in result.history], [0, 1])
        self.assertIn("anchor_loss", result.history[1])

    def test_sparse_anchor_selection_is_protocol_timed_and_seed_deterministic(self) -> None:
        field_time = np.asarray([0.0, 120.0, 140.0, 250.0, 270.0, 390.0, 493.0, 500.0])

        first = select_sparse_anchor_indices(
            field_time, node_count=20, sample_count=3, seed=17
        )
        second = select_sparse_anchor_indices(
            field_time, node_count=20, sample_count=3, seed=17
        )

        self.assertEqual(first[0], (1, 3, 5, 6))
        self.assertEqual(first, second)
        self.assertEqual(len(first[1]), 3)

    def test_anchor_diagnostic_has_the_three_predeclared_dispositions(self) -> None:
        optimization = AnchorDiagnosticReport.adjudicate(
            phase_fraction_range=0.06,
            structure_error=0.20,
            physics_audit_max=1.20,
        )
        tension = AnchorDiagnosticReport.adjudicate(
            phase_fraction_range=0.06,
            structure_error=0.20,
            physics_audit_max=1.30,
        )
        representation = AnchorDiagnosticReport.adjudicate(
            phase_fraction_range=0.0,
            structure_error=0.229,
            physics_audit_max=1.0,
        )

        self.assertEqual(optimization.gate_outcome, "OPTIMIZATION_BOTTLENECK_CONFIRMED")
        self.assertEqual(tension.gate_outcome, "PHYSICS_CONSTRAINT_TENSION")
        self.assertEqual(
            representation.gate_outcome, "REPRESENTATION_OR_RESIDUAL_BOTTLENECK"
        )
        self.assertEqual(
            optimization.route_disposition,
            "CLOSE_QPOP_PINN_CONTINUE_N3B_REDUCED_ORACLE",
        )


if __name__ == "__main__":
    unittest.main()
