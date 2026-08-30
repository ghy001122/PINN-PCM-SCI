"""Machine adjudication and two-stage confirmation freeze for PHK-V2.2R v1.1."""

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
from .phk_v22r_prediction import read_prediction_carrier
from .phk_v22r_reference import TARGETS


ROOT = Path(__file__).resolve().parents[1]
CONFIRMATION_CASES = (
    PhkControl.INTERFACE_WIDTH_0_025,
    PhkControl.HEATER_WIDTH_0_50,
)
CONFIRMATION_ROLES = (
    "SELECTED_METHOD",
    "STRONGEST_COMPARATOR",
    "PARAMETER_MATCHED_MEASURED_TIME_BUDGET_RAW_CONTROL",
)


def _sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def _portable_path(path: Path) -> str:
    resolved = Path(path).resolve()
    try:
        return str(resolved.relative_to(ROOT))
    except ValueError:
        return str(resolved)


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid JSON artifact: {path}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"JSON artifact is not an object: {path}")
    return payload


def _write_json_exclusive(path: Path, payload: Mapping[str, Any]) -> None:
    exact = Path(path)
    exact.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(
        payload,
        indent=2,
        sort_keys=True,
        ensure_ascii=False,
        allow_nan=False,
    )
    with exact.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(serialized)
        handle.write("\n")


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


def _terminal_nominal_decision(
    *,
    status: str,
    reason: str,
    eligible: Mapping[str, bool],
) -> dict[str, Any]:
    return {
        "schema_id": "phk-v22r-nominal-decision-v1-1",
        "status": status,
        "eligible": dict(eligible),
        "selected_arm": None,
        "strongest_comparator": None,
        "confirmation_training_authorized": False,
        "stress_unseal_authorized": False,
        "reason": reason,
        "terminal_no_rescue": True,
    }


def adjudicate_nominal(
    evaluations: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    """Apply the frozen four-arm decision; only the full arm may advance."""

    required_arms = {
        PhkV22RArm.STRONG_RAW.value,
        PhkV22RArm.MF_ONLY.value,
        PhkV22RArm.SAMPLER_ONLY.value,
        PhkV22RArm.MF_PLUS_SAMPLER.value,
    }
    if set(evaluations) != required_arms:
        raise ValueError("nominal adjudication requires exactly the four v1.1 arms")
    for arm, report in evaluations.items():
        if report.get("case_control") != PhkControl.FULL.value:
            raise ValueError(f"{arm} is not a nominal-case evaluation")
        architecture = report.get("architecture")
        if not isinstance(architecture, dict) or architecture.get("arm") != arm:
            raise ValueError(f"{arm} evaluation architecture identity mismatch")
        _metrics(report)

    eligible = {arm: _eligible(report) for arm, report in evaluations.items()}
    if not any(eligible.values()):
        return _terminal_nominal_decision(
            status="MVP_NO_GO_NO_BASIC_COMPETENCE",
            reason="ALL_FOUR_ARMS_FAILED_FROZEN_COMPETENCE_GUARDS",
            eligible=eligible,
        )

    combined_arm = PhkV22RArm.MF_PLUS_SAMPLER.value
    if not eligible[combined_arm]:
        return _terminal_nominal_decision(
            status="MVP_NO_GO_NO_ATTRIBUTABLE_GAIN",
            reason="FULL_ARM_FAILED_COMPETENCE_WHILE_ANOTHER_ARM_WAS_COMPETENT",
            eligible=eligible,
        )

    component_arms = [
        arm
        for arm in (PhkV22RArm.MF_ONLY.value, PhkV22RArm.SAMPLER_ONLY.value)
        if eligible[arm]
    ]
    if not component_arms:
        return _terminal_nominal_decision(
            status="MVP_NO_GO_NO_ATTRIBUTABLE_GAIN",
            reason="NO_COMPETENT_COMPONENT_COMPARATOR_FOR_ATTRIBUTION",
            eligible=eligible,
        )

    strongest = min(
        component_arms,
        key=lambda arm: _geometric_error(
            float(
                _metrics(evaluations[arm])[
                    "time_averaged_phase_region_symmetric_difference"
                ]
            ),
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
        "schema_id": "phk-v22r-nominal-decision-v1-1",
        "status": (
            "SELECTED_PHYSICS_ONLY_MF_PLUS_SAMPLER"
            if passed
            else "MVP_NO_GO_NO_ATTRIBUTABLE_GAIN"
        ),
        "eligible": eligible,
        "selected_arm": combined_arm if passed else None,
        "strongest_comparator": strongest,
        "confirmation_training_authorized": passed,
        "stress_unseal_authorized": False,
        "ratios": {
            "primary_vs_strongest_comparator": primary_ratio,
            "co_primary_vs_strongest_comparator": co_primary_ratio,
            "joint_vs_strongest_comparator": joint_ratio,
            "joint_vs_strong_raw": raw_joint_ratio,
        },
        "noninferiority_limits": {
            "temperature": temperature_limit,
            "current": current_limit,
        },
        "gates": gates,
        "reason": (
            "ALL_FROZEN_COMPETENCE_GAIN_AND_NONINFERIORITY_GATES_PASS"
            if passed
            else "ONE_OR_MORE_FROZEN_GAIN_OR_NONINFERIORITY_GATES_FAILED"
        ),
        "terminal_no_rescue": not passed,
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
                "path": _portable_path(source),
                "sha256": _sha256_path(source),
                "training_config_sha256": evaluations[arm][
                    "training_config_sha256"
                ],
            }
            for arm, source in evaluation_paths.items()
        },
    }
    _write_json_exclusive(path, payload)
    return payload


