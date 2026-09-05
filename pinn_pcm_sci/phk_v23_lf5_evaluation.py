"""Post-shutdown nominal evaluation and terminal adjudication for LF5."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from .phk_benchmark import PhkControl
from .phk_v22r_evaluator import evaluate_prediction
from .phk_v22r_training import ROOT
from .phk_v23_lf0 import _read_json, _sha256_path
from .phk_v23_lf0_evaluation import _prediction_potential_guard, _sanitize_nonfinite, write_strict_json
from .phk_v23_lf1_evaluation import B0_ROLE as LF1_B0_ROLE, B_FINAL_ROLE as LF1_B_FINAL_ROLE, LF_ONLY_ROLE, _competent, _evaluation_valid, compare_b_to_comparator
from .phk_v23_lf2_evaluation import LF2_FINAL_ROLE as _POOL_FINAL_ROLE, LF2_M0_ROLE as _POOL_M0_ROLE, _component_floors, _fixed_physics_values, _inherited_prediction_paths, _safe_bound_path
from .phk_v23_lf3_evaluation import LF2_M0_ROLE, LF3_T0_ROLE
from .phk_v23_lf5 import DEV_T_ROLE, P0_ROLE, TASK_ID, load_contracts, read_cpu_qualification


GPU_LIFECYCLE_SHUTDOWN_VERIFIED = "SHUTDOWN_VERIFIED"


def _terminal(outcome: str, *, contract: Mapping[str, Any], details: Mapping[str, Any] | None=None) -> dict[str, Any]:
    mapping=contract["machine_outcomes_and_unique_next"]
    if outcome not in mapping: raise ValueError(f"unmapped LF5 outcome: {outcome}")
    return {"status":"TERMINAL","outcome":outcome,"candidate":P0_ROLE if outcome=="LF5_PROVISIONAL_SINGLE_SEED_SIGNAL" else None,"unique_next":mapping[outcome],"next_research_execution_authorized":False,**dict(details or {})}


def terminal_from_cpu(cpu: Mapping[str, Any], *, contract: Mapping[str, Any]) -> dict[str, Any]:
    status=cpu.get("status")
    if status not in {"LF5_TEMPORAL_GEOMETRY_BLOCKED","LF5_TZL_ALIGNMENT_NOT_SUPPORTED_CPU"}: raise ValueError("LF5 CPU payload is not terminal")
    return _terminal(str(status),contract=contract,details={"DEV_T":"NOT_RUN","P0":"NOT_RUN","optimizer_updates":0,"gpu_used":False})


def _artifact_path(root: Path, summary: Mapping[str, Any], key: str, *, required: bool=True) -> Path | None:
    record=summary.get("artifacts",{}).get(key)
    if record is None and not required: return None
    if not isinstance(record,Mapping): raise ValueError(f"LF5 recovered run lacks artifact: {key}")
    relative=Path(str(record.get("path","")))
    if relative.is_absolute() or ".." in relative.parts: raise PermissionError(f"LF5 artifact escaped run root: {key}")
    path=(root/relative).resolve(); path.relative_to(root.resolve())
    if not path.is_file() or path.stat().st_size!=int(record.get("size_bytes",-1)) or _sha256_path(path)!=str(record.get("sha256","")).upper(): raise ValueError(f"LF5 recovered artifact drift: {key}")
    return path


def _run_files(path: Path) -> dict[str, Any]:
    root=Path(path).resolve(); summary_path=root/"summary.json"; summary=json.loads(summary_path.read_text(encoding="utf-8"))
    if summary.get("schema_id")!="phk-v23-lf5-reference-blind-run-summary-v1" or summary.get("task_id")!=TASK_ID or summary.get("prediction_reference_free") is not True or summary.get("fine_extra_lf_only_evaluator_stress_read") is not False: raise ValueError("LF5 recovered run identity drift")
    if bool(summary.get("post_qualification_user_override")) != (summary.get("evidence_role") == "POST_QUALIFICATION_USER_OVERRIDE_EXPLORATORY"): raise ValueError("LF5 override evidence-role drift")
    return {"root":root,"summary":summary_path,"payload":summary,"prediction_dev":_artifact_path(root,summary,"prediction_dev_t"),"checkpoint_dev":_artifact_path(root,summary,"checkpoint_dev_t"),"prediction_p0":_artifact_path(root,summary,"prediction_p0",required=False),"checkpoint_p0":_artifact_path(root,summary,"checkpoint_p0",required=False)}


def _fixed_physics(checkpoints: Mapping[str, Path], *, contracts: Mapping[str, Any]) -> dict[str, Any]:
    legacy={_POOL_M0_ROLE:checkpoints[DEV_T_ROLE]}
    if P0_ROLE in checkpoints: legacy[_POOL_FINAL_ROLE]=checkpoints[P0_ROLE]
    pool_contract={"local_evaluation":{"fixed_reference_blind_physics_pool":{"seed":17301,"dtype":"FLOAT64","device":"CPU","active_windows":4,"interior_points":512,"boundary_points_total":128,"initial_points":128,"objective":"NORMALIZED_PDE_PLUS_5_TIMES_BOUNDARY_PLUS_INITIAL","sha256":contracts["data"]["fixed_blind_physics_pool_sha256"]}},"provisional_positive_gate":{"fixed_physics_objective_ratio_final_to_M0_maximum":0.5}}
    report=_fixed_physics_values(legacy,contract=pool_contract); role_map={_POOL_M0_ROLE:DEV_T_ROLE,_POOL_FINAL_ROLE:P0_ROLE}
    report["values"]={role_map[k]:v for k,v in report["values"].items()}; report["components"]={role_map[k]:v for k,v in report["components"].items()}
    if "final_to_M0" in report: report["P0_to_DEV_T"]=report.pop("final_to_M0")
    return report


def adjudicate(*, contract: Mapping[str, Any], run: Mapping[str, Any], evaluations: Mapping[str, Mapping[str, Any]], potential: Mapping[str, Mapping[str, Any]], comparisons: Mapping[str, Mapping[str, Any]], physics: Mapping[str, Any]) -> dict[str, Any]:
    dev=run["DEV_T"]
    if dev.get("numerical_valid") is not True: return _terminal("LF5_NUMERICAL_OR_IDENTITY_INVALID",contract=contract)
    if dev["carrier_gate"].get("passed") is not True: return _terminal("LF5_DEV_T_CARRIER_NOT_ESTABLISHED",contract=contract,details={"P0":"NOT_RUN","DEV_T_gate":dev["carrier_gate"]})
    p0=run.get("P0")
    if p0 is None: raise ValueError("LF5 DEV-T passed but P0 is absent")
    if p0["preservation_gate"].get("passed") is not True: return _terminal("LF5_P0_PRESERVATION_FAILED",contract=contract,details={"P0_gate":p0["preservation_gate"]})
    if p0["strict_gate"].get("passed") is not True: return _terminal("LF5_P0_STRICT_CARRIER_NOT_REACHED",contract=contract,details={"P0_gate":p0["strict_gate"]})
    mandatory={LF_ONLY_ROLE,LF1_B0_ROLE,LF1_B_FINAL_ROLE,LF2_M0_ROLE,LF3_T0_ROLE,DEV_T_ROLE,P0_ROLE}
    if any(not _evaluation_valid(evaluations[role]) for role in mandatory) or any(potential[role].get("passed") is not True for role in mandatory): return _terminal("LF5_NUMERICAL_OR_IDENTITY_INVALID",contract=contract)
    within=comparisons["P0_vs_DEV_T"]; ratio=physics["P0_to_DEV_T"]
    level2=bool(_competent(evaluations[DEV_T_ROLE]) and _competent(evaluations[P0_ROLE]) and within["phase_noninferiority_passed"] and within["preservation_passed"] and ratio.get("passed") is True)
    if not level2: return _terminal("LF5_NO_PINN_PARETO",contract=contract,details={"P0_vs_DEV_T":within,"fixed_physics_gate":ratio})
    direct=comparisons["P0_vs_LF_ONLY"]
    level3=bool(_competent(evaluations[LF_ONLY_ROLE]) and direct["phase_noninferiority_passed"] and direct["preservation_passed"])
    if not level3: return _terminal("LF5_SINGLE_SEED_PINN_PILOT_DIRECT_BASELINE_GAP",contract=contract,details={"P0_vs_LF_ONLY":direct,"within_architecture_pareto":True})
    return _terminal("LF5_PROVISIONAL_SINGLE_SEED_SIGNAL",contract=contract,details={"single_seed_only":True})


def evaluate_lf5_campaign(*, output_directory: Path, run_directory: Path, cpu_qualification_path: Path, gpu_lifecycle: str=GPU_LIFECYCLE_SHUTDOWN_VERIFIED) -> dict[str, Any]:
    if gpu_lifecycle!=GPU_LIFECYCLE_SHUTDOWN_VERIFIED: raise PermissionError("LF5 local evaluation requires verified GPU shutdown")
    contracts=load_contracts(); files=_run_files(run_directory)
    read_cpu_qualification(cpu_qualification_path,allow_user_override=bool(files["payload"].get("post_qualification_user_override")))
    for binding in contracts["data"]["local_evaluation_only"].values():
        if isinstance(binding,Mapping): _safe_bound_path(binding,label="LF5 local nominal reference")
    run=files["payload"]
    lf3_decision=_read_json(ROOT/"configs/phk_v23/decision_contract_lf3_phase_latent_carrier.json"); lf3_data=_read_json(ROOT/"configs/phk_v23/data_contract_lf3_phase_latent_carrier.json")
    paths=_inherited_prediction_paths(lf3_decision); paths.pop("A_RANGE_PRESERVING_SCRATCH",None); paths[LF2_M0_ROLE]=_safe_bound_path(lf3_data["inherited_comparators"]["lf2_m0_prediction"],label="LF2-M0 prediction"); paths[LF3_T0_ROLE]=ROOT/"outputs/runs/20260904T150300Z-phk-v23-lf3-phase-latent-97a5b74/prediction-t0-step-1200.npz"; paths[DEV_T_ROLE]=files["prediction_dev"]
    if files["prediction_p0"] is not None: paths[P0_ROLE]=files["prediction_p0"]
    evaluations={role:evaluate_prediction(prediction_path=path,control=PhkControl.FULL) for role,path in paths.items()}; potential={role:_prediction_potential_guard(path,absolute_tolerance=1e-6) for role,path in paths.items()}; floors=_component_floors(lf3_decision); comparisons={}
    if P0_ROLE in evaluations: comparisons={"P0_vs_DEV_T":compare_b_to_comparator(evaluations[P0_ROLE],evaluations[DEV_T_ROLE],component_floors=floors),"P0_vs_LF_ONLY":compare_b_to_comparator(evaluations[P0_ROLE],evaluations[LF_ONLY_ROLE],component_floors=floors)}
    checkpoints={DEV_T_ROLE:files["checkpoint_dev"]};
    if files["checkpoint_p0"] is not None: checkpoints[P0_ROLE]=files["checkpoint_p0"]
    physics=_fixed_physics(checkpoints,contracts=contracts); decision=adjudicate(contract=contracts["decision"],run=run,evaluations=evaluations,potential=potential,comparisons=comparisons,physics=physics); sanitized,replaced=_sanitize_nonfinite(evaluations)
    report={"schema_id":"phk-v23-lf5-local-adjudication-v1","task_id":TASK_ID,"status":"COMPLETE","case_control":"FULL","gpu_lifecycle":gpu_lifecycle,"run_status":run["status"],"evidence_role":run.get("evidence_role"),"post_qualification_user_override":bool(run.get("post_qualification_user_override")),"roles_evaluated":list(paths),"prediction_bindings":{role:{"path":str(path),"sha256":_sha256_path(path),"size_bytes":path.stat().st_size} for role,path in paths.items()},"evaluations":sanitized,"evaluator_nonfinite_diagnostics_represented_as_json_null":replaced,"potential_maximum_principle":potential,"component_floors":floors,"comparisons":comparisons,"fixed_physics_objective":physics,"DEV_T_gate":run["DEV_T"]["carrier_gate"],"P0_gate":run.get("P0"),"decision":decision,"fine_extra_use":"LOCAL_NOMINAL_ONLY_AFTER_SHUTDOWN","stress_status":"TWO_STRESS_REFERENCES_SEALED_UNREAD","claim_boundary":contracts["decision"]["claim_boundary"]}
    output=Path(output_directory).resolve(); output.mkdir(parents=True,exist_ok=False); write_strict_json(output/"adjudication.json",report); return report


def _parser()->argparse.ArgumentParser:
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument("--output-directory",type=Path,required=True); parser.add_argument("--run-directory",type=Path,required=True); parser.add_argument("--cpu-qualification",type=Path,required=True); return parser


def main(argv:Sequence[str]|None=None)->int:
    args=_parser().parse_args(argv); report=evaluate_lf5_campaign(output_directory=args.output_directory,run_directory=args.run_directory,cpu_qualification_path=args.cpu_qualification); print(json.dumps({"outcome":report["decision"]["outcome"],"candidate":report["decision"]["candidate"]},sort_keys=True)); return 0


if __name__=="__main__": raise SystemExit(main())


__all__=["adjudicate","evaluate_lf5_campaign","terminal_from_cpu"]
