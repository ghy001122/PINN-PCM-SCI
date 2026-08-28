"""Generate the PHK-V2.1 terminal figures from immutable S1 evidence."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
SUMMARY = ROOT / "outputs/runs/20260828T-phk-v21-s1-q-terminal-summary-001/summary.json"
EXPECTED_SUMMARY_SHA256 = "5E6343D3E8DFE63C1C3F2F031FCF04B455E8C53B5BF454F8AFA013D33C33A9C9"
REPORT_RUNS = {
    2: "20260828T-phk-v21-s1-q-02-zero-drive",
    3: "20260828T-phk-v21-s1-q-03-nominal-coarse",
    4: "20260828T-phk-v21-s1-q-04-nominal-medium",
    5: "20260828T-phk-v21-s1-q-05-nominal-fine",
    6: "20260828T-phk-v21-s1-q-06-nominal-extra-fine",
    7: "20260828T-phk-v21-s1-q-07-medium-half-dt",
    8: "20260828T-phk-v21-s1-q-08-fine-exact-replay",
    9: "20260828T-phk-v21-s1-q-09-joule-gain-zero",
    10: "20260828T-phk-v21-s1-q-10-conductivity-ratio-one",
    11: "20260828T-phk-v21-s1-q-11-latent-ratio-zero",
    12: "20260828T-phk-v21-s1-q-12-wide-heater",
    13: "20260828T-phk-v21-s1-q-13-narrow-interface",
    14: "20260828T-phk-v21-s1-q-14-pseudo-crosscheck",
}

NAVY = "#12355B"
BLUE = "#2D6A9F"
TEAL = "#2A9D8F"
GREEN = "#4C956C"
ORANGE = "#E09F3E"
RED = "#C44536"
GRAY = "#A7B0B8"
LIGHT = "#F4F7FA"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def report(intent: int) -> dict:
    return read_json(ROOT / "outputs/runs" / REPORT_RUNS[intent] / "report.json")


def write_csv(name: str, fieldnames: list[str], rows: list[dict]) -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    with (DATA / name).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def save(fig: plt.Figure, stem: str) -> None:
    fig.savefig(HERE / f"{stem}.png", dpi=300, bbox_inches="tight", facecolor="white")
    fig.savefig(HERE / f"{stem}.pdf", bbox_inches="tight", facecolor="white")
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


def figure_01() -> None:
    rows = [
        {"stage": "E1 solver", "status": "PASS", "evidence": "logit Newton selected"},
        {"stage": "E2 object", "status": "PASS", "evidence": "41/41 engineering cases"},
        {"stage": "S0 freeze", "status": "PASS", "evidence": "5 contracts + 128 cases"},
        {"stage": "S1 intents", "status": "PASS", "evidence": "14/14 completed"},
        {"stage": "S1 convergence", "status": "NO-GO", "evidence": "event-time nonmonotonic"},
        {"stage": "PINN/formal", "status": "NOT REACHED", "evidence": "stopped upstream"},
    ]
    write_csv("workflow.csv", ["stage", "status", "evidence"], rows)
    fig, ax = plt.subplots(figsize=(12, 3.2))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 3.2)
    ax.axis("off")
    colors = [GREEN, GREEN, GREEN, GREEN, RED, GRAY]
    for index, (row, color) in enumerate(zip(rows, colors)):
        x = 0.25 + index * 1.95
        box = FancyBboxPatch(
            (x, 1.05), 1.65, 1.15,
            boxstyle="round,pad=0.04,rounding_size=0.08",
            facecolor=color, edgecolor="white", linewidth=1.5,
        )
        ax.add_patch(box)
        ax.text(x + 0.825, 1.82, row["stage"], ha="center", va="center", color="white", weight="bold")
        ax.text(x + 0.825, 1.48, row["status"], ha="center", va="center", color="white", fontsize=8, weight="bold")
        ax.text(x + 0.825, 1.19, row["evidence"], ha="center", va="center", color="white", fontsize=6.8)
        if index < len(rows) - 1:
            ax.add_patch(FancyArrowPatch((x + 1.66, 1.62), (x + 1.93, 1.62), arrowstyle="-|>", mutation_scale=12, color=NAVY))
    ax.text(6, 2.75, "Failure-preserving PHK-V2.1 route", ha="center", color=NAVY, fontsize=14, weight="bold")
    ax.text(6, 0.42, "The upstream numerical gate closed before author-metric replication or PINN training.", ha="center", color=NAVY)
    save(fig, "figure-01-route-outcome")


def figure_02() -> None:
    intents = [
        (1, "Manufactured", "operator pass"), (2, "Zero drive", "no-event pass"),
        (3, "Coarse", "event pass"), (4, "Medium", "event pass"),
        (5, "Fine", "event pass"), (6, "Extra-fine", "event pass"),
        (7, "Half-dt", "event pass"), (8, "Replay", "exact 0"),
        (9, "Joule off", "no-event pass"), (10, "Conductivity", "guard pass"),
        (11, "Latent off", "guard pass"), (12, "Wide heater", "cycle 2 absent"),
        (13, "Narrow interface", "guard pass"), (14, "Solver x-check", "event pass"),
    ]
    rows = [{"intent": i, "label": label, "outcome": outcome, "execution": "COMPLETED"} for i, label, outcome in intents]
    write_csv("qualification_ladder.csv", ["intent", "label", "outcome", "execution"], rows)
    fig, ax = plt.subplots(figsize=(12, 4.6))
    ax.set_xlim(0.3, 14.7)
    ax.set_ylim(-1.2, 1.3)
    ax.axhline(0, color=NAVY, lw=2)
    for i, label, outcome in intents:
        color = ORANGE if i == 12 else (TEAL if "no-event" in outcome else GREEN)
        ax.scatter(i, 0, s=340, color=color, edgecolor="white", linewidth=1.5, zorder=3)
        y = 0.45 if i % 2 else -0.45
        ax.plot([i, i], [0.12 * np.sign(y), y * 0.72], color=GRAY, lw=1)
        ax.text(i, y, f"{i}. {label}\n{outcome}", ha="center", va="center", fontsize=7.2, color=NAVY)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title("All 14 qualification intents completed; the terminal decision came from convergence", weight="bold", color=NAVY)
    ax.text(7.5, -1.02, "No intent, case, or seed was replaced", ha="center", color=RED, weight="bold")
    save(fig, "figure-02-qualification-ladder")


def figure_03() -> None:
    levels = [(3, "coarse"), (4, "medium"), (5, "fine"), (6, "extra-fine")]
    rows: list[dict] = []
    for intent, name in levels:
        cycles = report(intent)["event"]["cycles"]
        for cycle in cycles:
            rows.append(
                {
                    "resolution": name,
                    "cycle": cycle["cycle_index"],
                    "event_time": cycle["event_time"],
                    "roi_peak": cycle["peak_roi_fraction"],
                    "recovery": cycle["recovery_fraction"],
                }
            )
    write_csv("nominal_events.csv", ["resolution", "cycle", "event_time", "roi_peak", "recovery"], rows)
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.0))
    x = np.arange(4)
    for cycle, color in ((1, BLUE), (2, ORANGE)):
        subset = [row for row in rows if row["cycle"] == cycle]
        axes[0].plot(x, [r["event_time"] for r in subset], "o-", color=color, label=f"cycle {cycle}", lw=2)
        axes[1].plot(x, [r["roi_peak"] for r in subset], "o-", color=color, label=f"cycle {cycle}", lw=2)
    for ax in axes:
        ax.set_xticks(x, [name for _, name in levels], rotation=20)
        ax.grid(axis="y", alpha=0.25)
        ax.legend(frameon=False)
    axes[0].set_ylabel("Event time")
    axes[0].set_title("Finite two-cycle event times")
    axes[1].set_ylabel("Peak ROI phase fraction")
    axes[1].set_title("Localized event amplitude")
    fig.suptitle("Every nominal resolution looks event-valid", fontsize=13, weight="bold", color=NAVY)
    fig.tight_layout()
    save(fig, "figure-03-nominal-events")


def figure_04() -> None:
    controls = [
        (4, "nominal"), (2, "zero drive"), (9, "Joule off"),
        (10, "conductivity ratio 1"), (11, "latent off"),
        (12, "wide heater"), (13, "narrow interface"),
    ]
    rows: list[dict] = []
    for intent, name in controls:
        for cycle in report(intent)["event"]["cycles"]:
            rows.append({"control": name, "cycle": cycle["cycle_index"], "roi_peak": cycle["peak_roi_fraction"], "event_time": cycle["event_time"]})
    write_csv("control_events.csv", ["control", "cycle", "roi_peak", "event_time"], rows)
    fig, ax = plt.subplots(figsize=(10.8, 4.4))
    names = [name for _, name in controls]
    x = np.arange(len(names))
    width = 0.36
    for cycle, offset, color in ((1, -width / 2, BLUE), (2, width / 2, ORANGE)):
        vals = [next(r["roi_peak"] for r in rows if r["control"] == name and r["cycle"] == cycle) for name in names]
        ax.bar(x + offset, vals, width, label=f"cycle {cycle}", color=color)
    ax.axhline(0.02, color=RED, ls="--", lw=1.2, label="event peak threshold")
    ax.set_xticks(x, names, rotation=22, ha="right")
    ax.set_ylabel("Peak ROI phase fraction")
    ax.set_title("Controls delimit causality and geometry sensitivity", weight="bold", color=NAVY)
    ax.legend(frameon=False, ncol=3)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    save(fig, "figure-04-controls")


def figure_05(summary: dict) -> None:
    mf = np.asarray(summary["comparisons"]["medium_fine"]["component_deltas"], dtype=float)
    fe = np.asarray(summary["comparisons"]["fine_extra_fine"]["component_deltas"], dtype=float)
    names = ["phase", "temperature", "current", "event time", "phase region", "recovery"]
    declared = np.asarray([1e-8, 1e-8, 1e-8, 1e-6, 1e-6, 1e-6])
    denominator = np.maximum(mf, declared)
    ratio = fe / denominator
    rows = [
        {"component": name, "medium_fine": a, "fine_extra_fine": b, "monotonic_ratio": c, "pass": bool(c <= 1.0)}
        for name, a, b, c in zip(names, mf, fe, ratio)
    ]
    write_csv("convergence_components.csv", ["component", "medium_fine", "fine_extra_fine", "monotonic_ratio", "pass"], rows)
    fig, ax = plt.subplots(figsize=(9.8, 4.5))
    colors = [GREEN if value <= 1 else RED for value in ratio]
    bars = ax.bar(np.arange(6), ratio, color=colors, width=0.68)
    ax.axhline(1.0, color=NAVY, ls="--", lw=1.5, label="monotonic limit")
    ax.set_xticks(np.arange(6), names, rotation=18)
    ax.set_ylabel("fine→extra-fine / max(medium→fine, tolerance)")
    ax.set_title("One component closes the oracle route", weight="bold", color=NAVY)
    ax.set_ylim(0, max(1.55, float(np.max(ratio)) * 1.2))
    for bar, value in zip(bars, ratio):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.04, f"{value:.2f}", ha="center", fontsize=8, weight="bold")
    ax.legend(frameon=False)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    save(fig, "figure-05-convergence-gate")


def figure_06(summary: dict) -> None:
    rows = [
        {"layer": "Engineering solver/object", "status": "SUPPORTED", "count": 41},
        {"layer": "Qualification intents", "status": "COMPLETED", "count": 14},
        {"layer": "Qualified oracle/floor", "status": "NO-GO", "count": 0},
        {"layer": "Sharp/PF metric replication", "status": "NOT REACHED", "count": 0},
        {"layer": "PINN/PHA/KC", "status": "NOT REACHED", "count": 0},
        {"layer": "Formal OOD", "status": "NOT REACHED", "count": 0},
    ]
    write_csv("claim_boundary.csv", ["layer", "status", "count"], rows)
    fig, ax = plt.subplots(figsize=(10.5, 4.8))
    ax.set_xlim(0, 10.5)
    ax.set_ylim(0, 6.6)
    ax.axis("off")
    colors = [GREEN, GREEN, RED, GRAY, GRAY, GRAY]
    for idx, (row, color) in enumerate(zip(rows, colors)):
        y = 5.65 - idx * 0.86
        ax.add_patch(FancyBboxPatch((0.35, y - 0.3), 5.7, 0.58, boxstyle="round,pad=0.03", facecolor=LIGHT, edgecolor=color, linewidth=2))
        ax.text(0.62, y, row["layer"], va="center", color=NAVY, weight="bold")
        ax.text(5.72, y, row["status"], va="center", ha="right", color=color, weight="bold")
    cpu = summary["gross_compute"]["process_cpu_core_hours"]
    ax.add_patch(FancyBboxPatch((6.55, 3.45), 3.5, 2.2, boxstyle="round,pad=0.08", facecolor=NAVY, edgecolor=NAVY))
    ax.text(8.3, 5.15, "Recorded S1 compute", ha="center", color="white", weight="bold", fontsize=12)
    ax.text(8.3, 4.55, f"{cpu:.6f}\nCPU core-hours", ha="center", va="center", color="white", fontsize=18, weight="bold")
    ax.text(8.3, 3.82, "0 failed intents\n0 GPU hours", ha="center", color="white")
    ax.add_patch(FancyBboxPatch((6.55, 0.75), 3.5, 1.85, boxstyle="round,pad=0.08", facecolor="#FFF3E0", edgecolor=ORANGE, linewidth=2))
    ax.text(8.3, 2.22, "Claim ceiling", ha="center", color=NAVY, weight="bold")
    ax.text(8.3, 1.55, "Synthetic numerical\nqualification No-Go", ha="center", va="center", color=RED, fontsize=13, weight="bold")
    ax.text(8.3, 0.98, "No PINN method evidence", ha="center", color=NAVY)
    ax.set_title("Evidence accumulated only up to the failed oracle gate", weight="bold", color=NAVY, pad=8)
    save(fig, "figure-06-claim-boundary")


def write_manifest(summary: dict) -> None:
    inputs = [SUMMARY, ROOT / "configs/phk_v21/oracle_and_floor_contract.json", ROOT / "configs/phk_v21/object_numerical_contract.json", ROOT / "docs/experiment/2026-08-28-phk-v21-s1-terminal-closeout.md"]
    inputs.extend(ROOT / "outputs/runs" / run / "report.json" for run in REPORT_RUNS.values())
    outputs = sorted(DATA.glob("*.csv")) + sorted(HERE.glob("figure-*.png")) + sorted(HERE.glob("figure-*.pdf"))
    payload = {
        "schema_id": "phk-v21-figure-source-manifest-v1",
        "terminal_outcome": summary["adjudication"]["outcome"],
        "generator_sha256": sha(Path(__file__)),
        "inputs": [{"path": str(p.relative_to(ROOT)).replace("\\", "/"), "sha256": sha(p), "bytes": p.stat().st_size} for p in inputs],
        "outputs": [{"path": str(p.relative_to(ROOT)).replace("\\", "/"), "sha256": sha(p), "bytes": p.stat().st_size} for p in outputs],
        "solver_or_training_executed": False,
    }
    (HERE / "source-manifest.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    if sha(SUMMARY) != EXPECTED_SUMMARY_SHA256:
        raise RuntimeError("terminal summary identity drift")
    summary = read_json(SUMMARY)
    if summary["adjudication"]["outcome"] != "PHK_V21_ORACLE_NO_GO_STOP_BEFORE_PINN":
        raise RuntimeError("terminal outcome drift")
    HERE.mkdir(parents=True, exist_ok=True)
    style()
    figure_01()
    figure_02()
    figure_03()
    figure_04()
    figure_05(summary)
    figure_06(summary)
    write_manifest(summary)
    print("PHK_V21_FIGURES_GENERATED")


if __name__ == "__main__":
    main()
