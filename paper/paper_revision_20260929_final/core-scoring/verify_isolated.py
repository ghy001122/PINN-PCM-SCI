"""One real isolated score and one missing-input negative check; no fallback."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import os
import sys

import numpy  # Import the installed runtime before denying scientific source roots.


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--forbid-root", type=Path, nargs=2, required=True)
    parser.add_argument("--runtime-root", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    forbidden = [path.resolve() for path in args.forbid_root]
    runtime = args.runtime_root.resolve()
    if any(root.is_relative_to(path) for path in forbidden):
        raise ValueError("The verification copy must be outside both scientific roots")
    denied = []

    def guard(event, values):
        if event not in ("open", "os.listdir", "os.scandir") or not values:
            return
        raw = values[0]
        if not isinstance(raw, (str, bytes, os.PathLike)):
            return
        path = Path(os.fsdecode(raw)).resolve()
        if path.is_relative_to(runtime):
            return
        if any(path.is_relative_to(base) for base in forbidden):
            denied.append(str(path))
            raise PermissionError("Scientific source root is unavailable during isolated scoring")

    sys.addaudithook(guard)
    probes = []
    for base, filename in zip(forbidden, ("README.md", "handoff.json")):
        try:
            (base / filename).open("rb")
        except PermissionError:
            probes.append(True)
        else:
            raise AssertionError("Source read was not denied")
    baseline_denied = len(denied)
    manifest = json.loads((root / "manifest.json").read_text())
    for item in manifest["files"]:
        digest = hashlib.sha256()
        with (root / item["path"]).open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        if digest.hexdigest() != item["sha256"]:
            raise ValueError("Copied input differs: " + item["path"])
    spec = importlib.util.spec_from_file_location("isolated_core_score", root / "score.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    config = json.loads((root / "config.json").read_text())
    missing = root / config["candidates"][0]["path"]
    held = missing.with_name(missing.name + ".missing-check")
    missing.rename(held)
    missing_failed = False
    try:
        module.score(root)
    except FileNotFoundError as exc:
        missing_failed = "Missing package input" in str(exc)
    finally:
        held.rename(missing)
    if not missing_failed:
        raise AssertionError("Missing input did not fail explicitly")
    result = module.score(root)
    if len(denied) != baseline_denied:
        raise AssertionError("Scorer attempted access outside the copied package")
    verification = dict(status="PASS", isolated_python=bool(sys.flags.isolated),
        independent_directory=str(root), scientific_roots_denied=[str(path) for path in forbidden],
        denial_probes_passed=probes, runtime_exception=str(runtime),
        source_fallback_attempts=0, missing_input_failed_without_fallback=missing_failed,
        copied_input_hashes_verified=len(manifest["files"]), metric_comparison=result["status"],
        checked_metrics=result["checked_metrics"], rtol=result["rtol"], atol=result["atol"],
        maximum_absolute_difference=result["maximum_absolute_difference"],
        frozen_qualification_action="copied only; full A/B not recomputed")
    (root / "independent-verification.json").write_text(json.dumps(verification, indent=2) + "\n")
    print(json.dumps(verification))


if __name__ == "__main__":
    main()
