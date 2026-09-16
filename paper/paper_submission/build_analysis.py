"""Reorganize saved V28--V32 results for the submission manuscript.

This script reads CSV/JSON/NPZ evidence only. It does not import the scientific
model, load checkpoints, train networks, or solve an electrical/reference PDE.
Run from the repository root with the project Python environment.
"""
from pathlib import Path
import csv
import json
import shutil
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
V32 = ROOT / "paper/paper_v32"
TABLES = HERE / "tables"
FIGURES = HERE / "figures"
TABLES.mkdir(parents=True, exist_ok=True)
FIGURES.mkdir(parents=True, exist_ok=True)
COLORS = {"E": "#176B87", "F": "#D16A3A", "B": "#767B84", "D": "#6D8B50"}
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9,
                     "axes.spines.top": False, "axes.spines.right": False,
                     "axes.titleweight": "bold", "axes.titlesize": 10,
                     "savefig.dpi": 240, "pdf.fonttype": 42})
SOURCES = {}


def read_table(name, version="paper_v32"):
    path = ROOT / "paper" / version / "tables" / (name + ".csv")
    SOURCES[f"{version}/{name}"] = str(path.relative_to(ROOT)).replace("\\", "/")
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def number(row, key):
    return float(row[key])


def write_table(name, rows, columns=None):
    columns = columns or list(rows[0])
    with (TABLES / f"{name}.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows({k: r.get(k, "") for k in columns} for r in rows)
    def fmt(v):
        return f"{v:.9g}" if isinstance(v, (float, np.floating)) else str(v)
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    lines += ["| " + " | ".join(fmt(r.get(k, "")) for k in columns) + " |" for r in rows]
    (TABLES / f"{name}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def save(fig, name):
    fig.savefig(FIGURES / f"{name}.png", bbox_inches="tight", facecolor="white")
    fig.savefig(FIGURES / f"{name}.pdf", bbox_inches="tight", facecolor="white")
    plt.close(fig)


raw = read_table("cross-protocol-metrics")
rows = []
seen = set()
for r in raw:
    key = (r["protocol"], "baseline" if r["role"] == "B_E" else r["seed"], r["role"])
    if key in seen:
        existing = next(x for x in rows if (x["protocol"], x["seed"], x["role"]) == key)
        for k in ("S", "Ephi", "ET", "EV", "current_percent", "power_percent", "energy_percent"):
            assert number(existing, k) == number(r, k), (key, k)
        continue
    seen.add(key)
    out = dict(r)
    out["seed"] = key[1]
    rows.append(out)
rows.sort(key=lambda r: (r["protocol"] != "Original", r["seed"] == "baseline", r["seed"], r["role"]))
assert len(rows) == 10
write_table("unified-results", rows)

state_rows, device_rows = [], []
for r in rows:
    method = "B_E" if r["role"] == "B_E" else ("E" if r["role"] == "E/projected" else "F/projected")
    base = {"Case": "Original" if r["protocol"] == "Original" else "Earlier pulse", "Seed": "--" if r["seed"] == "baseline" else r["seed"], "Method": method}
    state_rows.append({**base, "S (x 10^-3)": number(r, "S") * 1000,
                       "Phase RMS": number(r, "Ephi"), "T RMS / 0.45 (%)": number(r, "ET") * 100,
                       "V RMS (x 10^-3)": number(r, "EV") * 1000})
    device_rows.append({**base, "Current NRMSE (%)": number(r, "current_percent"),
                        "Power NRMSE (%)": number(r, "power_percent"),
                        "Energy error (%)": number(r, "energy_percent")})
write_table("state-results", state_rows)
write_table("device-results", device_rows)

groups = [(p, s) for p in ("Original", "Shorter gap") for s in ("29", "43")]
metrics = ("S", "Ephi", "ET", "EV", "current_percent", "power_percent", "energy_percent")
effects = []
for p, s in groups:
    e = next(r for r in rows if r["protocol"] == p and r["seed"] == s and r["role"] == "E/projected")
    for comparator in ("F_raw/projected", "B_E"):
        f = next(r for r in rows if r["protocol"] == p and r["role"] == comparator and (r["seed"] == s or comparator == "B_E"))
        for m in metrics:
            ev, fv = number(e, m), number(f, m)
            effects.append({"protocol": p, "seed": s, "comparator": comparator, "metric": m,
                            "E": ev, "comparator_value": fv, "E_minus_comparator": ev - fv,
                            "relative_reduction_percent": 100 * (fv - ev) / fv,
                            "percentage_point_change": ev - fv if m.endswith("percent") else ""})
write_table("paired-effects", effects)

events = []
seen = set()
for r in read_table("complete-events"):
    q = dict(r)
    if q["role"] == "B_E":
        q["seed"] = "baseline"
    key = (q["protocol"], q["seed"], q["role"], q["cycle"])
    if key not in seen:
        seen.add(key)
        events.append(q)
assert len(events) == 20
write_table("complete-events", events)

latency = []
for seed, role in [(s, r) for s in ("29", "43") for r in ("E/projected", "F_raw/projected")] + [("baseline", "B_E")]:
    old = next(r for r in events if r["protocol"] == "Original" and r["seed"] == seed and r["role"] == role and r["cycle"] == "2")
    new = next(r for r in events if r["protocol"] == "Shorter gap" and r["seed"] == seed and r["role"] == role and r["cycle"] == "2")
    old_delay = number(old, "event_time") - 1.25
    new_delay = number(new, "event_time") - 1.01
    ref_old = number(old, "reference_event_time") - 1.25
    ref_new = number(new, "reference_event_time") - 1.01
    delta = old_delay - new_delay
    ref_delta = ref_old - ref_new
    latency.append({"seed": seed, "role": role, "original_latency": old_delay, "earlier_latency": new_delay,
                    "predicted_shortening": delta, "reference_shortening": ref_delta,
                    "absolute_shortening_error": abs(delta - ref_delta), "status": "report-only; no new selection or gate"})
write_table("latency-change-report-only", latency)
assert abs(latency[0]["reference_shortening"] - .0316) < 1e-12
assert latency[1]["absolute_shortening_error"] < latency[0]["absolute_shortening_error"]

hist = read_table("historical-mechanism-controls")
write_table("historical-controls", hist)
for name in ("reference-history", "prepulse-state", "per-pulse-power-energy", "second-cycle", "common-parents-and-calibration", "execution-budget", "new-protocol-adjudication", "new-protocol-all-readouts"):
    write_table(name, read_table(name))
write_table("original-clean-execution", read_table("clean-execution", "paper_v31"))
write_table("original-clean-adjudication", read_table("clean-adjudication", "paper_v31"))
remaining = [r for r in read_table("fixed-endpoints", "paper_v29") if r["role"] in ("D_C", "P1", "P_kappa")]
write_table("remaining-pde-controls", [{"Method": r["role"], "S": number(r, "S"),
    "Phase RMS": number(r, "Ephi"), "Current (%)": 100*number(r, "bottom_current_NRMSE"),
    "Power (%)": 100*number(r, "power_trace_NRMSE"), "Local q NRMSE (%)": 100*number(r, "local_joule_NRMSE")} for r in remaining])
event_quality, event_shape, event_masses = [], [], []
for r in events:
    identity = {"Case": "O" if r["protocol"] == "Original" else "S", "Seed": "--" if r["seed"] == "baseline" else r["seed"],
                "Method": "B_E" if r["role"] == "B_E" else ("E" if r["role"] == "E/projected" else "F"), "Cycle": r["cycle"]}
    event_quality.append({**identity, "Onset": number(r, "event_time"), "Onset error": number(r, "timing_absolute"),
        "Recall": number(r, "recall"), "Precision": number(r, "precision"), "Mass ratio": number(r, "mass_ratio")})
    event_shape.append({**identity, "Pre ROI": number(r, "pre_roi_fraction"), "Peak ROI": number(r, "peak_roi_fraction"),
        "Peak full": number(r, "peak_full_domain_fraction"), "Peak outside": number(r, "peak_outside_roi_fraction"), "Recovery": number(r, "recovery_fraction")})
    event_masses.append({**identity, "Reference mass": number(r, "teacher_active_target_mass"),
        "Predicted mass": number(r, "predicted_active_target_mass"), "Overlap mass": number(r, "true_positive_target_mass")})
write_table("event-quality", event_quality)
write_table("event-shape", event_shape)
write_table("event-masses", event_masses)
write_table("latency-summary", [{"Seed": r["seed"], "Method": r["role"].replace("F_raw/projected", "F").replace("E/projected", "E"),
    "Original latency": r["original_latency"], "Earlier latency": r["earlier_latency"],
    "Shortening": r["predicted_shortening"], "Absolute shift error": r["absolute_shortening_error"]} for r in latency])
write_table("history-summary", [{"State": r["field"], "Original mean": number(r, "original_ROI_mean"),
    "Earlier mean": number(r, "new_ROI_mean"), "Original maximum": number(r, "original_ROI_max"),
    "Earlier maximum": number(r, "new_ROI_max")} for r in read_table("reference-history")])
write_table("historical-summary", [{"Method": r["role"], "S": number(r, "S"), "Phase RMS": number(r, "Ephi"),
    "Current (%)": number(r, "current_percent"), "Power (%)": number(r, "power_percent"), "Energy (%)": number(r, "energy_percent")} for r in hist])
write_table("pulse-summary", [{"Role": r["role"], "Cycle": r["cycle"], "Power error (%)": 100*number(r, "power_NRMSE"),
    "Signed energy error": number(r, "signed_energy_error"), "Abs. signed integral": number(r, "absolute_signed_energy_error"),
    "Integral abs. power error": number(r, "integrated_absolute_power_error")} for r in read_table("per-pulse-power-energy")
    if "/network" not in r["role"]])
write_table("parent-summary", [{"Case": "O" if r["protocol"] == "Original" else "S", "Seed": r["seed"],
    "Visible V / 0.72 (%)": 100*number(r, "visible_V_RMS_over_072"), "Visible T / 0.45 (%)": 100*number(r, "visible_T_RMS_over_045"),
    "a": number(r, "a_s_c"), "b": number(r, "b_s_c")} for r in read_table("common-parents-and-calibration")])

# Figure 1: method definition. Every arrow represents an implemented interface.
fig, ax = plt.subplots(figsize=(10.4, 6.4))
ax.set(xlim=(0, 10.4), ylim=(0, 6.4)); ax.axis("off")
def box(x, y, w, h, text, color):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.10", fc=color, ec="#B8C3CD", lw=.8))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=9)
def arrow(a, b):
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle="-|>", mutation_scale=12, color="#506273", lw=1.1))
ax.text(.1, 6.15, "Sparse observations + known geometry, drive, constitutive laws and IC/BC", fontsize=12, weight="bold")
box(.15, 4.45, 2.6, 1.15, "Same fitted parent per case/seed\nT and phase neural fields\nconductivity from T and phase", "#F1F5F8")
box(3.3, 4.45, 3.05, 1.15, "E: training-time elimination\nA(σ)V* = f(U,σ)\ncomplete implicit derivative", "#DAEBF1")
box(7, 4.45, 3.05, 1.15, "F: soft electrical PINN\nV network + finite penalty\nrₑ = (AV − f) / cell volume", "#F7E9DF")
arrow((2.9, 5.05), (3.2, 5.05))
ax.plot([2.85, 3.00, 8.52, 8.52], [5.45, 5.88, 5.88, 5.81], color="#506273", lw=1.1)
arrow((8.52, 5.83), (8.52, 5.69))
box(3.3, 2.7, 6.75, 1.1, "Shared face network: half-resistance Joule deposition\nShared thermal cell balance + phase AD residual + observations + BC/IC\nFixed endpoints; complete active gradients; no reference-driven selection", "#F1F5F8")
arrow((4.8, 4.35), (4.8, 3.9)); arrow((8.5, 4.35), (8.5, 3.9))
box(.15, 2.7, 2.6, 1.1, "B_E: same sparse T/phase\nfixed interpolation\nno learned weights", "#EDEFF1")
box(.15, .95, 9.9, 1.0, "COMMON INFERENCE: freeze each T/phase state → same 160 × 80 electrical solve\nCompare phase, current, power, energy and events on one fixed numerical reference", "#E5EFE5")
arrow((1.45, 2.6), (1.45, 2.08)); arrow((6.65, 2.6), (6.65, 2.08))
ax.text(.15, .22, "Method-package comparison: initial V, active parameters, constraint times and gradient maps differ.\nThe design does not isolate the implicit derivative alone. T/phase and their events are unchanged by final projection.", fontsize=9)
save(fig, "fig01-method")

