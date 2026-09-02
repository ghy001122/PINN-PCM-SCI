"""Fail-closed, zero-update AutoDL preflight for the PHK-V2.3 R1X bundle."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch

from pinn_pcm_sci.phk_v22r_training import load_case_physics
from pinn_pcm_sci.phk_v23_r1x import (
    _assert_deployed_source_identity,
    load_r1x_contracts,
)


ROOT = Path(__file__).resolve().parents[2]


def run_preflight(source_identity: str) -> dict[str, object]:
    load_r1x_contracts()
    _assert_deployed_source_identity(source_identity)
    physics, _, _ = load_case_physics()
    forbidden = [
        str(path.relative_to(ROOT))
        for path in ROOT.rglob("*")
        if path.is_file()
        and (
            "result-intent" in path.name.lower()
            or "stress-reference" in path.name.lower()
        )
    ]
    if forbidden:
        raise PermissionError(f"reference-like cloud files are forbidden: {forbidden}")
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is unavailable")
    gpu_name = torch.cuda.get_device_name(0)
    if gpu_name != "Tesla V100-PCIE-32GB":
        raise RuntimeError(f"unexpected GPU: {gpu_name}")
    return {
        "status": "REMOTE_R1X_PREFLIGHT_VALID",
        "source_identity": source_identity,
        "gpu_name": gpu_name,
        "torch_version": torch.__version__,
        "torch_cuda_version": torch.version.cuda,
        "physics_control": physics.control,
        "reference_like_files": forbidden,
        "optimizer_constructed": False,
        "optimizer_updates": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-identity", required=True)
    args = parser.parse_args()
    print(json.dumps(run_preflight(args.source_identity), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
