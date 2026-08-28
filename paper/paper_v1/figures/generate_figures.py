"""Rebuild the bounded GOAL-PAPER-ONE-SHOT-V1 scientific figure package.

The script reads only frozen/terminal evidence already present in the repository.
It does not run the SYN_EDT solver, infer missing results, or modify authority,
status, ledger, manuscript, or core-code files.  Every plotted numeric trace is
exported to ``paper/paper_v1/figures/data`` and every evidence carrier is hashed in
``source-manifest.json``.
"""

from __future__ import annotations

import csv
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import platform
import sys
from typing import Any, Iterable, Mapping, Sequence

import h5py
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle
import numpy as np


ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
DATA = OUT / "data"

S0 = ROOT / "configs/goal_paper_one_shot_v1/s0_contract.json"
S2 = ROOT / "configs/goal_paper_one_shot_v1/s2_numerical_contract.json"
S1 = ROOT / "docs/references/2026-08-26-goal-paper-one-shot-v1-s1-source-legal-novelty-review.md"
CLOSEOUT = ROOT / "docs/experiment/2026-08-26-goal-paper-one-shot-v1-s2-terminal-closeout.md"
FREEZE = ROOT / "docs/experiment/manifests/20260826T113537Z-goal-paper-one-shot-v1-s2-freeze-002.json"
Q_MANIFEST = ROOT / "outputs/runs/20260826T113537Z-goal-paper-one-shot-v1-s2-freeze-002/case-manifest-q-only.json"
Q0_MANIFEST = ROOT / "docs/experiment/manifests/20260826T113638Z-goal-paper-one-shot-v1-s2-intent-01-q0.json"
Q0_H5 = ROOT / "outputs/runs/20260826T113638Z-goal-paper-one-shot-v1-s2-intent-01-q0/case-q0-intent-01-coarse-coarse-full.h5"
Q0_REPORT = ROOT / "outputs/runs/20260826T113638Z-goal-paper-one-shot-v1-s2-intent-01-q0/report.json"
QN_MANIFEST = ROOT / "docs/experiment/manifests/20260826T113752Z-goal-paper-one-shot-v1-s2-intent-02-qn-coarse-fine.json"
CORE = ROOT / "pinn_pcm_sci/syn_edt_2d.py"
CORE_TEST = ROOT / "tests/test_syn_edt_2d.py"

EXPECTED_SHA256 = {
    S0: "947E737A255D27A7BB2553286809ADB98219FD4E48B932B170CB06608A2E3A75",
    S2: "D059AA2261CC227C3B16B7965A75C461AD64110C2A20C3700B62E54FDE25E8E6",
    FREEZE: "74B5CD92A5271FD481A134DD52A80DD22FC65DC6784F761C5B8B74B880AB2F35",
    Q_MANIFEST: "EF093A5C2F2E798FF05E768C3D0837CF08C3E10FD6AE79B432F26585F0FCD09C",
    Q0_MANIFEST: "6451DFC6C1E331A0AF86997FDCC74083CD4C8C781C96C2C2A156EB149504205E",
    Q0_H5: "01F5DCF28E25A75E74C5EDBE612456A542ECA36EFFCB8CAFEC196AE4994F7A01",
    Q0_REPORT: "0964E3B55431AA49CDE158FFF7F98F3478288865A6DE670CC88ABD9B7BF3D1A8",
    QN_MANIFEST: "A1806D03A1D5F8687FCE252F66BA2CCE921DA78902EADA149B5A84C42CE0ECB8",
}

NAVY = "#17324D"
BLUE = "#2C7FB8"
TEAL = "#2A9D8F"
RED = "#C84C4C"
AMBER = "#E6A33D"
PURPLE = "#7656A8"
GRAY = "#D9E0E6"
DARK_GRAY = "#596773"
LIGHT = "#F5F7F9"
WHITE = "#FFFFFF"
BLACK = "#17212B"

FIGURES = [
    "figure-01-route-gates",
    "figure-02-source-matrix",
    "figure-03-s2-ladder",
    "figure-04-q0-guard",
    "figure-05-newton-diagnostic",
    "figure-06-claim-boundary",
]
CAPTIONS = OUT / "captions.md"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON root must be an object: {relative(path)}")
    return value


def assert_contains(text: str, markers: Sequence[str], role: str) -> None:
    missing = [marker for marker in markers if marker not in text]
    if missing:
        raise RuntimeError(f"{role} is missing frozen markers: {missing}")


def validate_sources() -> dict[str, Any]:
    for path, expected in EXPECTED_SHA256.items():
        actual = sha256(path)
        if actual != expected:
            raise RuntimeError(
                f"evidence hash drift for {relative(path)}: {actual} != {expected}"
            )

    s0 = read_json(S0)
    s2 = read_json(S2)
    freeze = read_json(FREEZE)
    q_manifest = read_json(Q_MANIFEST)
    q0_manifest = read_json(Q0_MANIFEST)
    q0_report = read_json(Q0_REPORT)
    qn_manifest = read_json(QN_MANIFEST)
    s1_text = S1.read_text(encoding="utf-8")
    closeout_text = CLOSEOUT.read_text(encoding="utf-8")

    if s0["route_order"][-1] != "SYN_EDT_2D_V1":
        raise RuntimeError("S0 fallback route identity drifted")
    if len(s2["qualification_ladder"]) != 13:
        raise RuntimeError("S2 qualification ladder is not the frozen 13-intent ladder")
    if freeze.get("supersedes") != "20260826T110938Z-goal-paper-one-shot-v1-s2-freeze-001":
        raise RuntimeError("effective freeze does not supersede freeze-001")
    if set(q_manifest["cases"]) != {"Q0", "QL", "QN", "QH"}:
        raise RuntimeError("Q-only case manifest identity drifted")
    if not q0_report["guard_report"]["passed"]:
        raise RuntimeError("Q0 guard report is no longer PASS")
    if q0_report["event_report"]["applicable"]:
        raise RuntimeError("Q0 event report must remain non-applicable")
    if qn_manifest.get("execution_status") != "FAILED":
        raise RuntimeError("QN intent-02 is not the frozen execution failure")
    failure_message = qn_manifest["actual_budget"]["failure_identity"]["message"]
    if failure_message != "transport Newton exceeded its frozen iteration limit":
        raise RuntimeError("QN intent-02 failure identity drifted")

    assert_contains(
        s1_text,
        (
            "ROUTE_1_FAIL + ROUTE_2_FAIL + ACTIVATE_SYN_EDT_2D_V1",
            "NOT_NOVELTY_CLEARED_FOR_POSITIVE_ARCHITECTURE_CLAIM",
            "FULLY_TRANSPARENT_SYNTHETIC",
            "NOT_EXPERIMENTALLY_VALIDATED",
        ),
        "S1 report",
    )
    assert_contains(
        closeout_text,
        (
            "SYN_EDT_2D_V1_NUMERICAL_CONTRACT_NO_GO",
            "NO_ORACLE_EVENT_OR_PINN_EVIDENCE",
            "1.5106745331996967e-3",
            "1.4406930175716191e-9",
            "1.7339861280712171e-10",
            "0.002326388888888889 CPU_PROCESS_CORE_HOURS",
        ),
        "S2 terminal closeout",
    )

    with h5py.File(Q0_H5, "r") as handle:
        if handle.attrs["evidence_identity"] != "SYN_EDT_2D_V1_S2_NOT_YET_QUALIFIED":
            raise RuntimeError("Q0 H5 evidence ceiling drifted")
        if handle["time/circuit"].shape != (401,):
            raise RuntimeError("Q0 H5 circuit timeline drifted")
        if handle["time/field"].shape != (801,):
            raise RuntimeError("Q0 H5 field timeline drifted")

    return {
        "s0": s0,
        "s2": s2,
        "freeze": freeze,
        "q_manifest": q_manifest,
        "q0_manifest": q0_manifest,
        "q0_report": q0_report,
        "qn_manifest": qn_manifest,
        "s1_text": s1_text,
        "closeout_text": closeout_text,
    }


