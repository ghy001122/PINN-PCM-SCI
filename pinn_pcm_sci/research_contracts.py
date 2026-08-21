"""Frozen research contracts shared by Q-POP qualification and PINN runs."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
from typing import Any, Mapping, TypeVar


@dataclass(frozen=True)
class EvaluatorAudit:
    status: str
    disposition: str
    official_evaluator: str | None
    frozen_project_evaluator: str | None

    def __post_init__(self) -> None:
        if self.status not in {"PRESENT", "ABSENT", "AMBIGUOUS"}:
            raise ValueError("evaluator audit status must be PRESENT, ABSENT, or AMBIGUOUS")
        if self.status == "ABSENT":
            if self.disposition != "OFFICIAL_EVALUATOR_NOT_PROVIDED":
                raise ValueError("absent evaluator requires the canonical disposition")
            if self.official_evaluator is not None:
                raise ValueError("absent evaluator cannot name an official evaluator")
        if self.status == "PRESENT" and not self.official_evaluator:
            raise ValueError("present evaluator must name its frozen official identity")


@dataclass(frozen=True)
class BenchmarkContract:
    benchmark_id: str
    source_identity: Mapping[str, Any]
    canonical_case_id: str
    input_contract: Mapping[str, Any]
    output_contract: Mapping[str, Any]
    preprocessing: tuple[str, ...]
    metric_specs: tuple[str, ...]
    evaluator_audit: EvaluatorAudit

    def __post_init__(self) -> None:
        if not self.benchmark_id or not self.canonical_case_id:
            raise ValueError("benchmark and canonical case identities must be non-empty")


@dataclass(frozen=True)
class PhysicalContract:
    contract_id: str
    source_identity: Mapping[str, Any]
    independent_unknowns: tuple[str, ...]
    equations: tuple[str, ...]
    constitutive_relations: tuple[str, ...]
    units: Mapping[str, str]
    initial_conditions: tuple[str, ...]
    boundary_conditions: tuple[str, ...]
    interface_conditions: tuple[str, ...]
    circuit_constraints: tuple[str, ...]
    breakpoints: tuple[float, ...]
    discretization: Mapping[str, Any]
    conservation_checks: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.contract_id:
            raise ValueError("physical contract id must be non-empty")
        if not self.independent_unknowns or not self.equations:
            raise ValueError("physical contract must close unknowns with equations")
        if any(right <= left for left, right in zip(self.breakpoints, self.breakpoints[1:])):
            raise ValueError("physical breakpoints must be strictly increasing")


ContractT = TypeVar("ContractT", PhysicalContract, BenchmarkContract)


def write_contract(path: Path, contract: PhysicalContract | BenchmarkContract) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(f"frozen contract already exists: {path}")
    temporary = path.with_name(f".{path.name}.tmp")
    payload = json.dumps(asdict(contract), indent=2, sort_keys=True) + "\n"
    with temporary.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def read_contract(path: Path, contract_type: type[ContractT]) -> ContractT:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("contract payload must be a JSON object")
    if contract_type is PhysicalContract:
        for key in (
            "independent_unknowns",
            "equations",
            "constitutive_relations",
            "initial_conditions",
            "boundary_conditions",
            "interface_conditions",
            "circuit_constraints",
            "breakpoints",
            "conservation_checks",
        ):
            payload[key] = tuple(payload[key])
        return PhysicalContract(**payload)  # type: ignore[return-value]
    if contract_type is BenchmarkContract:
        payload["preprocessing"] = tuple(payload["preprocessing"])
        payload["metric_specs"] = tuple(payload["metric_specs"])
        payload["evaluator_audit"] = EvaluatorAudit(**payload["evaluator_audit"])
        return BenchmarkContract(**payload)  # type: ignore[return-value]
    raise TypeError(f"unsupported contract type: {contract_type!r}")
