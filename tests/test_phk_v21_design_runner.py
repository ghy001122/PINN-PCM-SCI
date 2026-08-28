from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from unittest import mock

from pinn_pcm_sci.ledger import ExperimentLedger
from pinn_pcm_sci.phk_benchmark import (
    PhkCycleEvent,
    PhkEventReport,
    PhkGuardReport,
)
from pinn_pcm_sci.phk_v21_design_runner import run_campaign
from pinn_pcm_sci.phk_v21_engineering import PhkV21EngineeringRun


ROOT = Path(__file__).resolve().parents[1]


def fake_run(*, event_passed: bool) -> PhkV21EngineeringRun:
    event_time = 0.2 if event_passed else None
    cycles = tuple(
        PhkCycleEvent(
            cycle_index=index,
            event_time=event_time,
            pre_roi_fraction=0.0,
            peak_roi_fraction=0.1,
            peak_full_domain_fraction=0.05,
            peak_outside_roi_fraction=0.01,
            recovery_fraction=0.8,
            saved_steps_at_or_above_threshold=4,
        )
        for index in (1, 2)
    )
    event = PhkEventReport(
        cycles=cycles,
        cycle_peak_relative_drift=0.0,
        passed=event_passed,
        failures=() if event_passed else ("event_missing",),
    )
    guard = PhkGuardReport(
        passed=True,
        failures=(),
        nonfinite_count=0,
        maximum_current_balance_relative=0.0,
        maximum_thermal_residual_scaled=0.0,
        maximum_phase_residual_scaled=0.0,
        maximum_linear_residual_scaled=0.0,
        maximum_no_flux_residual_scaled=0.0,
        potential_range=(0.0, 1.0),
        temperature_range=(0.0, 1.0),
        phase_range=(0.0, 1.0),
    )
    return PhkV21EngineeringRun(
        result=None,  # type: ignore[arg-type]
        event=event,
        guard=guard,
        phase_solver_statistics={"phase_calls_total": 1},
    )


class PhkV21DesignRunnerTest(unittest.TestCase):
    def _kwargs(self, root: Path, run_id: str) -> dict[str, object]:
        output = root / "outputs"
        experiment = root / "experiment"
        output.mkdir()
        experiment.mkdir()
        (experiment / "index.jsonl").write_text("", encoding="utf-8")
        return {
            "run_id": run_id,
            "program_path": ROOT / "configs/phk_v21/program_contract.json",
            "engineering_path": ROOT / "configs/phk_v21/engineering_contract.json",
            "selection_path": ROOT / "configs/phk_v21/e1_solver_selection.json",
            "legacy_program_path": ROOT / "configs/phk_v2/program_contract.json",
            "legacy_object_path": ROOT / "configs/phk_v2/object_numerical_contract.json",
            "output_root": output,
            "experiment_root": experiment,
        }

    def test_intent_precedes_solve_and_failed_event_route_stops_before_controls(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            kwargs = self._kwargs(root, "TEST-V21-E2-NOGO")
            experiment = kwargs["experiment_root"]
            calls = 0

            def side_effect(**_):
                nonlocal calls
                calls += 1
                self.assertTrue(
                    (Path(experiment) / "intents/TEST-V21-E2-NOGO.json").is_file()
                )
                return fake_run(event_passed=False)

            with mock.patch(
                "pinn_pcm_sci.phk_v21_design_runner.run_engineering_case",
                side_effect=side_effect,
            ):
                self.assertEqual(run_campaign(**kwargs), 0)
            self.assertEqual(calls, 35)
            summary = (
                Path(kwargs["output_root"])
                / "TEST-V21-E2-NOGO/summary.json"
            ).read_text(encoding="utf-8")
            self.assertIn("PHK_V21_ENGINEERING_NO_ADMISSIBLE_REPEATABLE_EVENT_OBJECT", summary)
            ExperimentLedger(experiment).validate()

    def test_full_pass_executes_exact_six_controls_and_finalizes_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            kwargs = self._kwargs(root, "TEST-V21-E2-PASS")
            controls: list[str] = []

            def side_effect(**call):
                control = call["control"]
                controls.append(control.value)
                return fake_run(
                    event_passed=control.value not in {"ZERO_DRIVE", "JOULE_GAIN_ZERO"}
                )

            with mock.patch(
                "pinn_pcm_sci.phk_v21_design_runner.run_engineering_case",
                side_effect=side_effect,
            ):
                self.assertEqual(run_campaign(**kwargs), 0)
            self.assertEqual(len(controls), 41)
            self.assertEqual(
                controls[-6:],
                [
                    "ZERO_DRIVE",
                    "JOULE_GAIN_ZERO",
                    "CONDUCTIVITY_PHASE_RATIO_ONE",
                    "LATENT_RATIO_ZERO",
                    "HEATER_WIDTH_0_50",
                    "INTERFACE_WIDTH_0_025",
                ],
            )
            summary = (
                Path(kwargs["output_root"])
                / "TEST-V21-E2-PASS/summary.json"
            ).read_text(encoding="utf-8")
            self.assertIn("PHK_V21_E2_ENGINEERING_OBJECT_CANDIDATE_SELECTED", summary)


if __name__ == "__main__":
    unittest.main()
