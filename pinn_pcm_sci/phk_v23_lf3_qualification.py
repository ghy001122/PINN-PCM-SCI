"""Zero-update local CPU qualification for the PHK-V2.3 LF3 pilot."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import subprocess
from typing import Any, Mapping, Sequence

import numpy as np
import torch

from .phk_v22r_pinn import POTENTIAL_TRANSFORM_EXACT_TOP_RANGE_PRESERVING
from .phk_v22r_training import ROOT, load_case_physics
from .phk_v23_lf0 import _sha256_path
from .phk_v23_lf2 import CATEGORY_NAMES, MeasureCalibratedBatchStream
from .phk_v23_lf3 import (
    CLIP_EPSILON,
    EXPECTED_PARTITION_SHA256,
    EXPECTED_T0_STREAM_SHA256,
    LOGIT_SPAN,
    Q_ABSOLUTE_BOUND,
    TASK_ID,
    build_training_config,
    contract_identity,
    full_medium_audit,
    load_contracts,
    load_lf1_b0_initialization,
    load_medium_dataset,
    phase_logit_targets,
)


LF3_WORKTREE_ALLOWLIST = (
    "cloud/phk_v23_lf3_autodl/",
    "configs/phk_v23/program_contract_lf3_phase_latent_carrier.json",
    "configs/phk_v23/method_contract_lf3_phase_latent_carrier.json",
    "configs/phk_v23/data_contract_lf3_phase_latent_carrier.json",
    "configs/phk_v23/decision_contract_lf3_phase_latent_carrier.json",
    "pinn_pcm_sci/phk_v23_lf3.py",
    "pinn_pcm_sci/phk_v23_lf3_qualification.py",
    "pinn_pcm_sci/phk_v23_lf3_evaluation.py",
    "tests/test_phk_v23_lf3.py",
    "tests/test_phk_v23_lf3_evaluation.py",
    "tests/test_phk_v23_lf3_cloud.py",
    "docs/references/2026-09-04-phk-v23-lf3-prior-art-closure.md",
    "docs/adr/0059-activate-phk-v23-lf3-phase-latent-carrier-pilot.md",
    "docs/experiment/2026-09-04-phk-v23-lf3-cpu-qualification.md",
    "docs/experiment/2026-09-04-phk-v23-lf3-terminal-closeout.md",
    "docs/experiment/artifacts/20260904T150300Z-phk-v23-lf3-terminal-",
    "docs/experiment/manifests/20260904T150300Z-phk-v23-lf3-terminal-",
    "paper/paper_v23/",
    "CONTEXT.md",
    "active_phase.md",
    "PROJECT_STATE.md",
    "docs/plans/NEXT_ACTIONS.md",
    "docs/README.md",
    "docs/references/README.md",
    "docs/adr/README.md",
    "docs/experiment/README.md",
    "docs/experiment/artifacts/README.md",
    "docs/experiment/manifests/README.md",
)


def _status_path(line: str) -> str:
    """Return the porcelain path without altering or acting on the worktree."""

    path = line[3:] if len(line) >= 3 else line
    if " -> " in path:
        path = path.split(" -> ", 1)[1]
    return path.strip('"').replace("\\", "/")


def _is_lf3_allowlisted(path: str) -> bool:
    return any(
        path == entry or (entry.endswith("/") and path.startswith(entry))
        or (entry.endswith("-") and path.startswith(entry))
        for entry in LF3_WORKTREE_ALLOWLIST
    )


def _verify_binding(binding: Mapping[str, Any], *, label: str) -> Path:
    relative, expected = binding.get("path"), binding.get("sha256")
    if not isinstance(relative, str) or not isinstance(expected, str):
        raise ValueError(f"LF3 malformed input binding: {label}")
    exact = (ROOT / Path(relative.replace("/", "\\"))).resolve()
    try:
        exact.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise PermissionError(f"LF3 input escaped repository: {label}") from exc
    if not exact.is_file() or _sha256_path(exact) != expected.upper():
        raise ValueError(f"LF3 input absent or hash-drifted: {label}")
    return exact


def _strict_write(path: Path, payload: Mapping[str, Any]) -> Path:
    exact = Path(path).resolve()
    exact.parent.mkdir(parents=True, exist_ok=True)
    encoded = (json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")
    with exact.open("xb") as handle:
        handle.write(encoded)
    return exact


def record_initial_worktree(path: Path) -> dict[str, Any]:
    status = subprocess.run(
        ["git", "status", "--porcelain=v1", "-uall"], cwd=ROOT,
        capture_output=True, text=True, encoding="utf-8", errors="replace", check=True,
    ).stdout
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    branch = subprocess.run(["git", "branch", "--show-current"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    lines = status.splitlines()
    unrelated = [line for line in lines if not _is_lf3_allowlisted(_status_path(line))]
    unrelated_text = "\n".join(unrelated) + ("\n" if unrelated else "")
    payload = {
        "schema_id": "phk-v23-lf3-initial-worktree-v1", "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        "head": head, "branch": branch, "status_porcelain_v1_uall": lines,
        "status_sha256": hashlib.sha256(status.encode("utf-8")).hexdigest().upper(),
        "lf3_allowlist": list(LF3_WORKTREE_ALLOWLIST),
        "preexisting_unrelated_status_porcelain_v1_uall": unrelated,
        "preexisting_unrelated_status_sha256": hashlib.sha256(unrelated_text.encode("utf-8")).hexdigest().upper(),
        "lf3_entries_excluded_from_preexisting_snapshot": len(lines) - len(unrelated),
        "policy": "PRESERVE_UNRELATED_DIRTY_NO_STASH_RESET_CLEAN_RESTORE_CHECKOUT_DELETE_OR_MOVE",
    }
    written = _strict_write(path, payload)
    return {"path": written.relative_to(ROOT).as_posix(), "sha256": _sha256_path(written), "entries": len(payload["status_porcelain_v1_uall"])}


def _latent_math_identity(dataset: Any, physics: Any, *, chunk: int = 65536) -> dict[str, Any]:
    reconstruction_max = 0.0
    q_max = 0.0
    delta_min, delta_max = math.inf, -math.inf
    startup_min, startup_max = math.inf, -math.inf
    t0_count = 0
    supervised_count = 0
    finite = True
    for start in range(0, dataset.node_count, chunk):
        stop = min(start + chunk, dataset.node_count)
        coordinates = torch.as_tensor(dataset.coordinates[start:stop], dtype=torch.float64)
        target = torch.as_tensor(dataset.targets[start:stop, 2:3], dtype=torch.float64)
        delta, startup, mask = phase_logit_targets(coordinates, target, physics=physics)
        initial = physics.initial_phase(coordinates).clamp(CLIP_EPSILON, 1.0 - CLIP_EPSILON)
        reconstructed = torch.sigmoid(torch.logit(initial) + delta)
        clipped = target.clamp(CLIP_EPSILON, 1.0 - CLIP_EPSILON)
        reconstruction_max = max(reconstruction_max, float(torch.max(torch.abs(reconstructed - clipped))))
        q_max = max(q_max, float(torch.max(torch.abs(delta / 8.0))))
        delta_min = min(delta_min, float(torch.min(delta)))
        delta_max = max(delta_max, float(torch.max(delta)))
        startup_min = min(startup_min, float(torch.min(startup)))
        startup_max = max(startup_max, float(torch.max(startup)))
        t0_count += int(torch.count_nonzero(~mask))
        supervised_count += int(torch.count_nonzero(mask))
        finite = finite and bool(torch.isfinite(delta).all() and torch.isfinite(startup).all())
    return {
        "clip_epsilon": CLIP_EPSILON, "logit_span_normalizer": LOGIT_SPAN,
        "q_absolute_bound": Q_ABSOLUTE_BOUND, "observed_q_absolute_maximum": q_max,
        "delta_logit_minimum": delta_min, "delta_logit_maximum": delta_max,
        "startup_minimum": startup_min, "startup_maximum": startup_max,
        "t0_masked_node_count": t0_count, "supervised_t_greater_t0_node_count": supervised_count,
        "finite": finite, "reconstruction_maximum_absolute_error": reconstruction_max,
        "reconstruction_tolerance": 1.0e-12,
        "passed": finite and q_max <= Q_ABSOLUTE_BOUND + 1.0e-12 and reconstruction_max <= 1.0e-12 and startup_min >= 0.0 and startup_max < 1.0 and t0_count > 0 and supervised_count > 0,
    }


def _full_stream_identity(dataset: Any) -> dict[str, Any]:
    stream = MeasureCalibratedBatchStream(dataset, role="M0")
    first = None
    final = None
    for step in range(1, 1201):
        batch = stream.draw(step)
        if first is None:
            first = batch.batch_sha256
        final = batch.batch_sha256
    rejected = False
    try:
        MeasureCalibratedBatchStream(dataset, role="M0").draw(2)
    except ValueError:
        rejected = True
    return {
        "draws": stream.draw_count, "first_batch_sha256": first,
        "final_batch_sha256": final, "rolling_sha256": stream.rolling_sha256,
        "expected_rolling_sha256": EXPECTED_T0_STREAM_SHA256,
        "strict_out_of_order_rejected": rejected,
        "physics_sampler_constructed": False, "physics_sampler_draws": 0,
        "passed": stream.draw_count == 1200 and stream.rolling_sha256 == EXPECTED_T0_STREAM_SHA256 and rejected,
    }


def qualify_cpu(*, output_path: Path, initial_worktree_path: Path | None = None) -> dict[str, Any]:
    contracts = load_contracts()
    identities = contract_identity()
    data, decision = contracts["data"], contracts["decision"]
    source_path = _verify_binding(data["training_source"], label="medium training source")
    checkpoint_path = _verify_binding(data["initial_checkpoint"], label="LF1-B0 checkpoint")
    bound_inputs = {
        name: {"path": binding["path"], "sha256": _sha256_path(_verify_binding(binding, label=name))}
        for name, binding in decision["qualification_inputs"].items()
    }
    config = build_training_config("cpu")
    physics, physical_program_sha256, physical_object_sha256 = load_case_physics("FULL")
    dataset = load_medium_dataset(source_path, physics=physics, contracts=contracts)
    model, checkpoint = load_lf1_b0_initialization(
        checkpoint_path, physics=physics, config=config, contracts=contracts, device=torch.device("cpu")
    )
    baseline = full_medium_audit(model, dataset, device=torch.device("cpu"), absolute_tolerance=1.0e-6)
    latent = _latent_math_identity(dataset, physics)
    stream = _full_stream_identity(dataset)
    mass_sum = float(sum(dataset.category_masses.values()))
    partition = {
        "saved_node_count": dataset.node_count, "time_node_count": int(dataset.time.size), "cell_count": int(dataset.cell_count),
        "category_order": list(CATEGORY_NAMES), "category_counts": dataset.category_counts,
        "category_target_measure_masses_pi": dataset.category_masses,
        "target_measure_mass_sum": mass_sum,
        "mutually_exclusive": sum(dataset.category_counts.values()) == dataset.node_count,
        "exhaustive": sum(dataset.category_counts.values()) == dataset.node_count,
        "all_required_categories_nonempty": all(dataset.category_counts[name] > 0 for name in CATEGORY_NAMES),
        "partition_sha256": dataset.partition_sha256,
        "expected_partition_sha256": EXPECTED_PARTITION_SHA256,
    }
    dtypes = sorted({str(parameter.dtype) for parameter in model.parameters()})
    identity = {
        "medium_sha256": _sha256_path(source_path), "lf1_b0_checkpoint_sha256": _sha256_path(checkpoint_path),
        "checkpoint_schema_id": checkpoint.get("schema_id"), "checkpoint_stage": checkpoint.get("lf1", {}).get("stage"),
        "checkpoint_global_step": checkpoint.get("lf1", {}).get("global_optimizer_step"), "optimizer_state_loaded": False,
        "model_parameter_dtypes": dtypes, "float64_exact": dtypes == ["torch.float64"],
        "potential_transform": POTENTIAL_TRANSFORM_EXACT_TOP_RANGE_PRESERVING,
        "physical_program_sha256": physical_program_sha256, "physical_object_sha256": physical_object_sha256,
        "fine_extra_fine_lf_only_frozen_evaluator_cloud_access": False, "stress_cloud_access": False,
    }
    worktree = record_initial_worktree(initial_worktree_path) if initial_worktree_path is not None else None
    passed = all((
        partition["mutually_exclusive"], partition["exhaustive"], partition["all_required_categories_nonempty"],
        partition["partition_sha256"] == EXPECTED_PARTITION_SHA256,
        math.isclose(mass_sum, 1.0, rel_tol=0.0, abs_tol=1.0e-14),
        latent["passed"], stream["passed"], identity["float64_exact"],
        baseline["all_values_finite"], baseline["phase_range"]["passed"], baseline["potential_maximum_principle"]["passed"],
    ))
    report = {
        "schema_id": "phk-v23-lf3-cpu-qualification-v1", "task_id": TASK_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(), "contracts": identities,
        "bound_qualification_inputs": bound_inputs, "partition": partition,
        "T0_phase_logit_math": latent, "T0_matched_stream_identity": stream,
        "lf1_b0_full_medium_audit": baseline, "identity_and_reference_boundary": identity,
        "initial_worktree_record": worktree,
        "scientific_model_optimizer_updates": 0, "gpu_used": False,
        "fine_extra_fine_reference_read": False, "stress_fields_or_metrics_read": False,
        "status": "LF3_CPU_QUALIFICATION_PASS" if passed else "LF3_CPU_OR_INPUT_BLOCKED",
        "gpu_execution_authorized_by_cpu_gate": bool(passed),
    }
    written = _strict_write(output_path, report)
    report["output_path"] = written.relative_to(ROOT).as_posix()
    report["output_sha256"] = _sha256_path(written)
    return report


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--initial-worktree-record", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    report = qualify_cpu(output_path=args.output, initial_worktree_path=args.initial_worktree_record)
    print(json.dumps({"status": report["status"], "output_path": report["output_path"], "output_sha256": report["output_sha256"]}, sort_keys=True))
    return 0 if report["gpu_execution_authorized_by_cpu_gate"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
