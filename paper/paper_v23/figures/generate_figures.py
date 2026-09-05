from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap
from matplotlib.patches import FancyBboxPatch


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DATA_PATH = HERE / "data" / "lf3_terminal_metrics.json"
LF4_DATA_PATH = HERE / "data" / "lf4_terminal_metrics.json"
PREDICTION_PATH = ROOT / "outputs" / "runs" / "20260904T150300Z-phk-v23-lf3-phase-latent-97a5b74" / "prediction-t0-step-1200.npz"
REFERENCE_PATH = ROOT / "outputs" / "runs" / "20260828T-phk-v21-s1-q-06-nominal-extra-fine" / "result-intent-06.npz"

NAVY = "#17324d"
BLUE = "#3274a1"
TEAL = "#2a9d8f"
ORANGE = "#e76f51"
GOLD = "#e9c46a"
RED = "#b6403a"
GRAY = "#6b7280"
LIGHT = "#eef3f7"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def save(fig: plt.Figure, stem: str) -> list[Path]:
    paths = [HERE / f"{stem}.png", HERE / f"{stem}.pdf"]
    fig.savefig(paths[0], dpi=240, bbox_inches="tight", facecolor="white")
    fig.savefig(paths[1], bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return paths


def setup() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 9,
            "axes.titlesize": 10,
            "axes.labelsize": 9,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "legend.frameon": False,
            "figure.dpi": 120,
        }
    )


def recovery_ladder(data: dict) -> list[Path]:
    rows = data["route_ladder"]
    fig, ax = plt.subplots(figsize=(10.2, 3.9))
    x = np.arange(len(rows))
    values = [row["phase_maximum"] for row in rows]
    colors = [GRAY, RED, GOLD, BLUE, TEAL]
    bars = ax.bar(x, values, color=colors, width=0.67, edgecolor="white", linewidth=1.2)
    ax.axhline(0.5, color=RED, linestyle="--", linewidth=1.2, label="event threshold $\\phi=0.5$")
    ax.axhline(0.9, color=NAVY, linestyle=":", linewidth=1.2, label="LF3 carrier phase-max gate")
    ax.set_ylim(0, 1.08)
    ax.set_ylabel("Full-medium phase maximum")
    ax.set_xticks(x, [f"{row['stage']}\n{row['event_state']}" for row in rows])
    for bar, row in zip(bars, rows):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.025,
            f"{row['phase_maximum']:.3f}",
            ha="center",
            va="bottom",
            fontweight="bold",
            color=NAVY,
        )
    ax.set_title("Representation and supervision repairs progressively recover the rare phase event")
    ax.legend(loc="upper left", ncol=2)
    ax.text(
        0.995,
        -0.31,
        "Single-seed nominal development evidence; LF3 still fails the frozen recall gate.",
        transform=ax.transAxes,
        ha="right",
        color=GRAY,
        fontsize=8,
    )
    fig.tight_layout()
    return save(fig, "figure-01-recovery-ladder")


def event_metrics(data: dict) -> list[Path]:
    source = data["full_medium_event_metrics"]
    methods = list(source)
    colors = [NAVY, GOLD, BLUE, TEAL]
    fig, axes = plt.subplots(1, 3, figsize=(11.2, 3.7))
    panels = [
        ("recall", "Recall", (0, 1.08), (0.9, None)),
        ("precision", "Precision", (0, 1.08), (0.8, None)),
        ("active_mass_ratio", "Active-mass ratio", (0, 6.35), (0.8, 1.2)),
    ]
    width = 0.36
    positions = np.arange(len(methods))
    for ax, (key, title, ylim, gate) in zip(axes, panels):
        for cycle, offset, hatch in [("cycle_1", -width / 2, ""), ("cycle_2", width / 2, "//")]:
            vals = [source[m][cycle][key] for m in methods]
            bars = ax.bar(
                positions + offset,
                vals,
                width,
                color=colors,
                alpha=0.9,
                edgecolor="white",
                linewidth=0.8,
                hatch=hatch,
                label="cycle 1" if cycle == "cycle_1" else "cycle 2",
            )
            for bar, value in zip(bars, vals):
                if value > 0:
                    ax.text(bar.get_x() + bar.get_width() / 2, value + 0.02 * ylim[1], f"{value:.2f}", ha="center", fontsize=6.8)
        if gate[1] is None:
            ax.axhline(gate[0], color=RED, linestyle="--", linewidth=1)
        else:
            ax.axhspan(gate[0], gate[1], color=TEAL, alpha=0.13)
            ax.axhline(1.0, color=TEAL, linestyle="--", linewidth=1)
        ax.set_ylim(*ylim)
        ax.set_title(title)
        ax.set_xticks(positions, methods, rotation=25, ha="right")
        ax.grid(axis="y", alpha=0.18)
    axes[0].legend(loc="lower left")
    fig.suptitle("LF3 corrects LF1 overbreadth but remains a high-precision, incomplete-support carrier", color=NAVY, fontweight="bold")
    fig.tight_layout()
    return save(fig, "figure-02-full-medium-event-metrics")


