"""Zero-update remote identity, leakage, process, and V100 preflight for LF5."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
from typing import Any

import torch


ROOT=Path(__file__).resolve().parents[2]
TASK_ID="PHK_V23_LF5_CYCLE_RESOLVED_TEMPORAL_ZERO_LEVEL_ALIGNMENT_AND_CONDITIONAL_PHYSICS_PILOT_EXECUTE"
EXPECTED_GPU="Tesla V100-PCIE-32GB"
MEDIUM_RELATIVE=PurePosixPath("outputs/runs/20260828T-phk-v21-s1-q-04-nominal-medium/result-intent-04.npz")
CHECKPOINT_RELATIVE=PurePosixPath("outputs/runs/20260904T150300Z-phk-v23-lf3-phase-latent-97a5b74/checkpoint-t0-step-1200.pt")
CONTRACT_RELATIVES={name:PurePosixPath(f"configs/phk_v23/{name}_contract_lf5_temporal_zero_level.json") for name in ("program","method","data","decision")}
REQUIRED_RUNTIME=frozenset({*(path.as_posix() for path in CONTRACT_RELATIVES.values()),"cloud/phk_v23_lf5_autodl/preflight.py","cloud/phk_v23_lf5_autodl/run.sh","pinn_pcm_sci/phk_v23_lf5.py","pinn_pcm_sci/phk_v23_lf4.py","pinn_pcm_sci/phk_v23_lf3.py","pinn_pcm_sci/phk_v23_lf2.py","pinn_pcm_sci/phk_v23_lf1.py","pinn_pcm_sci/phk_v23_lf0.py","pinn_pcm_sci/phk_v22r_training.py","tests/test_phk_v21_benchmark.py"})


def _sha(path:Path)->str:
    digest=hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda:handle.read(1024*1024),b""): digest.update(block)
    return digest.hexdigest().upper()


def _safe(root:Path,relative:str)->Path:
    normalized=PurePosixPath(relative)
    if normalized.is_absolute() or ".." in normalized.parts: raise PermissionError("LF5 path escaped deployment root")
    exact=(root/Path(*normalized.parts)).resolve(); exact.relative_to(root.resolve()); return exact


def _forbidden(root:Path)->list[str]:
    allowed={MEDIUM_RELATIVE.as_posix(),CHECKPOINT_RELATIVE.as_posix()}; result=[]
    for path in root.rglob("*"):
        if not path.is_file(): continue
        relative=path.resolve().relative_to(root.resolve()).as_posix(); lower=relative.lower()
        if relative in allowed: continue
        if path.suffix.lower() in {".npz",".pt"} or "nominal-fine" in lower or "nominal-extra-fine" in lower or "lf-only" in lower or any("stress" in part for part in PurePosixPath(lower).parts) or "evaluator" in path.name.lower(): result.append(relative)
    return sorted(result)


def run_preflight(*,source_identity:str,deployment_root:Path,medium_carrier:Path,initial_checkpoint:Path,cuda_probe:Any=None,pythonpath:str|None=None,user_override_cpu_gate:bool=False)->dict[str,Any]:
    root=ROOT.resolve()
    if Path(deployment_root).resolve()!=root: raise ValueError("LF5 deployment root mismatch")
    entries=(os.environ.get("PYTHONPATH","") if pythonpath is None else pythonpath).split(os.pathsep)
    if root not in [Path(entry).resolve() for entry in entries if Path(entry).is_absolute()]: raise RuntimeError("LF5 absolute root absent from PYTHONPATH")
    manifest=json.loads((root/"cloud/phk_v23_lf5_autodl/deployed-source-manifest.json").read_text(encoding="utf-8"))
    if manifest.get("source_identity")!=source_identity: raise ValueError("LF5 manifest identity drift")
    files=manifest.get("files",{})
    if REQUIRED_RUNTIME.difference(files): raise ValueError("LF5 runtime closure incomplete")
    lines=[]
    for relative,expected in sorted(files.items()):
        exact=_safe(root,relative); actual=_sha(exact) if exact.is_file() else None
        if actual!=str(expected).upper(): raise ValueError(f"LF5 deployed source drift: {relative}")
        lines.append(f"{relative}={actual}\n")
    if source_identity!="LF5-BUNDLE-"+hashlib.sha256("".join(lines).encode()).hexdigest().upper(): raise ValueError("LF5 aggregate identity drift")
    qualification_binding=manifest["cpu_qualification"]; qualification_path=_safe(root,qualification_binding["path"]); qualification=json.loads(qualification_path.read_text(encoding="utf-8"))
    gate_passed=qualification.get("status")=="LF5_CPU_T_QUALIFICATION_PASS" and qualification.get("gpu_execution_authorized_by_cpu_gate") is True
    override_valid=user_override_cpu_gate and qualification.get("status")=="LF5_TZL_ALIGNMENT_NOT_SUPPORTED_CPU" and qualification.get("gpu_execution_authorized_by_cpu_gate") is False
    if _sha(qualification_path)!=qualification_binding["sha256"] or not (gate_passed or override_valid): raise PermissionError("LF5 CPU-T qualification/override invalid")
    if bool(manifest.get("post_qualification_user_override")) != bool(override_valid): raise PermissionError("LF5 deployment override identity drift")
    if _forbidden(root): raise PermissionError("LF5 forbidden cloud files present")
    cuda=torch.cuda if cuda_probe is None else cuda_probe
    if not cuda.is_available() or cuda.get_device_name(0)!=EXPECTED_GPU: raise RuntimeError("LF5 exact V100 unavailable")
    return {"status":"REMOTE_LF5_PREFLIGHT_VALID","task_id":TASK_ID,"source_identity":source_identity,"evidence_role":"POST_QUALIFICATION_USER_OVERRIDE_EXPLORATORY" if override_valid else "PREREGISTERED_CPU_QUALIFIED","gpu_name":EXPECTED_GPU,"dtype":"FLOAT64","seed":17,"maximum_optimizer_updates":1600,"maximum_scientific_trajectories":1,"optimizer_constructed":False,"optimizer_updates":0,"stress_fields_present":False}


def main()->int:
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument("--source-identity",required=True); parser.add_argument("--deployment-root",type=Path,required=True); parser.add_argument("--medium-carrier",type=Path,required=True); parser.add_argument("--initial-checkpoint",type=Path,required=True); parser.add_argument("--user-override-cpu-gate",action="store_true"); args=parser.parse_args(); print(json.dumps(run_preflight(source_identity=args.source_identity,deployment_root=args.deployment_root,medium_carrier=args.medium_carrier,initial_checkpoint=args.initial_checkpoint,user_override_cpu_gate=args.user_override_cpu_gate),sort_keys=True)); return 0


if __name__=="__main__": raise SystemExit(main())