def write_csv(path: Path, rows: Iterable[Mapping[str, Any]], fields: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def style() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 9,
            "axes.titlesize": 11,
            "axes.labelsize": 9,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "axes.edgecolor": DARK_GRAY,
            "axes.labelcolor": BLACK,
            "text.color": BLACK,
            "xtick.color": DARK_GRAY,
            "ytick.color": DARK_GRAY,
            "figure.facecolor": WHITE,
            "axes.facecolor": WHITE,
            "savefig.facecolor": WHITE,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )


def save_figure(fig: plt.Figure, stem: str) -> None:
    png = OUT / f"{stem}.png"
    pdf = OUT / f"{stem}.pdf"
    fig.savefig(
        png,
        dpi=300,
        bbox_inches="tight",
        metadata={"Software": "GOAL-PAPER-ONE-SHOT-V1 generate_figures.py"},
    )
    fixed_time = datetime(2026, 8, 26, tzinfo=timezone.utc)
    fig.savefig(
        pdf,
        bbox_inches="tight",
        metadata={
            "Title": stem,
            "Creator": "GOAL-PAPER-ONE-SHOT-V1 generate_figures.py",
            "Producer": f"Matplotlib {matplotlib.__version__}",
            "CreationDate": fixed_time,
            "ModDate": fixed_time,
        },
    )
    plt.close(fig)


def rounded_box(
    ax: plt.Axes,
    xy: tuple[float, float],
    width: float,
    height: float,
    text: str,
    *,
    facecolor: str,
    edgecolor: str = WHITE,
    textcolor: str = BLACK,
    fontsize: float = 8.5,
    linewidth: float = 1.5,
) -> None:
    patch = FancyBboxPatch(
        xy,
        width,
        height,
        boxstyle="round,pad=0.012,rounding_size=0.018",
        facecolor=facecolor,
        edgecolor=edgecolor,
        linewidth=linewidth,
    )
    ax.add_patch(patch)
    ax.text(
        xy[0] + width / 2,
        xy[1] + height / 2,
        text,
        ha="center",
        va="center",
        color=textcolor,
        fontsize=fontsize,
        fontweight="bold",
        linespacing=1.25,
    )


def arrow(
    ax: plt.Axes,
    start: tuple[float, float],
    end: tuple[float, float],
    *,
    color: str = DARK_GRAY,
    connectionstyle: str = "arc3",
) -> None:
    ax.add_patch(
        FancyArrowPatch(
            start,
            end,
            arrowstyle="-|>",
            mutation_scale=13,
            linewidth=1.8,
            color=color,
            connectionstyle=connectionstyle,
        )
    )


def figure_01_route_gates(ctx: Mapping[str, Any]) -> None:
    rows = [
        {
            "order": 0,
            "node": "S0 preregistration",
            "status": "FROZEN",
            "evidence": "route order + fallback rules",
            "next": "bounded S1 review",
        },
        {
            "order": 1,
            "node": "Route 1: COMSOL 6.4",
            "status": "FAIL",
            "evidence": "legal research-use PASS not established; source contract incomplete",
            "next": "activate Route 2",
        },
        {
            "order": 2,
            "node": "Route 2: PCMO reaction-drift",
            "status": "FAIL",
            "evidence": "point-device + unpublished TCAD LUT; no 2D conservative field",
            "next": "activate Route 3",
        },
        {
            "order": 3,
            "node": "Route 3: SYN_EDT_2D_V1",
            "status": "ACTIVATED_SYNTHETIC",
            "evidence": "engineering-specified, transparent, not source-aligned",
            "next": "freeze S2 numerics",
        },
        {
            "order": 4,
            "node": "S2 numerical preregistration",
            "status": "FROZEN_BEFORE_RESULT",
            "evidence": "13-intent qualification ladder + hard stop/no rescue",
            "next": "execute in frozen order",
        },
    ]
    write_csv(
        DATA / "figure-01-route-gates.csv",
        rows,
        ("order", "node", "status", "evidence", "next"),
    )

    fig, ax = plt.subplots(figsize=(12.2, 6.2))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.text(
        0.02,
        0.96,
        "Pre-registered source fallback and numerical-entry gates",
        fontsize=15,
        fontweight="bold",
        color=NAVY,
        va="top",
    )
    ax.text(
        0.02,
        0.905,
        "Every transition was fixed before the downstream evidence was read.",
        fontsize=9.5,
        color=DARK_GRAY,
        va="top",
    )

    rounded_box(
        ax,
        (0.03, 0.59),
        0.17,
        0.18,
        "S0\nPREREGISTRATION\nroute order frozen",
        facecolor=NAVY,
        textcolor=WHITE,
    )
    rounded_box(
        ax,
        (0.27, 0.59),
        0.17,
        0.18,
        "S1\nBOUNDED REVIEW\n13 primary carriers",
        facecolor=BLUE,
        textcolor=WHITE,
    )
    rounded_box(
        ax,
        (0.51, 0.68),
        0.18,
        0.18,
        "ROUTE 1 — FAIL\nCOMSOL 6.4\nrequired research-use PASS\nnot established\n+ source-contract fail",
        facecolor="#F5D5D5",
        edgecolor=RED,
        fontsize=6.8,
    )
    rounded_box(
        ax,
        (0.51, 0.39),
        0.18,
        0.18,
        "ROUTE 2 — FAIL\nPCMO reaction–drift\nsource/topology gate",
        facecolor="#F5D5D5",
        edgecolor=RED,
    )
    rounded_box(
        ax,
        (0.77, 0.48),
        0.20,
        0.22,
        "ROUTE 3 — ACTIVATED\nSYN_EDT_2D_V1\ntransparent synthetic\nengineering contract",
        facecolor="#D9EEF7",
        edgecolor=BLUE,
    )
    rounded_box(
        ax,
        (0.77, 0.16),
        0.20,
        0.16,
        "S2 NUMERICS\n13 intents frozen\nbefore first result",
        facecolor="#D7EEE8",
        edgecolor=TEAL,
    )

    arrow(ax, (0.20, 0.68), (0.27, 0.68), color=NAVY)
    arrow(ax, (0.44, 0.68), (0.51, 0.77), color=BLUE)
    arrow(ax, (0.60, 0.68), (0.60, 0.57), color=RED)
    arrow(ax, (0.69, 0.48), (0.77, 0.59), color=RED)
    arrow(ax, (0.87, 0.48), (0.87, 0.32), color=BLUE)
    ax.text(0.615, 0.615, "automatic fallback", fontsize=7.5, color=RED)
    ax.text(0.69, 0.53, "automatic fallback", fontsize=7.5, color=RED, rotation=20)

    ax.add_patch(Rectangle((0.025, 0.035), 0.95, 0.075, facecolor=LIGHT, edgecolor=GRAY))
    ax.text(
        0.5,
        0.072,
        "Boundary: no COMSOL execution • no source stitching • no experimental identity • synthetic specification is not validation",
        ha="center",
        va="center",
        fontsize=8.4,
        color=DARK_GRAY,
    )
    save_figure(fig, FIGURES[0])


