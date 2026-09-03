from __future__ import annotations

import unittest
from pathlib import Path
import tempfile
import hashlib
import json
import shutil
from unittest import mock

import numpy as np
import torch
from torch import nn

from pinn_pcm_sci.phk_v22r_pinn import (
    FrequencyBand,
    POTENTIAL_TRANSFORM_EXACT_TOP_RAW,
    PhkV22RModel,
)
from pinn_pcm_sci.phk_v22r_training import load_case_physics
from pinn_pcm_sci.phk_v22r_prediction import _load_model
from pinn_pcm_sci.phk_v23_lf0 import (
    ARM_A,
    ARM_B,
    ARM_C,
    RUN_ARMS,
    REQUIRED_DEPLOYED_RUNTIME_RELATIVE_PATHS,
    LF0LowFidelityBatchStream,
    LF0OptimizerStateMachine,
    LF0PhysicsBatchStream,
    build_training_config,
    build_exact_top_model,
    cosine_anchor_weight,
    contract_identity,
    iter_run_steps,
    load_contracts,
    normalized_low_fidelity_loss,
    potential_maximum_principle_guard,
    potential_maximum_principle_windowed_guard,
    physics_active_windows,
    _write_checkpoint,
    _low_fidelity_objective,
    _physics_objective,
    _assert_deployed_source_identity,
    _validate_c_trigger,
    run_reference_blind_gpu_arm,
)


ROOT = Path(__file__).resolve().parents[1]


