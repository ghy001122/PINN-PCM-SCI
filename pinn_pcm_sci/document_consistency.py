"""Deterministic consistency audit for the live documentation authority chain."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import re
from typing import Sequence

from .ledger import ExperimentLedger, LedgerValidationError


STATUS_FIELDS = ("phase_id", "lifecycle_state", "blocker_id", "claim_status")
STATUS_SURFACES = (
    Path("active_phase.md"),
    Path("README.md"),
    Path("PROJECT_STATE.md"),
    Path("docs/plans/NEXT_ACTIONS.md"),
)
LINK_SURFACES = (
    *STATUS_SURFACES,
    Path("CODEX_CONTEXT.md"),
    Path("CONTEXT.md"),
    Path("rules.md"),
    Path("docs/README.md"),
    Path("docs/adr/README.md"),
    Path("docs/experiment/README.md"),
    Path("archive/README.md"),
)
_FIELD_PATTERN = re.compile(r"^- `(?P<name>[a-z_]+)`: `(?P<value>[^`]+)`$", re.MULTILINE)
_LINK_PATTERN = re.compile(r"\[[^\]]+\]\((?P<target>[^)]+)\)")
_STALE_README_MARKERS = (
    "尚无求解器实现",
    "当前授权仍为文档与治理工作",
    "尚无求解器实现、PINN 训练",
)


@dataclass(frozen=True)
class DocumentIssue:
    code: str
    path: str
    message: str


def _status_fields(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    text = path.read_text(encoding="utf-8")
    return {
        match.group("name"): match.group("value")
        for match in _FIELD_PATTERN.finditer(text)
        if match.group("name") in STATUS_FIELDS
    }


def audit_repository(root: Path) -> list[DocumentIssue]:
    """Return every current authority-chain inconsistency found under *root*."""

    root = root.resolve()
    issues: list[DocumentIssue] = []
    reference_path = root / STATUS_SURFACES[0]
    reference = _status_fields(reference_path)
    for relative_path in STATUS_SURFACES:
        path = root / relative_path
        fields = _status_fields(path)
        for field in STATUS_FIELDS:
            if fields.get(field) != reference.get(field):
                issues.append(
                    DocumentIssue(
                        code="STATUS_FIELD_MISMATCH",
                        path=relative_path.as_posix(),
                        message=(
                            f"{field}={fields.get(field)!r} differs from "
                            f"active_phase.md={reference.get(field)!r}"
                        ),
                    )
                )
    plan_root = root / "docs" / "plans"
    live_plans = sorted(plan_root.glob("*.md")) if plan_root.is_dir() else []
    if len(live_plans) != 1 or (root / "NEXT_ACTIONS.md").exists():
        issues.append(
            DocumentIssue(
                code="MULTIPLE_LIVE_PLAN",
                path="docs/plans",
                message="exactly docs/plans/NEXT_ACTIONS.md may be live",
            )
        )
    live_plan = root / "docs" / "plans" / "NEXT_ACTIONS.md"
    if live_plan.is_file() and "## 已完成的本轮 PLAN" in live_plan.read_text(
        encoding="utf-8"
    ):
        issues.append(
            DocumentIssue(
                code="LIVE_PLAN_CONTAINS_HISTORY",
                path="docs/plans/NEXT_ACTIONS.md",
                message="completed execution history belongs in experiment or archive records",
            )
        )
    readme = root / "README.md"
    if readme.is_file():
        readme_text = readme.read_text(encoding="utf-8")
        if any(marker in readme_text for marker in _STALE_README_MARKERS):
            issues.append(
                DocumentIssue(
                    code="STALE_README_STATUS",
                    path="README.md",
                    message="README contains a retired pre-research status marker",
                )
            )
    if reference_path.is_file():
        phase_text = reference_path.read_text(encoding="utf-8")
        if "## 当前裁决" in phase_text or "_run_count" in phase_text:
            issues.append(
                DocumentIssue(
                    code="PHASE_CONTAINS_EXECUTION_HISTORY",
                    path="active_phase.md",
                    message="execution facts belong in PROJECT_STATE.md or experiment records",
                )
            )
    adr_root = root / "docs" / "adr"
    adr_index = adr_root / "README.md"
    adr_index_text = (
        adr_index.read_text(encoding="utf-8") if adr_index.is_file() else ""
    )
    for adr_path in sorted(adr_root.glob("[0-9][0-9][0-9][0-9]-*.md")):
        if adr_path.name not in adr_index_text:
            issues.append(
                DocumentIssue(
                    code="ADR_NOT_INDEXED",
                    path=adr_path.relative_to(root).as_posix(),
                    message="numbered ADR is missing from docs/adr/README.md",
                )
            )
    for relative_path in LINK_SURFACES:
        path = root / relative_path
        if not path.is_file():
            continue
        for match in _LINK_PATTERN.finditer(path.read_text(encoding="utf-8")):
            target = match.group("target").strip().strip("<>")
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            target_path = target.split("#", 1)[0]
            if target_path and not (path.parent / target_path).resolve().exists():
                issues.append(
                    DocumentIssue(
                        code="BROKEN_LOCAL_LINK",
                        path=relative_path.as_posix(),
                        message=f"local link target does not exist: {target}",
                    )
                )
    ignore_path = root / ".gitignore"
    ignore_lines = (
        {
            line.strip()
            for line in ignore_path.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        }
        if ignore_path.is_file()
        else set()
    )
    if not ignore_lines.intersection(
        {".ledger.lock", "**/.ledger.lock", "docs/experiment/.ledger.lock"}
    ):
        issues.append(
            DocumentIssue(
                code="LEDGER_LOCK_NOT_IGNORED",
                path=".gitignore",
                message="docs/experiment/.ledger.lock is a runtime lock, not evidence",
            )
        )
    try:
        ExperimentLedger(root / "docs" / "experiment").validate()
    except (LedgerValidationError, OSError, ValueError) as exc:
        issues.append(
            DocumentIssue(
                code="EXPERIMENT_LEDGER_INVALID",
                path="docs/experiment",
                message=str(exc),
            )
        )
    return issues


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    arguments = parser.parse_args(argv)
    issues = audit_repository(arguments.root)
    if issues:
        for issue in issues:
            print(f"{issue.code}: {issue.path}: {issue.message}")
        return 1
    print("DOCUMENT_CONSISTENCY_VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