def figure_02_source_matrix(ctx: Mapping[str, Any]) -> None:
    row_labels = [
        "Research-use / executable rights",
        "2D device-field topology",
        "Conservative defect field",
        "Complete IC / BC / interfaces",
        "Absolute waveform",
        "Machine-readable reference fields",
        "S1 route disposition",
    ]
    col_labels = ["Route 1\nCOMSOL 6.4", "Route 2\nPCMO reaction–drift", "Route 3\nSYN_EDT_2D_V1"]
    labels = np.asarray(
        [
            ["NOT ESTABLISHED", "UNKNOWN / NOT PASS", "N/A — synthetic"],
            ["DOCUMENTED", "FAIL — point device", "ENGINEERING-SPECIFIED"],
            ["IDENTITY-SCOPED", "FAIL", "ENGINEERING-SPECIFIED"],
            ["PARTIAL", "FAIL", "ENGINEERING-SPECIFIED"],
            ["DOCUMENTED", "FAIL after compliance", "ENGINEERING-SPECIFIED"],
            ["FAIL", "FAIL", "LOCAL OUTPUTS ONLY*"],
            ["FAIL", "FAIL", "ACTIVATED AT S1*"],
        ],
        dtype=object,
    )
    # -2 fail/closed, -1 partial/unknown, 0 N/A, 1 documented component,
    # 2 explicit synthetic engineering specification (not validation).
    values = np.asarray(
        [
            [-2, -1, 0],
            [1, -2, 2],
            [1, -2, 2],
            [-1, -2, 2],
            [1, -2, 2],
            [-2, -2, 2],
            [-2, -2, 2],
        ],
        dtype=float,
    )
    rows = []
    for row_index, dimension in enumerate(row_labels):
        for col_index, route in enumerate(("route_1", "route_2", "route_3")):
            rows.append(
                {
                    "dimension": dimension,
                    "route": route,
                    "label": labels[row_index, col_index],
                    "category_code": int(values[row_index, col_index]),
                }
            )
    write_csv(
        DATA / "figure-02-source-matrix.csv",
        rows,
        ("dimension", "route", "label", "category_code"),
    )

    cmap = ListedColormap(["#F2C7C7", "#F6E2B8", "#E6EAEE", "#D8E8D7", "#D6EAF4"])
    norm = BoundaryNorm([-2.5, -1.5, -0.5, 0.5, 1.5, 2.5], cmap.N)
    fig, ax = plt.subplots(figsize=(11.8, 6.8))
    ax.imshow(values, cmap=cmap, norm=norm, aspect="auto")
    ax.set_xticks(range(3), col_labels, fontweight="bold")
    ax.set_yticks(range(len(row_labels)), row_labels)
    ax.tick_params(axis="x", bottom=False, top=True, labelbottom=False, labeltop=True, pad=8)
    ax.tick_params(axis="y", length=0, pad=8)
    for i in range(values.shape[0]):
        for j in range(values.shape[1]):
            ax.text(
                j,
                i,
                labels[i, j],
                ha="center",
                va="center",
                fontsize=8.1,
                fontweight="bold" if i == values.shape[0] - 1 else "normal",
                color=BLACK,
                linespacing=1.15,
            )
    ax.set_xticks(np.arange(-0.5, 3, 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(row_labels), 1), minor=True)
    ax.grid(which="minor", color=WHITE, linewidth=2)
    ax.tick_params(which="minor", bottom=False, left=False)
    ax.set_title(
        "Source-route qualification matrix (bounded S1 review)",
        loc="left",
        color=NAVY,
        fontweight="bold",
        fontsize=14,
        pad=26,
    )
    legend = [
        ("#F2C7C7", "failed / route-closing"),
        ("#F6E2B8", "partial / unknown-not-pass"),
        ("#D8E8D7", "documented component; not route admission"),
        ("#D6EAF4", "synthetic engineering specification; not validation"),
        ("#E6EAEE", "not applicable"),
    ]
    x = 0.02
    for color, text in legend:
        fig.add_artist(Rectangle((x, 0.022), 0.014, 0.018, transform=fig.transFigure, facecolor=color, edgecolor=GRAY))
        fig.text(x + 0.018, 0.031, text, va="center", fontsize=7.3, color=DARK_GRAY)
        x += 0.19 if "documented" not in text and "synthetic" not in text else 0.255
    fig.text(
        0.02,
        0.065,
        "* Route 3 was activated as a non-source-aligned benchmark; S2 later terminated numerically (Fig. 3).",
        fontsize=8,
        color=DARK_GRAY,
    )
    fig.subplots_adjust(left=0.29, right=0.98, top=0.80, bottom=0.13)
    save_figure(fig, FIGURES[1])


def figure_03_s2_ladder(ctx: Mapping[str, Any]) -> None:
    ladder = ctx["s2"]["qualification_ladder"]
    rows = []
    for item in ladder:
        intent = int(item["intent"])
        if intent == 1:
            status = "COMPLETED_Q0_GUARD_ONLY"
        elif intent == 2:
            status = "FAILED_EXECUTION_STOP"
        else:
            status = "NOT_STARTED_AFTER_STOP"
        rows.append(
            {
                "intent": intent,
                "case": item["case"],
                "space": item["space"],
                "time": item["time"],
                "control": item["control"],
                "role": item.get("role", ""),
                "status": status,
            }
        )
    write_csv(
        DATA / "figure-03-s2-ladder.csv",
        rows,
        ("intent", "case", "space", "time", "control", "role", "status"),
    )

    fig, ax = plt.subplots(figsize=(14.2, 5.6))
    ax.set_xlim(0.35, 13.65)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.set_title(
        "Frozen S2 qualification ladder and observed termination point",
        loc="left",
        color=NAVY,
        fontweight="bold",
        fontsize=14,
        pad=12,
    )
    ax.text(
        0.5,
        0.93,
        "Execution order →",
        fontsize=8.5,
        color=DARK_GRAY,
        va="center",
    )
    ax.plot([0.7, 13.3], [0.84, 0.84], color=GRAY, linewidth=2, zorder=0)

    abbreviations = {
        "FULL": "FULL",
        "DIRECT_T_TO_TRANSPORT_OFF": "DTT OFF",
        "FULL_ISOTHERMAL_COUPLING_OFF": "ISO OFF",
    }
    for row in rows:
        intent = int(row["intent"])
        status = row["status"]
        if status == "COMPLETED_Q0_GUARD_ONLY":
            face, edge, status_label = "#D7EEE8", TEAL, "Q0 GUARD\nVERIFIED"
        elif status == "FAILED_EXECUTION_STOP":
            face, edge, status_label = "#F4D1D1", RED, "FAILED\nSTOP"
        else:
            face, edge, status_label = "#EBEEF1", GRAY, "NOT\nSTARTED"
        x = intent
        ax.add_patch(
            FancyBboxPatch(
                (x - 0.43, 0.33),
                0.86,
                0.47,
                boxstyle="round,pad=0.012,rounding_size=0.02",
                facecolor=face,
                edgecolor=edge,
                linewidth=2 if intent <= 2 else 1,
            )
        )
        ax.text(x, 0.755, str(intent), ha="center", va="center", fontsize=11, fontweight="bold", color=NAVY)
        ax.text(x, 0.68, str(row["case"]), ha="center", va="center", fontsize=9, fontweight="bold")
        ax.text(
            x,
            0.59,
            f"{str(row['space'])[0].upper()}/{str(row['time'])[0].upper()}",
            ha="center",
            va="center",
            fontsize=8,
        )
        ax.text(
            x,
            0.50,
            abbreviations[str(row["control"])],
            ha="center",
            va="center",
            fontsize=6.6,
        )
        ax.text(
            x,
            0.39,
            status_label,
            ha="center",
            va="center",
            fontsize=6.7,
            color=RED if intent == 2 else DARK_GRAY,
            fontweight="bold",
            linespacing=1.05,
        )

    ax.annotate(
        "Hard stop at first driven case\nRuntimeError: transport Newton\nexceeded frozen iteration limit",
        xy=(2, 0.80),
        xytext=(3.3, 0.93),
        arrowprops=dict(arrowstyle="-|>", color=RED, linewidth=1.8),
        ha="left",
        va="top",
        fontsize=8.5,
        color=RED,
        fontweight="bold",
    )
    ax.add_patch(Rectangle((0.55, 0.10), 12.9, 0.13, facecolor=LIGHT, edgecolor=GRAY))
    ax.text(
        7,
        0.165,
        "Intent 1: zero-drive guard only  |  Intent 2: execution failure  |  Intents 3–13: no run, no fields, no event, no floor, no thermal gate",
        ha="center",
        va="center",
        fontsize=8.2,
        color=DARK_GRAY,
    )
    ax.text(
        0.55,
        0.035,
        "C/M/F = coarse/medium/fine.  Stop rule forbids timestep rescue, parameter rescue, or post-result threshold changes.",
        fontsize=7.8,
        color=DARK_GRAY,
    )
    save_figure(fig, FIGURES[2])


