from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap
    from matplotlib.patches import FancyBboxPatch
except ModuleNotFoundError:  # LF5-only has a Pillow fallback in the bundled runtime.
    matplotlib = None
    plt = None
    ListedColormap = None
    FancyBboxPatch = None


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DATA_PATH = HERE / "data" / "lf3_terminal_metrics.json"
LF4_DATA_PATH = HERE / "data" / "lf4_terminal_metrics.json"
LF5_DATA_PATH = HERE / "data" / "lf5_terminal_metrics.json"
LF6_DATA_PATH = HERE / "data" / "lf6_terminal_metrics.json"
LF7_DATA_PATH = HERE / "data" / "lf7_terminal_metrics.json"
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
    if plt is None:
        raise RuntimeError("matplotlib is required unless --lf5-only is used")
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


def _pil_canvas(title: str):
    from PIL import Image, ImageDraw, ImageFont
    image=Image.new("RGB",(1800,760),"white"); draw=ImageDraw.Draw(image)
    try: font=ImageFont.truetype("C:/Windows/Fonts/arial.ttf",30); bold=ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf",36); small=ImageFont.truetype("C:/Windows/Fonts/arial.ttf",24)
    except OSError: font=bold=small=ImageFont.load_default()
    draw.text((60,35),title,fill=NAVY,font=bold); return image,draw,font,bold,small


def _save_pil(image, stem: str) -> list[Path]:
    paths=[HERE/f"{stem}.png",HERE/f"{stem}.pdf"]; image.save(paths[0],dpi=(240,240)); image.save(paths[1],"PDF",resolution=240.0); return paths


def lf5_temporal_edge_geometry(data: dict) -> list[Path]:
    image,draw,font,bold,small=_pil_canvas("LF5 CPU-T: aggregate timing improvement does not imply local zero-level alignment")
    names=[name.replace("_"," ") for name in data["pool_order"]]; m=data["DEV_M_mean_abs_residual"]; c=data["DEV_C_mean_abs_residual"]
    draw.text((80,120),"Valid edge pools",fill=NAVY,font=font); draw.text((760,120),"Weighted mean absolute zero-level residual (log scale)",fill=NAVY,font=font)
    for i,(name,count) in enumerate(zip(names,data["pool_counts"])):
        y=190+i*115; draw.text((80,y+20),name,fill=NAVY,font=small); draw.rectangle((300,y,300+count*5,y+55),fill=BLUE if "ONSET" in name else TEAL); draw.text((650,y+10),str(count),fill=NAVY,font=small)
        scale=230*np.log10(1+max(m[i],c[i])); draw.text((760,y+16),name,fill=NAVY,font=small); draw.rectangle((1030,y,1030+230*np.log10(1+m[i]),y+24),fill=TEAL); draw.rectangle((1030,y+31,1030+scale,y+55),fill=ORANGE); draw.text((1500,y),f"M {m[i]:.3f}",fill=TEAL,font=small); draw.text((1500,y+30),f"C {c[i]:.3f}",fill=ORANGE,font=small)
    return _save_pil(image,"20260905T150045Z-lf5-temporal-edge-geometry")


def lf5_timing_calibration(data: dict) -> list[Path]:
    image,draw,font,bold,small=_pil_canvas("LF5 exploratory endpoint: support recovered, cycle-1 timing still misses")
    x0,y0,x1,y1=180,150,1660,650; draw.line((x0,y1,x1,y1),fill=NAVY,width=4); draw.line((x0,y0,x0,y1),fill=NAVY,width=4)
    draw.text((600,690),"Worst-cycle event-time error (right is worse)",fill=NAVY,font=small); draw.text((20,370),"phase MSE",fill=NAVY,font=small)
    gate_x=x0+(0.005/0.012)*(x1-x0); draw.line((gate_x,y0,gate_x,y1),fill=RED,width=3); draw.text((gate_x+8,y0),"timing gate",fill=RED,font=small)
    for name,color in (("DEV_M",TEAL),("DEV_C",ORANGE),("DEV_T",BLUE)):
        item=data["timing"][name]; x=x0+max(item["cycle_1_error"],item["cycle_2_error"])/0.012*(x1-x0); y=y1-(np.log10(item["phase_weighted_mse"])-np.log10(0.0008))/(np.log10(0.05)-np.log10(0.0008))*(y1-y0); y=min(y1-18,max(y0+18,y)); draw.ellipse((x-15,y-15,x+15,y+15),fill=color); label_x=x-260 if name=="DEV_T" else x+22; label_y=y-45 if name=="DEV_T" else y-15; draw.text((label_x,label_y),f"{name.replace('_','-')}: {item['phase_weighted_mse']:.4g}",fill=color,font=small)
    draw.text((170,100),"DEV-T values are directional only: its temporal batch identity drifted from the CPU-frozen stream.",fill=GRAY,font=font); return _save_pil(image,"20260905T150045Z-lf5-timing-calibration")