def local_error_gap(data: dict) -> list[Path]:
    source = data["local_extra_fine_metrics"]
    baseline = source["LF_ONLY"]
    methods = ["LF1 B0", "LF1 final", "LF2 M0", "LF3 T0"]
    metrics = [
        ("phase_roi_rms", "Phase ROI RMS"),
        ("phase_symmetric_difference", "Phase support error"),
        ("temperature_roi_rms", "Temperature ROI RMS"),
        ("current_nrmse", "Current nRMSE"),
        ("potential_rms", "Potential RMS"),
    ]
    ratios = np.asarray([[source[m][key] / baseline[key] for key, _ in metrics] for m in methods])
    fig, ax = plt.subplots(figsize=(10.7, 4.1))
    width = 0.19
    x = np.arange(len(metrics))
    colors = [GOLD, ORANGE, BLUE, TEAL]
    for idx, method in enumerate(methods):
        offset = (idx - 1.5) * width
        ax.bar(x + offset, ratios[idx], width, label=method, color=colors[idx])
    ax.axhline(1.0, color=NAVY, linestyle="--", linewidth=1.2, label="direct LF_ONLY")
    ax.set_yscale("log")
    ax.set_ylabel("Error ratio to direct LF_ONLY (lower is better)")
    ax.set_xticks(x, [label for _, label in metrics])
    ax.set_ylim(0.8, max(100, ratios.max() * 1.25))
    ax.grid(axis="y", which="both", alpha=0.18)
    ax.legend(ncol=3, loc="upper left")
    ax.set_title("Solver recovery narrows the gap, but the strongest direct baseline remains far ahead")
    fig.tight_layout()
    return save(fig, "figure-03-local-error-gap")


def phase_snapshots() -> list[Path]:
    with np.load(PREDICTION_PATH, allow_pickle=False) as pred, np.load(REFERENCE_PATH, allow_pickle=False) as ref:
        x = pred["x"]
        z = pred["z"]
        time = pred["time"]
        indices = [140, 634]
        pred_slices = [pred["phase"][idx].reshape(len(z), len(x)) for idx in indices]
        ref_slices = [ref["phase"][idx].reshape(len(z), len(x)) for idx in indices]
    fig, axes = plt.subplots(2, 3, figsize=(10.4, 5.5), sharex=True, sharey=True)
    support_map = ListedColormap(["#f2f4f6", TEAL, RED, BLUE])
    for row, (idx, ref_phase, pred_phase) in enumerate(zip(indices, ref_slices, pred_slices)):
        axes[row, 0].imshow(ref_phase, origin="lower", extent=[x.min(), x.max(), z.min(), z.max()], vmin=0, vmax=1, cmap="magma", aspect="auto")
        axes[row, 1].imshow(pred_phase, origin="lower", extent=[x.min(), x.max(), z.min(), z.max()], vmin=0, vmax=1, cmap="magma", aspect="auto")
        ref_active = ref_phase >= 0.5
        pred_active = pred_phase >= 0.5
        classes = np.zeros_like(ref_phase, dtype=np.int8)
        classes[ref_active & pred_active] = 1
        classes[ref_active & ~pred_active] = 2
        classes[~ref_active & pred_active] = 3
        axes[row, 2].imshow(classes, origin="lower", extent=[x.min(), x.max(), z.min(), z.max()], vmin=0, vmax=3, cmap=support_map, aspect="auto")
        axes[row, 0].set_ylabel(f"cycle {row + 1}\nz")
        axes[row, 2].text(0.98, 0.93, f"t={time[idx]:.4f}", transform=axes[row, 2].transAxes, ha="right", va="top", fontsize=8, color=NAVY)
    for ax, title in zip(axes[0], ["Extra-fine reference", "LF3 T0", "Threshold support audit"]):
        ax.set_title(title)
    for ax in axes[-1]:
        ax.set_xlabel("x")
    axes[0, 2].text(0.02, 0.08, "green overlap\nred missed\nblue excess", transform=axes[0, 2].transAxes, fontsize=7.5, color=NAVY, va="bottom")
    fig.suptitle("Localized event topology is recovered, but boundary support remains incomplete", color=NAVY, fontweight="bold")
    fig.tight_layout()
    return save(fig, "figure-04-phase-support-snapshots")