def _complete_manifest(path: Path) -> dict[str, Any]:
    manifest = _load_json(path)
    if manifest.get("schema_id") != "phk-v22r-training-run-manifest-v1-1":
        raise ValueError("training manifest is not a v1.1 artifact")
    if manifest.get("status") != "COMPLETE":
        raise ValueError("training manifest is not complete")
    if manifest.get("reference_fields_read") is not False:
        raise ValueError("training manifest is not reference blind")
    if manifest.get("training_labels_used") is not False:
        raise ValueError("training manifest used labels")
    if manifest.get("initialization") != "SCRATCH_START":
        raise ValueError("training manifest is not a scratch start")
    if manifest.get("checkpoint_policy") != "FINAL_ONLY":
        raise ValueError("training manifest did not preserve final-checkpoint only")
    if manifest.get("program_contract_sha256") != _sha256_path(PROGRAM_CONTRACT):
        raise ValueError("training manifest program contract drift")
    if manifest.get("method_contract_sha256") != _sha256_path(METHOD_CONTRACT):
        raise ValueError("training manifest method contract drift")
    config = manifest.get("training_config")
    architecture = manifest.get("architecture")
    if not isinstance(config, dict) or not isinstance(architecture, dict):
        raise ValueError("training manifest lacks config or architecture")
    if manifest.get("training_config_sha256") is None:
        raise ValueError("training manifest lacks a configuration hash")
    return manifest


def _assert_common_v11_config(config: Mapping[str, Any]) -> None:
    required = {
        "case_control": PhkControl.FULL.value,
        "seed": 17,
        "frequency_band": "BAND_A",
        "learning_rate": 1.0e-3,
        "gradient_clip_norm": 10.0,
        "interior_points": 512,
        "boundary_points": 128,
        "initial_points": 128,
        "candidate_pool_multiplier": 4,
        "refresh_updates": 250,
        "pde_weight": 1.0,
        "boundary_weight": 5.0,
        "initial_weight": 1.0,
        "dtype": "float64",
    }
    for key, expected in required.items():
        if config.get(key) != expected:
            raise ValueError(f"training manifest changed frozen v1.1 key: {key}")