def _runner_admission_tree(
    *, include_qualification: bool = True
) -> tuple[tempfile.TemporaryDirectory[str], Path, Path, str]:
    temporary = tempfile.TemporaryDirectory()
    root = Path(temporary.name).resolve()
    file_hashes: dict[str, str] = {}
    for relative in sorted(REQUIRED_DEPLOYED_RUNTIME_RELATIVE_PATHS):
        source = ROOT / Path(relative)
        target = root / Path(relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        file_hashes[relative] = hashlib.sha256(target.read_bytes()).hexdigest().upper()
    lines = "".join(
        f"{relative}={digest}\n" for relative, digest in sorted(file_hashes.items())
    )
    identity = "LF0-BUNDLE-" + hashlib.sha256(lines.encode("utf-8")).hexdigest().upper()
    source_commit = "1" * 40
    data = json.loads(
        (root / "configs/phk_v23/data_contract_lf0_medium_only.json").read_text(
            encoding="utf-8"
        )
    )
    decision = json.loads(
        (root / "configs/phk_v23/decision_contract_lf0_attribution.json").read_text(
            encoding="utf-8"
        )
    )
    medium = data["training_source"]
    manifest_payload: dict[str, object] = {
        "schema_id": "phk-v23-lf0-deployed-source-manifest-v1",
        "identity_definition": "SHA256_OF_SORTED_PATH_EQUALS_UPPERCASE_SHA256_LINES",
        "source_identity": identity,
        "source_commit": source_commit,
        "files": file_hashes,
        "training_input": {
            "path": medium["path"],
            "sha256": medium["sha256"],
            "size_bytes": 1,
        },
    }
    if include_qualification:
        qualification = root / "docs/experiment/artifacts/lf0-cpu-qualification.json"
        qualification.parent.mkdir(parents=True, exist_ok=True)
        contract_paths = {
            "program": "configs/phk_v23/program_contract_lf0_exact_top_warmstart.json",
            "method": "configs/phk_v23/method_contract_lf0_exact_top_warmstart.json",
            "data": "configs/phk_v23/data_contract_lf0_medium_only.json",
            "decision": "configs/phk_v23/decision_contract_lf0_attribution.json",
        }
        input_identities = {
            "low_fidelity_training_source": {**medium, "size_bytes": 1},
            "qualification_fine": data["qualification_only"]["fine"],
            "qualification_extra_fine": data["qualification_only"]["extra_fine"],
            **decision["qualification_inputs"],
        }
        qualification.write_text(
            json.dumps(
                {
                    "schema_id": "phk-v23-lf0-cpu-qualification-v1",
                    "task_id": "PHK_V23_LF0_EXACT_TOP_WARMSTART_ATTRIBUTION_EXECUTE",
                    "status": "LF0_CPU_QUALIFIED",
                    "passed": True,
                    "blockers": [],
                    "qualified_source_identity": identity,
                    "source_commit": source_commit,
                    "contract_identities": {
                        role: {"path": path, "sha256": file_hashes[path]}
                        for role, path in contract_paths.items()
                    },
                    "input_identities": input_identities,
                }
            ),
            encoding="utf-8",
        )
        manifest_payload["cpu_qualification"] = {
            "path": qualification.relative_to(root).as_posix(),
            "sha256": hashlib.sha256(qualification.read_bytes()).hexdigest().upper(),
            "size_bytes": qualification.stat().st_size,
        }
    manifest = root / "deployed-source-manifest.json"
    manifest.write_text(json.dumps(manifest_payload), encoding="utf-8")
    return temporary, root, manifest, identity


class _ConstantLatent(nn.Module):
    def __init__(self, value: float) -> None:
        super().__init__()
        self.value = float(value)

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        return features.new_full((features.shape[0], 1), self.value)


def _exact_top_model(*, potential_latent: float = 0.0) -> PhkV22RModel:
    physics, _, _ = load_case_physics("FULL")
    model = PhkV22RModel(
        physics=physics,
        arm="STRONG_RAW",
        hidden_width=8,
        hidden_layers=2,
        frequency_band=FrequencyBand.band_a(),
        potential_output_transform=POTENTIAL_TRANSFORM_EXACT_TOP_RAW,
    ).to(dtype=torch.float64)
    model.heads["potential"] = _ConstantLatent(potential_latent)
    return model


class PhkV23LF0Tests(unittest.TestCase):
    def test_four_contracts_load_as_one_cross_validated_identity(self) -> None:
        contracts = load_contracts()
        identities = contract_identity()
        self.assertEqual(set(contracts), {"program", "method", "data", "decision"})
        self.assertEqual(set(identities), set(contracts))
        self.assertTrue(all(len(item["sha256"]) == 64 for item in identities.values()))
        self.assertEqual(
            tuple(contracts["program"]["run_limits"]["fixed_order"]), RUN_ARMS
        )

    def test_runner_rejects_manifest_without_runtime_closure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "pinn_pcm_sci" / "phk_v23_lf0.py"
            source.parent.mkdir(parents=True)
            source.write_bytes(b"frozen-lf0-source")
            digest = hashlib.sha256(source.read_bytes()).hexdigest().upper()
            identity = "LF0-BUNDLE-" + hashlib.sha256(
                f"pinn_pcm_sci/phk_v23_lf0.py={digest}\n".encode("utf-8")
            ).hexdigest().upper()
            manifest = root / "deployed-source-manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "schema_id": "phk-v23-lf0-deployed-source-manifest-v1",
                        "identity_definition": (
                            "SHA256_OF_SORTED_PATH_EQUALS_UPPERCASE_SHA256_LINES"
                        ),
                        "source_identity": identity,
                        "files": {"pinn_pcm_sci/phk_v23_lf0.py": digest},
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "runtime closure"):
                _assert_deployed_source_identity(
                    identity,
                    root=root,
                    manifest_path=manifest,
                )

    def test_runner_requires_bound_passed_cpu_qualification(self) -> None:
        temporary, root, manifest, identity = _runner_admission_tree(
            include_qualification=False
        )
        self.addCleanup(temporary.cleanup)
        with self.assertRaisesRegex(ValueError, "CPU qualification"):
            _assert_deployed_source_identity(
                identity, root=root, manifest_path=manifest
            )

    def test_runner_consumes_only_matching_passed_cpu_qualification(self) -> None:
        temporary, root, manifest, identity = _runner_admission_tree()
        self.addCleanup(temporary.cleanup)
        admission = _assert_deployed_source_identity(
            identity, root=root, manifest_path=manifest
        )
        self.assertEqual(admission["status"], "LF0_CPU_QUALIFIED")

        manifest_payload = json.loads(manifest.read_text(encoding="utf-8"))
        qualification = root / manifest_payload["cpu_qualification"]["path"]
        record = json.loads(qualification.read_text(encoding="utf-8"))
        record["passed"] = False
        qualification.write_text(json.dumps(record), encoding="utf-8")
        manifest_payload["cpu_qualification"]["sha256"] = hashlib.sha256(
            qualification.read_bytes()
        ).hexdigest().upper()
        manifest_payload["cpu_qualification"]["size_bytes"] = qualification.stat().st_size
        manifest.write_text(json.dumps(manifest_payload), encoding="utf-8")
        with self.assertRaisesRegex(PermissionError, "did not pass"):
            _assert_deployed_source_identity(
                identity, root=root, manifest_path=manifest
            )

    def test_c_trigger_rejects_fabricated_all_true_record_without_evidence_bindings(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            trigger = Path(directory) / "c-trigger.json"
            trigger.write_text(
                json.dumps(
                    {
                        "schema_id": "phk-v23-lf0-c-trigger-v1",
                        "task_id": "PHK_V23_LF0_EXACT_TOP_WARMSTART_ATTRIBUTION_EXECUTE",
                        "action": "RUN_C_EXACT_TOP_COMPUTE_CONTROL_IF_TRIGGERED",
                        "b_competent": True,
                        "b_provisional_increment_vs_all_comparators": True,
                        "pde_ratio_pass": True,
                        "preservation_pass": True,
                        "potential_validity_pass": True,
                        "input_bindings": {},
                        "stress_fields_or_metrics_read": False,
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(PermissionError, "evidence bindings"):
                _validate_c_trigger(trigger)

    def test_c_trigger_is_itself_source_bound_without_uploading_prior_run_carriers(self) -> None:
        temporary, root, manifest, _ = _runner_admission_tree()
        self.addCleanup(temporary.cleanup)
        manifest_payload = json.loads(manifest.read_text(encoding="utf-8"))
        decision_relative = "configs/phk_v23/decision_contract_lf0_attribution.json"
        decision_path = root / decision_relative
        bindings = {
            name: {
                "path": f"C:/local-lf0-evidence/{name}.bin",
                "sha256": "A" * 64,
                "size_bytes": 1,
            }
            for name in (
                "decision_contract",
                "a_prediction",
                "a_final_checkpoint",
                "a_physics_hash_log",
                "b_prediction",
                "b_lf_data_only_prediction",
                "b_final_checkpoint",
                "b_lf_data_only_checkpoint",
                "b_physics_hash_log",
                "lf_only_prediction",
            )
        }
        bindings["decision_contract"] = {
            "path": str((ROOT / decision_relative).resolve()),
            "sha256": manifest_payload["files"][decision_relative],
            "size_bytes": decision_path.stat().st_size,
        }
        trigger = root / "cloud/phk_v23_lf0_autodl/c-trigger.json"
        trigger.parent.mkdir(parents=True, exist_ok=True)
        trigger.write_text(
            json.dumps(
                {
                    "schema_id": "phk-v23-lf0-c-trigger-v1",
                    "task_id": "PHK_V23_LF0_EXACT_TOP_WARMSTART_ATTRIBUTION_EXECUTE",
                    "action": "RUN_C_EXACT_TOP_COMPUTE_CONTROL_IF_TRIGGERED",
                    "b_competent": True,
                    "b_provisional_increment_vs_all_comparators": True,
                    "pde_ratio_pass": True,
                    "preservation_pass": True,
                    "potential_validity_pass": True,
                    "input_bindings": bindings,
                    "stress_fields_or_metrics_read": False,
                }
            ),
            encoding="utf-8",
        )
        trigger_relative = trigger.relative_to(root).as_posix()
        manifest_payload["files"][trigger_relative] = hashlib.sha256(
            trigger.read_bytes()
        ).hexdigest().upper()
        lines = "".join(
            f"{relative}={digest}\n"
            for relative, digest in sorted(manifest_payload["files"].items())
        )
        identity = "LF0-BUNDLE-" + hashlib.sha256(lines.encode()).hexdigest().upper()
        manifest_payload["source_identity"] = identity
        qualification = root / manifest_payload["cpu_qualification"]["path"]
        qualification_payload = json.loads(qualification.read_text(encoding="utf-8"))
        qualification_payload["qualified_source_identity"] = identity
        qualification.write_text(json.dumps(qualification_payload), encoding="utf-8")
        manifest_payload["cpu_qualification"]["sha256"] = hashlib.sha256(
            qualification.read_bytes()
        ).hexdigest().upper()
        manifest_payload["cpu_qualification"]["size_bytes"] = qualification.stat().st_size
        manifest.write_text(json.dumps(manifest_payload), encoding="utf-8")

        _assert_deployed_source_identity(identity, root=root, manifest_path=manifest)
        result = _validate_c_trigger(
            trigger,
            source_identity=identity,
            root=root,
            manifest_path=manifest,
        )
        self.assertEqual(result["task_id"], "PHK_V23_LF0_EXACT_TOP_WARMSTART_ATTRIBUTION_EXECUTE")
        trigger.write_text(trigger.read_text(encoding="utf-8") + "\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "not bound"):
            _validate_c_trigger(
                trigger,
                source_identity=identity,
                root=root,
                manifest_path=manifest,
            )

    def test_numerical_failure_writes_truthful_recoverable_terminal_summary(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "run"

            def fail_after_output(**_: object) -> dict[str, object]:
                output.mkdir()
                (output / "training-log.jsonl").write_text(
                    '{"global_step":1}\n', encoding="utf-8"
                )
                raise FloatingPointError("nonfinite objective at step 2")

            with mock.patch(
                "pinn_pcm_sci.phk_v23_lf0._execute_reference_blind_gpu_arm",
                side_effect=fail_after_output,
            ):
                result = run_reference_blind_gpu_arm(
                    arm=ARM_A,
                    output_root=output,
                    device_name="cuda:0",
                    source_identity="LF0-BUNDLE-TEST",
                    hourly_price_cny=1.0,
                )
            written = json.loads((output / "summary.json").read_text(encoding="utf-8"))
        self.assertEqual(result["status"], "LF0_NUMERICAL_OR_IDENTITY_INVALID")
        self.assertEqual(written, result)
        self.assertIn("training-log.jsonl", result["artifacts_recovered_before_shutdown"])

    def test_exact_top_raw_transform_satisfies_top_and_zero_waveform(self) -> None:
        model = _exact_top_model(potential_latent=-3.0)
        coordinates = torch.tensor(
            [
                [-0.4, model.physics.z_max, 0.20],
                [0.3, model.physics.z_max, 1.45],
                [0.0, 0.35, 0.0],
                [0.0, 0.35, 0.75],
            ],
            dtype=torch.float64,
        )
        potential = model(coordinates)[:, 0:1]
        expected = model.physics.waveform(coordinates[:, 2:3])
        self.assertTrue(torch.equal(potential[:2], expected[:2]))
        self.assertEqual(float(potential[2]), 0.0)
        self.assertEqual(float(potential[3]), 0.0)

    def test_exact_top_raw_transform_has_no_artificial_interior_lower_bound(self) -> None:
        model = _exact_top_model(potential_latent=-3.0)
        coordinates = torch.tensor([[0.0, 0.5, 0.20]], dtype=torch.float64)
        diagnostics = model.read_only_output_diagnostics(coordinates)
        waveform = model.physics.waveform(coordinates[:, 2:3])
        z_fraction = coordinates[:, 1:2]
        self.assertLess(float(diagnostics.output.fields[0, 0]), 0.0)
        self.assertTrue(
            torch.equal(
                diagnostics.analytic_output_jacobians["potential"],
                waveform * (1.0 - z_fraction),
            )
        )

    def test_physics_schedule_uses_physics_local_steps(self) -> None:
        observed = [
            physics_active_windows(step)
            for step in (1, 150, 151, 350, 351, 550, 551, 2000)
        ]
        self.assertEqual(observed, [1, 1, 2, 2, 3, 3, 4, 4])

    def test_run_plans_preserve_b_optimizer_and_sampler_boundaries(self) -> None:
        a = list(iter_run_steps(ARM_A))
        b = list(iter_run_steps(ARM_B))
        c = list(iter_run_steps(ARM_C))
        self.assertEqual((len(a), len(b), len(c)), (1200, 2000, 2000))
        self.assertTrue(all(step.uses_physics and not step.uses_low_fidelity for step in a))
        self.assertTrue(all(step.physics_local_step == step.global_step for step in a))
        self.assertTrue(all(step.uses_physics and not step.uses_low_fidelity for step in c))
        self.assertEqual([step.stage for step in b[:800]], ["B0_LF_ONLY"] * 800)
        self.assertTrue(all(not step.uses_physics for step in b[:800]))
        self.assertTrue(all(step.physics_local_step is None for step in b[:800]))
        self.assertEqual(b[800].physics_local_step, 1)
        self.assertEqual(b[800].low_fidelity_step, 801)
        self.assertEqual(b[999].physics_local_step, 200)
        self.assertEqual(b[999].low_fidelity_step, 1000)
        self.assertEqual(b[1000].physics_local_step, 201)
        self.assertIsNone(b[1000].low_fidelity_step)
        self.assertTrue(all(not step.uses_low_fidelity for step in b[1000:]))
        self.assertEqual(sum(step.uses_physics for step in b), 1200)
        self.assertEqual(sum(step.uses_low_fidelity for step in b), 1000)

    def test_training_configs_freeze_expected_total_steps_and_raw_arm(self) -> None:
        self.assertEqual(build_training_config(ARM_A, "cuda:0").updates, 1200)
        self.assertEqual(build_training_config(ARM_B, "cuda:0").updates, 2000)
        self.assertEqual(build_training_config(ARM_C, "cuda:0").updates, 2000)
        for arm in (ARM_A, ARM_B, ARM_C):
            config = build_training_config(arm, "cuda:0")
            self.assertEqual(config.arm, "STRONG_RAW")
            self.assertEqual(config.seed, 17)
            self.assertEqual(config.dtype, "float64")
            self.assertEqual(config.refresh_updates, 250)

    def test_b_optimizer_state_is_destroyed_then_b1_b2_share_new_adam(self) -> None:
        model = nn.Linear(1, 1, dtype=torch.float64)
        machine = LF0OptimizerStateMachine(model=model, arm=ARM_B, learning_rate=1.0e-3)
        b0 = next(iter_run_steps(ARM_B))
        optimizer_b0 = machine.prepare(b0)
        loss = model(torch.ones((1, 1), dtype=torch.float64)).square().mean()
        loss.backward()
        optimizer_b0.step()
        self.assertTrue(optimizer_b0.state)

        b1 = list(iter_run_steps(ARM_B))[800]
        optimizer_b1 = machine.prepare(b1)
        self.assertIsNot(optimizer_b0, optimizer_b1)
        self.assertEqual(optimizer_b1.state, {})

        b2 = list(iter_run_steps(ARM_B))[1000]
        optimizer_b2 = machine.prepare(b2)
        self.assertIs(optimizer_b1, optimizer_b2)
        self.assertEqual(machine.optimizer_instance_count, 2)
        self.assertTrue(machine.b0_optimizer_destroyed)

    def test_cosine_anchor_has_frozen_endpoints(self) -> None:
        values = [cosine_anchor_weight(step) for step in range(1, 201)]
        self.assertEqual(values[0], 1.0)
        self.assertEqual(values[-1], 0.0)
        self.assertTrue(all(a >= b for a, b in zip(values[:-1], values[1:], strict=True)))

    def test_low_fidelity_loss_is_equal_average_of_normalized_fields(self) -> None:
        prediction = torch.tensor([[0.72, 0.45, 0.5]], dtype=torch.float64)
        target = torch.zeros_like(prediction)
        loss, components = normalized_low_fidelity_loss(
            prediction,
            target,
            potential_scale=0.72,
            temperature_scale=0.45,
            phase_scale=0.5,
        )
        self.assertEqual(float(loss), 1.0)
        self.assertEqual(components, {"potential": 1.0, "temperature": 1.0, "phase": 1.0})

    def test_low_fidelity_stream_has_eight_fixed_strata_and_is_deterministic(self) -> None:
        physics, _, _ = load_case_physics("FULL")
        time = np.array([0.0, 1.25, 2.5], dtype=np.float64)
        x = np.array([-1.0, 1.0], dtype=np.float64)
        z = np.array([0.0, 1.0], dtype=np.float64)
        base = np.arange(12, dtype=np.float64).reshape(3, 2, 2)
        fields = {"potential": base, "temperature": base + 20.0, "phase": base + 40.0}
        first = LF0LowFidelityBatchStream.from_structured_arrays(
            physics=physics, time=time, x=x, z=z, fields=fields, points_per_stratum=4
        )
        second = LF0LowFidelityBatchStream.from_structured_arrays(
            physics=physics, time=time, x=x, z=z, fields=fields, points_per_stratum=4
        )
        batch_a = first.draw(1)
        batch_b = second.draw(1)
        self.assertTrue(torch.equal(batch_a.coordinates, batch_b.coordinates))
        self.assertTrue(torch.equal(batch_a.targets, batch_b.targets))
        self.assertEqual(batch_a.coordinates.shape, (32, 3))
        self.assertEqual(batch_a.targets.shape, (32, 3))
        self.assertEqual(batch_a.strata, (
            "W1_ROI", "W1_OUTSIDE", "W2_ROI", "W2_OUTSIDE",
            "W3_ROI", "W3_OUTSIDE", "W4_ROI", "W4_OUTSIDE",
        ))
        for index, name in enumerate(batch_a.strata):
            block = batch_a.coordinates[index * 4 : (index + 1) * 4]
            in_roi = (block[:, 0].abs() <= 0.55) & (block[:, 1] <= 0.55)
            self.assertTrue(bool(torch.all(in_roi)) if name.endswith("ROI") else bool(torch.all(~in_roi)))
        self.assertTrue(torch.isfinite(batch_a.targets).all())

    def test_low_fidelity_interpolation_is_exact_at_source_nodes(self) -> None:
        physics, _, _ = load_case_physics("FULL")
        time = np.array([0.0, 1.25, 2.5], dtype=np.float64)
        x = np.array([-1.0, 1.0], dtype=np.float64)
        z = np.array([0.0, 1.0], dtype=np.float64)
        base = np.arange(12, dtype=np.float64).reshape(3, 2, 2)
        stream = LF0LowFidelityBatchStream.from_structured_arrays(
            physics=physics,
            time=time,
            x=x,
            z=z,
            fields={"potential": base, "temperature": base + 20.0, "phase": base + 40.0},
            points_per_stratum=2,
        )
        coordinates = torch.tensor([[-1.0, 0.0, 0.0], [1.0, 1.0, 2.5]], dtype=torch.float64)
        labels = stream.labels_at(coordinates)
        self.assertTrue(
            torch.equal(
                labels,
                torch.tensor([[0.0, 20.0, 40.0], [11.0, 31.0, 51.0]], dtype=torch.float64),
            )
        )

    def test_seeded_physics_streams_have_equal_first_1200_batch_identity(self) -> None:
        physics, _, _ = load_case_physics("FULL")
        config = type("TinyConfig", (), {"hidden_width": 8, "hidden_layers": 2})()
        model = build_exact_top_model(physics=physics, config=config)
        first = LF0PhysicsBatchStream(
            physics=physics, interior_points=4, boundary_points=4, initial_points=4
        )
        second = LF0PhysicsBatchStream(
            physics=physics, interior_points=4, boundary_points=4, initial_points=4
        )
        refresh_steps = []
        for step in range(1, 1201):
            a = first.draw(model, step, dtype=torch.float64, device=torch.device("cpu"))
            b = second.draw(model, step, dtype=torch.float64, device=torch.device("cpu"))
            self.assertEqual(a.batch_sha256, b.batch_sha256)
            self.assertEqual(a.interior_sha256, b.interior_sha256)
            self.assertEqual(a.boundary_sha256, b.boundary_sha256)
            self.assertEqual(a.initial_sha256, b.initial_sha256)
            self.assertTrue(
                all(
                    len(value) == 64
                    for value in (
                        a.interior_sha256,
                        a.boundary_sha256,
                        a.initial_sha256,
                        a.batch_sha256,
                    )
                )
            )
            if a.refreshed:
                refresh_steps.append(step)
        self.assertEqual(first.rolling_sha256, second.rolling_sha256)
        self.assertEqual(refresh_steps, [1, 151, 251, 351, 501, 551, 751, 1001])

    def test_exact_top_model_supports_finite_physics_and_lf_backward(self) -> None:
        physics, _, _ = load_case_physics("FULL")
        config = build_training_config(ARM_A, "cpu")
        tiny = type(
            "TinyConfig",
            (),
            {
                "hidden_width": 8,
                "hidden_layers": 2,
                "pde_weight": config.pde_weight,
                "boundary_weight": config.boundary_weight,
                "initial_weight": config.initial_weight,
            },
        )()
        model = build_exact_top_model(physics=physics, config=tiny).to(dtype=torch.float64)
        physics_stream = LF0PhysicsBatchStream(
            physics=physics, interior_points=4, boundary_points=4, initial_points=4
        )
        physics_batch = physics_stream.draw(
            model, 1, dtype=torch.float64, device=torch.device("cpu")
        )
        physics_loss, _ = _physics_objective(model, physics_batch, tiny)
        self.assertTrue(bool(torch.isfinite(physics_loss)))
        physics_loss.backward()

        time = np.array([0.0, 1.25, 2.5], dtype=np.float64)
        x = np.array([-1.0, 1.0], dtype=np.float64)
        z = np.array([0.0, 1.0], dtype=np.float64)
        zeros = np.zeros((3, 2, 2), dtype=np.float64)
        lf_stream = LF0LowFidelityBatchStream.from_structured_arrays(
            physics=physics,
            time=time,
            x=x,
            z=z,
            fields={"potential": zeros, "temperature": zeros, "phase": zeros},
            points_per_stratum=1,
        )
        model.zero_grad(set_to_none=True)
        lf_loss, _ = _low_fidelity_objective(
            model, lf_stream.draw(1), physics=physics, device=torch.device("cpu")
        )
        self.assertTrue(bool(torch.isfinite(lf_loss)))
        lf_loss.backward()

    def test_potential_maximum_principle_is_a_separate_pointwise_guard(self) -> None:
        waveform = np.array([0.0, 0.72, 0.72], dtype=np.float64)
        passing = potential_maximum_principle_guard(
            np.array([[0.0, 0.0], [0.1, 0.72], [0.2, 0.71]], dtype=np.float64),
            waveform,
        )
        failing = potential_maximum_principle_guard(
            np.array([[0.0], [0.720002], [-0.000002]], dtype=np.float64),
            waveform,
        )
        self.assertTrue(passing["passed"])
        self.assertEqual(passing["violation_fraction"], 0.0)
        self.assertFalse(failing["passed"])
        self.assertGreater(failing["maximum_absolute_excess"], 1.0e-6)

    def test_potential_guard_uses_waveform_order_independent_bounds(self) -> None:
        valid = potential_maximum_principle_guard(
            np.array([[-0.2, -0.72]], dtype=np.float64),
            np.array([-0.72], dtype=np.float64),
        )
        invalid = potential_maximum_principle_guard(
            np.array([[0.1]], dtype=np.float64),
            np.array([-0.72], dtype=np.float64),
        )
        self.assertTrue(valid["passed"])
        self.assertFalse(invalid["passed"])

    def test_potential_guard_reports_global_and_each_physical_window(self) -> None:
        time = np.array([0.1, 0.4, 1.3, 1.7], dtype=np.float64)
        waveform = np.full(4, 0.72, dtype=np.float64)
        potential = np.array([[0.1], [0.2], [0.720002], [0.4]], dtype=np.float64)
        result = potential_maximum_principle_windowed_guard(
            potential, time, waveform
        )
        self.assertFalse(result["passed"])
        self.assertEqual(set(result["by_window"]), {"W1", "W2", "W3", "W4"})
        self.assertTrue(result["by_window"]["W1"]["passed"])
        self.assertFalse(result["by_window"]["W3"]["passed"])
        self.assertFalse(result["global"]["passed"])

    def test_lf0_checkpoint_remains_prediction_loader_compatible(self) -> None:
        physics, program_sha, object_sha = load_case_physics("FULL")
        config = build_training_config(ARM_A, "cpu")
        model = build_exact_top_model(physics=physics, config=config).to(dtype=torch.float64)
        optimizer = torch.optim.Adam(model.parameters(), lr=config.learning_rate)
        with tempfile.TemporaryDirectory() as directory:
            checkpoint = Path(directory) / "checkpoint.pt"
            _write_checkpoint(
                path=checkpoint,
                model=model,
                optimizer=optimizer,
                config=config,
                global_step=1200,
                physics_program_sha256=program_sha,
                physics_object_sha256=object_sha,
                arm=ARM_A,
                stage="A_PURE_PHYSICS",
                source_identity="LF0-BUNDLE-TEST",
                contracts=contract_identity(),
            )
            loaded, loaded_config, payload = _load_model(
                checkpoint, device=torch.device("cpu")
            )
        self.assertEqual(loaded_config, config)
        self.assertEqual(
            loaded.architecture_manifest()["potential_output_transform"],
            POTENTIAL_TRANSFORM_EXACT_TOP_RAW,
        )
        self.assertEqual(payload["lf0"]["run_arm"], ARM_A)


if __name__ == "__main__":
    unittest.main()