def lf5_physics_pareto(data: dict) -> list[Path]:
    image,draw,font,bold,small=_pil_canvas("LF5 outcome: DEV-T identity invalid; P0 not run")
    boxes=[(80,"CPU-T","FAIL / OVERRIDDEN",ORANGE,"valid geometry; premise refuted"),(640,"DEV-T","400 / ID INVALID",RED,"temporal stream SHA drift"),(1200,"P0","NOT RUN",GRAY,"no valid carrier checkpoint")]
    for x,title,status,color,detail in boxes:
        draw.rounded_rectangle((x,190,x+460,430),radius=25,outline=color,width=5); draw.text((x+30,225),title,fill=NAVY,font=bold); draw.text((x+30,290),status,fill=color,font=font); draw.text((x+30,355),detail,fill=GRAY,font=small)
    draw.line((545,310,625,310),fill=GRAY,width=5); draw.polygon([(625,310),(600,295),(600,325)],fill=GRAY); draw.line((1105,310,1185,310),fill=GRAY,width=5); draw.polygon([(1185,310),(1160,295),(1160,325)],fill=GRAY)
    draw.text((100,520),"Directional telemetry: recall 0.918/0.917, phase MSE 7.84e-4, but C1 timing error 0.0094.",fill=NAVY,font=font); draw.text((100,580),"Identity failure overrides metrics: no checkpoint, P0, PINN Pareto, or candidate claim.",fill=RED,font=font); return _save_pil(image,"20260905T150045Z-lf5-physics-pareto")


def lf6_event_frontier(data: dict) -> list[Path]:
    source = data["event_frontier"]
    image, draw, font, bold, small = _pil_canvas("LF6 event-frontier geometry: teacher-side critical-rank exposure")
    cycles = [source["cycles"]["cycle_1"], source["cycles"]["cycle_2"]]
    draw.text((80, 120), "Saved endpoints bracket the 2% active-count threshold", fill=NAVY, font=font)
    draw.line((90, 500, 790, 500), fill=NAVY, width=3)
    threshold_y = 500 - int(source["q"] / 0.026 * 300)
    draw.line((90, threshold_y, 790, threshold_y), fill=RED, width=3)
    draw.text((95, threshold_y - 38), "2% threshold", fill=RED, font=small)
    for idx, cycle in enumerate(cycles):
        base_x = 250 + idx * 330
        for offset, key, color, label in ((-65, "pre_fraction", GRAY, "pre"), (20, "post_fraction", TEAL, "post")):
            value = cycle[key]
            height = int(value / 0.026 * 300)
            draw.rectangle((base_x + offset, 500 - height, base_x + offset + 60, 500), fill=color)
            draw.text((base_x + offset - 12, 515), label, fill=NAVY, font=small)
            draw.text((base_x + offset - 15, 465 - height), f"{100 * value:.2f}%", fill=color, font=small)
        draw.text((base_x - 55, 570), f"Cycle {idx + 1}", fill=NAVY, font=font)
    draw.text((930, 120), "Frozen order-statistic band", fill=NAVY, font=font)
    draw.text((940, 175), f"ROI cells: {source['roi_cell_count']}   critical rank: {source['critical_rank_one_based']}", fill=GRAY, font=small)
    for idx, cycle in enumerate(cycles):
        y = 300 + idx * 190
        x0 = 1020 + (cycle["rank_start"] - 16) * 65
        x1 = 1020 + (cycle["rank_stop"] - 16) * 65
        xc = 1020 + (source["critical_rank_one_based"] - 16) * 65
        draw.line((1020, y, 1535, y), fill=GRAY, width=3)
        draw.line((x0, y, x1, y), fill=BLUE, width=20)
        draw.ellipse((xc - 13, y - 13, xc + 13, y + 13), fill=RED)
        draw.text((925, y - 18), f"C{idx + 1}", fill=NAVY, font=font)
        draw.text((x0, y + 28), f"ranks {cycle['rank_start']}-{cycle['rank_stop']} ({cycle['pool_size']} cells)", fill=BLUE, font=small)
    draw.text((930, 650), "Red dot: downstream count threshold; blue band: supervised frontier", fill=GRAY, font=small)
    return _save_pil(image, "20260906T065434Z-lf6-event-frontier")


