"""CPU-F geometry qualification and full deterministic ledger materialization."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import torch

from .phk_v22r_pinn import PhkCollocationSampler
from .phk_v22r_training import ROOT, load_case_physics
from .phk_v23_lf0 import LF0PhysicsBatchStream, _read_json, _sha256_path, _write_json_exclusive
from .phk_v23_lf2 import load_medium_dataset
from .phk_v23_lf3 import build_training_config, full_medium_audit
from .phk_v23_lf4 import ARM_M as LF4_ARM_M
from .phk_v23_lf4 import BandStream, BaseDevelopmentStream, InterfaceBandDataset, _field_state_sha256, contract_identity as lf4_contract_identity, load_lf3_t0_model
from .phk_v23_lf6 import (
    DEV_M,
    DEV_R,
    FRONTIER_POOL_NAMES,
    LEDGER_ARRAY_NAMES,
    TASK_ID,
    EndpointBatch,
    array_sha256,
    contract_identity,
    endpoint_logit_loss,
    load_contracts,
    rolling_batch_sha256,
    semantic_ledger_sha256,
)


Q = 0.02
EPSILON = 1.0e-8
UNIFORM_SEEDS = (17611, 17612, 17613, 17614)
LF4_TASK_ID = "PHK_V23_LF4_THRESHOLD_ALIGNED_INTERFACE_BAND_MECHANISM_AND_CONDITIONAL_PHYSICS_PILOT_EXECUTE"
LF4_SOURCE_IDENTITY = "LF4-BUNDLE-EF532BCCF7FAC4482BEBD56A49DFAFE2D5F2FD4B2043540BD4414B6668CA644F"


def _verify_binding(binding: Mapping[str, Any], *, label: str) -> Path:
    path = (ROOT / str(binding["path"])).resolve()
    try:
        path.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise PermissionError(f"LF6 {label} escaped repository") from exc
    if not path.is_file() or _sha256_path(path) != str(binding["sha256"]).upper():
        raise ValueError(f"LF6 {label} is absent or hash-drifted")
    return path


def _stable_descending_order(values: np.ndarray, cell_indices: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=np.float64).reshape(-1)
    cells = np.asarray(cell_indices, dtype=np.int64).reshape(-1)
    if values.shape != cells.shape or not np.isfinite(values).all():
        raise ValueError("LF6 stable-rank input is invalid")
    return np.lexsort((cells, -values))


def event_frontier_geometry(dataset: Any) -> dict[str, Any]:
    roi_cells = np.flatnonzero(dataset.roi_cells).astype(np.int64)
    count = int(roi_cells.size)
    critical_rank = int(math.ceil(Q * count))
    phase = np.clip(dataset.fields["phase"][:, roi_cells], EPSILON, 1.0 - EPSILON)
    logits = np.log(phase / (1.0 - phase))
    active_count = np.sum(logits >= 0.0, axis=1).astype(np.int64)
    active_fraction = active_count.astype(np.float64) / float(count)
    records: dict[str, Any] = {}
    frontier: dict[str, np.ndarray] = {}
    uniform: dict[str, np.ndarray] = {}
    for cycle, window, before_name, after_name, seed_pair in (
        (1, "W1", "C1_PRE", "C1_POST", UNIFORM_SEEDS[:2]),
        (2, "W3", "C2_PRE", "C2_POST", UNIFORM_SEEDS[2:]),
    ):
        indices = np.flatnonzero(dataset.window_time_masks[window])
        bracket: tuple[int, int] | None = None
        for first, second in zip(indices[:-1], indices[1:], strict=True):
            if active_fraction[first] < Q <= active_fraction[second]:
                bracket = (int(first), int(second)); break
        if bracket is None:
            raise ValueError(f"LF6 cycle {cycle} has no first 2% active-fraction bracket")
        minus, plus = bracket; n_minus = int(active_count[minus]); n_plus = int(active_count[plus])
        if n_plus <= n_minus or not (n_minus < critical_rank <= n_plus):
            raise ValueError(f"LF6 cycle {cycle} critical-rank containment failed")
        rank_start, rank_stop = n_minus, n_plus
        records[f"cycle_{cycle}"] = {
            "window": window,
            "pre_time_index": minus,
            "post_time_index": plus,
            "pre_time": float(dataset.time[minus]),
            "post_time": float(dataset.time[plus]),
            "active_fraction_pre": float(active_fraction[minus]),
            "active_fraction_post": float(active_fraction[plus]),
            "n_minus": n_minus,
            "n_plus": n_plus,
            "critical_rank_one_based": critical_rank,
            "frontier_rank_start_one_based": n_minus + 1,
            "frontier_rank_stop_one_based": n_plus,
        }
        for time_index, pool_name, seed in ((minus, before_name, seed_pair[0]), (plus, after_name, seed_pair[1])):
            order = _stable_descending_order(logits[time_index], roi_cells)
            chosen = roi_cells[order[rank_start:rank_stop]]
            if chosen.size == 0:
                raise ValueError(f"LF6 empty frontier pool: {pool_name}")
            complement = np.setdiff1d(roi_cells, chosen, assume_unique=True)
            if complement.size < chosen.size:
                raise ValueError(f"LF6 uniform complement too small: {pool_name}")
            rng = np.random.default_rng(int(seed))
            control = np.sort(rng.choice(complement, size=chosen.size, replace=False).astype(np.int64))
            frontier[pool_name] = chosen.astype(np.int64, copy=False)
            uniform[pool_name] = control
            records["cycle_1" if cycle == 1 else "cycle_2"].setdefault("pools", {})[pool_name] = {
                "time_index": time_index,
                "time": float(dataset.time[time_index]),
                "count": int(chosen.size),
                "frontier_cells": chosen.tolist(),
                "uniform_cells": control.tolist(),
                "uniform_seed": int(seed),
            }
    return {"q":Q,"roi_cell_count":count,"critical_rank_one_based":critical_rank,"cycles":records,"frontier":frontier,"uniform":uniform}


def _endpoint_arrays(dataset: Any, geometry: Mapping[str, Any], role: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    groups = geometry[role]
    coordinates: list[np.ndarray] = []; targets: list[np.ndarray] = []; offsets = [0]
    for pool_name in FRONTIER_POOL_NAMES:
        cycle = 1 if pool_name.startswith("C1") else 2
        time_index = int(geometry["cycles"][f"cycle_{cycle}"]["pools"][pool_name]["time_index"])
        cells = np.asarray(groups[pool_name], dtype=np.int64)
        node = time_index * dataset.cell_count + cells
        coordinates.append(np.asarray(dataset.coordinates[node], dtype=np.float64))
        targets.append(np.asarray(dataset.targets[node], dtype=np.float64))
        offsets.append(offsets[-1] + int(cells.size))
    return np.ascontiguousarray(np.concatenate(coordinates)), np.ascontiguousarray(np.concatenate(targets)), np.asarray(offsets, dtype=np.int64)


def _materialize_arrays(dataset: Any, *, model: torch.nn.Module, physics: Any) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
    arrays: dict[str, np.ndarray] = {}
    base_stream = BaseDevelopmentStream(dataset); band_stream = BandStream(InterfaceBandDataset(dataset))
    base_coordinates: list[np.ndarray] = []; base_targets: list[np.ndarray] = []; base_hashes: list[str] = []
    spatial_coordinates: list[np.ndarray] = []; spatial_targets: list[np.ndarray] = []; spatial_hashes: list[str] = []
    for step in range(1, 401):
        base = base_stream.draw(step); spatial = band_stream.draw(step)
        base_coordinates.append(base.coordinates.numpy()); base_targets.append(base.targets.numpy()); base_hashes.append(base.batch_sha256)
        spatial_coordinates.append(spatial.coordinates.numpy()); spatial_targets.append(spatial.targets.numpy()); spatial_hashes.append(spatial.batch_sha256)
    arrays["base_coordinates"] = np.ascontiguousarray(np.stack(base_coordinates).astype(np.float64, copy=False))
    arrays["base_targets"] = np.ascontiguousarray(np.stack(base_targets).astype(np.float64, copy=False))
    arrays["base_batch_sha256"] = np.asarray(base_hashes, dtype="S64")
    arrays["spatial_coordinates"] = np.ascontiguousarray(np.stack(spatial_coordinates).astype(np.float64, copy=False))
    arrays["spatial_targets"] = np.ascontiguousarray(np.stack(spatial_targets).astype(np.float64, copy=False))
    arrays["spatial_batch_sha256"] = np.asarray(spatial_hashes, dtype="S64")
    geometry = event_frontier_geometry(dataset)
    for role, prefix in (("frontier", "frontier"), ("uniform", "uniform")):
        coordinates, targets, offsets = _endpoint_arrays(dataset, geometry, role)
        arrays[f"{prefix}_coordinates"] = coordinates; arrays[f"{prefix}_targets"] = targets; arrays[f"{prefix}_offsets"] = offsets
    physics_stream = LF0PhysicsBatchStream(physics=physics, interior_points=512, boundary_points=128, initial_points=128, refresh_updates=250, seed=17)
    p0: dict[str, list[Any]] = {name: [] for name in ("interior","left","right","bottom","top","initial","active_windows","refreshed","interior_sha256","boundary_sha256","initial_sha256","batch_sha256")}
    for step in range(1, 1201):
        batch = physics_stream.draw(model, step, dtype=torch.float64, device=torch.device("cpu"))
        p0["interior"].append(batch.interior.numpy())
        for name in ("left","right","bottom","top"): p0[name].append(batch.boundary[name].numpy())
        p0["initial"].append(batch.initial.numpy()); p0["active_windows"].append(batch.active_windows); p0["refreshed"].append(batch.refreshed)
        for name in ("interior_sha256","boundary_sha256","initial_sha256","batch_sha256"): p0[name].append(getattr(batch,name))
    for name in ("interior","left","right","bottom","top","initial"): arrays[f"p0_{name}"] = np.ascontiguousarray(np.stack(p0[name]).astype(np.float64,copy=False))
    arrays["p0_active_windows"] = np.asarray(p0["active_windows"],dtype=np.int16); arrays["p0_refreshed"] = np.asarray(p0["refreshed"],dtype=np.bool_)
    for name in ("interior_sha256","boundary_sha256","initial_sha256","batch_sha256"): arrays[f"p0_{name}"] = np.asarray(p0[name],dtype="S64")
    fixed_sampler = PhkCollocationSampler(physics=physics,seed=17301)
    arrays["fixed_interior"] = fixed_sampler.select_interior(model,count=512,active_windows=4,physics_aware=False,dtype=torch.float64,device=torch.device("cpu")).detach().numpy()
    fixed_boundary = fixed_sampler.boundary(32,active_windows=4,dtype=torch.float64,device=torch.device("cpu"))
    for name in ("left","right","bottom","top"): arrays[f"fixed_{name}"] = fixed_boundary[name].detach().numpy()
    arrays["fixed_initial"] = fixed_sampler.initial(128,dtype=torch.float64,device=torch.device("cpu")).detach().numpy()
    if set(arrays) != set(LEDGER_ARRAY_NAMES):
        raise AssertionError("LF6 materializer array key mismatch")
    streams = {
        "base_400_sha256": base_stream.window_sha256,
        "base_rolling_1600_sha256": base_stream.rolling_1600_sha256,
        "spatial_400_sha256": band_stream.rolling_sha256,
        "P0_physics_1200_sha256": physics_stream.rolling_sha256,
    }
    fixed_digest=hashlib.sha256(b"PHK_V23_LF2_FIXED_REFERENCE_BLIND_FULL_W1_W4")
    for name in ("interior","left","right","bottom","top","initial"):
        array=np.ascontiguousarray(arrays[f"fixed_{name}"],dtype=np.float64); fixed_digest.update(str(tuple(array.shape)).encode("ascii")); fixed_digest.update(array.tobytes(order="C"))
    streams["fixed_blind_pool_sha256"]=fixed_digest.hexdigest().upper()
    return arrays,{"geometry":geometry,"streams":streams}


def materialize_ledger(*, output_directory: Path) -> dict[str, Any]:
    contracts=load_contracts(require_ledger_freeze=False); data=contracts["data"]
    medium=_verify_binding(data["training_source"],label="medium"); initial=_verify_binding(data["initial_checkpoint"],label="LF3-T0 checkpoint")
    config=build_training_config("cpu"); physics,_,_=load_case_physics(config.case_control); dataset=load_medium_dataset(medium,physics=physics,contracts=contracts)
    if dataset.partition_sha256 != data["target_measure"]["partition_sha256"]: raise ValueError("LF6 partition drift")
    model,_=load_lf3_t0_model(initial,physics=physics,config=config,device=torch.device("cpu"),expected_sha256=data["initial_checkpoint"]["sha256"])
    arrays,details=_materialize_arrays(dataset,model=model,physics=physics)
    streams=details["streams"]
    if streams["base_400_sha256"] != data["base_stream_source"]["rolling_sha256"] or streams["spatial_400_sha256"] != data["spatial_stream_source"]["rolling_sha256"] or streams["P0_physics_1200_sha256"] != data["materialized_ledger"]["P0_physics_1200_sha256"] or streams["fixed_blind_pool_sha256"] != data["materialized_ledger"]["fixed_blind_pool_sha256"]:
        raise ValueError("LF6 inherited stream materialization drift")
    output=Path(output_directory).resolve(); output.mkdir(parents=True,exist_ok=True); ledger_path=output/"materialized_ledger.npz"; manifest_path=output/"materialized_ledger_manifest.json"
    if ledger_path.exists() or manifest_path.exists(): raise FileExistsError("LF6 CPU-F ledger already exists")
    np.savez_compressed(ledger_path,**arrays)
    array_records={name:{"shape":list(value.shape),"dtype":value.dtype.str,"sha256":array_sha256(name,value)} for name,value in arrays.items()}
    semantic=semantic_ledger_sha256({name:record["sha256"] for name,record in array_records.items()})
    frontier_semantic=semantic_ledger_sha256({name:array_records[name]["sha256"] for name in ("frontier_coordinates","frontier_targets","frontier_offsets")})
    uniform_semantic=semantic_ledger_sha256({name:array_records[name]["sha256"] for name in ("uniform_coordinates","uniform_targets","uniform_offsets")})
    geometry=details["geometry"]
    compact_geometry={key:value for key,value in geometry.items() if key not in ("frontier","uniform")}
    manifest={"schema_id":"phk-v23-lf6-materialized-ledger-manifest-v1","task_id":TASK_ID,"created_at_utc":datetime.now(timezone.utc).isoformat(),"ledger":{"path":ledger_path.relative_to(ROOT).as_posix(),"sha256":_sha256_path(ledger_path),"size_bytes":ledger_path.stat().st_size},"semantic_sha256":semantic,"arrays":array_records,"streams":streams,"frontier_endpoint_sha256":frontier_semantic,"uniform_endpoint_sha256":uniform_semantic,"event_frontier_geometry":compact_geometry,"runtime_sampling_permitted":False}
    _write_json_exclusive(manifest_path,manifest)
    return {"ledger_path":ledger_path,"ledger_sha256":_sha256_path(ledger_path),"ledger_size_bytes":ledger_path.stat().st_size,"manifest_path":manifest_path,"manifest_sha256":_sha256_path(manifest_path),"semantic_sha256":semantic,"frontier_endpoint_sha256":frontier_semantic,"uniform_endpoint_sha256":uniform_semantic,"streams":streams,"event_frontier_geometry":compact_geometry,"arrays":array_records}


def _validate_dev_m_checkpoint(path: Path, *, data: Mapping[str,Any], initial_sha256: str) -> dict[str,Any]:
    payload=torch.load(path,map_location="cpu",weights_only=False); metadata=payload.get("lf4",{})
    checks={
        "schema":payload.get("schema_id")=="phk-v22r-checkpoint-v1-1",
        "task":metadata.get("task_id")==LF4_TASK_ID,
        "role":metadata.get("role")==LF4_ARM_M,
        "update":metadata.get("optimizer_update")==400,
        "parent":metadata.get("parent_checkpoint_sha256")==initial_sha256,
        "source_identity":metadata.get("source_identity")==LF4_SOURCE_IDENTITY,
        "contracts":metadata.get("contracts")==lf4_contract_identity(),
        "medium_labels":metadata.get("medium_labels_used") is True,
        "physics_unused":metadata.get("physics_residual_used") is False,
        "stress_unread":metadata.get("stress_read") is False,
    }
    return {"passed":all(checks.values()),"checks":checks}


def compute_cpu_payload(*, ledger_path: Path, ledger_manifest_path: Path, require_ledger_freeze: bool=True) -> dict[str,Any]:
    contracts=load_contracts(require_ledger_freeze=require_ledger_freeze); data=contracts["data"]
    medium=_verify_binding(data["training_source"],label="medium"); lf1=_verify_binding(data["lf1_b0_identity"],label="LF1-B0"); initial=_verify_binding(data["initial_checkpoint"],label="LF3-T0"); dev_m=_verify_binding(data["LF4_DEV_M"],label="LF4 DEV-M")
    prediction=initial.parent/"prediction-t0-step-1200.npz"
    if not prediction.is_file() or _sha256_path(prediction)!=data["initial_checkpoint"]["prediction_sha256"]: raise ValueError("LF6 LF3 prediction drift")
    summary=_verify_binding(data["LF4_raw"]["summary"],label="LF4 summary"); telemetry=_verify_binding(data["LF4_raw"]["telemetry"],label="LF4 telemetry"); compact=_verify_binding(data["LF4_compact_evidence"]["cpu"],label="LF4 CPU compact")
    manifest=_read_json(ledger_manifest_path)
    if manifest.get("schema_id")!="phk-v23-lf6-materialized-ledger-manifest-v1" or manifest.get("task_id")!=TASK_ID: raise ValueError("LF6 ledger manifest identity drift")
    if not Path(ledger_path).is_file() or _sha256_path(ledger_path)!=manifest["ledger"]["sha256"]: raise ValueError("LF6 ledger file drift")
    if require_ledger_freeze:
        binding=data["materialized_ledger"]
        if _sha256_path(ledger_path)!=binding["file_sha256"] or _sha256_path(ledger_manifest_path)!=binding["manifest_sha256"] or manifest["semantic_sha256"]!=binding["semantic_sha256"]: raise ValueError("LF6 frozen ledger binding mismatch")
    with np.load(ledger_path,allow_pickle=False) as archive: arrays={name:np.asarray(archive[name]) for name in archive.files}
    if set(arrays)!=set(LEDGER_ARRAY_NAMES): raise ValueError("LF6 ledger array set drift")
    hashes={name:array_sha256(name,value) for name,value in arrays.items()}
    if any(hashes[name]!=manifest["arrays"][name]["sha256"] for name in arrays) or semantic_ledger_sha256(hashes)!=manifest["semantic_sha256"]: raise ValueError("LF6 ledger semantic drift")
    config=build_training_config("cpu"); physics,_,_=load_case_physics(config.case_control); dataset=load_medium_dataset(medium,physics=physics,contracts=contracts)
    model,_=load_lf3_t0_model(initial,physics=physics,config=config,device=torch.device("cpu"),expected_sha256=data["initial_checkpoint"]["sha256"])
    lf3_audit=full_medium_audit(model,dataset,device=torch.device("cpu"))
    dev_m_identity=_validate_dev_m_checkpoint(dev_m,data=data,initial_sha256=data["initial_checkpoint"]["sha256"])
    dev_m_model,_=load_lf3_t0_model(initial,physics=physics,config=config,device=torch.device("cpu"),expected_sha256=data["initial_checkpoint"]["sha256"]); dev_m_payload=torch.load(dev_m,map_location="cpu",weights_only=False); dev_m_model.load_state_dict(dev_m_payload["model_state_dict"],strict=True); dev_m_model.eval()
    dev_m_audit=full_medium_audit(dev_m_model,dataset,device=torch.device("cpu"))
    compact_payload=_read_json(compact); lf1_b0=compact_payload.get("lf1_b0_full_medium_audit")
    if not isinstance(lf1_b0,Mapping): raise ValueError("LF6 lacks inherited LF1-B0 audit")
    endpoint=EndpointBatch(torch.as_tensor(arrays["frontier_coordinates"],dtype=torch.float64),torch.as_tensor(arrays["frontier_targets"],dtype=torch.float64),tuple(int(v) for v in arrays["frontier_offsets"]),DEV_R)
    model.zero_grad(set_to_none=True); loss=endpoint_logit_loss(model,endpoint,physics=physics,device=torch.device("cpu"))["loss"]; loss.backward()
    gradients=[parameter.grad for parameter in tuple(model.encoders["phase"].parameters())+tuple(model.heads["phase"].parameters()) if parameter.grad is not None]
    backward_ok=bool(gradients and all(torch.isfinite(value).all() for value in gradients) and any(float(torch.linalg.vector_norm(value))>0.0 for value in gradients))
    streams=manifest["streams"]
    checks={"input_hashes":True,"partition":dataset.partition_sha256==data["target_measure"]["partition_sha256"],"geometry":all(len(manifest["event_frontier_geometry"]["cycles"][f"cycle_{c}"]["pools"][name]["frontier_cells"])>0 for c,names in ((1,FRONTIER_POOL_NAMES[:2]),(2,FRONTIER_POOL_NAMES[2:])) for name in names),"ledger_arrays":True,"base_hash":streams["base_400_sha256"]==data["base_stream_source"]["rolling_sha256"],"spatial_hash":streams["spatial_400_sha256"]==data["spatial_stream_source"]["rolling_sha256"],"physics_hash":streams["P0_physics_1200_sha256"]==data["materialized_ledger"]["P0_physics_1200_sha256"],"fixed_pool_hash":streams["fixed_blind_pool_sha256"]==data["materialized_ledger"]["fixed_blind_pool_sha256"],"dev_m_identity":dev_m_identity["passed"],"finite_nonzero_phase_backward":backward_ok,"zero_optimizer_updates":True,"fine_extra_stress_unread":True}
    return {"schema_id":"phk-v23-lf6-cpu-qualification-v1","task_id":TASK_ID,"created_at_utc":datetime.now(timezone.utc).isoformat(),"status":"LF6_CPU_F_QUALIFICATION_PASS" if all(checks.values()) else "LF6_EVENT_FRONTIER_GEOMETRY_BLOCKED","gpu_execution_authorized_by_cpu_gate":bool(all(checks.values())),"scientific_model_optimizer_updates":0,"gpu_used":False,"contracts":contract_identity(),"checks":checks,"partition_sha256":dataset.partition_sha256,"event_frontier_geometry":manifest["event_frontier_geometry"],"ledger":{"path":Path(ledger_path).relative_to(ROOT).as_posix(),"sha256":_sha256_path(ledger_path),"size_bytes":Path(ledger_path).stat().st_size,"manifest_path":Path(ledger_manifest_path).relative_to(ROOT).as_posix(),"manifest_sha256":_sha256_path(ledger_manifest_path),"semantic_sha256":manifest["semantic_sha256"],"streams":streams,"arrays":manifest["arrays"]},"lf3_t0_full_medium_audit":lf3_audit,"dev_m_full_medium_audit":dev_m_audit,"dev_m_input_valid":dev_m_identity["passed"],"dev_m_state_sha256":{"potential":_field_state_sha256(dev_m_model,"potential"),"temperature":_field_state_sha256(dev_m_model,"temperature"),"phase":_field_state_sha256(dev_m_model,"phase")},"lf1_b0_full_medium_audit":lf1_b0,"input_bindings":{"medium":{"path":str(medium),"sha256":_sha256_path(medium)},"lf1_b0":{"path":str(lf1),"sha256":_sha256_path(lf1)},"lf3_t0":{"path":str(initial),"sha256":_sha256_path(initial)},"lf3_prediction":{"path":str(prediction),"sha256":_sha256_path(prediction)},"lf4_dev_m":{"path":str(dev_m),"sha256":_sha256_path(dev_m)},"lf4_summary":{"path":str(summary),"sha256":_sha256_path(summary)},"lf4_telemetry":{"path":str(telemetry),"sha256":_sha256_path(telemetry)}},"reference_boundary":{"fine_extra_read":False,"stress_read":False,"frozen_evaluator_read":False}}


def qualify_cpu(*,artifact_path:Path,manifest_path:Path,raw_output_directory:Path)->dict[str,Any]:
    raw=Path(raw_output_directory).resolve(); ledger=raw/"materialized_ledger.npz"; ledger_manifest=raw/"materialized_ledger_manifest.json"
    payload=compute_cpu_payload(ledger_path=ledger,ledger_manifest_path=ledger_manifest,require_ledger_freeze=True)
    if payload["status"]!="LF6_CPU_F_QUALIFICATION_PASS": raise RuntimeError(payload["status"])
    raw_report=raw/"qualification.json"
    if not raw_report.exists(): _write_json_exclusive(raw_report,payload)
    _write_json_exclusive(Path(artifact_path),payload)
    run_id="20260906T065434Z-phk-v23-lf6-cpu-qualification"
    manifest={
        "schema_version":"run-manifest-v1",
        "run_id":run_id,
        "experiment_group_id":"PHK_V23_LF6",
        "tier":"qualification",
        "scientific_role":"cpu_only_event_frontier_geometry_ledger_and_fallback_qualification",
        "gate":"PHK_V23_LF6_CPU_F",
        "started_at":"2026-09-06T06:54:34+00:00",
        "ended_at":payload["created_at_utc"],
        "command":[".venv/Scripts/python.exe","-m","pinn_pcm_sci.phk_v23_lf6_qualification"],
        "execution_status":"COMPLETE",
        "numerical_validity":"VALID_CPU_FP64_HASH_BOUND_FRONTIER_UNIFORM_BASE_SPATIAL_PHYSICS_FIXED_POOL_AND_DEV_M_FALLBACK_NO_GPU_OR_LOCAL_EVALUATOR",
        "gate_outcome":payload["status"],
        "route_disposition":"RUN_MATCHED_DEV_U_AND_DEV_R_THEN_SAFETY_GATED_CONDITIONAL_P0",
        "evidence_identity":"ZERO_UPDATE_HASH_BOUND_EVENT_FRONTIER_GEOMETRY_AND_FULL_MATERIALIZED_STREAM_QUALIFICATION",
        "claim_status":"LF6_EVENT_FRONTIER_GEOMETRY_AND_MATERIALIZED_STREAMS_QUALIFIED_GPU_MECHANISM_UNTESTED",
        "code_identity":{"base_commit":"9d3c22674dc6279846fa341433d36f603a0854f1","workspace_scope":"LF6_EXACT_ALLOWLIST_UNRELATED_DIRTY_PRESERVED"},
        "environment":{"device":"CPU","dtype":"FLOAT64","cloud_connection_opened":False,"stress_status":"TWO_STRESS_REFERENCES_SEALED_UNREAD"},
        "physical_contract_id":"PHK_V21_FIXED_DISCRETIZATION_FULL_NOMINAL",
        "split_id":"MEDIUM_METHOD_INPUT_LF3_T0_INITIALIZATION_DEV_M_FALLBACK_FINE_EXTRA_LOCAL_ONLY_STRESS_SEALED",
        "method_id":"phk-v23-lf6-event-frontier-rank-band-v1",
        "case_id":"PHK_V21_NOMINAL_MEDIUM_EVENT_FRONTIER_QUALIFICATION",
        "seed":17,
        "planned_budget":{"gpu_trajectories":0,"optimizer_updates":0},
        "actual_budget":{"gpu_trajectories":0,"optimizer_updates":0,"gpu_used":False},
        "checkpoint":{"lf3_t0_source_sha256":payload["input_bindings"]["lf3_t0"]["sha256"],"lf4_dev_m_source_sha256":payload["input_bindings"]["lf4_dev_m"]["sha256"],"loaded_read_only":True},
        "evaluator_id":"NOT_READ_DURING_CPU_F",
        "artifacts":{"compact_qualification":f"artifacts/{Path(artifact_path).name}#sha256={_sha256_path(Path(artifact_path))}","raw_report":f"{raw_report.relative_to(ROOT).as_posix()}#sha256={_sha256_path(raw_report)}","materialized_ledger":f"{payload['ledger']['path']}#sha256={payload['ledger']['sha256']}"},
        "failure_class":None,
        "replay_of":None,
        "supersedes":None,
    }
    _write_json_exclusive(Path(manifest_path),manifest); return payload


def _parser()->argparse.ArgumentParser:
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument("--raw-output-directory",type=Path,required=True); parser.add_argument("--materialize-only",action="store_true"); parser.add_argument("--artifact",type=Path); parser.add_argument("--manifest",type=Path); return parser


def main(argv:Sequence[str]|None=None)->int:
    args=_parser().parse_args(argv)
    if args.materialize_only:
        result=materialize_ledger(output_directory=args.raw_output_directory); print(json.dumps({key:(str(value) if isinstance(value,Path) else value) for key,value in result.items() if key not in {"arrays","event_frontier_geometry"}},sort_keys=True)); return 0
    if args.artifact is None or args.manifest is None: raise SystemExit("--artifact and --manifest are required unless --materialize-only")
    payload=qualify_cpu(artifact_path=args.artifact,manifest_path=args.manifest,raw_output_directory=args.raw_output_directory); print(json.dumps({"status":payload["status"],"ledger_sha256":payload["ledger"]["sha256"]},sort_keys=True)); return 0


if __name__=="__main__": raise SystemExit(main())


__all__=["compute_cpu_payload","event_frontier_geometry","materialize_ledger","qualify_cpu"]