def q0_data(ctx: Mapping[str, Any]) -> dict[str, np.ndarray]:
    with h5py.File(Q0_H5, "r") as handle:
        circuit_time = np.asarray(handle["time/circuit"], dtype=float)
        field_time = np.asarray(handle["time/field"], dtype=float)
        circuit = {
            name: np.asarray(handle[f"circuit/{name}"], dtype=float)
            for name in (
                "voltage",
                "current_top",
                "current_bottom",
                "active_mass_hat",
                "joule_power",
                "heat_sink_power",
                "temperature_min",
                "temperature_max",
                "roi_depletion",
                "annulus_depletion",
            )
        }
        y = np.asarray(handle["fields/defect_fraction_y"], dtype=float)
        flux_r = np.asarray(handle["fields/defect_flux_r"], dtype=float)
        flux_z = np.asarray(handle["fields/defect_flux_z"], dtype=float)
        potential = np.asarray(handle["fields/electric_potential"], dtype=float)

    mass0 = circuit["active_mass_hat"][0]
    mass_drift = np.abs(circuit["active_mass_hat"] - mass0) / abs(mass0)
    circuit_rows = []
    for index, time in enumerate(circuit_time):
        circuit_rows.append(
            {
                "time_s": time,
                **{name: values[index] for name, values in circuit.items()},
                "relative_mass_drift": mass_drift[index],
                "temperature_min_offset_k": circuit["temperature_min"][index] - 300.0,
                "temperature_max_offset_k": circuit["temperature_max"][index] - 300.0,
            }
        )
    circuit_fields = (
        "time_s",
        *circuit.keys(),
        "relative_mass_drift",
        "temperature_min_offset_k",
        "temperature_max_offset_k",
    )
    write_csv(DATA / "figure-04-q0-circuit.csv", circuit_rows, circuit_fields)

    y_min = np.min(y, axis=1)
    y_max = np.max(y, axis=1)
    flux_max = np.max(np.sqrt(flux_r**2 + flux_z**2), axis=1)
    potential_max_abs = np.max(np.abs(potential), axis=1)
    field_rows = [
        {
            "time_s": field_time[index],
            "y_min": y_min[index],
            "y_max": y_max[index],
            "max_vector_flux_m_s": flux_max[index],
            "max_abs_potential_v": potential_max_abs[index],
        }
        for index in range(field_time.size)
    ]
    write_csv(
        DATA / "figure-04-q0-field.csv",
        field_rows,
        ("time_s", "y_min", "y_max", "max_vector_flux_m_s", "max_abs_potential_v"),
    )

    guard = ctx["q0_report"]["guard_report"]
    guard_rows = [
        {"guard": "mass drift", "value": guard["relative_mass_drift_max"], "unit": "relative", "passed": True},
        {"guard": "no-flux", "value": guard["no_flux_residual_max"], "unit": "scaled", "passed": True},
        {"guard": "heat balance", "value": guard["relative_heat_balance_residual_max"], "unit": "relative", "passed": True},
        {"guard": "terminal current mismatch", "value": guard["relative_terminal_current_mismatch_max"], "unit": "relative", "passed": True},
        {"guard": "state lower bound", "value": guard["y_min"], "unit": "fraction", "passed": True},
        {"guard": "state upper bound", "value": guard["y_max"], "unit": "fraction", "passed": True},
        {"guard": "temperature minimum", "value": guard["temperature_min_k"], "unit": "K", "passed": True},
        {"guard": "temperature maximum", "value": guard["temperature_max_k"], "unit": "K", "passed": True},
        {"guard": "event", "value": "N/A", "unit": "Q0 zero drive", "passed": True},
    ]
    write_csv(
        DATA / "figure-04-q0-guard-summary.csv",
        guard_rows,
        ("guard", "value", "unit", "passed"),
    )
    return {
        "circuit_time": circuit_time,
        "field_time": field_time,
        "mass_drift": mass_drift,
        "y_min": y_min,
        "y_max": y_max,
        **circuit,
    }


