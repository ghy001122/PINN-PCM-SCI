"""PHK-V2.3 R0C effective-update materiality replay and adjudication."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import random
import time
from typing import Any, Mapping, Sequence

import numpy as np
import torch

from .phk_v22r_pinn import PhkCollocationSampler, PhkV22RArm, PhkV22RModel
from .phk_v22r_training import PhkTrainingConfig, TrainingObservation, train
from .phk_v23_diagnostics import (
    gradient_matrix_preserving_state,
    summarize_model_mapping,
    write_json_exclusive_atomic,
)


ROOT = Path(__file__).resolve().parents[1]
PROGRAM_CONTRACT_PATH = ROOT / "configs" / "phk_v23" / "program_contract_r0c_effective_update_25.json"
METHOD_CONTRACT_PATH = ROOT / "configs" / "phk_v23" / "method_contract_r0c_effective_update_25.json"
DIAGNOSTIC_CONTRACT_PATH = ROOT / "configs" / "phk_v23" / "r0c_diagnostic_contract_effective_update_25.json"
DEPLOYED_SOURCE_MANIFEST_PATH = ROOT / "cloud" / "phk_v23_r0c_autodl" / "deployed-source-manifest.json"
HEADS = ("potential", "temperature", "phase")


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


def _tensor_sha256(tensor: torch.Tensor) -> str:
    raw = tensor.detach().to(device="cpu").contiguous().numpy().tobytes(order="C")
    return hashlib.sha256(raw).hexdigest().upper()


def _finite(value: Any) -> float:
    result = float(value.detach().cpu()) if isinstance(value, torch.Tensor) else float(value)
    if not math.isfinite(result):
        raise FloatingPointError("R0C produced a non-finite scalar")
    return result


def load_r0c_contracts() -> dict[str, dict[str, Any]]:
    program = _read_json(PROGRAM_CONTRACT_PATH)
    method = _read_json(METHOD_CONTRACT_PATH)
    diagnostic = _read_json(DIAGNOSTIC_CONTRACT_PATH)
    if program.get("schema_id") != "phk-v23-program-contract-r0c-effective-update-25":
        raise ValueError("unsupported R0C program contract")
    if method.get("schema_id") != "phk-v23-method-contract-r0c-effective-update-25":
        raise ValueError("unsupported R0C method contract")
    if diagnostic.get("schema_id") != "phk-v23-r0c-diagnostic-contract-effective-update-25":
        raise ValueError("unsupported R0C diagnostic contract")
    authorization = program["authorization"]
    for name in (
        "contract_and_implementation_writes_authorized",
        "r0c_reference_blind_gpu_replay_authorized",
        "local_reference_blind_adjudication_authorized",
        "instance_shutdown_after_recovery_required",
    ):
        if authorization.get(name) is not True:
            raise PermissionError(f"R0C authorization missing: {name}")
    for name in (
        "r1_or_recovery_intervention_authorized",
        "pjgr_or_other_method_authorized",
        "nominal_reference_access_authorized",
        "stress_reference_access_authorized",
        "second_gpu_run_or_seed_change_authorized",
        "submission_or_external_contact_authorized",
    ):
        if authorization.get(name) is not False:
            raise PermissionError(f"R0C out-of-scope authorization detected: {name}")
    identity = method["execution_identity"]
    if identity["scientific_schedule_denominator"] != 1000:
        raise ValueError("R0C schedule denominator drift")
    if identity["canonical_optimizer_steps"] != 25:
        raise ValueError("R0C canonical step drift")
    reference = diagnostic["reference_boundary"]
    if any(bool(value) for value in reference.values()):
        raise PermissionError("R0C reference boundary is not fail-closed")
    return {"program": program, "method": method, "diagnostic": diagnostic}


def _contract_identity() -> dict[str, dict[str, str]]:
    return {
        name: {
            "path": str(path.relative_to(ROOT)).replace("\\", "/"),
            "sha256": _sha256_path(path),
        }
        for name, path in (
            ("program", PROGRAM_CONTRACT_PATH),
            ("method", METHOD_CONTRACT_PATH),
            ("diagnostic", DIAGNOSTIC_CONTRACT_PATH),
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


def _assert_method_identity(config: PhkTrainingConfig, contracts: Mapping[str, Mapping[str, Any]]) -> None:
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
            raise ValueError(f"R0C strong-raw identity drift: {name}")
    for path_name, hash_name in (
        ("v22r_program_contract", "v22r_program_contract_sha256"),
        ("v22r_method_contract", "v22r_method_contract_sha256"),
    ):
        if _sha256_path(ROOT / expected[path_name]) != expected[hash_name]:
            raise ValueError(f"R0C inherited contract drift: {path_name}")


def _assert_deployed_source_identity(source_identity: str) -> None:
    if not DEPLOYED_SOURCE_MANIFEST_PATH.is_file():
        raise ValueError("R0C deployed source manifest is missing")
    manifest = _read_json(DEPLOYED_SOURCE_MANIFEST_PATH)
    if manifest.get("schema_id") != "phk-v23-r0c-deployed-source-manifest-v1":
        raise ValueError("unsupported R0C deployed source manifest")
    if manifest.get("source_identity") != source_identity:
        raise ValueError("R0C deployed source identity mismatch")
    files = manifest.get("files")
    if not isinstance(files, dict) or not files:
        raise ValueError("R0C deployed source manifest has no files")
    for relative, expected in files.items():
        exact = (ROOT / relative).resolve()
        try:
            exact.relative_to(ROOT.resolve())
        except ValueError as exc:
            raise PermissionError("R0C deployed source path escaped project") from exc
        if not exact.is_file() or _sha256_path(exact) != expected:
            raise ValueError(f"R0C deployed source drift: {relative}")


def _numpy_rng_equal(first: tuple[Any, ...], second: tuple[Any, ...]) -> bool:
    return first[0] == second[0] and np.array_equal(first[1], second[1]) and first[2:] == second[2:]


def _grad_snapshot(model: PhkV22RModel) -> list[torch.Tensor | None]:
    return [None if p.grad is None else p.grad.detach().clone() for p in model.parameters()]


def _assert_grads_equal(model: PhkV22RModel, before: Sequence[torch.Tensor | None]) -> None:
    for parameter, expected in zip(model.parameters(), before, strict=True):
        if expected is None:
            if parameter.grad is not None:
                raise RuntimeError("R0C observer created a persistent gradient")
        elif parameter.grad is None or not torch.equal(parameter.grad, expected):
            raise RuntimeError("R0C observer changed an existing gradient")


class R0CObserver:
    """Measure canonical gradients and Adam-effective head updates read-only."""

    include_optimizer_state_summary = True

    def __init__(self, *, run_directory: Path, contracts: Mapping[str, Mapping[str, Any]], source_identity: str, soft_stop_seconds: float) -> None:
        self.run_directory = Path(run_directory)
        self.contracts = contracts
        self.source_identity = source_identity
        self.soft_stop_seconds = float(soft_stop_seconds)
        self.requested_phases = frozenset(contracts["method"]["observer"]["requested_phases"])
        self.started = time.perf_counter()
        self.telemetry_path = self.run_directory / "r0c-effective-update-telemetry.jsonl"
        self.handle = None
        self.record_count = 0
        self.groups: dict[str, tuple[tuple[str, torch.nn.Parameter], ...]] = {}
        self.pre_parameters: dict[str, tuple[torch.Tensor, ...]] = {}
        self.preclip: dict[str, float] = {}
        self.postclip: dict[str, float] = {}
        self.pool: torch.Tensor | None = None
        self.w1: torch.Tensor | None = None
        self.gradient_w1: torch.Tensor | None = None
        self.boundary_w1: dict[str, torch.Tensor] | None = None
        self.initial: torch.Tensor | None = None
        self.pool_identity: dict[str, Any] = {}
        self.raw_states: dict[int, dict[str, torch.Tensor]] = {}
        self.identity_passed = True

    def _append(self, record: Mapping[str, Any]) -> None:
        if self.handle is None:
            self.handle = self.telemetry_path.open("x", encoding="utf-8", newline="\n")
        self.handle.write(json.dumps(record, sort_keys=True, allow_nan=False) + "\n")
        self.handle.flush()
        self.record_count += 1

    def _assert_groups(self, model: PhkV22RModel) -> None:
        named = tuple(model.named_parameters())
        assigned: set[int] = set()
        for head in HEADS:
            prefix = f"heads.{head}."
            group = tuple((name, parameter) for name, parameter in named if name.startswith(prefix))
            if not group:
                raise RuntimeError(f"R0C parameter group is empty: {head}")
            if any(id(parameter) in assigned for _, parameter in group):
                raise RuntimeError("R0C parameter group overlap")
            assigned.update(id(parameter) for _, parameter in group)
            self.groups[head] = group
        unassigned = [name for name, parameter in named if parameter.requires_grad and id(parameter) not in assigned]
        if unassigned:
            raise RuntimeError(f"R0C unassigned trainable parameters: {unassigned}")

    def _build_pool(self, model: PhkV22RModel) -> None:
        contract = self.contracts["method"]["diagnostic_pool"]
        device = next(model.parameters()).device
        dtype = next(model.parameters()).dtype
        sampler = PhkCollocationSampler(physics=model.physics, seed=int(contract["seed"]))
        pool = sampler.interior_uniform(
            int(contract["scalar_points_total"]), active_windows=2, dtype=dtype, device=device
        ).detach()
        per_window = int(contract["scalar_points_per_window"])
        self.pool = pool
        self.w1 = pool[:per_window]
        self.gradient_w1 = self.w1[: int(contract["gradient_points_w1"])]
        boundary = sampler.boundary(
            2 * int(contract["boundary_points_per_side_w1"]),
            active_windows=2,
            dtype=dtype,
            device=device,
        )
        self.boundary_w1 = {
            side: coordinates[coordinates[:, 2] < 0.35].detach()
            for side, coordinates in boundary.items()
        }
        self.initial = sampler.initial(int(contract["initial_points"]), dtype=dtype, device=device).detach()
        self.pool_identity = {
            "seed": int(contract["seed"]),
            "pool_sha256": _tensor_sha256(pool),
            "w1_sha256": _tensor_sha256(self.w1),
            "gradient_w1_sha256": _tensor_sha256(self.gradient_w1),
            "initial_sha256": _tensor_sha256(self.initial),
        }
        for observed, key in (
            (self.pool_identity["pool_sha256"], "expected_pool_sha256"),
            (self.pool_identity["w1_sha256"], "expected_w1_sha256"),
            (self.pool_identity["gradient_w1_sha256"], "expected_gradient_w1_sha256"),
            (self.pool_identity["initial_sha256"], "expected_initial_sha256"),
        ):
            if observed != contract[key]:
                raise RuntimeError(f"R0C fixed diagnostic pool drift: {key}")

    def _group_gradient_norms(self) -> dict[str, float]:
        result: dict[str, float] = {}
        for head, group in self.groups.items():
            squared = torch.zeros((), dtype=group[0][1].dtype, device=group[0][1].device)
            for _, parameter in group:
                if parameter.grad is not None:
                    squared = squared + torch.sum(parameter.grad.detach().square())
            result[head] = _finite(torch.sqrt(squared))
        return result

    def _snapshot_parameters(self) -> None:
        self.pre_parameters = {
            head: tuple(parameter.detach().clone() for _, parameter in group)
            for head, group in self.groups.items()
        }

    def _updates(self) -> dict[str, dict[str, float]]:
        result: dict[str, dict[str, float]] = {}
        for head, group in self.groups.items():
            before = self.pre_parameters[head]
            delta_squared = torch.zeros((), dtype=before[0].dtype, device=before[0].device)
            base_squared = torch.zeros_like(delta_squared)
            for old, (_, current) in zip(before, group, strict=True):
                delta_squared = delta_squared + torch.sum((current.detach() - old).square())
                base_squared = base_squared + torch.sum(old.square())
            absolute = torch.sqrt(delta_squared)
            relative = absolute / torch.clamp(torch.sqrt(base_squared), min=1.0e-18)
            result[head] = {"absolute_l2": _finite(absolute), "relative_l2": _finite(relative)}
        return result

    def _adam_summary(self, observation: TrainingObservation) -> dict[str, dict[str, Any]]:
        source = observation.optimizer_state_summary
        if source is None:
            raise RuntimeError("R0C optimizer scalar summary is missing")
        result: dict[str, dict[str, Any]] = {}
        for head, group in self.groups.items():
            states = [source[name] for name, _ in group]
            steps = sorted({int(item["step"]) for item in states})
            if not set(steps).issubset({0, observation.optimizer_step}) or observation.optimizer_step not in steps:
                raise RuntimeError(f"R0C Adam state step mismatch for {head}: {steps}")
            result[head] = {
                "step_min": steps[0],
                "step_max": steps[-1],
                "initialized_parameter_tensor_count": sum(
                    int(item["step"]) == observation.optimizer_step for item in states
                ),
                "exp_avg_l2": math.sqrt(sum(float(item["exp_avg_l2"]) ** 2 for item in states)),
                "exp_avg_sq_l2": math.sqrt(sum(float(item["exp_avg_sq_l2"]) ** 2 for item in states)),
                "parameter_tensor_count": len(states),
            }
        return result

    @staticmethod
    def _q95(summary: Mapping[str, Any]) -> float:
        return float(summary["quantiles"]["q95"])

    def _fixed_metrics(self, model: PhkV22RModel, step: int) -> dict[str, Any]:
        assert self.pool is not None and self.w1 is not None and self.boundary_w1 is not None
        fields, phase, electro, _ = summarize_model_mapping(
            model, self.pool, self.boundary_w1, self.contracts
        )
        w1_field = fields["per_window"][0]
        w1_phase = phase["per_window"][0]
        output = model.read_only_output_diagnostics(self.w1)
        jacobian = output.analytic_output_jacobians["phase"].detach()
        raw = {
            "phase": output.output.fields[:, 2:3].detach().to(device="cpu"),
            "latent": output.latents["phase"].detach().to(device="cpu"),
            "jacobian": jacobian.to(device="cpu"),
        }
        if step in {0, 1, 10}:
            self.raw_states[step] = {name: value.clone() for name, value in raw.items()}
        metrics: dict[str, Any] = {
            "temperature_max_w1": float(w1_field["fields"]["temperature"]["max"]),
            "phase_max_w1": float(w1_field["fields"]["phase"]["max"]),
            "phase_jacobian_q95_w1": self._q95(w1_field["analytic_output_jacobians"]["phase"]),
            "phase_jacobian_below_floor_fraction_w1": _finite(
                torch.mean((jacobian < 0.01).to(torch.float64))
            ),
            "positive_growth_roi_fraction_w1": float(w1_phase["positive_growth_roi_fraction"]),
        }
        if step == 10 and {0, 1, 10}.issubset(self.raw_states):
            epsilon = 1.0e-18

            def capacity(first: int, second: int) -> float:
                start = self.raw_states[first]
                end = self.raw_states[second]
                rate = torch.abs(end["latent"] - start["latent"]) / float(second - first)
                numerator = torch.quantile(torch.abs(start["jacobian"]) * rate, 0.95)
                denominator = max(0.5 - _finite(torch.quantile(start["phase"], 0.95)), epsilon)
                return _finite(numerator) / denominator

            metrics["phase_output_capacity_0_1"] = capacity(0, 1)
            metrics["phase_output_capacity_1_10"] = capacity(1, 10)
        return metrics

    def _fixed_gradient_ratio(self, model: PhkV22RModel) -> float:
        assert self.gradient_w1 is not None and self.boundary_w1 is not None and self.initial is not None
        result = gradient_matrix_preserving_state(
            model,
            self.gradient_w1,
            self.boundary_w1,
            self.contracts,
            initial=self.initial,
            loss_rows=("TOTAL_OBJECTIVE",),
        )
        norms = result["gradient_norms"]["TOTAL_OBJECTIVE"]
        return float(norms["phase"]) / max(float(norms["potential"]), float(norms["temperature"]), 1.0e-18)

    def _identity_check(self, step: int, scalars: Mapping[str, float], metrics: Mapping[str, Any], fixed_ratio: float | None) -> dict[str, Any] | None:
        contract = self.contracts["diagnostic"]["trajectory_identity"]
        anchor = contract["anchors"].get(str(step))
        if anchor is None:
            return None
        rtol = float(contract["relative_tolerance"])
        atol = float(contract["absolute_tolerance"])
        observed = {**dict(scalars), **dict(metrics)}
        if fixed_ratio is not None:
            observed["fixed_pool_gradient_ratio"] = fixed_ratio
        differences: dict[str, Any] = {}
        passed = True
        for name, expected in anchor.items():
            if name not in observed:
                passed = False
                differences[name] = {"status": "MISSING"}
                continue
            actual = float(observed[name])
            ok = math.isclose(actual, float(expected), rel_tol=rtol, abs_tol=atol)
            differences[name] = {"expected": float(expected), "observed": actual, "passed": ok}
            passed = passed and ok
        self.identity_passed = self.identity_passed and passed
        return {"passed": passed, "fields": differences}

    def _record_post_step(self, observation: TrainingObservation) -> None:
        step = observation.optimizer_step
        updates = self._updates()
        epsilon = float(self.contracts["diagnostic"]["decision"]["epsilon"])
        raw_ratio = self.preclip["phase"] / max(
            self.preclip["potential"], self.preclip["temperature"], epsilon
        )
        update_ratio = updates["phase"]["relative_l2"] / max(
            updates["potential"]["relative_l2"], updates["temperature"]["relative_l2"], epsilon
        )
        metrics = self._fixed_metrics(observation.model, step)
        fixed_ratio = self._fixed_gradient_ratio(observation.model) if step in {1, 10, 25} else None
        identity = self._identity_check(step, observation.scalars, metrics, fixed_ratio)
        self._append(
            {
                "schema_id": "phk-v23-r0c-effective-update-step-v1",
                "optimizer_step": step,
                "active_windows": observation.active_windows,
                "collocation_refreshed": observation.collocation_refreshed,
                "training_scalars": dict(observation.scalars),
                "preclip_gradient_norms": self.preclip,
                "postclip_gradient_norms": self.postclip,
                "head_updates": updates,
                "raw_gradient_ratio": raw_ratio,
                "effective_update_ratio": update_ratio,
                "adam_compensation_factor": update_ratio / max(raw_ratio, epsilon),
                "adam_state": self._adam_summary(observation),
                "fixed_pool_metrics": metrics,
                "identity_fixed_pool_gradient_ratio": fixed_ratio,
                "trajectory_identity": identity,
            }
        )

    def _observe_impl(self, observation: TrainingObservation) -> None:
        if time.perf_counter() - self.started > self.soft_stop_seconds:
            raise TimeoutError("R0C paid-work soft stop reached inside observer")
        if observation.phase == "PRE_RUN":
            self._assert_groups(observation.model)
            self._build_pool(observation.model)
            self._fixed_metrics(observation.model, 0)
            return
        if observation.phase == "PRE_BACKWARD":
            self._snapshot_parameters()
            return
        if observation.phase == "POST_BACKWARD_PRE_CLIP":
            self.preclip = self._group_gradient_norms()
            return
        if observation.phase == "POST_CLIP_PRE_STEP":
            self.postclip = self._group_gradient_norms()
            return
        if observation.phase == "POST_STEP":
            self._record_post_step(observation)

    def observe(self, observation: TrainingObservation) -> None:
        model = observation.model
        before_versions = tuple(parameter._version for parameter in model.parameters())
        before_grads = _grad_snapshot(model)
        before_mode = model.training
        before_python = random.getstate()
        before_numpy = np.random.get_state()
        before_cpu_rng = torch.random.get_rng_state().clone()
        device = next(model.parameters()).device
        before_cuda_rng = torch.cuda.get_rng_state(device).clone() if device.type == "cuda" else None
        self._observe_impl(observation)
        if tuple(parameter._version for parameter in model.parameters()) != before_versions:
            raise RuntimeError("R0C observer changed model parameters")
        _assert_grads_equal(model, before_grads)
        if model.training != before_mode:
            raise RuntimeError("R0C observer changed model mode")
        if random.getstate() != before_python or not _numpy_rng_equal(np.random.get_state(), before_numpy):
            raise RuntimeError("R0C observer changed Python or NumPy RNG")
        if not torch.equal(torch.random.get_rng_state(), before_cpu_rng):
            raise RuntimeError("R0C observer changed Torch CPU RNG")
        if before_cuda_rng is not None and not torch.equal(torch.cuda.get_rng_state(device), before_cuda_rng):
            raise RuntimeError("R0C observer changed Torch CUDA RNG")

    def finalize(self) -> dict[str, Any]:
        if self.handle is not None:
            self.handle.close()
            self.handle = None
        if self.record_count != 25:
            raise RuntimeError(f"R0C telemetry record count mismatch: {self.record_count}")
        if not self.identity_passed:
            raise RuntimeError("R0C trajectory identity failed")
        summary = {
            "schema_id": "phk-v23-r0c-telemetry-summary-v1",
            "status": "REFERENCE_BLIND_EFFECTIVE_UPDATE_TELEMETRY_COMPLETE",
            "record_count": self.record_count,
            "telemetry_path": self.telemetry_path.name,
            "telemetry_sha256": _sha256_path(self.telemetry_path),
            "pool_identity": self.pool_identity,
            "trajectory_identity_passed": True,
            "reference_fields_read": False,
            "stress_fields_or_metrics_read": False,
        }
        write_json_exclusive_atomic(self.run_directory / "r0c-telemetry-summary.json", summary)
        return summary


def run_reference_blind_gpu_replay(*, output_root: Path, device_name: str, source_identity: str, hourly_price_cny: float) -> dict[str, Any]:
    contracts = load_r0c_contracts()
    _assert_deployed_source_identity(source_identity)
    output = Path(output_root).resolve()
    if output.exists():
        raise FileExistsError(f"R0C output already exists: {output}")
    if device_name != "cuda:0" or not torch.cuda.is_available():
        raise PermissionError("R0C requires authorized CUDA device cuda:0")
    gpu_name = torch.cuda.get_device_name(torch.device(device_name))
    if gpu_name != "Tesla V100-PCIE-32GB":
        raise PermissionError(f"R0C GPU identity mismatch: {gpu_name}")
    price = float(hourly_price_cny)
    if not math.isfinite(price) or price <= 0.0:
        raise ValueError("R0C hourly price must be positive and finite")
    budget = contracts["program"]["execution_budget"]
    projected_hours = 0.15
    if projected_hours > float(budget["gpu_wall_hours_hard_cap"]):
        raise TimeoutError("R0C projected GPU time exceeds hard cap")
    if projected_hours * price > float(budget["estimated_incremental_cost_cny_hard_cap"]):
        raise TimeoutError("R0C projected cost exceeds hard cap")
    config = _strong_raw_config(device_name)
    _assert_method_identity(config, contracts)
    arm_directory = output / "strong_raw"
    observer = R0CObserver(
        run_directory=arm_directory,
        contracts=contracts,
        source_identity=source_identity,
        soft_stop_seconds=60.0 * float(budget["gpu_paid_work_soft_stop_minutes"]),
    )
    started = time.perf_counter()
    started_at = datetime.now(timezone.utc).isoformat()
    outcome = train(
        config,
        run_directory=arm_directory,
        execution_limit=25,
        observer=observer,
        execution_metadata={
            "task_id": "PHK_V23_R0C_EFFECTIVE_UPDATE_25_V100",
            "source_identity": source_identity,
            "contracts": _contract_identity(),
            "reference_blind": True,
            "stress_fields_read": False,
            "cloud_shadow_optimizer_steps": 0,
        },
    )
    telemetry = observer.finalize()
    torch.cuda.synchronize(torch.device(device_name))
    wall_seconds = time.perf_counter() - started
    estimated_cost = wall_seconds / 3600.0 * price
    if wall_seconds > 3600.0 * float(budget["gpu_wall_hours_hard_cap"]):
        raise TimeoutError("R0C GPU wall-time hard cap exceeded")
    if estimated_cost > float(budget["estimated_incremental_cost_cny_hard_cap"]):
        raise TimeoutError("R0C estimated cost hard cap exceeded")
    environment = {
        "schema_id": "phk-v23-r0c-environment-v1",
        "gpu_name": gpu_name,
        "torch_version": torch.__version__,
        "torch_cuda_version": torch.version.cuda,
        "numpy_version": np.__version__,
        "python": os.sys.version,
        "omp_num_threads": os.environ.get("OMP_NUM_THREADS"),
        "reference_fields_present": False,
    }
    write_json_exclusive_atomic(output / "environment.json", environment)
    files = {
        "checkpoint": outcome.checkpoint_path,
        "training_log": arm_directory / "training-log.jsonl",
        "manifest_start": arm_directory / "manifest-start.json",
        "manifest_final": arm_directory / "manifest-final.json",
        "telemetry": arm_directory / "r0c-effective-update-telemetry.jsonl",
        "telemetry_summary": arm_directory / "r0c-telemetry-summary.json",
        "environment": output / "environment.json",
    }
    summary = {
        "schema_id": "phk-v23-r0c-reference-blind-run-summary-v1",
        "task_id": "PHK_V23_R0C_EFFECTIVE_UPDATE_25_V100",
        "status": "R0C_REFERENCE_BLIND_GPU_REPLAY_COMPLETE",
        "started_at_utc": started_at,
        "finished_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_identity": source_identity,
        "contracts": _contract_identity(),
        "device": gpu_name,
        "dtype": "FLOAT64",
        "seed": 17,
        "arm": "STRONG_RAW",
        "scientific_schedule_denominator": 1000,
        "canonical_optimizer_steps": 25,
        "cloud_shadow_optimizer_steps": 0,
        "wall_seconds": wall_seconds,
        "hourly_price_cny": price,
        "estimated_incremental_cost_cny": estimated_cost,
        "reference_fields_read": False,
        "stress_fields_or_metrics_read": False,
        "telemetry_record_count": telemetry["record_count"],
        "artifacts": {
            name: {
                "path": str(path.relative_to(output)).replace("\\", "/"),
                "sha256": _sha256_path(path),
                "size_bytes": path.stat().st_size,
            }
            for name, path in files.items()
        },
    }
    write_json_exclusive_atomic(output / "summary.json", summary)
    return summary


def read_telemetry(path: Path) -> list[dict[str, Any]]:
    records = [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]
    if [int(item["optimizer_step"]) for item in records] != list(range(1, 26)):
        raise ValueError("R0C telemetry must contain exactly steps 1 through 25")
    return records


def _first_block(records: Mapping[int, Mapping[str, Any]], predicate: Any, minimum: int) -> tuple[int, int] | None:
    for start in range(10, 26 - minimum + 1):
        end = start + minimum - 1
        if all(predicate(records[step]) for step in range(start, end + 1)):
            return start, end
    return None


def adjudicate_reference_blind(records: Sequence[Mapping[str, Any]], contracts: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    by_step = {int(item["optimizer_step"]): item for item in records}
    if set(by_step) != set(range(1, 26)):
        raise ValueError("R0C adjudication requires steps 1 through 25")
    decision = contracts["diagnostic"]["decision"]
    if not all(item.get("trajectory_identity") is None or item["trajectory_identity"].get("passed") is True for item in records):
        raise ValueError("R0C trajectory identity is invalid")
    step10 = by_step[10]["fixed_pool_metrics"]
    output_confound = (
        float(step10["phase_jacobian_below_floor_fraction_w1"]) >= float(decision["output_low_jacobian_fraction_min"])
        or (
            float(step10["phase_jacobian_q95_w1"]) <= float(decision["output_jacobian_q95_max"])
            and float(step10["phase_output_capacity_0_1"]) <= float(decision["output_capacity_max"])
            and float(step10["phase_output_capacity_1_10"]) <= float(decision["output_capacity_max"])
        )
    )

    def activity(record: Mapping[str, Any]) -> bool:
        updates = record["head_updates"]
        return max(float(updates["potential"]["relative_l2"]), float(updates["temperature"]["relative_l2"])) >= float(decision["other_head_update_activity_floor"])

    def electrothermal(record: Mapping[str, Any]) -> bool:
        metrics = record["fixed_pool_metrics"]
        return float(metrics["temperature_max_w1"]) <= float(decision["electrothermal_temperature_max"]) and float(metrics["positive_growth_roi_fraction_w1"]) <= float(decision["electrothermal_positive_growth_max"])

    minimum = int(decision["minimum_consecutive_steps"])
    supported = None if output_confound else _first_block(
        by_step,
        lambda record: float(record["raw_gradient_ratio"]) <= float(decision["raw_gradient_starvation_ratio_max"])
        and float(record["effective_update_ratio"]) <= float(decision["effective_update_starvation_ratio_max"])
        and activity(record)
        and not electrothermal(record),
        minimum,
    )
    compensated = None if output_confound else _first_block(
        by_step,
        lambda record: float(record["raw_gradient_ratio"]) <= float(decision["raw_gradient_starvation_ratio_max"])
        and float(record["effective_update_ratio"]) >= float(decision["adam_compensation_ratio_min"])
        and activity(record),
        minimum,
    )
    if supported is not None:
        outcome = "R0C_EFFECTIVE_UPDATE_STARVATION_SUPPORTED"
        block = supported
        recommendation = "R1A_GRADIENT_MATERIALITY_SINGLE_INTERVENTION_PLAN_ONLY_NOT_AUTHORIZED"
    elif compensated is not None:
        outcome = "R0C_ADAM_PRECONDITIONING_COMPENSATES_RAW_GRADIENT"
        block = compensated
        recommendation = "REJECT_GRADIENT_MAGNITUDE_RESCUE_AS_FIRST_R1A"
    else:
        outcome = "R0C_INCONCLUSIVE_STOP"
        block = None
        recommendation = "NO_R1_EXECUTION_AUTHORIZED"
    return {
        "schema_id": "phk-v23-r0c-reference-blind-adjudication-v1",
        "task_id": "PHK_V23_R0C_EFFECTIVE_UPDATE_25_V100",
        "status": outcome,
        "qualifying_block": ({"start": block[0], "end": block[1]} if block else None),
        "output_conditioning_confound": output_confound,
        "electrothermal_confound_steps": [step for step in range(10, 26) if electrothermal(by_step[step])],
        "next_recommendation": recommendation,
        "competence_recovered": False,
        "method_gain_proven": False,
        "causal_root_cause_identified": False,
        "reference_fields_read": False,
        "stress_fields_or_metrics_read": False,
        "next_stage_authorized": False,
    }


def write_reference_blind_adjudication(*, telemetry_path: Path, output_path: Path) -> dict[str, Any]:
    contracts = load_r0c_contracts()
    records = read_telemetry(telemetry_path)
    result = adjudicate_reference_blind(records, contracts)
    result["telemetry_path"] = str(Path(telemetry_path).resolve())
    result["telemetry_sha256"] = _sha256_path(telemetry_path)
    result["contracts"] = _contract_identity()
    result["written_at_utc"] = datetime.now(timezone.utc).isoformat()
    write_json_exclusive_atomic(output_path, result)
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
    decide.add_argument("--telemetry", type=Path, required=True)
    decide.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "run":
        result = run_reference_blind_gpu_replay(
            output_root=args.output_root,
            device_name=args.device,
            source_identity=args.source_identity,
            hourly_price_cny=args.hourly_price_cny,
        )
    else:
        result = write_reference_blind_adjudication(
            telemetry_path=args.telemetry, output_path=args.output
        )
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