def _stress_seals() -> dict[str, Any]:
    seals: dict[str, Any] = {}
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
        seals[control.value] = {
            "byte_seal_path": _portable_path(byte_seal_path),
            "byte_seal_sha256": _sha256_path(byte_seal_path),
            "carrier_sha256": seal["carrier_sha256"],
            "carrier_size_bytes": seal["carrier_size_bytes"],
        }
    return seals


def write_confirmation_plan(
    path: Path,
    *,
    nominal_decision_path: Path,
    selected_training_manifest_path: Path,
    comparator_training_manifest_path: Path,
    raw_timing_manifest_path: Path,
) -> dict[str, Any]:
    """Freeze the three confirmation roles without authorizing reference access."""

    decision = _load_json(nominal_decision_path)
    if decision.get("status") != "SELECTED_PHYSICS_ONLY_MF_PLUS_SAMPLER":
        raise ValueError("only a passing v1.1 nominal decision may plan confirmation")
    if decision.get("confirmation_training_authorized") is not True:
        raise ValueError("nominal decision did not authorize confirmation training")
    if decision.get("stress_unseal_authorized") is not False:
        raise ValueError("nominal decision incorrectly authorized stress unsealing")

    selected = _complete_manifest(selected_training_manifest_path)
    comparator = _complete_manifest(comparator_training_manifest_path)
    raw_timing = _complete_manifest(raw_timing_manifest_path)
    selected_config = dict(selected["training_config"])
    comparator_config = dict(comparator["training_config"])
    raw_timing_config = dict(raw_timing["training_config"])
    for config in (selected_config, comparator_config, raw_timing_config):
        _assert_common_v11_config(config)

    if selected_config.get("arm") != PhkV22RArm.MF_PLUS_SAMPLER.value:
        raise ValueError("selected manifest is not MF_PLUS_SAMPLER")
    if int(selected_config.get("updates", -1)) != 1000:
        raise ValueError("selected manifest does not use 1000 updates")
    strongest = decision.get("strongest_comparator")
    if strongest not in {
        PhkV22RArm.MF_ONLY.value,
        PhkV22RArm.SAMPLER_ONLY.value,
    }:
        raise ValueError("nominal decision lacks a valid strongest comparator")
    if comparator_config.get("arm") != strongest:
        raise ValueError("comparator manifest differs from the nominal decision")
    if int(comparator_config.get("updates", -1)) != 1000:
        raise ValueError("comparator manifest does not use 1000 updates")

    method = _load_json(METHOD_CONTRACT)
    raw_rule = method["fairness"][
        "parameter_matched_measured_time_budget_raw_control"
    ]
    expected_raw = {
        "arm": PhkV22RArm.STRONG_RAW.value,
        "hidden_width": int(raw_rule["hidden_width"]),
        "hidden_layers": int(raw_rule["hidden_layers"]),
        "updates": int(raw_rule["timing_calibration_updates"]),
    }
    for key, expected in expected_raw.items():
        if raw_timing_config.get(key) != expected:
            raise ValueError(f"raw timing calibration identity mismatch: {key}")
    if int(raw_timing["architecture"].get("trainable_parameter_count", -1)) != int(
        raw_rule["trainable_parameter_count"]
    ):
        raise ValueError("raw timing calibration is not parameter matched")

    selected_seconds = float(selected.get("wall_seconds", math.nan))
    raw_seconds_per_update = float(raw_timing.get("seconds_per_update", math.nan))
    if not math.isfinite(selected_seconds) or selected_seconds <= 0.0:
        raise ValueError("selected nominal manifest lacks finite measured wall time")
    if not math.isfinite(raw_seconds_per_update) or raw_seconds_per_update <= 0.0:
        raise ValueError("raw timing manifest lacks finite seconds/update")
    raw_updates = math.floor(selected_seconds / raw_seconds_per_update)
    if raw_updates < int(raw_rule["minimum_updates"]):
        raise ValueError("measured-time raw update budget is below the frozen minimum")

    selected_template = {**selected_config, "case_control": "<STRESS_CASE>"}
    comparator_template = {**comparator_config, "case_control": "<STRESS_CASE>"}
    raw_template = {
        **raw_timing_config,
        "case_control": "<STRESS_CASE>",
        "updates": raw_updates,
        "log_every": 25,
        "checkpoint_every": raw_updates,
    }
    payload = {
        "schema_id": "phk-v22r-confirmation-plan-v1-1",
        "status": "IDENTITIES_FROZEN_PREDICTIONS_PENDING",
        "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
        "program_contract_sha256": _sha256_path(PROGRAM_CONTRACT),
        "method_contract_sha256": _sha256_path(METHOD_CONTRACT),
        "nominal_decision": {
            "path": _portable_path(nominal_decision_path),
            "sha256": _sha256_path(nominal_decision_path),
            "status": decision["status"],
        },
        "roles": {
            "SELECTED_METHOD": {
                "arm": selected_config["arm"],
                "training_config_template": selected_template,
                "nominal_training_manifest_path": _portable_path(
                    selected_training_manifest_path
                ),
                "nominal_training_manifest_sha256": _sha256_path(
                    selected_training_manifest_path
                ),
            },
            "STRONGEST_COMPARATOR": {
                "arm": comparator_config["arm"],
                "training_config_template": comparator_template,
                "nominal_training_manifest_path": _portable_path(
                    comparator_training_manifest_path
                ),
                "nominal_training_manifest_sha256": _sha256_path(
                    comparator_training_manifest_path
                ),
            },
            "PARAMETER_MATCHED_MEASURED_TIME_BUDGET_RAW_CONTROL": {
                "arm": PhkV22RArm.STRONG_RAW.value,
                "training_config_template": raw_template,
                "trainable_parameter_count": int(
                    raw_rule["trainable_parameter_count"]
                ),
                "parameter_ratio_to_selected": float(
                    raw_rule["parameter_ratio_to_mf_plus_sampler"]
                ),
                "selected_nominal_training_wall_seconds": selected_seconds,
                "raw_calibration_seconds_per_update": raw_seconds_per_update,
                "derived_updates": raw_updates,
                "update_rule": raw_rule["update_rule"],
                "raw_timing_manifest_path": _portable_path(raw_timing_manifest_path),
                "raw_timing_manifest_sha256": _sha256_path(raw_timing_manifest_path),
            },
        },
        "confirmation_cases": [control.value for control in CONFIRMATION_CASES],
        "required_prediction_count": 6,
        "stress_reference_seals": _stress_seals(),
        "stress_reference_access_authorized": False,
        "final_freeze_rule": "VERIFY_ALL_SIX_REFERENCE_BLIND_PREDICTION_IDENTITIES_AND_HASHES_BEFORE_WRITING_CANDIDATE_FREEZE",
        "immutable_after_this_plan": [
            "ROLE_IDENTITIES",
            "ARCHITECTURES",
            "SEED",
            "LOSS_AND_SAMPLING",
            "SELECTED_AND_COMPARATOR_UPDATES",
            "RAW_TIME_BUDGET_AND_DERIVED_UPDATES",
            "METRICS_AND_THRESHOLDS",
        ],
    }
    _write_json_exclusive(path, payload)
    return payload