def figure_04_q0_guard(ctx: Mapping[str, Any]) -> None:
    data = q0_data(ctx)
    guard = ctx["q0_report"]["guard_report"]
    fig, axes = plt.subplots(2, 2, figsize=(12.2, 8.0), constrained_layout=True)
    ax = axes[0, 0]
    ax.plot(data["circuit_time"], data["voltage"], color=BLUE, linewidth=2, label="voltage (V)")
    ax.set_xlabel("time (s)")
    ax.set_ylabel("voltage (V)", color=BLUE)
    ax.set_ylim(-0.02, 0.02)
    ax.grid(alpha=0.25)
    ax2 = ax.twinx()
    ax2.plot(data["circuit_time"], data["current_top"] * 1e12, color=RED, linewidth=1.4, label="top current")
    ax2.plot(data["circuit_time"], data["current_bottom"] * 1e12, color=PURPLE, linewidth=1.2, linestyle="--", label="bottom current")
    ax2.set_ylabel("current (pA)", color=RED)
    ax2.set_ylim(-1.0, 1.0)
    handles = ax.get_lines() + ax2.get_lines()
    ax.legend(handles, [line.get_label() for line in handles], loc="upper right", fontsize=7.5)
    ax.set_title("a  Applied drive and terminal currents", loc="left", fontweight="bold")

    ax = axes[0, 1]
    ax.plot(data["field_time"], (data["y_min"] - 0.5) * 1e12, color=TEAL, linewidth=2, label="min y − 0.5")
    ax.plot(data["field_time"], (data["y_max"] - 0.5) * 1e12, color=NAVY, linewidth=1.2, linestyle="--", label="max y − 0.5")
    ax.set_ylim(-1.0, 1.0)
    ax.set_xlabel("time (s)")
    ax.set_ylabel("defect-fraction offset (10⁻¹²)")
    ax.grid(alpha=0.25)
    ax.legend(loc="upper right", fontsize=7.5)
    ax.text(
        0.03,
        0.08,
        f"max relative mass drift = {np.max(data['mass_drift']):.1e}",
        transform=ax.transAxes,
        fontsize=8,
        color=DARK_GRAY,
    )
    ax.set_title("b  State bounds and exact mass conservation", loc="left", fontweight="bold")

    ax = axes[1, 0]
    ax.plot(
        data["circuit_time"],
        (data["temperature_min"] - 300.0) * 1e12,
        color=BLUE,
        linewidth=1.5,
        label="min T − 300 K",
    )
    ax.plot(
        data["circuit_time"],
        (data["temperature_max"] - 300.0) * 1e12,
        color=RED,
        linewidth=1.5,
        label="max T − 300 K",
    )
    ax.axhline(0.0, color=DARK_GRAY, linewidth=0.8)
    ax.set_xlabel("time (s)")
    ax.set_ylabel("temperature offset (pK)")
    ax.grid(alpha=0.25)
    ax.legend(loc="center right", fontsize=7.5)
    ax.set_title("c  Floating-point-scale temperature offsets", loc="left", fontweight="bold")

    ax = axes[1, 1]
    ax.axis("off")
    ax.set_title("d  Frozen guard summary", loc="left", fontweight="bold")
    summary_lines = [
        ("Hard guards", "PASS", TEAL),
        ("mass drift", f"{guard['relative_mass_drift_max']:.1e}", BLACK),
        ("no-flux residual", f"{guard['no_flux_residual_max']:.1e}", BLACK),
        ("heat-balance residual", f"{guard['relative_heat_balance_residual_max']:.1e}", BLACK),
        ("terminal mismatch", f"{guard['relative_terminal_current_mismatch_max']:.1e}", BLACK),
        ("y range", f"{guard['y_min']:.1f} – {guard['y_max']:.1f}", BLACK),
        ("T range (K)", f"{guard['temperature_min_k']:.15g} – {guard['temperature_max_k']:.15g}", BLACK),
        ("event evaluation", "N/A for Q0", DARK_GRAY),
    ]
    y = 0.90
    for label, value, color in summary_lines:
        ax.text(0.04, y, label, fontsize=8.5, color=DARK_GRAY, va="center")
        ax.text(0.96, y, value, fontsize=8.5, color=color, va="center", ha="right", fontweight="bold")
        ax.plot([0.04, 0.96], [y - 0.045, y - 0.045], color=GRAY, linewidth=0.7)
        y -= 0.105
    ax.add_patch(Rectangle((0.035, 0.01), 0.93, 0.075, transform=ax.transAxes, facecolor="#FFF3D9", edgecolor=AMBER))
    ax.text(
        0.50,
        0.048,
        "Zero-drive guard verification only — not driven-event or oracle qualification",
        transform=ax.transAxes,
        ha="center",
        va="center",
        fontsize=7.5,
        color="#7B5414",
        fontweight="bold",
    )
    fig.suptitle(
        "Q0 intent 1: actual zero-drive H5 traces and guard report",
        fontsize=14,
        fontweight="bold",
        color=NAVY,
    )
    save_figure(fig, FIGURES[3])


def run_non_scientific_newton_diagnostic() -> dict[str, Any]:
    """Execute and trace the current core's private fixture-only Newton seam.

    This is deliberately the same 12-cell, one-step fixture used by the unit
    test and terminal closeout.  It is not a solver case, is never persisted as
    a CaseArtifact, and must never enter a ledger or scientific endpoint.
    """

    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from dataclasses import replace

    from scipy.sparse.linalg import spsolve
    from scipy.special import expit

    from pinn_pcm_sci.syn_edt_2d import (
        SynEdtCaseSpec,
        SynEdtControl,
        SynEdtPhysicalContract,
        SynEdtResolution,
        _OracleEngine,
        _stable_logit,
    )

    contract = SynEdtPhysicalContract.from_s0(S0, S2)
    case = replace(
        SynEdtCaseSpec.qualification("QN", contract).as_fixture(
            total_duration_s=0.00125
        ),
        active_radius_nm=50.0,
    )
    resolution = SynEdtResolution.fixture(
        active_h_max_nm=100.0,
        corner_h_max_nm=100.0,
        dt_max_s=0.00125,
        saved_field_interval_s=0.00125,
    )

    def build_state() -> tuple[Any, np.ndarray, np.ndarray, np.ndarray]:
        engine = _OracleEngine(contract, case, resolution, SynEdtControl.FULL)
        y_old = np.full(
            engine.mesh.active_full.size,
            case.initial_y,
            dtype=np.float64,
        )
        theta = np.ones(engine.mesh.domain.size, dtype=np.float64)
        psi, joule, *_ = engine._electric(y_old, theta, 0.01125)
        theta_target, *_ = engine._thermal(joule)
        relaxation = float(engine.numerics["block_relaxation"])
        theta_relaxed = (1.0 - relaxation) * theta + relaxation * theta_target
        return engine, y_old, psi, theta_relaxed

    # Fail closed against the unmodified production method first.  The trace
    # below is accepted only if the real method still reaches the exact frozen
    # exception rather than succeeding or failing by a different mechanism.
    engine, y_old, psi, theta_relaxed = build_state()
    dt_hat = 0.00125 / contract.time_s
    expected_exception = "transport Newton exceeded its frozen iteration limit"
    try:
        engine._transport_newton(y_old, y_old, psi, theta_relaxed, dt_hat)
    except RuntimeError as exc:
        if str(exc) != expected_exception:
            raise RuntimeError(
                f"NON_SCIENTIFIC diagnostic failure identity drifted: {exc}"
            ) from exc
    else:
        raise RuntimeError(
            "NON_SCIENTIFIC diagnostic unexpectedly passed the frozen Newton gate"
        )

    # Re-run the exact private residual/Jacobian/line-search operations while
    # retaining the accepted step and residual at each iteration.
    engine, y_old, psi, theta_relaxed = build_state()
    conductance, drive = engine._transport_coefficients(psi, theta_relaxed)
    w = _stable_logit(y_old)
    tolerance = float(engine.numerics["transport_scaled_residual_tolerance"])
    maximum = int(engine.numerics["transport_newton_max_iterations"])
    initial_step = float(engine.numerics["transport_newton_initial_step"])
    minimum_step = float(engine.numerics["transport_newton_min_step"])
    trace: list[dict[str, Any]] = []
    for iteration in range(maximum + 1):
        residual, matrix, scaled = engine._transport_system(
            w,
            y_old,
            dt_hat,
            conductance,
            drive,
            jacobian=True,
        )
        row: dict[str, Any] = {
            "iteration": iteration,
            "measured_scaled_residual": float(scaled),
            "accepted_step": "",
            "accepted_candidate_scaled_residual": "",
            "frozen_tolerance": tolerance,
            "frozen_max_iterations": maximum,
            "diagnostic_identity": "NON_SCIENTIFIC_DIAGNOSTIC",
        }
        trace.append(row)
        if scaled <= tolerance:
            raise RuntimeError(
                "NON_SCIENTIFIC diagnostic trace unexpectedly met tolerance"
            )
        if iteration == maximum or matrix is None:
            break
        delta = np.asarray(spsolve(matrix, -residual), dtype=np.float64)
        if not np.all(np.isfinite(delta)):
            raise RuntimeError("NON_SCIENTIFIC diagnostic Newton direction is non-finite")
        step = initial_step
        while step >= minimum_step - 1.0e-15:
            candidate = w + step * delta
            _, _, candidate_scaled = engine._transport_system(
                candidate,
                y_old,
                dt_hat,
                conductance,
                drive,
                jacobian=False,
            )
            if candidate_scaled < scaled or candidate_scaled <= tolerance:
                row["accepted_step"] = float(step)
                row["accepted_candidate_scaled_residual"] = float(candidate_scaled)
                w = candidate
                break
            step *= 0.5
        else:
            raise RuntimeError(
                "NON_SCIENTIFIC diagnostic line search reached its frozen minimum"
            )

    expected_initial = 1.5106745331996967e-3
    expected_final = 1.4406930175716191e-9
    measured_initial = float(trace[0]["measured_scaled_residual"])
    measured_final = float(trace[-1]["measured_scaled_residual"])
    accepted_steps = [float(row["accepted_step"]) for row in trace[:-1]]
    if engine.mesh.active_full.size != 12:
        raise RuntimeError("NON_SCIENTIFIC diagnostic active-cell count drifted")
    if maximum != 20 or not math.isclose(tolerance, 1.0e-10, rel_tol=0.0, abs_tol=0.0):
        raise RuntimeError("NON_SCIENTIFIC diagnostic frozen Newton contract drifted")
    if not all(step == 0.5 for step in accepted_steps):
        raise RuntimeError("NON_SCIENTIFIC diagnostic accepted-step sequence drifted")
    if not math.isclose(measured_initial, expected_initial, rel_tol=2.0e-9, abs_tol=0.0):
        raise RuntimeError("NON_SCIENTIFIC diagnostic initial residual drifted")
    # Sparse-direct libraries differ by a few ulps in the accumulated final
    # residual; the evidence identity is guarded at 1e-7 relative while the
    # exact render environment is recorded in source-manifest.json.
    if not math.isclose(measured_final, expected_final, rel_tol=1.0e-7, abs_tol=0.0):
        raise RuntimeError(
            "NON_SCIENTIFIC diagnostic final residual drifted: "
            f"{measured_final:.17g} != {expected_final:.17g}"
        )
    if measured_final <= tolerance:
        raise RuntimeError("NON_SCIENTIFIC diagnostic no longer exceeds tolerance")

    return {
        "trace": trace,
        "active_cells": int(engine.mesh.active_full.size),
        "dt_s": 0.00125,
        "voltage_v": 0.01125,
        "tolerance": tolerance,
        "maximum": maximum,
        "initial": measured_initial,
        "final": measured_final,
        "exception": expected_exception,
    }


