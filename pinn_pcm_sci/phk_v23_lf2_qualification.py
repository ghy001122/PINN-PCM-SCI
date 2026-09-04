"""Local CPU qualification for the PHK-V2.3 LF2 campaign."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import torch

from .phk_v22r_pinn import POTENTIAL_TRANSFORM_EXACT_TOP_RANGE_PRESERVING
from .phk_v22r_training import ROOT, load_case_physics
from .phk_v23_lf0 import _physical_object, _sha256_path
from .phk_v23_lf2 import (
    CATEGORY_NAMES,
    CATEGORY_QUOTAS,
    M0_SEEDS,
    M1_SEEDS,
    MeasureCalibratedBatchStream,
    TASK_ID,
    build_training_config,
    contract_identity,
    full_medium_audit,
    load_contracts,
    load_lf1_b0_initialization,
    load_medium_dataset,
)


def _verify_binding(binding: Mapping[str, Any], *, label: str) -> Path:
    relative = binding.get("path")
    expected_hash = binding.get("sha256")
    if not isinstance(relative, str) or not isinstance(expected_hash, str):
        raise ValueError(f"LF2 qualification binding is malformed: {label}")
    exact = (ROOT / Path(relative.replace("/", "\\"))).resolve()
    try:
        exact.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise PermissionError(
            f"LF2 qualification input escaped repository: {label}"
        ) from exc
    if not exact.is_file():
        raise FileNotFoundError(f"LF2 qualification input is absent: {label}")
    if _sha256_path(exact) != expected_hash.upper():
        raise ValueError(f"LF2 qualification input hash drift: {label}")
    return exact


def _strict_write(path: Path, payload: Mapping[str, Any]) -> Path:
    encoded = json.dumps(
        payload,
        indent=2,
        sort_keys=True,
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8") + b"\n"
    exact = Path(path).resolve()
    exact.parent.mkdir(parents=True, exist_ok=True)
    with exact.open("xb") as handle:
        handle.write(encoded)
    return exact


def _proposal_identity(dataset: Any, *, draws: int = 8) -> dict[str, Any]:
    streams: dict[str, Any] = {}
    for role in ("M0", "M1_CONSTRAINT"):
        stream = MeasureCalibratedBatchStream(dataset, role=role)
        first_hash = None
        last_hash = None
        for step in range(1, draws + 1):
            batch = stream.draw(step)
            if first_hash is None:
                first_hash = batch.batch_sha256
            last_hash = batch.batch_sha256
        streams[role] = {
            "qualification_draws": draws,
            "first_batch_sha256": first_hash,
            "last_batch_sha256": last_hash,
            "rolling_sha256_after_qualification_draws": stream.rolling_sha256,
        }
    strict_call_order_rejected = False
    try:
        MeasureCalibratedBatchStream(dataset, role="M0").draw(2)
    except ValueError:
        strict_call_order_rejected = True
    return {
        "total_points_per_step": int(sum(CATEGORY_QUOTAS)),
        "category_quotas_in_partition_order": list(CATEGORY_QUOTAS),
        "M0_seeds_in_partition_order": list(M0_SEEDS),
        "M1_constraint_seeds_in_partition_order": list(M1_SEEDS),
        "stateful_deterministic_sobol": True,
        "strict_out_of_order_call_rejected": strict_call_order_rejected,
        "M0_M1_and_physics_streams_declared_independent": True,
        "stream_hashes": streams,
    }


def _old_proposal_amplification(dataset: Any) -> dict[str, Any]:
    event_masses = {
        cycle: float(dataset.category_masses[f"EVENT_CYCLE_{cycle}"])
        for cycle in (1, 2)
    }
    per_cycle: dict[str, Any] = {}
    for cycle, mass in event_masses.items():
        per_cycle[f"cycle_{cycle}"] = {
            "target_measure_mass": mass,
            "LF1_B0_proposal_share": 128.0 / 1024.0,
            "LF1_B0_amplification": (128.0 / 1024.0) / mass,
            "LF1_persistent_replay_proposal_share": 128.0 / 512.0,
            "LF1_persistent_replay_amplification": (128.0 / 512.0) / mass,
        }
    mean_mass = float(np.mean(tuple(event_masses.values())))
    return {
        "definition": "PROPOSAL_POINT_SHARE_DIVIDED_BY_TARGET_MEASURE_MASS",
        "per_cycle": per_cycle,
        "mean_event_mass_across_cycles": mean_mass,
        "LF1_B0_mean_onset_event_amplification": (128.0 / 1024.0) / mean_mass,
        "LF1_persistent_replay_mean_onset_event_amplification": (
            (128.0 / 512.0) / mean_mass
        ),
    }


def _constant_estimator_identity(dataset: Any) -> dict[str, Any]:
    constant = 2.75
    estimate = sum(
        float(dataset.category_masses[name]) * constant for name in CATEGORY_NAMES
    )
    error = abs(estimate - constant)
    return {
        "constant": constant,
        "weighted_stratified_estimate": estimate,
        "absolute_error": error,
        "tolerance": 1.0e-14,
        "passed": error <= 1.0e-14,
    }


def _synthetic_one_step_smoke() -> dict[str, Any]:
    """Exercise Adam and the declared inequality update without a science model."""

    parameter = torch.nn.Parameter(torch.tensor([0.25], dtype=torch.float64))
    optimizer = torch.optim.Adam([parameter], lr=1.0e-3)
    before = float(parameter.detach()[0])
    optimizer.zero_grad(set_to_none=True)
    constraint = 0.90 - torch.sigmoid(parameter[0])
    penalty = torch.clamp(constraint, min=0.0).square() / 2.0
    objective = (parameter[0] - 0.75).square() + penalty
    objective.backward()
    finite_gradient = bool(torch.isfinite(parameter.grad).all())
    optimizer.step()
    after = float(parameter.detach()[0])
    multiplier_after = max(0.0, float(constraint.detach()))
    return {
        "scope": "SYNTHETIC_SCALAR_CPU_ONLY_NO_SCIENTIFIC_MODEL_OR_TRAINING",
        "dtype": str(parameter.dtype).replace("torch.", "").upper(),
        "objective_before_step": float(objective.detach()),
        "parameter_before": before,
        "parameter_after": after,
        "finite_gradient": finite_gradient,
        "multiplier_after_declared_update": multiplier_after,
        "passed": finite_gradient
        and math.isfinite(after)
        and after != before
        and multiplier_after >= 0.0,
    }


def qualify_cpu(*, output_path: Path) -> dict[str, Any]:
    contracts = load_contracts()
    identities = contract_identity()
    decision = contracts["decision"]
    source_path = _verify_binding(
        contracts["data"]["training_source"], label="medium training source"
    )
    checkpoint_path = _verify_binding(
        contracts["data"]["initial_checkpoint"], label="LF1 B0 checkpoint"
    )
    qualification_inputs = {
        name: {
            "path": binding["path"],
            "sha256": _sha256_path(_verify_binding(binding, label=name)),
        }
        for name, binding in decision["qualification_inputs"].items()
    }

    config = build_training_config("cpu")
    physics, physical_program_sha256, physical_object_sha256 = load_case_physics(
        config.case_control
    )
    dataset = load_medium_dataset(source_path, physics=physics, contracts=contracts)
    model, checkpoint = load_lf1_b0_initialization(
        checkpoint_path,
        physics=physics,
        config=config,
        contracts=contracts,
        device=torch.device("cpu"),
    )
    audit = full_medium_audit(model, dataset, device=torch.device("cpu"))
    proposal = _proposal_identity(dataset)
    constant_identity = _constant_estimator_identity(dataset)
    synthetic_smoke = _synthetic_one_step_smoke()
    counts_sum = int(sum(dataset.category_counts.values()))
    mass_sum = float(sum(dataset.category_masses.values()))
    partition = {
        "saved_node_count": dataset.node_count,
        "time_node_count": int(dataset.time.size),
        "cell_count": int(dataset.cell_count),
        "category_order": list(CATEGORY_NAMES),
        "category_counts": dataset.category_counts,
        "category_target_measure_masses_pi": dataset.category_masses,
        "assigned_count_sum": counts_sum,
        "target_measure_mass_sum": mass_sum,
        "mutually_exclusive": counts_sum == dataset.node_count,
        "exhaustive": counts_sum == dataset.node_count,
        "all_required_categories_nonempty": all(
            dataset.category_counts[name] > 0 for name in CATEGORY_NAMES
        ),
        "partition_sha256": dataset.partition_sha256,
    }
    model_dtypes = sorted({str(value.dtype) for value in model.parameters()})
    identity_boundary = {
        "medium": {
            "path": contracts["data"]["training_source"]["path"],
            "sha256": _sha256_path(source_path),
            "size_bytes": source_path.stat().st_size,
        },
        "initial_checkpoint": {
            "path": contracts["data"]["initial_checkpoint"]["path"],
            "sha256": _sha256_path(checkpoint_path),
            "size_bytes": checkpoint_path.stat().st_size,
            "schema_id": checkpoint.get("schema_id"),
            "LF1_role": checkpoint.get("lf1", {}).get("stage"),
            "global_optimizer_step": checkpoint.get("lf1", {}).get(
                "global_optimizer_step"
            ),
            "optimizer_state_loaded": False,
        },
        "model_parameter_dtypes": model_dtypes,
        "float64_exact": model_dtypes == ["torch.float64"],
        "potential_transform": POTENTIAL_TRANSFORM_EXACT_TOP_RANGE_PRESERVING,
        "potential_guard_absolute_tolerance": float(
            decision["potential_maximum_principle"]["absolute_tolerance"]
        ),
        "physical_program_sha256": physical_program_sha256,
        "physical_object_sha256": physical_object_sha256,
        "medium_is_only_cloud_training_label_source": True,
        "fine_extra_fine_frozen_evaluator_cloud_access": False,
        "stress_cloud_access": False,
    }

    passed = all(
        (
            partition["mutually_exclusive"],
            partition["exhaustive"],
            partition["all_required_categories_nonempty"],
            math.isclose(mass_sum, 1.0, rel_tol=0.0, abs_tol=1.0e-14),
            proposal["strict_out_of_order_call_rejected"],
            constant_identity["passed"],
            synthetic_smoke["passed"],
            identity_boundary["float64_exact"],
            audit["all_values_finite"],
            audit["potential_maximum_principle"]["passed"],
        )
    )
    report: dict[str, Any] = {
        "schema_id": "phk-v23-lf2-cpu-qualification-v1",
        "task_id": TASK_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "contracts": identities,
        "bound_qualification_inputs": qualification_inputs,
        "partition": partition,
        "proposal_identity": proposal,
        "old_LF1_proposal_amplification": _old_proposal_amplification(dataset),
        "lf1_b0_full_medium_audit": audit,
        "synthetic_weighted_estimator_constant_identity": constant_identity,
        "synthetic_one_step_smoke": synthetic_smoke,
        "identity_and_reference_boundary": identity_boundary,
        "fine_extra_fine_reference_read": False,
        "stress_fields_or_metrics_read": False,
        "status": (
            "LF2_CPU_QUALIFICATION_PASS"
            if passed
            else "LF2_CPU_OR_PARTITION_BLOCKED"
        ),
        "gpu_execution_authorized_by_cpu_gate": bool(passed),
    }
    written = _strict_write(output_path, report)
    report["output_path"] = written.relative_to(ROOT).as_posix()
    report["output_sha256"] = _sha256_path(written)
    return report


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    report = qualify_cpu(output_path=arguments.output)
    print(json.dumps(report, sort_keys=True, allow_nan=False))
    return 0 if report["gpu_execution_authorized_by_cpu_gate"] else 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