# Figure 2: same-state repair, followed by a common-projection comparison.
h = {r["role"]: r for r in hist}
fig, axes = plt.subplots(1, 3, figsize=(10.4, 3.5))
for ax, key, title in zip(axes[:2], ("current_percent", "power_percent"), ("(a) Current NRMSE (%)", "(b) Power NRMSE (%)")):
    for j, name in enumerate(("F_raw", "F_full")):
        vals = [number(h[name + "/" + m], key) for m in ("network", "projected")]
        ax.plot([0, 1], vals, "o-", color=(COLORS["F"] if j == 0 else "#8B5C90"), label=name.replace("_", " "))
        for x, y in zip([0, 1], vals):
            ax.annotate(f"{y:.3f}", (x, y), xytext=(5, 5 if j == 0 else -13), textcoords="offset points", fontsize=8)
    ax.set_yscale("log"); ax.set_xticks([0, 1], ["Network V", "Re-solved V"])
    ax.set_xlim(-.18, 1.48); ax.set_title(title); ax.grid(axis="y", alpha=.2)
axes[0].legend(frameon=False, fontsize=8)
names = ("P_E", "F_raw/projected", "F_full/projected")
axes[2].bar([0, 1, 2], [number(h[n], "power_percent") for n in names], color=[COLORS["E"], COLORS["F"], "#8B5C90"])
axes[2].set_xticks([0, 1, 2], ["E", "F raw\nprojected", "F full\nprojected"])
axes[2].set_title("(c) Common projection: power (%)")
axes[2].grid(axis="y", alpha=.2)
fig.tight_layout(); save(fig, "fig02-repair")

