"""Generate the five PHK-V2.2R terminal nominal figures from bound evidence."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
import numpy as np


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
RUN_ID = "20260830T112225-phk-v22r-v11-nominal-69109cd"
RUN = ROOT / "outputs" / "runs" / RUN_ID

ARMS = {
    "STRONG_RAW": "strong_raw",
    "MF_ONLY": "mf_only",
    "SAMPLER_ONLY": "sampler_only",
    "MF_PLUS_SAMPLER": "mf_plus_sampler",
}
LABELS = {
    "STRONG_RAW": "Strong raw",
    "MF_ONLY": "MF only",
    "SAMPLER_ONLY": "Sampler only",
    "MF_PLUS_SAMPLER": "MF + sampler",
}
COLORS = {
    "STRONG_RAW": "#355070",
    "MF_ONLY": "#6D597A",
    "SAMPLER_ONLY": "#2A9D8F",
    "MF_PLUS_SAMPLER": "#E76F51",
}
NAVY = "#12355B"
BLUE = "#2D6A9F"
GREEN = "#4C956C"
ORANGE = "#E09F3E"
RED = "#C44536"
GRAY = "#8A949E"
LIGHT = "#F3F6F9"

EXPECTED_HASHES = {
    "summary.json": "721D0ADC537F42622F66CFF7266A287D02A626967E8D9A95F1CFC906C26F03FA",
    "nominal-decision.json": "15F4D2B1BF53200872E4D05BDBEB832FB8AB7B04D7189C1B7B8286976C7A2943",
    "strong_raw/evaluation-nominal-v11.json": "E5F3A5CF19C8A11581357AF1BD612C1931DFE077D6F0017F64F20193041153E6",
    "mf_only/evaluation-nominal-v11.json": "50C4F4C6073CFD28FC016C5E813D63BC60177BA98FC90F2C005A471F8A5383CB",
    "sampler_only/evaluation-nominal-v11.json": "457D7786C8AE6080D51AD87AF504F5DFDFFDAFA9010692A68FFE2E4D228CD1E9",
    "mf_plus_sampler/evaluation-nominal-v11.json": "9BC51F8A6E2A26EE52BAE268CB705AB28F81CD2AC09F7D06E315BD4FD0CFD450",
    "strong_raw/prediction-extra-fine-axes.npz": "4BC26A06D9FA702C8E470BBB0B8513B6E03D03BFC70E1A01C9098C818CB487F2",
    "mf_only/prediction-extra-fine-axes.npz": "8691AE454D1AB51687A48F9DF0049E624563DBC743D2DAEC8BC90BEC72D90CAD",
    "sampler_only/prediction-extra-fine-axes.npz": "8BCC4E8AD7B602BAA387D9DB36933A3F049491FF35ACB891518D88863BA45286",
    "mf_plus_sampler/prediction-extra-fine-axes.npz": "09C4C06279F8C53D01384C2422E34223D2186CE6A20E5ED6680C7925214D55C1",
}
EXPECTED_REFERENCE_SHA256 = "0CE36347433983DB3631C9CD92E3FBFDAEF5A692D3370736071696135FFB73CE"
NOMINAL_REFERENCE = (
    ROOT
    / "outputs"
    / "runs"
    / "20260828T-phk-v21-s1-q-06-nominal-extra-fine"
    / "result-intent-06.npz"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_prediction(path: Path) -> dict[str, np.ndarray]:
    with np.load(path, allow_pickle=False) as archive:
        metadata = json.loads(str(archive["metadata_json"].item()))
        if metadata.get("schema_id") != "phk-v22r-prediction-carrier-v1-1":
            raise AssertionError(f"unexpected prediction schema: {path}")
        if metadata.get("reference_fields_read") is not False:
            raise AssertionError(f"prediction is not reference blind: {path}")
        return {
            name: np.asarray(archive[name], dtype=np.float64).copy()
            for name in ("x", "z", "time", "potential", "temperature", "phase", "top_current", "joule_power")
        }


def read_nominal_reference() -> SimpleNamespace:
    if sha256(NOMINAL_REFERENCE) != EXPECTED_REFERENCE_SHA256:
        raise AssertionError("nominal reference drift")
    with np.load(NOMINAL_REFERENCE, allow_pickle=False) as archive:
        metadata = json.loads(str(archive["metadata_json"].item()))
        if metadata.get("schema_id") != "phk-v21-oracle-result-npz-v1":
            raise AssertionError("unexpected nominal reference schema")
        x_flat = np.asarray(archive["x"], dtype=np.float64).copy()
        z_flat = np.asarray(archive["z"], dtype=np.float64).copy()
        grid = SimpleNamespace(
            x_centers=np.unique(x_flat),
            z_centers=np.unique(z_flat),
            cell_x=x_flat,
            cell_z=z_flat,
        )
        return SimpleNamespace(
            grid=grid,
            time=np.asarray(archive["time"], dtype=np.float64).copy(),
            potential=np.asarray(archive["potential"], dtype=np.float64).copy(),
            temperature=np.asarray(archive["temperature"], dtype=np.float64).copy(),
            phase=np.asarray(archive["phase"], dtype=np.float64).copy(),
            top_current=np.asarray(archive["top_current"], dtype=np.float64).copy(),
            joule_power=np.asarray(archive["joule_power"], dtype=np.float64).copy(),
        )


def verify_inputs() -> None:
    for relative, expected in EXPECTED_HASHES.items():
        path = RUN / relative
        if sha256(path) != expected:
            raise AssertionError(f"input evidence drift: {path}")
    decision = read_json(RUN / "nominal-decision.json")
    if decision["status"] != "MVP_NO_GO_NO_BASIC_COMPETENCE":
        raise AssertionError("unexpected nominal outcome")
    if decision["stress_unseal_authorized"] is not False:
        raise AssertionError("stress reference access unexpectedly authorized")


def write_csv(name: str, fieldnames: list[str], rows: list[dict]) -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    with (DATA / name).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def save(fig: plt.Figure, stem: str) -> None:
    fig.savefig(HERE / f"{stem}.png", dpi=300, bbox_inches="tight", facecolor="white")
    fig.savefig(
        HERE / f"{stem}.pdf",
        bbox_inches="tight",
        facecolor="white",
        metadata={
            "Creator": "PHK-V2.2R figure generator",
            "Producer": "Matplotlib",
            "CreationDate": None,
            "ModDate": None,
        },
    )
    plt.close(fig)


def style() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 9,
            "axes.titlesize": 11,
            "axes.labelsize": 9,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "figure.facecolor": "white",
        }
    )


def load_evidence():
    summary = read_json(RUN / "summary.json")
    decision = read_json(RUN / "nominal-decision.json")
    evaluations = {
        arm: read_json(RUN / folder / "evaluation-nominal-v11.json")
        for arm, folder in ARMS.items()
    }
    predictions = {
        arm: read_prediction(RUN / folder / "prediction-extra-fine-axes.npz")
        for arm, folder in ARMS.items()
    }
    reference = read_nominal_reference()
    return summary, decision, evaluations, predictions, reference


def figure_01(decision: dict) -> None:
    rows = [
        {"stage": "P0 v1.1", "status": "PASS", "evidence": "16 focused / 47 combined"},
        {"stage": "V100 nominal", "status": "COMPLETE", "evidence": "4 arms, 1000 updates"},
        {"stage": "Local scoring", "status": "FAIL", "evidence": "0/4 hard guards"},
        {"stage": "Decision", "status": "NO-GO", "evidence": "no basic competence"},
        {"stage": "Confirmation", "status": "NOT RUN", "evidence": "not authorized"},
        {"stage": "Stress refs", "status": "SEALED", "evidence": "unread"},
    ]
    write_csv("figure-01-terminal-route.csv", ["stage", "status", "evidence"], rows)
    fig, ax = plt.subplots(figsize=(12.5, 3.4))
    ax.set_xlim(0, 12.5)
    ax.set_ylim(0, 3.4)
    ax.axis("off")
    colors = [GREEN, GREEN, RED, RED, GRAY, NAVY]
    for index, (row, color) in enumerate(zip(rows, colors, strict=True)):
        x = 0.2 + index * 2.05
        box = FancyBboxPatch(
            (x, 1.02), 1.75, 1.25,
            boxstyle="round,pad=0.04,rounding_size=0.08",
            facecolor=color, edgecolor="white", linewidth=1.5,
        )
        ax.add_patch(box)
        ax.text(x + 0.875, 1.91, row["stage"], ha="center", color="white", weight="bold")
        ax.text(x + 0.875, 1.58, row["status"], ha="center", color="white", fontsize=8, weight="bold")
        ax.text(x + 0.875, 1.25, row["evidence"], ha="center", color="white", fontsize=7)
        if index < len(rows) - 1:
            ax.add_patch(
                FancyArrowPatch(
                    (x + 1.76, 1.64), (x + 2.03, 1.64),
                    arrowstyle="-|>", mutation_scale=12, color=NAVY,
                )
            )
    ax.text(6.25, 2.92, "Frozen PHK-V2.2R v1.1 route and terminal outcome", ha="center", color=NAVY, fontsize=14, weight="bold")
    ax.text(
        6.25, 0.42,
        f"{decision['status']}: no seed change, extension, rescue axis, candidate freeze, or stress-reference access.",
        ha="center", color=RED, weight="bold",
    )
    save(fig, "figure-01-terminal-route")


def _training_rows(summary: dict) -> tuple[list[dict], dict[str, list[dict]]]:
    summary_by_arm = {item["arm"]: item for item in summary["runs"]}
    rows: list[dict] = []
    traces: dict[str, list[dict]] = {}
    for arm, folder in ARMS.items():
        log_rows = [
            json.loads(line)
            for line in (RUN / folder / "training-log.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        traces[arm] = log_rows
        item = summary_by_arm[arm]
        rows.append(
            {
                "arm": arm,
                "seconds_per_update": item["seconds_per_update"],
                "wall_seconds": item["wall_seconds"],
                "peak_gpu_memory_gb": item["peak_gpu_memory_bytes"] / 1.0e9,
                "final_total_loss": item["final_loss"],
                "minimum_total_loss": item["minimum_loss"],
                "final_pde_loss": log_rows[-1]["pde_loss"],
                "first_pde_loss": log_rows[0]["pde_loss"],
            }
        )
    return rows, traces


def figure_02(summary: dict) -> None:
    rows, traces = _training_rows(summary)
    write_csv("figure-02-training-compute.csv", list(rows[0]), rows)
    fig, axes = plt.subplots(1, 3, figsize=(13.2, 3.8))
    for arm, trace in traces.items():
        update = [row["update"] for row in trace]
        pde = [row["pde_loss"] for row in trace]
        axes[0].semilogy(update, pde, label=LABELS[arm], color=COLORS[arm], linewidth=1.8)
    axes[0].set_title("(a) Logged physics residual")
    axes[0].set_xlabel("Adam update")
    axes[0].set_ylabel("PDE loss")
    axes[0].grid(alpha=0.2)
    axes[0].legend(frameon=False, fontsize=7)

    x = np.arange(len(rows))
    axes[1].bar(x, [row["seconds_per_update"] for row in rows], color=[COLORS[row["arm"]] for row in rows])
    axes[1].set_xticks(x, [LABELS[row["arm"]] for row in rows], rotation=25, ha="right")
    axes[1].set_ylabel("Seconds / update")
    axes[1].set_title("(b) Measured V100 cost")
    axes[1].set_ylim(0, 0.62)
    axes[1].grid(axis="y", alpha=0.2)

    axes[2].bar(x, [row["peak_gpu_memory_gb"] for row in rows], color=[COLORS[row["arm"]] for row in rows])
    axes[2].set_xticks(x, [LABELS[row["arm"]] for row in rows], rotation=25, ha="right")
    axes[2].set_ylabel("Peak allocated GPU memory (GB)")
    axes[2].set_title("(c) Peak GPU allocation")
    axes[2].set_ylim(0, 1.3)
    axes[2].grid(axis="y", alpha=0.2)
    fig.suptitle("All arms trained finitely and reduced PDE loss, but training convergence did not imply event competence", color=NAVY, weight="bold")
    fig.tight_layout()
    save(fig, "figure-02-training-and-compute")


def figure_03(evaluations: dict, predictions: dict, reference) -> None:
    peak_indices = [int(cycle["peak_time_index"]) for cycle in evaluations["STRONG_RAW"]["reference_event"]["cycles"]]
    rows = []
    for cycle, index in enumerate(peak_indices, 1):
        rows.append({"cycle": cycle, "time": float(reference.time[index]), "reference_peak_roi_fraction": evaluations["STRONG_RAW"]["reference_event"]["cycles"][cycle - 1]["peak_roi_fraction"]})
    write_csv("figure-03-phase-snapshots.csv", list(rows[0]), rows)
    nx = reference.grid.x_centers.size
    nz = reference.grid.z_centers.size
    fields = [("Reference", reference.phase)] + [(LABELS[arm], predictions[arm]["phase"]) for arm in ARMS]
    fig, axes = plt.subplots(2, 5, figsize=(13.5, 5.4), sharex=True, sharey=True)
    image = None
    for row_index, time_index in enumerate(peak_indices):
        for col_index, (label, phase) in enumerate(fields):
            ax = axes[row_index, col_index]
            image = ax.imshow(
                phase[time_index].reshape(nz, nx),
                origin="lower", aspect="auto", vmin=0.0, vmax=1.0,
                extent=[reference.grid.x_centers[0], reference.grid.x_centers[-1], reference.grid.z_centers[0], reference.grid.z_centers[-1]],
                cmap="magma",
            )
            if row_index == 0:
                ax.set_title(label)
            if col_index == 0:
                ax.set_ylabel(f"Cycle {row_index + 1}\nz")
            if row_index == 1:
                ax.set_xlabel("x")
            if col_index > 0:
                max_phase = float(np.max(phase[time_index]))
                ax.text(0.04, 0.93, f"max={max_phase:.3f}", transform=ax.transAxes, color="white", fontsize=7, va="top")
            else:
                ax.text(0.04, 0.93, f"t={reference.time[time_index]:.3f}", transform=ax.transAxes, color="white", fontsize=7, va="top")
    assert image is not None
    fig.subplots_adjust(top=0.84, wspace=0.08, hspace=0.15, right=0.91)
    colorbar_axis = fig.add_axes([0.93, 0.19, 0.014, 0.60])
    colorbar = fig.colorbar(image, cax=colorbar_axis)
    colorbar.set_label("Phase field")
    fig.suptitle("Reference phase events versus four final-checkpoint PINN predictions", color=NAVY, weight="bold")
    save(fig, "figure-03-phase-event-collapse")


def _roi_mask(reference) -> np.ndarray:
    legacy = read_json(ROOT / "configs" / "phk_v2" / "object_numerical_contract.json")
    roi = legacy["qualification_event"]["roi"]
    return (
        (np.abs(reference.grid.cell_x) <= float(roi["abs_x_max"]))
        & (reference.grid.cell_z >= float(roi["z_min"]))
        & (reference.grid.cell_z <= float(roi["z_max"]))
    )


def figure_04(predictions: dict, reference) -> None:
    roi = _roi_mask(reference)
    time = reference.time
    traces = {"Reference": {
        "phase_roi_fraction": np.mean(reference.phase[:, roi] >= 0.5, axis=1),
        "top_current": reference.top_current,
        "max_temperature": np.max(reference.temperature, axis=1),
        "joule_power": reference.joule_power,
    }}
    for arm, prediction in predictions.items():
        traces[arm] = {
            "phase_roi_fraction": np.mean(prediction["phase"][:, roi] >= 0.5, axis=1),
            "top_current": prediction["top_current"],
            "max_temperature": np.max(prediction["temperature"], axis=1),
            "joule_power": prediction["joule_power"],
        }
    csv_rows = []
    stride = 10
    for index in range(0, time.size, stride):
        for identity, values in traces.items():
            csv_rows.append({
                "time": float(time[index]),
                "identity": identity,
                "phase_roi_fraction": float(values["phase_roi_fraction"][index]),
                "top_current": float(values["top_current"][index]),
                "max_temperature": float(values["max_temperature"][index]),
                "joule_power": float(values["joule_power"][index]),
            })
    write_csv("figure-04-device-qoi.csv", list(csv_rows[0]), csv_rows)
    fig, axes = plt.subplots(2, 2, figsize=(12.5, 7.0), sharex=True)
    definitions = [
        ("phase_roi_fraction", "Active phase fraction in ROI", "(a) Phase event support"),
        ("max_temperature", "Maximum temperature", "(b) Thermal response"),
        ("top_current", "Top terminal current", "(c) Electrical response"),
        ("joule_power", "Integrated Joule power", "(d) Joule response"),
    ]
    for ax, (key, ylabel, title) in zip(axes.ravel(), definitions, strict=True):
        ax.plot(time, traces["Reference"][key], color="black", linewidth=2.1, label="Reference")
        for arm in ARMS:
            ax.plot(time, traces[arm][key], color=COLORS[arm], linewidth=1.15, alpha=0.88, label=LABELS[arm])
        ax.set_title(title)
        ax.set_ylabel(ylabel)
        ax.grid(alpha=0.2)
    axes[1, 0].set_xlabel("Dimensionless time")
    axes[1, 1].set_xlabel("Dimensionless time")
    axes[0, 0].axhline(0.02, color=RED, linestyle="--", linewidth=1.0, label="event fraction threshold")
    axes[0, 1].legend(frameon=False, fontsize=7, ncol=2)
    fig.suptitle("Device-level quantities reveal a shared failure to reproduce both phase events", color=NAVY, weight="bold")
    fig.tight_layout()
    save(fig, "figure-04-device-qoi")


def figure_05(evaluations: dict, decision: dict) -> None:
    metric_names = [
        ("phase_roi_continuous_rms", "Phase ROI RMS"),
        ("temperature_roi_nrmse_by_0_45", "Temperature nRMSE"),
        ("terminal_current_trace_nrmse", "Current nRMSE"),
        ("pulse_energy_relative_error", "Pulse-energy rel. error"),
    ]
    rows = []
    matrix = []
    for arm in ARMS:
        report = evaluations[arm]
        values = [float(report["metrics"][name]) for name, _ in metric_names]
        matrix.append(values)
        rows.append({
            "arm": arm,
            "eligible": decision["eligible"][arm],
            "hard_guards_passed": report["hard_guards"]["passed"],
            "primary": report["metrics"]["time_averaged_phase_region_symmetric_difference"],
            **{name: value for (name, _), value in zip(metric_names, values, strict=True)},
        })
    write_csv("figure-05-metrics-and-claim-boundary.csv", list(rows[0]), rows)
    matrix_array = np.asarray(matrix)
    fig = plt.figure(figsize=(13.0, 4.8))
    grid = fig.add_gridspec(1, 2, width_ratios=[1.45, 1.0], wspace=0.25)
    ax = fig.add_subplot(grid[0, 0])
    image = ax.imshow(matrix_array, aspect="auto", cmap="YlOrRd", vmin=0.0, vmax=max(1.1, float(matrix_array.max())))
    ax.set_xticks(np.arange(len(metric_names)), [label for _, label in metric_names], rotation=20, ha="right")
    ax.set_yticks(np.arange(len(ARMS)), [LABELS[arm] for arm in ARMS])
    for i in range(matrix_array.shape[0]):
        for j in range(matrix_array.shape[1]):
            ax.text(j, i, f"{matrix_array[i, j]:.3f}", ha="center", va="center", fontsize=8, color="black")
    ax.set_title("(a) Nominal local-reference errors")
    fig.colorbar(image, ax=ax, shrink=0.82, label="Error (metric-specific scale)")

    ax2 = fig.add_subplot(grid[0, 1])
    ax2.set_xlim(0, 1)
    ax2.set_ylim(0, 1)
    ax2.axis("off")
    boundary = [
        (0.87, "VERIFIED", "4/4 finite V100 runs", GREEN),
        (0.70, "VERIFIED", "PDE loss decreased", GREEN),
        (0.53, "FAILED", "0/4 reproduced events", RED),
        (0.36, "NO-GO", "No eligible candidate", RED),
        (0.19, "SEALED", "Stress cases not opened", NAVY),
    ]
    for y, status, text, color in boundary:
        box = FancyBboxPatch((0.05, y - 0.055), 0.90, 0.11, boxstyle="round,pad=0.02", facecolor=color, edgecolor="white")
        ax2.add_patch(box)
        ax2.text(0.10, y, status, color="white", va="center", weight="bold")
        ax2.text(0.38, y, text, color="white", va="center")
    ax2.set_title("(b) Evidence and claim boundary")
    fig.suptitle("Scalar errors are subordinate to competence: the small primary value reflects a missed localized event", color=NAVY, weight="bold")
    save(fig, "figure-05-metrics-and-claim-boundary")


def write_source_manifest() -> None:
    inputs = []
    for relative in EXPECTED_HASHES:
        path = RUN / relative
        inputs.append({
            "path": str(path.relative_to(ROOT)).replace("\\", "/"),
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        })
    reference_path = NOMINAL_REFERENCE
    inputs.append({
        "path": str(reference_path.relative_to(ROOT)).replace("\\", "/"),
        "bytes": reference_path.stat().st_size,
        "sha256": sha256(reference_path),
        "role": "NOMINAL_DEVELOPMENT_LOCAL_ONLY",
    })
    outputs = []
    for path in sorted(list(HERE.glob("figure-*.png")) + list(HERE.glob("figure-*.pdf")) + list(DATA.glob("*.csv"))):
        outputs.append({
            "path": str(path.relative_to(ROOT)).replace("\\", "/"),
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        })
    payload = {
        "schema_id": "phk-v22r-figure-source-manifest-v1",
        "run_id": RUN_ID,
        "terminal_outcome": "MVP_NO_GO_NO_BASIC_COMPETENCE",
        "nominal_reference_read_for_local_figures": True,
        "stress_references_read": False,
        "stress_results_present": False,
        "generator_sha256": sha256(Path(__file__)),
        "inputs": inputs,
        "outputs": outputs,
    }
    (HERE / "source-manifest.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def main() -> None:
    style()
    verify_inputs()
    summary, decision, evaluations, predictions, reference = load_evidence()
    figure_01(decision)
    figure_02(summary)
    figure_03(evaluations, predictions, reference)
    figure_04(predictions, reference)
    figure_05(evaluations, decision)
    write_source_manifest()
    print("PHK_V22R_FIVE_FIGURES_GENERATED")


if __name__ == "__main__":
    main()
