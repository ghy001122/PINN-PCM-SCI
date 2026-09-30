"""Render fixed-record interface comparisons and report recorded work only.

No array rescoring, neural inference, PDE solve, or qualification adjudication.
Run with the project Python. All outputs remain in this revision directory.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
TABLES = HERE / "tables"
FIGURES = HERE / "figures"
LEGACY = "paper/paper_revision_20260918/tables/reader-all-effects.csv"
COVERAGE = "paper/paper_revision_20260926_core/tables/fcov-all-effects.csv"
LEGACY_GATES = "paper/paper_revision_20260918/tables/reader-all-decisions.csv"
COVERAGE_GATES = "paper/paper_revision_20260926_core/tables/fcov-all-decisions.csv"
METRICS = ("Ephi", "bottom_current_NRMSE", "power_trace_NRMSE")
TITLE = "What the electrical training interface changes—and what it does not"
SOURCES: dict[str, dict] = {}


def source(path: str) -> Path:
    p = ROOT / path
    raw = p.read_bytes()
    SOURCES[path] = {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
    return p


def records(path: str) -> list[dict]:
    with source(path).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def read_json(path: str) -> dict:
    return json.loads(source(path).read_text(encoding="utf-8"))


def save_csv(name: str, rows: list[dict]) -> None:
    fields = list(dict.fromkeys(k for row in rows for k in row))
    with (TABLES / name).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def markdown(headers: list[str], rows: list[list]) -> str:
    return "\n".join([
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
        *("| " + " | ".join(str(x) for x in row) + " |" for row in rows),
    ])


def boolean(value: str) -> bool:
    if value not in ("True", "False"):
        raise ValueError(f"Unexpected saved Boolean {value!r}")
    return value == "True"


def exactly_one(rows: list[dict], **keys) -> tuple[int, dict]:
    matches = [(i + 2, row) for i, row in enumerate(rows)
               if all(str(row.get(k)) == str(v) for k, v in keys.items())]
    if len(matches) != 1:
        raise ValueError(f"Expected one existing row for {keys}; got {len(matches)}")
    return matches[0]


def select_effects() -> list[dict]:
    historical = records(LEGACY)
    coverage = records(COVERAGE)
    gates = records(LEGACY_GATES)
    coverage_gates = records(COVERAGE_GATES)
    selections = []
    for case in ("original", "shorter"):
        for seed in (29, 43):
            selections.append(("A", "E_vs_F", case, seed, "spatial"))
    for seed in (29, 43):
        selections.append(("B", "E_vs_F_cov", "shorter", seed, "spatial"))
    for seed in (29, 43):
        selections.append(("C", "E_vs_D_E", "shorter", seed, "spatial"))
    for reference in ("old", "refined", "spatial"):
        selections.append(("D", "E_vs_B_E", "original", 43, reference))
    output = []
    for panel, comparison, case, seed, reference in selections:
        is_cov = comparison == "E_vs_F_cov"
        identity = dict(reference=reference, reader="fine", seed=seed)
        if is_cov:
            gate_line, gate = exactly_one(coverage_gates, **identity)
            a, b = boolean(gate[comparison + "_A"]), boolean(gate[comparison + "_B"])
        else:
            identity.update(protocol=case)
            gate_line, gate = exactly_one(gates, **identity, comparison=comparison)
            a, b = boolean(gate["A"]), boolean(gate["B"])
        for metric in METRICS:
            line, row = exactly_one(coverage if is_cov else historical, **identity,
                                    comparison=comparison, metric=metric)
            candidate = float(row["candidate" if is_cov else "candidate_error"])
            control = float(row["control" if is_cov else "control_error"])
            delta = control - candidate
            relative = float(row["relative_error_reduction"])
            assert math.isclose(delta, -float(row["signed_candidate_minus_control"]),
                                rel_tol=2e-12, abs_tol=2e-15)
            assert math.isclose(relative, delta / control, rel_tol=2e-12, abs_tol=2e-15)
            output.append(dict(
                panel=panel, protocol=case, seed=seed, reference=reference, reader="fine",
                comparison=comparison, candidate_role="E", control_role=comparison[5:],
                metric=metric, candidate_error=candidate, control_error=control,
                absolute_difference_control_minus_E=delta,
                relative_error_reduction=relative,
                display_difference=delta * (1 if metric == "Ephi" else 100),
                display_difference_unit="phase fraction" if metric == "Ephi" else "percentage points",
                original_A=a, original_B=b,
                metric_source=COVERAGE if is_cov else LEGACY, metric_source_line=line,
                qualification_source=COVERAGE_GATES if is_cov else LEGACY_GATES,
                qualification_source_line=gate_line,
                phase_measure="full history; original 160x80 ROI",
                port_measure="native 240x120 common electrical readout; original normalization",
                status="VERIFIED_EXISTING_RECORD",
            ))
    assert len(output) == 33
    assert all(r["original_B"] for r in output if r["panel"] in ("A", "B"))
    assert all(not r["original_A"] and not r["original_B"]
               for r in output if r["panel"] in ("C", "D"))
    return output


def grouped(rows: list[dict], panel: str) -> list[list[dict]]:
    selected = [row for row in rows if row["panel"] == panel]
    return [selected[i:i + 3] for i in range(0, len(selected), 3)]


def effect_table(rows: list[dict]) -> None:
    display = []
    for panel in "ABCD":
        for triple in grouped(rows, panel):
            row = triple[0]
            identity = f"{row['comparison'].replace('_vs_', '/')}; {row['protocol']}/{row['seed']}"
            if panel == "D":
                identity += "; " + {"old": "original ref.", "refined": "time ref.", "spatial": "space ref."}[row["reference"]]
            display.append([
                identity,
                f"{triple[0]['absolute_difference_control_minus_E']:+.6f}",
                " / ".join(f"{r['display_difference']:+.5f}" for r in triple[1:]),
                " / ".join(f"{100 * r['relative_error_reduction']:+.2f}" for r in triple),
                f"{'Pass' if row['original_A'] else 'Fail'} / {'Pass' if row['original_B'] else 'Fail'}",
            ])
    text = markdown(["Comparison; protocol/seed", "Δ phase RMS", "Δ I / Δ P (pp)",
                     "Relative reduction: φ / I / P (%)", "Original A / B"], display)
    text += ("\n\nΔ = control error − E error; positive values favor E. Relative reduction is Δ/control. "
             "The current and power differences are percentage points, not relative percentages. "
             "A/B are the original full qualification decisions, copied from saved decision tables; "
             "they are not reconstructed from these three metrics. Rows A–C use the spatial reference "
             "and fine reader; the B_E boundary uses the original-protocol seed-43 fine reader under "
             "all three pre-existing references. Display rounding never changes a decision. "
             "Full-precision values and source lines: [interface-effects-full.csv](interface-effects-full.csv).\n")
    (TABLES / "interface-effects-compact.md").write_text(text, encoding="utf-8")


def figure(rows: list[dict]) -> None:
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 12.5,
                         "axes.titlesize": 12.5, "axes.labelsize": 12.5,
                         "xtick.labelsize": 12.5, "ytick.labelsize": 12.5,
                         "pdf.fonttype": 42, "ps.fonttype": 42})
    # 12.5 pt axes become 8.04 pt at the manuscript's 6.82-inch image width.
    fig = plt.figure(figsize=(10.6, 10.0), facecolor="white")
    gs = fig.add_gridspec(4, 3, left=.185, right=.974, top=.848, bottom=.152,
                          height_ratios=[4.3, 2.7, 2.7, 3.5], hspace=.81, wspace=.25)
    blue, red, grey = "#126C8B", "#B23A33", "#545D66"
    titles = {
        "A": "A  E / F · four paired fits",
        "B": r"B  E / F$_{\rm cov}$ · coverage-enhanced soft electrical control",
        "C": r"C  E / D$_E$ · added thermal/phase residual package (detail axes)",
        "D": r"D  E / B$_E$ · interpolation boundary, original / 43 (detail axes)",
    }
    names = ["Phase RMS", "Current NRMSE (%)", "Power NRMSE (%)"]
    for pi, panel in enumerate("ABCD"):
        triples = grouped(rows, panel)
        for mi, metric in enumerate(METRICS):
            ax = fig.add_subplot(gs[pi, mi])
            if mi == 0:
                fig.text(.032, ax.get_position().y1 + .016, titles[panel],
                         fontweight="bold", fontsize=12.5, va="bottom")
            labels = []
            for j, triple in enumerate(triples):
                row = triple[mi]
                factor = 1 if mi == 0 else 100
                e, c = row["candidate_error"] * factor, row["control_error"] * factor
                worse = e > c
                color = red if worse else blue
                if worse:
                    ax.axhspan(j - .34, j + .34, color=red, alpha=.065, zorder=0)
                ax.plot([c, e], [j, j], color=color, lw=2.8, zorder=2)
                ax.scatter([c], [j], s=58, marker="o", facecolors="white",
                           edgecolors=grey, linewidths=1.6, zorder=4)
                ax.scatter([e], [j], s=44, marker="D", facecolors=color,
                           edgecolors=color, linewidths=.8, zorder=5)
                if panel == "D":
                    labels.append({"old": "Original reference", "refined": "Time-refined", "spatial": "Space-refined"}[row["reference"]])
                else:
                    labels.append(f"{row['protocol'].capitalize()} / {row['seed']}")
            ax.set_yticks(range(len(triples)), labels if mi == 0 else [])
            ax.set_ylim(len(triples) - .5, -.5)
            # A/B share zero-based axes. Declared detail axes keep small adverse
            # C/D differences legible without changing the native error values.
            axis_rows = rows if panel in "AB" else [r for triple in triples for r in triple]
            values = [v * (1 if mi == 0 else 100) for r in axis_rows if r["metric"] == metric
                      for v in (r["candidate_error"], r["control_error"])]
            if panel in "AB":
                ax.set_xlim(0, max(values) * 1.12)
            else:
                margin = (max(values) - min(values)) * .18
                ax.set_xlim(min(values) - margin, max(values) + margin)
            ax.set_xlabel(names[mi], labelpad=3)
            ax.grid(axis="x", color="#DDE3E7", lw=.6, zorder=0)
            for side in ("top", "right", "left"):
                ax.spines[side].set_visible(False)
            ax.spines["bottom"].set_color("#AAB2B8")
            ax.tick_params(axis="y", length=0, pad=8)
            ax.locator_params(axis="x", nbins=3)
            if mi == 0 and panel == "C":
                ax.xaxis.set_major_formatter(matplotlib.ticker.FormatStrFormatter("%.4f"))
    fig.suptitle(TITLE, x=.51, y=.979, fontsize=14.5, fontweight="bold")
    fig.text(.51, .944, "Same final electrical repair · lower error is better · fixed historical endpoints",
             ha="center", fontsize=11.5, color="#38434B")
    handles = [
        Line2D([], [], marker="D", color=blue, lw=0, markersize=7, label="E (filled diamond)"),
        Line2D([], [], marker="o", color=grey, markerfacecolor="white", lw=0, markersize=7,
               label="Paired control (open circle)"),
        Line2D([], [], marker="D", color=red, lw=2, markersize=6, label="E has larger error"),
    ]
    fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(.51, .925), ncol=3,
               frameon=False, fontsize=11.5, handletextpad=.6, columnspacing=1.0)
    fig.text(.05, .027,
             "A–C: spatial reference / fine reader. D: three references / fine reader. C–D: expanded raw-error axes.\n"
             "Phase: original 160 × 80 ROI; ports: native 240 × 120. Configuration comparisons; no isolated VJP attribution.",
             fontsize=10, color="#38434B", linespacing=1.6)
    fig.savefig(FIGURES / "electrical-interface-effects.png", dpi=240, facecolor="white")
    fig.savefig(FIGURES / "electrical-interface-effects.pdf", facecolor="white")
    plt.close(fig)


def costs() -> tuple[list[dict], list[dict]]:
    branches = []
    environments = {"original": read_json("paper/paper_v31/evidence/public-execution-summary.json")["stage_B_environment"],
                    "F_cov": read_json("outputs/runs/20260926-core-revision-vo2-bridge/environment.json")}
    for case, base in [("original", "paper/paper_v31/evidence/confirmation"),
                       ("shorter", "paper/paper_v32/evidence")]:
        for seed in (29, 43):
            for role in ("E", "F"):
                path = f"{base}/seed-{seed}/{'F_raw' if role == 'F' else role}/terminal.json"
                terminal = read_json(path)
                assert terminal["status"] == "VALID_FIXED_ENDPOINT"
                stat, lb = terminal["statistics"], terminal["lbfgs"]
                elec, explicit = stat["electrical"], stat.get("explicit_work", {})
                branches.append(dict(protocol=case, seed=seed, role=role, stage="branch_training",
                    adam=terminal["adam_updates"], lbfgs_evaluations=lb["evaluations"],
                    lbfgs_accepted=lb["accepted_steps"], forward_solves=elec["forward_solves"],
                    adjoint_solves=elec["adjoint_solves"],
                    explicit_face_evaluations=explicit.get("explicit_face_evaluations"),
                    full_grid_network_evaluations=explicit.get("full_grid_network_evaluations"),
                    termination=lb["termination"], recorded_seconds=terminal.get("elapsed_seconds_internal"),
                    timing_field="elapsed_seconds_internal" if "elapsed_seconds_internal" in terminal else "NOT_RECORDED",
                    timing_comparable=False, source=path,
                    electrical_count_source="statistics.electrical; direct per-branch record, not aggregate allocation",
                    device=terminal.get("device", "NOT_RECORDED"),
                    hardware_source="paper/paper_v31/evidence/public-execution-summary.json#/stage_B_environment" if case == "original" else "NOT_CONFIRMED_FOR_TIMING_COMPARISON"))
    fcov_table = records("paper/paper_revision_20260926_core/tables/fcov-work.csv")
    for seed in (29, 43):
        path = f"outputs/runs/20260926-core-revision-vo2-bridge/fcov/seed-{seed}/F_cov/terminal.json"
        terminal = read_json(path)
        stat, lb, progress = terminal["statistics"], terminal["lbfgs"], terminal["progress"]
        _, saved = exactly_one(fcov_table, seed=seed)
        assert progress["lbfgs_charged"] == progress["lbfgs_complete"] == lb["evaluations"]
        assert int(saved["lbfgs_accepted"]) == lb["accepted_steps"]
        branches.append(dict(protocol="shorter", seed=seed, role="F_cov", stage="branch_training",
            adam=progress["adam_updates"], lbfgs_evaluations=lb["evaluations"],
            lbfgs_accepted=lb["accepted_steps"], forward_solves=stat["electrical"]["forward_solves"],
            adjoint_solves=stat["electrical"]["adjoint_solves"],
            explicit_face_evaluations=stat["explicit_work"]["explicit_face_evaluations"],
            full_grid_network_evaluations=stat["explicit_work"]["full_grid_network_evaluations"],
            termination=lb["termination"], recorded_seconds=terminal["current_session_seconds"],
            timing_field="current_session_seconds", timing_comparable=False, source=path,
            electrical_count_source="statistics.electrical; zero sparse solves does not mean zero electrical work",
            device=terminal["device"], hardware_source="outputs/runs/20260926-core-revision-vo2-bridge/environment.json"))
    shorter = read_json("paper/paper_v32/evidence/execution-summary.json")
    for key in ("forward_solves", "adjoint_solves"):
        actual = sum(r[key] for r in branches if r["protocol"] == "shorter" and r["role"] == "E")
        assert actual == shorter["totals"]["E_forward" if key == "forward_solves" else "E_adjoint"] == 39186
    stages = []
    parent_csv = "paper/paper_v32/tables/common-parents-and-calibration.csv"
    for row in records(parent_csv):
        case = "original" if row["protocol"] == "Original" else "shorter"
        stages.append(dict(protocol=case, seed=int(row["seed"]), role="shared parent", stage="parent",
            adam=int(row["Adam"]), lbfgs_evaluations=int(row["complete_evaluations"]),
            lbfgs_accepted=None, forward_solves=None, adjoint_solves=None,
            source=parent_csv, scope="one parent shared by E/F; shorter parents reused by F_cov, not retrained"))
    for case, base in [("original", "paper/paper_v31/evidence/confirmation"),
                       ("shorter", "paper/paper_v32/evidence")]:
        for seed in (29, 43):
            path = f"{base}/seed-{seed}/calibration.json"
            cal = read_json(path)
            e = cal["statistics"]["electrical"]
            stages.append(dict(protocol=case, seed=seed, role="shared calibration", stage="calibration",
                adam=0, lbfgs_evaluations=0, forward_solves=e["forward_solves"],
                adjoint_solves=e["adjoint_solves"], source=path,
                scope="one shared calibration; F_cov inherits original scales, no recalibration"))
    # These are the actual historical readout counters, with their original scopes.
    old_cost = "paper/paper_v31/tables/clean-execution.csv"
    for row in records(old_cost):
        stages.append(dict(protocol="original", seed=int(row["seed"]), role="F" if row["role"] == "F_raw" else row["role"],
            stage="historical_projected_readout", forward_solves=int(row["inference_forward"]),
            adjoint_solves=0, source=old_cost,
            scope="one historical readout per endpoint; not a measured total for both later common readers"))
    stages.append(dict(protocol="shorter", seed="aggregate", role="E/F/B_E", stage="historical_projected_readout",
        forward_solves=shorter["totals"]["inference_forward"], adjoint_solves=0,
        source="paper/paper_v32/evidence/execution-summary.json#/totals",
        scope="1390 aggregate: four endpoints plus one shared B_E; not allocated to individual endpoints"))
    for seed in (29, 43):
        for level in ("coarse", "fine"):
            path = f"outputs/runs/20260926-core-revision-vo2-bridge/fcov/seed-{seed}/F_cov/{level}/readers-complete.json"
            readout = read_json(path)
            assert readout["status"] == "PASS"
            stages.append(dict(protocol="shorter", seed=seed, role="F_cov", stage="common_readout_" + level,
                forward_solves=readout["forward_solves"], adjoint_solves=0, source=path,
                scope="completed powered-time sparse solves; all 1001 times saved"))
            stages.append(dict(protocol="shorter", seed=seed, role="F_cov", stage="discarded_readout_" + level,
                discarded_forward_upper_bound=readout.get("discarded_inflight_upper_bound", 0), source=path,
                scope="upper bound for discarded in-flight work, not an additional completed solve count"))
    save_csv("accuracy-work-full.csv", branches)
    save_csv("accuracy-work-stages.csv", stages)
    display = [[r["protocol"].capitalize() + "/" + str(r["seed"]), r["role"], r["adam"],
                f"{r['lbfgs_evaluations']} / {r['lbfgs_accepted']}",
                f"{r['forward_solves']:,} / {r['adjoint_solves']:,}",
                "NR" if r["explicit_face_evaluations"] is None else f"{r['explicit_face_evaluations']:,}"]
               for r in branches]
    main_table = markdown(["Protocol/seed", "Role", "Adam", "L-BFGS eval. / accepted",
                           "Forward / adjoint solves", "Explicit face calls"], display)
    (TABLES / "accuracy-work-main.md").write_text(
        main_table + "\n\nSame fixed endpoints as the interface-effect table. NR = not recorded, not zero. "
        "These are actual branch-training counts, not comparable wall times; zero sparse solves does not mean "
        "zero electrical work. Parent, calibration, readout and discarded work are separate in S26.\n",
        encoding="utf-8")
    text = ("Actual work for the fixed endpoints in the interface-effect comparison. "
            "Accuracy uses the unchanged common-reader errors in the adjacent effect table; "
            "the work below is not a wall-time speed comparison.\n\n" +
            markdown(["Protocol/seed", "Role", "Adam", "L-BFGS evaluations / accepted steps",
                      "Training forward / adjoint solves", "Explicit face evaluations"], display) +
            "\n\nNR = not recorded in that log, not zero. Every arm completed 1500 Adam updates "
            "and 300 full L-BFGS evaluations; trial/repeated closures count, and budget interruption may "
            "roll back to the last accepted state. Sparse-solve counts and explicit face-operator calls "
            "are distinct work measures. A zero sparse-solve count does not mean zero electrical or AD work. "
            "Shorter-protocol E counters come directly from per-arm terminal records: 19608 and 19578, "
            "whose sum matches the frozen 39186 aggregate; no aggregate was divided between seeds.\n\n" +
            markdown(["Separate stage", "Recorded scope and work"], [
                ["Shared parents", "Per protocol and seed: 2400 Adam + 600 full evaluations; charged once. F_cov reuses the shorter parents."],
                ["Shared calibration", "50 forward / 0 adjoint solves per parent; F_cov inherits the scales without recalibration."],
                ["Historical projected readout", "Original E/F: 278 forward solves per endpoint. Shorter: 1390 aggregate across four endpoints and one B_E. These are not totals for the two later common readers."],
                ["F_cov common readout", "278 forward solves per grid and seed, 556 per endpoint; no adjoint solve. Coarse/fine grids remain separate."],
                ["Discarded readout work", "F_cov seed 29: 0; seed 43: at most 1 in-flight solve. This is separate from completed work."],
            ]) +
            "\n\nHistorical E records contain `elapsed_seconds_internal`; F records lack matching time fields. "
            "F_cov records `current_session_seconds` (3710.590 and 3742.518 s), excluding separately logged "
            "profiles and readout. These fields do not establish a common timing boundary or an acceleration ratio. "
            "The original clean-confirmation environment and F_cov environment identify a Tesla V100-PCIE-32GB, "
            "Python 3.11.9, Torch 2.5.1+cu118, NumPy 2.1.1 and SciPy 1.14.1; F_cov records four CPU threads. "
            "A complete comparable historical hardware/thread/timing record is not asserted. "
            "Raw timing fields, termination, and direct sources are retained in "
            "[accuracy-work-full.csv](accuracy-work-full.csv); stage boundaries and provenance are in "
            "[accuracy-work-stages.csv](accuracy-work-stages.csv).\n")
    (TABLES / "accuracy-work.md").write_text(text, encoding="utf-8")
    return branches, stages


def main() -> None:
    TABLES.mkdir(exist_ok=True)
    FIGURES.mkdir(exist_ok=True)
    rows = select_effects()
    save_csv("interface-effects-full.csv", rows)
    effect_table(rows)
    figure(rows)
    branches, stages = costs()
    source_info = dict(
        status="VERIFIED_EXISTING_RECORD_DERIVATION", title=TITLE,
        selections="A: original/shorter x 29/43; B/C: shorter x 29/43; A-C spatial/fine; D: original/43/fine x old/refined/spatial",
        metric_rows=len(rows), paired_conditions=11,
        metric_names=list(METRICS), branch_cost_records=len(branches), separate_stage_records=len(stages),
        delta="control minus E; positive favors E",
        qualification="copied saved A/B; no metric subset re-adjudication",
        no_new_scoring=True, no_model_calls=True, no_solves=True,
        interpretation="configuration-level comparisons; mixed-measure coverage enhancement, no isolated VJP attribution",
        timing_comparison="not established; no wall-time speedup claim",
        inputs=SOURCES,
        validation=dict(unique_source_rows=True, saved_difference_consistency=True,
                        saved_relative_effect_consistency=True, original_qualification_copied=True,
                        shorter_direct_counters_match_aggregate=True),
    )
    (TABLES / "interface-evidence-sources.json").write_text(
        json.dumps(source_info, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": source_info["status"], "metric_rows": len(rows),
                      "branch_cost_records": len(branches), "separate_stage_records": len(stages)}))


if __name__ == "__main__":
    main()