def lf6_matched_development(data: dict) -> list[Path]:
    arms = data["development"]
    image, draw, font, bold, small = _pil_canvas("LF6 matched development: safety endpoint, no rank-specific increment")
    order = ["DEV_U", "DEV_R"]
    labels = ["Uniform endpoint control", "Event-frontier rank band"]
    colors = [GRAY, BLUE]
    draw.text((90, 120), "Minimum cycle recall", fill=NAVY, font=font)
    draw.line((90, 525, 790, 525), fill=NAVY, width=3)
    gate_y = 525 - int((0.90 - 0.86) / 0.08 * 330)
    draw.line((90, gate_y, 790, gate_y), fill=RED, width=3)
    draw.text((95, gate_y - 35), "safety gate 0.90", fill=RED, font=small)
    for idx, name in enumerate(order):
        value = min(arms[name]["recall"])
        height = int((value - 0.86) / 0.08 * 330)
        x = 235 + idx * 350
        draw.rectangle((x, 525 - height, x + 130, 525), fill=colors[idx])
        draw.text((x + 12, 485 - height), f"{value:.3f}", fill=colors[idx], font=font)
        draw.text((x - 45, 550), labels[idx], fill=NAVY, font=small)
    draw.text((930, 120), "Cycle-wise event-time error", fill=NAVY, font=font)
    draw.line((950, 525, 1660, 525), fill=NAVY, width=3)
    timing_gate_y = 525 - int(0.005 / 0.012 * 330)
    draw.line((950, timing_gate_y, 1660, timing_gate_y), fill=RED, width=3)
    for idx, name in enumerate(order):
        x = 1085 + idx * 350
        for offset, value, color in ((0, arms[name]["timing"][0], ORANGE), (70, arms[name]["timing"][1], TEAL)):
            height = int(value / 0.012 * 330)
            draw.rectangle((x + offset, 525 - height, x + offset + 55, 525), fill=color)
        draw.text((x - 45, 550), labels[idx], fill=NAVY, font=small)
    draw.rectangle((950, timing_gate_y - 38, 1190, timing_gate_y - 4), fill="white")
    draw.text((955, timing_gate_y - 35), "strict gate 0.005", fill=RED, font=small)
    draw.text((990, 650), "orange: cycle 1    teal: cycle 2", fill=GRAY, font=small)
    draw.text((95, 665), "DEV-R is safety-valid but misses strict cycle-1 timing; neither arm is a strict carrier.", fill=NAVY, font=small)
    return _save_pil(image, "20260906T065434Z-lf6-matched-development")


