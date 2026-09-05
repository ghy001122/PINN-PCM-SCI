"""Build the committed reference-blind LF5 bundle after qualification or explicit override."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import tarfile
from typing import Sequence


ROOT=Path(__file__).resolve().parents[2]
MANIFEST=ROOT/"cloud/phk_v23_lf5_autodl/deployed-source-manifest.json"
MEDIUM=ROOT/"outputs/runs/20260828T-phk-v21-s1-q-04-nominal-medium/result-intent-04.npz"
INITIAL_CHECKPOINT=ROOT/"outputs/runs/20260904T150300Z-phk-v23-lf3-phase-latent-97a5b74/checkpoint-t0-step-1200.pt"
STATIC_FILES=(
    "cloud/phk_v23_lf5_autodl/preflight.py","cloud/phk_v23_lf5_autodl/run.sh","cloud/phk_v23_lf5_autodl/README.md",
    "configs/phk_v23/program_contract_lf5_temporal_zero_level.json","configs/phk_v23/method_contract_lf5_temporal_zero_level.json","configs/phk_v23/data_contract_lf5_temporal_zero_level.json","configs/phk_v23/decision_contract_lf5_temporal_zero_level.json",
    "configs/phk_v23/program_contract_lf4_interface_band.json","configs/phk_v23/method_contract_lf4_interface_band.json","configs/phk_v23/data_contract_lf4_interface_band.json","configs/phk_v23/decision_contract_lf4_interface_band.json",
    "configs/phk_v23/program_contract_lf3_phase_latent_carrier.json","configs/phk_v23/method_contract_lf3_phase_latent_carrier.json","configs/phk_v23/data_contract_lf3_phase_latent_carrier.json","configs/phk_v23/decision_contract_lf3_phase_latent_carrier.json",
    "configs/phk_v23/program_contract_lf2_measure_calibrated_feasible_pinn.json","configs/phk_v23/method_contract_lf2_measure_calibrated_feasible_pinn.json","configs/phk_v23/data_contract_lf2_measure_calibrated_medium.json","configs/phk_v23/decision_contract_lf2_measure_calibrated_feasible_pinn.json",
    "configs/phk_v23/program_contract_lf1_event_preserving_multifidelity.json","configs/phk_v23/method_contract_lf1_event_preserving_multifidelity.json","configs/phk_v23/data_contract_lf1_medium_event_replay.json","configs/phk_v23/decision_contract_lf1_event_preserving.json",
    "configs/phk_v22r/program_contract.json","configs/phk_v22r/method_contract.json","configs/phk_v21/program_contract.json","configs/phk_v21/object_numerical_contract.json","configs/phk_v21/engineering_contract.json","configs/phk_v21/e1_solver_selection.json","configs/phk_v2/program_contract.json","configs/phk_v2/object_numerical_contract.json","outputs/runs/20260827T-phk-v21-e2-engineering-search-001/summary.json",
    "pinn_pcm_sci/__init__.py","pinn_pcm_sci/artifacts.py","pinn_pcm_sci/phk_contract.py","pinn_pcm_sci/phk_benchmark.py","pinn_pcm_sci/phk_v21_benchmark.py","pinn_pcm_sci/phk_v21_solver.py","pinn_pcm_sci/phk_v22r_pinn.py","pinn_pcm_sci/phk_v22r_training.py","pinn_pcm_sci/phk_v22r_prediction.py","pinn_pcm_sci/phk_v23_lf0.py","pinn_pcm_sci/phk_v23_lf1.py","pinn_pcm_sci/phk_v23_lf2.py","pinn_pcm_sci/phk_v23_lf3.py","pinn_pcm_sci/phk_v23_lf4.py","pinn_pcm_sci/phk_v23_lf5.py",
    "tests/test_phk_v21_benchmark.py"
)


def _sha(path:Path)->str:
    digest=hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda:handle.read(1024*1024),b""): digest.update(block)
    return digest.hexdigest().upper()


def build(*,qualification_path:Path,archive_path:Path,base_commit:str,user_override_cpu_gate:bool=False)->dict[str,object]:
    qualification=Path(qualification_path).resolve(); payload=json.loads(qualification.read_text(encoding="utf-8"))
    gate_passed=payload.get("status")=="LF5_CPU_T_QUALIFICATION_PASS" and payload.get("gpu_execution_authorized_by_cpu_gate") is True
    override_valid=user_override_cpu_gate and payload.get("status")=="LF5_TZL_ALIGNMENT_NOT_SUPPORTED_CPU" and payload.get("gpu_execution_authorized_by_cpu_gate") is False
    if not (gate_passed or override_valid): raise PermissionError("LF5 bundle requires passed CPU-T qualification or explicit user override")
    relative_qualification=qualification.relative_to(ROOT).as_posix(); files=(*STATIC_FILES,relative_qualification)
    if len(files)!=len(set(files)): raise ValueError("LF5 bundle contains duplicate paths")
    bindings={relative:_sha(ROOT/relative) for relative in files}; lines="".join(f"{relative}={digest}\n" for relative,digest in sorted(bindings.items())); source_identity="LF5-BUNDLE-"+hashlib.sha256(lines.encode()).hexdigest().upper()
    manifest={"schema_id":"phk-v23-lf5-deployed-source-manifest-v1","source_identity":source_identity,"identity_definition":"SHA256_OF_SORTED_PATH_EQUALS_UPPERCASE_SHA256_LINES","base_commit":base_commit,"workspace_scope":"LF5_EXACT_COMMITTED_ALLOWLIST_UNRELATED_DIRTY_EXCLUDED","evidence_role":"POST_QUALIFICATION_USER_OVERRIDE_EXPLORATORY" if override_valid else "PREREGISTERED_CPU_QUALIFIED","cpu_gate_passed":gate_passed,"post_qualification_user_override":override_valid,"training_inputs":{"medium":{"path":MEDIUM.relative_to(ROOT).as_posix(),"sha256":_sha(MEDIUM),"size_bytes":MEDIUM.stat().st_size},"initial_checkpoint":{"path":INITIAL_CHECKPOINT.relative_to(ROOT).as_posix(),"sha256":_sha(INITIAL_CHECKPOINT),"size_bytes":INITIAL_CHECKPOINT.stat().st_size}},"cpu_qualification":{"path":relative_qualification,"sha256":_sha(qualification),"size_bytes":qualification.stat().st_size},"files":dict(sorted(bindings.items()))}
    if MANIFEST.exists(): raise FileExistsError(MANIFEST)
    MANIFEST.write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8",newline="\n")
    archive=Path(archive_path).resolve(); archive.parent.mkdir(parents=True,exist_ok=True)
    if archive.exists(): raise FileExistsError(archive)
    with tarfile.open(archive,"w:gz") as handle:
        for relative in files: handle.add(ROOT/relative,arcname=relative,recursive=False)
        handle.add(MANIFEST,arcname=MANIFEST.relative_to(ROOT).as_posix(),recursive=False)
    return {"source_identity":source_identity,"manifest":str(MANIFEST),"manifest_sha256":_sha(MANIFEST),"archive":str(archive),"archive_sha256":_sha(archive),"file_count":len(files)}


def main(argv:Sequence[str]|None=None)->int:
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument("--qualification",type=Path,required=True); parser.add_argument("--archive",type=Path,required=True); parser.add_argument("--base-commit",required=True); parser.add_argument("--user-override-cpu-gate",action="store_true"); args=parser.parse_args(argv); print(json.dumps(build(qualification_path=args.qualification,archive_path=args.archive,base_commit=args.base_commit,user_override_cpu_gate=args.user_override_cpu_gate),sort_keys=True)); return 0


if __name__=="__main__": raise SystemExit(main())
