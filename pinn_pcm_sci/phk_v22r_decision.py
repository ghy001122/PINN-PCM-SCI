"""Machine adjudication and one-way candidate freeze for PHK-V2.2R."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping

from .phk_benchmark import PhkControl
from .phk_v22r_evaluator import METHOD_CONTRACT, PROGRAM_CONTRACT
from .phk_v22r_pinn import PhkV22RArm
from .phk_v22r_reference import TARGETS


ROOT = Path(__file__).resolve().parents[1]


def _sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid JSON artifact: {path}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"JSON artifact is not an object: {path}")
    return payload


def _metrics(record: Mapping[str, Any]) -> Mapping[str, float]:
    metrics = record.get("metrics")
    if not isinstance(metrics, dict):
        raise ValueError("nominal evaluation record lacks metrics")
    required = {
        "time_averaged_phase_region_symmetric_difference",
        "phase_roi_continuous_rms",
        "temperature_roi_nrmse_by_0_45",
        "terminal_current_trace_nrmse",
    }
    if not required.issubset(metrics):
        raise ValueError("nominal evaluation record lacks decision metrics")
    return metrics


def _eligible(record: Mapping[str, Any]) -> bool:
    hard = record.get("hard_guards")
    trend = record.get("training_trend")
    return bool(
        isinstance(hard, dict)
        and hard.get("passed") is True
        and isinstance(trend, dict)
        and trend.get("decreasing_pde_loss") is True
    )


def _geometric_error(primary: float, co_primary: float) -> float:
    return math.sqrt(max(primary, 1.0e-15) * max(co_primary, 1.0e-15))


def adjudicate_nominal(
    evaluations: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    """Apply the frozen physics-only route-A decision without rescue tuning."""

    required_arms = {
        PhkV22RArm.STRONG_RAW.value,
        PhkV22RArm.MF_ONLY.value,
        PhkV22RArm.SAMPLER_ONLY.value,
        PhkV22RArm.MF_PLUS_SAMPLER.value,
    }
    if set(evaluations) != required_arms:
        raise ValueError("nominal adjudication requires exactly the four primary arms")
    for arm, report in evaluations.items():
        if report.get("case_control") != PhkControl.FULL.value:
            raise ValueError(f"{arm} is not a nominal-case evaluation")
        architecture = report.get("architecture")
        if not isinstance(architecture, dict) or architecture.get("arm") != arm:
            raise ValueError(f"{arm} evaluation architecture identity mismatch")
        _metrics(report)

    eligible = {arm: _eligible(report) for arm, report in evaluations.items()}
    if not any(eligible.values()):
        return {
            "schema_id": "phk-v22r-nominal-decision-v1",
            "status": "ROUTE_A_ALL_ARMS_INCOMPETENT_ALLOW_SINGLE_ROUTE_B",
            "eligible": eligible,
            "selected_arm": None,
            "stress_unseal_authorized": False,
            "reason": "ALL_ROUTE_A_ARMS_FAILED_HARD_COMPETENCE_GUARDS",
        }
    combined_arm = PhkV22RArm.MF_PLUS_SAMPLER.value
    if not eligible[combined_arm]:
        return {
            "schema_id": "phk-v22r-nominal-decision-v1",
            "status": "MVP_NO_GO_NO_ATTRIBUTABLE_GAIN",
            "eligible": eligible,
            "selected_arm": None,
            "stress_unseal_authorized": False,
            "reason": "COMBINED_ARM_FAILED_HARD_GUARDS_WHILE_ROUTE_A_HAS_COMPETENT_ARM",
        }
    component_arms = [
        arm
        for arm in (PhkV22RArm.MF_ONLY.value, PhkV22RArm.SAMPLER_ONLY.value)
        if eligible[arm]
    ]
    if not component_arms:
        return {
            "schema_id": "phk-v22r-nominal-decision-v1",
            "status": "MVP_NO_GO_NO_ATTRIBUTABLE_GAIN",
            "eligible": eligible,
            "selected_arm": None,
            "stress_unseal_authorized": False,
            "reason": "NO_COMPETENT_COMPONENT_COMPARATOR_FOR_ATTRIBUTION",
        }
    strongest = min(
        component_arms,
        key=lambda arm: _geometric_error(
            float(_metrics(evaluations[arm])[
                "time_averaged_phase_region_symmetric_difference"
            ]),
            float(_metrics(evaluations[arm])["phase_roi_continuous_rms"]),
        ),
    )
    combined = _metrics(evaluations[combined_arm])
    comparator = _metrics(evaluations[strongest])
    raw = _metrics(evaluations[PhkV22RArm.STRONG_RAW.value])
    primary_ratio = float(
        combined["time_averaged_phase_region_symmetric_difference"]
    ) / max(
        float(comparator["time_averaged_phase_region_symmetric_difference"]),
        1.0e-15,
    )
    co_primary_ratio = float(combined["phase_roi_continuous_rms"]) / max(
        float(comparator["phase_roi_continuous_rms"]), 1.0e-15
    )
    joint_ratio = math.sqrt(primary_ratio * co_primary_ratio)
    raw_joint_ratio = _geometric_error(
        float(combined["time_averaged_phase_region_symmetric_difference"]),
        float(combined["phase_roi_continuous_rms"]),
    ) / max(
        _geometric_error(
            float(raw["time_averaged_phase_region_symmetric_difference"]),
            float(raw["phase_roi_continuous_rms"]),
        ),
        1.0e-15,
    )
    temperature_limit = max(
        1.10 * float(comparator["temperature_roi_nrmse_by_0_45"]), 0.05
    )
    current_limit = max(
        1.10 * float(comparator["terminal_current_trace_nrmse"]), 0.15
    )
    gates = {
        "primary_ratio_le_0_98": primary_ratio <= 0.98,
        "co_primary_ratio_le_0_98": co_primary_ratio <= 0.98,
        "joint_ratio_le_0_95": joint_ratio <= 0.95,
        "joint_ratio_vs_raw_le_0_90": raw_joint_ratio <= 0.90,
        "temperature_noninferiority": float(
            combined["temperature_roi_nrmse_by_0_45"]
        )
        <= temperature_limit,
        "current_noninferiority": float(combined["terminal_current_trace_nrmse"])
        <= current_limit,
    }
    passed = all(gates.values())
    return {
        "schema_id": "phk-v22r-nominal-decision-v1",
        "status": (
            "SELECTED_PHYSICS_ONLY_MF_PLUS_SAMPLER"
            if passed
            else "MVP_NO_GO_NO_ATTRIBUTABLE_GAIN"
        ),
        "eligible": eligible,
        "selected_arm": combined_arm if passed else None,
        "strongest_component": strongest,
        "stress_unseal_authorized": passed,
        "ratios": {
            "primary_vs_strongest_component": primary_ratio,
            "co_primary_vs_strongest_component": co_primary_ratio,
            "joint_vs_strongest_component": joint_ratio,
            "joint_vs_strong_raw": raw_joint_ratio,
        },
        "noninferiority_limits": {
            "temperature": temperature_limit,
            "current": current_limit,
        },
        "gates": gates,
        "reason": "ALL_FROZEN_GAIN_AND_NONINFERIORITY_GATES_PASS"
        if passed
        else "ONE_OR_MORE_FROZEN_GAIN_OR_NONINFERIORITY_GATES_FAILED",
    }


def write_nominal_decision(
    path: Path,
    *,
    evaluation_paths: Mapping[str, Path],
) -> dict[str, Any]:
    evaluations = {arm: _load_json(source) for arm, source in evaluation_paths.items()}
    decision = adjudicate_nominal(evaluations)
    payload = {
        **decision,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "program_contract_sha256": _sha256_path(PROGRAM_CONTRACT),
        "method_contract_sha256": _sha256_path(METHOD_CONTRACT),
        "evaluation_artifacts": {
            arm: {
                "path": str(source.resolve().relative_to(ROOT)),
                "sha256": _sha256_path(source),
                "training_config_sha256": evaluations[arm][
                    "training_config_sha256"
                ],
            }
            for arm, source in evaluation_paths.items()
        },
    }
    exact = Path(path)
    exact.parent.mkdir(parents=True, exist_ok=True)
    with exact.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")
    return payload


def freeze_selected_candidate(
    path: Path,
    *,
    nominal_decision_path: Path,
    selected_training_manifest_path: Path,
    equal_compute_raw_identity: Mapping[str, Any],
) -> dict[str, Any]:
    """Write the one-way candidate freeze and bind both unread stress byte seals."""

    decision = _load_json(nominal_decision_path)
    if decision.get("status") != "SELECTED_PHYSICS_ONLY_MF_PLUS_SAMPLER":
        raise ValueError("only a passing frozen nominal decision can unseal stress cases")
    manifest = _load_json(selected_training_manifest_path)
    config = manifest.get("training_config")
    architecture = manifest.get("architecture")
    if not isinstance(config, dict) or not isinstance(architecture, dict):
        raise ValueError("selected training manifest lacks config or architecture")
    if config.get("arm") != PhkV22RArm.MF_PLUS_SAMPLER.value:
        raise ValueError("selected training manifest is not the combined arm")
    if manifest.get("status") != "COMPLETE":
        raise ValueError("selected training run is not complete")
    method_contract = _load_json(METHOD_CONTRACT)
    expected_equal_raw = method_contract["fairness"]["equal_compute_raw"]
    required_equal_raw = {
        "arm": PhkV22RArm.STRONG_RAW.value,
        "hidden_width": int(expected_equal_raw["hidden_width"]),
        "hidden_layers": int(expected_equal_raw["hidden_layers"]),
        "trainable_parameter_count": int(
            expected_equal_raw["trainable_parameter_count"]
        ),
    }
    for key, expected in required_equal_raw.items():
        if equal_compute_raw_identity.get(key) != expected:
            raise ValueError(f"equal-compute raw identity mismatch: {key}")

    stress_seals = {}
    for control, directory in TARGETS.items():
        byte_seal_path = directory / "byte-seal.json"
        seal = _load_json(byte_seal_path)
        if seal.get("status") != "SEALED_UNREAD_PENDING_CANDIDATE_FREEZE":
            raise ValueError(f"{control.value} is not in the unread sealed state")
        carrier = directory / "reference.npz"
        if seal.get("carrier_sha256") != _sha256_path(carrier):
            raise ValueError(f"{control.value} sealed carrier hash mismatch")
        if seal.get("field_or_metric_read_after_write") is not False:
            raise ValueError(f"{control.value} seal does not preserve unread status")
        stress_seals[control.value] = {
            "byte_seal_path": str(byte_seal_path.resolve().relative_to(ROOT)),
            "byte_seal_sha256": _sha256_path(byte_seal_path),
            "carrier_sha256": seal["carrier_sha256"],
            "carrier_size_bytes": seal["carrier_size_bytes"],
        }

    payload = {
        "schema_id": "phk-v22r-candidate-freeze-v1",
        "status": "FROZEN",
        "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
        "program_contract_sha256": _sha256_path(PROGRAM_CONTRACT),
        "method_contract_sha256": _sha256_path(METHOD_CONTRACT),
        "nominal_decision": {
            "path": str(Path(nominal_decision_path).resolve().relative_to(ROOT)),
            "sha256": _sha256_path(nominal_decision_path),
            "status": decision["status"],
        },
        "selected_candidate": {
            "arm": config["arm"],
            "training_config_sha256": manifest["training_config_sha256"],
            "seed": config["seed"],
            "updates": config["updates"],
            "architecture": architecture,
            "training_config": config,
            "decision_status": decision["status"],
            "training_manifest_path": str(
                Path(selected_training_manifest_path).resolve().relative_to(ROOT)
            ),
            "training_manifest_sha256": _sha256_path(
                selected_training_manifest_path
            ),
        },
        "strongest_component": decision["strongest_component"],
        "equal_compute_raw_identity": required_equal_raw,
        "stress_reference_seals": stress_seals,
        "immutable_after_freeze": [
            "ARCHITECTURE",
            "HYPERPARAMETERS",
            "LOSS_AND_SAMPLING",
            "SEED",
            "UPDATES",
            "METRICS_AND_THRESHOLDS",
            "ROUTE_A_OR_B",
            "STRONGEST_COMPONENT",
            "EQUAL_COMPUTE_RAW_IDENTITY",
        ],
        "stress_results_may_not_trigger": [
            "METHOD_OR_HYPERPARAMETER_CHANGE",
            "A_TO_B_RESCUE",
            "SEED_REPLACEMENT",
            "CASE_SUPPRESSION",
        ],
    }
    exact = Path(path)
    exact.parent.mkdir(parents=True, exist_ok=True)
    with exact.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")
    return payload


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    decide = subparsers.add_parser("decide")
    decide.add_argument("--raw", type=Path, required=True)
    decide.add_argument("--mf-only", type=Path, required=True)
    decide.add_argument("--sampler-only", type=Path, required=True)
    decide.add_argument("--combined", type=Path, required=True)
    decide.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "decide":
        payload = write_nominal_decision(
            args.output,
            evaluation_paths={
                PhkV22RArm.STRONG_RAW.value: args.raw,
                PhkV22RArm.MF_ONLY.value: args.mf_only,
                PhkV22RArm.SAMPLER_ONLY.value: args.sampler_only,
                PhkV22RArm.MF_PLUS_SAMPLER.value: args.combined,
            },
        )
        print(
            json.dumps(
                {
                    "status": payload["status"],
                    "selected_arm": payload["selected_arm"],
                    "stress_unseal_authorized": payload[
                        "stress_unseal_authorized"
                    ],
                    "output": str(args.output.resolve()),
                },
                sort_keys=True,
            )
        )
        return 0
    raise AssertionError("unreachable command")


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "adjudicate_nominal",
    "freeze_selected_candidate",
    "main",
    "write_nominal_decision",
]
