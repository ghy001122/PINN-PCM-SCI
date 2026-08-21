"""Small paired raw-time/identity/KC development pilot on the Q-POP equations."""

from __future__ import annotations

import argparse
import copy
import json
import math
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
from typing import Any, Mapping, Sequence

import numpy as np
import torch

from .artifacts import CaseArtifact, PredictionArtifact
from .ledger import ExperimentLedger, RunManifest
from .qpop_physics import QPopParameters, fermi
from .qpop_pinn import (
    PHA_METHODS,
    QPopPINN,
    boundary_residuals,
    evaluate_fields,
    initial_residuals,
    interior_residuals,
    normalized_residual_loss,
    residual_scales,
)


METHODS = ("raw", "identity", "kc")


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _write_json_once(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    with temporary.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


class PilotBatches:
    def __init__(
        self,
        *,
        interior: torch.Tensor,
        initial: torch.Tensor,
        boundaries: Mapping[str, torch.Tensor],
    ) -> None:
        self.interior = interior
        self.initial = initial
        self.boundaries = dict(boundaries)

    @classmethod
    def fixed(
        cls,
        *,
        seed: int,
        interior: int,
        initial: int,
        boundary_per_side: int,
    ) -> "PilotBatches":
        generator = torch.Generator().manual_seed(seed)
        interior_coordinates = torch.rand(
            (interior, 3), generator=generator, dtype=torch.float64
        )
        initial_coordinates = torch.rand(
            (initial, 2), generator=generator, dtype=torch.float64
        )
        boundaries: dict[str, torch.Tensor] = {}
        for side in ("left", "right", "bottom", "top"):
            coordinates = torch.rand(
                (boundary_per_side, 3), generator=generator, dtype=torch.float64
            )
            if side == "left":
                coordinates[:, 0] = 0.0
            elif side == "right":
                coordinates[:, 0] = 1.0
            elif side == "bottom":
                coordinates[:, 1] = 0.0
            else:
                coordinates[:, 1] = 1.0
            boundaries[side] = coordinates
        return cls(
            interior=interior_coordinates,
            initial=initial_coordinates,
            boundaries=boundaries,
        )


def training_batches(
    model: QPopPINN,
    *,
    seed: int,
    interior: int,
    initial: int,
    boundary_per_side: int,
    candidate_multiplier: int = 4,
) -> tuple[PilotBatches, dict[str, Any]]:
    """Build paired batches and expose the PHA sampling decision as an audit."""

    if candidate_multiplier < 1:
        raise ValueError("candidate multiplier must be positive")
    candidate_count = (
        interior * candidate_multiplier if model.method in PHA_METHODS else interior
    )
    generated = PilotBatches.fixed(
        seed=seed,
        interior=candidate_count,
        initial=initial,
        boundary_per_side=boundary_per_side,
    )
    if model.method not in PHA_METHODS:
        return generated, {
            "candidate_count": candidate_count,
            "selected_count": interior,
            "gate_adaptive": False,
            "candidate_gate_mean": None,
            "selected_gate_mean": None,
        }
    with torch.no_grad():
        physical_gate = model.phase_hotspot_diagnostics(
            generated.interior
        ).physical_gate[:, 0]
    if model.method in {"pha_sampling", "pha_shared"}:
        selected = model.select_interior(generated.interior, count=interior)
        selected_indices = torch.topk(
            model.collocation_weights(generated.interior)[:, 0],
            k=interior,
            largest=True,
            sorted=True,
        ).indices
        gate_adaptive = True
    else:
        selected_indices = torch.arange(interior)
        selected = generated.interior[selected_indices]
        gate_adaptive = False
    return (
        PilotBatches(
            interior=selected,
            initial=generated.initial,
            boundaries=generated.boundaries,
        ),
        {
            "candidate_count": candidate_count,
            "selected_count": interior,
            "gate_adaptive": gate_adaptive,
            "candidate_gate_mean": float(physical_gate.mean()),
            "selected_gate_mean": float(physical_gate[selected_indices].mean()),
        },
    )


def _all_residuals(model: QPopPINN, batches: PilotBatches) -> dict[str, torch.Tensor]:
    residuals = {
        f"interior/{name}": value
        for name, value in interior_residuals(model, batches.interior).items()
    }
    residuals.update(
        {
            f"initial/{name}": value
            for name, value in initial_residuals(model, batches.initial).items()
        }
    )
    for side, coordinates in batches.boundaries.items():
        residuals.update(
            {
                f"boundary/{side}/{name}": value
                for name, value in boundary_residuals(
                    model, coordinates, side=side
                ).items()
            }
        )
    return residuals


def _subset(
    residuals: Mapping[str, torch.Tensor], prefix: str
) -> dict[str, torch.Tensor]:
    return {
        name: value for name, value in residuals.items() if name.startswith(prefix)
    }


def pilot_loss(
    model: QPopPINN,
    batches: PilotBatches,
    *,
    stop_gradient_clock_target: bool,
    scales: Mapping[str, float] | None = None,
) -> tuple[torch.Tensor, dict[str, torch.Tensor]]:
    residuals = _all_residuals(model, batches)
    components = {
        "interior": normalized_residual_loss(
            _subset(residuals, "interior/"), scales
        ),
        "initial": normalized_residual_loss(_subset(residuals, "initial/"), scales),
        "boundary": normalized_residual_loss(
            _subset(residuals, "boundary/"), scales
        ),
    }
    if model.method == "kc":
        bundle = evaluate_fields(model, batches.interior)
        p = model.parameters_contract
        physical_xy = torch.stack(
            [
                bundle.coordinates[:, 0] * p.lx,
                bundle.coordinates[:, 1] * p.ly,
            ],
            dim=1,
        )
        tcvar = p.tc_variance(physical_xy).unsqueeze(1)
        force = torch.abs(
            2.0
            * p.structural_mobility
            * p.dfb_deta(
                bundle.values["temperature"],
                bundle.values["eta"],
                bundle.values["mu"],
                tcvar,
            )
        )
        denominator = torch.mean(force.detach()).clamp_min(1.0e-12)
        target = 0.1 + force / denominator
        if stop_gradient_clock_target:
            target = target.detach()
        predicted = model.clock.rate(bundle.coordinates)
        components["clock_alignment"] = torch.mean((predicted - target).square())
    else:
        components["clock_alignment"] = torch.zeros(
            (), dtype=batches.interior.dtype, device=batches.interior.device
        )
    total = (
        components["interior"]
        + components["initial"]
        + components["boundary"]
        + 0.05 * components["clock_alignment"]
    )
    return total, components


def _audit_score(
    model: QPopPINN,
    batches: PilotBatches,
    scales: Mapping[str, float],
) -> tuple[float, float, dict[str, float]]:
    residuals = _all_residuals(model, batches)
    normalized = {
        name: float(
            torch.sqrt(torch.mean(value.detach().square())).cpu()
            / max(float(scales[name]), 1.0e-12)
        )
        for name, value in residuals.items()
    }
    return max(normalized.values()), sum(normalized.values()), normalized


def _train_method(
    *,
    model: QPopPINN,
    seed: int,
    updates: int,
    scales: Mapping[str, float],
    audit_batches: PilotBatches,
    stop_gradient_clock_target: bool = True,
) -> dict[str, Any]:
    optimizer = torch.optim.Adam(model.parameters(), lr=1.0e-4)
    initial_maximum, initial_total, _ = _audit_score(model, audit_batches, scales)
    history: list[dict[str, Any]] = [
        {
            "step": 0,
            "training_loss": None,
            "components": {},
            "physics_audit_max": initial_maximum,
            "physics_audit_sum": initial_total,
        }
    ]
    best_score = (initial_maximum, initial_total)
    best_state: dict[str, Any] | None = copy.deepcopy(model.state_dict())
    started = time.monotonic()
    audit_every = max(1, updates // 5)
    for step in range(updates):
        batches, sampling_audit = training_batches(
            model,
            seed=seed + step,
            interior=8,
            initial=4,
            boundary_per_side=3,
        )
        optimizer.zero_grad(set_to_none=True)
        loss, components = pilot_loss(
            model,
            batches,
            stop_gradient_clock_target=stop_gradient_clock_target,
            scales=scales,
        )
        if not torch.isfinite(loss):
            raise RuntimeError(f"{model.method} produced a non-finite pilot loss")
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 10.0)
        optimizer.step()
        if step == 0 or (step + 1) % audit_every == 0 or step + 1 == updates:
            maximum, total, detail = _audit_score(model, audit_batches, scales)
            record = {
                "step": step + 1,
                "training_loss": float(loss.detach()),
                "components": {
                    name: float(value.detach()) for name, value in components.items()
                },
                "physics_audit_max": maximum,
                "physics_audit_sum": total,
                "sampling_audit": sampling_audit,
            }
            history.append(record)
            if (maximum, total) < best_score:
                best_score = (maximum, total)
                best_state = copy.deepcopy(model.state_dict())
    if best_state is None:
        raise RuntimeError("pilot checkpoint selector found no finite checkpoint")
    model.load_state_dict(best_state)
    return {
        "history": history,
        "checkpoint_score": {
            "max_normalized_violation": best_score[0],
            "sum_normalized_violation": best_score[1],
        },
        "wall_seconds": time.monotonic() - started,
    }


def _train_kc_with_identity_warmup(
    *,
    model: QPopPINN,
    seed: int,
    updates: int,
    warmup_updates: int,
    scales: Mapping[str, float],
    audit_batches: PilotBatches,
    stop_gradient_clock_target: bool,
) -> dict[str, Any]:
    if not 0 < warmup_updates < updates:
        raise ValueError("identity warm-up must be positive and smaller than total updates")
    warmup = QPopPINN(
        parameters=model.parameters_contract,
        horizon_ns=model.horizon_ns,
        method="identity",
        hidden_width=24,
        hidden_layers=3,
    ).double()
    warmup.eta_model.load_state_dict(model.eta_model.state_dict())
    warmup.physical_model.load_state_dict(model.physical_model.state_dict())
    first = _train_method(
        model=warmup,
        seed=seed,
        updates=warmup_updates,
        scales=scales,
        audit_batches=audit_batches,
        stop_gradient_clock_target=True,
    )
    model.eta_model.load_state_dict(warmup.eta_model.state_dict())
    model.physical_model.load_state_dict(warmup.physical_model.state_dict())
    second = _train_method(
        model=model,
        seed=seed + warmup_updates,
        updates=updates - warmup_updates,
        scales=scales,
        audit_batches=audit_batches,
        stop_gradient_clock_target=stop_gradient_clock_target,
    )
    history: list[dict[str, Any]] = []
    for record in first["history"]:
        history.append({**record, "phase": "identity_warmup", "total_step": record["step"]})
    for record in second["history"]:
        history.append(
            {
                **record,
                "phase": "learned_clock",
                "total_step": warmup_updates + record["step"],
            }
        )
    return {
        "history": history,
        "checkpoint_score": second["checkpoint_score"],
        "wall_seconds": first["wall_seconds"] + second["wall_seconds"],
        "protocol": {
            "warmup_updates": warmup_updates,
            "learned_clock_updates": updates - warmup_updates,
            "clock_gradient": "stop" if stop_gradient_clock_target else "full",
        },
    }


def _predict_fields(
    model: QPopPINN, oracle: CaseArtifact, *, batch_size: int = 8192
) -> dict[str, np.ndarray]:
    node_coordinates = torch.as_tensor(oracle.nodes, dtype=torch.float64)
    chunks: dict[str, list[np.ndarray]] = {
        name: [] for name in oracle.fields
    }
    p = model.parameters_contract
    model.eval()
    with torch.no_grad():
        for field_time in oracle.field_time:
            normalized_time = float(field_time) / model.horizon_ns
            per_time: dict[str, list[np.ndarray]] = {name: [] for name in chunks}
            for start in range(0, node_coordinates.shape[0], batch_size):
                xy = node_coordinates[start : start + batch_size]
                q = torch.cat(
                    [
                        xy[:, 0:1] / p.lx,
                        xy[:, 1:2] / p.ly,
                        torch.full(
                            (xy.shape[0], 1),
                            normalized_time,
                            dtype=torch.float64,
                        ),
                    ],
                    dim=1,
                )
                values = model(q)
                decoded = {
                    "eta": values[:, 0],
                    "psi": values[:, 1],
                    "electron_occupancy": p.electron_density_of_states
                    * fermi(values[:, 2])
                    * p.unit_cell_volume,
                    "hole_occupancy": p.hole_density_of_states
                    * fermi(values[:, 3])
                    * p.unit_cell_volume,
                    "electric_potential": values[:, 4] * 1.0e-3,
                    "temperature": values[:, 5] * 338.0,
                }
                for name in per_time:
                    per_time[name].append(decoded[name].cpu().numpy())
            for name in chunks:
                chunks[name].append(np.concatenate(per_time[name]))
    return {name: np.stack(values) for name, values in chunks.items()}


def _predict_circuit(model: QPopPINN, oracle: CaseArtifact) -> dict[str, np.ndarray]:
    p = model.parameters_contract
    x = torch.linspace(0.0, 1.0, 32, dtype=torch.float64)
    voltage: list[float] = []
    resistance: list[float] = []
    model.eval()
    with torch.no_grad():
        for value in oracle.circuit_time:
            q = torch.stack(
                [x, torch.zeros_like(x), torch.full_like(x, float(value) / model.horizon_ns)],
                dim=1,
            )
            fields = model(q)
            physical_voltage = float(torch.mean(fields[:, 4])) * 1.0e-3
            physical_current = float(torch.mean(fields[:, 6])) * (
                (1.3806504e-23 * 338.0 / 1.0e-3) / 1.0e-9
            )
            voltage.append(physical_voltage)
            resistance.append(
                abs(physical_voltage / physical_current)
                if abs(physical_current) > 1.0e-30
                else 1.0e30
            )
    return {
        "qpop_cpc_v1_reported_voltage_drop": np.asarray(voltage, dtype=np.float64),
        "qpop_cpc_v1_reported_resistance": np.asarray(resistance, dtype=np.float64),
    }


def _write_prediction(
    *, model: QPopPINN, oracle: CaseArtifact, method_id: str, path: Path
) -> None:
    prediction = PredictionArtifact(
        case_id=oracle.case_id,
        physical_contract_id=oracle.physical_contract_id,
        method_id=method_id,
        checkpoint_id="oracle-blind-physics-audit-best",
        mesh_identity=oracle.mesh_identity,
        field_time=oracle.field_time,
        circuit_time=oracle.circuit_time,
        time_unit=oracle.time_unit,
        fields=_predict_fields(model, oracle),
        field_units=oracle.field_units,
        field_registry=oracle.field_registry,
        circuit=_predict_circuit(model, oracle),
        circuit_units=oracle.circuit_units,
    )
    prediction.write(path)
    PredictionArtifact.read(path)


def run_development_pilot(
    *,
    run_id: str,
    oracle_path: Path,
    input_path: Path,
    split_path: Path,
    metric_spec_path: Path,
    output_root: Path,
    experiment_root: Path,
    seed: int,
    updates: int,
    supersedes: str | None = None,
    methods: tuple[str, ...] = METHODS,
    clock_gradient_mode: str = "stop",
    kc_warmup_updates: int = 0,
    baseline_run_root: Path | None = None,
) -> int:
    if not methods or any(method not in METHODS for method in methods):
        raise ValueError("pilot methods must be a non-empty subset of raw, identity, kc")
    if "kc" not in methods:
        raise ValueError("development protocol pilot must retain a kc arm")
    if "raw" not in methods and baseline_run_root is None:
        raise ValueError("a KC-only protocol arm requires a frozen raw baseline run")
    if clock_gradient_mode not in {"stop", "full"}:
        raise ValueError("clock gradient mode must be stop or full")
    if kc_warmup_updates < 0 or kc_warmup_updates >= updates:
        raise ValueError("KC warm-up updates must be non-negative and below total updates")
    started_at = _utc_now()
    started = time.monotonic()
    run_root = output_root / run_id
    run_root.mkdir(parents=True, exist_ok=False)
    intent_path = experiment_root / "intents" / f"{run_id}.json"
    _write_json_once(
        intent_path,
        {
            "schema_version": "qpop-method-development-pilot-intent-v1",
            "run_id": run_id,
            "tier": "pilot",
            "scientific_role": "protocol_selection",
            "gate": "G6",
            "methods": list(methods),
            "seed": seed,
            "updates_per_method": updates,
            "clock_gradient_mode": clock_gradient_mode,
            "kc_warmup_updates": kc_warmup_updates,
            "baseline_run_root": None if baseline_run_root is None else str(baseline_run_root),
            "supersedes": supersedes,
            "training_uses_qpop_transient_labels": False,
            "claim_status": "NO_SCIENTIFIC_CLAIMS_UNQUALIFIED_ORACLE",
            "started_at": started_at,
        },
    )
    failure: Exception | None = None
    metrics_by_method: dict[str, dict[str, Any]] = {}
    training_by_method: dict[str, dict[str, Any]] = {}
    artifact_paths: dict[str, str] = {"intent": str(intent_path)}
    try:
        oracle = CaseArtifact.read(oracle_path)
        parameters = QPopParameters.from_input(input_path)
        horizon = max(float(oracle.field_time[-1]), float(oracle.circuit_time[-1]))
        torch.manual_seed(seed)
        raw = QPopPINN(
            parameters=parameters,
            horizon_ns=horizon,
            method="raw",
            hidden_width=24,
            hidden_layers=3,
        ).double()
        kc = QPopPINN(
            parameters=parameters,
            horizon_ns=horizon,
            method="kc",
            hidden_width=24,
            hidden_layers=3,
        ).double()
        kc.eta_model.load_state_dict(raw.eta_model.state_dict())
        kc.physical_model.load_state_dict(raw.physical_model.state_dict())
        models: dict[str, QPopPINN] = {"raw": raw, "kc": kc}
        if "identity" in methods:
            identity = QPopPINN(
                parameters=parameters,
                horizon_ns=horizon,
                method="identity",
                hidden_width=24,
                hidden_layers=3,
            ).double()
            identity.eta_model.load_state_dict(raw.eta_model.state_dict())
            identity.physical_model.load_state_dict(raw.physical_model.state_dict())
            models["identity"] = identity
        models = {method: models[method] for method in methods}
        audit_batches = PilotBatches.fixed(
            seed=seed + 100000,
            interior=12,
            initial=8,
            boundary_per_side=5,
        )
        shared_scales = residual_scales(_all_residuals(raw, audit_batches))
        if "raw" not in models:
            assert baseline_run_root is not None
            baseline_metrics_path = baseline_run_root / "metrics-raw.json"
            baseline_summary_path = baseline_run_root / "pilot_summary.json"
            metrics_by_method["raw"] = json.loads(
                baseline_metrics_path.read_text(encoding="utf-8")
            )
            artifact_paths["baseline_raw_metrics"] = str(baseline_metrics_path)
            artifact_paths["baseline_run_summary"] = str(baseline_summary_path)
        for method, model in models.items():
            if method == "kc" and kc_warmup_updates:
                training = _train_kc_with_identity_warmup(
                    model=model,
                    seed=seed,
                    updates=updates,
                    warmup_updates=kc_warmup_updates,
                    scales=shared_scales,
                    audit_batches=audit_batches,
                    stop_gradient_clock_target=clock_gradient_mode == "stop",
                )
            else:
                training = _train_method(
                    model=model,
                    seed=seed,
                    updates=updates,
                    scales=shared_scales,
                    audit_batches=audit_batches,
                    stop_gradient_clock_target=clock_gradient_mode == "stop",
                )
            training_by_method[method] = training
            checkpoint_path = run_root / f"checkpoint-{method}.pt"
            torch.save(model.state_dict(), checkpoint_path)
            history_path = run_root / f"training-{method}.json"
            _write_json_once(history_path, training)
            prediction_path = run_root / f"prediction-{method}.h5"
            _write_prediction(
                model=model,
                oracle=oracle,
                method_id=(
                    f"qpop-{method}-{clock_gradient_mode}-"
                    f"{'identity-warmup' if method == 'kc' and kc_warmup_updates else 'joint'}-development-pilot-v1"
                ),
                path=prediction_path,
            )
            metrics_path = run_root / f"metrics-{method}.json"
            stdout_path = run_root / f"evaluator-{method}.stdout.log"
            stderr_path = run_root / f"evaluator-{method}.stderr.log"
            command = [
                sys.executable,
                "-m",
                "pinn_pcm_sci.evaluate",
                "--prediction",
                str(prediction_path),
                "--oracle",
                str(oracle_path),
                "--split",
                str(split_path),
                "--metric-spec",
                str(metric_spec_path),
                "--out",
                str(metrics_path),
            ]
            with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
                completed = subprocess.run(
                    command, stdout=stdout, stderr=stderr, timeout=300, check=False
                )
            if completed.returncode != 0:
                raise RuntimeError(
                    f"independent evaluator failed for {method} with {completed.returncode}"
                )
            metrics_by_method[method] = json.loads(
                metrics_path.read_text(encoding="utf-8")
            )
            artifact_paths.update(
                {
                    f"checkpoint_{method}": str(checkpoint_path),
                    f"training_{method}": str(history_path),
                    f"prediction_{method}": str(prediction_path),
                    f"metrics_{method}": str(metrics_path),
                }
            )
        if "identity" in models:
            raw_identity_delta = max(
                abs(
                    metrics_by_method["raw"][metric]
                    - metrics_by_method["identity"][metric]
                )
                for metric in (
                    "structure_symmetric_difference_cycle_equal",
                    "device_trajectory_nrmse",
                )
            )
            if raw_identity_delta > 1.0e-12:
                raise RuntimeError("raw and identity controls diverged under the paired protocol")
    except Exception as exc:
        failure = exc

    kc_signal = False
    if failure is None:
        kc_signal = (
            metrics_by_method["kc"]["structure_symmetric_difference_cycle_equal"]
            < metrics_by_method["raw"]["structure_symmetric_difference_cycle_equal"]
            and metrics_by_method["kc"]["device_trajectory_nrmse"]
            <= metrics_by_method["raw"]["device_trajectory_nrmse"]
        )
    summary_path = run_root / "pilot_summary.json"
    _write_json_once(
        summary_path,
        {
            "schema_version": "qpop-method-development-pilot-summary-v1",
            "metrics": metrics_by_method,
            "training": training_by_method,
            "kc_signal_detected": kc_signal,
            "oracle_qualification": "UNQUALIFIED",
            "scientific_use": "DEVELOPMENT_ONLY",
            "failure": None if failure is None else str(failure),
        },
    )
    artifact_paths["summary"] = str(summary_path)
    manifest = RunManifest(
        run_id=run_id,
        experiment_group_id="g6-qpop-raw-identity-kc-development-pilot-v1",
        tier="pilot",
        scientific_role="protocol_selection",
        gate="G6",
        started_at=started_at,
        ended_at=_utc_now(),
        command=["python", "-m", "pinn_pcm_sci.qpop_method_pilot"],
        execution_status="FAILED" if failure else "COMPLETED",
        numerical_validity="NOT_EVALUATED" if failure else "VALID_DEVELOPMENT_PILOT",
        gate_outcome=(
            "G6_DEVELOPMENT_PILOT_FAILED"
            if failure
            else (
                "DEVELOPMENT_KC_SIGNAL_PRESENT"
                if kc_signal
                else "DEVELOPMENT_KC_SIGNAL_NOT_DETECTED"
            )
        ),
        route_disposition=(
            "BLOCKED_ENGINEERING"
            if failure
            else "CONTINUE_G3_G6_DEVELOPMENT_ONLY"
        ),
        evidence_identity="QPOP_CPC_V1_BUNDLED_REFERENCE_UNQUALIFIED",
        claim_status="NO_SCIENTIFIC_CLAIMS_UNQUALIFIED_ORACLE",
        code_identity={"kind": "working-tree", "dirty": True},
        environment={
            "python": platform.python_version(),
            "torch": torch.__version__,
            "dtype": "float64",
            "device": "cpu",
        },
        physical_contract_id="PROVISIONAL_G3_QPOP_CPC_V1_IMT_CONTRACT",
        split_id="qpop-cpc-v1-bundled-reference-development-only-v1",
        method_id=(
            f"paired-{'-'.join(methods)}-qpop-full-physics-"
            f"{clock_gradient_mode}-"
            f"{'identity-warmup' if kc_warmup_updates else 'joint'}-pilot-v1"
        ),
        case_id="qpop-cpc-v1-imt-intrinsic-voltage-osc-bundled-reference-through-512.0793ns",
        seed=seed,
        planned_budget={"methods": len(methods), "optimizer_updates_per_method": updates},
        actual_budget={
            "optimizer_updates": 0 if failure else len(methods) * updates,
            "wall_seconds": time.monotonic() - started,
            "training": training_by_method,
        },
        checkpoint={
            "id": "oracle-blind-physics-audit-best",
            "selection": "max normalized raw physics violation, then sum",
        },
        evaluator_id="frozen-project-development-evaluator-qpop-reference-v1",
        artifacts=artifact_paths,
        failure_class=None if failure is None else type(failure).__name__,
        replay_of=None,
        supersedes=supersedes,
    )
    ledger = ExperimentLedger(experiment_root)
    ledger.record(manifest)
    ledger.validate()
    if failure is not None:
        raise failure
    return 0


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--oracle", type=Path, required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--split", type=Path, required=True)
    parser.add_argument("--metric-spec", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, default=Path("outputs/runs"))
    parser.add_argument("--experiment-root", type=Path, default=Path("docs/experiment"))
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--updates", type=int, default=40)
    parser.add_argument("--supersedes")
    parser.add_argument("--methods", default="raw,identity,kc")
    parser.add_argument("--clock-gradient-mode", choices=("stop", "full"), default="stop")
    parser.add_argument("--kc-warmup-updates", type=int, default=0)
    parser.add_argument("--baseline-run-root", type=Path)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    methods = tuple(part.strip() for part in args.methods.split(",") if part.strip())
    return run_development_pilot(
        run_id=args.run_id,
        oracle_path=args.oracle,
        input_path=args.input,
        split_path=args.split,
        metric_spec_path=args.metric_spec,
        output_root=args.output_root,
        experiment_root=args.experiment_root,
        seed=args.seed,
        updates=args.updates,
        supersedes=args.supersedes,
        methods=methods,
        clock_gradient_mode=args.clock_gradient_mode,
        kc_warmup_updates=args.kc_warmup_updates,
        baseline_run_root=args.baseline_run_root,
    )


if __name__ == "__main__":
    raise SystemExit(main())
