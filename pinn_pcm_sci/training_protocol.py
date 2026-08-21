"""Training protocol seam for bounded Q-POP PINN development runs."""

from __future__ import annotations

import copy
from dataclasses import dataclass
import hashlib
import math
import time
from typing import Any, Mapping, Sequence

import numpy as np
import torch

from .qpop_pinn import (
    QPopPINN,
    boundary_residuals,
    initial_residuals,
    interior_residuals,
)


_AGGREGATIONS = {"grouped_mean", "smooth_max"}
_TEMPORAL_SCHEDULES = {"joint", "four_prefix_warmup"}


def phase_fraction_dynamic_range(
    eta: np.ndarray,
    field_time: np.ndarray,
    *,
    threshold: float,
    analysis_end_ns: float = 494.0,
) -> float:
    eta_values = np.asarray(eta, dtype=np.float64)
    times = np.asarray(field_time, dtype=np.float64)
    if eta_values.ndim != 2 or times.ndim != 1:
        raise ValueError("eta and field time must be a time-by-node field and a vector")
    if eta_values.shape[0] != times.size:
        raise ValueError("eta and field time lengths do not match")
    selected = times <= analysis_end_ns
    if not np.any(selected):
        raise ValueError("analysis window contains no structure snapshots")
    values = eta_values[selected]
    if not np.isfinite(values).all() or not np.isfinite(times[selected]).all():
        raise ValueError("structure event diagnostic requires finite data")
    fractions = np.mean(values >= threshold, axis=1)
    return float(np.max(fractions) - np.min(fractions))


