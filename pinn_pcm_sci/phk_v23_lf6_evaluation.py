"""Post-shutdown nominal evaluation and terminal adjudication for LF6."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import tempfile
from typing import Any, Mapping, Sequence

import torch

from .phk_benchmark import PhkControl
from .phk_v22r_evaluator import evaluate_prediction
from .phk_v22r_prediction import _load_model, write_prediction_carrier
from .phk_v22r_training import ROOT
from .phk_v23_lf0 import PhysicsBatch, _physics_objective, _read_json, _sha256_path
from .phk_v23_lf0_evaluation import _clone_batch, _prediction_potential_guard, _sanitize_nonfinite, safe_error_ratio, write_strict_json
from .phk_v23_lf1_evaluation import B0_ROLE as LF1_B0_ROLE, B_FINAL_ROLE as LF1_B_FINAL_ROLE, LF_ONLY_ROLE, _competent, _evaluation_valid, compare_b_to_comparator
from .phk_v23_lf2_evaluation import _component_floors, _inherited_prediction_paths, _safe_bound_path
from .phk_v23_lf3_evaluation import LF2_M0_ROLE, LF3_T0_ROLE
from .phk_v23_lf6 import DEV_M, DEV_R, DEV_U, DEV_ORDER, MaterializedLedger, TASK_ID, load_contracts, read_cpu_qualification


SELECTED_ROLE = "LF6_SELECTED_DEVELOPMENT_CARRIER"
P0_ROLE = "LF6_P0_FULL_PHYSICS"
DEV_U_ROLE = "LF6_DEV_U"
DEV_R_ROLE = "LF6_DEV_R"
GPU_LIFECYCLE_SHUTDOWN_VERIFIED = "SHUTDOWN_VERIFIED"


def _artifact_path(root: Path, summary: Mapping[str, Any], key: str, *, required: bool=True) -> Path | None:
    record=summary.get("artifacts",{}).get(key)
    if record is None and not required: return None
    if not isinstance(record,Mapping): raise ValueError(f"LF6 recovered run lacks artifact: {key}")
    relative=Path(str(record.get("path","")))
    if relative.is_absolute() or ".." in relative.parts: raise PermissionError(f"LF6 artifact escaped run root: {key}")
    path=(root/relative).resolve()
    try: path.relative_to(root.resolve())
    except ValueError as exc: raise PermissionError(f"LF6 artifact escaped run root: {key}") from exc
    if not path.is_file() or path.stat().st_size!=int(record.get("size_bytes",-1)) or _sha256_path(path)!=str(record.get("sha256","")).upper(): raise ValueError(f"LF6 recovered artifact drift: {key}")
    return path


def _run_files(path: Path, *, contracts: Mapping[str,Any]) -> dict[str,Any]:
    root=Path(path).resolve(); summary_path=root/"run_summary.json"; summary=_read_json(summary_path)
    if summary.get("schema_id")!="phk-v23-lf6-reference-blind-run-summary-v1" or summary.get("task_id")!=TASK_ID or summary.get("prediction_reference_free") is not True or summary.get("fine_extra_lf_only_evaluator_stress_read") is not False: raise ValueError("LF6 recovered run identity drift")
    result={"root":root,"summary":summary_path,"summary_payload":summary}
    for arm,role in ((DEV_U,DEV_U_ROLE),(DEV_R,DEV_R_ROLE)):
        result[f"prediction_{role}"]=_artifact_path(root,summary,f"{arm}_prediction")
        result[f"checkpoint_{role}"]=_artifact_path(root,summary,f"{arm}_checkpoint")
    result["prediction_p0"]=_artifact_path(root,summary,"P0_prediction",required=False); result["checkpoint_p0"]=_artifact_path(root,summary,"P0_checkpoint",required=False)
    selected=summary.get("selected_role")
    if selected==DEV_U:
        result["checkpoint_selected"]=result[f"checkpoint_{DEV_U_ROLE}"]; result["prediction_selected"]=result[f"prediction_{DEV_U_ROLE}"]
    elif selected==DEV_R:
        result["checkpoint_selected"]=result[f"checkpoint_{DEV_R_ROLE}"]; result["prediction_selected"]=result[f"prediction_{DEV_R_ROLE}"]
    elif selected==DEV_M:
        result["checkpoint_selected"]=_safe_bound_path(contracts["data"]["LF4_DEV_M"],label="LF6 exact DEV-M fallback"); result["prediction_selected"]=None
    elif selected is None:
        result["checkpoint_selected"]=None; result["prediction_selected"]=None
    else: raise ValueError("LF6 selected role drift")
    return result


def _fixed_physics(checkpoints: Mapping[str,Path], *, contracts: Mapping[str,Any], qualification: Mapping[str,Any]) -> dict[str,Any]:
    if set(checkpoints) not in ({SELECTED_ROLE},{SELECTED_ROLE,P0_ROLE}): raise ValueError("LF6 fixed-physics checkpoint roles drift")
    ledger=MaterializedLedger(ROOT/contracts["data"]["materialized_ledger"]["path"],contracts=contracts,qualification=qualification); arrays=ledger.arrays; device=torch.device("cpu")
    tensor=lambda name:torch.as_tensor(arrays[f"fixed_{name}"],dtype=torch.float64,device=device)
    batch=PhysicsBatch(interior=tensor("interior"),boundary={name:tensor(name) for name in ("left","right","bottom","top")},initial=tensor("initial"),active_windows=4,refreshed=True,interior_sha256="MATERIALIZED_FIXED_INTERIOR",boundary_sha256="MATERIALIZED_FIXED_BOUNDARY",initial_sha256="MATERIALIZED_FIXED_INITIAL",batch_sha256=contracts["data"]["materialized_ledger"]["fixed_blind_pool_sha256"])
    values={}; components={}
    for role,path in checkpoints.items():
        model,config,_=_load_model(path,device=device)
        with torch.enable_grad(): _,scalars=_physics_objective(model,_clone_batch(batch),config)
        values[role]=float(scalars["physics_total"]); components[role]=scalars
    ratio=None; defined=False
    if P0_ROLE in values: ratio,defined=safe_error_ratio(values[P0_ROLE],values[SELECTED_ROLE])
    return {"fixed_pool_sha256":batch.batch_sha256,"source":"CPU_F_PREMATERIALIZED_LEDGER_NO_RUNTIME_SAMPLING","values":values,"components":components,"P0_to_selected":{"ratio":ratio,"defined":defined,"maximum":0.5,"passed":bool(defined and ratio is not None and ratio<=0.5)},"reference_or_low_fidelity_values_read":False,"device":"CPU","dtype":"FLOAT64"}


def _terminal(outcome: str, *, contract: Mapping[str,Any], details: Mapping[str,Any]|None=None) -> dict[str,Any]:
    mapping=contract["machine_outcomes_and_unique_next"]
    if outcome not in mapping: raise ValueError(f"unmapped LF6 outcome: {outcome}")
    return {"status":"TERMINAL","outcome":outcome,"candidate":P0_ROLE if outcome=="LF6_PROVISIONAL_SINGLE_SEED_SIGNAL" else None,"unique_next":mapping[outcome],"next_research_execution_authorized":False,**dict(details or {})}


def adjudicate(*, contract: Mapping[str,Any], run: Mapping[str,Any], evaluations: Mapping[str,Mapping[str,Any]], potential: Mapping[str,Mapping[str,Any]], comparisons: Mapping[str,Mapping[str,Any]], physics: Mapping[str,Any]) -> dict[str,Any]:
    selected=run.get("selected_role")
    if selected is None:
        return _terminal("LF6_NO_VALID_SAFETY_CARRIER",contract=contract,details={"P0":"NOT_RUN","mechanism_outcome":run.get("mechanism_outcome")})
    p0=run.get("P0")
    if p0 is None or P0_ROLE not in evaluations:
        return _terminal("LF6_P0_NUMERICAL_OR_IDENTITY_INVALID",contract=contract,details={"selected_role":selected,"reason":"MANDATORY_P0_MISSING_AFTER_SAFETY_SELECTION"})
    mandatory={LF_ONLY_ROLE,LF1_B0_ROLE,LF1_B_FINAL_ROLE,LF2_M0_ROLE,LF3_T0_ROLE,SELECTED_ROLE,P0_ROLE}
    if any(role not in evaluations or not _evaluation_valid(evaluations[role]) for role in mandatory) or any(role not in potential or potential[role].get("passed") is not True for role in mandatory):
        return _terminal("LF6_P0_NUMERICAL_OR_IDENTITY_INVALID",contract=contract,details={"selected_role":selected})
    if p0.get("numerical_valid") is not True:
        return _terminal("LF6_P0_NUMERICAL_OR_IDENTITY_INVALID",contract=contract,details={"selected_role":selected})
    preservation=p0.get("preservation_gate",{})
    if preservation.get("passed") is not True:
        return _terminal("LF6_P0_PRESERVATION_FAILED",contract=contract,details={"selected_role":selected,"P0_preservation":preservation})
    if p0.get("strict_gate",{}).get("passed") is not True:
        return _terminal("LF6_P0_FINAL_STRICT_NOT_REACHED",contract=contract,details={"selected_role":selected,"P0_preservation":preservation})
    within=comparisons["P0_vs_selected"]; fixed=physics["P0_to_selected"]
    level2=bool(_competent(evaluations[SELECTED_ROLE]) and _competent(evaluations[P0_ROLE]) and within["phase_noninferiority_passed"] and within["preservation_passed"] and fixed.get("passed") is True)
    if not level2: return _terminal("LF6_NO_PINN_PARETO",contract=contract,details={"selected_role":selected,"P0_vs_selected":within,"fixed_physics_gate":fixed})
    direct=comparisons["P0_vs_LF_ONLY"]
    level3=bool(_competent(evaluations[LF_ONLY_ROLE]) and _competent(evaluations[P0_ROLE]) and direct["phase_noninferiority_passed"] and direct["preservation_passed"] and potential[LF_ONLY_ROLE]["passed"] and potential[P0_ROLE]["passed"])
    if not level3: return _terminal("LF6_SINGLE_SEED_PINN_PILOT_DIRECT_BASELINE_GAP",contract=contract,details={"selected_role":selected,"P0_vs_LF_ONLY":direct,"within_architecture_pareto":True})
    return _terminal("LF6_PROVISIONAL_SINGLE_SEED_SIGNAL",contract=contract,details={"selected_role":selected,"mechanism_outcome":run.get("mechanism_outcome"),"single_seed_only":True})


def evaluate_lf6_campaign(*,output_directory:Path,run_directory:Path,cpu_qualification_path:Path,gpu_lifecycle:str=GPU_LIFECYCLE_SHUTDOWN_VERIFIED)->dict[str,Any]:
    if gpu_lifecycle!=GPU_LIFECYCLE_SHUTDOWN_VERIFIED: raise PermissionError("LF6 local evaluation requires verified GPU shutdown")
    contracts=load_contracts(); qualification=read_cpu_qualification(cpu_qualification_path)
    for binding in contracts["data"]["local_evaluation_only"].values():
        if isinstance(binding,Mapping): _safe_bound_path(binding,label="LF6 local nominal reference")
    run_files=_run_files(run_directory,contracts=contracts); run=run_files["summary_payload"]
    lf3_decision=_read_json(ROOT/"configs/phk_v23/decision_contract_lf3_phase_latent_carrier.json"); lf3_data=_read_json(ROOT/"configs/phk_v23/data_contract_lf3_phase_latent_carrier.json")
    paths=_inherited_prediction_paths(lf3_decision); paths.pop("A_RANGE_PRESERVING_SCRATCH",None)
    paths[LF2_M0_ROLE]=_safe_bound_path(lf3_data["inherited_comparators"]["lf2_m0_prediction"],label="LF2-M0 prediction")
    paths[LF3_T0_ROLE]=ROOT/"outputs/runs/20260904T150300Z-phk-v23-lf3-phase-latent-97a5b74/prediction-t0-step-1200.npz"
    paths[DEV_U_ROLE]=run_files[f"prediction_{DEV_U_ROLE}"]; paths[DEV_R_ROLE]=run_files[f"prediction_{DEV_R_ROLE}"]
    temporary: tempfile.TemporaryDirectory[str] | None=None
    try:
        if run.get("selected_role")==DEV_M:
            temporary=tempfile.TemporaryDirectory(prefix="phk-v23-lf6-selected-"); selected_prediction=Path(temporary.name)/"selected-dev-m.npz"; write_prediction_carrier(checkpoint_path=run_files["checkpoint_selected"],output_path=selected_prediction,device_name="cpu"); paths[SELECTED_ROLE]=selected_prediction
        elif run_files["prediction_selected"] is not None: paths[SELECTED_ROLE]=run_files["prediction_selected"]
        if run_files["prediction_p0"] is not None: paths[P0_ROLE]=run_files["prediction_p0"]
        evaluations={role:evaluate_prediction(prediction_path=path,control=PhkControl.FULL) for role,path in paths.items()}
        potential={role:_prediction_potential_guard(path,absolute_tolerance=1.0e-6) for role,path in paths.items()}
        floors=_component_floors(lf3_decision); comparisons={}
        if P0_ROLE in evaluations: comparisons={"P0_vs_selected":compare_b_to_comparator(evaluations[P0_ROLE],evaluations[SELECTED_ROLE],component_floors=floors),"P0_vs_LF_ONLY":compare_b_to_comparator(evaluations[P0_ROLE],evaluations[LF_ONLY_ROLE],component_floors=floors)}
        checkpoints={SELECTED_ROLE:run_files["checkpoint_selected"]} if run_files["checkpoint_selected"] is not None else {}
        if run_files["checkpoint_p0"] is not None: checkpoints[P0_ROLE]=run_files["checkpoint_p0"]
        physics=_fixed_physics(checkpoints,contracts=contracts,qualification=qualification) if checkpoints else {"not_run":True}
        decision=adjudicate(contract=contracts["decision"],run=run,evaluations=evaluations,potential=potential,comparisons=comparisons,physics=physics)
        sanitized,replaced=_sanitize_nonfinite(evaluations)
        bindings={role:{"path":str(path) if not (temporary and str(path).startswith(temporary.name)) else "EPHEMERAL_FROM_HASH_BOUND_EXACT_DEV_M_CHECKPOINT","sha256":_sha256_path(path),"size_bytes":path.stat().st_size} for role,path in paths.items()}
        report={"schema_id":"phk-v23-lf6-local-adjudication-v1","task_id":TASK_ID,"status":"COMPLETE","case_control":"FULL","gpu_lifecycle":gpu_lifecycle,"run_status":run["status"],"selected_role":run.get("selected_role"),"mechanism_outcome":run.get("mechanism_outcome"),"roles_evaluated":list(paths),"prediction_bindings":bindings,"evaluations":sanitized,"evaluator_nonfinite_diagnostics_represented_as_json_null":replaced,"potential_maximum_principle":potential,"component_floors":floors,"comparisons":comparisons,"fixed_physics_objective":physics,"development_gates":{name:{"safety":run["development"][name]["safety_gate"],"strict":run["development"][name]["strict_gate"]} for name in DEV_ORDER},"P0_gate":run.get("P0"),"decision":decision,"fine_extra_use":"LOCAL_NOMINAL_ONLY_AFTER_SHUTDOWN","stress_status":"TWO_STRESS_REFERENCES_SEALED_UNREAD","claim_boundary":contracts["decision"]["claim_boundary"]}
    finally:
        if temporary is not None: temporary.cleanup()
    output=Path(output_directory).resolve(); output.mkdir(parents=True,exist_ok=True); path=output/"adjudication.json"
    if path.exists(): raise FileExistsError("LF6 local adjudication already exists")
    write_strict_json(path,report); return report


def _parser()->argparse.ArgumentParser:
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument("--output-directory",type=Path,required=True); parser.add_argument("--run-directory",type=Path,required=True); parser.add_argument("--cpu-qualification",type=Path,required=True); return parser


def main(argv:Sequence[str]|None=None)->int:
    args=_parser().parse_args(argv); report=evaluate_lf6_campaign(output_directory=args.output_directory,run_directory=args.run_directory,cpu_qualification_path=args.cpu_qualification); print(json.dumps({"outcome":report["decision"]["outcome"],"candidate":report["decision"]["candidate"]},sort_keys=True)); return 0


if __name__=="__main__": raise SystemExit(main())


__all__=["DEV_R_ROLE","DEV_U_ROLE","P0_ROLE","SELECTED_ROLE","adjudicate","evaluate_lf6_campaign"]
