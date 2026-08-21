from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from pinn_pcm_sci.document_consistency import audit_repository, main


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _metadata(*, lifecycle: str = "AWAITING") -> str:
    return (
        "- `phase_id`: `PHASE_A`\n"
        f"- `lifecycle_state`: `{lifecycle}`\n"
        "- `blocker_id`: `BLOCKER_A`\n"
        "- `claim_status`: `NO_FORMAL_EVIDENCE`\n"
    )


class DocumentConsistencyTests(unittest.TestCase):
    def test_status_field_divergence_is_reported_at_the_public_audit_seam(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _write(root / "active_phase.md", "# Phase\n\n" + _metadata())
            _write(root / "README.md", "# Project\n\n" + _metadata())
            _write(root / "PROJECT_STATE.md", "# State\n\n" + _metadata())
            _write(
                root / "docs" / "plans" / "NEXT_ACTIONS.md",
                "# Plan\n\n" + _metadata(lifecycle="ACTIVE"),
            )

            issues = audit_repository(root)

            self.assertIn("STATUS_FIELD_MISMATCH", {issue.code for issue in issues})

    def test_duplicate_or_historical_live_plan_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for relative_path, title in (
                ("active_phase.md", "Phase"),
                ("README.md", "Project"),
                ("PROJECT_STATE.md", "State"),
            ):
                _write(root / relative_path, f"# {title}\n\n" + _metadata())
            _write(
                root / "docs" / "plans" / "NEXT_ACTIONS.md",
                "# Plan\n\n" + _metadata() + "\n## 已完成的本轮 PLAN\n",
            )
            _write(root / "NEXT_ACTIONS.md", "# Retired plan\n")

            codes = {issue.code for issue in audit_repository(root)}

            self.assertIn("MULTIPLE_LIVE_PLAN", codes)
            self.assertIn("LIVE_PLAN_CONTAINS_HISTORY", codes)

    def test_stale_readme_and_experiment_history_in_phase_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _write(
                root / "active_phase.md",
                "# Phase\n\n" + _metadata() + "\n## 当前裁决\n- run metrics\n",
            )
            _write(
                root / "README.md",
                "# Project\n\n" + _metadata() + "\n尚无求解器实现。\n",
            )
            _write(root / "PROJECT_STATE.md", "# State\n\n" + _metadata())
            _write(
                root / "docs" / "plans" / "NEXT_ACTIONS.md",
                "# Plan\n\n" + _metadata(),
            )

            codes = {issue.code for issue in audit_repository(root)}

            self.assertIn("STALE_README_STATUS", codes)
            self.assertIn("PHASE_CONTAINS_EXECUTION_HISTORY", codes)

    def test_every_numbered_adr_must_be_linked_from_the_adr_index(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for relative_path, title in (
                ("active_phase.md", "Phase"),
                ("README.md", "Project"),
                ("PROJECT_STATE.md", "State"),
            ):
                _write(root / relative_path, f"# {title}\n\n" + _metadata())
            _write(
                root / "docs" / "plans" / "NEXT_ACTIONS.md",
                "# Plan\n\n" + _metadata(),
            )
            _write(root / "docs" / "adr" / "README.md", "# ADR index\n")
            _write(root / "docs" / "adr" / "0001-example.md", "# Decision\n")

            issues = audit_repository(root)

            self.assertIn("ADR_NOT_INDEXED", {issue.code for issue in issues})

    def test_broken_authority_link_and_unignored_ledger_lock_are_reported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for relative_path, title in (
                ("active_phase.md", "Phase"),
                ("README.md", "Project"),
                ("PROJECT_STATE.md", "State"),
            ):
                _write(root / relative_path, f"# {title}\n\n" + _metadata())
            _write(
                root / "docs" / "plans" / "NEXT_ACTIONS.md",
                "# Plan\n\n" + _metadata(),
            )
            _write(root / "docs" / "README.md", "[missing](missing.md)\n")
            _write(root / "docs" / "experiment" / ".ledger.lock", "\n")
            _write(root / ".gitignore", "outputs/\n")

            codes = {issue.code for issue in audit_repository(root)}

            self.assertIn("BROKEN_LOCAL_LINK", codes)
            self.assertIn("LEDGER_LOCK_NOT_IGNORED", codes)

    def test_cli_returns_zero_only_for_a_consistent_repository(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for relative_path, title in (
                ("active_phase.md", "Phase"),
                ("README.md", "Project"),
                ("PROJECT_STATE.md", "State"),
            ):
                _write(root / relative_path, f"# {title}\n\n" + _metadata())
            plan_path = root / "docs" / "plans" / "NEXT_ACTIONS.md"
            _write(plan_path, "# Plan\n\n" + _metadata())
            _write(root / "docs" / "adr" / "README.md", "# ADR index\n")
            _write(root / ".gitignore", "docs/experiment/.ledger.lock\n")

            self.assertEqual(main(["--root", str(root)]), 0)

            _write(plan_path, "# Plan\n\n" + _metadata(lifecycle="ACTIVE"))
            self.assertEqual(main(["--root", str(root)]), 1)


if __name__ == "__main__":
    unittest.main()