def _expected_prediction_keys() -> set[tuple[str, str]]:
    return {
        (control.value, role)
        for control in CONFIRMATION_CASES
        for role in CONFIRMATION_ROLES
    }


def freeze_selected_candidate(
    path: Path,
    *,
    confirmation_plan_path: Path,
    prediction_paths: Mapping[tuple[str, str], Path],
) -> dict[str, Any]:
    """Write the final freeze only after six blind carriers pass identity checks."""

    plan = _load_json(confirmation_plan_path)
    if plan.get("schema_id") != "phk-v22r-confirmation-plan-v1-1":
        raise ValueError("confirmation plan schema is not v1.1")
    if plan.get("status") != "IDENTITIES_FROZEN_PREDICTIONS_PENDING":
        raise ValueError("confirmation plan is not awaiting predictions")
    if plan.get("stress_reference_access_authorized") is not False:
        raise ValueError("confirmation plan did not preserve the sealed boundary")
    if plan.get("program_contract_sha256") != _sha256_path(PROGRAM_CONTRACT):
        raise ValueError("confirmation plan is not bound to the live program contract")
    if plan.get("method_contract_sha256") != _sha256_path(METHOD_CONTRACT):
        raise ValueError("confirmation plan is not bound to the live method contract")
    if set(prediction_paths) != _expected_prediction_keys():
        raise ValueError("final freeze requires exactly two cases by three roles")

    verified: dict[str, dict[str, Any]] = {}
    for control in CONFIRMATION_CASES:
        case_records: dict[str, Any] = {}
        for role in CONFIRMATION_ROLES:
            prediction_path = Path(prediction_paths[(control.value, role)])
            metadata, arrays = read_prediction_carrier(prediction_path)
            del arrays
            if metadata.get("reference_fields_read") is not False:
                raise ValueError("confirmation prediction is not reference blind")
            if metadata.get("program_contract_sha256") != _sha256_path(
                PROGRAM_CONTRACT
            ):
                raise ValueError("confirmation prediction program contract mismatch")
            if metadata.get("method_contract_sha256") != _sha256_path(METHOD_CONTRACT):
                raise ValueError("confirmation prediction method contract mismatch")
            config = metadata.get("training_config")
            if not isinstance(config, dict):
                raise ValueError("confirmation prediction lacks a training config")
            template = dict(plan["roles"][role]["training_config_template"])
            template["case_control"] = control.value
            if config != template:
                raise ValueError(
                    f"{control.value}/{role} changed the frozen training identity"
                )
            if metadata.get("checkpoint_update") != int(template["updates"]):
                raise ValueError(f"{control.value}/{role} is not a final checkpoint")
            architecture = metadata.get("architecture")
            if not isinstance(architecture, dict):
                raise ValueError("confirmation prediction lacks architecture identity")
            if architecture.get("arm") != plan["roles"][role]["arm"]:
                raise ValueError(f"{control.value}/{role} arm identity mismatch")
            if role == "PARAMETER_MATCHED_MEASURED_TIME_BUDGET_RAW_CONTROL":
                if int(architecture.get("trainable_parameter_count", -1)) != int(
                    plan["roles"][role]["trainable_parameter_count"]
                ):
                    raise ValueError("confirmation raw control is not parameter matched")
            case_records[role] = {
                "path": _portable_path(prediction_path),
                "sha256": _sha256_path(prediction_path),
                "size_bytes": prediction_path.stat().st_size,
                "training_config_sha256": metadata["training_config_sha256"],
                "checkpoint_sha256": metadata["checkpoint_sha256"],
                "checkpoint_update": metadata["checkpoint_update"],
                "arm": architecture["arm"],
                "reference_fields_read": False,
            }
        verified[control.value] = case_records

    live_seals = _stress_seals()
    if live_seals != plan.get("stress_reference_seals"):
        raise ValueError("stress byte seals changed after the confirmation plan")
    payload = {
        "schema_id": "phk-v22r-candidate-freeze-v1-1",
        "status": "FROZEN_SIX_PREDICTION_IDENTITIES_VERIFIED",
        "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
        "program_contract_sha256": _sha256_path(PROGRAM_CONTRACT),
        "method_contract_sha256": _sha256_path(METHOD_CONTRACT),
        "confirmation_plan": {
            "path": _portable_path(confirmation_plan_path),
            "sha256": _sha256_path(confirmation_plan_path),
            "status": plan["status"],
        },
        "roles": plan["roles"],
        "confirmation_cases": plan["confirmation_cases"],
        "verified_prediction_count": 6,
        "prediction_carriers": verified,
        "stress_reference_seals": live_seals,
        "stress_reference_access_authorized": True,
        "immutable_after_freeze": [
            "ARCHITECTURES",
            "HYPERPARAMETERS",
            "LOSS_AND_SAMPLING",
            "SEED",
            "UPDATES_OR_TIME_BUDGET_RULE",
            "METRICS_AND_THRESHOLDS",
            "ROLE_IDENTITIES",
            "PREDICTION_CARRIER_HASHES",
        ],
        "stress_results_may_not_trigger": [
            "METHOD_OR_HYPERPARAMETER_CHANGE",
            "NEW_SEED_OR_TRAINING_EXTENSION",
            "NEW_MODULE_OR_ROUTE",
            "CASE_OR_METRIC_SUPPRESSION",
        ],
    }
    _write_json_exclusive(path, payload)
    return payload


