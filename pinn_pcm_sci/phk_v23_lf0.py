"""PHK-V2.3 LF0 exact-top and low-fidelity attribution campaign.

The module owns the LF0 training state machine.  It reuses the frozen V2.2R
model, residual, boundary, initial-condition, sampler, prediction, and local
evaluator seams; no physical equation is reimplemented here.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import random
import time
from typing import Any, Iterator, Mapping, Sequence

import numpy as np
from scipy.interpolate import RegularGridInterpolator
import torch

from .phk_v21_benchmark import (
    PhkV21OracleResult,
    load_phk_v21_physical,
    read_phk_v21_result,
)
from .phk_v22r_pinn import (
    FrequencyBand,
    POTENTIAL_TRANSFORM_EXACT_TOP_RAW,
    PhkCollocationSampler,
    PhkV22RModel,
    PhkV22RPhysics,
    initial_residuals,
    interior_residuals,
    normalized_residual_loss,
)
from .phk_v22r_prediction import read_prediction_carrier, write_prediction_carrier
from .phk_v22r_training import (
    INITIAL_SCALES,
    METHOD_CONTRACT_PATH as V22R_METHOD_CONTRACT_PATH,
    PDE_SCALES,
    PROGRAM_CONTRACT_PATH as V22R_PROGRAM_CONTRACT_PATH,
    ROOT,
    PhkTrainingConfig,
    _boundary_loss,
    _checkpoint_payload,
    load_case_physics,
)


PROGRAM_CONTRACT_PATH = (
    ROOT / "configs" / "phk_v23" / "program_contract_lf0_exact_top_warmstart.json"
)
METHOD_CONTRACT_PATH = (
    ROOT / "configs" / "phk_v23" / "method_contract_lf0_exact_top_warmstart.json"
)
DATA_CONTRACT_PATH = ROOT / "configs" / "phk_v23" / "data_contract_lf0_medium_only.json"
DECISION_CONTRACT_PATH = (
    ROOT / "configs" / "phk_v23" / "decision_contract_lf0_attribution.json"
)
DEPLOYED_SOURCE_MANIFEST_PATH = (
    ROOT / "cloud" / "phk_v23_lf0_autodl" / "deployed-source-manifest.json"
)
CONTRACT_PATHS = {
    "program": PROGRAM_CONTRACT_PATH,
    "method": METHOD_CONTRACT_PATH,
    "data": DATA_CONTRACT_PATH,
    "decision": DECISION_CONTRACT_PATH,
}
EXPECTED_CONTRACT_SCHEMAS = {
    "program": "phk-v23-lf0-program-contract-v1",
    "method": "phk-v23-lf0-method-contract-v1",
    "data": "phk-v23-lf0-data-contract-v1",
    "decision": "phk-v23-lf0-decision-contract-v1",
}
TASK_ID = "PHK_V23_LF0_EXACT_TOP_WARMSTART_ATTRIBUTION_EXECUTE"
ARM_A = "A_EXACT_TOP_SCRATCH"
ARM_B = "B_MEDIUM_WARMSTART"
ARM_C = "C_EXACT_TOP_COMPUTE_CONTROL_IF_TRIGGERED"
RUN_ARMS = (ARM_A, ARM_B, ARM_C)
WINDOWS = (
    (0.00, 0.35),
    (0.35, 1.25),
    (1.25, 1.60),
    (1.60, 2.50),
)
LF_STRATA = (
    "W1_ROI",
    "W1_OUTSIDE",
    "W2_ROI",
    "W2_OUTSIDE",
    "W3_ROI",
    "W3_OUTSIDE",
    "W4_ROI",
    "W4_OUTSIDE",
)
LF_SEEDS = tuple(range(17017, 17025))
C_TRIGGER_REQUIRED_EVIDENCE_BINDINGS = frozenset(
    {
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
    }
)
REQUIRED_DEPLOYED_RUNTIME_RELATIVE_PATHS = frozenset(
    {
        *(path.relative_to(ROOT).as_posix() for path in CONTRACT_PATHS.values()),
        "cloud/phk_v23_lf0_autodl/preflight.py",
        "configs/phk_v22r/program_contract.json",
        "configs/phk_v22r/method_contract.json",
        "configs/phk_v21/program_contract.json",
        "configs/phk_v21/object_numerical_contract.json",
        "configs/phk_v21/engineering_contract.json",
        "configs/phk_v21/e1_solver_selection.json",
        "configs/phk_v2/program_contract.json",
        "configs/phk_v2/object_numerical_contract.json",
        "outputs/runs/20260827T-phk-v21-e2-engineering-search-001/summary.json",
        "pinn_pcm_sci/__init__.py",
        "pinn_pcm_sci/artifacts.py",
        "pinn_pcm_sci/phk_contract.py",
        "pinn_pcm_sci/phk_benchmark.py",
        "pinn_pcm_sci/phk_v21_benchmark.py",
        "pinn_pcm_sci/phk_v21_solver.py",
        "pinn_pcm_sci/phk_v22r_pinn.py",
        "pinn_pcm_sci/phk_v22r_training.py",
        "pinn_pcm_sci/phk_v22r_prediction.py",
        "pinn_pcm_sci/phk_v23_lf0.py",
        "tests/test_phk_v21_benchmark.py",
    }
)


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
        json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False)
        handle.write("\n")


def _tensor_bytes(value: torch.Tensor) -> bytes:
    array = value.detach().to(device="cpu", dtype=torch.float64).contiguous().numpy()
    return array.tobytes(order="C")


def _batch_sha256(*values: torch.Tensor, metadata: str = "") -> str:
    digest = hashlib.sha256(metadata.encode("utf-8"))
    for value in values:
        digest.update(str(tuple(value.shape)).encode("ascii"))
        digest.update(_tensor_bytes(value))
    return digest.hexdigest().upper()


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected one JSON object: {path}")
    return value


def _is_upper_sha256(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and value == value.upper()
        and all(character in "0123456789ABCDEF" for character in value)
    )


def _safe_deployed_path(root: Path, relative: object) -> Path:
    if not isinstance(relative, str) or not relative:
        raise ValueError("LF0 deployed path is missing")
    portable = Path(relative.replace("/", os.sep))
    if portable.is_absolute() or ".." in portable.parts:
        raise PermissionError("LF0 deployed path escaped its root")
    exact = (root / portable).resolve()
    try:
        exact.relative_to(root)
    except ValueError as exc:
        raise PermissionError("LF0 deployed path escaped its root") from exc
    return exact


def load_contracts() -> dict[str, dict[str, Any]]:
    """Load the four frozen LF0 contracts through one validated interface."""

    contracts = {name: _read_json(path) for name, path in CONTRACT_PATHS.items()}
    for name, schema in EXPECTED_CONTRACT_SCHEMAS.items():
        if contracts[name].get("schema_id") != schema:
            raise ValueError(f"unsupported PHK-V2.3 LF0 {name} contract")
    relative = {
        name: path.relative_to(ROOT).as_posix() for name, path in CONTRACT_PATHS.items()
    }
    program = contracts["program"]
    method = contracts["method"]
    data = contracts["data"]
    decision = contracts["decision"]
    if program.get("phase_id") != TASK_ID:
        raise ValueError("LF0 task identity drift")
    if tuple(program.get("run_limits", {}).get("fixed_order", ())) != RUN_ARMS:
        raise ValueError("LF0 A/B/C run-order identity drift")
    if (
        method.get("program_contract") != relative["program"]
        or data.get("program_contract") != relative["program"]
        or decision.get("program_contract") != relative["program"]
        or decision.get("method_contract") != relative["method"]
        or decision.get("data_contract") != relative["data"]
    ):
        raise ValueError("LF0 cross-contract identity drift")
    authorization = program.get("authorization", {})
    if not all(
        authorization.get(name) is True
        for name in ("gpu_run_a", "gpu_run_b_after_valid_a", "conditional_gpu_run_c")
    ):
        raise PermissionError("LF0 GPU campaign is not fully authorized")
    if any(
        authorization.get(name) is not False
        for name in (
            "new_seed",
            "stress_prediction_or_unseal",
            "pjgr_or_r2",
            "benchmark_physics_reference_evaluator_change",
        )
    ):
        raise PermissionError("LF0 authorization boundary drift")
    identity = method.get("common_gpu_identity", {})
    if (
        identity.get("gpu") != "TESLA_V100_PCIE_32GB_ONLY"
        or identity.get("dtype") != "FLOAT64"
        or identity.get("seed") != 17
        or identity.get("arm") != "STRONG_RAW"
        or identity.get("potential_transform")
        != "POTENTIAL_TRANSFORM_EXACT_TOP_AFFINE_RAW_LIFT"
    ):
        raise ValueError("LF0 frozen model/GPU identity drift")
    source = data.get("training_source", {})
    if (
        source.get("resolution") != "medium"
        or source.get("only_gpu_training_label_source") is not True
    ):
        raise PermissionError("LF0 medium-only data identity drift")
    if decision.get("stress_status") != "TWO_STRESS_REFERENCES_SEALED_UNREAD":
        raise PermissionError("LF0 stress boundary drift")
    return contracts


def contract_identity() -> dict[str, dict[str, str]]:
    """Return compact path/hash bindings for run manifests and checkpoints."""

    return {
        name: {
            "path": path.relative_to(ROOT).as_posix(),
            "sha256": _sha256_path(path),
        }
        for name, path in CONTRACT_PATHS.items()
    }


def _validate_deployed_cpu_qualification(
    *,
    root: Path,
    manifest: Mapping[str, Any],
    files: Mapping[str, Any],
    source_identity: str,
) -> dict[str, Any]:
    binding = manifest.get("cpu_qualification")
    if not isinstance(binding, dict):
        raise ValueError("LF0 CPU qualification binding is missing")
    expected_sha = binding.get("sha256")
    expected_size = binding.get("size_bytes")
    if (
        not _is_upper_sha256(expected_sha)
        or not isinstance(expected_size, int)
        or isinstance(expected_size, bool)
        or expected_size <= 0
    ):
        raise ValueError("LF0 CPU qualification binding is malformed")
    exact = _safe_deployed_path(root, binding.get("path"))
    if (
        not exact.is_file()
        or exact.stat().st_size != expected_size
        or _sha256_path(exact) != expected_sha
    ):
        raise ValueError("LF0 CPU qualification artifact drift")
    record = _read_json(exact)
    if (
        record.get("schema_id") != "phk-v23-lf0-cpu-qualification-v1"
        or record.get("task_id") != TASK_ID
        or record.get("status") != "LF0_CPU_QUALIFIED"
        or record.get("passed") is not True
        or record.get("blockers") != []
    ):
        raise PermissionError("LF0 CPU qualification did not pass")
    if record.get("qualified_source_identity") != source_identity:
        raise ValueError("LF0 CPU qualification source identity mismatch")
    source_commit = manifest.get("source_commit")
    if (
        not isinstance(source_commit, str)
        or len(source_commit) != 40
        or any(character not in "0123456789abcdefABCDEF" for character in source_commit)
        or record.get("source_commit") != source_commit
    ):
        raise ValueError("LF0 CPU qualification source commit mismatch")

    contract_paths = {
        role: path.relative_to(ROOT).as_posix() for role, path in CONTRACT_PATHS.items()
    }
    contract_identities = record.get("contract_identities")
    if not isinstance(contract_identities, dict) or set(contract_identities) != set(
        contract_paths
    ):
        raise ValueError("LF0 CPU qualification contract identities are incomplete")
    for role, relative in contract_paths.items():
        if contract_identities.get(role) != {
            "path": relative,
            "sha256": files.get(relative),
        }:
            raise ValueError(f"LF0 CPU qualification {role} contract mismatch")

    data = _read_json(root / contract_paths["data"])
    decision = _read_json(root / contract_paths["decision"])
    expected_inputs: dict[str, Any] = {
        "low_fidelity_training_source": data.get("training_source"),
        "qualification_fine": data.get("qualification_only", {}).get("fine"),
        "qualification_extra_fine": data.get("qualification_only", {}).get("extra_fine"),
        **decision.get("qualification_inputs", {}),
    }
    input_identities = record.get("input_identities")
    if not isinstance(input_identities, dict) or set(input_identities) != set(expected_inputs):
        raise ValueError("LF0 CPU qualification input identities are incomplete")
    for label, expected in expected_inputs.items():
        actual = input_identities.get(label)
        if (
            not isinstance(expected, dict)
            or not isinstance(actual, dict)
            or actual.get("path") != expected.get("path")
            or actual.get("sha256") != str(expected.get("sha256", "")).upper()
        ):
            raise ValueError(f"LF0 CPU qualification {label} identity mismatch")
    training_input = manifest.get("training_input")
    medium = input_identities["low_fidelity_training_source"]
    if not isinstance(training_input, dict) or any(
        medium.get(name) != training_input.get(name)
        for name in ("path", "sha256", "size_bytes")
    ):
        raise ValueError("LF0 CPU qualification medium input mismatch")
    return {
        "path": str(binding["path"]),
        "sha256": str(expected_sha),
        "size_bytes": expected_size,
        "status": "LF0_CPU_QUALIFIED",
        "source_commit": source_commit,
    }


def _assert_deployed_source_identity(
    source_identity: str,
    *,
    root: Path = ROOT,
    manifest_path: Path = DEPLOYED_SOURCE_MANIFEST_PATH,
) -> dict[str, Any]:
    """Bind the runner to the exact preflighted deployment bundle."""

    deployment_root = Path(root).resolve()
    manifest = _read_json(Path(manifest_path))
    if manifest.get("schema_id") != "phk-v23-lf0-deployed-source-manifest-v1":
        raise ValueError("unsupported LF0 deployed-source manifest")
    if manifest.get("identity_definition") != (
        "SHA256_OF_SORTED_PATH_EQUALS_UPPERCASE_SHA256_LINES"
    ):
        raise ValueError("unsupported LF0 source identity definition")
    if manifest.get("source_identity") != source_identity:
        raise ValueError("LF0 deployed-source identity mismatch")
    files = manifest.get("files")
    if not isinstance(files, dict) or not files:
        raise ValueError("LF0 deployed-source manifest has no files")
    missing_runtime = sorted(REQUIRED_DEPLOYED_RUNTIME_RELATIVE_PATHS.difference(files))
    if missing_runtime:
        raise ValueError(f"LF0 deployed-source runtime closure is incomplete: {missing_runtime}")
    identity_lines: list[str] = []
    for relative, expected in sorted(files.items()):
        if not isinstance(relative, str) or not isinstance(expected, str):
            raise ValueError("invalid LF0 deployed-source file entry")
        exact = _safe_deployed_path(deployment_root, relative)
        actual = _sha256_path(exact) if exact.is_file() else None
        if actual != expected.upper():
            raise ValueError(f"LF0 deployed-source drift: {relative}")
        identity_lines.append(f"{relative}={actual}\n")
    aggregate = hashlib.sha256("".join(identity_lines).encode("utf-8")).hexdigest().upper()
    if source_identity != f"LF0-BUNDLE-{aggregate}":
        raise ValueError("LF0 aggregate source identity mismatch")
    return _validate_deployed_cpu_qualification(
        root=deployment_root,
        manifest=manifest,
        files=files,
        source_identity=source_identity,
    )


def physics_active_windows(physics_local_step: int) -> int:
    """Return the frozen causal-window count on the physics-local step axis."""

    step = int(physics_local_step)
    if step <= 0:
        raise ValueError("physics-local optimizer step must be positive")
    if step <= 150:
        return 1
    if step <= 350:
        return 2
    if step <= 550:
        return 3
    return 4


def cosine_anchor_weight(b1_local_step: int) -> float:
    """Cosine LF anchor on the 200 B1 steps, with exact 1 and 0 endpoints."""

    step = int(b1_local_step)
    if not 1 <= step <= 200:
        raise ValueError("B1 local step must lie in [1, 200]")
    if step == 1:
        return 1.0
    if step == 200:
        return 0.0
    return 0.5 * (1.0 + math.cos(math.pi * (step - 1) / 199.0))


@dataclass(frozen=True)
class LF0Step:
    global_step: int
    stage: str
    physics_local_step: int | None
    low_fidelity_step: int | None
    anchor_weight: float

    @property
    def uses_physics(self) -> bool:
        return self.physics_local_step is not None

    @property
    def uses_low_fidelity(self) -> bool:
        return self.low_fidelity_step is not None


def iter_run_steps(arm: str) -> Iterator[LF0Step]:
    """Yield the complete frozen optimizer-stage plan for one LF0 arm."""

    if arm == ARM_A:
        for step in range(1, 1201):
            yield LF0Step(step, "A_PURE_PHYSICS", step, None, 0.0)
        return
    if arm == ARM_B:
        for step in range(1, 801):
            yield LF0Step(step, "B0_LF_ONLY", None, step, 1.0)
        for b1_step in range(1, 201):
            global_step = 800 + b1_step
            yield LF0Step(
                global_step,
                "B1_PHYSICS_PLUS_LF_ANCHOR",
                b1_step,
                global_step,
                cosine_anchor_weight(b1_step),
            )
        for physics_step in range(201, 1201):
            yield LF0Step(800 + physics_step, "B2_PURE_PHYSICS", physics_step, None, 0.0)
        return
    if arm == ARM_C:
        for step in range(1, 2001):
            yield LF0Step(step, "C_PURE_PHYSICS", step, None, 0.0)
        return
    raise ValueError(f"unknown LF0 arm: {arm}")


def build_training_config(arm: str, device_name: str) -> PhkTrainingConfig:
    """Materialize the common frozen optimizer/model identity for one arm."""

    if arm not in RUN_ARMS:
        raise ValueError(f"unknown LF0 arm: {arm}")
    updates = 1200 if arm == ARM_A else 2000
    config = PhkTrainingConfig(
        arm="STRONG_RAW",
        case_control="FULL",
        updates=updates,
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
        checkpoint_every=updates,
        pde_weight=1.0,
        boundary_weight=5.0,
        initial_weight=1.0,
        dtype="float64",
        device=device_name,
    )
    config.validate()
    return config


class LF0OptimizerStateMachine:
    """Own optimizer lifetime so the B0 state cannot leak into B1/B2.

    B0 receives one LF-only Adam.  Crossing into B1 releases that optimizer and
    constructs a fresh physics Adam, which is then retained unchanged through
    B2.  A and C construct only the physics Adam.
    """

    def __init__(
        self,
        *,
        model: torch.nn.Module,
        arm: str,
        learning_rate: float,
    ) -> None:
        if arm not in RUN_ARMS:
            raise ValueError(f"unknown LF0 arm: {arm}")
        self.model = model
        self.arm = arm
        self.learning_rate = float(learning_rate)
        if not math.isfinite(self.learning_rate) or self.learning_rate <= 0.0:
            raise ValueError("LF0 learning rate must be positive and finite")
        self.optimizer: torch.optim.Adam | None = None
        self.role: str | None = None
        self.optimizer_instance_count = 0
        self.b0_optimizer_destroyed = False

    @staticmethod
    def _role(step: LF0Step) -> str:
        return "LF_DATA_ONLY" if step.stage == "B0_LF_ONLY" else "PHYSICS"

    def _construct(self, role: str) -> torch.optim.Adam:
        self.optimizer = torch.optim.Adam(
            self.model.parameters(),
            lr=self.learning_rate,
            betas=(0.9, 0.999),
            eps=1.0e-8,
            weight_decay=0.0,
            amsgrad=False,
        )
        self.role = role
        self.optimizer_instance_count += 1
        return self.optimizer

    def prepare(self, step: LF0Step) -> torch.optim.Adam:
        desired = self._role(step)
        if self.optimizer is None:
            return self._construct(desired)
        if self.role == desired:
            return self.optimizer
        if self.arm != ARM_B or self.role != "LF_DATA_ONLY" or desired != "PHYSICS":
            raise RuntimeError("invalid LF0 optimizer role transition")
        self.optimizer = None
        self.role = None
        self.b0_optimizer_destroyed = True
        return self._construct("PHYSICS")

    def manifest(self) -> dict[str, Any]:
        return {
            "optimizer_instance_count": self.optimizer_instance_count,
            "current_role": self.role,
            "b0_optimizer_destroyed_before_b1": self.b0_optimizer_destroyed,
            "b1_b2_optimizer_shared_without_reset": (
                self.arm != ARM_B
                or (self.optimizer_instance_count == 2 and self.role == "PHYSICS")
            ),
        }


@dataclass(frozen=True)
class LowFidelityBatch:
    coordinates: torch.Tensor
    targets: torch.Tensor
    strata: tuple[str, ...]
    batch_sha256: str


class LF0LowFidelityBatchStream:
    """Eight isolated Sobol strata over the frozen medium field carrier."""

    def __init__(
        self,
        *,
        physics: PhkV22RPhysics,
        time_axis: np.ndarray,
        x_axis: np.ndarray,
        z_axis: np.ndarray,
        fields: Mapping[str, np.ndarray],
        points_per_stratum: int = 128,
    ) -> None:
        self.physics = physics
        self.time_axis = self._axis(time_axis, "time")
        self.x_axis = self._axis(x_axis, "x")
        self.z_axis = self._axis(z_axis, "z")
        self.points_per_stratum = int(points_per_stratum)
        if self.points_per_stratum <= 0:
            raise ValueError("LF points per stratum must be positive")
        expected = (self.time_axis.size, self.z_axis.size, self.x_axis.size)
        self.interpolators: dict[str, RegularGridInterpolator] = {}
        for name in ("potential", "temperature", "phase"):
            values = np.asarray(fields[name], dtype=np.float64)
            if values.shape != expected or not np.isfinite(values).all():
                raise ValueError(f"LF structured field is invalid: {name}")
            self.interpolators[name] = RegularGridInterpolator(
                (self.time_axis, self.z_axis, self.x_axis),
                values,
                method="linear",
                bounds_error=False,
                fill_value=None,
            )
        self.engines = tuple(
            torch.quasirandom.SobolEngine(3, scramble=True, seed=seed)
            for seed in LF_SEEDS
        )
        self.draw_count = 0
        self._rolling = hashlib.sha256(b"PHK_V23_LF0_LOW_FIDELITY_BATCHES")

    @staticmethod
    def _axis(value: np.ndarray, name: str) -> np.ndarray:
        axis = np.asarray(value, dtype=np.float64).reshape(-1)
        if axis.size < 2 or not np.isfinite(axis).all() or np.any(np.diff(axis) <= 0.0):
            raise ValueError(f"LF {name} axis is invalid")
        return axis

    @classmethod
    def from_structured_arrays(
        cls,
        *,
        physics: PhkV22RPhysics,
        time: np.ndarray,
        x: np.ndarray,
        z: np.ndarray,
        fields: Mapping[str, np.ndarray],
        points_per_stratum: int = 128,
    ) -> "LF0LowFidelityBatchStream":
        return cls(
            physics=physics,
            time_axis=time,
            x_axis=x,
            z_axis=z,
            fields=fields,
            points_per_stratum=points_per_stratum,
        )

    @classmethod
    def from_result(
        cls,
        result: PhkV21OracleResult,
        *,
        physics: PhkV22RPhysics,
        points_per_stratum: int = 128,
    ) -> "LF0LowFidelityBatchStream":
        shape = (result.time.size, result.grid.nz, result.grid.nx)
        return cls.from_structured_arrays(
            physics=physics,
            time=result.time,
            x=result.grid.x_centers,
            z=result.grid.z_centers,
            fields={
                name: np.asarray(getattr(result, name), dtype=np.float64).reshape(shape)
                for name in ("potential", "temperature", "phase")
            },
            points_per_stratum=points_per_stratum,
        )

    def _roi_points(self, unit: torch.Tensor, window: tuple[float, float]) -> torch.Tensor:
        x = -0.55 + 1.10 * unit[:, 0:1]
        z = 0.55 * unit[:, 1:2]
        t = window[0] + (window[1] - window[0]) * unit[:, 2:3]
        return torch.cat((x, z, t), dim=1)

    def _outside_points(self, unit: torch.Tensor, window: tuple[float, float]) -> torch.Tensor:
        # Uniform map onto the disjoint outside union: left and right full-height
        # strips plus the upper central strip.  The first Sobol coordinate selects
        # a rectangle with probability proportional to its physical area and is
        # then reused as that rectangle's local x coordinate.
        x_min, x_max = self.physics.x_min, self.physics.x_max
        z_min, z_max = self.physics.z_min, self.physics.z_max
        areas = unit.new_tensor(
            [
                (-0.55 - x_min) * (z_max - z_min),
                (x_max - 0.55) * (z_max - z_min),
                1.10 * (z_max - 0.55),
            ]
        )
        if bool(torch.any(areas <= 0.0)):
            raise ValueError("frozen LF ROI is outside the physical domain")
        total = torch.sum(areas)
        selector = unit[:, 0:1] * total
        first_end = areas[0]
        second_end = areas[0] + areas[1]
        left = selector < first_end
        right = (selector >= first_end) & (selector < second_end)
        top = selector >= second_end
        x = torch.empty_like(selector)
        z = torch.empty_like(selector)
        x[left] = x_min + selector[left] / areas[0] * (-0.55 - x_min)
        z[left] = z_min + unit[:, 1:2][left] * (z_max - z_min)
        local_right = selector[right] - first_end
        x[right] = 0.55 + local_right / areas[1] * (x_max - 0.55)
        z[right] = z_min + unit[:, 1:2][right] * (z_max - z_min)
        local_top = selector[top] - second_end
        x[top] = -0.55 + local_top / areas[2] * 1.10
        z[top] = 0.55 + unit[:, 1:2][top] * (z_max - 0.55)
        t = window[0] + (window[1] - window[0]) * unit[:, 2:3]
        return torch.cat((x, z, t), dim=1)

    @property
    def rolling_sha256(self) -> str:
        return self._rolling.copy().hexdigest().upper()

    def labels_at(self, coordinates: torch.Tensor) -> torch.Tensor:
        """Interpolate the three medium fields at physical ``(x,z,t)`` points."""

        if coordinates.ndim != 2 or coordinates.shape[1] != 3:
            raise ValueError("LF coordinates must have physical x, z, and t columns")
        query = coordinates.detach().to(device="cpu", dtype=torch.float64).numpy()[:, (2, 1, 0)]
        labels = torch.as_tensor(
            np.column_stack(
                [self.interpolators[name](query) for name in ("potential", "temperature", "phase")]
            ),
            dtype=torch.float64,
        )
        if not bool(torch.isfinite(labels).all()):
            raise FloatingPointError("LF0 low-fidelity interpolation produced non-finite labels")
        return labels

    def draw(self, low_fidelity_step: int) -> LowFidelityBatch:
        step = int(low_fidelity_step)
        if step != self.draw_count + 1:
            raise ValueError("LF batch stream must be consumed once in strict step order")
        pieces: list[torch.Tensor] = []
        for index, (engine, name) in enumerate(zip(self.engines, LF_STRATA, strict=True)):
            unit = engine.draw(self.points_per_stratum, dtype=torch.float64)
            window = WINDOWS[index // 2]
            pieces.append(
                self._roi_points(unit, window)
                if name.endswith("_ROI")
                else self._outside_points(unit, window)
            )
        coordinates = torch.cat(pieces, dim=0)
        targets = self.labels_at(coordinates)
        digest = _batch_sha256(coordinates, targets, metadata=f"LF:{step}")
        self._rolling.update(bytes.fromhex(digest))
        self.draw_count = step
        return LowFidelityBatch(coordinates, targets, LF_STRATA, digest)


@dataclass(frozen=True)
class PhysicsBatch:
    interior: torch.Tensor
    boundary: Mapping[str, torch.Tensor]
    initial: torch.Tensor
    active_windows: int
    refreshed: bool
    interior_sha256: str
    boundary_sha256: str
    initial_sha256: str
    batch_sha256: str


class LF0PhysicsBatchStream:
    """Seed-17 Sobol stream keyed only by the physics-local optimizer step."""

    def __init__(
        self,
        *,
        physics: PhkV22RPhysics,
        interior_points: int = 512,
        boundary_points: int = 128,
        initial_points: int = 128,
        refresh_updates: int = 250,
        seed: int = 17,
    ) -> None:
        if boundary_points % 4:
            raise ValueError("LF0 boundary point count must be divisible by four")
        self.sampler = PhkCollocationSampler(physics=physics, seed=seed)
        self.interior_points = int(interior_points)
        self.boundary_points = int(boundary_points)
        self.initial_points = int(initial_points)
        self.refresh_updates = int(refresh_updates)
        self.local_step = 0
        self.cached: PhysicsBatch | None = None
        self._rolling = hashlib.sha256(b"PHK_V23_LF0_PHYSICS_BATCHES")

    @property
    def rolling_sha256(self) -> str:
        return self._rolling.copy().hexdigest().upper()

    def draw(
        self,
        model: PhkV22RModel,
        physics_local_step: int,
        *,
        dtype: torch.dtype,
        device: torch.device,
    ) -> PhysicsBatch:
        step = int(physics_local_step)
        if step != self.local_step + 1:
            raise ValueError("physics batch stream must be consumed once in strict local-step order")
        windows = physics_active_windows(step)
        refresh = (
            self.cached is None
            or (step - 1) % self.refresh_updates == 0
            or self.cached.active_windows != windows
        )
        if refresh:
            interior = self.sampler.select_interior(
                model,
                count=self.interior_points,
                active_windows=windows,
                physics_aware=False,
                dtype=dtype,
                device=device,
            ).detach()
            boundary = {
                name: value.detach()
                for name, value in self.sampler.boundary(
                    self.boundary_points // 4,
                    active_windows=windows,
                    dtype=dtype,
                    device=device,
                ).items()
            }
            initial = self.sampler.initial(
                self.initial_points, dtype=dtype, device=device
            ).detach()
            ordered = tuple(boundary[name] for name in ("left", "right", "bottom", "top"))
            interior_digest = _batch_sha256(
                interior, metadata=f"PHYSICS_INTERIOR_WINDOWS:{windows}"
            )
            boundary_digest = _batch_sha256(
                *ordered, metadata=f"PHYSICS_BOUNDARY_WINDOWS:{windows}"
            )
            initial_digest = _batch_sha256(
                initial, metadata=f"PHYSICS_INITIAL_WINDOWS:{windows}"
            )
            digest = _batch_sha256(
                interior,
                *ordered,
                initial,
                metadata=f"PHYSICS_WINDOWS:{windows}",
            )
            self.cached = PhysicsBatch(
                interior,
                boundary,
                initial,
                windows,
                True,
                interior_digest,
                boundary_digest,
                initial_digest,
                digest,
            )
        assert self.cached is not None
        batch = PhysicsBatch(
            self.cached.interior,
            self.cached.boundary,
            self.cached.initial,
            self.cached.active_windows,
            refresh,
            self.cached.interior_sha256,
            self.cached.boundary_sha256,
            self.cached.initial_sha256,
            self.cached.batch_sha256,
        )
        self._rolling.update(bytes.fromhex(batch.batch_sha256))
        self.local_step = step
        return batch


def normalized_low_fidelity_loss(
    prediction: torch.Tensor,
    target: torch.Tensor,
    *,
    potential_scale: float,
    temperature_scale: float,
    phase_scale: float = 0.5,
) -> tuple[torch.Tensor, dict[str, float]]:
    """Equal average of the three frozen normalized field MSE terms."""

    if prediction.shape != target.shape or prediction.ndim != 2 or prediction.shape[1] != 3:
        raise ValueError("LF prediction and target must have matching (N, 3) shapes")
    scales = prediction.new_tensor(
        [float(potential_scale), float(temperature_scale), float(phase_scale)]
    )
    if not bool(torch.isfinite(scales).all()) or bool(torch.any(scales <= 0.0)):
        raise ValueError("LF field scales must be positive and finite")
    components_tensor = torch.mean(((prediction - target) / scales).square(), dim=0)
    loss = torch.mean(components_tensor)
    components = {
        name: float(value.detach().cpu())
        for name, value in zip(
            ("potential", "temperature", "phase"), components_tensor, strict=True
        )
    }
    return loss, components


def potential_maximum_principle_guard(
    potential: np.ndarray,
    waveform: np.ndarray,
    *,
    absolute_tolerance: float = 1.0e-6,
) -> dict[str, Any]:
    """Apply the separate LF0 pointwise ``0 <= V <= waveform`` guard."""

    values = np.asarray(potential, dtype=np.float64)
    drive = np.asarray(waveform, dtype=np.float64).reshape(-1, 1)
    if values.ndim != 2 or values.shape[0] != drive.shape[0]:
        raise ValueError("potential and waveform axes do not align")
    tolerance = float(absolute_tolerance)
    if not math.isfinite(tolerance) or tolerance < 0.0:
        raise ValueError("potential guard tolerance must be finite and nonnegative")
    finite = bool(np.isfinite(values).all() and np.isfinite(drive).all())
    if finite:
        lower = np.minimum(0.0, drive)
        upper = np.maximum(0.0, drive)
        excess = np.maximum(lower - values, values - upper)
        maximum = float(np.max(np.maximum(excess, 0.0)))
        violations = excess > tolerance
        fraction = float(np.mean(violations))
    else:
        maximum = math.inf
        fraction = 1.0
    return {
        "passed": finite and maximum <= tolerance and fraction == 0.0,
        "all_pointwise_values_finite": finite,
        "absolute_tolerance": tolerance,
        "maximum_absolute_excess": maximum,
        "violation_fraction": fraction,
    }


def potential_maximum_principle_windowed_guard(
    potential: np.ndarray,
    time_axis: np.ndarray,
    waveform: np.ndarray,
    *,
    absolute_tolerance: float = 1.0e-6,
) -> dict[str, Any]:
    """Report the validity guard globally and on every frozen physical window."""

    values = np.asarray(potential, dtype=np.float64)
    times = np.asarray(time_axis, dtype=np.float64).reshape(-1)
    drive = np.asarray(waveform, dtype=np.float64).reshape(-1)
    if values.ndim != 2 or values.shape[0] != times.size or times.size != drive.size:
        raise ValueError("potential, time, and waveform axes do not align")
    by_window: dict[str, dict[str, Any]] = {}
    for index, (lower, upper) in enumerate(WINDOWS, start=1):
        # Keep shared endpoints in both adjacent diagnostic windows, matching
        # the contract's closed interval notation.
        mask = (times >= lower) & (times <= upper)
        if not bool(np.any(mask)):
            raise ValueError(f"prediction carrier has no saved time in W{index}")
        by_window[f"W{index}"] = potential_maximum_principle_guard(
            values[mask], drive[mask], absolute_tolerance=absolute_tolerance
        )
    global_guard = potential_maximum_principle_guard(
        values, drive, absolute_tolerance=absolute_tolerance
    )
    return {
        "passed": global_guard["passed"] and all(
            item["passed"] for item in by_window.values()
        ),
        "global": global_guard,
        "by_window": by_window,
    }


def build_exact_top_model(
    *,
    physics: PhkV22RPhysics,
    config: PhkTrainingConfig,
    frequency_band: FrequencyBand | None = None,
) -> PhkV22RModel:
    return PhkV22RModel(
        physics=physics,
        arm="STRONG_RAW",
        hidden_width=config.hidden_width,
        hidden_layers=config.hidden_layers,
        frequency_band=frequency_band or FrequencyBand.band_a(),
        potential_output_transform=POTENTIAL_TRANSFORM_EXACT_TOP_RAW,
    )


def _assert_config_identity(
    config: PhkTrainingConfig,
    arm: str,
    contracts: Mapping[str, Mapping[str, Any]],
) -> None:
    identity = contracts["method"]["common_gpu_identity"]
    expected = {
        "arm": identity["arm"],
        "case_control": identity["case_control"],
        "seed": identity["seed"],
        "hidden_width": identity["network"]["hidden_width"],
        "hidden_layers": identity["network"]["hidden_layers"],
        "learning_rate": identity["optimizer"]["learning_rate"],
        "gradient_clip_norm": identity["gradient_clip_norm"],
        "interior_points": identity["collocation_counts"]["interior"],
        "boundary_points": identity["collocation_counts"]["boundary"],
        "initial_points": identity["collocation_counts"]["initial"],
        "dtype": "float64",
    }
    for name, value in expected.items():
        if getattr(config, name) != value:
            raise ValueError(f"LF0 training identity drift: {name}")
    frozen_runs = contracts["method"]["runs"]
    expected_updates = {
        ARM_A: int(frozen_runs["A"]["physics_updates"]),
        ARM_B: int(frozen_runs["B"]["global_updates"]),
        ARM_C: int(frozen_runs["C"]["physics_updates"]),
    }[arm]
    if config.updates != expected_updates:
        raise ValueError("LF0 arm update count drift")
    schedule = contracts["method"]["physics_schedule"]
    if (
        schedule.get("axis") != "PHYSICS_LOCAL_OPTIMIZER_STEP"
        or schedule.get("1-150") != 1
        or schedule.get("151-350") != 2
        or schedule.get("351-550") != 3
        or schedule.get("551+") != 4
        or schedule.get("refresh_updates") != config.refresh_updates
    ):
        raise ValueError("LF0 physics-local schedule drift")


def _physical_object():
    return load_phk_v21_physical(
        program_path=ROOT / "configs" / "phk_v21" / "program_contract.json",
        object_path=ROOT / "configs" / "phk_v21" / "object_numerical_contract.json",
        legacy_program_path=ROOT / "configs" / "phk_v2" / "program_contract.json",
        legacy_object_path=ROOT / "configs" / "phk_v2" / "object_numerical_contract.json",
    )


def _load_medium_stream(
    *,
    medium_carrier: Path,
    physics: PhkV22RPhysics,
    contracts: Mapping[str, Mapping[str, Any]],
) -> LF0LowFidelityBatchStream:
    source = contracts["data"]["training_source"]
    relative = Path(str(source["path"]).replace("/", os.sep))
    expected = (ROOT / relative).resolve()
    supplied = Path(medium_carrier).resolve()
    if supplied != expected:
        raise PermissionError("only the exact frozen LF0 medium carrier is allowed")
    if _sha256_path(supplied) != str(source["sha256"]).upper():
        raise ValueError("LF0 medium carrier byte identity drift")
    result = read_phk_v21_result(supplied, physical=_physical_object())
    return LF0LowFidelityBatchStream.from_result(result, physics=physics)


def _physics_objective(
    model: PhkV22RModel,
    batch: PhysicsBatch,
    config: PhkTrainingConfig,
) -> tuple[torch.Tensor, dict[str, float]]:
    """Evaluate the inherited V2.2R summed strong-form objective."""

    interior = interior_residuals(model, batch.interior)
    pde_loss = normalized_residual_loss(interior, scales=PDE_SCALES)
    boundary_loss, boundary_diagnostics = _boundary_loss(model, batch.boundary)
    initial_loss = normalized_residual_loss(
        initial_residuals(model, batch.initial), scales=INITIAL_SCALES
    )
    total = (
        config.pde_weight * pde_loss
        + config.boundary_weight * boundary_loss
        + config.initial_weight * initial_loss
    )
    scalars = {
        "physics_total": float(total.detach().cpu()),
        "pde_loss": float(pde_loss.detach().cpu()),
        "boundary_loss": float(boundary_loss.detach().cpu()),
        "initial_loss": float(initial_loss.detach().cpu()),
        **{f"boundary:{name}": value for name, value in boundary_diagnostics.items()},
    }
    return total, scalars


def _low_fidelity_objective(
    model: PhkV22RModel,
    batch: LowFidelityBatch,
    *,
    physics: PhkV22RPhysics,
    device: torch.device,
) -> tuple[torch.Tensor, dict[str, float]]:
    coordinates = batch.coordinates.to(device=device, dtype=torch.float64)
    target = batch.targets.to(device=device, dtype=torch.float64)
    prediction = model(coordinates)
    return normalized_low_fidelity_loss(
        prediction,
        target,
        potential_scale=physics.waveform_amplitude,
        temperature_scale=physics.theta_transition,
        phase_scale=0.5,
    )


def _write_checkpoint(
    *,
    path: Path,
    model: PhkV22RModel,
    optimizer: torch.optim.Optimizer,
    config: PhkTrainingConfig,
    global_step: int,
    physics_program_sha256: str,
    physics_object_sha256: str,
    arm: str,
    stage: str,
    source_identity: str,
    contracts: Mapping[str, Mapping[str, str]],
) -> Path:
    payload = _checkpoint_payload(
        model=model,
        optimizer=optimizer,
        config=config,
        update=global_step,
        program_contract_sha256=_sha256_path(V22R_PROGRAM_CONTRACT_PATH),
        method_contract_sha256=_sha256_path(V22R_METHOD_CONTRACT_PATH),
        physical_program_sha256=physics_program_sha256,
        physical_object_sha256=physics_object_sha256,
    )
    payload["lf0"] = {
        "schema_id": "phk-v23-lf0-checkpoint-metadata-v1",
        "task_id": TASK_ID,
        "run_arm": arm,
        "stage": stage,
        "global_optimizer_step": int(global_step),
        "source_identity": source_identity,
        "contracts": dict(contracts),
        "potential_transform": POTENTIAL_TRANSFORM_EXACT_TOP_RAW,
        "medium_training_labels_used": arm == ARM_B,
        "medium_training_source_role": (
            "DECLARED_MEDIUM_LOW_FIDELITY_METHOD_INPUT"
            if arm == ARM_B
            else "NONE"
        ),
        "nominal_evaluation_reference_read": False,
        "prediction_reference_free": True,
        "stress_fields_or_metrics_read": False,
    }
    exact = Path(path)
    exact.parent.mkdir(parents=True, exist_ok=True)
    with exact.open("xb") as handle:
        torch.save(payload, handle)
    return exact


def _append_json_line(handle: Any, payload: Mapping[str, Any]) -> None:
    handle.write(
        json.dumps(payload, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n"
    )
    handle.flush()


def _artifact_record(path: Path, root: Path) -> dict[str, Any]:
    return {
        "path": path.relative_to(root).as_posix(),
        "sha256": _sha256_path(path),
        "size_bytes": path.stat().st_size,
    }


def _validate_c_trigger(
    path: Path | None,
    *,
    source_identity: str | None = None,
    root: Path = ROOT,
    manifest_path: Path = DEPLOYED_SOURCE_MANIFEST_PATH,
) -> dict[str, Any]:
    if path is None:
        raise PermissionError("LF0 C requires the frozen post-B trigger record")
    trigger = _read_json(Path(path))
    required = (
        "b_competent",
        "b_provisional_increment_vs_all_comparators",
        "pde_ratio_pass",
        "preservation_pass",
        "potential_validity_pass",
    )
    if (
        trigger.get("schema_id") != "phk-v23-lf0-c-trigger-v1"
        or trigger.get("task_id") != TASK_ID
        or trigger.get("action") != "RUN_C_EXACT_TOP_COMPUTE_CONTROL_IF_TRIGGERED"
        or any(trigger.get(name) is not True for name in required)
        or trigger.get("stress_fields_or_metrics_read") is not False
    ):
        raise PermissionError("LF0 C trigger conditions are not all satisfied")
    bindings = trigger.get("input_bindings")
    if not isinstance(bindings, dict) or set(bindings) != set(
        C_TRIGGER_REQUIRED_EVIDENCE_BINDINGS
    ):
        raise PermissionError("LF0 C trigger evidence bindings are incomplete")
    for label, binding in bindings.items():
        if (
            not isinstance(binding, dict)
            or not isinstance(binding.get("path"), str)
            or not binding["path"]
            or not _is_upper_sha256(binding.get("sha256"))
            or not isinstance(binding.get("size_bytes"), int)
            or isinstance(binding.get("size_bytes"), bool)
            or binding["size_bytes"] <= 0
        ):
            raise PermissionError(f"LF0 C trigger evidence binding is malformed: {label}")
        lowered = binding["path"].replace("\\", "/").lower()
        if "stress" in lowered or "/sealed/" in f"/{lowered.strip('/')}" :
            raise PermissionError("LF0 C trigger must not bind stress or sealed evidence")

    if source_identity is None:
        raise PermissionError("LF0 C trigger requires its deployed source identity")
    deployment_root = Path(root).resolve()
    manifest = _read_json(Path(manifest_path))
    if manifest.get("source_identity") != source_identity:
        raise ValueError("LF0 C trigger deployment identity mismatch")
    files = manifest.get("files")
    if not isinstance(files, dict):
        raise ValueError("LF0 C trigger deployment has no file bindings")
    exact_trigger = Path(path).resolve()
    try:
        relative_trigger = exact_trigger.relative_to(deployment_root).as_posix()
    except ValueError as exc:
        raise PermissionError("LF0 C trigger is outside its deployed source root") from exc
    if files.get(relative_trigger) != _sha256_path(exact_trigger):
        raise ValueError("LF0 C trigger is not bound by the deployed source manifest")
    decision_relative = DECISION_CONTRACT_PATH.relative_to(ROOT).as_posix()
    decision_binding = bindings["decision_contract"]
    deployed_decision = deployment_root / decision_relative
    if (
        decision_binding["sha256"] != files.get(decision_relative)
        or decision_binding["size_bytes"] != deployed_decision.stat().st_size
    ):
        raise ValueError("LF0 C trigger decision-contract binding mismatch")
    return trigger


def _prediction_guard(
    prediction_path: Path,
    *,
    physics: PhkV22RPhysics,
    absolute_tolerance: float,
) -> dict[str, Any]:
    _, arrays = read_prediction_carrier(prediction_path)
    times = torch.as_tensor(arrays["time"], dtype=torch.float64).reshape(-1, 1)
    waveform = physics.waveform(times).detach().cpu().numpy().reshape(-1)
    return potential_maximum_principle_windowed_guard(
        arrays["potential"],
        arrays["time"],
        waveform,
        absolute_tolerance=absolute_tolerance,
    )


def _execute_reference_blind_gpu_arm(
    *,
    arm: str,
    output_root: Path,
    device_name: str,
    source_identity: str,
    hourly_price_cny: float,
    medium_carrier: Path | None = None,
    c_trigger_record: Path | None = None,
) -> dict[str, Any]:
    """Execute one frozen LF0 arm and emit recovery-ready cloud artifacts.

    This interface intentionally owns the complete A/B/C state machine.  It
    does not evaluate against the nominal development target and has no route
    to stress data.
    """

    if arm not in RUN_ARMS:
        raise ValueError(f"unknown LF0 arm: {arm}")
    contracts = load_contracts()
    identities = contract_identity()
    if not isinstance(source_identity, str) or not source_identity.startswith("LF0-BUNDLE-"):
        raise ValueError("LF0 source identity is missing or malformed")
    cpu_qualification = _assert_deployed_source_identity(source_identity)
    c_trigger = (
        _validate_c_trigger(c_trigger_record, source_identity=source_identity)
        if arm == ARM_C
        else None
    )
    if arm != ARM_C and c_trigger_record is not None:
        raise PermissionError("a C trigger record is valid only for LF0 C")
    price = float(hourly_price_cny)
    if not math.isfinite(price) or price <= 0.0:
        raise ValueError("LF0 hourly price must be positive and finite")
    if device_name != "cuda:0" or not torch.cuda.is_available():
        raise PermissionError("LF0 requires the authorized CUDA device cuda:0")
    device = torch.device(device_name)
    gpu_name = torch.cuda.get_device_name(device)
    if gpu_name != "Tesla V100-PCIE-32GB":
        raise PermissionError(f"LF0 GPU identity mismatch: {gpu_name}")
    if arm == ARM_B and medium_carrier is None:
        raise ValueError("LF0 B requires the frozen medium carrier")
    if arm != ARM_B and medium_carrier is not None:
        raise PermissionError("LF0 A/C must not open a low-fidelity carrier")
    output = Path(output_root).resolve()
    output.mkdir(parents=True, exist_ok=False)
    config = build_training_config(arm, device_name)
    _assert_config_identity(config, arm, contracts)
    physics, physical_program_sha256, physical_object_sha256 = load_case_physics(
        config.case_control
    )
    random.seed(config.seed)
    np.random.seed(config.seed)
    torch.manual_seed(config.seed)
    torch.cuda.manual_seed_all(config.seed)
    torch.cuda.reset_peak_memory_stats(device)
    model = build_exact_top_model(physics=physics, config=config).to(
        device=device, dtype=torch.float64
    )
    if model.architecture_manifest()["potential_output_transform"] != (
        "POTENTIAL_TRANSFORM_EXACT_TOP_AFFINE_RAW_LIFT"
    ):
        raise ValueError("LF0 model did not materialize the frozen exact-top transform")

    lf_stream = (
        _load_medium_stream(
            medium_carrier=Path(medium_carrier),
            physics=physics,
            contracts=contracts,
        )
        if arm == ARM_B and medium_carrier is not None
        else None
    )
    # The B physics sampler is deliberately absent throughout B0.  A/C create
    # it before their first (physics-local) update.
    physics_stream = (
        None
        if arm == ARM_B
        else LF0PhysicsBatchStream(
            physics=physics,
            interior_points=config.interior_points,
            boundary_points=config.boundary_points,
            initial_points=config.initial_points,
            refresh_updates=config.refresh_updates,
            seed=config.seed,
        )
    )
    optimizer_machine = LF0OptimizerStateMachine(
        model=model, arm=arm, learning_rate=config.learning_rate
    )
    started_at = datetime.now(timezone.utc).isoformat()
    started = time.perf_counter()
    run_identity = contracts["method"]["runs"][
        {ARM_A: "A", ARM_B: "B", ARM_C: "C"}[arm]
    ]["identity"]
    medium_relative = (
        contracts["data"]["training_source"]["path"] if arm == ARM_B else None
    )
    manifest_start = {
        "schema_id": "phk-v23-lf0-run-manifest-v1",
        "task_id": TASK_ID,
        "status": "RUNNING_REFERENCE_BLIND_GPU_ARM",
        "started_at_utc": started_at,
        "source_identity": source_identity,
        "cpu_qualification": cpu_qualification,
        "contracts": identities,
        "run_arm": arm,
        "run_identity": run_identity,
        "training_config": asdict(config),
        "training_config_sha256": config.identity,
        "architecture": model.architecture_manifest(),
        "device": gpu_name,
        "dtype": "FLOAT64",
        "seed": 17,
        "initialization": "SCRATCH_START",
        "gradient_combination": "LEGACY_SUMMED_LOSS_BACKWARD_NO_CONFIG",
        "physics_schedule_axis": "PHYSICS_LOCAL_OPTIMIZER_STEP",
        "medium_training_source": medium_relative,
        "medium_training_labels_used": arm == ARM_B,
        "fine_extra_fine_or_evaluator_read": False,
        "stress_fields_or_metrics_read": False,
        "manual_early_stop": False,
        "accuracy_checkpoint_selection": False,
        "checkpoint_policy": (
            "FIXED_STEP_800_AND_FINAL_STEP_2000_ONLY"
            if arm == ARM_B
            else f"FINAL_STEP_{config.updates}_ONLY"
        ),
        "c_trigger": (
            {
                "filename": Path(c_trigger_record).name,
                "sha256": _sha256_path(Path(c_trigger_record)),
            }
            if c_trigger is not None and c_trigger_record is not None
            else None
        ),
    }
    _write_json_exclusive(output / "manifest-start.json", manifest_start)

    log_path = output / "training-log.jsonl"
    physics_hash_path = output / "physics-batch-hashes.jsonl"
    lf_hash_path = output / "low-fidelity-batch-hashes.jsonl"
    checkpoints: dict[str, Path] = {}
    minimum_total = math.inf
    final_scalars: dict[str, float] = {}
    executed_global_steps = 0
    last_stage: str | None = None
    boundary_log_steps = {
        ARM_A: {1, 1199, 1200},
        ARM_B: {1, 799, 800, 801, 999, 1000, 1001, 1999, 2000},
        ARM_C: {1, 1999, 2000},
    }[arm]
    with (
        log_path.open("x", encoding="utf-8", newline="\n") as log_handle,
        physics_hash_path.open("x", encoding="utf-8", newline="\n") as physics_handle,
        lf_hash_path.open("x", encoding="utf-8", newline="\n") as lf_handle,
    ):
        for step in iter_run_steps(arm):
            optimizer = optimizer_machine.prepare(step)
            if step.uses_physics and physics_stream is None:
                if arm != ARM_B or step.stage != "B1_PHYSICS_PLUS_LF_ANCHOR":
                    raise RuntimeError("LF0 physics sampler construction boundary drift")
                physics_stream = LF0PhysicsBatchStream(
                    physics=physics,
                    interior_points=config.interior_points,
                    boundary_points=config.boundary_points,
                    initial_points=config.initial_points,
                    refresh_updates=config.refresh_updates,
                    seed=config.seed,
                )
            optimizer.zero_grad(set_to_none=True)
            total: torch.Tensor | None = None
            scalars: dict[str, float] = {}
            physics_batch: PhysicsBatch | None = None
            if step.physics_local_step is not None:
                assert physics_stream is not None
                physics_batch = physics_stream.draw(
                    model,
                    step.physics_local_step,
                    dtype=torch.float64,
                    device=device,
                )
                physics_loss, physics_scalars = _physics_objective(
                    model, physics_batch, config
                )
                total = physics_loss
                scalars.update(physics_scalars)
                _append_json_line(
                    physics_handle,
                    {
                        "global_step": step.global_step,
                        "physics_local_step": step.physics_local_step,
                        "stage": step.stage,
                        "active_windows": physics_batch.active_windows,
                        "refreshed": physics_batch.refreshed,
                        "interior_coordinate_sha256": physics_batch.interior_sha256,
                        "boundary_coordinate_sha256": physics_batch.boundary_sha256,
                        "initial_coordinate_sha256": physics_batch.initial_sha256,
                        "batch_sha256": physics_batch.batch_sha256,
                    },
                )
            if step.low_fidelity_step is not None:
                assert lf_stream is not None
                lf_batch = lf_stream.draw(step.low_fidelity_step)
                lf_loss, lf_components = _low_fidelity_objective(
                    model, lf_batch, physics=physics, device=device
                )
                weighted_lf = step.anchor_weight * lf_loss
                total = weighted_lf if total is None else total + weighted_lf
                scalars["low_fidelity_loss"] = float(lf_loss.detach().cpu())
                scalars.update(
                    {f"low_fidelity:{name}": value for name, value in lf_components.items()}
                )
                _append_json_line(
                    lf_handle,
                    {
                        "global_step": step.global_step,
                        "low_fidelity_step": step.low_fidelity_step,
                        "stage": step.stage,
                        "anchor_weight": step.anchor_weight,
                        "batch_sha256": lf_batch.batch_sha256,
                    },
                )
            if total is None or not bool(torch.isfinite(total)):
                raise FloatingPointError(f"LF0 non-finite objective at step {step.global_step}")
            total.backward()
            gradient_norm = torch.nn.utils.clip_grad_norm_(
                model.parameters(), config.gradient_clip_norm
            )
            if not bool(torch.isfinite(gradient_norm)):
                raise FloatingPointError(f"LF0 non-finite gradient at step {step.global_step}")
            optimizer.step()
            total_value = float(total.detach().cpu())
            minimum_total = min(minimum_total, total_value)
            final_scalars = {
                **scalars,
                "total_loss": total_value,
                "gradient_norm_before_clip": float(gradient_norm.detach().cpu()),
            }
            executed_global_steps = step.global_step
            stage_changed = step.stage != last_stage
            if (
                stage_changed
                or step.global_step % config.log_every == 0
                or step.global_step in boundary_log_steps
            ):
                _append_json_line(
                    log_handle,
                    {
                        "global_step": step.global_step,
                        "stage": step.stage,
                        "physics_local_step": step.physics_local_step,
                        "low_fidelity_step": step.low_fidelity_step,
                        "anchor_weight": step.anchor_weight,
                        "active_windows": (
                            physics_batch.active_windows if physics_batch is not None else 0
                        ),
                        "optimizer_role": optimizer_machine.role,
                        **final_scalars,
                    },
                )
            last_stage = step.stage
            if arm == ARM_B and step.global_step == 800:
                checkpoints["lf_data_only"] = _write_checkpoint(
                    path=output / "checkpoint-lf-data-only-step-800.pt",
                    model=model,
                    optimizer=optimizer,
                    config=config,
                    global_step=800,
                    physics_program_sha256=physical_program_sha256,
                    physics_object_sha256=physical_object_sha256,
                    arm=arm,
                    stage=step.stage,
                    source_identity=source_identity,
                    contracts=identities,
                )

    if executed_global_steps != config.updates:
        raise RuntimeError("LF0 run ended before its frozen final step")
    expected_physics_draws = {ARM_A: 1200, ARM_B: 1200, ARM_C: 2000}[arm]
    expected_lf_draws = 1000 if arm == ARM_B else 0
    if physics_stream is None or physics_stream.local_step != expected_physics_draws:
        raise RuntimeError("LF0 physics draw count drift")
    if (lf_stream.draw_count if lf_stream else 0) != expected_lf_draws:
        raise RuntimeError("LF0 low-fidelity draw count drift")
    expected_optimizer_instances = 2 if arm == ARM_B else 1
    if optimizer_machine.optimizer_instance_count != expected_optimizer_instances:
        raise RuntimeError("LF0 optimizer instance count drift")
    if arm == ARM_B and not optimizer_machine.b0_optimizer_destroyed:
        raise RuntimeError("LF0 B0 optimizer was not destroyed before B1")
    assert optimizer_machine.optimizer is not None
    checkpoints["final"] = _write_checkpoint(
        path=output / "checkpoint-final.pt",
        model=model,
        optimizer=optimizer_machine.optimizer,
        config=config,
        global_step=config.updates,
        physics_program_sha256=physical_program_sha256,
        physics_object_sha256=physical_object_sha256,
        arm=arm,
        stage=last_stage or "UNKNOWN",
        source_identity=source_identity,
        contracts=identities,
    )

    predictions: dict[str, Path] = {}
    if "lf_data_only" in checkpoints:
        predictions["lf_data_only"] = write_prediction_carrier(
            checkpoint_path=checkpoints["lf_data_only"],
            output_path=output / "prediction-lf-data-only-step-800.npz",
            device_name=device_name,
        )
    predictions["final"] = write_prediction_carrier(
        checkpoint_path=checkpoints["final"],
        output_path=output / "prediction-final.npz",
        device_name=device_name,
    )
    torch.cuda.synchronize(device)
    wall_seconds = time.perf_counter() - started
    absolute_tolerance = float(
        contracts["decision"]["potential_maximum_principle"]["absolute_tolerance"]
    )
    potential_guards = {
        name: _prediction_guard(
            path, physics=physics, absolute_tolerance=absolute_tolerance
        )
        for name, path in predictions.items()
    }
    validity_passed = all(item["passed"] for item in potential_guards.values())
    status = (
        "LF0_REFERENCE_BLIND_GPU_RUN_COMPLETE"
        if validity_passed
        else "LF0_NUMERICAL_OR_IDENTITY_INVALID"
    )
    environment_path = output / "environment.json"
    _write_json_exclusive(
        environment_path,
        {
            "schema_id": "phk-v23-lf0-environment-v1",
            "gpu_name": gpu_name,
            "torch_version": torch.__version__,
            "torch_cuda_version": torch.version.cuda,
            "numpy_version": np.__version__,
            "scipy_version": __import__("scipy").__version__,
            "python": os.sys.version,
            "omp_num_threads": os.environ.get("OMP_NUM_THREADS"),
            "medium_training_labels_present": arm == ARM_B,
            "fine_extra_fine_evaluator_present": False,
            "stress_fields_present": False,
        },
    )
    manifest_final_path = output / "manifest-final.json"
    _write_json_exclusive(
        manifest_final_path,
        {
            **manifest_start,
            "status": status,
            "finished_at_utc": datetime.now(timezone.utc).isoformat(),
            "executed_global_optimizer_steps": executed_global_steps,
            "optimizer_lifecycle": optimizer_machine.manifest(),
            "physics_batch_draws": physics_stream.local_step if physics_stream else 0,
            "physics_batch_rolling_sha256": (
                physics_stream.rolling_sha256 if physics_stream else None
            ),
            "low_fidelity_batch_draws": lf_stream.draw_count if lf_stream else 0,
            "low_fidelity_batch_rolling_sha256": (
                lf_stream.rolling_sha256 if lf_stream else None
            ),
            "potential_maximum_principle": potential_guards,
        },
    )
    files: dict[str, Path] = {
        "manifest_start": output / "manifest-start.json",
        "manifest_final": manifest_final_path,
        "training_log": log_path,
        "physics_batch_hashes": physics_hash_path,
        "low_fidelity_batch_hashes": lf_hash_path,
        "environment": environment_path,
        **{f"checkpoint_{name}": path for name, path in checkpoints.items()},
        **{f"prediction_{name}": path for name, path in predictions.items()},
    }
    summary = {
        "schema_id": "phk-v23-lf0-reference-blind-run-summary-v1",
        "task_id": TASK_ID,
        "status": status,
        "run_arm": arm,
        "run_identity": run_identity,
        "source_identity": source_identity,
        "contracts": identities,
        "device": gpu_name,
        "dtype": "FLOAT64",
        "seed": 17,
        "initialization": "SCRATCH_START",
        "architecture": model.architecture_manifest(),
        "executed_global_optimizer_steps": executed_global_steps,
        "physics_objective_steps": physics_stream.local_step if physics_stream else 0,
        "low_fidelity_batch_draws": lf_stream.draw_count if lf_stream else 0,
        "stage_update_counts": (
            {"A_PURE_PHYSICS": 1200}
            if arm == ARM_A
            else (
                {
                    "B0_LF_ONLY": 800,
                    "B1_PHYSICS_PLUS_LF_ANCHOR": 200,
                    "B2_PURE_PHYSICS": 1000,
                }
                if arm == ARM_B
                else {"C_PURE_PHYSICS": 2000}
            )
        ),
        "optimizer_lifecycle": optimizer_machine.manifest(),
        "minimum_total_loss_across_stage_objectives": minimum_total,
        "final_scalars": final_scalars,
        "physics_batch_rolling_sha256": (
            physics_stream.rolling_sha256 if physics_stream else None
        ),
        "low_fidelity_batch_rolling_sha256": (
            lf_stream.rolling_sha256 if lf_stream else None
        ),
        "potential_maximum_principle": potential_guards,
        "wall_seconds_including_prediction": wall_seconds,
        "gpu_hours": wall_seconds / 3600.0,
        "hourly_price_cny": price,
        "estimated_incremental_cost_cny": wall_seconds / 3600.0 * price,
        "medium_training_labels_used": arm == ARM_B,
        "fine_extra_fine_or_evaluator_read": False,
        "prediction_reference_free": True,
        "stress_fields_or_metrics_read": False,
        "manual_early_stop": False,
        "accuracy_checkpoint_selection": False,
        "artifacts": {name: _artifact_record(path, output) for name, path in files.items()},
    }
    _write_json_exclusive(output / "summary.json", summary)
    return summary


def run_reference_blind_gpu_arm(
    *,
    arm: str,
    output_root: Path,
    device_name: str,
    source_identity: str,
    hourly_price_cny: float,
    medium_carrier: Path | None = None,
    c_trigger_record: Path | None = None,
) -> dict[str, Any]:
    """Run one arm and preserve a truthful terminal record on numerical failure."""

    try:
        return _execute_reference_blind_gpu_arm(
            arm=arm,
            output_root=output_root,
            device_name=device_name,
            source_identity=source_identity,
            hourly_price_cny=hourly_price_cny,
            medium_carrier=medium_carrier,
            c_trigger_record=c_trigger_record,
        )
    except FloatingPointError as exc:
        output = Path(output_root).resolve()
        if not output.is_dir():
            raise
        existing = {
            path.name: _artifact_record(path, output)
            for path in sorted(output.iterdir())
            if path.is_file() and path.name not in {"summary.json", "manifest-final.json"}
        }
        terminal = {
            "schema_id": "phk-v23-lf0-reference-blind-run-summary-v1",
            "task_id": TASK_ID,
            "status": "LF0_NUMERICAL_OR_IDENTITY_INVALID",
            "run_arm": arm,
            "source_identity": source_identity,
            "failure_class": type(exc).__name__,
            "failure": str(exc),
            "finished_at_utc": datetime.now(timezone.utc).isoformat(),
            "prediction_reference_free": True,
            "stress_fields_or_metrics_read": False,
            "artifacts_recovered_before_shutdown": existing,
        }
        manifest_final = output / "manifest-final.json"
        if not manifest_final.exists():
            _write_json_exclusive(
                manifest_final,
                {
                    "schema_id": "phk-v23-lf0-run-manifest-v1",
                    "task_id": TASK_ID,
                    "status": "LF0_NUMERICAL_OR_IDENTITY_INVALID",
                    "run_arm": arm,
                    "source_identity": source_identity,
                    "failure_class": type(exc).__name__,
                    "failure": str(exc),
                    "finished_at_utc": terminal["finished_at_utc"],
                    "stress_fields_or_metrics_read": False,
                },
            )
        summary_path = output / "summary.json"
        if not summary_path.exists():
            _write_json_exclusive(summary_path, terminal)
        return terminal


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    run = subparsers.add_parser("run")
    run.add_argument("--arm", choices=RUN_ARMS, required=True)
    run.add_argument("--output-root", type=Path, required=True)
    run.add_argument("--device", default="cuda:0")
    run.add_argument("--source-identity", required=True)
    run.add_argument("--hourly-price-cny", type=float, required=True)
    run.add_argument("--medium-carrier", type=Path)
    run.add_argument("--c-trigger-record", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    summary = run_reference_blind_gpu_arm(
        arm=args.arm,
        output_root=args.output_root,
        device_name=args.device,
        source_identity=args.source_identity,
        hourly_price_cny=args.hourly_price_cny,
        medium_carrier=args.medium_carrier,
        c_trigger_record=args.c_trigger_record,
    )
    print(
        json.dumps(
            {
                "status": summary["status"],
                "run_arm": summary["run_arm"],
                "summary": str((Path(args.output_root).resolve() / "summary.json")),
            },
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
        )
    )
    return 0 if summary["status"] == "LF0_REFERENCE_BLIND_GPU_RUN_COMPLETE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
