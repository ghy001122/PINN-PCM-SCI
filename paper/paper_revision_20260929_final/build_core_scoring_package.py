"""Extract the approved FP64 primary ROI/port subset; verify once in isolation.

Only ten frozen candidate fields and two mapped spatial references are touched.
No model, new readout, new reference, full-domain scoring, or neural AD is used.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import time as clock
import zipfile
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SOURCE = Path("D:/Temp/PINN-PCM-Standalone-20260926")
ARCHIVE = SOURCE / "outputs/submission-rescore-20260921"
PACK = HERE / "core-scoring"
BUILD = HERE / "build"
METRICS = ("Ephi", "bottom_current_NRMSE", "power_trace_NRMSE")


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")


def digest(path):
    result = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def selected_provenance(path, fields):
    with zipfile.ZipFile(path) as archive:
        members = {field: dict(crc32=archive.getinfo(field + ".npy").CRC,
                               uncompressed_member_bytes=archive.getinfo(field + ".npy").file_size)
                   for field in fields}
    return dict(source_path=path.relative_to(SOURCE).as_posix(), source_bytes=path.stat().st_size,
                selected_members=members, source_kind="project synthetic numerical evidence")


def phase_subset(path, roi, time):
    # np.load on an NPZ member is lazy: no V, T, q or other field is expanded.
    with np.load(path, allow_pickle=False) as archive:
        np.testing.assert_array_equal(archive["time"], time)
        phase = archive["phase"]
        if phase.dtype != np.dtype("float64") or phase.shape != (1001, 12800):
            raise ValueError("Unexpected phase precision or shape: " + str(path))
        selected = np.ascontiguousarray(phase[:, roi])
    if selected.shape != (1001, 3872) or not np.isfinite(selected).all():
        raise ValueError("Invalid saved ROI field")
    return selected


def build():
    started = clock.perf_counter()
    if (PACK / "manifest.json").exists():
        raise FileExistsError("Package already built; use --verify-isolated without --build")
    manifest = read(ARCHIVE / "manifest.json")
    old_path = ARCHIVE / "primary-rescore/results.json"
    cov_path = SOURCE / "outputs/runs/20260926-core-revision-vo2-bridge/fcov-scoring/results.json"
    old, cov = read(old_path), read(cov_path)
    if cov["status"] != "COMPLETE_F_COV_FIXED_ENDPOINT_SCORING":
        raise ValueError("F_cov scoring is not locked complete")
    with np.load(ARCHIVE / manifest["grid_arrays"], allow_pickle=False) as arrays:
        x, z = arrays["cell_x"], arrays["cell_z"]
    roi = (np.abs(x) <= .55) & (z >= 0) & (z <= .55)
    if roi.shape != (12800,) or roi.sum() != 3872:
        raise ValueError("Original ROI identity differs")
    first = ARCHIVE / manifest["protocols"]["original"]["references"]["spatial"]
    with np.load(first, allow_pickle=False) as archive:
        time = archive["time"]
    if time.dtype != np.dtype("float64") or time.shape != (1001,) or time[0] != 0 or time[-1] != 2.5:
        raise ValueError("Original time support differs")
    tw = np.empty_like(time)
    tw[0], tw[-1] = (time[1] - time[0]) / 2, (time[-1] - time[-2]) / 2
    tw[1:-1] = (time[2:] - time[:-2]) / 2
    tw /= time[-1] - time[0]
    (PACK / "arrays").mkdir(parents=True, exist_ok=True)
    np.savez_compressed(PACK / "arrays/geometry.npz", time=time, time_weights=tw,
                        cell_x=x, cell_z=z, roi_mask=roi, roi_indices=np.flatnonzero(roi),
                        roi_x=x[roi], roi_z=z[roi], space_weights=np.full(3872, 1 / 3872))
    config = dict(task_id="PCM-20260929-FINAL-MANUSCRIPT-CONSOLIDATION-01", geometry="arrays/geometry.npz",
                  reference="spatial", reader="fine", phase_grid=[160, 80], port_grid=[240, 120],
                  original_ROI=dict(abs_x_max=.55, z_min=0, z_max=.55), references={}, candidates=[])
    provenance = dict(original_local_source_root=str(SOURCE), runtime_fallback=False,
        phase_selection="coarse/prediction phase is the original fine-reader Ephi input; no restriction of fine phase",
        reference_selection="existing mapped-reference phase; no new restriction or reference generation",
        selected_inputs=[], expected_metric_sources=[str(old_path.relative_to(SOURCE)), str(cov_path.relative_to(SOURCE))],
        expected_source_sha256=[digest(old_path), digest(cov_path)],
        public_access=False, remote_copy="NOT_SYNCED_THIS_TASK", P03="OPEN")
    expected = dict(metrics={}, frozen_A_B=[], tolerances=dict(rtol=2e-10, atol=2e-12),
                    qualification_scope="frozen A/B only; no qualification recomputed from three metrics")
    for protocol in ("original", "shorter"):
        desc = manifest["protocols"][protocol]
        cfg = read(ARCHIVE / desc["config"])
        if cfg["qualification_event"]["roi"] != config["original_ROI"]:
            raise ValueError("ROI contract differs between protocols")
        path = ARCHIVE / desc["references"]["spatial"]
        phase = phase_subset(path, roi, time)
        with np.load(path, allow_pickle=False) as archive:
            ports = {key: archive[key] for key in ("top_current", "bottom_current", "joule_power")}
        name = f"arrays/reference-{protocol}.npz"
        np.savez_compressed(PACK / name, phase_roi=phase, time=time, **ports)
        del phase, ports
        config["references"][protocol] = name
        provenance["selected_inputs"].append(selected_provenance(path, ["phase", "time", "top_current", "bottom_current", "joule_power"]))
        print("Retained reference ROI: " + protocol, flush=True)
    objects = [item for item in manifest["objects"] if item["role"] in ("E", "F")]
    if len(objects) != 8:
        raise ValueError("Expected eight historical candidate endpoints")
    for seed in (29, 43):
        base = SOURCE / f"outputs/runs/20260926-core-revision-vo2-bridge/fcov/seed-{seed}/F_cov"
        objects.append(dict(id=f"shorter/{seed}/F_cov", protocol="shorter", seed=seed, role="F_cov",
                            prediction=base / "coarse/projected/prediction.npz",
                            fine_readout=base / "fine/projected/own-readout.npz"))
    for item in objects:
        phase_path = ARCHIVE / item["prediction"]
        port_path = ARCHIVE / item["fine_readout"]
        phase = phase_subset(phase_path, roi, time)
        with np.load(port_path, allow_pickle=False) as archive:
            np.testing.assert_array_equal(archive["time"], time)
            ports = {key: archive[key] for key in ("bottom_current", "joule_power")}
        name = "arrays/" + item["id"].replace("/", "-") + ".npz"
        np.savez_compressed(PACK / name, phase_roi=phase, time=time, **ports)
        del phase, ports
        config["candidates"].append(dict(id=item["id"], protocol=item["protocol"], seed=item["seed"], role=item["role"], path=name))
        result = (cov if item["role"] == "F_cov" else old)["records"]["spatial"]["fine"][item["id"]]
        expected["metrics"][item["id"]] = {key: result["metrics"][key] for key in METRICS}
        provenance["selected_inputs"].append(selected_provenance(phase_path, ["phase", "time"]))
        provenance["selected_inputs"].append(selected_provenance(port_path, ["bottom_current", "joule_power", "time"]))
        print("Retained candidate ROI and native ports: " + item["id"], flush=True)
    for protocol in ("original", "shorter"):
        for seed in (29, 43):
            pair = old["decisions"]["spatial"]["fine"][protocol][str(seed)]["E_vs_F"]
            expected["frozen_A_B"].append(dict(protocol=protocol, seed=seed, comparison="E_vs_F",
                reference="spatial", reader="fine", A=pair["A"], B=pair["B"],
                source=old_path.relative_to(SOURCE).as_posix()))
    for seed in (29, 43):
        pair = cov["comparisons"]["spatial"]["fine"][str(seed)]["E_vs_F_cov"]
        expected["frozen_A_B"].append(dict(protocol="shorter", seed=seed, comparison="E_vs_F_cov",
            reference="spatial", reader="fine", A=pair["A"], B=pair["B"],
            source=cov_path.relative_to(SOURCE).as_posix()))
    save(PACK / "config.json", config)
    save(PACK / "expected.json", expected)
    save(PACK / "provenance.json", provenance)
    metric_path = ARCHIVE / "portable/readout_metrics.py"
    source = metric_path.read_text(encoding="utf-8")
    nodes = ast.parse(source).body
    snippets = [ast.get_source_segment(source, node) for node in nodes
                if isinstance(node, ast.FunctionDef) and node.name in ("time_rms", "field_rms", "add_power_metrics")]
    (PACK / "frozen-metric-excerpt.py").write_text(
        "# Provenance excerpt only; score.py is the independent executable entry.\nimport numpy as np\n\n" +
        "\n\n".join(snippets) + "\n", encoding="utf-8")
    (PACK / "README.md").write_text(
        "# Core phase and port scoring subset\n\n"
        "This local package independently recomputes 30 existing primary metrics for ten frozen endpoints: "
        "E/F on original and shorter protocols, seeds 29/43, and F_cov on shorter/29/43. "
        "It contains two existing spatial references. No endpoint is selected using these errors.\n\n"
        "Run with Python >=3.11 and NumPy >=2.0:\n\n"
        "```text\npython -I score.py --root <this-package-directory>\n```\n\n"
        "Every runtime input resolves beneath the explicit root; missing or escaped inputs raise an error. "
        "There is no old-workspace fallback. Results appear in `recomputed/results.json`.\n\n"
        "## Exact scope and measurement\n\n"
        "- Ephi: original FP64 phase on 160×80 cells, retaining all 1001 times over 0–2.5 and all 3872 original ROI cells "
        "(|x|≤0.55, 0≤z≤0.55). Spatial averaging is uniform over ROI cells; time uses the normalized original trapezoid rule. "
        "The main fine electrical reader originally scored this saved coarse-grid phase; this package does not substitute restricted fine-grid phase.\n"
        "- Electrical traces: saved native 240×120 common-readout bottom current and Joule power. The historical "
        "`bottom_current_NRMSE` compares candidate **bottom** current with reference **top** current, then divides by reference **top** RMS. "
        "This preserves `add_power_metrics`; it is not silently changed to bottom-versus-bottom. Reference bottom current is retained to make this distinction explicit.\n"
        "- Power: RMS(candidate Joule power − reference Joule power) / reference Joule-power RMS.\n"
        "- Geometry contains full ROI mask and indices, cell coordinates, ROI coordinates, original time vector, normalized spatial and temporal weights. "
        "FP64 values are retained without rounding or thinning and stored with lossless NPZ compression.\n\n"
        "## Verification and limits\n\n"
        "The required comparison tolerance is rtol=2e−10, atol=2e−12. `independent-verification.json` records the actual separate-directory test "
        "with both scientific source roots blocked, the runtime-only environment exception, and the missing-input negative check. "
        "The exact frozen A/B records are copied for context only; ET, EV, full-domain S, event guards and all qualifications are not recomputed. "
        "This is ROI/full-history saved-array rescoring, not full-domain validation, saved-residual reaggregation, neural AD recomputation, "
        "checkpoint inference, training, or a new reference solve.\n\n"
        "## Access and provenance\n\n"
        "This package is a local delivery and is **not externally published**. P03 remains **OPEN**; it does not provide the full-paper arrays, "
        "checkpoints or all historical evaluation inputs. No extra ZIP copy is maintained. Source paths in provenance are archival identities, "
        "never runtime fallback paths. No GPU was used; a remote copy has not been synchronized in this task.\n\n"
        "The arrays are project-generated synthetic numerical evidence. No third-party experimental records, publisher figures, "
        "author-model data or model checkpoints are included. Scoring code is project-authored; this local package does not grant a new public "
        "redistribution licence. NumPy is an external dependency and is not redistributed.\n", encoding="utf-8")
    files = []
    for path in sorted(PACK.rglob("*")):
        if path.is_file() and "__pycache__" not in path.parts and "recomputed" not in path.parts:
            files.append(dict(path=path.relative_to(PACK).as_posix(), bytes=path.stat().st_size, sha256=digest(path)))
    total = sum(item["bytes"] for item in files)
    save(PACK / "manifest.json", dict(files=files, total_input_bytes=total, format="FP64 lossless NPZ",
        candidates=10, references=2, time_nodes=1001, roi_cells=3872, expected_primary_metrics=30,
        publication="LOCAL_NOT_PUBLIC", P03="OPEN"))
    report = dict(status="BUILT_PENDING_ISOLATED_VERIFICATION", files=len(files), total_input_bytes=total,
        total_input_MiB=total / 2**20, elapsed_seconds=clock.perf_counter() - started,
        source_arrays_modified=False, extra_field_arrays_loaded=False, new_model_or_solver_calls=0)
    save(BUILD / "core-scoring-build.json", report)
    print(json.dumps(report), flush=True)


def verify():
    manifest = read(PACK / "manifest.json")
    temp_parent = Path(tempfile.gettempdir()).resolve()
    temporary = Path(tempfile.mkdtemp(prefix="pinn-pcm-core-scoring-", dir=temp_parent)).resolve()
    isolated = temporary / "package"
    # This exact generated directory is the only temporary-cleanup whitelist.
    cleanup = dict(path=str(temporary), retained_package=str(PACK), deletion="PENDING",
                   reason="isolated verification copy; source and retained package remain intact")
    save(BUILD / "core-scoring-cleanup.json", cleanup)
    shutil.copytree(PACK, isolated, ignore=shutil.ignore_patterns("__pycache__", "recomputed", "independent-verification.json"))
    command = [sys.executable, "-I", str(isolated / "verify_isolated.py"), "--root", str(isolated),
               "--forbid-root", str(ROOT), str(SOURCE), "--runtime-root", str(ROOT / ".venv")]
    result = subprocess.run(command, cwd=temporary, capture_output=True, text=True, encoding="utf-8")
    report = dict(returncode=result.returncode, stdout=result.stdout, stderr=result.stderr,
                  command=command, copied_input_bytes=manifest["total_input_bytes"])
    save(BUILD / "core-scoring-isolated-process.json", report)
    if result.returncode != 0:
        cleanup["deletion"] = "PRESERVED_FAILED_VERIFICATION"
        save(BUILD / "core-scoring-cleanup.json", cleanup)
        raise RuntimeError("Independent verification failed; retained package and temporary inputs preserved")
    verified = read(isolated / "independent-verification.json")
    if verified["status"] != "PASS" or verified["checked_metrics"] != 30:
        raise ValueError("Incomplete isolated verification")
    shutil.copy2(isolated / "independent-verification.json", PACK / "independent-verification.json")
    (PACK / "recomputed").mkdir(exist_ok=True)
    shutil.copy2(isolated / "recomputed/results.json", PACK / "recomputed/results.json")
    save(BUILD / "core-scoring-validation.json", verified)
    # Check resolved containment and the precise self-created path before removal.
    if temporary.parent != temp_parent or not temporary.name.startswith("pinn-pcm-core-scoring-"):
        raise ValueError("Unexpected temporary cleanup path")
    if temporary.is_relative_to(ROOT) or temporary.is_relative_to(SOURCE):
        raise ValueError("Temporary cleanup would touch an authoritative root")
    if not (PACK / "independent-verification.json").is_file() or not (PACK / "recomputed/results.json").is_file():
        raise ValueError("Verification reports were not recovered")
    shutil.rmtree(temporary)
    cleanup.update(deletion="REMOVED_EXACT_VERIFIED_TEMPORARY_COPY", verification_report_recovered=True,
                   path_exists_after_cleanup=temporary.exists())
    save(BUILD / "core-scoring-cleanup.json", cleanup)
    build_report = read(BUILD / "core-scoring-build.json")
    build_report.update(status="COMPLETE_INDEPENDENT_ARRAY_RESCORING",
                        validation="core-scoring-validation.json", isolated_metrics_passed=30,
                        maximum_absolute_difference=verified["maximum_absolute_difference"],
                        temporary_copy_removed=True)
    save(BUILD / "core-scoring-build.json", build_report)
    print(json.dumps(verified), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--verify-isolated", action="store_true")
    args = parser.parse_args()
    if not args.build and not args.verify_isolated:
        parser.error("Select --build and/or --verify-isolated")
    if args.build:
        build()
    if args.verify_isolated:
        verify()