def figure_05_newton_diagnostic(ctx: Mapping[str, Any]) -> None:
    diagnostic = run_non_scientific_newton_diagnostic()
    initial = float(diagnostic["initial"])
    final = float(diagnostic["final"])
    tolerance = float(diagnostic["tolerance"])
    budget = int(diagnostic["maximum"])
    required = int(math.ceil(math.log(initial / tolerance, 2.0)))
    iterations = np.arange(0, required + 1)
    analytic = initial * 0.5**iterations
    trajectory_rows = []
    trace_by_iteration = {
        int(row["iteration"]): row for row in diagnostic["trace"]
    }
    for index, value in zip(iterations, analytic):
        measured = trace_by_iteration.get(int(index), {})
        trajectory_rows.append(
            {
                "iteration": int(index),
                "measured_scaled_residual": measured.get(
                    "measured_scaled_residual", ""
                ),
                "accepted_step": measured.get("accepted_step", ""),
                "accepted_candidate_scaled_residual": measured.get(
                    "accepted_candidate_scaled_residual", ""
                ),
                "analytic_half_step_reference": value,
                "frozen_tolerance": tolerance,
                "frozen_max_iterations": budget,
                "within_frozen_budget": bool(index <= budget),
                "diagnostic_identity": "NON_SCIENTIFIC_DIAGNOSTIC",
            }
        )
    write_csv(
        DATA / "figure-05-newton-trajectory.csv",
        trajectory_rows,
        (
            "iteration",
            "measured_scaled_residual",
            "accepted_step",
            "accepted_candidate_scaled_residual",
            "analytic_half_step_reference",
            "frozen_tolerance",
            "frozen_max_iterations",
            "within_frozen_budget",
            "diagnostic_identity",
        ),
    )
    admissible_initial = tolerance * 2**budget
    summary_rows = [
        {"quantity": "fixture_active_cells", "value": diagnostic["active_cells"], "unit": "cells", "evidence_kind": "recomputed current-core fixture"},
        {"quantity": "fixture_dt", "value": diagnostic["dt_s"], "unit": "s", "evidence_kind": "fixture specification"},
        {"quantity": "fixture_voltage", "value": diagnostic["voltage_v"], "unit": "V", "evidence_kind": "fixture specification"},
        {"quantity": "initial_scaled_residual", "value": initial, "unit": "1", "evidence_kind": "measured fixture"},
        {"quantity": "iteration_20_scaled_residual", "value": final, "unit": "1", "evidence_kind": "measured fixture"},
        {"quantity": "frozen_tolerance", "value": tolerance, "unit": "1", "evidence_kind": "S2 contract"},
        {"quantity": "frozen_iteration_budget", "value": budget, "unit": "iterations", "evidence_kind": "S2 contract"},
        {"quantity": "ideal_half_step_iterations_required", "value": required, "unit": "iterations", "evidence_kind": "derived analytic"},
        {"quantity": "admissible_initial_residual_for_20_half_steps", "value": admissible_initial, "unit": "1", "evidence_kind": "derived analytic"},
        {"quantity": "observed_over_admissible", "value": initial / admissible_initial, "unit": "ratio", "evidence_kind": "derived analytic"},
        {"quantity": "jacobian_directional_relative_inf_error", "value": 1.7339861280712171e-10, "unit": "1", "evidence_kind": "measured fixture"},
        {"quantity": "outer_initial_mismatch_limit", "value": 4.096e-5, "unit": "1", "evidence_kind": "derived latent risk"},
        {"quantity": "verified_terminal_exception", "value": diagnostic["exception"], "unit": "exception identity", "evidence_kind": "recomputed current-core fixture"},
    ]
    write_csv(
        DATA / "figure-05-newton-summary.csv",
        summary_rows,
        ("quantity", "value", "unit", "evidence_kind"),
    )

    fig = plt.figure(figsize=(11.8, 7.6), constrained_layout=True)
    grid = fig.add_gridspec(2, 2, height_ratios=(2.2, 1.0))
    ax = fig.add_subplot(grid[0, :])
    measured_iterations = np.asarray(
        [int(row["iteration"]) for row in diagnostic["trace"]], dtype=int
    )
    measured_residuals = np.asarray(
        [float(row["measured_scaled_residual"]) for row in diagnostic["trace"]],
        dtype=float,
    )
    ax.semilogy(
        measured_iterations,
        measured_residuals,
        color=BLUE,
        linewidth=2.2,
        marker="o",
        markersize=3.5,
        label="recomputed current-core residual",
    )
    ax.semilogy(iterations, analytic, linestyle="--", color=NAVY, linewidth=1.3, label="analytic half-step reference r₀·2⁻ᵏ")
    ax.scatter([budget], [final], color=RED, s=58, zorder=4, label="frozen terminal residual")
    ax.axhline(tolerance, color=RED, linewidth=1.5, linestyle=":", label="frozen tolerance 10⁻¹⁰")
    ax.axvline(budget, color=RED, linewidth=1.2)
    ax.axvspan(budget, required + 0.5, color="#F8E3E3", alpha=0.8)
    ax.annotate(
        f"iteration 20\n{final:.3e} > 1e−10",
        xy=(budget, final),
        xytext=(14.0, 2.5e-8),
        arrowprops=dict(arrowstyle="->", color=RED),
        color=RED,
        fontsize=8.5,
        fontweight="bold",
    )
    ax.annotate(
        f"ideal half-step count needed: {required}",
        xy=(required, analytic[-1]),
        xytext=(17.5, 2.2e-11),
        arrowprops=dict(arrowstyle="->", color=NAVY),
        color=NAVY,
        fontsize=8,
    )
    ax.set_xlim(-0.5, required + 0.5)
    ax.set_ylim(2e-11, 4e-3)
    ax.set_xlabel("accepted Newton iteration")
    ax.set_ylabel("scaled transport residual")
    ax.grid(which="both", alpha=0.22)
    ax.legend(loc="upper right", fontsize=8)
    ax.set_title("a  Inner Newton half-step contract versus iteration budget", loc="left", fontweight="bold")

    ax = fig.add_subplot(grid[1, 0])
    ax.barh([0.7], [budget], color=RED, height=0.32, label="frozen budget")
    ax.barh([0.25], [required], color=BLUE, height=0.32, label="idealized minimum")
    ax.set_xlim(0, 26)
    ax.set_yticks([0.25, 0.7], ["idealized minimum", "frozen maximum"])
    ax.set_xlabel("iterations")
    ax.grid(axis="x", alpha=0.25)
    ax.text(budget + 0.3, 0.7, str(budget), va="center", color=RED, fontweight="bold")
    ax.text(required + 0.3, 0.25, str(required), va="center", color=BLUE, fontweight="bold")
    ax.set_title("b  Four-iteration incompatibility", loc="left", fontweight="bold")

    ax = fig.add_subplot(grid[1, 1])
    ax.axis("off")
    diagnostic_text = (
        f"Observed r₀ / admissible r₀ = {initial / admissible_initial:.2f}×\n"
        f"Jacobian directional error = {1.7339861280712171e-10:.3e}\n"
        "Outer block: 0.5 relaxation / 12 steps / 1e−8\n"
        "requires initial mismatch ≤ 4.096e−5 (latent risk only)"
    )
    ax.add_patch(FancyBboxPatch((0.02, 0.13), 0.96, 0.72, boxstyle="round,pad=0.02", facecolor=LIGHT, edgecolor=GRAY))
    ax.text(0.06, 0.72, diagnostic_text, va="top", fontsize=8.4, linespacing=1.55)
    ax.text(
        0.06,
        0.20,
        "Blue trace is recomputed; dashed curve is the analytic half-step reference.",
        fontsize=7.4,
        color=DARK_GRAY,
        fontstyle="italic",
    )
    ax.set_title("c  Scope and latent outer-block risk", loc="left", fontweight="bold")
    fig.suptitle(
        "NON-SCIENTIFIC DIAGNOSTIC — minimal QN fixture, not production or oracle evidence",
        fontsize=14,
        color=RED,
        fontweight="bold",
    )
    save_figure(fig, FIGURES[4])