# Figure 3: development controls. These are not additional clean repetitions.
names = ("P_E", "D_E", "F_raw/projected", "F_bal/projected", "F_full/projected", "B_E")
labels = ("E", "D_E", "F raw", "F bal", "F full", "B_E")
fig, axes = plt.subplots(1, 3, figsize=(10.4, 3.6))
for ax, key, title in zip(axes, ("Ephi", "current_percent", "energy_percent"), ("(a) Raw phase RMS", "(b) Current NRMSE (%)", "(c) Integrated energy error (%)")):
    vals = [number(h[n], key) for n in names]
    colors = [COLORS["E"], COLORS["D"], COLORS["F"], "#E5A56E", "#8B5C90", COLORS["B"]]
    ax.bar(np.arange(6), vals, color=colors)
    ax.set_xticks(np.arange(6), labels, rotation=40, ha="right"); ax.set_title(title)
    ax.grid(axis="y", alpha=.2)
fig.tight_layout(); save(fig, "fig03-controls")

# Figure 4: individual clean pairs, with a baseline reused (not counted twice).
fig, axes = plt.subplots(2, 2, figsize=(10.4, 6.6))
xs = np.arange(4)
for ax, key, title in zip(axes.flat[:3], ("Ephi", "current_percent", "power_percent"), ("(a) Raw phase RMS", "(b) Current NRMSE (%)", "(c) Power NRMSE (%)")):
    for offset, name, label, color in ((-.18, "E/projected", "E", COLORS["E"]), (.18, "F_raw/projected", "F / projected", COLORS["F"])):
        vals = [number(next(r for r in rows if r["protocol"] == p and r["seed"] == s and r["role"] == name), key) for p, s in groups]
        ax.bar(xs + offset, vals, .34, color=color, label=label)
    for i, (p, s) in enumerate(groups):
        val = number(next(r for r in rows if r["protocol"] == p and r["role"] == "B_E"), key)
        ax.plot([i-.4, i+.4], [val, val], "--", color=COLORS["B"], lw=1.5, label="B_E (shared per case)" if i == 0 else None)
    ax.set_title(title); ax.set_xticks(xs, ["Orig. 29", "Orig. 43", "Earlier 29", "Earlier 43"]); ax.grid(axis="y", alpha=.2)
