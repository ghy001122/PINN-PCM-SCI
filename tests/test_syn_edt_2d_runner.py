from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import threading
import unittest
from unittest import mock

import numpy as np

from pinn_pcm_sci.artifacts import CaseArtifact
from pinn_pcm_sci.ledger import ExperimentLedger
from pinn_pcm_sci import syn_edt_2d_runner as runner


LADDER = [
    {"intent": 1, "case": "Q0", "space": "coarse", "time": "coarse", "control": "FULL"},
    {"intent": 2, "case": "QN", "space": "coarse", "time": "fine", "control": "FULL"},
    {"intent": 3, "case": "QN", "space": "medium", "time": "fine", "control": "FULL"},
    {"intent": 4, "case": "QN", "space": "fine", "time": "coarse", "control": "FULL"},
    {"intent": 5, "case": "QN", "space": "fine", "time": "medium", "control": "FULL"},
    {"intent": 6, "case": "QN", "space": "fine", "time": "fine", "control": "FULL"},
    {"intent": 7, "case": "QL", "space": "medium", "time": "medium", "control": "FULL"},
    {"intent": 8, "case": "QH", "space": "medium", "time": "medium", "control": "FULL"},
    {
        "intent": 9,
        "case": "QN",
        "space": "medium",
        "time": "fine",
        "control": "DIRECT_T_TO_TRANSPORT_OFF",
    },
    {
        "intent": 10,
        "case": "QN",
        "space": "fine",
        "time": "fine",
        "control": "DIRECT_T_TO_TRANSPORT_OFF",
    },
    {
        "intent": 11,
        "case": "QN",
        "space": "medium",
        "time": "fine",
        "control": "FULL_ISOTHERMAL_COUPLING_OFF",
    },
    {
        "intent": 12,
        "case": "QN",
        "space": "fine",
        "time": "fine",
        "control": "FULL_ISOTHERMAL_COUPLING_OFF",
    },
    {
        "intent": 13,
        "case": "QN",
        "space": "fine",
        "time": "fine",
        "control": "FULL",
        "role": "INDEPENDENT_PROCESS_EXACT_REPLAY_FOR_ORACLE_FLOOR",
    },
]