def select_sparse_anchor_indices(
    field_time: np.ndarray,
    *,
    node_count: int,
    sample_count: int,
    seed: int = 17,
    target_times_ns: Sequence[float] = (130.0, 260.0, 390.0, 494.0),
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    """Freeze the N2 snapshot and node indices without inspecting model output."""
    times = np.asarray(field_time, dtype=np.float64)
    if times.ndim != 1 or times.size == 0 or not np.all(np.isfinite(times)):
        raise ValueError("field time must be a non-empty finite vector")
    if np.any(np.diff(times) < 0.0):
        raise ValueError("field time must be monotone")
    if node_count <= 0 or sample_count <= 0 or sample_count > node_count:
        raise ValueError("anchor node counts are invalid")
    targets = np.asarray(target_times_ns, dtype=np.float64)
    if targets.ndim != 1 or targets.size == 0 or not np.all(np.isfinite(targets)):
        raise ValueError("anchor target times must be a non-empty finite vector")

    time_indices = tuple(int(np.argmin(np.abs(times - target))) for target in targets)
    generator = np.random.default_rng(seed)
    node_indices = tuple(
        sorted(int(index) for index in generator.choice(node_count, sample_count, replace=False))
    )
    return time_indices, node_indices


@dataclass(frozen=True)
class EventCompetenceReport:
    selected_step: int
    phase_fraction_range: float
    structure_error: float
    device_nrmse: float
    physics_audit_max: float
    passed: bool
    gate_outcome: str
    failure_reasons: tuple[str, ...]

    @classmethod
    def adjudicate(
        cls,
        *,
        selected_step: int,
        phase_fraction_range: float,
        structure_error: float,
        device_nrmse: float,
        physics_audit_max: float,
    ) -> "EventCompetenceReport":
        values = (
            phase_fraction_range,
            structure_error,
            device_nrmse,
            physics_audit_max,
        )
        reasons: list[str] = []
        if not all(math.isfinite(value) for value in values):
            reasons.append("NONFINITE_RESULT")
        if selected_step <= 0:
            reasons.append("INITIAL_CHECKPOINT_SELECTED")
        if phase_fraction_range < 0.05:
            reasons.append("PHASE_FRACTION_RANGE_BELOW_MINIMUM")
        if structure_error > 0.2190643041:
            reasons.append("STRUCTURE_ERROR_ABOVE_MAXIMUM")
        if physics_audit_max > 1.0483889664:
            reasons.append("PHYSICS_AUDIT_NONINFERIORITY_FAILED")
        if device_nrmse > 1.0427065837:
            reasons.append("DEVICE_NRMSE_NONINFERIORITY_FAILED")
        passed = not reasons
        return cls(
            selected_step=selected_step,
            phase_fraction_range=phase_fraction_range,
            structure_error=structure_error,
            device_nrmse=device_nrmse,
            physics_audit_max=physics_audit_max,
            passed=passed,
            gate_outcome="RAW_EVENT_RESOLVED" if passed else "RAW_EVENT_NOT_RESOLVED",
            failure_reasons=tuple(reasons),
        )


@dataclass(frozen=True)
class AnchorDiagnosticReport:
    phase_fraction_range: float
    structure_error: float
    physics_audit_max: float
    gate_outcome: str
    route_disposition: str = "CLOSE_QPOP_PINN_CONTINUE_N3B_REDUCED_ORACLE"

    @classmethod
    def adjudicate(
        cls,
        *,
        phase_fraction_range: float,
        structure_error: float,
        physics_audit_max: float,
    ) -> "AnchorDiagnosticReport":
        values = (phase_fraction_range, structure_error, physics_audit_max)
        event_resolved = bool(
            all(math.isfinite(value) for value in values)
            and phase_fraction_range >= 0.05
            and structure_error <= 0.2190643041
        )
        physics_valid = bool(
            math.isfinite(physics_audit_max) and physics_audit_max <= 1.25
        )
        if event_resolved and physics_valid:
            outcome = "OPTIMIZATION_BOTTLENECK_CONFIRMED"
        elif event_resolved:
            outcome = "PHYSICS_CONSTRAINT_TENSION"
        else:
            outcome = "REPRESENTATION_OR_RESIDUAL_BOTTLENECK"
        return cls(
            phase_fraction_range=phase_fraction_range,
            structure_error=structure_error,
            physics_audit_max=physics_audit_max,
            gate_outcome=outcome,
        )


def select_screen_protocol(
    reports: Mapping[str, Mapping[str, Any]],
    *,
    tie_tolerance: float = 0.001,
) -> str:
    if tie_tolerance < 0.0:
        raise ValueError("screen tie tolerance must be non-negative")
    valid = {
        protocol_id: float(report["structure_error"])
        for protocol_id, report in reports.items()
        if bool(report.get("valid"))
        and math.isfinite(float(report["structure_error"]))
    }
    if not valid:
        raise ValueError("raw protocol screen found no numerically valid arm")
    best_error = min(valid.values())
    preferred = "r4-smooth-causal"
    if preferred in valid and valid[preferred] <= best_error + tie_tolerance:
        return preferred
    return min(valid, key=lambda protocol_id: (valid[protocol_id], protocol_id))


def select_anchor_checkpoint(
    records: Sequence[Mapping[str, Any]],
    *,
    physics_ceiling: float = 1.25,
) -> Mapping[str, Any]:
    admissible = [
        record
        for record in records
        if math.isfinite(float(record["physics_audit_max"]))
        and math.isfinite(float(record["physics_audit_sum"]))
        and math.isfinite(float(record["anchor_loss"]))
        and float(record["physics_audit_max"]) <= physics_ceiling
    ]
    if not admissible:
        raise ValueError("anchor diagnostic found no physics-admissible checkpoint")
    return min(
        admissible,
        key=lambda record: (
            float(record["anchor_loss"]),
            float(record["physics_audit_max"]),
            float(record["physics_audit_sum"]),
            int(record["step"]),
        ),
    )


@dataclass(frozen=True)
class TrainingProtocol:
    """Frozen optimizer behavior shared by raw-time development arms."""

    protocol_id: str
    aggregation: str
    temporal_schedule: str
    smooth_max_tau: float = 0.1
    warmup_updates: int = 200
    time_prefixes_ns: tuple[float, ...] = (130.0, 260.0, 390.0, 494.0)
    interior_points: int = 64
    initial_points: int = 32
    boundary_points_per_side: int = 16
    audit_interior_points: int = 128
    audit_initial_points: int = 64
    audit_boundary_points_per_side: int = 32
    learning_rate: float = 1.0e-4
    gradient_clip: float = 10.0

    def __post_init__(self) -> None:
        if not self.protocol_id:
            raise ValueError("training protocol id must be non-empty")
        if self.aggregation not in _AGGREGATIONS:
            raise ValueError("unsupported residual aggregation")
        if self.temporal_schedule not in _TEMPORAL_SCHEDULES:
            raise ValueError("unsupported temporal schedule")
        if self.smooth_max_tau <= 0.0:
            raise ValueError("smooth-max temperature must be positive")
        if self.warmup_updates <= 0 or self.warmup_updates % len(self.time_prefixes_ns):
            raise ValueError("warm-up updates must divide evenly across time prefixes")
        if any(
            right <= left
            for left, right in zip(self.time_prefixes_ns, self.time_prefixes_ns[1:])
        ):
            raise ValueError("time prefixes must be strictly increasing")
        counts = (
            self.interior_points,
            self.initial_points,
            self.boundary_points_per_side,
            self.audit_interior_points,
            self.audit_initial_points,
            self.audit_boundary_points_per_side,
        )
        if any(count <= 0 for count in counts):
            raise ValueError("training and audit batch sizes must be positive")
        if self.learning_rate <= 0.0 or self.gradient_clip <= 0.0:
            raise ValueError("optimizer controls must be positive")

    def time_ceiling_ns(self, update_index: int) -> float:
        if update_index < 0:
            raise ValueError("update index must be non-negative")
        if self.temporal_schedule == "joint" or update_index >= self.warmup_updates:
            return self.time_prefixes_ns[-1]
        updates_per_prefix = self.warmup_updates // len(self.time_prefixes_ns)
        prefix_index = min(update_index // updates_per_prefix, len(self.time_prefixes_ns) - 1)
        return self.time_prefixes_ns[prefix_index]

    def apply_time_support(
        self,
        coordinates: torch.Tensor,
        *,
        update_index: int,
        model_horizon_ns: float,
    ) -> torch.Tensor:
        if coordinates.ndim != 2 or coordinates.shape[1] != 3:
            raise ValueError("collocation coordinates must have x, y, and normalized time")
        ceiling = self.time_ceiling_ns(update_index)
        if model_horizon_ns < ceiling:
            raise ValueError("model horizon is shorter than the registered analysis window")
        limited = coordinates.clone()
        limited[:, 2] = limited[:, 2] * (ceiling / model_horizon_ns)
        return limited

    def select_checkpoint(
        self, records: Sequence[Mapping[str, Any]]
    ) -> Mapping[str, Any]:
        finite = [
            record
            for record in records
            if int(record["step"]) > 0
            and math.isfinite(float(record["physics_audit_max"]))
            and math.isfinite(float(record["physics_audit_sum"]))
        ]
        if not finite:
            raise ValueError(
                "checkpoint selection requires a finite non-initial physics audit"
            )
        return min(
            finite,
            key=lambda record: (
                float(record["physics_audit_max"]),
                float(record["physics_audit_sum"]),
                int(record["step"]),
            ),
        )

    def objective(
        self,
        residuals: Mapping[str, torch.Tensor],
        scales: Mapping[str, float],
    ) -> torch.Tensor:
        if not residuals:
            raise ValueError("training objective requires residuals")
        normalized_losses: dict[str, torch.Tensor] = {}
        for name, residual in residuals.items():
            if name not in scales:
                raise ValueError(f"missing frozen scale for residual {name}")
            scale = torch.as_tensor(
                max(float(scales[name]), 1.0e-12),
                dtype=residual.dtype,
                device=residual.device,
            )
            normalized_losses[name] = torch.mean((residual / scale).square())

        if self.aggregation == "smooth_max":
            values = torch.stack(list(normalized_losses.values()))
            tau = torch.as_tensor(
                self.smooth_max_tau, dtype=values.dtype, device=values.device
            )
            return tau * (
                torch.logsumexp(values / tau, dim=0)
                - torch.log(torch.as_tensor(values.numel(), dtype=values.dtype, device=values.device))
            )

        grouped: list[torch.Tensor] = []
        for prefix in ("interior/", "initial/", "boundary/"):
            members = [
                value
                for name, value in normalized_losses.items()
                if name.startswith(prefix)
            ]
            if members:
                grouped.append(torch.stack(members).mean())
        if not grouped:
            raise ValueError("grouped objective found no physics, initial, or boundary residuals")
        return torch.stack(grouped).sum()


@dataclass(frozen=True)
class TrainingBatches:
    interior: torch.Tensor
    initial: torch.Tensor
    boundaries: Mapping[str, torch.Tensor]

    @classmethod
    def fixed(
        cls,
        *,
        seed: int,
        interior: int,
        initial: int,
        boundary_per_side: int,
    ) -> "TrainingBatches":
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
                (boundary_per_side, 3),
                generator=generator,
                dtype=torch.float64,
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
        return cls(interior_coordinates, initial_coordinates, boundaries)

    def with_time_support(
        self,
        protocol: TrainingProtocol,
        *,
        update_index: int,
        model_horizon_ns: float,
    ) -> "TrainingBatches":
        return TrainingBatches(
            interior=protocol.apply_time_support(
                self.interior,
                update_index=update_index,
                model_horizon_ns=model_horizon_ns,
            ),
            initial=self.initial,
            boundaries={
                side: protocol.apply_time_support(
                    coordinates,
                    update_index=update_index,
                    model_horizon_ns=model_horizon_ns,
                )
                for side, coordinates in self.boundaries.items()
            },
        )

    def update_digest(self, digest: "hashlib._Hash") -> None:
        digest.update(self.interior.numpy().tobytes())
        digest.update(self.initial.numpy().tobytes())
        for side in ("left", "right", "bottom", "top"):
            digest.update(self.boundaries[side].numpy().tobytes())


def _all_qpop_residuals(
    model: QPopPINN, batches: TrainingBatches
) -> dict[str, torch.Tensor]:
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


def _audit_qpop(
    model: QPopPINN,
    batches: TrainingBatches,
    scales: Mapping[str, float],
) -> tuple[float, float, dict[str, float]]:
    residuals = _all_qpop_residuals(model, batches)
    normalized = {
        name: float(
            torch.sqrt(torch.mean(value.detach().square())).cpu()
            / max(float(scales[name]), 1.0e-12)
        )
        for name, value in residuals.items()
    }
    return max(normalized.values()), sum(normalized.values()), normalized


@dataclass
class TrainingContinuation:
    terminal_state: dict[str, Any]
    optimizer_state: dict[str, Any]
    best_state: dict[str, Any]
    best_score: tuple[float, float, int]
    history: list[dict[str, Any]]
    sampling_digest: str
    completed_updates: int


@dataclass
class TrainingResult:
    selected_step: int
    checkpoint_score: dict[str, float]
    history: list[dict[str, Any]]
    actual_updates: int
    wall_seconds: float
    sampling_digest: str
    continuation: TrainingContinuation

    def summary(self) -> dict[str, Any]:
        return {
            "selected_step": self.selected_step,
            "checkpoint_score": self.checkpoint_score,
            "history": self.history,
            "actual_updates": self.actual_updates,
            "wall_seconds": self.wall_seconds,
            "sampling_digest": self.sampling_digest,
        }


@dataclass(frozen=True)
class AnchorSet:
    coordinates: torch.Tensor
    eta_targets: torch.Tensor

    def __post_init__(self) -> None:
        if self.coordinates.ndim != 2 or self.coordinates.shape[1] != 3:
            raise ValueError("anchor coordinates must have normalized x, y, and time")
        if self.eta_targets.shape != (self.coordinates.shape[0], 1):
            raise ValueError("anchor eta targets must align with coordinates")
        if self.coordinates.shape[0] == 0:
            raise ValueError("anchor diagnostic requires at least one label")


@dataclass
class AnchorTrainingResult:
    selected_step: int
    selected_anchor_loss: float
    checkpoint_score: dict[str, float]
    history: list[dict[str, Any]]
    actual_updates: int
    wall_seconds: float
    sampling_digest: str

    def summary(self) -> dict[str, Any]:
        return {
            "selected_step": self.selected_step,
            "selected_anchor_loss": self.selected_anchor_loss,
            "checkpoint_score": self.checkpoint_score,
            "history": self.history,
            "actual_updates": self.actual_updates,
            "wall_seconds": self.wall_seconds,
            "sampling_digest": self.sampling_digest,
        }


@dataclass(frozen=True)
class QPopTrainingSession:
    audit_batches: TrainingBatches
    scales: Mapping[str, float]
    initial_audit: tuple[float, float, Mapping[str, float]]

    @classmethod
    def freeze(
        cls,
        reference_model: QPopPINN,
        protocol: TrainingProtocol,
        *,
        seed: int,
    ) -> "QPopTrainingSession":
        audit_batches = TrainingBatches.fixed(
            seed=seed + 100000,
            interior=protocol.audit_interior_points,
            initial=protocol.audit_initial_points,
            boundary_per_side=protocol.audit_boundary_points_per_side,
        ).with_time_support(
            protocol,
            update_index=protocol.warmup_updates,
            model_horizon_ns=reference_model.horizon_ns,
        )
        residuals = _all_qpop_residuals(reference_model, audit_batches)
        scales = {
            name: max(
                float(torch.sqrt(torch.mean(value.detach().square())).cpu()),
                1.0e-12,
            )
            for name, value in residuals.items()
        }
        initial_audit = _audit_qpop(reference_model, audit_batches, scales)
        return cls(audit_batches, scales, initial_audit)

    def train(
        self,
        model: QPopPINN,
        protocol: TrainingProtocol,
        *,
        seed: int,
        updates: int,
        continuation: TrainingContinuation | None = None,
    ) -> TrainingResult:
        if model.method != "raw":
            raise ValueError("strong raw training session accepts raw-time models only")
        if updates <= 0:
            raise ValueError("optimizer updates must be positive")
        started = time.monotonic()
        optimizer = torch.optim.Adam(model.parameters(), lr=protocol.learning_rate)
        if continuation is None:
            initial_maximum, initial_total, initial_detail = self.initial_audit
            history: list[dict[str, Any]] = [
                {
                    "step": 0,
                    "training_loss": None,
                    "physics_audit_max": initial_maximum,
                    "physics_audit_sum": initial_total,
                    "physics_audit_detail": dict(initial_detail),
                }
            ]
            best_state = copy.deepcopy(model.state_dict())
            best_score = (math.inf, math.inf, 2**31 - 1)
            completed_updates = 0
            sampling_state = b""
        else:
            model.load_state_dict(continuation.terminal_state)
            optimizer.load_state_dict(continuation.optimizer_state)
            history = copy.deepcopy(continuation.history)
            best_state = copy.deepcopy(continuation.best_state)
            best_score = continuation.best_score
            completed_updates = continuation.completed_updates
            sampling_state = bytes.fromhex(continuation.sampling_digest)

        audit_every = 40 if completed_updates < protocol.warmup_updates else 100
        if updates == 1:
            audit_every = 1
        for local_index in range(updates):
            update_index = completed_updates + local_index
            base_batches = TrainingBatches.fixed(
                seed=seed + update_index,
                interior=protocol.interior_points,
                initial=protocol.initial_points,
                boundary_per_side=protocol.boundary_points_per_side,
            )
            step_digest = hashlib.sha256()
            base_batches.update_digest(step_digest)
            sampling_state = hashlib.sha256(
                sampling_state + step_digest.digest()
            ).digest()
            batches = base_batches.with_time_support(
                protocol,
                update_index=update_index,
                model_horizon_ns=model.horizon_ns,
            )
            optimizer.zero_grad(set_to_none=True)
            loss = protocol.objective(
                _all_qpop_residuals(model, batches), self.scales
            )
            if not torch.isfinite(loss):
                raise RuntimeError(
                    f"{protocol.protocol_id} produced a non-finite training loss"
                )
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), protocol.gradient_clip)
            optimizer.step()
            step = update_index + 1
            if step == 1 or step % audit_every == 0 or local_index + 1 == updates:
                maximum, total, detail = _audit_qpop(
                    model, self.audit_batches, self.scales
                )
                record = {
                    "step": step,
                    "training_loss": float(loss.detach()),
                    "physics_audit_max": maximum,
                    "physics_audit_sum": total,
                    "physics_audit_detail": detail,
                    "time_ceiling_ns": protocol.time_ceiling_ns(update_index),
                }
                history.append(record)
                score = (maximum, total, step)
                if score < best_score:
                    best_score = score
                    best_state = copy.deepcopy(model.state_dict())

        if best_score[2] <= 0 or not math.isfinite(best_score[0]):
            raise RuntimeError("training produced no finite non-initial checkpoint")

        terminal_state = copy.deepcopy(model.state_dict())
        completed_updates += updates
        sampling_digest = sampling_state.hex()
        continuation_result = TrainingContinuation(
            terminal_state=terminal_state,
            optimizer_state=copy.deepcopy(optimizer.state_dict()),
            best_state=copy.deepcopy(best_state),
            best_score=best_score,
            history=copy.deepcopy(history),
            sampling_digest=sampling_digest,
            completed_updates=completed_updates,
        )
        model.load_state_dict(best_state)
        return TrainingResult(
            selected_step=best_score[2],
            checkpoint_score={
                "max_normalized_violation": best_score[0],
                "sum_normalized_violation": best_score[1],
            },
            history=history,
            actual_updates=completed_updates,
            wall_seconds=time.monotonic() - started,
            sampling_digest=sampling_digest,
            continuation=continuation_result,
        )

    def train_anchor_diagnostic(
        self,
        model: QPopPINN,
        protocol: TrainingProtocol,
        *,
        anchors: AnchorSet,
        seed: int,
        updates: int,
        physics_ceiling: float = 1.25,
    ) -> AnchorTrainingResult:
        if model.method != "raw":
            raise ValueError("anchor diagnostic accepts a raw-time model only")
        if updates <= 0:
            raise ValueError("anchor diagnostic updates must be positive")

        def anchor_loss() -> torch.Tensor:
            eta = model(anchors.coordinates)[:, 0:1]
            return torch.mean(((eta - anchors.eta_targets) / 1.6).square())

        started = time.monotonic()
        optimizer = torch.optim.Adam(model.parameters(), lr=protocol.learning_rate)
        initial_maximum, initial_total, initial_detail = self.initial_audit
        initial_anchor = float(anchor_loss().detach())
        history: list[dict[str, Any]] = [
            {
                "step": 0,
                "training_loss": None,
                "anchor_loss": initial_anchor,
                "physics_audit_max": initial_maximum,
                "physics_audit_sum": initial_total,
                "physics_audit_detail": dict(initial_detail),
            }
        ]
        states: dict[int, dict[str, Any]] = {
            0: copy.deepcopy(model.state_dict())
        }
        sampling_state = b""
        audit_every = 1 if updates == 1 else 100
        for update_index in range(updates):
            base_batches = TrainingBatches.fixed(
                seed=seed + update_index,
                interior=protocol.interior_points,
                initial=protocol.initial_points,
                boundary_per_side=protocol.boundary_points_per_side,
            )
            step_digest = hashlib.sha256()
            base_batches.update_digest(step_digest)
            sampling_state = hashlib.sha256(
                sampling_state + step_digest.digest()
            ).digest()
            batches = base_batches.with_time_support(
                protocol,
                update_index=update_index,
                model_horizon_ns=model.horizon_ns,
            )
            optimizer.zero_grad(set_to_none=True)
            label_loss = anchor_loss()
            loss = (
                protocol.objective(
                    _all_qpop_residuals(model, batches), self.scales
                )
                + label_loss
            )
            if not torch.isfinite(loss):
                raise RuntimeError("anchor diagnostic produced a non-finite loss")
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), protocol.gradient_clip)
            optimizer.step()
            step = update_index + 1
            if step == 1 or step % audit_every == 0 or step == updates:
                maximum, total, detail = _audit_qpop(
                    model, self.audit_batches, self.scales
                )
                record = {
                    "step": step,
                    "training_loss": float(loss.detach()),
                    "anchor_loss": float(anchor_loss().detach()),
                    "physics_audit_max": maximum,
                    "physics_audit_sum": total,
                    "physics_audit_detail": detail,
                    "time_ceiling_ns": protocol.time_ceiling_ns(update_index),
                }
                history.append(record)
                states[step] = copy.deepcopy(model.state_dict())

        selected = select_anchor_checkpoint(
            history, physics_ceiling=physics_ceiling
        )
        selected_step = int(selected["step"])
        model.load_state_dict(states[selected_step])
        return AnchorTrainingResult(
            selected_step=selected_step,
            selected_anchor_loss=float(selected["anchor_loss"]),
            checkpoint_score={
                "max_normalized_violation": float(
                    selected["physics_audit_max"]
                ),
                "sum_normalized_violation": float(
                    selected["physics_audit_sum"]
                ),
            },
            history=history,
            actual_updates=updates,
            wall_seconds=time.monotonic() - started,
            sampling_digest=sampling_state.hex(),
        )