def figure_06_claim_boundary(ctx: Mapping[str, Any]) -> None:
    claim_rows = [
        {
            "evidence_layer": "S1 bounded source review",
            "status": "COMPLETED",
            "allowed_claim": "route-specific source/legal/novelty disposition",
            "forbidden_extension": "global legality, novelty, or numerical validity",
        },
        {
            "evidence_layer": "Q0 zero-drive guard",
            "status": "VERIFIED",
            "allowed_claim": "zero-drive conservation and artifact-chain guards",
            "forbidden_extension": "driven event or qualified oracle",
        },
        {
            "evidence_layer": "QN first driven intent",
            "status": "EXECUTION_FAILED",
            "allowed_claim": "frozen Newton iteration-limit failure",
            "forbidden_extension": "physical or method-category failure",
        },
        {
            "evidence_layer": "convergence/event/thermal floors",
            "status": "NOT_REACHED",
            "allowed_claim": "none",
            "forbidden_extension": "event, floor, thermal-effect, or oracle claim",
        },
        {
            "evidence_layer": "PINN/development/OOD/formal",
            "status": "NOT_STARTED",
            "allowed_claim": "none",
            "forbidden_extension": "PINN effectiveness or comparative ranking",
        },
        {
            "evidence_layer": "experiment",
            "status": "NOT_PRESENT",
            "allowed_claim": "none",
            "forbidden_extension": "experimental validation or device prediction",
        },
    ]
    write_csv(
        DATA / "figure-06-claim-boundary.csv",
        claim_rows,
        ("evidence_layer", "status", "allowed_claim", "forbidden_extension"),
    )
    q0_budget = ctx["q0_manifest"]["actual_budget"]
    qn_budget = ctx["qn_manifest"]["actual_budget"]
    total_cpu = float(q0_budget["cpu_core_hours"]) + float(qn_budget["cpu_core_hours"])
    compute_rows = [
        {"quantity": "cpu_solver_intents_consumed", "value": 2, "unit": "of 40"},
        {"quantity": "completed_q0_guard_intents", "value": 1, "unit": "intent"},
        {"quantity": "failed_driven_intents", "value": 1, "unit": "intent"},
        {"quantity": "recorded_cpu_process_core_hours", "value": total_cpu, "unit": "CPU_PROCESS_CORE_HOURS"},
        {"quantity": "q0_timesteps", "value": q0_budget["solver_statistics"]["timesteps"], "unit": "steps"},
        {"quantity": "q0_linear_solves", "value": q0_budget["solver_statistics"]["linear_solves_total"], "unit": "solves"},
        {"quantity": "automatic_differentiation_work", "value": 0, "unit": "work units"},
        {"quantity": "peak_vram_bytes", "value": 0, "unit": "bytes"},
        {"quantity": "production_reruns_after_failure", "value": 0, "unit": "runs"},
    ]
    write_csv(
        DATA / "figure-06-compute-accounting.csv",
        compute_rows,
        ("quantity", "value", "unit"),
    )

    fig = plt.figure(figsize=(12.8, 7.8), constrained_layout=True)
    grid = fig.add_gridspec(1, 2, width_ratios=(1.45, 1.0))
    ax = fig.add_subplot(grid[0, 0])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.set_title("a  Evidence ceiling and permitted claim", loc="left", color=NAVY, fontweight="bold", fontsize=12)
    status_colors = {
        "COMPLETED": BLUE,
        "VERIFIED": TEAL,
        "EXECUTION_FAILED": RED,
        "NOT_REACHED": GRAY,
        "NOT_STARTED": GRAY,
        "NOT_PRESENT": GRAY,
    }
    y = 0.89
    for row in claim_rows:
        color = status_colors[row["status"]]
        ax.add_patch(FancyBboxPatch((0.02, y - 0.105), 0.96, 0.115, boxstyle="round,pad=0.01", facecolor=LIGHT, edgecolor=color, linewidth=1.5))
        ax.add_patch(Rectangle((0.035, y - 0.085), 0.018, 0.075, facecolor=color, edgecolor=color))
        ax.text(0.07, y - 0.028, row["evidence_layer"], fontsize=8.5, fontweight="bold", va="center")
        ax.text(0.96, y - 0.028, row["status"], fontsize=7.1, color=color, ha="right", va="center", fontweight="bold")
        ax.text(0.07, y - 0.072, "May claim: " + row["allowed_claim"], fontsize=7.1, color=DARK_GRAY, va="center")
        y -= 0.145
    ax.text(
        0.02,
        0.015,
        "Ceiling: NO_ORACLE_EVENT_OR_PINN_EVIDENCE",
        fontsize=9,
        color=RED,
        fontweight="bold",
    )

    ax = fig.add_subplot(grid[0, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.set_title("b  Gross compute accounting at hard stop", loc="left", color=NAVY, fontweight="bold", fontsize=12)
    left = 0.08
    width = 0.84
    ybar = 0.82
    ax.add_patch(Rectangle((left, ybar), width * 1 / 40, 0.075, facecolor=TEAL, edgecolor=WHITE))
    ax.add_patch(Rectangle((left + width / 40, ybar), width * 1 / 40, 0.075, facecolor=RED, edgecolor=WHITE))
    ax.add_patch(Rectangle((left + 2 * width / 40, ybar), width * 38 / 40, 0.075, facecolor=GRAY, edgecolor=WHITE))
    ax.text(left, ybar + 0.10, "CPU solver-intent budget: 2 / 40 consumed", fontsize=8.5, fontweight="bold")
    ax.text(left, ybar - 0.035, "1 Q0 guard completed", fontsize=7.2, color=TEAL)
    ax.text(left + 0.39, ybar - 0.035, "1 driven failure", fontsize=7.2, color=RED)
    ax.text(left + 0.68, ybar - 0.035, "38 not run", fontsize=7.2, color=DARK_GRAY)

    cards = [
        ("Recorded production solver CPU", f"{total_cpu:.16f}\ncore-hours (freeze excluded)"),
        ("Q0 execution", f"{q0_budget['solver_statistics']['timesteps']} timesteps\n{q0_budget['solver_statistics']['linear_solves_total']} linear solves"),
        ("Neural / GPU", "0 forward calls\n0 AD work / 0 VRAM"),
        ("After failure", "0 production reruns\n0 rescue attempts"),
    ]
    positions = [(0.08, 0.54), (0.54, 0.54), (0.08, 0.29), (0.54, 0.29)]
    for (title, value), (x, y0) in zip(cards, positions):
        ax.add_patch(FancyBboxPatch((x, y0), 0.38, 0.17, boxstyle="round,pad=0.012", facecolor=LIGHT, edgecolor=GRAY))
        ax.text(x + 0.025, y0 + 0.13, title, fontsize=7.4, color=DARK_GRAY, fontweight="bold")
        ax.text(x + 0.025, y0 + 0.075, value, fontsize=8.2, color=BLACK, va="center", linespacing=1.35)
    ax.add_patch(Rectangle((0.08, 0.08), 0.84, 0.10, facecolor="#FFF3D9", edgecolor=AMBER))
    ax.text(
        0.50,
        0.13,
        "Unused budget is not evidence; the frozen hard gate ended the route.",
        ha="center",
        va="center",
        fontsize=7.8,
        color="#7B5414",
        fontweight="bold",
    )
    fig.suptitle(
        "Claim–evidence boundary and compute accounting",
        fontsize=14,
        fontweight="bold",
        color=NAVY,
    )
    save_figure(fig, FIGURES[5])


def write_manifest() -> None:
    source_roles = {
        S0: "route order, synthetic identity, budgets",
        S2: "frozen numerical ladder and no-rescue contract",
        S1: "bounded source/legal/novelty route adjudication",
        CLOSEOUT: "terminal S2 status and non-scientific diagnostic facts",
        FREEZE: "effective Q-only freeze identity",
        Q_MANIFEST: "Q0/QL/QN/QH roles",
        Q0_MANIFEST: "Q0 execution and compute accounting",
        Q0_H5: "actual Q0 zero-drive traces",
        Q0_REPORT: "Q0 guard summary and event non-applicability",
        QN_MANIFEST: "first driven QN failure and compute accounting",
        CORE: "current private residual/Jacobian/line-search seam for non-scientific diagnostic",
        CORE_TEST: "fixture identity and explicit NON_SCIENTIFIC_DIAGNOSTIC boundary",
    }
    sources = [
        {
            "path": relative(path),
            "sha256": sha256(path),
            "expected_sha256": EXPECTED_SHA256.get(path),
            "role": role,
        }
        for path, role in source_roles.items()
    ]
    output_paths = [OUT / f"{stem}.{suffix}" for stem in FIGURES for suffix in ("png", "pdf")]
    data_paths = sorted(DATA.glob("*.csv"))
    payload = {
        "schema_version": "goal-paper-one-shot-v1-figure-source-manifest-v1",
        "evidence_ceiling": "NO_ORACLE_EVENT_OR_PINN_EVIDENCE",
        "terminal_disposition": "SYN_EDT_2D_V1_NUMERICAL_CONTRACT_NO_GO",
        "generator": {
            "path": relative(Path(__file__)),
            "sha256": sha256(Path(__file__)),
        },
        "render_environment": {
            "python": platform.python_version(),
            "matplotlib": matplotlib.__version__,
            "numpy": np.__version__,
            "h5py": h5py.__version__,
        },
        "sources": sources,
        "source_data": [
            {"path": relative(path), "sha256": sha256(path)} for path in data_paths
        ],
        "documentation": {
            "path": relative(CAPTIONS),
            "sha256": sha256(CAPTIONS),
        },
        "figures": [
            {"path": relative(path), "sha256": sha256(path), "bytes": path.stat().st_size}
            for path in output_paths
        ],
        "reproduction": {
            "command": "python paper/figures/generate_figures.py",
            "working_directory": ".",
            "required_imports": ["numpy", "h5py", "matplotlib"],
            "production_scientific_solver_invoked": False,
            "non_scientific_fixture_diagnostic_invoked": True,
        },
        "claim_guards": [
            "Q0 is zero-drive guard evidence only",
            "QN intent 2 failed before case/evaluation/report fields existed",
            "Newton figure is explicitly NON_SCIENTIFIC_DIAGNOSTIC",
            "Newton trace invokes private core seams only on the 12-cell non-scientific fixture and is never ledgered",
            "no oracle, event, PINN, OOD, formal, reserve, or experimental result is plotted",
        ],
        "post_render_checks": [
            "all PNG files decode and have nonzero dimensions",
            "all PDF files have PDF header and EOF marker",
            "all figure and source-data hashes match the manifest",
            "generator and captions hashes match the manifest",
            "captions cover all six stable figure stems",
        ],
    }
    target = OUT / "source-manifest.json"
    target.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False)
        + "\n",
        encoding="utf-8",
    )