def write_contracts(root: Path) -> tuple[Path, Path]:
    s0_path = root / "s0.json"
    s0_path.write_text(
        json.dumps(
            {
                "schema_version": "goal-paper-one-shot-v1-s0-v1",
                "budgets": {"cpu_solver_intents": 40, "cpu_core_hours": 256},
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    s2_path = root / "s2.json"
    s2_path.write_text(
        json.dumps(
            {
                "schema_version": "goal-paper-one-shot-v1-s2-numerics-v1",
                "physical_contract_id": runner.PHYSICAL_CONTRACT_ID,
                "derived_from_s0_sha256": hashlib.sha256(
                    s0_path.read_bytes()
                ).hexdigest().upper(),
                "qualification_ladder": LADDER,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return s0_path, s2_path


def generated_q_case_manifest() -> dict[str, object]:
    roles = {
        "Q0": "zero_drive_guard",
        "QL": "nonvoting_low_bracket",
        "QN": "sole_event_qualification_vote",
        "QH": "nonvoting_high_bracket",
    }
    return {
        "cases": {
            case_id: {
                "pool": "Q",
                "qualification_case": case_id,
                "qualification_id": case_id,
                "role": role,
            }
            for case_id, role in roles.items()
        }
    }


def fixture_artifact(
    case_id: str = "syn-edt-fixture-q0",
    physical_contract_id: str = runner.PHYSICAL_CONTRACT_ID,
) -> CaseArtifact:
    registry = {
        "defect_fraction": {
            "source_name": "defect_fraction",
            "physical_symbol": "y",
            "quantity_label": "non-scientific fixture",
            "unit": "1",
            "association": "cell_center",
            "temporal_kind": "dynamic",
            "qualification_status": "NON_SCIENTIFIC_TEST_FIXTURE",
        }
    }
    return CaseArtifact(
        case_id=case_id,
        physical_contract_id=physical_contract_id,
        evidence_identity="NON_SCIENTIFIC_TEST_FIXTURE",
        nodes=np.array([[0.0, 0.0]], dtype=np.float64),
        cells=np.array([[0]], dtype=np.int64),
        mesh_unit="m",
        field_time=np.array([0.0, 1.0], dtype=np.float64),
        circuit_time=np.array([0.0, 1.0], dtype=np.float64),
        time_unit="s",
        fields={
            "defect_fraction": np.array([[0.5], [0.5]], dtype=np.float64)
        },
        field_units={"defect_fraction": "1"},
        field_registry=registry,
        breakpoints=np.array([0.5], dtype=np.float64),
        circuit={"top_terminal_current": np.array([0.0, 0.0], dtype=np.float64)},
        circuit_units={"top_terminal_current": "A"},
    )


class FakeResult:
    solver_statistics = {
        "timesteps": 5,
        "block_iterations_total": 7,
        "block_iterations_max": 2,
        "transport_newton_iterations_total": 11,
        "transport_newton_iterations_max": 3,
        "final_consistency_evaluations_total": 23,
        "electric_linear_solves_total": 13,
        "thermal_linear_solves_total": 17,
        "transport_linear_solves_total": 19,
        "linear_solves_total": 49,
        "final_transport_scaled_residual_max": 1.0e-11,
    }

    def __init__(
        self,
        *,
        s0_sha256: str | None = None,
        numerical_sha256: str | None = None,
    ) -> None:
        self.s0_sha256 = s0_sha256
        self.numerical_sha256 = numerical_sha256

    def to_report_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "case_id": "syn-edt-fixture-q0",
            "physical_contract_id": runner.PHYSICAL_CONTRACT_ID,
            "event_report": {"passed": True, "identity": "NON_SCIENTIFIC_FIXTURE"},
            "guard_report": {"passed": True, "identity": "NON_SCIENTIFIC_FIXTURE"},
            "mesh": {"identity": "NON_SCIENTIFIC_FIXTURE"},
        }
        if self.s0_sha256 is not None and self.numerical_sha256 is not None:
            payload["case_manifest"] = {
                "physical_contract_id": runner.PHYSICAL_CONTRACT_ID,
                "s0_sha256": self.s0_sha256,
                "s2_numerical_sha256": self.numerical_sha256,
            }
        return payload


class FakeCaseSpec:
    @staticmethod
    def qualification(case_id: str, contract: object) -> object:
        del contract
        return SimpleNamespace(case_id=f"syn-edt-fixture-{case_id.lower()}")


class FakeResolution:
    @staticmethod
    def from_levels(space: str, time: str, contract: object) -> object:
        if contract is None:
            raise AssertionError("the exact physical/numerical contract is required")
        return SimpleNamespace(
            space_level=space, time_level=time, contract_id=id(contract)
        )


class FakeEvaluationArtifact:
    def write(self, path: str | Path) -> None:
        Path(path).write_bytes(b"NON_SCIENTIFIC_EVALUATOR_FIXTURE")


class RunnerTest(unittest.TestCase):
    def core_patches(self, *, solve: object | None = None) -> ExitStack:
        stack = ExitStack()
        physical_contract = SimpleNamespace(
            contract_id=runner.PHYSICAL_CONTRACT_ID,
            physical={"fixture_physical": True},
            numerical={"fixture_numerical": True},
        )
        stack.enter_context(
            mock.patch.object(
                runner.syn_core.SynEdtPhysicalContract,
                "from_s0",
                return_value=physical_contract,
            )
        )
        stack.enter_context(
            mock.patch.object(runner.syn_core, "SynEdtCaseSpec", FakeCaseSpec)
        )
        stack.enter_context(
            mock.patch.object(
                runner.syn_core,
                "build_syn_edt_case_manifest",
                side_effect=lambda *_args, **_kwargs: generated_q_case_manifest(),
            )
        )
        stack.enter_context(
            mock.patch.object(runner.syn_core, "SynEdtResolution", FakeResolution)
        )
        stack.enter_context(
            mock.patch.object(
                runner.syn_core,
                "SynEdtControl",
                {
                    "FULL": "FULL",
                    "DIRECT_T_TO_TRANSPORT_OFF": "DIRECT_T_TO_TRANSPORT_OFF",
                    "FULL_ISOTHERMAL_COUPLING_OFF": "FULL_ISOTHERMAL_COUPLING_OFF",
                },
            )
        )
        if solve is not None:
            oracle = mock.Mock()
            if isinstance(solve, BaseException):
                oracle.solve.side_effect = solve
            elif callable(solve):
                oracle.solve.side_effect = solve
            else:
                oracle.solve.return_value = solve
            stack.enter_context(
                mock.patch.object(
                    runner.syn_core, "SynEdtOracleCase", return_value=oracle
                )
            )
        stack.enter_context(
            mock.patch.object(
                runner,
                "_code_identity",
                return_value={"kind": "test", "revision": "fixture", "dirty": False},
            )
        )
        stack.enter_context(
            mock.patch.object(
                runner,
                "_environment",
                return_value={"python": "fixture", "device": "cpu"},
            )
        )
        stack.enter_context(mock.patch.object(runner, "_peak_process_rss_bytes", return_value=1))

        def evaluator_adapter(
            result: object,
            *,
            physical: object,
            numerical: object,
            s0_sha256: str,
            numerical_contract_sha256: str,
        ) -> FakeEvaluationArtifact:
            self.assertIsInstance(result, FakeResult)
            self.assertIs(physical, physical_contract.physical)
            self.assertIsInstance(numerical, dict)
            self.assertEqual(
                numerical.get("schema_version"),
                "goal-paper-one-shot-v1-s2-numerics-v1",
            )
            self.assertEqual(len(s0_sha256), 64)
            self.assertEqual(len(numerical_contract_sha256), 64)
            return FakeEvaluationArtifact()

        stack.enter_context(
            mock.patch.object(
                runner.syn_eval,
                "artifact_from_oracle_result",
                side_effect=evaluator_adapter,
            )
        )
        return stack

    def freeze_fixture(
        self,
        *,
        root: Path,
        s0_path: Path,
        s2_path: Path,
        run_id: str = "freeze-fixture",
        supersedes_freeze_run_id: str | None = None,
    ) -> str:
        status = runner.run_freeze_cases(
            run_id=run_id,
            supersedes_freeze_run_id=supersedes_freeze_run_id,
            s0_contract_path=s0_path,
            s2_contract_path=s2_path,
            output_root=root / "runs",
            experiment_root=root / "experiment",
        )
        self.assertEqual(status, 0)
        return run_id

    def test_contract_loader_uses_dynamic_thirteen_intent_ladder(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            s0_path, s2_path = write_contracts(root)
            with self.core_patches():
                bundle = runner._load_contract_bundle(s0_path, s2_path)

        self.assertEqual(len(bundle.ladder), 13)
        self.assertEqual(bundle.ladder[-1].number, 13)
        self.assertEqual(
            bundle.ladder[-1].role,
            "INDEPENDENT_PROCESS_EXACT_REPLAY_FOR_ORACLE_FLOOR",
        )

    def test_freeze_cases_writes_only_q_and_records_one_ledger_row(self) -> None:
        generated = {
            "cases": [
                {"pool": "Q", "qualification_case": "Q0"},
                {"pool": "Q", "qualification_case": "QL"},
                {"pool": "Q", "qualification_case": "QN"},
                {"pool": "Q", "qualification_case": "QH"},
                {
                    "case_id": "development",
                    "pool": "D",
                    "qualification_case": "NOT_Q",
                },
            ]
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            s0_path, s2_path = write_contracts(root)
            output_root = root / "runs"
            experiment_root = root / "experiment"
            with self.core_patches(), mock.patch.object(
                runner.syn_core,
                "build_syn_edt_case_manifest",
                return_value=generated,
            ):
                status = runner.run_freeze_cases(
                    run_id="freeze-q-fixture",
                    s0_contract_path=s0_path,
                    s2_contract_path=s2_path,
                    output_root=output_root,
                    experiment_root=experiment_root,
                )
            frozen = json.loads(
                (output_root / "freeze-q-fixture" / "case-manifest-q-only.json").read_text(
                    encoding="utf-8"
                )
            )
            manifest = json.loads(
                (
                    experiment_root / "manifests" / "freeze-q-fixture.json"
                ).read_text(encoding="utf-8")
            )
            intent = json.loads(
                (experiment_root / "intents" / "freeze-q-fixture.json").read_text(
                    encoding="utf-8"
                )
            )
            case_manifest_path = Path(manifest["artifacts"]["case_manifest"])
            case_manifest_sha256 = hashlib.sha256(
                case_manifest_path.read_bytes()
            ).hexdigest().upper()
            s0_sha256 = hashlib.sha256(s0_path.read_bytes()).hexdigest().upper()
            s2_sha256 = hashlib.sha256(s2_path.read_bytes()).hexdigest().upper()
            ExperimentLedger(experiment_root).validate()
            rows = (experiment_root / "index.jsonl").read_text(encoding="utf-8").splitlines()

        self.assertEqual(status, 0)
        self.assertEqual(set(frozen["cases"]), {"Q0", "QL", "QN", "QH"})
        self.assertEqual(frozen["scope"], "S2_Q_ONLY")
        self.assertEqual(
            manifest["artifacts"]["case_manifest_sha256"], case_manifest_sha256
        )
        self.assertEqual(manifest["artifacts"]["s0_sha256"], s0_sha256)
        self.assertEqual(manifest["artifacts"]["s2_sha256"], s2_sha256)
        self.assertEqual(intent["s0_sha256"], s0_sha256)
        self.assertEqual(intent["s2_sha256"], s2_sha256)
        self.assertEqual(len(rows), 1)

    def test_second_freeze_records_explicit_validated_supersession(self) -> None:
        generated = {
            "cases": [
                {"pool": "Q", "qualification_case": case_id}
                for case_id in ("Q0", "QL", "QN", "QH")
            ]
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            s0_path, s2_path = write_contracts(root)
            output_root = root / "runs"
            experiment_root = root / "experiment"
            with self.core_patches(), mock.patch.object(
                runner.syn_core,
                "build_syn_edt_case_manifest",
                return_value=generated,
            ):
                self.assertEqual(
                    runner.run_freeze_cases(
                        run_id="freeze-original",
                        s0_contract_path=s0_path,
                        s2_contract_path=s2_path,
                        output_root=output_root,
                        experiment_root=experiment_root,
                    ),
                    0,
                )
                status = runner.run_freeze_cases(
                    run_id="freeze-superseding",
                    supersedes_freeze_run_id="freeze-original",
                    s0_contract_path=s0_path,
                    s2_contract_path=s2_path,
                    output_root=output_root,
                    experiment_root=experiment_root,
                )
            manifest = json.loads(
                (
                    experiment_root / "manifests" / "freeze-superseding.json"
                ).read_text(encoding="utf-8")
            )
            intent = json.loads(
                (
                    experiment_root / "intents" / "freeze-superseding.json"
                ).read_text(encoding="utf-8")
            )

        self.assertEqual(status, 0)
        self.assertEqual(manifest["supersedes"], "freeze-original")
        self.assertEqual(intent["supersedes_freeze_run_id"], "freeze-original")

    def test_run_case_cannot_bypass_a_completed_frozen_case_binding(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            s0_path, s2_path = write_contracts(root)
            experiment_root = root / "experiment"
            with self.core_patches(solve=FakeResult()):
                with self.assertRaisesRegex(
                    runner.RunnerContractError, "freeze manifest does not exist"
                ):
                    runner.run_case(
                        run_id="case-without-freeze",
                        intent_number=1,
                        freeze_run_id="missing-freeze",
                        s0_contract_path=s0_path,
                        s2_contract_path=s2_path,
                        output_root=root / "runs",
                        experiment_root=experiment_root,
                    )

            self.assertFalse((experiment_root / "intent_claims").exists())
            self.assertFalse((root / "runs" / "case-without-freeze").exists())

    def test_run_case_rejects_a_tampered_frozen_case_manifest_before_claim(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            s0_path, s2_path = write_contracts(root)
            experiment_root = root / "experiment"
            with self.core_patches(solve=FakeResult()):
                freeze_run_id = self.freeze_fixture(
                    root=root, s0_path=s0_path, s2_path=s2_path
                )
                freeze_manifest = json.loads(
                    (
                        experiment_root / "manifests" / f"{freeze_run_id}.json"
                    ).read_text(encoding="utf-8")
                )
                case_manifest_path = Path(
                    freeze_manifest["artifacts"]["case_manifest"]
                )
                with case_manifest_path.open("ab") as handle:
                    handle.write(b"\nTAMPERED_AFTER_FREEZE")

                with self.assertRaisesRegex(
                    runner.RunnerContractError, "case manifest hash mismatch"
                ):
                    runner.run_case(
                        run_id="case-after-freeze-tamper",
                        intent_number=1,
                        freeze_run_id=freeze_run_id,
                        s0_contract_path=s0_path,
                        s2_contract_path=s2_path,
                        output_root=root / "runs",
                        experiment_root=experiment_root,
                    )

            self.assertFalse((experiment_root / "intent_claims").exists())

    def test_run_case_rejects_contract_drift_from_the_freeze_before_claim(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            s0_path, s2_path = write_contracts(root)
            experiment_root = root / "experiment"
            with self.core_patches(solve=FakeResult()):
                freeze_run_id = self.freeze_fixture(
                    root=root, s0_path=s0_path, s2_path=s2_path
                )
                drifted_s0 = json.loads(s0_path.read_text(encoding="utf-8"))
                drifted_s0["budgets"]["cpu_core_hours"] = 257
                s0_path.write_text(
                    json.dumps(drifted_s0, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
                drifted_s2 = json.loads(s2_path.read_text(encoding="utf-8"))
                drifted_s2["derived_from_s0_sha256"] = hashlib.sha256(
                    s0_path.read_bytes()
                ).hexdigest().upper()
                s2_path.write_text(
                    json.dumps(drifted_s2, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )

                with self.assertRaisesRegex(
                    runner.RunnerContractError, "freeze S0 hash mismatch"
                ):
                    runner.run_case(
                        run_id="case-after-contract-drift",
                        intent_number=1,
                        freeze_run_id=freeze_run_id,
                        s0_contract_path=s0_path,
                        s2_contract_path=s2_path,
                        output_root=root / "runs",
                        experiment_root=experiment_root,
                    )

            self.assertFalse((experiment_root / "intent_claims").exists())

    def test_run_case_persists_intent_before_solve_and_accounts_exactly(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            s0_path, s2_path = write_contracts(root)
            output_root = root / "runs"
            experiment_root = root / "experiment"
            run_id = "case-intent-001"

            def solve_after_intent() -> FakeResult:
                self.assertTrue((experiment_root / "intents" / f"{run_id}.json").is_file())
                return FakeResult()

            with self.core_patches(solve=solve_after_intent), mock.patch.object(
                runner.syn_core,
                "syn_edt_result_to_artifact",
                return_value=fixture_artifact(),
            ):
                freeze_run_id = self.freeze_fixture(
                    root=root, s0_path=s0_path, s2_path=s2_path
                )
                status = runner.run_case(
                    run_id=run_id,
                    intent_number=1,
                    freeze_run_id=freeze_run_id,
                    s0_contract_path=s0_path,
                    s2_contract_path=s2_path,
                    output_root=output_root,
                    experiment_root=experiment_root,
                )
            manifest = json.loads(
                (experiment_root / "manifests" / f"{run_id}.json").read_text(
                    encoding="utf-8"
                )
            )
            case_intent = json.loads(
                (experiment_root / "intents" / f"{run_id}.json").read_text(
                    encoding="utf-8"
                )
            )
            freeze_manifest = json.loads(
                (
                    experiment_root / "manifests" / f"{freeze_run_id}.json"
                ).read_text(encoding="utf-8")
            )
            report = json.loads(
                (output_root / run_id / "report.json").read_text(encoding="utf-8")
            )
            artifact_path = Path(manifest["artifacts"]["case"])
            artifact_exists = artifact_path.is_file()
            artifact_name = artifact_path.name
            artifact_hash = hashlib.sha256(
                artifact_path.read_bytes()
            ).hexdigest().upper()
            report_path = Path(manifest["artifacts"]["report"])
            report_hash = hashlib.sha256(
                report_path.read_bytes()
            ).hexdigest().upper()
            evaluation_path = Path(manifest["artifacts"]["evaluation"])
            evaluation_hash = hashlib.sha256(
                evaluation_path.read_bytes()
            ).hexdigest().upper()
            ExperimentLedger(experiment_root).validate()

        self.assertEqual(status, 0)
        self.assertEqual(manifest["gate_outcome"], "SYN_EDT_S2_CASE_COMPLETED")
        self.assertEqual(manifest["actual_budget"]["solver_intents"], 1)
        self.assertEqual(manifest["actual_budget"]["failed_intents"], 0)
        self.assertEqual(manifest["actual_budget"]["s2_intent"], 1)
        self.assertEqual(manifest["actual_budget"]["case_pool"], "Q")
        self.assertEqual(manifest["actual_budget"]["rescue_attempts"], 0)
        self.assertEqual(manifest["artifacts"]["freeze_run_id"], freeze_run_id)
        for key in ("case_manifest_sha256", "s0_sha256", "s2_sha256"):
            self.assertEqual(
                manifest["artifacts"][key], freeze_manifest["artifacts"][key]
            )
            self.assertEqual(case_intent[key], freeze_manifest["artifacts"][key])
        required_accounting = {
            "intent_id",
            "method_id",
            "case_id",
            "seed",
            "parameter_count",
            "forward_calls",
            "automatic_differentiation_work",
            "optimizer_closures_or_updates",
            "wall_clock_seconds",
            "peak_ram_bytes",
            "peak_vram_bytes",
            "hardware_identity",
            "gross_compute",
            "failure_identity",
            "superseding_rerun_eligibility",
        }
        self.assertTrue(required_accounting <= set(manifest["actual_budget"]))
        self.assertEqual(manifest["actual_budget"]["intent_id"], run_id)
        self.assertEqual(
            manifest["actual_budget"]["method_id"], runner.ORACLE_METHOD_ID
        )
        self.assertEqual(
            manifest["actual_budget"]["case_id"], "syn-edt-fixture-q0"
        )
        self.assertEqual(manifest["actual_budget"]["seed"], 0)
        self.assertEqual(
            manifest["actual_budget"]["wall_clock_seconds"],
            manifest["actual_budget"]["wall_seconds"],
        )
        self.assertEqual(
            manifest["actual_budget"]["gross_compute"],
            manifest["actual_budget"]["cpu_core_hours"],
        )
        self.assertEqual(
            manifest["actual_budget"]["gross_compute_unit"],
            "CPU_PROCESS_CORE_HOURS",
        )
        self.assertEqual(
            manifest["actual_budget"]["failure_identity"],
            {
                "status": "NO_FAILURE",
                "failure_class": None,
                "message": None,
            },
        )
        self.assertFalse(
            manifest["actual_budget"]["superseding_rerun_eligibility"]
        )
        self.assertEqual(
            manifest["actual_budget"]["superseding_rerun_disposition"],
            "NOT_APPLICABLE_SUCCESSFUL_INTENT",
        )
        self.assertEqual(
            manifest["actual_budget"]["solver_statistics"],
            FakeResult.solver_statistics,
        )
        self.assertEqual(
            manifest["actual_budget"]["solver_counters"]["linear_solves_total"],
            49,
        )
        self.assertTrue(report["event_report"]["passed"])
        self.assertTrue(report["guard_report"]["passed"])
        self.assertTrue(artifact_exists)
        self.assertNotIn(":", artifact_name)
        self.assertEqual(manifest["artifacts"]["case_sha256"], artifact_hash)
        self.assertEqual(manifest["artifacts"]["report_sha256"], report_hash)
        self.assertEqual(
            manifest["artifacts"]["evaluation_sha256"], evaluation_hash
        )

    def test_run_case_failure_is_execution_invalid_and_consumes_intent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            s0_path, s2_path = write_contracts(root)
            output_root = root / "runs"
            experiment_root = root / "experiment"
            run_id = "case-intent-failure-001"
            with self.core_patches(solve=RuntimeError("forced fixture failure")):
                freeze_run_id = self.freeze_fixture(
                    root=root, s0_path=s0_path, s2_path=s2_path
                )
                status = runner.run_case(
                    run_id=run_id,
                    intent_number=1,
                    freeze_run_id=freeze_run_id,
                    s0_contract_path=s0_path,
                    s2_contract_path=s2_path,
                    output_root=output_root,
                    experiment_root=experiment_root,
                )
            manifest = json.loads(
                (experiment_root / "manifests" / f"{run_id}.json").read_text(
                    encoding="utf-8"
                )
            )

        self.assertEqual(status, 1)
        self.assertEqual(manifest["execution_status"], "FAILED")
        self.assertEqual(manifest["numerical_validity"], "NOT_EVALUATED")
        self.assertEqual(manifest["gate_outcome"], "SYN_EDT_S2_EXECUTION_FAILED")
        self.assertEqual(manifest["actual_budget"]["solver_intents"], 1)
        self.assertEqual(manifest["actual_budget"]["failed_intents"], 1)
        self.assertEqual(manifest["actual_budget"]["intent_id"], run_id)
        self.assertEqual(
            manifest["actual_budget"]["failure_identity"],
            {
                "status": "FAILED_INTENT",
                "failure_class": "RuntimeError",
                "message": "forced fixture failure",
            },
        )
        self.assertFalse(
            manifest["actual_budget"]["superseding_rerun_eligibility"]
        )
        self.assertEqual(
            manifest["actual_budget"]["superseding_rerun_disposition"],
            "REQUIRES_RELEVANT_INPUT_IMPLEMENTATION_OR_CONTRACT_CHANGE_"
            "AND_EXPLICIT_RECONCILIATION",
        )
        self.assertEqual(manifest["actual_budget"]["solver_statistics"], {})
        self.assertEqual(manifest["failure_class"], "RuntimeError")
        self.assertNotIn("NO_GO", manifest["gate_outcome"])

    def test_inconsistent_core_solver_total_is_execution_invalid(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            s0_path, s2_path = write_contracts(root)
            result = FakeResult()
            result.solver_statistics = {
                **FakeResult.solver_statistics,
                "linear_solves_total": 48,
            }
            experiment_root = root / "experiment"
            run_id = "case-intent-invalid-solver-total"
            with self.core_patches(solve=result):
                freeze_run_id = self.freeze_fixture(
                    root=root, s0_path=s0_path, s2_path=s2_path
                )
                status = runner.run_case(
                    run_id=run_id,
                    intent_number=1,
                    freeze_run_id=freeze_run_id,
                    s0_contract_path=s0_path,
                    s2_contract_path=s2_path,
                    output_root=root / "runs",
                    experiment_root=experiment_root,
                )
            manifest = json.loads(
                (experiment_root / "manifests" / f"{run_id}.json").read_text(
                    encoding="utf-8"
                )
            )

        self.assertEqual(status, 1)
        self.assertEqual(manifest["failure_class"], "RunnerContractError")
        self.assertEqual(manifest["actual_budget"]["failed_intents"], 1)
        self.assertIn(
            "exact component sum",
            manifest["actual_budget"]["failure_identity"]["message"],
        )
        self.assertEqual(manifest["actual_budget"]["solver_statistics"], {})

    def test_selected_case_loader_rejects_any_mutated_evidence_carrier(self) -> None:
        for carrier in ("case", "report", "evaluation"):
            with self.subTest(carrier=carrier), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                s0_path, s2_path = write_contracts(root)
                s0_sha = hashlib.sha256(s0_path.read_bytes()).hexdigest().upper()
                s2_sha = hashlib.sha256(s2_path.read_bytes()).hexdigest().upper()
                output_root = root / "runs"
                experiment_root = root / "experiment"
                run_id = f"mutated-{carrier}"
                result = FakeResult(s0_sha256=s0_sha, numerical_sha256=s2_sha)
                with self.core_patches(solve=result), mock.patch.object(
                    runner.syn_core,
                    "syn_edt_result_to_artifact",
                    return_value=fixture_artifact(),
                ):
                    freeze_run_id = self.freeze_fixture(
                        root=root, s0_path=s0_path, s2_path=s2_path
                    )
                    self.assertEqual(
                        runner.run_case(
                            run_id=run_id,
                            intent_number=1,
                            freeze_run_id=freeze_run_id,
                            s0_contract_path=s0_path,
                            s2_contract_path=s2_path,
                            output_root=output_root,
                            experiment_root=experiment_root,
                        ),
                        0,
                    )
                manifest = json.loads(
                    (experiment_root / "manifests" / f"{run_id}.json").read_text(
                        encoding="utf-8"
                    )
                )
                carrier_path = Path(manifest["artifacts"][carrier])
                with carrier_path.open("ab") as handle:
                    handle.write(b"\nMUTATED_AFTER_FINALIZATION")
                evaluation = SimpleNamespace(
                    physical_contract_id=runner.PHYSICAL_CONTRACT_ID,
                    case_id="syn-edt-fixture-q0",
                    s0_sha256=s0_sha,
                    numerical_contract_sha256=s2_sha,
                )
                with mock.patch.object(
                    runner.syn_eval.SynEdtEvaluationArtifact,
                    "read",
                    return_value=evaluation,
                ):
                    with self.assertRaisesRegex(
                        runner.RunnerContractError, f"{carrier} artifact hash mismatch"
                    ):
                        runner._load_selected_case_runs(
                            experiment_root,
                            [run_id],
                            (runner.S2Intent.from_payload(LADDER[0]),),
                            expected_s0_sha256=s0_sha,
                            expected_numerical_sha256=s2_sha,
                            expected_q_manifest=runner._q_only_manifest(
                                generated_q_case_manifest()
                            ),
                        )

    def test_selected_case_loader_rejects_sealed_identity_mismatch(self) -> None:
        scenarios = (
            ("report_contract", "report artifact contract mismatch"),
            ("case_id", "case artifact identity mismatch"),
            ("physical_contract", "case artifact identity mismatch"),
        )
        for scenario, expected_error in scenarios:
            with self.subTest(scenario=scenario), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                s0_path, s2_path = write_contracts(root)
                s0_sha = hashlib.sha256(s0_path.read_bytes()).hexdigest().upper()
                s2_sha = hashlib.sha256(s2_path.read_bytes()).hexdigest().upper()
                result = FakeResult(
                    s0_sha256="F" * 64 if scenario == "report_contract" else s0_sha,
                    numerical_sha256=s2_sha,
                )
                artifact = fixture_artifact(
                    case_id=(
                        "wrong-case-id"
                        if scenario == "case_id"
                        else "syn-edt-fixture-q0"
                    ),
                    physical_contract_id=(
                        "WRONG_PHYSICAL_CONTRACT"
                        if scenario == "physical_contract"
                        else runner.PHYSICAL_CONTRACT_ID
                    ),
                )
                experiment_root = root / "experiment"
                run_id = f"identity-{scenario}"
                with self.core_patches(solve=result), mock.patch.object(
                    runner.syn_core,
                    "syn_edt_result_to_artifact",
                    return_value=artifact,
                ):
                    freeze_run_id = self.freeze_fixture(
                        root=root, s0_path=s0_path, s2_path=s2_path
                    )
                    self.assertEqual(
                        runner.run_case(
                            run_id=run_id,
                            intent_number=1,
                            freeze_run_id=freeze_run_id,
                            s0_contract_path=s0_path,
                            s2_contract_path=s2_path,
                            output_root=root / "runs",
                            experiment_root=experiment_root,
                        ),
                        0,
                    )
                evaluation = SimpleNamespace(
                    physical_contract_id=runner.PHYSICAL_CONTRACT_ID,
                    case_id="syn-edt-fixture-q0",
                    s0_sha256=s0_sha,
                    numerical_contract_sha256=s2_sha,
                )
                with mock.patch.object(
                    runner.syn_eval.SynEdtEvaluationArtifact,
                    "read",
                    return_value=evaluation,
                ):
                    with self.assertRaisesRegex(
                        runner.RunnerContractError, expected_error
                    ):
                        runner._load_selected_case_runs(
                            experiment_root,
                            [run_id],
                            (runner.S2Intent.from_payload(LADDER[0]),),
                            expected_s0_sha256=s0_sha,
                            expected_numerical_sha256=s2_sha,
                            expected_q_manifest=runner._q_only_manifest(
                                generated_q_case_manifest()
                            ),
                        )

    def test_concurrent_duplicate_intent_has_exactly_one_atomic_claim(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            s0_path, s2_path = write_contracts(root)
            experiment_root = root / "experiment"
            barrier = threading.Barrier(2)
            original_order_check = runner._assert_intent_order

            def synchronized_order_check(
                selected_root: Path, intent: runner.S2Intent
            ) -> None:
                original_order_check(selected_root, intent)
                barrier.wait(timeout=5.0)

            def execute(run_id: str) -> int:
                return runner.run_case(
                    run_id=run_id,
                    intent_number=1,
                    freeze_run_id=freeze_run_id,
                    s0_contract_path=s0_path,
                    s2_contract_path=s2_path,
                    output_root=root / "runs",
                    experiment_root=experiment_root,
                )

            with self.core_patches(solve=FakeResult()), mock.patch.object(
                runner.syn_core,
                "syn_edt_result_to_artifact",
                return_value=fixture_artifact(),
            ), mock.patch.object(
                runner,
                "_assert_intent_order",
                side_effect=synchronized_order_check,
            ):
                freeze_run_id = self.freeze_fixture(
                    root=root, s0_path=s0_path, s2_path=s2_path
                )
                with ThreadPoolExecutor(max_workers=2) as executor:
                    futures = [
                        executor.submit(execute, "duplicate-a"),
                        executor.submit(execute, "duplicate-b"),
                    ]
                    outcomes: list[int | str] = []
                    for future in futures:
                        try:
                            outcomes.append(future.result(timeout=10.0))
                        except runner.RunnerContractError as exc:
                            outcomes.append(str(exc))

            manifests = [
                path
                for path in (experiment_root / "manifests").glob("*.json")
                if json.loads(path.read_text(encoding="utf-8")).get("gate")
                == "S2_CASE"
            ]

        self.assertEqual(outcomes.count(0), 1)
        blocked = [item for item in outcomes if isinstance(item, str)]
        self.assertEqual(len(blocked), 1)
        self.assertIn("RECONCILIATION_REQUIRED", blocked[0])
        self.assertEqual(len(manifests), 1)

    def test_orphan_intent_blocks_automatic_replay(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            s0_path, s2_path = write_contracts(root)
            experiment_root = root / "experiment"
            orphan_path = experiment_root / "intents" / "orphan.json"
            orphan_path.parent.mkdir(parents=True)
            orphan_path.write_text(
                json.dumps(
                    {
                        "schema_version": "syn-edt-s2-case-intent-v1",
                        "run_id": "orphan",
                        "physical_contract_id": runner.PHYSICAL_CONTRACT_ID,
                        "split_id": runner.SPLIT_ID,
                        "ladder": LADDER[0],
                    }
                ),
                encoding="utf-8",
            )
            with self.core_patches(solve=FakeResult()), mock.patch.object(
                runner.syn_core,
                "syn_edt_result_to_artifact",
                return_value=fixture_artifact(),
            ):
                freeze_run_id = self.freeze_fixture(
                    root=root, s0_path=s0_path, s2_path=s2_path
                )
                with self.assertRaisesRegex(
                    runner.RunnerContractError,
                    "ORPHAN_S2_INTENT_RECONCILIATION_REQUIRED",
                ):
                    runner.run_case(
                        run_id="automatic-replay-must-not-start",
                        intent_number=1,
                        freeze_run_id=freeze_run_id,
                        s0_contract_path=s0_path,
                        s2_contract_path=s2_path,
                        output_root=root / "runs",
                        experiment_root=experiment_root,
                    )
            self.assertFalse(
                (root / "runs" / "automatic-replay-must-not-start").exists()
            )
            self.assertFalse(
                (
                    experiment_root
                    / "manifests"
                    / "automatic-replay-must-not-start.json"
                ).exists()
            )

    def test_s2_summary_never_infers_pass_without_full_adjudicator(self) -> None:
        artifact = fixture_artifact("syn-edt-fixture-qn")
        manifests = {
            number: {"execution_status": "COMPLETED"} for number in range(1, 14)
        }
        reports = {
            number: {
                "event_report": {"passed": True},
                "guard_report": {"passed": True},
            }
            for number in range(1, 14)
        }
        artifacts = {number: artifact for number in range(1, 14)}
        with mock.patch.object(
            runner.syn_core,
            "compare_syn_edt_artifacts",
            return_value={"passed": True},
            create=True,
        ), mock.patch.object(
            runner.syn_core, "adjudicate_syn_edt_s2", new=None, create=True
        ):
            summary = runner._build_s2_summary(
                contract=SimpleNamespace(
                    physical={"absolute_waveform": {"cycles": 2}}
                ),
                numerical_contract={},
                manifests=manifests,
                reports=reports,
                artifacts=artifacts,
            )

        self.assertFalse(summary["adjudicated"])
        self.assertFalse(summary["passed"])
        self.assertEqual(summary["outcome"], "S2_NOT_ADJUDICATED")
        self.assertIn("independent_process_replay", summary["comparisons"])

    def test_summarize_s2_rejects_thirteen_cases_from_mixed_freezes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            s0_path, s2_path = write_contracts(root)
            s0_sha256 = hashlib.sha256(s0_path.read_bytes()).hexdigest().upper()
            s2_sha256 = hashlib.sha256(s2_path.read_bytes()).hexdigest().upper()
            experiment_root = root / "experiment"
            output_root = root / "runs"
            result = FakeResult(
                s0_sha256=s0_sha256, numerical_sha256=s2_sha256
            )
            evaluation = SimpleNamespace(
                physical_contract_id=runner.PHYSICAL_CONTRACT_ID,
                case_id="syn-edt-fixture-q0",
                s0_sha256=s0_sha256,
                numerical_contract_sha256=s2_sha256,
            )
            case_run_ids: list[str] = []
            with self.core_patches(solve=result), mock.patch.object(
                runner.syn_core,
                "syn_edt_result_to_artifact",
                return_value=fixture_artifact(),
            ), mock.patch.object(
                runner.syn_eval.SynEdtEvaluationArtifact,
                "read",
                return_value=evaluation,
            ):
                first_freeze = self.freeze_fixture(
                    root=root,
                    s0_path=s0_path,
                    s2_path=s2_path,
                    run_id="freeze-first",
                )
                for number in range(1, 14):
                    if number == 2:
                        selected_freeze = self.freeze_fixture(
                            root=root,
                            s0_path=s0_path,
                            s2_path=s2_path,
                            run_id="freeze-second",
                            supersedes_freeze_run_id=first_freeze,
                        )
                    elif number == 1:
                        selected_freeze = first_freeze
                    run_id = f"mixed-freeze-case-{number:02d}"
                    self.assertEqual(
                        runner.run_case(
                            run_id=run_id,
                            intent_number=number,
                            freeze_run_id=selected_freeze,
                            s0_contract_path=s0_path,
                            s2_contract_path=s2_path,
                            output_root=output_root,
                            experiment_root=experiment_root,
                        ),
                        0,
                    )
                    case_run_ids.append(run_id)

                status = runner.run_summarize_s2(
                    run_id="mixed-freeze-summary",
                    case_run_ids=case_run_ids,
                    s0_contract_path=s0_path,
                    s2_contract_path=s2_path,
                    output_root=output_root,
                    experiment_root=experiment_root,
                )
            summary = json.loads(
                (output_root / "mixed-freeze-summary" / "summary.json").read_text(
                    encoding="utf-8"
                )
            )

        self.assertEqual(status, 1)
        self.assertEqual(summary["reason"], "SUMMARY_INPUT_INVALID")
        self.assertIn("same S2 freeze binding", summary["failure"])

    def test_s2_summary_uses_exact_floor_schema_and_preserves_not_adjudicated(
        self,
    ) -> None:
        manifests = {
            number: {"execution_status": "COMPLETED"} for number in range(1, 14)
        }
        reports = {
            number: {
                "event_report": {
                    "passed": True,
                    "event_time_s": [0.1, 1.1],
                },
                "guard_report": {"passed": True},
            }
            for number in range(1, 14)
        }
        artifacts = {
            number: SimpleNamespace(intent_number=number) for number in range(1, 14)
        }
        floor = {
            "schema_version": runner.syn_eval.FLOOR_SCHEMA,
            "physical_contract_id": runner.PHYSICAL_CONTRACT_ID,
            "s0_sha256": "A" * 64,
            "numerical_contract_sha256": "B" * 64,
            "source_case_id": "syn-edt-fixture-qn",
            "component_order": list(runner.syn_eval.COMPONENT_ORDER),
            "cycles": [{"cycle": 1}, {"cycle": 2}],
            "normalizers_by_case": {
                "syn-edt-fixture-qn": [
                    {"defect_flux": 1.0, "port_current": 2.0},
                    {"defect_flux": 1.0, "port_current": 4.0},
                ]
            },
            "sealed_before_neural_work": True,
            "seal_sha256": "FIXTURE_SEAL_HASH",
        }

        compared_pairs: list[tuple[int, int]] = []

        def compare(left: object, right: object, *_: object) -> dict[str, object]:
            pair = (left.intent_number, right.intent_number)
            compared_pairs.append(pair)
            effect = pair in {(6, 10), (6, 12)}
            peak = 0.02 if effect else 1.0e-7
            event = 0.01 if effect else 1.0e-7
            current = 0.4 if effect else 2.0e-7
            return {
                "passed": True,
                "thermal_component_deltas_by_cycle": [
                    [peak, event, None],
                    [peak, event, None],
                ],
                "thermal_effect_signed_by_cycle": {
                    "peak_depletion": [peak, peak],
                    "event_time": [event, event],
                    "current_trace_rms": [current, current],
                },
                "thermal_current_rms_difference_a_by_cycle": [current, current],
            }

        adjudicator = mock.Mock(
            return_value={
                "adjudicated": False,
                "passed": False,
                "reason": "FIXTURE_REMAINS_OPEN",
            }
        )
        numerical_contract = {
            "qualification_ladder": LADDER,
            "endpoint_and_floor_contract": {
                "declared_solver_tolerance_each_dimensionless_component": 1.0e-6
            },
        }
        with mock.patch.object(
            runner.syn_core,
            "compare_syn_edt_artifacts",
            side_effect=compare,
        ), mock.patch.object(
            runner.syn_core,
            "adjudicate_syn_edt_s2",
            adjudicator,
        ):
            summary = runner._build_s2_summary(
                contract=SimpleNamespace(
                    physical={"absolute_waveform": {"cycles": 2}}
                ),
                numerical_contract=numerical_contract,
                manifests=manifests,
                reports=reports,
                artifacts=artifacts,
                floor_seal=floor,
            )

        self.assertIn((6, 10), compared_pairs)
        self.assertIn((6, 12), compared_pairs)
        self.assertEqual(
            summary["comparisons"]["endpoint_component_floors"], floor
        )
        direct = summary["comparisons"]["full_vs_direct_thermal_effect"][
            "thermal_gate"
        ]
        self.assertTrue(direct["ready"])
        self.assertTrue(direct["effect_exceeds_numerical_uncertainty"])
        self.assertEqual(direct["current_normalizers_by_cycle_a"], [2.0, 4.0])
        self.assertEqual(direct["effect_by_cycle"][0][2], 0.2)
        adjudicator.assert_called_once()
        self.assertFalse(summary["adjudicated"])
        self.assertFalse(summary["passed"])
        self.assertEqual(summary["outcome"], "S2_NOT_ADJUDICATED")
        self.assertEqual(summary["reason"], "FIXTURE_REMAINS_OPEN")

    def test_parser_exposes_three_commands_and_accepts_intent_thirteen(self) -> None:
        parser = runner.build_parser()
        freeze = parser.parse_args(["freeze-cases", "--run-id", "freeze"])
        case = parser.parse_args(
            [
                "run-case",
                "--run-id",
                "case-13",
                "--intent",
                "13",
                "--freeze-run-id",
                "freeze",
            ]
        )
        with self.assertRaises(SystemExit):
            parser.parse_args(
                ["run-case", "--run-id", "case-without-freeze", "--intent", "1"]
            )
        summary = parser.parse_args(
            [
                "summarize-s2",
                "--run-id",
                "summary",
                *sum(
                    (["--case-run-id", f"case-{number}"] for number in range(1, 14)),
                    [],
                ),
            ]
        )

        self.assertEqual(freeze.command, "freeze-cases")
        self.assertEqual(case.command, "run-case")
        self.assertEqual(case.intent, 13)
        self.assertEqual(case.freeze_run_id, "freeze")
        self.assertEqual(summary.command, "summarize-s2")
        self.assertEqual(len(summary.case_run_ids), 13)


if __name__ == "__main__":
    unittest.main()