axes[0, 0].legend(frameon=False, fontsize=7, loc="lower right")
ax = axes[1, 1]
for offset, metric, color, label in ((-.15, "current_percent", COLORS["E"], "Current"), (.15, "power_percent", "#699EA7", "Power")):
    vals = [next(r["relative_reduction_percent"] for r in effects if r["protocol"] == p and r["seed"] == s and r["metric"] == metric and r["comparator"] == "F_raw/projected") for p, s in groups]
    ax.bar(xs + offset, vals, .28, color=color, label=label)
ax.set_title("(d) E reduction vs projected F (%)")
ax.set_xticks(xs, ["Orig. 29", "Orig. 43", "Earlier 29", "Earlier 43"])
ax.axhline(10, color="#59616A", ls=":", lw=1); ax.set_ylim(0, 90); ax.legend(frameon=False, fontsize=8)
ax.grid(axis="y", alpha=.2)
fig.tight_layout(); save(fig, "fig04-clean-pairs")

# Figure 5: pulse-history evidence and report-only latency/cancellation analysis.
refhistory = read_table("reference-history")
pulse = read_table("per-pulse-power-energy")
traces_path = V32 / "evidence/evaluation/traces.npz"
SOURCES["saved_traces"] = str(traces_path.relative_to(ROOT)).replace("\\", "/")
with np.load(traces_path, allow_pickle=False) as data:
    traces = {key: data[key] for key in data.files}