def verify_package() -> None:
    manifest_path = OUT / "source-manifest.json"
    manifest = read_json(manifest_path)
    generator = manifest.get("generator", {})
    if generator.get("sha256") != sha256(Path(__file__)):
        raise RuntimeError("source manifest does not bind the exact generator bytes")
    documentation = manifest.get("documentation", {})
    if documentation.get("sha256") != sha256(CAPTIONS):
        raise RuntimeError("source manifest does not bind the exact captions bytes")
    caption_text = CAPTIONS.read_text(encoding="utf-8")
    for stem in FIGURES:
        if stem not in caption_text:
            raise RuntimeError(f"captions do not cover {stem}")
    for entry in manifest["source_data"] + manifest["figures"]:
        path = ROOT / entry["path"]
        if sha256(path) != entry["sha256"]:
            raise RuntimeError(f"post-render hash mismatch: {entry['path']}")
    for stem in FIGURES:
        png = OUT / f"{stem}.png"
        image = plt.imread(png)
        if image.ndim not in (2, 3) or min(image.shape[:2]) <= 0:
            raise RuntimeError(f"PNG decode/dimension check failed: {png.name}")
        pdf = OUT / f"{stem}.pdf"
        raw = pdf.read_bytes()
        if not raw.startswith(b"%PDF-") or b"%%EOF" not in raw[-1024:]:
            raise RuntimeError(f"PDF signature check failed: {pdf.name}")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    DATA.mkdir(parents=True, exist_ok=True)
    style()
    ctx = validate_sources()
    figure_01_route_gates(ctx)
    figure_02_source_matrix(ctx)
    figure_03_s2_ladder(ctx)
    figure_04_q0_guard(ctx)
    figure_05_newton_diagnostic(ctx)
    figure_06_claim_boundary(ctx)
    write_manifest()
    verify_package()
    print(f"Wrote {len(FIGURES)} PNG/PDF figure pairs to {OUT}")


if __name__ == "__main__":
    main()