def evidence_gates(data: dict) -> list[Path]:
    fig, ax = plt.subplots(figsize=(10.4, 3.8))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 4)
    ax.axis("off")
    boxes = [
        (0.25, 2.5, 2.7, 1.05, "Level 1: carrier competence", "FAIL", RED, "recall 0.806 / 0.769 < 0.90"),
        (3.65, 2.5, 2.7, 1.05, "Level 2: PINN Pareto", "NOT REACHED", GRAY, "P0 correctly stopped at 0 updates"),
        (7.05, 2.5, 2.7, 1.05, "Level 3: direct baseline", "NOT REACHED", GRAY, "no candidate or paper-positive claim"),
    ]
    for x, y, w, h, title, status, color, detail in boxes:
        patch = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.03,rounding_size=0.08", linewidth=1.5, edgecolor=color, facecolor="white")
        ax.add_patch(patch)
        ax.text(x + 0.12, y + 0.75, title, color=NAVY, fontweight="bold")
        ax.text(x + 0.12, y + 0.46, status, color=color, fontweight="bold")
        ax.text(x + 0.12, y + 0.16, detail, color=GRAY, fontsize=8)
    ax.annotate("", xy=(3.5, 3.02), xytext=(3.08, 3.02), arrowprops={"arrowstyle": "->", "color": GRAY})
    ax.annotate("", xy=(6.9, 3.02), xytext=(6.48, 3.02), arrowprops={"arrowstyle": "->", "color": GRAY})
    ax.text(0.3, 1.6, "Supported now", color=TEAL, fontweight="bold")
    ax.text(0.3, 1.25, "Representation + supervision choices can recover valid, well-timed rare events after cold collapse.", color=NAVY)
    ax.text(0.3, 0.9, "The remaining error is predominantly missed support, not diffuse false-positive mass.", color=NAVY)
    ax.text(0.3, 0.45, "Not supported", color=RED, fontweight="bold")
    ax.text(1.45, 0.45, "carrier success; physics refinement; PINN-specific gain; superiority to LF_ONLY; OOD/stress robustness.", color=NAVY)
    ax.set_title("Competence-first gates prevent a near-pass from becoming an unsupported method claim", color=NAVY, fontweight="bold", pad=10)
    fig.tight_layout()
    return save(fig, "figure-05-evidence-gates")