def lf6_physics_pareto(data: dict) -> list[Path]:
    physics = data["physics"]
    rows = physics["timeline"]
    image, draw, font, bold, small = _pil_canvas("LF6 P0: residual reduction and event preservation diverge")
    x0, y0, x1, y1 = 100, 175, 1120, 610
    draw.line((x0, y1, x1, y1), fill=NAVY, width=4)
    draw.line((x0, y0, x0, y1), fill=NAVY, width=4)
    draw.text((380, 650), "P0 physics update", fill=NAVY, font=small)
    draw.text((110, 125), "Minimum cycle recall", fill=NAVY, font=font)
    points = []
    for row in rows:
        x = x0 + int(row["step"] / 1200 * (x1 - x0))
        y = y1 - int(row["recall_min"] * (y1 - y0))
        points.append((x, y))
    draw.line(points, fill=TEAL, width=7)
    for x, y in points:
        draw.ellipse((x - 10, y - 10, x + 10, y + 10), fill=TEAL)
    gate_y = y1 - int(0.90 * (y1 - y0))
    draw.line((x0, gate_y, x1, gate_y), fill=RED, width=3)
    unfreeze_x = x0 + int(550 / 1200 * (x1 - x0))
    draw.line((unfreeze_x, y0, unfreeze_x, y1), fill=GRAY, width=3)
    draw.text((unfreeze_x + 8, y0 + 12), "phase unfreezes", fill=GRAY, font=small)
    for tick in (0, 550, 800, 1200):
        x = x0 + int(tick / 1200 * (x1 - x0))
        draw.text((x - 25, y1 + 12), str(tick), fill=NAVY, font=small)
    draw.rounded_rectangle((1200, 150, 1710, 575), radius=25, outline=RED, width=5)
    draw.text((1240, 185), "Fixed blind physics", fill=NAVY, font=font)
    draw.text((1240, 240), f"4.9279 -> 0.06315", fill=TEAL, font=bold)
    draw.text((1240, 305), f"ratio = {physics['fixed_blind_ratio']:.4f} (PASS)", fill=TEAL, font=font)
    draw.text((1240, 385), "Carrier preservation", fill=NAVY, font=font)
    draw.text((1240, 440), "FAIL", fill=RED, font=bold)
    draw.text((1240, 505), "final recall = 0 / 0", fill=RED, font=font)
    draw.text((120, 700), "V/T drift while phase is frozen; event recall collapses immediately after joint unfreeze.", fill=NAVY, font=small)
    return _save_pil(image, "20260906T065434Z-lf6-physics-pareto")