def _prediction_mapping(args: argparse.Namespace) -> dict[tuple[str, str], Path]:
    return {
        (PhkControl.INTERFACE_WIDTH_0_025.value, "SELECTED_METHOD"): args.narrow_selected,
        (
            PhkControl.INTERFACE_WIDTH_0_025.value,
            "STRONGEST_COMPARATOR",
        ): args.narrow_comparator,
        (
            PhkControl.INTERFACE_WIDTH_0_025.value,
            "PARAMETER_MATCHED_MEASURED_TIME_BUDGET_RAW_CONTROL",
        ): args.narrow_raw,
        (PhkControl.HEATER_WIDTH_0_50.value, "SELECTED_METHOD"): args.wide_selected,
        (PhkControl.HEATER_WIDTH_0_50.value, "STRONGEST_COMPARATOR"): args.wide_comparator,
        (
            PhkControl.HEATER_WIDTH_0_50.value,
            "PARAMETER_MATCHED_MEASURED_TIME_BUDGET_RAW_CONTROL",
        ): args.wide_raw,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    decide = subparsers.add_parser("decide")
    decide.add_argument("--raw", type=Path, required=True)
    decide.add_argument("--mf-only", type=Path, required=True)
    decide.add_argument("--sampler-only", type=Path, required=True)
    decide.add_argument("--combined", type=Path, required=True)
    decide.add_argument("--output", type=Path, required=True)

    plan = subparsers.add_parser("plan-confirmation")
    plan.add_argument("--nominal-decision", type=Path, required=True)
    plan.add_argument("--selected-manifest", type=Path, required=True)
    plan.add_argument("--comparator-manifest", type=Path, required=True)
    plan.add_argument("--raw-timing-manifest", type=Path, required=True)
    plan.add_argument("--output", type=Path, required=True)

    freeze = subparsers.add_parser("freeze")
    freeze.add_argument("--confirmation-plan", type=Path, required=True)
    freeze.add_argument("--narrow-selected", type=Path, required=True)
    freeze.add_argument("--narrow-comparator", type=Path, required=True)
    freeze.add_argument("--narrow-raw", type=Path, required=True)
    freeze.add_argument("--wide-selected", type=Path, required=True)
    freeze.add_argument("--wide-comparator", type=Path, required=True)
    freeze.add_argument("--wide-raw", type=Path, required=True)
    freeze.add_argument("--output", type=Path, required=True)
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
    elif args.command == "plan-confirmation":
        payload = write_confirmation_plan(
            args.output,
            nominal_decision_path=args.nominal_decision,
            selected_training_manifest_path=args.selected_manifest,
            comparator_training_manifest_path=args.comparator_manifest,
            raw_timing_manifest_path=args.raw_timing_manifest,
        )
    elif args.command == "freeze":
        payload = freeze_selected_candidate(
            args.output,
            confirmation_plan_path=args.confirmation_plan,
            prediction_paths=_prediction_mapping(args),
        )
    else:
        raise AssertionError("unreachable command")
    print(
        json.dumps(
            {
                "status": payload["status"],
                "stress_reference_access_authorized": payload.get(
                    "stress_reference_access_authorized",
                    payload.get("stress_unseal_authorized", False),
                ),
                "output": str(args.output.resolve()),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "CONFIRMATION_CASES",
    "CONFIRMATION_ROLES",
    "adjudicate_nominal",
    "freeze_selected_candidate",
    "main",
    "write_confirmation_plan",
    "write_nominal_decision",
]
