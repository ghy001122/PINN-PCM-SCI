"""PHK-V2.3 R1a ConFIG competence-recovery execution and adjudication."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import time
from typing import Any, Mapping, Sequence

import numpy as np
import torch

from .phk_v22r_pinn import PhkV22RArm, PhkV22RModel
from .phk_v22r_prediction import write_prediction_carrier
from .phk_v22r_training import PhkTrainingConfig, TrainingObservation, train


ROOT = Path(__file__).resolve().parents[1]
PROGRAM_CONTRACT_PATH = (
    ROOT / "configs" / "phk_v23" / "program_contract_r1a_config.json"
)
METHOD_CONTRACT_PATH = (
    ROOT / "configs" / "phk_v23" / "method_contract_r1a_config.json"
)
DEPLOYED_SOURCE_MANIFEST_PATH = (
    ROOT / "cloud" / "phk_v23_r1a_config_autodl" / "deployed-source-manifest.json"
)
GROUP_NAMES = (
    "G1_ELECTRIC_PDE",
    "G2_THERMAL_PDE",
    "G3_PHASE_PDE",
    "G4_BOUNDARY_INITIAL",
)
MECHANISM_STEPS = frozenset(
    {1, 10, 25, 50, 75, 100, 150, 250, 350, 550, 750, 1000}
)


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected one JSON object: {path}")
    return value


def _sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def _write_json_exclusive(path: Path, payload: Mapping[str, Any]) -> None:
    exact = Path(path)
    exact.parent.mkdir(parents=True, exist_ok=True)
    with exact.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")


def _finite(value: torch.Tensor | float) -> float:
    result = float(value.detach().cpu()) if isinstance(value, torch.Tensor) else float(value)
    if not math.isfinite(result):
        raise FloatingPointError("R1A_NUMERICAL_INVALID_STOP: non-finite scalar")
    return result


def load_r1a_contracts() -> dict[str, dict[str, Any]]:
    program = _read_json(PROGRAM_CONTRACT_PATH)
    method = _read_json(METHOD_CONTRACT_PATH)
    if program.get("schema_id") != "phk-v23-program-contract-r1a-config":
        raise ValueError("unsupported R1a program contract")
    if method.get("schema_id") != "phk-v23-method-contract-r1a-config":
        raise ValueError("unsupported R1a method contract")
    authorization = program["authorization"]
    for name in (
        "contract_implementation_and_state_writes_authorized",
        "one_r1a_reference_blind_v100_run_authorized",
        "reference_free_prediction_authorized",
        "local_nominal_evaluation_after_shutdown_authorized",
        "instance_shutdown_after_recovery_required",
        "selective_commit_and_push_authorized",
    ):
        if authorization.get(name) is not True:
            raise PermissionError(f"R1a authorization missing: {name}")
    for name in (
        "second_r1a_run_or_seed_change_authorized",
        "r1b_authorized",
        "pjgr_or_other_method_authorized",
        "stress_prediction_or_unseal_authorized",
        "submission_or_external_contact_authorized",
    ):
        if authorization.get(name) is not False:
            raise PermissionError(f"R1a out-of-scope authorization detected: {name}")
    identity = method["execution_identity"]
    if identity["optimizer_updates"] != 1000:
        raise ValueError("R1a update count drift")
    if identity["seed"] != 17 or identity["arm"] != "STRONG_RAW":
        raise ValueError("R1a arm or seed drift")
    if tuple(method["config_gradient_groups"]) != GROUP_NAMES:
        raise ValueError("R1a ConFIG group identity drift")
    return {"program": program, "method": method}


def _contract_identity() -> dict[str, dict[str, str]]:
    return {
        name: {
            "path": str(path.relative_to(ROOT)).replace("\\", "/"),
            "sha256": _sha256_path(path),
        }
        for name, path in (
            ("program", PROGRAM_CONTRACT_PATH),
            ("method", METHOD_CONTRACT_PATH),
        )
    }


def _strong_raw_config(device: str) -> PhkTrainingConfig:
    return PhkTrainingConfig(
        arm=PhkV22RArm.STRONG_RAW.value,
        case_control="FULL",
        updates=1000,
        seed=17,
        hidden_width=64,
        hidden_layers=4,
        frequency_band="BAND_A",
        learning_rate=1.0e-3,
        gradient_clip_norm=10.0,
        interior_points=512,
        boundary_points=128,
        initial_points=128,
        candidate_pool_multiplier=4,
        refresh_updates=250,
        log_every=25,
        checkpoint_every=1000,
        pde_weight=1.0,
        boundary_weight=5.0,
        initial_weight=1.0,
        dtype="float64",
        device=device,
    )


def _assert_method_identity(
    config: PhkTrainingConfig, contracts: Mapping[str, Mapping[str, Any]]
) -> None:
    expected = contracts["method"]["legacy_identity"]
    observed = {
        "arm": config.arm,
        "case_control": config.case_control,
        "initialization": "SCRATCH_START",
        "seed": config.seed,
        "dtype": "FLOAT64",
        "hidden_width": config.hidden_width,
        "hidden_layers": config.hidden_layers,
        "frequency_band": config.frequency_band,
        "learning_rate": config.learning_rate,
        "gradient_clip_norm": config.gradient_clip_norm,
        "interior_points": config.interior_points,
        "boundary_points": config.boundary_points,
        "initial_points": config.initial_points,
        "candidate_pool_multiplier": config.candidate_pool_multiplier,
        "refresh_updates": config.refresh_updates,
        "checkpoint_every": config.checkpoint_every,
        "loss_weights": {
            "pde": config.pde_weight,
            "boundary": config.boundary_weight,
            "initial": config.initial_weight,
        },
    }
    for name, value in observed.items():
        if expected.get(name) != value:
            raise ValueError(f"R1a strong-raw identity drift: {name}")
    for path_name, hash_name in (
        ("v22r_program_contract", "v22r_program_contract_sha256"),
        ("v22r_method_contract", "v22r_method_contract_sha256"),
    ):
        if _sha256_path(ROOT / expected[path_name]) != expected[hash_name]:
            raise ValueError(f"R1a inherited contract drift: {path_name}")


def _assert_deployed_source_identity(source_identity: str) -> None:
    manifest = _read_json(DEPLOYED_SOURCE_MANIFEST_PATH)
    if manifest.get("schema_id") != "phk-v23-r1a-config-deployed-source-manifest-v1":
        raise ValueError("unsupported R1a deployed-source manifest")
    if manifest.get("source_identity") != source_identity:
        raise ValueError("R1a deployed-source identity mismatch")
    files = manifest.get("files")
    if not isinstance(files, dict) or not files:
        raise ValueError("R1a deployed-source manifest has no files")
    for relative, expected in files.items():
        exact = (ROOT / relative).resolve()
        try:
            exact.relative_to(ROOT.resolve())
        except ValueError as exc:
            raise PermissionError("R1a deployed-source path escaped project") from exc
        if not exact.is_file() or _sha256_path(exact) != expected:
            raise ValueError(f"R1a deployed-source drift: {relative}")


class ConFIGGradientCombiner:
    """Parameter-free adaptation of the official standard ConFIG update."""

    def __init__(self, *, relative_tolerance: float = 1.0e-12, absolute_tolerance: float = 1.0e-14) -> None:
        self.relative_tolerance = float(relative_tolerance)
        self.absolute_tolerance = float(absolute_tolerance)
        self.epsilon = 1.0e-18
        self.calls = 0

    def manifest(self) -> Mapping[str, Any]:
        return {
            "method": "STANDARD_CONFIG_EQUAL_DIRECTION_WEIGHTS",
            "role": "ATTRIBUTED_SHARED_SOLVER_BACKBONE_NOT_PAPER_INNOVATION",
            "source_paper": "Liu_Chu_Thuerey_ICLR_2025",
            "source_repository": "https://github.com/tum-pbs/ConFIG",
            "source_license": "MIT",
            "gradient_groups": list(GROUP_NAMES),
            "linear_solver": "MOORE_PENROSE_VIA_FOUR_BY_FOUR_GRAM_PINV",
            "projection_length": "SUM_GROUP_PROJECTIONS_ON_TARGET_UNIT",
            "trainable_parameters": 0,
        }

    @staticmethod
    def _flatten_gradients(
        gradients: Sequence[torch.Tensor | None],
        parameters: Sequence[torch.nn.Parameter],
    ) -> torch.Tensor:
        pieces = [
            torch.zeros_like(parameter).reshape(-1)
            if gradient is None
            else gradient.reshape(-1)
            for parameter, gradient in zip(parameters, gradients, strict=True)
        ]
        return torch.cat(pieces)

    @staticmethod
    def _write_flat_gradient(
        flat: torch.Tensor, parameters: Sequence[torch.nn.Parameter]
    ) -> None:
        offset = 0
        for parameter in parameters:
            count = parameter.numel()
            parameter.grad = flat[offset : offset + count].view_as(parameter).clone()
            offset += count
        if offset != flat.numel():
            raise RuntimeError("R1A_NUMERICAL_INVALID_STOP: gradient unflatten mismatch")

    def combine(
        self,
        *,
        model: PhkV22RModel,
        loss_groups: Mapping[str, torch.Tensor],
        legacy_total: torch.Tensor,
    ) -> Mapping[str, Any]:
        if tuple(loss_groups) != GROUP_NAMES:
            raise ValueError("R1a ConFIG loss-group order drift")
        grouped_total = torch.stack(tuple(loss_groups.values())).sum()
        if not torch.allclose(
            grouped_total,
            legacy_total,
            rtol=self.relative_tolerance,
            atol=self.absolute_tolerance,
        ):
            raise RuntimeError("R1A_LOSS_DECOMPOSITION_IDENTITY_BLOCKED")
        parameters = tuple(parameter for parameter in model.parameters() if parameter.requires_grad)
        if not parameters:
            raise RuntimeError("R1A_NUMERICAL_INVALID_STOP: no trainable parameters")
        flat_gradients: list[torch.Tensor] = []
        for index, loss in enumerate(loss_groups.values()):
            gradients = torch.autograd.grad(
                loss,
                parameters,
                retain_graph=index + 1 < len(loss_groups),
                allow_unused=True,
            )
            flat_gradients.append(self._flatten_gradients(gradients, parameters))
        stacked = torch.stack(flat_gradients)
        if not bool(torch.isfinite(stacked).all()):
            raise FloatingPointError("R1A_NUMERICAL_INVALID_STOP: non-finite group gradient")
        norms = torch.linalg.vector_norm(stacked, dim=1)
        units = torch.nan_to_num(stacked / norms[:, None], nan=0.0, posinf=0.0, neginf=0.0)
        equal_weights = torch.ones(
            (len(GROUP_NAMES),), dtype=stacked.dtype, device=stacked.device
        )
        gram_pseudoinverse = torch.linalg.pinv(units @ units.T)
        target = units.T @ gram_pseudoinverse @ equal_weights
        target_norm = torch.linalg.vector_norm(target)
        if not bool(torch.isfinite(target_norm)) or _finite(target_norm) <= self.epsilon:
            raise FloatingPointError("R1A_NUMERICAL_INVALID_STOP: degenerate ConFIG direction")
        target_unit = target / target_norm
        projections = stacked @ target_unit
        projection_length = torch.sum(projections)
        combined = projection_length * target_unit
        if not bool(torch.isfinite(combined).all()):
            raise FloatingPointError("R1A_NUMERICAL_INVALID_STOP: non-finite combined gradient")
        combined_norm = torch.linalg.vector_norm(combined)
        if _finite(combined_norm) <= self.epsilon:
            raise FloatingPointError("R1A_NUMERICAL_INVALID_STOP: zero combined gradient")
        self._write_flat_gradient(combined, parameters)
        dots = stacked @ combined
        cosines: list[float | None] = []
        for norm, dot in zip(norms, dots, strict=True):
            if _finite(norm) <= self.epsilon:
                cosines.append(None)
            else:
                cosines.append(_finite(dot / (norm * combined_norm)))
        self.calls += 1
        return {
            "schema_id": "phk-v23-r1a-config-gradient-combination-v1",
            "loss_decomposition_identity_passed": True,
            "loss_group_values": {
                name: _finite(value) for name, value in loss_groups.items()
            },
            "loss_group_gradient_norms": {
                name: _finite(value) for name, value in zip(GROUP_NAMES, norms, strict=True)
            },
            "combined_gradient_norm": _finite(combined_norm),
            "combined_dot_by_group": {
                name: _finite(value) for name, value in zip(GROUP_NAMES, dots, strict=True)
            },
            "combined_cosine_by_group": {
                name: value for name, value in zip(GROUP_NAMES, cosines, strict=True)
            },
            "zero_norm_groups": [
                name
                for name, value in zip(GROUP_NAMES, norms, strict=True)
                if _finite(value) <= self.epsilon
            ],
        }


class R1AMechanismObserver:
    """Persist the frozen reference-blind mechanism schedule after each Adam step."""

    requested_phases = frozenset({"POST_STEP"})

    def __init__(self, *, run_directory: Path, soft_stop_seconds: float) -> None:
        self.run_directory = Path(run_directory)
        self.telemetry_path = self.run_directory / "r1a-config-mechanism.jsonl"
        self.soft_stop_seconds = float(soft_stop_seconds)
        self.started = time.perf_counter()
        self.handle = None
        self.record_count = 0

    def observe(self, observation: TrainingObservation) -> None:
        if time.perf_counter() - self.started > self.soft_stop_seconds:
            raise TimeoutError("R1a paid-work soft stop reached")
        if observation.optimizer_step not in MECHANISM_STEPS:
            return
        diagnostics = observation.gradient_combination_diagnostics
        if diagnostics is None:
            raise RuntimeError("R1a mechanism diagnostics are missing")
        if observation.interior is None:
            raise RuntimeError("R1a canonical interior batch is missing")
        before_mode = observation.model.training
        with torch.no_grad():
            fields = observation.model(observation.interior).detach()
        if observation.model.training != before_mode:
            raise RuntimeError("R1a observer changed model mode")
        gradient_norm = float(observation.scalars["gradient_norm_before_clip"])
        clip_coefficient = min(1.0, 10.0 / max(gradient_norm, 1.0e-18))
        record = {
            "schema_id": "phk-v23-r1a-config-mechanism-step-v1",
            "optimizer_step": observation.optimizer_step,
            "active_windows": observation.active_windows,
            "collocation_refreshed": observation.collocation_refreshed,
            "training_scalars": dict(observation.scalars),
            "loss_group_values": diagnostics["loss_group_values"],
            "loss_group_gradient_norms": diagnostics["loss_group_gradient_norms"],
            "combined_gradient_norm": diagnostics["combined_gradient_norm"],
            "combined_dot_by_group": diagnostics["combined_dot_by_group"],
            "combined_cosine_by_group": diagnostics["combined_cosine_by_group"],
            "zero_norm_groups": diagnostics["zero_norm_groups"],
            "global_preclip_gradient_norm": gradient_norm,
            "clip_coefficient": clip_coefficient,
            "potential_max": _finite(torch.max(fields[:, 0])),
            "temperature_max": _finite(torch.max(fields[:, 1])),
            "phase_max": _finite(torch.max(fields[:, 2])),
            "phase_activity_fraction": _finite(
                torch.mean((fields[:, 2] >= 0.5).to(torch.float64))
            ),
            "elapsed_seconds": time.perf_counter() - self.started,
        }
        if self.handle is None:
            self.handle = self.telemetry_path.open("x", encoding="utf-8", newline="\n")
        self.handle.write(json.dumps(record, sort_keys=True, allow_nan=False) + "\n")
        self.handle.flush()
        self.record_count += 1

    def finalize(self) -> dict[str, Any]:
        if self.handle is not None:
            self.handle.close()
            self.handle = None
        if self.record_count != len(MECHANISM_STEPS):
            raise RuntimeError(f"R1a mechanism record count mismatch: {self.record_count}")
        return {
            "schema_id": "phk-v23-r1a-config-mechanism-summary-v1",
            "record_count": self.record_count,
            "steps": sorted(MECHANISM_STEPS),
            "telemetry_path": self.telemetry_path.name,
            "telemetry_sha256": _sha256_path(self.telemetry_path),
            "reference_fields_read": False,
            "stress_fields_or_metrics_read": False,
        }


def run_reference_blind_gpu_recovery(
    *,
    output_root: Path,
    device_name: str,
    source_identity: str,
    hourly_price_cny: float,
) -> dict[str, Any]:
    contracts = load_r1a_contracts()
    _assert_deployed_source_identity(source_identity)
    output = Path(output_root).resolve()
    if output.exists():
        raise FileExistsError(f"R1a output already exists: {output}")
    if device_name != "cuda:0" or not torch.cuda.is_available():
        raise PermissionError("R1a requires authorized CUDA device cuda:0")
    device = torch.device(device_name)
    gpu_name = torch.cuda.get_device_name(device)
    if gpu_name != "Tesla V100-PCIE-32GB":
        raise PermissionError(f"R1a GPU identity mismatch: {gpu_name}")
    price = float(hourly_price_cny)
    if not math.isfinite(price) or price <= 0.0:
        raise ValueError("R1a hourly price must be positive and finite")
    budget = contracts["program"]["execution_budget"]
    projected_hours = float(budget["predeclared_projected_gpu_hours"])
    if projected_hours > float(budget["gpu_wall_hours_hard_cap"]):
        raise TimeoutError("R1a projected GPU time exceeds hard cap")
    if projected_hours * price > float(budget["estimated_incremental_cost_cny_hard_cap"]):
        raise TimeoutError("R1a projected cost exceeds hard cap")
    config = _strong_raw_config(device_name)
    _assert_method_identity(config, contracts)
    arm_directory = output / "strong_raw"
    combiner = ConFIGGradientCombiner()
    observer = R1AMechanismObserver(
        run_directory=arm_directory,
        soft_stop_seconds=3600.0 * float(budget["gpu_wall_hours_hard_cap"]),
    )
    started = time.perf_counter()
    started_at = datetime.now(timezone.utc).isoformat()
    outcome = train(
        config,
        run_directory=arm_directory,
        observer=observer,
        gradient_combiner=combiner,
        execution_metadata={
            "task_id": "PHK_V23_R1A_CONFIG_COMPETENCE_RECOVERY",
            "source_identity": source_identity,
            "contracts": _contract_identity(),
            "reference_blind": True,
            "stress_fields_read": False,
            "recovery_axis": "STANDARD_CONFIG_CONFLICT_FREE_GRADIENT_COMBINATION_ONLY",
        },
    )
    mechanism = observer.finalize()
    if combiner.calls != 1000:
        raise RuntimeError(f"R1a ConFIG application count mismatch: {combiner.calls}")
    prediction_path = arm_directory / "prediction.npz"
    write_prediction_carrier(
        checkpoint_path=outcome.checkpoint_path,
        output_path=prediction_path,
        device_name=device_name,
    )
    torch.cuda.synchronize(device)
    wall_seconds = time.perf_counter() - started
    estimated_cost = wall_seconds / 3600.0 * price
    if wall_seconds > 3600.0 * float(budget["gpu_wall_hours_hard_cap"]):
        raise TimeoutError("R1a GPU wall-time hard cap exceeded")
    if estimated_cost > float(budget["estimated_incremental_cost_cny_hard_cap"]):
        raise TimeoutError("R1a estimated cost hard cap exceeded")
    environment = {
        "schema_id": "phk-v23-r1a-config-environment-v1",
        "gpu_name": gpu_name,
        "torch_version": torch.__version__,
        "torch_cuda_version": torch.version.cuda,
        "numpy_version": np.__version__,
        "python": os.sys.version,
        "omp_num_threads": os.environ.get("OMP_NUM_THREADS"),
        "reference_fields_present": False,
        "stress_fields_present": False,
    }
    _write_json_exclusive(output / "environment.json", environment)
    files = {
        "checkpoint": outcome.checkpoint_path,
        "training_log": arm_directory / "training-log.jsonl",
        "manifest_start": arm_directory / "manifest-start.json",
        "manifest_final": arm_directory / "manifest-final.json",
        "mechanism_telemetry": arm_directory / "r1a-config-mechanism.jsonl",
        "prediction": prediction_path,
        "environment": output / "environment.json",
    }
    summary = {
        "schema_id": "phk-v23-r1a-config-reference-blind-run-summary-v1",
        "task_id": "PHK_V23_R1A_CONFIG_COMPETENCE_RECOVERY",
        "status": "R1A_REFERENCE_BLIND_GPU_RUN_COMPLETE",
        "started_at_utc": started_at,
        "finished_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_identity": source_identity,
        "contracts": _contract_identity(),
        "device": gpu_name,
        "dtype": "FLOAT64",
        "seed": 17,
        "arm": "STRONG_RAW",
        "optimizer_updates": 1000,
        "config_application_count": combiner.calls,
        "wall_seconds_including_prediction": wall_seconds,
        "hourly_price_cny": price,
        "estimated_incremental_cost_cny": estimated_cost,
        "reference_fields_read": False,
        "stress_fields_or_metrics_read": False,
        "mechanism_record_count": mechanism["record_count"],
        "artifacts": {
            name: {
                "path": str(path.relative_to(output)).replace("\\", "/"),
                "sha256": _sha256_path(path),
                "size_bytes": path.stat().st_size,
            }
            for name, path in files.items()
        },
    }
    _write_json_exclusive(output / "summary.json", summary)
    return summary


def adjudicate_local_nominal(
    *, run_summary_path: Path, evaluation_path: Path, output_path: Path
) -> dict[str, Any]:
    summary = _read_json(run_summary_path)
    evaluation = _read_json(evaluation_path)
    if summary.get("status") != "R1A_REFERENCE_BLIND_GPU_RUN_COMPLETE":
        raise ValueError("R1a run summary is not complete")
    if evaluation.get("status") != "EVALUATED_LOCAL_REFERENCE_ONLY":
        raise ValueError("R1a evaluation is not local-reference evidence")
    if evaluation.get("case_control") != "FULL":
        raise ValueError("R1a evaluation is not the nominal FULL case")
    passed = evaluation["hard_guards"]["passed"] is True
    outcome = (
        "R1A_CONFIG_RAW_COMPETENCE_RECOVERED"
        if passed
        else "R1A_CONFIG_RAW_NO_COMPETENCE"
    )
    result = {
        "schema_id": "phk-v23-r1a-config-local-adjudication-v1",
        "status": outcome,
        "competence_recovered": passed,
        "hard_guard_failures": list(evaluation["hard_guards"]["failures"]),
        "metrics": evaluation["metrics"],
        "event_topology": evaluation["hard_guards"]["event_topology"],
        "run_summary_sha256": _sha256_path(run_summary_path),
        "evaluation_sha256": _sha256_path(evaluation_path),
        "claim_boundary": (
            "SOLVER_LEVEL_COMPETENCE_ONLY_NO_METHOD_SUPERIORITY"
            if passed
            else "BOUNDED_SINGLE_SEED_NO_COMPETENCE_NO_METHOD_EVIDENCE"
        ),
        "config_identity": "ATTRIBUTED_SHARED_SOLVER_BACKBONE_NOT_PAPER_INNOVATION",
        "stress_unseal_authorized": False,
        "next_research_execution_authorized": False,
        "written_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    _write_json_exclusive(output_path, result)
    return result


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("--output-root", type=Path, required=True)
    run.add_argument("--device", required=True)
    run.add_argument("--source-identity", required=True)
    run.add_argument("--hourly-price-cny", type=float, required=True)
    decide = sub.add_parser("adjudicate")
    decide.add_argument("--run-summary", type=Path, required=True)
    decide.add_argument("--evaluation", type=Path, required=True)
    decide.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "run":
        result = run_reference_blind_gpu_recovery(
            output_root=args.output_root,
            device_name=args.device,
            source_identity=args.source_identity,
            hourly_price_cny=args.hourly_price_cny,
        )
    else:
        result = adjudicate_local_nominal(
            run_summary_path=args.run_summary,
            evaluation_path=args.evaluation,
            output_path=args.output,
        )
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