fig, axes = plt.subplots(2, 3, figsize=(10.4, 6.6))
for ax, key, title in zip(axes[0, :2], ("temperature", "phase"), ("(a) Reference pre-pulse mean T", "(b) Reference pre-pulse mean phase")):
    r = next(r for r in refhistory if r["field"] == key)
    ax.bar([0, 1], [number(r, "original_ROI_mean"), number(r, "new_ROI_mean")], color=["#A8BDC8", COLORS["E"]])
    ax.set_xticks([0, 1], ["Original", "Earlier pulse"]); ax.set_title(title); ax.grid(axis="y", alpha=.2)
ax = axes[0, 2]
ax.bar(range(5), [r["predicted_shortening"] for r in latency], color=[COLORS["E"], COLORS["F"], COLORS["E"], COLORS["F"], COLORS["B"]])
ax.axhline(.0316, color="black", ls="--", label="Reference: 0.0316")
ax.set_xticks(range(5), ["E29", "F29", "E43", "F43", "B_E"]); ax.set_title("(c) Second-event latency shortening")
ax.legend(frameon=False, fontsize=7); ax.set_ylim(0, .044); ax.grid(axis="y", alpha=.2)
time = traces["time"]
axes[1, 0].plot(time, traces["reference_power"], color="black", label="Reference")
for role, color, label in (("43/E/projected", COLORS["E"], "E, seed 43"), ("43/F_raw/projected", COLORS["F"], "F, seed 43")):
    power = traces[role + "__joule_power"]
    axes[1, 0].plot(time, power, color=color, ls="--", label=label)
    axes[1, 1].plot(time, power - traces["reference_power"], color=color, label=label)
axes[1, 0].set_title("(d) Earlier-pulse power trajectory")
axes[1, 0].legend(frameon=False, fontsize=7)
axes[1, 1].set_title("(e) Signed power error")
axes[1, 1].axhline(0, color="black", lw=.6)
for ax in axes[1, :2]:
    ax.set_xlabel("Dimensionless time"); ax.grid(alpha=.2)
    ax.axvline(1.01, color="#999999", ls=":", lw=.8)
ax = axes[1, 2]
for x, role, color in ((0, "43/E/projected", COLORS["E"]), (1, "43/F_raw/projected", COLORS["F"])):
    vals = [number(next(r for r in pulse if r["role"] == role and r["cycle"] == str(c)), "signed_energy_error") for c in (1, 2)]
    ax.bar([x-.16, x+.16], vals, .27, color=color, alpha=.9)
    ax.plot([x], [sum(vals)], "kd", markersize=5, label="Sum of signed pulse errors" if x == 0 else None)