def lf7_competence_filtered_refinement(data: dict) -> list[Path]:
    """Render only identity-valid LF7 evidence; P0-F has no endpoint."""
    baseline = data["baseline"]
    small = data["arms"]["P0_S"]
    filtered = data["arms"]["P0_F"]
    if plt is None:
        image, draw, font, bold, small_font = _pil_canvas(
            "LF7: small-step forgetting; filtered arm has no valid endpoint"
        )
        # Panel A: normalized blind objective.
        draw.text((70, 115), "A  Blind physics / DEV-R", fill=NAVY, font=font)
        x0, y0, width, height = 80, 190, 430, 360
        draw.line((x0, y0 + height, x0 + width, y0 + height), fill=NAVY, width=3)
        gate_y = y0 + height - int(0.5 * height)
        draw.line((x0, gate_y, x0 + width, gate_y), fill=RED, width=3)
        draw.text((x0 + 5, gate_y - 32), "gate 0.50", fill=RED, font=small_font)
        for idx, (label, value, color) in enumerate(
            (("DEV-R", 1.0, GRAY), ("P0-S", small["fixed_blind_ratio"], BLUE))
        ):
            bx = x0 + 80 + idx * 180
            bh = int(value * height)
            draw.rectangle((bx, y0 + height - bh, bx + 90, y0 + height), fill=color)
            draw.text((bx + 5, y0 + height + 14), label, fill=NAVY, font=small_font)
            draw.text((bx + 5, y0 + height - bh - 34), f"{value:.3f}", fill=color, font=small_font)

        # Panel B: event recall/recovery.
        draw.text((620, 115), "B  Event functionals", fill=NAVY, font=font)
        bx0, by0, bwidth, bheight = 625, 190, 500, 360
        draw.line((bx0, by0 + bheight, bx0 + bwidth, by0 + bheight), fill=NAVY, width=3)
        for group, (label, recalls, recovery) in enumerate(
            (("DEV-R", baseline["recall"], baseline["recovery"]), ("P0-S", small["recall"], small["recovery"]))
        ):
            gx = bx0 + 60 + group * 250
            values = [recalls[0], recalls[1], recovery[0], recovery[1]]
            for j, (value, color) in enumerate(zip(values, (TEAL, BLUE, GOLD, ORANGE))):
                bh = int(value * bheight)
                xx = gx + j * 42
                draw.rectangle((xx, by0 + bheight - bh, xx + 30, by0 + bheight), fill=color)
            draw.text((gx + 30, by0 + bheight + 14), label, fill=NAVY, font=small_font)
        draw.text((640, 605), "C1/C2 recall; C1/C2 recovery", fill=GRAY, font=small_font)

        # Panel C: partial first-block screen.
        draw.text((1210, 115), "C  P0-F first block", fill=NAVY, font=font)
        attempts = filtered["attempts"]
        for idx, row in enumerate(attempts):
            y = 190 + idx * 72
            color = TEAL if row["decision"] == "ACCEPT" else RED
            draw.ellipse((1230, y, 1260, y + 30), fill=color)
            draw.text((1280, y - 2), f"eta0/{2 ** idx}: {row['decision']}", fill=color, font=small_font)
            draw.text((1530, y - 2), f"J/J0={row['fixed_blind_objective']/baseline['fixed_blind_objective']:.3f}", fill=NAVY, font=small_font)
        draw.text((1225, 585), "4 rejects; eta0/16 accepted", fill=NAVY, font=small_font)
        draw.text((1225, 625), "then Adam-state identity drift", fill=RED, font=small_font)
        draw.text((1225, 665), "NO VALID P0-F ENDPOINT", fill=RED, font=bold)
        return _save_pil(image, "20260907T144634Z-lf7-competence-filtered-refinement")

    fig, axes = plt.subplots(1, 3, figsize=(12.8, 3.9))

    # Panel A: the valid fixed-small-step control did not reach the physics gate.
    ratios = [1.0, small["fixed_blind_ratio"]]
    bars = axes[0].bar([0, 1], ratios, color=[GRAY, BLUE], width=0.62)
    axes[0].axhline(data["gates"]["physics_ratio_max"], color=RED, linestyle="--", linewidth=1.3, label="required ratio <= 0.50")
    axes[0].set_xticks([0, 1], ["DEV-R start", "P0-S\n1200 updates"])
    axes[0].set_ylabel("Fixed blind physics / DEV-R")
    axes[0].set_ylim(0, 1.12)
    axes[0].set_title("A  Residual reduction")
    axes[0].legend(loc="upper right", fontsize=7.5)
    for bar, value in zip(bars, ratios):
        axes[0].text(bar.get_x() + bar.get_width() / 2, value + 0.025, f"{value:.3f}", ha="center", color=NAVY, fontweight="bold")

    # Panel B: endpoint competence is assessed independently of residual decrease.
    x = np.arange(2)
    width = 0.18
    series = [
        ("C1 recall", [baseline["recall"][0], small["recall"][0]], TEAL),
        ("C2 recall", [baseline["recall"][1], small["recall"][1]], BLUE),
        ("C1 recovery", [baseline["recovery"][0], small["recovery"][0]], GOLD),
        ("C2 recovery", [baseline["recovery"][1], small["recovery"][1]], ORANGE),
    ]
    for idx, (label, values, color) in enumerate(series):
        axes[1].bar(x + (idx - 1.5) * width, values, width=width, color=color, label=label)
    axes[1].axhline(data["gates"]["recall_min"], color=RED, linestyle="--", linewidth=1.1)
    axes[1].set_xticks(x, ["DEV-R", "P0-S"])
    axes[1].set_ylim(0, 1.08)
    axes[1].set_ylabel("Event functional")
    axes[1].set_title("B  Carrier preservation")
    axes[1].legend(loc="upper right", fontsize=6.8, ncol=2)

    # Panel C: show partial filter behavior, never an endpoint or mechanism result.
    attempts = filtered["attempts"]
    rates = np.asarray([row["learning_rate"] for row in attempts], dtype=float)
    physics = np.asarray([row["fixed_blind_objective"] for row in attempts], dtype=float) / baseline["fixed_blind_objective"]
    colors = [RED if row["decision"] == "REJECT" else TEAL for row in attempts]
    axes[2].scatter(np.arange(1, len(attempts) + 1), physics, c=colors, s=70, zorder=3)
    axes[2].plot(np.arange(1, len(attempts) + 1), physics, color=GRAY, linewidth=1.0, zorder=2)
    axes[2].set_xticks(np.arange(1, len(attempts) + 1), [f"eta0/{2 ** (i - 1)}" for i in range(1, len(attempts) + 1)], rotation=25)
    axes[2].set_ylabel("Proposed block physics / DEV-R")
    axes[2].set_ylim(min(0.84, float(physics.min()) - 0.03), 1.02)
    axes[2].set_title("C  P0-F first block screen")
    axes[2].text(0.03, 0.04, "4 rejected; eta0/16 accepted\nthen state-identity drift -> no endpoint", transform=axes[2].transAxes, color=RED, fontsize=7.7, fontweight="bold")
    for idx, row in enumerate(attempts):
        marker = "R" if row["decision"] == "REJECT" else "A"
        axes[2].text(idx + 1, physics[idx] + 0.012, marker, ha="center", color=colors[idx], fontweight="bold", fontsize=8)

    fig.suptitle(
        "LF7: small-step physics still forgets the event; filtered arm is identity-invalid after one accepted block",
        color=NAVY,
        fontweight="bold",
    )
    fig.text(
        0.5,
        0.005,
        "Single-seed nominal pilot. P0-F points are block proposals, not a valid endpoint; no filter-mechanism or candidate claim.",
        ha="center",
        color=GRAY,
        fontsize=8,
    )
    fig.tight_layout(rect=(0, 0.045, 1, 0.92))
    return save(fig, "20260907T144634Z-lf7-competence-filtered-refinement")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Generate paper_v23 evidence figures")
    parser.add_argument("--lf4-only", action="store_true", help="Generate LF4 figures 6–8 without rewriting the LF3 source manifest")
    parser.add_argument("--lf5-only", action="store_true", help="Generate timestamped LF5 CPU-T terminal figures")
    parser.add_argument("--lf6-only", action="store_true", help="Generate timestamped LF6 terminal figures")
    parser.add_argument("--lf7-only", action="store_true", help="Generate the LF7 terminal figure only after terminal evidence is bound")
    args = parser.parse_args(argv)
    if args.lf5_only:
        data=json.loads(LF5_DATA_PATH.read_text(encoding="utf-8")); outputs=[]; outputs.extend(lf5_temporal_edge_geometry(data)); outputs.extend(lf5_timing_calibration(data)); outputs.extend(lf5_physics_pareto(data)); print(json.dumps({"figures":len(outputs)//2,"scope":"LF5_CPU_T_PLUS_IDENTITY_INVALID_EXPLORATORY_DEV_T"},sort_keys=True)); return
    if args.lf6_only:
        data = json.loads(LF6_DATA_PATH.read_text(encoding="utf-8"))
        outputs: list[Path] = []
        outputs.extend(lf6_event_frontier(data))
        outputs.extend(lf6_matched_development(data))
        outputs.extend(lf6_physics_pareto(data))
        print(json.dumps({"figures": len(outputs) // 2, "scope": "LF6_MATCHED_DEVELOPMENT_AND_EXECUTED_P0"}, sort_keys=True))
        return
    if args.lf7_only:
        data = json.loads(LF7_DATA_PATH.read_text(encoding="utf-8"))
        if data.get("campaign_state") != "COMPLETE" or data.get("terminal_outcome") is None:
            print(json.dumps({"figures": 0, "scope": "LF7_ACTIVE_RESULTS_PENDING", "status": "SKIPPED_NO_TERMINAL_DATA"}, sort_keys=True))
            return
        if plt is not None:
            setup()
        outputs = lf7_competence_filtered_refinement(data)
        print(json.dumps({"figures": len(outputs) // 2, "scope": "LF7_VALID_P0_S_PLUS_PARTIAL_IDENTITY_INVALID_P0_F"}, sort_keys=True))
        return
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
