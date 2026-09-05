"""Zero-update remote identity, leakage, process, and V100 preflight for LF4."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
from typing import Any

import torch


ROOT=Path(__file__).resolve().parents[2]
TASK_ID="PHK_V23_LF4_THRESHOLD_ALIGNED_INTERFACE_BAND_MECHANISM_AND_CONDITIONAL_PHYSICS_PILOT_EXECUTE"
EXPECTED_GPU="Tesla V100-PCIE-32GB"
MEDIUM_RELATIVE=PurePosixPath("outputs/runs/20260828T-phk-v21-s1-q-04-nominal-medium/result-intent-04.npz")
CHECKPOINT_RELATIVE=PurePosixPath("outputs/runs/20260904T150300Z-phk-v23-lf3-phase-latent-97a5b74/checkpoint-t0-step-1200.pt")
CONTRACT_RELATIVES={name:PurePosixPath(f"configs/phk_v23/{name}_contract_lf4_interface_band.json") for name in ("program","method","data","decision")}
REQUIRED_RUNTIME=frozenset({*(path.as_posix() for path in CONTRACT_RELATIVES.values()),"cloud/phk_v23_lf4_autodl/preflight.py","cloud/phk_v23_lf4_autodl/run.sh","pinn_pcm_sci/phk_v23_lf4.py","pinn_pcm_sci/phk_v23_lf3.py","pinn_pcm_sci/phk_v23_lf2.py","pinn_pcm_sci/phk_v23_lf1.py","pinn_pcm_sci/phk_v23_lf0.py","pinn_pcm_sci/phk_v22r_training.py"})


def _sha(path:Path)->str:
    digest=hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda:handle.read(1024*1024),b""): digest.update(block)
    return digest.hexdigest().upper()


def _read(path:Path)->dict[str,Any]:
    payload=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload,dict): raise ValueError(f"expected JSON object: {path}")
    return payload


def _safe(root:Path,relative:str)->Path:
    normalized=PurePosixPath(relative)
    if normalized.is_absolute() or ".." in normalized.parts: raise PermissionError("LF4 path escaped deployment root")
    exact=(root/Path(*normalized.parts)).resolve(); exact.relative_to(root.resolve()); return exact


def _manifest(root:Path,source_identity:str)->dict[str,Any]:
    manifest=_read(root/"cloud/phk_v23_lf4_autodl/deployed-source-manifest.json")
    if manifest.get("schema_id")!="phk-v23-lf4-deployed-source-manifest-v1" or manifest.get("identity_definition")!="SHA256_OF_SORTED_PATH_EQUALS_UPPERCASE_SHA256_LINES" or manifest.get("source_identity")!=source_identity: raise ValueError("LF4 manifest identity drift")
    files=manifest.get("files")
    if not isinstance(files,dict) or REQUIRED_RUNTIME.difference(files): raise ValueError("LF4 runtime closure incomplete")
    lines=[]
    for relative,expected in sorted(files.items()):
        exact=_safe(root,relative); actual=_sha(exact) if exact.is_file() else None
        if actual!=str(expected).upper(): raise ValueError(f"LF4 deployed source drift: {relative}")
        lines.append(f"{relative}={actual}\n")
    digest=hashlib.sha256("".join(lines).encode()).hexdigest().upper()
    if source_identity!=f"LF4-BUNDLE-{digest}": raise ValueError("LF4 aggregate identity mismatch")
    return manifest


def _forbidden(root:Path)->list[str]:
    allowed={MEDIUM_RELATIVE.as_posix(),CHECKPOINT_RELATIVE.as_posix()}; result=[]
    for path in root.rglob("*"):
        if not path.is_file(): continue
        relative=path.resolve().relative_to(root.resolve()).as_posix()
        if relative in allowed: continue
        lower=relative.lower()
        if path.suffix.lower() in {".npz",".pt"} or "nominal-fine" in lower or "nominal-extra-fine" in lower or "lf-only" in lower or any("stress" in part for part in PurePosixPath(lower).parts) or "evaluator" in path.name.lower(): result.append(relative)
    return sorted(result)


def _duplicates()->list[str]:
    if os.name!="posix" or not Path("/proc").is_dir(): return []
    matches=[]
    for candidate in Path("/proc").iterdir():
        if not candidate.name.isdigit() or int(candidate.name)==os.getpid(): continue
        try: tokens=[item.decode(errors="replace") for item in (candidate/"cmdline").read_bytes().split(b"\0") if item]
        except (FileNotFoundError,PermissionError,ProcessLookupError): continue
        if "pinn_pcm_sci.phk_v23_lf4" in tokens: matches.append(f"pid:{candidate.name}")
    return sorted(matches)


def run_preflight(*,source_identity:str,deployment_root:Path,medium_carrier:Path,initial_checkpoint:Path,cuda_probe:Any=None,pythonpath:str|None=None)->dict[str,Any]:
    root=ROOT.resolve()
    if not Path(deployment_root).is_absolute() or Path(deployment_root).resolve()!=root: raise ValueError("LF4 deployment root mismatch")
    entries=(os.environ.get("PYTHONPATH","") if pythonpath is None else pythonpath).split(os.pathsep)
    if root not in [Path(entry).resolve() for entry in entries if Path(entry).is_absolute()]: raise RuntimeError("LF4 absolute root absent from PYTHONPATH")
    manifest=_manifest(root,source_identity); contracts={role:_read(root/Path(*relative.parts)) for role,relative in CONTRACT_RELATIVES.items()}
    if contracts["program"].get("phase_id")!=TASK_ID or contracts["program"]["hard_limits"].get("gpu_price_or_cost_reporting") is not False: raise ValueError("LF4 contract identity drift")
    bindings={"medium":contracts["data"]["training_source"],"initial_checkpoint":contracts["data"]["initial_checkpoint"]}; supplied={"medium":(Path(medium_carrier).resolve(),MEDIUM_RELATIVE),"initial_checkpoint":(Path(initial_checkpoint).resolve(),CHECKPOINT_RELATIVE)}
    for role,(exact,relative) in supplied.items():
        required=(root/Path(*relative.parts)).resolve(); actual=_sha(exact) if exact.is_file() else None; record={"path":relative.as_posix(),"sha256":actual,"size_bytes":exact.stat().st_size if exact.is_file() else -1}
        if exact!=required or not exact.is_file() or bindings[role].get("path")!=relative.as_posix() or actual!=str(bindings[role].get("sha256","")).upper() or manifest["training_inputs"].get(role)!=record: raise PermissionError(f"LF4 exact {role} drift")
    qualification_binding=manifest["cpu_qualification"]; qualification_path=_safe(root,qualification_binding["path"]); qualification=_read(qualification_path)
    if _sha(qualification_path)!=qualification_binding["sha256"] or qualification.get("status")!="LF4_CPU_QUALIFICATION_PASS" or qualification.get("gpu_execution_authorized_by_cpu_gate") is not True: raise PermissionError("LF4 CPU qualification invalid")
    forbidden=_forbidden(root); duplicates=_duplicates()
    if forbidden: raise PermissionError(f"LF4 forbidden cloud files: {forbidden}")
    if duplicates: raise RuntimeError(f"duplicate LF4 process: {duplicates}")
    cuda=torch.cuda if cuda_probe is None else cuda_probe
    if not cuda.is_available() or cuda.get_device_name(0)!=EXPECTED_GPU: raise RuntimeError("LF4 exact V100 unavailable")
    return {"status":"REMOTE_LF4_PREFLIGHT_VALID","task_id":TASK_ID,"source_identity":source_identity,"gpu_name":EXPECTED_GPU,"dtype":"FLOAT64","seed":17,"maximum_optimizer_updates":2400,"maximum_scientific_trajectories":4,"forbidden_cloud_files":[],"duplicate_training_processes":[],"optimizer_constructed":False,"optimizer_updates":0,"stress_fields_present":False}


def main()->int:
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument("--source-identity",required=True); parser.add_argument("--deployment-root",type=Path,required=True); parser.add_argument("--medium-carrier",type=Path,required=True); parser.add_argument("--initial-checkpoint",type=Path,required=True); args=parser.parse_args(); print(json.dumps(run_preflight(source_identity=args.source_identity,deployment_root=args.deployment_root,medium_carrier=args.medium_carrier,initial_checkpoint=args.initial_checkpoint),sort_keys=True)); return 0


if __name__=="__main__": raise SystemExit(main())
