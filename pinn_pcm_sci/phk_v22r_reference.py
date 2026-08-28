"""Generate and hash-seal the two PHK-V2.2R stress references.

This runner intentionally has no evaluation function.  It writes the frozen
finite-volume carrier and a byte hash, but it does not compute or expose field
metrics before the method candidate is frozen.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
from typing import Any, Mapping

from .phk_benchmark import PhkControl
from .phk_v21_benchmark import (
    PhkV21CaseSpec,
    PhkV21OracleCase,
    load_phk_v21_physical,
    phk_v21_resolution,
    write_phk_v21_result,
)


ROOT = Path(__file__).resolve().parents[1]
TARGETS = {
    PhkControl.INTERFACE_WIDTH_0_025: ROOT
    / "outputs"
    / "sealed"
    / "phk_v22r"
    / "narrow_interface_extra_fine",
    PhkControl.HEATER_WIDTH_0_50: ROOT
    / "outputs"
    / "sealed"
    / "phk_v22r"
    / "wide_heater_extra_fine",
}


def _sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def _write_json_exclusive(path: Path, payload: Mapping[str, Any]) -> None:
    with Path(path).open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")


def generate_stress_reference(control: PhkControl | str) -> Path:
    selected = PhkControl(control)
    if selected not in TARGETS:
        raise ValueError("V2.2R admits only narrow-interface and wide-heater references")
    target = TARGETS[selected]
    target.mkdir(parents=True, exist_ok=False)
    program_contract = ROOT / "configs" / "phk_v22r" / "program_contract.json"
    program_sha = _sha256_path(program_contract)
    physical = load_phk_v21_physical(
        program_path=ROOT / "configs" / "phk_v21" / "program_contract.json",
        object_path=ROOT / "configs" / "phk_v21" / "object_numerical_contract.json",
        legacy_program_path=ROOT / "configs" / "phk_v2" / "program_contract.json",
        legacy_object_path=ROOT / "configs" / "phk_v2" / "object_numerical_contract.json",
    )
    case = PhkV21CaseSpec.nominal(physical, control=selected)
    resolution = phk_v21_resolution(physical, "extra_fine", period=case.period)
    intent = {
        "schema_id": "phk-v22r-sealed-reference-intent-v1",
        "status": "INTENT_WRITTEN_BEFORE_COMPUTE",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "control": selected.value,
        "case_id": case.case_id,
        "resolution": {
            "name": resolution.name,
            "nx": resolution.nx,
            "nz": resolution.nz,
            "dt": resolution.dt,
            "time_end": resolution.time_end,
            "save_every": resolution.save_every,
        },
        "program_contract_sha256": program_sha,
        "physical_program_sha256": physical.program.sha256,
        "physical_object_sha256": physical.object.sha256,
        "pre_freeze_access_policy": "WRITE_AND_HASH_ONLY_NO_FIELD_OR_METRIC_READ",
        "one_formal_solver_intent": True,
    }
    _write_json_exclusive(target / "intent.json", intent)
    start = time.perf_counter()
    result = PhkV21OracleCase(
        physical=physical,
        case=case,
        resolution=resolution,
    ).solve()
    carrier = target / "reference.npz"
    write_phk_v21_result(carrier, result)
    wall_seconds = time.perf_counter() - start
    seal = {
        "schema_id": "phk-v22r-sealed-reference-byte-seal-v1",
        "status": "SEALED_UNREAD_PENDING_CANDIDATE_FREEZE",
        "sealed_at_utc": datetime.now(timezone.utc).isoformat(),
        "control": selected.value,
        "case_id": case.case_id,
        "carrier": "reference.npz",
        "carrier_size_bytes": carrier.stat().st_size,
        "carrier_sha256": _sha256_path(carrier),
        "generation_wall_seconds": wall_seconds,
        "program_contract_sha256": program_sha,
        "physical_program_sha256": physical.program.sha256,
        "physical_object_sha256": physical.object.sha256,
        "field_or_metric_read_after_write": False,
        "evaluation_authorized_only_after": "configs/phk_v22r/candidate_freeze.json:FROZEN",
    }
    _write_json_exclusive(target / "byte-seal.json", seal)
    return target


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--control",
        required=True,
        choices=[
            PhkControl.INTERFACE_WIDTH_0_025.value,
            PhkControl.HEATER_WIDTH_0_50.value,
        ],
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    target = generate_stress_reference(args.control)
    seal = json.loads((target / "byte-seal.json").read_text(encoding="utf-8"))
    print(
        json.dumps(
            {
                "status": seal["status"],
                "control": seal["control"],
                "carrier_size_bytes": seal["carrier_size_bytes"],
                "carrier_sha256": seal["carrier_sha256"],
                "generation_wall_seconds": seal["generation_wall_seconds"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["TARGETS", "generate_stress_reference", "main"]
