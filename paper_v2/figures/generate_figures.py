from __future__ import annotations

import csv
import datetime as dt
import hashlib
import json
import sys
import textwrap
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


ROOT = Path(__file__).resolve().parents[2]
FIG_DIR = Path(__file__).resolve().parent
DATA_DIR = FIG_DIR / "data"
SUMMARY_PATH = ROOT / "outputs/runs/20260827T-phk-v2-s2-q-terminal-summary/summary.json"
OBJECT_PATH = ROOT / "configs/phk_v2/object_numerical_contract.json"
EXPECTED_SUMMARY_SHA256 = "8964ACB687F1BDB4F03C2E0D33891EE3705D4C2ABD271085D0C82A2B4469EA78"
FIXED_PDF_DATE = dt.datetime(2026, 8, 27, 12, 0, tzinfo=dt.timezone.utc)

COLORS = {
    "navy": "#183B56",
    "blue": "#2D6A9F",
    "cyan": "#3CA6A8",
    "green": "#3A8D5D",
    "amber": "#D18B2C",
    "red": "#B94747",
    "gray": "#8B96A3",
    "light": "#EEF3F7",
    "dark": "#263238",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, header: list[str], rows: list[list[object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


def save_figure(fig: mpl.figure.Figure, stem: str) -> list[Path]:
    png = FIG_DIR / f"{stem}.png"
    pdf = FIG_DIR / f"{stem}.pdf"
    fig.savefig(png, dpi=300, bbox_inches="tight", facecolor="white")
    fig.savefig(
        pdf,
        bbox_inches="tight",
        facecolor="white",
        metadata={
            "Title": stem,
            "Author": "PINN-PCM-SCI",
            "Creator": "paper_v2/figures/generate_figures.py",
            "CreationDate": FIXED_PDF_DATE,
            "ModDate": FIXED_PDF_DATE,
        },
    )
    plt.close(fig)
    return [png, pdf]


def add_box(
    ax: mpl.axes.Axes,
    xy: tuple[float, float],
    width: float,
    height: float,
    text: str,
    *,
    face: str,
    edge: str | None = None,
    text_color: str = "white",
    fontsize: float = 9.0,
    linewidth: float = 1.3,
) -> None:
    patch = FancyBboxPatch(
        xy,
        width,
        height,
        boxstyle="round,pad=0.018,rounding_size=0.025",
        facecolor=face,
        edgecolor=edge or face,
        linewidth=linewidth,
    )
    ax.add_patch(patch)
    wrapped_text = "\n".join(textwrap.fill(part, 25) for part in text.splitlines())
    ax.text(
        xy[0] + width / 2,
        xy[1] + height / 2,
        wrapped_text,
        ha="center",
        va="center",
        color=text_color,
        fontsize=fontsize,
        fontweight="semibold",
    )


def arrow(ax: mpl.axes.Axes, start: tuple[float, float], end: tuple[float, float], color: str) -> None:
    ax.add_patch(
        FancyArrowPatch(
            start,
            end,
            arrowstyle="-|>",
            mutation_scale=13,
            linewidth=1.5,
            color=color,
            shrinkA=2,
            shrinkB=2,
        )
    )


def figure_01_workflow() -> tuple[list[Path], list[Path]]:
    rows = [
        ["R0", "Primary-source, code, and license identities", "COMPLETED"],
        ["S0/S0B", "Program, object, split, event, and stop contracts", "COMPLETED"],
        ["S1", "Fixed-source module smokes", "COMPLETED_BOUNDED"],
        ["S2", "12-intent benchmark qualification", "ORACLE_NO_GO"],
        ["S3-S6", "PINN baseline, PHA, KC, formal OOD", "NOT_REACHED"],
        ["S7", "Negative/limits manuscript and reproducibility", "COMPLETED_PACKAGE"],
    ]
    csv_path = DATA_DIR / "workflow.csv"
    write_csv(csv_path, ["stage", "role", "status"], rows)

    fig, ax = plt.subplots(figsize=(12.4, 5.3))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.text(0.02, 0.94, "Qualification before approximation", fontsize=18, fontweight="bold", color=COLORS["navy"])
    ax.text(0.02, 0.885, "Every downstream claim consumes an upstream qualified identity", fontsize=10.5, color=COLORS["dark"])

    xs = [0.02, 0.19, 0.36, 0.53]
    labels = [
        "R0\nSource identities",
        "S0/S0B\nMachine contracts",
        "S1\nModule smokes",
        "S2\nOracle Gate",
    ]
    faces = [COLORS["blue"], COLORS["cyan"], COLORS["green"], COLORS["red"]]
    for x, label, face in zip(xs, labels, faces):
        add_box(ax, (x, 0.57), 0.13, 0.19, label, face=face, fontsize=8.5)
    for left, right in zip(xs[:-1], xs[1:]):
        arrow(ax, (left + 0.13, 0.665), (right, 0.665), COLORS["gray"])

    add_box(
        ax,
        (0.705, 0.61),
        0.265,
        0.15,
        "S3–S6 method attribution + formal OOD\nNOT REACHED",
        face="#E3E7EA",
        edge=COLORS["gray"],
        text_color=COLORS["gray"],
        fontsize=9,
    )
    arrow(ax, (0.66, 0.665), (0.705, 0.685), COLORS["gray"])
    ax.plot([0.681, 0.691], [0.735, 0.60], color=COLORS["red"], linewidth=4, solid_capstyle="round")

    add_box(
        ax,
        (0.53, 0.24),
        0.44,
        0.18,
        "S7 evidence-preserving closeout\nbenchmark / numerical-limits manuscript",
        face=COLORS["amber"],
        fontsize=10,
    )
    arrow(ax, (0.595, 0.57), (0.66, 0.42), COLORS["red"])

    ax.text(0.03, 0.30, "Oracle outcome", fontsize=11, fontweight="bold", color=COLORS["red"])
    ax.text(
        0.03,
        0.205,
        "Two-cycle event contract failed\n+ required control execution failed",
        fontsize=10,
        color=COLORS["dark"],
        linespacing=1.45,
    )
    ax.text(0.03, 0.095, "No neural floor • No PINN method estimand • No GPU/formal run", fontsize=10.5, color=COLORS["navy"], fontweight="semibold")
    outputs = save_figure(fig, "figure-01-workflow")
    return outputs, [csv_path]


def figure_02_source_anatomy() -> tuple[list[Path], list[Path]]:
    rows = [
        ["Sharp paper", "phase-field domain anchor", "A: staggered/RFF/modified MLP", "paper metric not reproduced"],
        ["Sharp repo 4b7029e", "separate long-budget recipe", "isolated GPL comparator", "module smoke only"],
        ["PF a25f75b", "sampling + NTK support control", "A′: phase/hotspot sampling", "module smoke only"],
        ["PirateNet / jaxpi2", "general strong architecture", "adaptive pseudo-time falsifies KC story", "architecture smoke only"],
        ["Causality-RBAR", "causal adaptive support", "separate best-method track", "official code URL 404"],
        ["Miquel et al.", "wall-cell causal-chain inspiration", "transparent dimensionless A′", "not an open oracle"],
    ]
    csv_path = DATA_DIR / "source_anatomy.csv"
    write_csv(csv_path, ["source", "true_role", "transfer", "phk_v2_status"], rows)

    fig, ax = plt.subplots(figsize=(12.5, 7.1))
    ax.axis("off")
    ax.text(0.01, 0.97, "Source anatomy: identity is not reproduction", transform=ax.transAxes, fontsize=18, fontweight="bold", color=COLORS["navy"], va="top")
    ax.text(0.01, 0.91, "Direct source modules (A), PCM adaptations (A′), and evidence status remain separate", transform=ax.transAxes, fontsize=10.5, color=COLORS["dark"], va="top")

    col_labels = ["Primary identity", "True role", "Transfer / control", "PHK-V2 evidence"]
    cell_text = [[textwrap.fill(str(c), 25) for c in row] for row in rows]
    table = ax.table(
        cellText=cell_text,
        colLabels=col_labels,
        colWidths=[0.20, 0.24, 0.29, 0.23],
        cellLoc="left",
        bbox=[0.01, 0.08, 0.98, 0.77],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    for (r, c), cell in table.get_celld().items():
        cell.set_edgecolor("white")
        if r == 0:
            cell.set_facecolor(COLORS["navy"])
            cell.get_text().set_color("white")
            cell.get_text().set_weight("bold")
        else:
            cell.set_facecolor("#F4F7F9" if r % 2 else "#E8EFF4")
            if c == 3:
                cell.get_text().set_color(COLORS["red"] if "not" in rows[r - 1][3] or "404" in rows[r - 1][3] else COLORS["amber"])
                cell.get_text().set_weight("semibold")
    ax.text(0.01, 0.025, "License boundary: Sharp/PF GPL; original jaxpi Penn-restricted; fixed jaxpi2 Apache-2.0. External trees are not packaged.", transform=ax.transAxes, fontsize=9.5, color=COLORS["dark"])
    outputs = save_figure(fig, "figure-02-source-anatomy")
    return outputs, [csv_path]


def figure_03_ladder(summary: dict) -> tuple[list[Path], list[Path]]:
    names = [
        "Manufactured operators",
        "Zero drive, medium",
        "Nominal coarse",
        "Nominal medium",
        "Nominal fine",
        "Medium half-dt",
        "Fine exact replay",
        "Joule-off medium",
        "Conductivity-feedback-off",
        "Latent-heat-off",
        "Wide heater",
        "Narrow interface",
    ]
    statuses = ["COMPLETED"] * 8 + ["FAILED_CONSUMED"] + ["NOT_REACHED"] * 3
    rows = [[i + 1, names[i], statuses[i]] for i in range(12)]
    csv_path = DATA_DIR / "qualification_ladder.csv"
    write_csv(csv_path, ["intent", "identity", "status"], rows)

    fig, ax = plt.subplots(figsize=(12.5, 7.3))
    ax.set_xlim(0, 1)
    ax.set_ylim(-1.1, 12.7)
    ax.axis("off")
    ax.text(0.0, 12.35, "Frozen qualification ladder", fontsize=18, fontweight="bold", color=COLORS["navy"])
    ax.text(0.0, 11.75, "Sequential, intent-first, no rescue or replacement", fontsize=10.5, color=COLORS["dark"])
    for idx, (name, status) in enumerate(zip(names, statuses)):
        y = 10.8 - idx * 0.82
        face = COLORS["green"] if status == "COMPLETED" else COLORS["red"] if status == "FAILED_CONSUMED" else "#D9DEE3"
        text_color = "white" if status != "NOT_REACHED" else COLORS["gray"]
        add_box(ax, (0.02, y), 0.63, 0.55, f"{idx+1:02d}  {name}", face=face, edge=face, text_color=text_color, fontsize=9.4)
        ax.text(0.69, y + 0.275, status.replace("_", " "), va="center", fontsize=9.3, color=face if status != "NOT_REACHED" else COLORS["gray"], fontweight="bold")
        if idx < 11:
            ax.plot([0.073, 0.073], [y - 0.27, y], color=COLORS["gray"], linewidth=1)
    ax.plot([0.02, 0.96], [0.92, 0.92], color=COLORS["red"], linestyle="--", linewidth=1.5)
    ax.text(0.71, 0.48, "STOP BEFORE PINN TRAINING", color=COLORS["red"], fontsize=10.5, fontweight="bold")
    ax.text(0.02, 0.05, f"Terminal: {summary['adjudication']['outcome']}", fontsize=9.2, color=COLORS["navy"], fontweight="semibold")
    ax.text(0.02, -0.62, "Intents 10–12 are not scientific failures; they were never opened after intent 9.", fontsize=9.5, color=COLORS["dark"])
    outputs = save_figure(fig, "figure-03-qualification-ladder")
    return outputs, [csv_path]


def result_path(intent: int, slug: str) -> Path:
    return ROOT / f"outputs/runs/20260827T-phk-v2-s2-intent-{intent:02d}-{slug}/result-intent-{intent:02d}.npz"


def load_result(path: Path) -> dict[str, np.ndarray]:
    with np.load(path, allow_pickle=False) as data:
        return {key: np.array(data[key]) for key in data.files if key != "metadata_json"}


def roi_fraction(data: dict[str, np.ndarray]) -> np.ndarray:
    mask = (np.abs(data["x"]) <= 0.55 + 1e-14) & (data["z"] <= 0.55 + 1e-14)
    weights = data["cell_volumes"][mask]
    active = data["phase"][:, mask] >= 0.5
    return (active * weights[None, :]).sum(axis=1) / weights.sum()


def waveform(t: np.ndarray) -> np.ndarray:
    phase = np.mod(t, 1.0)
    out = np.zeros_like(t, dtype=float)
    up = phase <= 0.05
    hold = (phase > 0.05) & (phase <= 0.30)
    down = (phase > 0.30) & (phase <= 0.35)
    out[up] = 0.75 * phase[up] / 0.05
    out[hold] = 0.75
    out[down] = 0.75 * (0.35 - phase[down]) / 0.05
    return out


def figure_04_trajectories() -> tuple[list[Path], list[Path]]:
    configs = [
        (3, "nominal-coarse", "Coarse", COLORS["gray"]),
        (4, "nominal-medium", "Medium", COLORS["blue"]),
        (5, "nominal-fine", "Fine", COLORS["red"]),
        (6, "medium-half-dt", "Medium half-dt", COLORS["green"]),
    ]
    csv_rows: list[list[object]] = []
    series: list[tuple[str, str, dict[str, np.ndarray], np.ndarray]] = []
    for intent, slug, label, color in configs:
        data = load_result(result_path(intent, slug))
        frac = roi_fraction(data)
        series.append((label, color, data, frac))
        roi = (np.abs(data["x"]) <= 0.55 + 1e-14) & (data["z"] <= 0.55 + 1e-14)
        temp_max = np.max(data["temperature"][:, roi], axis=1)
        for t_value, f_value, temp_value in zip(data["time"], frac, temp_max):
            csv_rows.append([intent, label, f"{t_value:.12g}", f"{f_value:.12g}", f"{temp_value:.12g}"])
    csv_path = DATA_DIR / "event_trajectories.csv"
    write_csv(csv_path, ["intent", "configuration", "time", "roi_phase_fraction", "roi_temperature_max"], csv_rows)

    fig, axes = plt.subplots(2, 1, figsize=(12.5, 7.4), sharex=True, gridspec_kw={"height_ratios": [1.2, 1]})
    ax1, ax2 = axes
    for label, color, data, frac in series:
        linewidth = 2.2 if label == "Fine" else 1.5
        ax1.plot(data["time"], frac, label=label, color=color, linewidth=linewidth)
        roi = (np.abs(data["x"]) <= 0.55 + 1e-14) & (data["z"] <= 0.55 + 1e-14)
        ax2.plot(data["time"], np.max(data["temperature"][:, roi], axis=1), color=color, linewidth=linewidth, label=label)
    for ax in axes:
        for boundary in [0.0, 0.35, 1.0, 1.35, 2.0]:
            ax.axvline(boundary, color="#D6DCE1", linewidth=0.8, zorder=0)
        ax.grid(True, alpha=0.18)
        ax.spines[["top", "right"]].set_visible(False)
    ax1.axhline(0.02, color=COLORS["amber"], linestyle="--", linewidth=1.5, label="Frozen event threshold")
    ax1.set_ylabel("ROI phase fraction")
    ax1.set_ylim(-0.02, 1.0)
    ax1.legend(ncol=3, frameon=False, loc="upper left", fontsize=8.8)
    ax1.set_title("First formation, incomplete recovery, and no new second-cycle crossing", loc="left", fontsize=16, fontweight="bold", color=COLORS["navy"])
    ax2.set_ylabel("Max ROI reduced temperature")
    ax2.set_xlabel("Physical time")
    ax2.set_xlim(0, 2)
    ax2b = ax2.twinx()
    fine_t = series[2][2]["time"]
    ax2b.plot(fine_t, waveform(fine_t), color=COLORS["amber"], linewidth=1.1, alpha=0.8, linestyle=":")
    ax2b.set_ylabel("Applied voltage", color=COLORS["amber"])
    ax2b.tick_params(axis="y", colors=COLORS["amber"])
    ax2b.spines["top"].set_visible(False)
    ax2.text(0.52, 0.08, "off interval", transform=ax2.transAxes, color=COLORS["gray"], fontsize=9)
    outputs = save_figure(fig, "figure-04-event-trajectories")
    return outputs, [csv_path]


def figure_05_convergence(summary: dict) -> tuple[list[Path], list[Path]]:
    order = summary["comparisons"]["coarse_medium"]["component_order"]
    keys = ["coarse_medium", "medium_fine", "medium_medium_half_dt", "fine_exact_replay"]
    labels = ["Coarse–medium", "Medium–fine", "Medium–half-dt", "Fine replay"]
    colors = [COLORS["gray"], COLORS["blue"], COLORS["green"], COLORS["red"]]
    values = np.array([summary["comparisons"][key]["component_deltas"] for key in keys], dtype=float)
    rows: list[list[object]] = []
    for label, row in zip(labels, values):
        for component, value in zip(order, row):
            rows.append([label, component, f"{value:.16g}"])
    csv_path = DATA_DIR / "convergence_components.csv"
    write_csv(csv_path, ["comparison", "component", "difference"], rows)

    fig, ax = plt.subplots(figsize=(12.5, 6.5))
    x = np.arange(len(order))
    width = 0.19
    plot_values = np.maximum(values, 1e-6)
    for idx, (label, color) in enumerate(zip(labels, colors)):
        bars = ax.bar(x + (idx - 1.5) * width, plot_values[idx], width=width, label=label, color=color, alpha=0.9)
        if idx == 3:
            for bar in bars:
                ax.text(bar.get_x() + bar.get_width() / 2, 1.35e-6, "0", ha="center", va="bottom", fontsize=7.5, color=COLORS["red"], rotation=90)
    abbreviations = ["Phase ROI", "Temp ROI", "Current", "Event time", "Phase region", "Recovery"]
    ax.set_xticks(x, abbreviations)
    ax.set_yscale("log")
    ax.set_ylim(7e-7, 0.25)
    ax.set_ylabel("Unclipped component difference (log scale)")
    ax.set_title("Refinement differences decrease; exact replay is zero", loc="left", fontsize=16, fontweight="bold", color=COLORS["navy"])
    ax.grid(True, axis="y", which="both", alpha=0.18)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, ncol=2, fontsize=9)
    ax.text(0.0, -0.17, "These diagnostics do not override the failed two-cycle event contract.", transform=ax.transAxes, fontsize=9.5, color=COLORS["dark"])
    outputs = save_figure(fig, "figure-05-convergence-controls")
    return outputs, [csv_path]


def figure_06_causal_claim(summary: dict) -> tuple[list[Path], list[Path]]:
    nominal = load_result(result_path(4, "nominal-medium"))
    joule_off = load_result(result_path(8, "joule-off-medium"))
    f_nom = roi_fraction(nominal)
    f_off = roi_fraction(joule_off)
    roi_nom = (np.abs(nominal["x"]) <= 0.55 + 1e-14) & (nominal["z"] <= 0.55 + 1e-14)
    roi_off = (np.abs(joule_off["x"]) <= 0.55 + 1e-14) & (joule_off["z"] <= 0.55 + 1e-14)
    t_nom = np.max(nominal["temperature"][:, roi_nom], axis=1)
    t_off = np.max(joule_off["temperature"][:, roi_off], axis=1)
    rows: list[list[object]] = []
    for i, time_value in enumerate(nominal["time"]):
        rows.append([f"{time_value:.12g}", f"{f_nom[i]:.12g}", f"{f_off[i]:.12g}", f"{t_nom[i]:.12g}", f"{t_off[i]:.12g}"])
    csv_path = DATA_DIR / "causal_control.csv"
    write_csv(csv_path, ["time", "nominal_roi_phase", "joule_off_roi_phase", "nominal_roi_temperature_max", "joule_off_roi_temperature_max"], rows)

    fig = plt.figure(figsize=(12.8, 7.1))
    grid = fig.add_gridspec(2, 2, width_ratios=[1.35, 1], hspace=0.24, wspace=0.28)
    ax_phase = fig.add_subplot(grid[0, 0])
    ax_temp = fig.add_subplot(grid[1, 0], sharex=ax_phase)
    ax_claim = fig.add_subplot(grid[:, 1])
    ax_phase.plot(nominal["time"], f_nom, color=COLORS["red"], linewidth=2, label="Nominal")
    ax_phase.plot(joule_off["time"], f_off, color=COLORS["blue"], linewidth=1.8, label="Joule off")
    ax_phase.axhline(0.02, color=COLORS["amber"], linestyle="--", linewidth=1.2)
    ax_phase.set_ylabel("ROI phase fraction")
    ax_phase.set_title("Resolved synthetic Joule control", loc="left", fontsize=15, fontweight="bold", color=COLORS["navy"])
    ax_phase.legend(frameon=False)
    ax_temp.plot(nominal["time"], t_nom, color=COLORS["red"], linewidth=2)
    ax_temp.plot(joule_off["time"], t_off, color=COLORS["blue"], linewidth=1.8)
    ax_temp.set_ylabel("Max ROI temperature")
    ax_temp.set_xlabel("Physical time")
    for ax in [ax_phase, ax_temp]:
        ax.grid(True, alpha=0.18)
        ax.spines[["top", "right"]].set_visible(False)
        ax.set_xlim(0, 2)

    effect = summary["thermal_effect"]
    ax_temp.text(
        0.02,
        0.87,
        f"Peak ΔT = {effect['peak_temperature_difference']:.6f}\nuncertainty = {effect['temperature_joint_space_time_uncertainty']:.6f}",
        transform=ax_temp.transAxes,
        fontsize=8.8,
        color=COLORS["dark"],
        va="top",
    )
    ax_claim.axis("off")
    ax_claim.text(0.0, 0.98, "Final claim boundary", fontsize=16, fontweight="bold", color=COLORS["navy"], va="top")
    add_box(ax_claim, (0.02, 0.72), 0.92, 0.17, "VERIFIED\nSynthetic Joule term has a resolved effect", face=COLORS["green"], fontsize=10)
    add_box(ax_claim, (0.02, 0.48), 0.92, 0.17, "TERMINAL NO-GO\nEvent contract + required-control execution", face=COLORS["red"], fontsize=10)
    add_box(ax_claim, (0.02, 0.24), 0.92, 0.17, "NOT REACHED\nStrong raw • PHA-MF • KC • formal OOD", face="#E3E7EA", edge=COLORS["gray"], text_color=COLORS["gray"], fontsize=10)
    ax_claim.text(0.03, 0.08, "No material validation\nNo PINN superiority or failure claim\nNo GPU or formal result", fontsize=10, color=COLORS["dark"], linespacing=1.55)
    outputs = save_figure(fig, "figure-06-causal-and-claim-boundary")
    return outputs, [csv_path]


def main() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    actual_summary_sha = sha256(SUMMARY_PATH)
    if actual_summary_sha != EXPECTED_SUMMARY_SHA256:
        raise RuntimeError(f"terminal summary identity mismatch: {actual_summary_sha}")
    summary = load_json(SUMMARY_PATH)
    if summary["adjudication"]["outcome"] != "PHK_V2_ORACLE_NO_GO_EVENT_CONTRACT_AND_CONTROL_EXECUTION_FAILURE":
        raise RuntimeError("terminal outcome mismatch")
    if summary["adjudication"]["method_route"] != "STOP_BEFORE_PINN_TRAINING":
        raise RuntimeError("method-route mismatch")

    mpl.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "axes.titlesize": 14,
            "axes.labelsize": 10,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )

    outputs: list[Path] = []
    derived: list[Path] = []
    for make in [
        figure_01_workflow,
        figure_02_source_anatomy,
        lambda: figure_03_ladder(summary),
        figure_04_trajectories,
        lambda: figure_05_convergence(summary),
        lambda: figure_06_causal_claim(summary),
    ]:
        made_outputs, made_data = make()
        outputs.extend(made_outputs)
        derived.extend(made_data)

    source_paths = [
        SUMMARY_PATH,
        OBJECT_PATH,
        result_path(3, "nominal-coarse"),
        result_path(4, "nominal-medium"),
        result_path(5, "nominal-fine"),
        result_path(6, "medium-half-dt"),
        result_path(8, "joule-off-medium"),
    ]
    manifest = {
        "schema_id": "phk-v2-figure-source-manifest-v1",
        "generated_from_existing_evidence_only": True,
        "scientific_compute_performed": False,
        "fixed_generation_date": "2026-08-27",
        "render_environment": {
            "python": sys.version.split()[0],
            "numpy": np.__version__,
            "matplotlib": mpl.__version__,
        },
        "generator": {
            "path": str(Path(__file__).resolve().relative_to(ROOT)).replace("\\", "/"),
            "sha256": sha256(Path(__file__).resolve()),
        },
        "sources": [
            {
                "path": str(path.relative_to(ROOT)).replace("\\", "/"),
                "sha256": sha256(path),
                "bytes": path.stat().st_size,
            }
            for path in source_paths
        ],
        "derived_data": [
            {
                "path": str(path.relative_to(ROOT)).replace("\\", "/"),
                "sha256": sha256(path),
                "bytes": path.stat().st_size,
            }
            for path in sorted(derived)
        ],
        "outputs": [
            {
                "path": str(path.relative_to(ROOT)).replace("\\", "/"),
                "sha256": sha256(path),
                "bytes": path.stat().st_size,
            }
            for path in sorted(outputs)
        ],
        "claim_ceiling": "PHK_V2_ORACLE_NO_GO_NO_PINN_METHOD_OR_EXPERIMENTAL_EVIDENCE",
    }
    (FIG_DIR / "source-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps({"figures": len(outputs) // 2, "derived_csv": len(derived), "source_manifest_sha256": sha256(FIG_DIR / "source-manifest.json")}, indent=2))


if __name__ == "__main__":
    main()
