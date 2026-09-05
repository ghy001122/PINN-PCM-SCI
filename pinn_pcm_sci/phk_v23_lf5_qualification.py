"""Zero-update CPU-T temporal geometry and mechanism qualification for LF5."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import torch

from .phk_v22r_training import ROOT, load_case_physics
from .phk_v23_lf0 import _sha256_path, _write_json_exclusive
from .phk_v23_lf2 import load_medium_dataset
from .phk_v23_lf4 import (
    ARM_C,
    ARM_M,
    BandStream,
    BaseDevelopmentStream,
    InterfaceBandDataset,
    precompute_stream_identities,
)
from .phk_v23_lf5 import (
    TASK_ID,
    TemporalEdgeDataset,
    TemporalEdgeStream,
    build_training_config,
    contract_identity,
    load_contracts,
    load_lf3_t0_model,
    precompute_temporal_stream_identity,
    temporal_pool_report,
    temporal_zero_level_terms,
)


def _verify_binding(binding: Mapping[str, Any], *, label: str) -> Path:
    path = (ROOT / str(binding["path"])).resolve()
    try: path.relative_to(ROOT.resolve())
    except ValueError as exc: raise PermissionError(f"LF5 {label} escaped repository") from exc
    if not path.is_file() or _sha256_path(path) != str(binding["sha256"]).upper():
        raise ValueError(f"LF5 {label} is absent or hash-drifted")
    return path


def _load_lf4_model(*, binding: Mapping[str, Any], role: str, initial: Path, physics: Any, config: Any) -> torch.nn.Module:
    path = _verify_binding(binding, label=role)
    model, _ = load_lf3_t0_model(initial, physics=physics, config=config, device=torch.device("cpu"), expected_sha256="4A679E54A4819A9D30CF55C6396C37129B9801BC635A8BD7EB3883F8F3B66EDA")
    payload = torch.load(path, map_location="cpu", weights_only=False)
    metadata = payload.get("lf4", {})
    if metadata.get("role") != role or int(metadata.get("optimizer_update", -1)) != 400:
        raise PermissionError(f"LF5 {role} is not the exact LF4 fixed endpoint")
    model.load_state_dict(payload["model_state_dict"], strict=True); model.eval()
    return model


def _timing_evidence(summary: Mapping[str, Any], telemetry_path: Path) -> dict[str, Any]:
    rows = [json.loads(line) for line in telemetry_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    result: dict[str, Any] = {}
    for role in (ARM_M, ARM_C):
        final_audit = summary["development"][role]["audit"]
        step350 = next((row for row in rows if row.get("arm") == role and row.get("step") == 350), None)
        role_report: dict[str, Any] = {"step_350": "UNKNOWN" if step350 is None else {}, "step_400": {}}
        for label, audit in (("step_350", None if step350 is None else step350.get("audit")), ("step_400", final_audit)):
            if audit is None: continue
            values: dict[str, Any] = {}
            for cycle in (1, 2):
                metric = audit["event_metrics"][f"cycle_{cycle}"]
                teacher = metric.get("teacher_event_time"); predicted = metric.get("predicted_event_time")
                values[f"cycle_{cycle}"] = {
                    "teacher_event_time": teacher,
                    "predicted_event_time": predicted,
                    "signed_predicted_minus_teacher": None if teacher is None or predicted is None else float(predicted) - float(teacher),
                    "direction": "UNKNOWN" if teacher is None or predicted is None else ("EARLY" if float(predicted) < float(teacher) else ("LATE" if float(predicted) > float(teacher) else "ALIGNED")),
                }
            role_report[label] = values
        result[role] = role_report
    return result


def compute_cpu_payload() -> dict[str, Any]:
    contracts = load_contracts(require_stream_freeze=True); data = contracts["data"]
    medium = _verify_binding(data["training_source"], label="medium")
    _verify_binding(data["lf1_b0_identity"], label="LF1-B0")
    initial = _verify_binding(data["initial_checkpoint"], label="LF3-T0 checkpoint")
    initial_prediction = initial.parent / "prediction-t0-step-1200.npz"
    if not initial_prediction.is_file() or _sha256_path(initial_prediction) != data["initial_checkpoint"]["prediction_sha256"]:
        raise ValueError("LF5 LF3-T0 prediction binding drift")
    fixed_paths = {name: _verify_binding(binding, label=f"LF4 {name}") for name, binding in data["LF4_fixed_inputs"].items()}
    compact_paths = {name: _verify_binding(binding, label=f"LF4 compact {name}") for name, binding in data["LF4_compact_evidence"].items()}
    config = build_training_config("cpu"); physics, _, _ = load_case_physics(config.case_control)
    dataset = load_medium_dataset(medium, physics=physics, contracts=contracts)
    if dataset.partition_sha256 != data["target_measure"]["partition_sha256"]: raise ValueError("LF5 partition hash drift")
    edges = TemporalEdgeDataset(dataset); temporal_identity = precompute_temporal_stream_identity(dataset)
    spatial_identity = precompute_stream_identities(dataset)
    stream_checks = {
        "base_window": spatial_identity["base_window_1201_1600_sha256"] == data["base_stream"]["development_window_sha256"],
        "spatial_band": spatial_identity["band_400_sha256"] == data["spatial_band_stream"]["rolling_sha256"],
        "temporal": temporal_identity["rolling_sha256"] == data["temporal_edge_stream"]["rolling_sha256"],
        "pool_counts": temporal_identity["pool_counts"] == data["temporal_edge_geometry"]["pool_counts"],
        "pool_hashes": temporal_identity["pool_hashes"] == data["temporal_edge_geometry"]["pool_hashes"],
    }
    model_m = _load_lf4_model(binding=data["LF4_fixed_inputs"]["DEV_M"], role=ARM_M, initial=initial, physics=physics, config=config)
    model_c = _load_lf4_model(binding=data["LF4_fixed_inputs"]["DEV_C"], role=ARM_C, initial=initial, physics=physics, config=config)
    report_m = temporal_pool_report(model_m, edges, physics=physics, device=torch.device("cpu")); report_c = temporal_pool_report(model_c, edges, physics=physics, device=torch.device("cpu"))
    summary = json.loads(fixed_paths["summary"].read_text(encoding="utf-8")); timing = _timing_evidence(summary, fixed_paths["telemetry"])
    onset_comparison: dict[str, Any] = {}
    onset_pass = True; sign_pass = True
    for cycle in (1, 2):
        pool = f"C{cycle}_ONSET"
        m_abs = report_m["pool_reports"][pool]["weighted_mean_absolute_residual"]
        c_abs = report_c["pool_reports"][pool]["weighted_mean_absolute_residual"]
        m_signed = report_m["pool_reports"][pool]["weighted_mean_signed_residual"]
        evidence = timing[ARM_M]["step_400"][f"cycle_{cycle}"]
        signed_time = evidence["signed_predicted_minus_teacher"]
        expected_residual_sign = None if signed_time is None else -int(np.sign(float(signed_time)))
        observed_residual_sign = int(np.sign(m_signed))
        comparison = {
            "DEV_M_weighted_mean_abs": m_abs,
            "DEV_C_weighted_mean_abs": c_abs,
            "DEV_C_strictly_better": c_abs < m_abs,
            "DEV_M_weighted_mean_signed": m_signed,
            "DEV_M_timing_direction": evidence["direction"],
            "expected_residual_sign_from_teacher_minus_prediction": expected_residual_sign,
            "observed_residual_sign": observed_residual_sign,
            "sign_aligned": expected_residual_sign is not None and expected_residual_sign == observed_residual_sign,
        }
        onset_comparison[pool] = comparison; onset_pass &= comparison["DEV_C_strictly_better"]; sign_pass &= comparison["sign_aligned"]
    model_t0, _ = load_lf3_t0_model(initial, physics=physics, config=config, device=torch.device("cpu"), expected_sha256=data["initial_checkpoint"]["sha256"])
    phase_parameters = tuple(model_t0.encoders["phase"].parameters()) + tuple(model_t0.heads["phase"].parameters())
    for parameter in phase_parameters: parameter.grad = None
    batch = TemporalEdgeStream(edges).draw(1); loss = temporal_zero_level_terms(model_t0, batch, physics=physics, device=torch.device("cpu"))["loss"]; loss.backward()
    grad_values = [torch.sum(parameter.grad.detach().square()) for parameter in phase_parameters if parameter.grad is not None]
    grad_norm = float(torch.sqrt(sum(grad_values)).cpu()) if grad_values else 0.0
    backward_pass = math.isfinite(float(loss.detach().cpu())) and math.isfinite(grad_norm) and grad_norm > 0.0
    checks = {
        "all_input_hashes": True,
        "partition": dataset.partition_sha256 == data["target_measure"]["partition_sha256"],
        "four_pools_nonempty": all(edges.pool_counts[name] > 0 for name in edges.pool_counts),
        "invalid_edge_fraction": edges.invalid_edge_fraction <= 0.01,
        "stream_hashes": all(stream_checks.values()),
        "raw_signed_timing_and_step350_present": all(timing[role]["step_350"] != "UNKNOWN" for role in (ARM_M, ARM_C)),
        "both_onset_DEV_C_strictly_better_than_DEV_M": onset_pass,
        "DEV_M_onset_sign_aligned": sign_pass,
        "finite_nonzero_phase_gradient_backward": backward_pass,
        "zero_optimizer_updates": True,
        "fine_extra_lf_only_stress_unread": True,
    }
    geometry_pass = all(checks[key] for key in ("partition","four_pools_nonempty","invalid_edge_fraction","stream_hashes","raw_signed_timing_and_step350_present","finite_nonzero_phase_gradient_backward"))
    status = "LF5_CPU_T_QUALIFICATION_PASS" if geometry_pass and onset_pass and sign_pass else ("LF5_TZL_ALIGNMENT_NOT_SUPPORTED_CPU" if geometry_pass else "LF5_TEMPORAL_GEOMETRY_BLOCKED")
    inherited_cpu = json.loads(compact_paths["cpu"].read_text(encoding="utf-8"))
    baseline = inherited_cpu.get("lf1_b0_full_medium_audit")
    if not isinstance(baseline, Mapping): raise ValueError("LF5 lacks inherited LF1-B0 full-medium audit")
    return {
        "schema_id":"phk-v23-lf5-cpu-qualification-v1","task_id":TASK_ID,"created_at_utc":datetime.now(timezone.utc).isoformat(),"status":status,"gpu_execution_authorized_by_cpu_gate":status=="LF5_CPU_T_QUALIFICATION_PASS","scientific_model_optimizer_updates":0,"gpu_used":False,"contracts":contract_identity(),"checks":checks,"partition_sha256":dataset.partition_sha256,"stream_checks":stream_checks,"stream_identities":{"base_window_1201_1600_sha256":spatial_identity["base_window_1201_1600_sha256"],"band_400_sha256":spatial_identity["band_400_sha256"],"temporal":temporal_identity},"temporal_geometry":{"cycle_semantics":"ONSET_W1_W3_THEN_RECOVERY_W2_W4_NO_WRAP","pool_counts":edges.pool_counts,"pool_hashes":edges.pool_hashes,"invalid_edge_count":edges.invalid_edge_count,"candidate_edge_count":edges.candidate_edge_count,"invalid_edge_fraction":edges.invalid_edge_fraction},"DEV_M_temporal_residuals":report_m,"DEV_C_temporal_residuals":report_c,"onset_mechanism_comparison":onset_comparison,"raw_timing_evidence":timing,"backward":{"loss":float(loss.detach().cpu()),"phase_gradient_norm":grad_norm,"optimizer_step_taken":False},"lf1_b0_full_medium_audit":baseline,"input_bindings":{"medium":{"path":str(medium),"sha256":_sha256_path(medium)},"lf3_t0_checkpoint":{"path":str(initial),"sha256":_sha256_path(initial)},"lf3_t0_prediction":{"path":str(initial_prediction),"sha256":_sha256_path(initial_prediction)},"LF4_fixed":{name:{"path":str(path),"sha256":_sha256_path(path)} for name,path in fixed_paths.items()},"LF4_compact":{name:{"path":str(path),"sha256":_sha256_path(path)} for name,path in compact_paths.items()}},"reference_boundary":{"fine_extra_read":False,"LF_ONLY_read":False,"stress_read":False,"frozen_evaluator_read":False},"claim_boundary":"CPU_T_CAN_FALSIFY_ALIGNMENT_INTERFACE_BUT_CANNOT_ESTABLISH_LATENT_OR_PINN_SUCCESS"}


def write_raw_cpu_evidence(*, output_directory: Path, payload: Mapping[str, Any]) -> Path:
    """Materialize ignored CPU-T pool and deterministic-stream evidence."""

    output = Path(output_directory).resolve()
    output.relative_to(ROOT.resolve())
    output.mkdir(parents=True, exist_ok=False)
    contracts = load_contracts(require_stream_freeze=True)
    data = contracts["data"]
    lock = json.loads((ROOT / "configs/phk_v23/lf5_write_allowlist_lock.json").read_text(encoding="utf-8"))
    _write_json_exclusive(
        output / "manifest-start.json",
        {
            "schema_id": "phk-v23-lf5-cpu-t-raw-start-v1",
            "task_id": TASK_ID,
            "branch": lock["start_identity"]["branch"],
            "head": lock["start_identity"]["head"],
            "initial_git_status_sha256": lock["start_identity"]["initial_status_sha256"],
            "initial_git_status_entry_count": lock["start_identity"]["initial_status_entry_count"],
            "initial_allowlist_overlap": lock["start_identity"]["initial_overlap"],
            "contracts": contract_identity(),
            "scientific_optimizer_updates": 0,
        },
    )
    config = build_training_config("cpu")
    physics, _, _ = load_case_physics(config.case_control)
    medium = _verify_binding(data["training_source"], label="medium")
    dataset = load_medium_dataset(medium, physics=physics, contracts=contracts)
    edges = TemporalEdgeDataset(dataset)
    pool_payload: dict[str, Any] = {
        "schema_id": "phk-v23-lf5-temporal-pools-v1",
        "task_id": TASK_ID,
        "partition_sha256": dataset.partition_sha256,
        "pool_order": list(edges.records),
        "candidate_edge_count": edges.candidate_edge_count,
        "invalid_edge_count": edges.invalid_edge_count,
        "invalid_edge_fraction": edges.invalid_edge_fraction,
        "pool_hashes": edges.pool_hashes,
        "pools": {},
    }
    for name, record in edges.records.items():
        pool_payload["pools"][name] = [
            {
                "cell": int(cell),
                "k": int(k),
                "k1": int(k1),
                "rho_star": float(rho),
                "teacher_denominator": float(denominator),
                "edge_weight": float(weight),
                "sampling_probability": float(probability),
            }
            for cell, k, k1, rho, denominator, weight, probability in zip(
                record["cell"], record["k"], record["k1"], record["rho"],
                record["denominator"], record["edge_weight"], record["probability"], strict=True,
            )
        ]
    _write_json_exclusive(output / "temporal-pools.json", pool_payload)
    stream = TemporalEdgeStream(edges)
    ledger_path = output / "temporal-stream-ledger.jsonl"
    with ledger_path.open("x", encoding="utf-8", newline="\n") as handle:
        for step in range(1, 401):
            batch = stream.draw(step)
            handle.write(json.dumps({"step":step,"batch_sha256":batch.batch_sha256,"rolling_sha256":stream.rolling_sha256,"pool_counts":dict(batch.pool_counts)},sort_keys=True,separators=(",",":")) + "\n")
    if stream.rolling_sha256 != data["temporal_edge_stream"]["rolling_sha256"]:
        raise ValueError("LF5 raw temporal stream identity drift")
    _write_json_exclusive(output / "cpu-t-report.json", dict(payload))
    records = {}
    for name in ("manifest-start.json", "temporal-pools.json", "temporal-stream-ledger.jsonl", "cpu-t-report.json"):
        path = output / name
        records[name] = {"size_bytes": path.stat().st_size, "sha256": _sha256_path(path)}
    _write_json_exclusive(output / "manifest-final.json", {"schema_id":"phk-v23-lf5-cpu-t-raw-final-v1","task_id":TASK_ID,"outcome":payload["status"],"scientific_optimizer_updates":0,"gpu_trajectories":0,"cloud_connection_opened":False,"DEV_T":"NOT_RUN","P0":"NOT_RUN","temporal_stream_sha256":stream.rolling_sha256,"artifacts":records})
    return output


def qualify_cpu(*, artifact_path: Path, manifest_path: Path, raw_output_directory: Path | None = None) -> dict[str, Any]:
    artifact_path=Path(artifact_path).resolve(); manifest_path=Path(manifest_path).resolve()
    if artifact_path.exists():
        payload=json.loads(artifact_path.read_text(encoding="utf-8"))
        if payload.get("task_id") != TASK_ID or payload.get("contracts") != contract_identity(): raise ValueError("existing LF5 CPU artifact identity drift")
    else:
        payload=compute_cpu_payload(); _write_json_exclusive(artifact_path,payload)
    manifest={"schema_version":"run-manifest-v1","run_id":"20260905T150045Z-phk-v23-lf5-cpu-qualification","experiment_group_id":"PHK_V23_LF5","tier":"qualification","scientific_role":"cpu_only_temporal_zero_level_geometry_and_mechanism_qualification","gate":"PHK_V23_LF5_CPU_T","gate_outcome":payload["status"],"execution_status":"COMPLETE","claim_status":"LF5_LOCAL_TEMPORAL_ALIGNMENT_PREMISE_REFUTED_NO_GPU" if payload["status"]=="LF5_TZL_ALIGNMENT_NOT_SUPPORTED_CPU" else "LF5_CPU_T_QUALIFIED","numerical_validity":"VALID_CPU_FP64_HASH_BOUND","route_disposition":"STOP_BEFORE_GPU" if payload["status"]!="LF5_CPU_T_QUALIFICATION_PASS" else "RUN_FIXED_DEV_T_THEN_CONDITIONAL_P0","method_id":"phk-v23-lf5-cycle-resolved-temporal-zero-level-alignment-v1","case_id":"PHK_V21_NOMINAL_MEDIUM_TEMPORAL_EDGE_QUALIFICATION","physical_contract_id":"PHK_V21_FIXED_DISCRETIZATION_FULL_NOMINAL","split_id":"MEDIUM_AND_LF4_FIXED_ENDPOINTS_CPU_ONLY_FINE_EXTRA_LF_ONLY_STRESS_UNREAD","seed":17,"replay_of":None,"supersedes":None,"started_at":"2026-09-05T15:00:45+00:00","ended_at":payload["created_at_utc"],"planned_budget":{"gpu_trajectories":0,"optimizer_updates":0},"actual_budget":{"gpu_trajectories":0,"optimizer_updates":0,"gpu_used":False},"environment":{"device":"CPU","dtype":"FLOAT64","cloud_connection_opened":False,"stress_status":"TWO_STRESS_REFERENCES_SEALED_UNREAD"},"evaluator_id":"NOT_READ_DURING_CPU_T","evidence_identity":"ZERO_UPDATE_TEMPORAL_ALIGNMENT_QUALIFICATION","failure_class":None if payload["status"]=="LF5_CPU_T_QUALIFICATION_PASS" else payload["status"],"code_identity":{"base_commit":"d86ddf1d206c611087a1b5284acda69efdfda9fa"},"checkpoint":{"source_sha256":"4A679E54A4819A9D30CF55C6396C37129B9801BC635A8BD7EB3883F8F3B66EDA","loaded_read_only":True},"artifacts":{"compact_qualification":f"artifacts/{artifact_path.name}#sha256={_sha256_path(artifact_path)}"},"command":[".venv/Scripts/python.exe","-m","pinn_pcm_sci.phk_v23_lf5_qualification"]}
    if manifest_path.exists():
        existing=json.loads(manifest_path.read_text(encoding="utf-8"))
        if existing.get("schema_version")!="run-manifest-v1" or existing.get("gate_outcome")!=payload["status"] or _sha256_path(artifact_path) not in json.dumps(existing): raise ValueError("existing LF5 CPU manifest drift")
    else: _write_json_exclusive(manifest_path,manifest)
    if raw_output_directory is not None:
        write_raw_cpu_evidence(output_directory=raw_output_directory, payload=payload)
    return payload


def _parser() -> argparse.ArgumentParser:
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument("--artifact",type=Path); parser.add_argument("--manifest",type=Path); parser.add_argument("--raw-output-directory",type=Path); parser.add_argument("--precompute-stream",action="store_true"); return parser


def main(argv: Sequence[str] | None=None)->int:
    args=_parser().parse_args(argv)
    if args.precompute_stream:
        contracts=load_contracts(); config=build_training_config("cpu"); physics,_,_=load_case_physics(config.case_control); dataset=load_medium_dataset(ROOT/contracts["data"]["training_source"]["path"],physics=physics,contracts=contracts); print(json.dumps(precompute_temporal_stream_identity(dataset),sort_keys=True)); return 0
    if args.artifact is None or args.manifest is None: raise SystemExit("--artifact and --manifest are required")
    payload=qualify_cpu(artifact_path=args.artifact,manifest_path=args.manifest,raw_output_directory=args.raw_output_directory); print(json.dumps({"status":payload["status"],"gpu_authorized":payload["gpu_execution_authorized_by_cpu_gate"]},sort_keys=True)); return 0


if __name__ == "__main__": raise SystemExit(main())


__all__=["compute_cpu_payload","qualify_cpu","write_raw_cpu_evidence"]
