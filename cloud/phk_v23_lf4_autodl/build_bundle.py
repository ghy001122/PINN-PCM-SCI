"""Build the committed, reference-blind LF4 AutoDL source bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import tarfile
from typing import Sequence


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "cloud/phk_v23_lf4_autodl/deployed-source-manifest.json"
MEDIUM = ROOT / "outputs/runs/20260828T-phk-v21-s1-q-04-nominal-medium/result-intent-04.npz"
INITIAL_CHECKPOINT = ROOT / "outputs/runs/20260904T150300Z-phk-v23-lf3-phase-latent-97a5b74/checkpoint-t0-step-1200.pt"
STATIC_FILES = (
    "cloud/phk_v23_lf4_autodl/preflight.py", "cloud/phk_v23_lf4_autodl/run.sh", "cloud/phk_v23_lf4_autodl/README.md",
    "configs/phk_v23/program_contract_lf4_interface_band.json", "configs/phk_v23/method_contract_lf4_interface_band.json", "configs/phk_v23/data_contract_lf4_interface_band.json", "configs/phk_v23/decision_contract_lf4_interface_band.json",
    "configs/phk_v23/program_contract_lf3_phase_latent_carrier.json", "configs/phk_v23/method_contract_lf3_phase_latent_carrier.json", "configs/phk_v23/data_contract_lf3_phase_latent_carrier.json", "configs/phk_v23/decision_contract_lf3_phase_latent_carrier.json",
    "configs/phk_v23/program_contract_lf2_measure_calibrated_feasible_pinn.json", "configs/phk_v23/method_contract_lf2_measure_calibrated_feasible_pinn.json", "configs/phk_v23/data_contract_lf2_measure_calibrated_medium.json", "configs/phk_v23/decision_contract_lf2_measure_calibrated_feasible_pinn.json",
    "configs/phk_v23/program_contract_lf1_event_preserving_multifidelity.json", "configs/phk_v23/method_contract_lf1_event_preserving_multifidelity.json", "configs/phk_v23/data_contract_lf1_medium_event_replay.json", "configs/phk_v23/decision_contract_lf1_event_preserving.json",
    "configs/phk_v22r/program_contract.json", "configs/phk_v22r/method_contract.json", "configs/phk_v21/program_contract.json", "configs/phk_v21/object_numerical_contract.json", "configs/phk_v21/engineering_contract.json", "configs/phk_v21/e1_solver_selection.json", "configs/phk_v2/program_contract.json", "configs/phk_v2/object_numerical_contract.json",
    "outputs/runs/20260827T-phk-v21-e2-engineering-search-001/summary.json",
    "pinn_pcm_sci/__init__.py", "pinn_pcm_sci/artifacts.py", "pinn_pcm_sci/phk_contract.py", "pinn_pcm_sci/phk_benchmark.py", "pinn_pcm_sci/phk_v21_benchmark.py", "pinn_pcm_sci/phk_v21_solver.py", "pinn_pcm_sci/phk_v22r_pinn.py", "pinn_pcm_sci/phk_v22r_training.py", "pinn_pcm_sci/phk_v22r_prediction.py", "pinn_pcm_sci/phk_v23_lf0.py", "pinn_pcm_sci/phk_v23_lf1.py", "pinn_pcm_sci/phk_v23_lf2.py", "pinn_pcm_sci/phk_v23_lf3.py", "pinn_pcm_sci/phk_v23_lf4.py", "tests/test_phk_v21_benchmark.py",
)


def _sha256(path: Path) -> str:
    digest=hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda:handle.read(1024*1024),b""): digest.update(block)
    return digest.hexdigest().upper()


def build(*,qualification_path:Path,archive_path:Path,base_commit:str)->dict[str,object]:
    qualification=Path(qualification_path).resolve(); qualification_relative=qualification.relative_to(ROOT).as_posix(); files=(*STATIC_FILES,qualification_relative)
    if len(files)!=len(set(files)): raise ValueError("LF4 bundle contains duplicate paths")
    bindings:dict[str,str]={}
    for relative in files:
        path=ROOT/relative
        if not path.is_file(): raise FileNotFoundError(f"LF4 source file absent: {relative}")
        bindings[relative]=_sha256(path)
    lines="".join(f"{relative}={digest}\n" for relative,digest in sorted(bindings.items())); aggregate=hashlib.sha256(lines.encode()).hexdigest().upper(); source_identity=f"LF4-BUNDLE-{aggregate}"
    if not MEDIUM.is_file() or not INITIAL_CHECKPOINT.is_file(): raise FileNotFoundError("LF4 separately uploaded input absent")
    qualification_payload=json.loads(qualification.read_text(encoding="utf-8"))
    if qualification_payload.get("status")!="LF4_CPU_QUALIFICATION_PASS" or qualification_payload.get("gpu_execution_authorized_by_cpu_gate") is not True: raise PermissionError("LF4 bundle requires passed CPU qualification")
    manifest={"schema_id":"phk-v23-lf4-deployed-source-manifest-v1","source_identity":source_identity,"identity_definition":"SHA256_OF_SORTED_PATH_EQUALS_UPPERCASE_SHA256_LINES","base_commit":base_commit,"workspace_scope":"LF4_EXACT_COMMITTED_ALLOWLIST_UNRELATED_DIRTY_EXCLUDED","training_inputs":{"medium":{"path":MEDIUM.relative_to(ROOT).as_posix(),"sha256":_sha256(MEDIUM),"size_bytes":MEDIUM.stat().st_size},"initial_checkpoint":{"path":INITIAL_CHECKPOINT.relative_to(ROOT).as_posix(),"sha256":_sha256(INITIAL_CHECKPOINT),"size_bytes":INITIAL_CHECKPOINT.stat().st_size}},"cpu_qualification":{"path":qualification_relative,"sha256":_sha256(qualification),"size_bytes":qualification.stat().st_size},"files":dict(sorted(bindings.items()))}
    if MANIFEST.exists(): raise FileExistsError(f"refusing to replace LF4 manifest: {MANIFEST}")
    MANIFEST.write_text(json.dumps(manifest,indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf-8",newline="\n")
    archive=Path(archive_path).resolve(); archive.parent.mkdir(parents=True,exist_ok=True)
    if archive.exists(): raise FileExistsError(f"refusing to replace LF4 archive: {archive}")
    with tarfile.open(archive,"w:gz") as handle:
        for relative in files: handle.add(ROOT/relative,arcname=relative,recursive=False)
        handle.add(MANIFEST,arcname=MANIFEST.relative_to(ROOT).as_posix(),recursive=False)
    return {"source_identity":source_identity,"manifest":str(MANIFEST),"manifest_sha256":_sha256(MANIFEST),"archive":str(archive),"archive_sha256":_sha256(archive),"file_count":len(files)}


def main(argv:Sequence[str]|None=None)->int:
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument("--qualification",type=Path,required=True); parser.add_argument("--archive",type=Path,required=True); parser.add_argument("--base-commit",required=True); args=parser.parse_args(argv); print(json.dumps(build(qualification_path=args.qualification,archive_path=args.archive,base_commit=args.base_commit),sort_keys=True)); return 0


if __name__=="__main__": raise SystemExit(main())