def interface_boundary_geometry(data: dict) -> list[Path]:
    source = data["cpu_boundary_geometry"]
    fn = source["fn_graph_distance"]
    fp = source["fp_graph_distance"]
    fig, axes = plt.subplots(1, 2, figsize=(9.7, 3.8), gridspec_kw={"width_ratios": [1.0, 1.35]})
    labels = ["False negatives", "False positives"]
    boundary = np.asarray([fn["0"], fp["0"]], dtype=float)
    adjacent = np.asarray([fn["1"], fp["1"]], dtype=float)
    x = np.arange(2)
    axes[0].bar(x, boundary, color=TEAL, label="teacher boundary (distance 0)")
    axes[0].bar(x, adjacent, bottom=boundary, color=GOLD, label="one graph step away")
    axes[0].set_xticks(x, labels)
    axes[0].set_ylabel("Full-medium node count")
    axes[0].set_title("LF3 errors are concentrated at the event interface")
    axes[0].legend(loc="upper right", fontsize=8)
    for idx, (bnd, adj) in enumerate(zip(boundary, adjacent)):
        axes[0].text(idx, bnd * 0.5, f"{bnd / (bnd + adj):.1%}\nat boundary", ha="center", va="center", color="white", fontweight="bold")
    quantiles = [0.0012280054511396089, 0.12952850518173212, 0.35014104749572733, 0.7890361004360981, 1.459346159020768, 2.0094926205441146, 3.4985109413202036]
    qlabels = ["min", "10%", "25%", "50%", "75%", "90%", "max"]
    axes[1].plot(np.arange(len(quantiles)), quantiles, marker="o", color=BLUE, linewidth=2)
    axes[1].axhline(source["boundary_logit_margin_median"], color=TEAL, linestyle="--", linewidth=1)
    axes[1].set_xticks(np.arange(len(quantiles)), qlabels)
    axes[1].set_ylabel("Absolute teacher logit margin")
    axes[1].set_title("The exposed interface spans near-threshold and easy nodes")
    axes[1].grid(axis="y", alpha=0.18)
    fig.suptitle("CPU-G localizes the remaining support error without claiming a mechanism", color=NAVY, fontweight="bold")
    fig.tight_layout()
    return save(fig, "figure-06-interface-boundary-geometry")


def lf4_development_ablation(data: dict) -> list[Path]:
    arms = data["development_arms"]
    order = ["DEV-G", "DEV-M", "DEV-C"]
    colors = [GRAY, TEAL, ORANGE]
    fig, axes = plt.subplots(1, 2, figsize=(10.8, 4.0))
    x = np.arange(3)
    rmin = [arms[name]["rmin"] for name in order]
    bars = axes[0].bar(x, rmin, color=colors)
    axes[0].axhline(data["gates"]["rmin_strict"], color=RED, linestyle="--", linewidth=1.2, label="strict recall gate")
    axes[0].set_ylim(0.75, 1.0)
    axes[0].set_ylabel("Minimum cycle-wise recall")
    axes[0].set_xticks(x, [arms[name]["label"] for name in order], rotation=18, ha="right")
    axes[0].legend(loc="lower right")
    for bar, value in zip(bars, rmin):
        axes[0].text(bar.get_x() + bar.get_width() / 2, value + 0.006, f"{value:.3f}", ha="center", color=NAVY, fontweight="bold")
    errors = [arms[name]["phase_weighted_mse"] for name in order]
    bars = axes[1].bar(x, errors, color=colors)
    axes[1].axhline(data["gates"]["phase_weighted_mse_maximum"], color=RED, linestyle="--", linewidth=1.2, label="entry error limit")
    axes[1].set_yscale("log")
    axes[1].set_ylabel("Full-medium phase weighted MSE")
    axes[1].set_xticks(x, [arms[name]["label"] for name in order], rotation=18, ha="right")
    axes[1].legend(loc="upper left")
    for bar, value in zip(bars, errors):
        axes[1].text(bar.get_x() + bar.get_width() / 2, value * 1.12, f"{value:.4f}", ha="center", fontsize=8)
    fig.suptitle("Matched LF4 screen: interface exposure improves recall; threshold BCE trades away field fidelity", color=NAVY, fontweight="bold")
    fig.tight_layout()
    return save(fig, "figure-07-lf4-development-ablation")