ax.axhline(0, color="black", lw=.6); ax.set_xticks([0, 1], ["E43: pulse 1 / 2", "F43: pulse 1 / 2"])
ax.tick_params(axis="x", labelsize=7); ax.set_title("(f) Pulse-energy cancellation")
ax.legend(frameon=False, fontsize=6, loc="lower left"); ax.grid(axis="y", alpha=.2)
fig.tight_layout(); save(fig, "fig05-history")

# Figure 6: adverse results remain in the main text, not only the supplement.
fig, axes = plt.subplots(2, 2, figsize=(10.4, 6.4))
for ax, key, title, threshold in ((axes[0, 0], "recall", "(a) First-cycle recall", .9),
                                  (axes[0, 1], "timing_absolute", "(b) Second-cycle onset error", .005)):
    cycle = "1" if key == "recall" else "2"
    for offset, role, label, color in ((-.14, "E/projected", "E", COLORS["E"]), (.14, "F_raw/projected", "F / projected", COLORS["F"])):
        vals = [number(next(r for r in events if r["protocol"] == p and r["seed"] == s and r["role"] == role and r["cycle"] == cycle), key) for p, s in groups]
        ax.bar(xs + offset, vals, .26, color=color, label=label)
    ax.axhline(threshold, color="black", ls="--", lw=1)
    ax.set_xticks(xs, ["Orig. 29", "Orig. 43", "Earlier 29", "Earlier 43"]); ax.set_title(title)
    ax.grid(axis="y", alpha=.2)
axes[0, 0].set_ylim(.72, 1.0); axes[0, 0].legend(frameon=False, fontsize=8)
second = read_table("second-cycle")
ax = axes[1, 0]
for offset, role, color in ((-.15, "E/projected", COLORS["E"]), (.15, "F_raw/projected", COLORS["F"])):
    ax.bar(np.arange(2) + offset, [number(next(r for r in second if r["role"] == s+"/"+role), "tail_phase_ROI_RMS") for s in ("29", "43")], .28, color=color)
ax.set_xticks([0, 1], ["Earlier 29", "Earlier 43"]); ax.set_title("(c) Tail phase RMS: E is worse")
ax.grid(axis="y", alpha=.2)
ax = axes[1, 1]
for offset, role, color in ((-.15, "E/projected", COLORS["E"]), (.15, "F_raw/projected", COLORS["F"])):
    vals = [number(next(r for r in rows if r["protocol"] == p and r["seed"] == s and r["role"] == role), "energy_percent") for p, s in groups]
    ax.bar(xs + offset, vals, .28, color=color)
ax.set_xticks(xs, ["Orig. 29", "Orig. 43", "Earlier 29", "Earlier 43"])
ax.set_title("(d) Energy error (%): not uniform dominance"); ax.grid(axis="y", alpha=.2)
fig.tight_layout(); save(fig, "fig06-limits")

figures = {
    "fig01-method": ["implemented mathematical interfaces; see supplement source map"],
    "fig02-repair": [SOURCES["paper_v32/historical-mechanism-controls"]],
    "fig03-controls": [SOURCES["paper_v32/historical-mechanism-controls"]],
    "fig04-clean-pairs": [SOURCES["paper_v32/cross-protocol-metrics"]],
    "fig05-history": [SOURCES["paper_v32/reference-history"], SOURCES["paper_v32/complete-events"], SOURCES["paper_v32/per-pulse-power-energy"], SOURCES["saved_traces"]],
    "fig06-limits": [SOURCES["paper_v32/complete-events"], SOURCES["paper_v32/second-cycle"], SOURCES["paper_v32/cross-protocol-metrics"]],
}
audit = {"activity": "saved-result arithmetic and plotting only", "new_training": 0,
         "checkpoint_loads_or_model_evaluations": 0, "new_electrical_or_reference_solves": 0,
         "stress_access": False, "unique_main_rows": len(rows), "unique_event_rows": len(events),
         "clean_protocols": 2, "initialization_seeds": [29, 43], "main_figures": figures,
         "inputs": SOURCES, "latency_comparison_is_report_only": True,
         "F29_shortening_error_is_smaller_than_E29": True}
(HERE / "analysis-provenance.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
print(json.dumps({"main_rows": len(rows), "events": len(events), "figures": len(figures),
                  "latency_report_only": latency}, indent=2))