def lf4_physics_pareto(data: dict) -> list[Path]:
    arms = data["development_arms"]
    fig, ax = plt.subplots(figsize=(10.6, 4.2))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 4.1)
    ax.axis("off")
    boxes = [
        (0.25, 2.55, 2.55, 1.05, "DEV-G", "NO ENTRY", RED, "timing failed in both cycles"),
        (3.05, 2.55, 2.55, 1.05, "DEV-M", "BOUNDARY EXPOSURE +", TEAL, "Rmin 0.819→0.909; cycle-1 timing failed"),
        (5.85, 2.55, 2.55, 1.05, "DEV-C", "NO ENTRY", RED, "timing passed; phase error 15.8× T0"),
        (7.15, 0.65, 2.55, 1.05, "Label-free P0", "NOT RUN", GRAY, "no eligible development carrier"),
    ]
    for x, y, w, h, title, status, color, detail in boxes:
        box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.03,rounding_size=0.08", linewidth=1.5, edgecolor=color, facecolor="white")
        ax.add_patch(box)
        ax.text(x + 0.12, y + 0.75, title, color=NAVY, fontweight="bold")
        ax.text(x + 0.12, y + 0.46, status, color=color, fontweight="bold", fontsize=8.5)
        ax.text(x + 0.12, y + 0.16, detail, color=GRAY, fontsize=7.6)
    ax.annotate("", xy=(2.98, 3.08), xytext=(2.83, 3.08), arrowprops={"arrowstyle": "->", "color": GRAY})
    ax.annotate("", xy=(5.78, 3.08), xytext=(5.63, 3.08), arrowprops={"arrowstyle": "->", "color": GRAY})
    ax.annotate("", xy=(8.35, 1.78), xytext=(7.45, 2.50), arrowprops={"arrowstyle": "->", "color": GRAY, "linestyle": "--"})
    ax.text(0.3, 1.45, "Mechanism result", color=TEAL, fontweight="bold")
    ax.text(0.3, 1.12, f"Boundary exposure passed the frozen matched gate (ΔRmin={data['mechanism_decision']['M_minus_G']:.3f}).", color=NAVY)
    ax.text(0.3, 0.78, "Threshold-aligned BCE did not preserve recovery/field quality, so it is not the load-bearing mechanism.", color=NAVY)
    ax.text(0.3, 0.35, "No selected carrier ⇒ no physics-objective ratio, no PINN Pareto, and no candidate claim.", color=RED, fontweight="bold")
    ax.set_title("LF4 advances mechanism attribution but does not reach the physics-Pareto stage", color=NAVY, fontweight="bold", pad=10)
    fig.tight_layout()
    return save(fig, "figure-08-lf4-physics-pareto")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Generate paper_v23 evidence figures")
    parser.add_argument("--lf4-only", action="store_true", help="Generate LF4 figures 6–8 without rewriting the LF3 source manifest")
    args = parser.parse_args(argv)
    setup()
    if args.lf4_only:
        data = json.loads(LF4_DATA_PATH.read_text(encoding="utf-8"))
        outputs: list[Path] = []
        outputs.extend(interface_boundary_geometry(data))
        outputs.extend(lf4_development_ablation(data))
        outputs.extend(lf4_physics_pareto(data))
        print(json.dumps({"figures": len(outputs) // 2, "scope": "LF4_ONLY_NO_SOURCE_MANIFEST_REWRITE"}, sort_keys=True))
        return
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    outputs: list[Path] = []
    outputs.extend(recovery_ladder(data))
    outputs.extend(event_metrics(data))
    outputs.extend(local_error_gap(data))
    outputs.extend(phase_snapshots())
    outputs.extend(evidence_gates(data))
    manifest = {
        "schema_id": "paper-v23-figure-source-manifest-v1",
        "scope": data["evidence_scope"],
        "inputs": {
            DATA_PATH.relative_to(ROOT).as_posix(): sha256(DATA_PATH),
            PREDICTION_PATH.relative_to(ROOT).as_posix(): sha256(PREDICTION_PATH),
            REFERENCE_PATH.relative_to(ROOT).as_posix(): sha256(REFERENCE_PATH),
        },
        "outputs": {path.relative_to(ROOT).as_posix(): sha256(path) for path in outputs},
        "stress_reference_read": False,
    }
    (HERE / "source-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"figures": len(outputs) // 2, "manifest": "source-manifest.json"}, sort_keys=True))


if __name__ == "__main__":
    main()
