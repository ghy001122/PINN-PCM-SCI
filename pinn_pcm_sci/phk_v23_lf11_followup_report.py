"""Render saved follow-up evidence and integrate paper_v25 without retraining."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import shutil

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .phk_v23_lf11 import ROOT, now, save_json
from .phk_v23_lf11_followup import RUN


COLORS = {"parent": "#64748b", "base": "#c28430", "fit": "#087f8c", "wave": "#8b4eab", "ref": "#1f2937"}


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def figures(root, paper):
    s0, s1 = read_json(root/"s0.json"), read_json(root/"s1/result.json")
    base = read_json(root/"s1/base_fit_metrics.json")["metrics"]
    result = read_json(root/"evaluation.json")
    records = result["records"]
    with np.load(root/"s0-visible.npz", allow_pickle=False) as f:
        visible = {k: f[k] for k in f.files}
    with np.load(root/"s1/fixed-visible.npz", allow_pickle=False) as f:
        final = f["fields"]
    with np.load(root/"evaluation-traces.npz", allow_pickle=False) as f:
        traces = {k: f[k] for k in f.files}
    time = traces["time"]
    q, target, weight = visible["coordinates"], visible["targets"], visible["weights"]
    st, sz, sx = np.unique(q[:, 2]), np.unique(q[:, 1]), np.unique(q[:, 0])
    shape = (len(st), len(sz), len(sx))
    w = weight.reshape(shape)
    spatial_mass = w.sum(axis=(1, 2))
    plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
                         "pdf.fonttype": 42, "ps.fonttype": 42})
    fig, axes = plt.subplots(3, 3, figsize=(15, 11), layout="constrained")
    states = [s0["parent_visible_metrics"], base, s1["metrics"]]
    labels = ["Parent", "Base fit", "Final fit"]
    for col, field, gate, title in ((0, "T", 2., "Visible temperature fit"), (1, "V", .5, "Visible voltage fit")):
        ax = axes[0, col]
        values = [100*(d["T_normalized_rms"]["all"] if field == "T" else d["V_normalized_rms"]) for d in states]
        ax.bar(labels, values, color=[COLORS["parent"], COLORS["base"], COLORS["fit"]])
        for x, value in enumerate(values):
            label_y = gate+1.0 if field == "T" and value < gate else value
            ax.annotate(f"{value:.3f}%", (x, label_y), xytext=(0, 4), textcoords="offset points", ha="center")
        ax.axhline(gate, color="#b91c1c", ls="--", lw=1, label=f"Admission: {gate:g}%")
        ax.set_ylim(0, max(values)*1.23)
        ax.set_ylabel(f"RMS / {'.45' if field == 'T' else '.72'} (%)")
        ax.set_title(title)
        ax.legend(loc="upper right", fontsize=8)
    ax = axes[0, 2]
    for values, label, color in ((visible["parent_fields"][:, 1]-target[:, 1], "Parent", COLORS["parent"]),
                                  (final[:, 1]-target[:, 1], "Final fit", COLORS["fit"]),
                                  (visible["interval_distance"], "Pointwise lower bound", "#b91c1c")):
        curve = np.sqrt(np.sum(w*values.reshape(shape)**2, axis=(1, 2))/spatial_mass)/.45
        ax.plot(st, 100*curve, label=label, color=color)
    ax.set(title="Temperature error across both pulses", xlabel="Time", ylabel="Spatial weighted RMS / .45 (%)")
    ax.legend(fontsize=8)
    ax = axes[1, 0]
    roles = ["warm_start", "S1_fixed_fit", "B_logit_waveform", "P_U"]
    names = ["Parent", "Final fit", "B-wave", "LF11 P-U"]
    positions = np.arange(len(roles))
    for offset, metric, color in ((-.18, "S", COLORS["fit"]), (.18, "Ephi", COLORS["wave"])):
        values = [records[r]["metrics"][metric]/records["warm_start"]["metrics"][metric] for r in roles]
        ax.bar(positions+offset, values, width=.36, color=color, label=metric)
    ax.set(xticks=positions, xticklabels=names, ylabel="Error / original parent error", title="Phase metrics: unchanged by S1")
    ax.axhline(1, color="#94a3b8", lw=.8)
    ax.legend(fontsize=8)
    ax = axes[1, 1]
    for role, label, color, ls in (("native_reference_readout_check", "Reference", COLORS["ref"], "-"),
                                  ("S1_fixed_fit", "Final fit = parent", COLORS["fit"], "--"),
                                  ("B_logit_waveform", "B-wave", COLORS["wave"], "-"),
                                  ("P_U", "LF11 P-U", "#b1b8c4", ":")):
        ax.plot(time, traces[role+"__roi_active_fraction"], label=label, color=color, ls=ls)
    ax.set(title="Complete-cycle event support", xlabel="Time", ylabel="Active ROI fraction")
    ax.legend(fontsize=8)
    ax = axes[1, 2]
    for shift, role, label, color in ((-.2, "S1_fixed_fit", "Final fit", COLORS["fit"]),
                                     (.2, "B_logit_waveform", "B-wave", COLORS["wave"])):
        values = [records[role]["metrics"][key]/records["warm_start"]["metrics"][key] for key in ("ET", "EI", "energy_error")]
        ax.bar(np.arange(3)+shift, values, width=.4, label=label, color=color)
    ax.set(xticks=np.arange(3), xticklabels=["Temperature", "Top current", "Energy"],
           yscale="log", ylabel="Error / original parent error", title="Device effects of fitting")
    ax.axhline(1, color="#94a3b8", lw=.8)
    ax.legend(fontsize=8)
    ax = axes[2, 0]
    ax.plot(time, traces["reference_current"], color=COLORS["ref"], label="Reference")
    ax.plot(time, traces["S1_fixed_fit__top_current"], color=COLORS["fit"], label="Final top")
    ax.plot(time, traces["S1_fixed_fit__bottom_current"], color=COLORS["fit"], ls="--", label="Final bottom")
    ax.plot(time, traces["B_logit_waveform__top_current"], color=COLORS["wave"], lw=1, label="B-wave top")
    ax.set(title="Two independent electrode currents", xlabel="Time", ylabel="Current")
    ax.legend(fontsize=8)
    ax = axes[2, 1]
    ax.plot(time, traces["reference_power"], color=COLORS["ref"], label="Reference")
    ax.plot(time, traces["S1_fixed_fit__joule_power"], color=COLORS["fit"], label="Final Joule")
    ax.plot(time, traces["S1_fixed_fit__input_power"], color=COLORS["fit"], ls="--", label="Final input")
    ax.plot(time, traces["B_logit_waveform__joule_power"], color=COLORS["wave"], lw=1, label="B-wave Joule")
    ax.set(title="Input power and field dissipation", xlabel="Time", ylabel="Power")
    ax.legend(fontsize=8)
    ax = axes[2, 2]
    for role, label, color in (("warm_start", "Parent", COLORS["parent"]),
                              ("S1_fixed_fit", "Final fit", COLORS["fit"]),
                              ("P_U", "LF11 P-U", "#c28430"),
                              ("B_logit_waveform", "B-wave", COLORS["wave"])):
        ax.plot(time, traces[role+"__power_defect"], label=label, color=color)
    ax.axhline(0, color="#94a3b8", lw=.8)
    ax.set(title="Power defect is retained", xlabel="Time", ylabel="$P_J-U I_{top}$")
    ax.legend(fontsize=8)
    for i, ax in enumerate(axes.ravel()):
        ax.text(-.12, 1.06, chr(97+i), transform=ax.transAxes, weight="bold", size=12)
    fig.suptitle("Sparse fitting repairs temperature; voltage admission remains unmet\nS1 is observation-only development. LF11 P-U is historical; new PDE branches were not run.", fontsize=13)
    directory = paper/"figures"
    directory.mkdir(parents=True, exist_ok=True)
    for extension in ("png", "pdf"):
        fig.savefig(directory/f"lf11-followup-main.{extension}", dpi=180)
    plt.close(fig)
    fig, axes = plt.subplots(2, 3, figsize=(14, 8), layout="constrained")
    ti = int(np.argmin(abs(st-.28)))
    panels = [(target[:, 1].reshape(shape)[ti], "Visible temperature at t=0.28", "magma"),
              (visible["envelope"].reshape(shape)[ti], "Upper output envelope at t=0.28", "magma"),
              (visible["interval_distance"].reshape(shape)[ti], "Unavoidable pointwise distance", "magma")]
    for ax, (value, title, cmap) in zip(axes[0], panels):
        im = ax.pcolormesh(sx, sz, value, shading="nearest", cmap=cmap)
        fig.colorbar(im, ax=ax, shrink=.8)
        ax.set(title=title, xlabel="x", ylabel="z")
    voltage_maps = [np.sqrt(np.sum(w*(values[:, 0]-target[:, 0]).reshape(shape)**2, axis=0)/w.sum(axis=0))/.72
                    for values in (visible["parent_fields"], final)]
    voltage_vmax = max(float(value.max()) for value in voltage_maps)
    for ax, values, title in ((axes[1, 0], visible["parent_fields"], "Parent visible voltage RMS / .72"),
                              (axes[1, 1], final, "Final visible voltage RMS / .72")):
        err = (values[:, 0]-target[:, 0]).reshape(shape)
        spatial = np.sqrt(np.sum(w*err**2, axis=0)/w.sum(axis=0))/.72
        im = ax.pcolormesh(sx, sz, spatial, shading="nearest", cmap="viridis", vmin=0,
                           vmax=voltage_vmax)
        fig.colorbar(im, ax=ax, shrink=.8)
        ax.set(title=title, xlabel="x", ylabel="z")
    loc = result["visible_error_localization"]["by_z"]
    axes[1, 2].barh([v["z"] for v in loc], [100*v["V_squared_error_fraction"] for v in loc],
                    height=.06, color=COLORS["fit"])
    axes[1, 2].set(title="Remaining voltage-error distribution", xlabel="Share of weighted squared V error (%)", ylabel="Visible z level")
    fig.suptitle("Representation lower bound and visible-error localization\n343 observations exceed the T envelope; their global lower bound is below the admission target.", fontsize=12)
    for extension in ("png", "pdf"):
        fig.savefig(directory/f"lf11-followup-localization.{extension}", dpi=180)
    plt.close(fig)


def markdown_table(headers, rows):
    return "\n".join(["| "+" | ".join(headers)+" |", "|"+"---|"*len(headers),
                      *["| "+" | ".join(str(v) for v in row)+" |" for row in rows]])


def write_paper(root, paper):
    s0, s1 = read_json(root/"s0.json"), read_json(root/"s1/result.json")
    base = read_json(root/"s1/base_fit_metrics.json")["metrics"]
    evaluation = read_json(root/"evaluation.json")
    records = evaluation["records"]
    parent, fit = s0["parent_visible_metrics"], s1["metrics"]
    old = ROOT/"paper/paper_v24"
    for path in (old/"figures").iterdir():
        if path.suffix in (".png", ".pdf"):
            shutil.copy2(path, paper/"figures"/path.name)
    tables = paper/"tables"
    tables.mkdir(exist_ok=True)
    roles = ["warm_start", "S1_fixed_fit", "B_logit_waveform", "D_B", "P_U", "P_I", "P_M", "B_L", "B_P", "B_logit", "dense_LF_ONLY", "native_reference_readout_check"]
    keys = ["S", "Ephi", "ET", "EV", "EI", "energy_error", "power_trace_NRMSE", "input_power_NRMSE", "bottom_current_NRMSE", "current_balance_rms", "power_defect_rms", "electric_fv_rms"]
    with (tables/"endpoint-metrics.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["role", "identity", *keys, "strict_device_pass"])
        for role in roles:
            identity = "NEW_S1_OBSERVATION_ONLY_FIXED_ENDPOINT" if role == "S1_fixed_fit" else "REUSED_LF11_EVIDENCE"
            writer.writerow([role, identity, *[records[role]["metrics"][key] for key in keys], records[role]["strict_device_pass"]])
    short_roles = ["warm_start", "S1_fixed_fit", "B_logit_waveform", "D_B", "P_U", "dense_LF_ONLY"]
    labels = {"warm_start": "Original parent", "S1_fixed_fit": "S1 fixed fit (new)", "D_B": "LF11 D_B (historical)", "P_U": "LF11 P_U (historical)", "B_logit_waveform": "B_logit_waveform", "dense_LF_ONLY": "Dense LF_ONLY (more information)"}
    primary = markdown_table(["Endpoint / baseline", "S", "Raw Ephi", "ET / .45", "Raw EV", "Current NRMSE", "Energy error"],
        [[labels[role], *[f"{records[role]['metrics'][key]:.9g}" for key in ("S", "Ephi", "ET", "EV", "EI", "energy_error")]] for role in short_roles])
    device = markdown_table(["Endpoint / baseline", "Power NRMSE", "Bottom-current NRMSE", "Current-balance RMS", "Power-defect RMS"],
        [[labels[role], *[f"{records[role]['metrics'][key]:.9g}" for key in ("power_trace_NRMSE", "bottom_current_NRMSE", "current_balance_rms", "power_defect_rms")]] for role in short_roles])
    visible = markdown_table(["Metric", "Original parent", "Base optimization", "Final fit", "Admission"], [
        ["T RMS / .45 (all)", f"{parent['T_normalized_rms']['all']:.9f}", f"{base['T_normalized_rms']['all']:.9f}", f"{fit['T_normalized_rms']['all']:.9f}", "<=0.02; PASS"],
        ["T RMS / .45 (heating)", f"{parent['T_normalized_rms']['heating']:.9f}", f"{base['T_normalized_rms']['heating']:.9f}", f"{fit['T_normalized_rms']['heating']:.9f}", "<=0.05; PASS"],
        ["T RMS / .45 (off)", f"{parent['T_normalized_rms']['off']:.9f}", f"{base['T_normalized_rms']['off']:.9f}", f"{fit['T_normalized_rms']['off']:.9f}", "<=0.05; PASS"],
        ["V RMS / .72", f"{parent['V_normalized_rms']:.9f}", f"{base['V_normalized_rms']:.9f}", f"{fit['V_normalized_rms']:.9f}", "<=0.005; FAIL"],
        ["Visible phase RMS", f"{parent['phase_raw_visible_rms']:.9f}", f"{base['phase_raw_visible_rms']:.9f}", f"{fit['phase_raw_visible_rms']:.9f}", "<=1.05 x parent; PASS"],
        ["Full phase-logit objective", f"{parent['phase_logit_objective']:.12f}", f"{base['phase_logit_objective']:.12f}", f"{fit['phase_logit_objective']:.12f}", "<=1.05 x parent; PASS"],
    ])
    (tables/"fit-admission.md").write_text(visible+"\n\nThese are training/development errors, not held-out validation. Base-to-final improvement includes further optimization and the single adapter; it is not an isolated adapter ablation.\n", encoding="utf-8")
    (tables/"fixed-endpoints.md").write_text(primary+"\n\nOnly S1 fixed fit is new. No new D_B/P_U/N/G/D_N endpoints exist. All errors are fractions, not percentages.\n\n"+device+"\n", encoding="utf-8")
    events = markdown_table(["Endpoint", "Recall C1 / C2", "Precision C1 / C2", "Timing error C1 / C2", "Strict"],
        [[labels[role], *[" / ".join("None" if c[key] is None else f"{c[key]:.8g}" for c in records[role]["cycles"]) for key in ("recall", "precision", "timing_absolute")], str(records[role]["strict_device_pass"])] for role in short_roles])
    (tables/"events.md").write_text(events+"\n", encoding="utf-8")
    manuscript = (old/"manuscript.md").read_text(encoding="utf-8")
    manuscript = manuscript.replace(manuscript.splitlines()[0], "# Separating representation feasibility, sparse fitting, and physical increments in electrothermal phase-change PINNs", 1)
    a, b = manuscript.index("## Abstract"), manuscript.index("## 1. Introduction")
    abstract = """## Abstract

Sparse electrothermal phase-change reconstruction requires separating function representation, optimization, interior physics, and device readout. An initial matched four-arm experiment finds no declared joint phase improvement from interior PDEs, importance-corrected interface sampling, or a calibrated phase-residual measure. Uniform physics reduces an independent residual objective by 80.37% while worsening phase-set and phase RMS errors by 40.68% and 17.74%. A subsequent sparse-only development experiment tests whether the poor neural temperature fit is forced by its bounded output transform. The exact pointwise interval-distance lower bound is 0.1504% in normalized visible RMS, below the 2% fitting criterion. Within 1200 Adam updates and 400 complete weighted objective/gradient evaluations, optimization with one smooth temperature-latent adapter reduces visible temperature error from 17.82% to 1.14%, with unchanged phase predictions. On the fixed nominal reference grid, ROI temperature error decreases from 28.22% to 1.75% and Joule-energy error from 106.74% to 49.20%. However, visible voltage error remains 0.8215%, exceeding the 0.5% admission threshold, so the new interior-PDE and electrical-normalization comparisons are not run. Independent bottom-current readout exposes remaining large electrical defects despite a 7.22% top-current NRMSE. The results establish a repairable temperature-fitting gap and narrow the remaining voltage problem, without attributing an independent benefit to the adapter or claiming a superior PINN method. Evidence concerns one synthetic geometry, one initialization, and a previously inspected nominal numerical reference.

"""
    manuscript = manuscript[:a]+abstract+manuscript[b:]
    introduction = """
The follow-up adds a second, logically separate question: is the poor fit already visible in the allowed observations caused by an unavoidable output envelope, or can bounded optimization substantially repair it? The original parent has previously seen every sparse observation. Reusing it therefore supports training/development attribution only; deleting time slices afterward would not create unseen validation. We first derive a pointwise representation lower bound, then perform bounded observation-only fitting before allowing any new interior-physics comparison.

![Sparse fitting and device consequences](figures/lf11-followup-main.png)

*Figure 1. The new fixed S1 fitting endpoint, its original parent, and the same-observation waveform baseline. Upper panels use complete visible observations; lower panels use the unchanged full nominal reference grid and independent face-flux readout. The displayed LF11 P_U is historical, not a new branch. Phase predictions remain identical during S1. Temperature repair alone neither establishes a matched PINN increment nor removes electrical dissipation defects.*

"""
    manuscript = manuscript.replace("## 2. Physical and numerical setting", introduction+"## 2. Physical and numerical setting", 1)
    manuscript = manuscript.replace("All neural arms use three independent modified-MLP", "All neural arms in the original four-arm experiment use three independent modified-MLP", 1)
    methods = r"""### 3.6 Representation feasibility and bounded sparse fitting

The follow-up preserves the nominal equations, coefficients, boundary conditions, observation mask, and original sparse parent. The actual temperature transform is

\[
T_\vartheta=A(x,z,t)\operatorname{sigmoid}h_T,\qquad
A=2.5(1-e^{-t/0.35})(1-z).
\]

For visible targets \(y_i\), define \(d_i=\max(-y_i,0)+\max(y_i-A_i,0)\). Every admissible prediction satisfies \(|T_{\vartheta,i}-y_i|\ge d_i\). Thus, for nonnegative observation weights,

\[
\frac{\sqrt{\sum_i w_i(T_{\vartheta,i}-y_i)^2/\sum_iw_i}}{0.45}
\ge\frac{\sqrt{\sum_iw_id_i^2/\sum_iw_i}}{0.45}.
\]

This is a lower bound over the pointwise closed interval, not a finite-network realizability guarantee. A finite sigmoid may only approach an interval endpoint. The projection used to calculate the bound never replaces a target or becomes a reported model. Initial-time and top-boundary zero envelopes are handled without division. Heating means positive known voltage and positive time; off means zero voltage at positive time. Both use conditional versions of the original global observation measure.

The fitted-parent criteria are visible normalized temperature RMS at most 0.02 globally and 0.05 in each heating/off stratum; normalized visible voltage RMS at most 0.005; and no more than 5% degradation in either raw visible phase RMS or the inherited full-logit observation objective. These new fitting criteria do not retroactively invalidate LF11 and are distinct from its strict device criteria.

We first use 600 Adam updates on the independent potential/temperature observation components, followed by 80 and 120 complete fixed-objective L-BFGS evaluations for the respective heads. Phase weights remain exactly unchanged during this separable observation-only stage. If admission is not achieved, the remaining development allowance permits one smooth additive temperature-latent adapter, 600 further Adam updates, and the remainder of the cumulative 400 fixed evaluations. The actual second allocation is 40 potential and 160 temperature evaluations. Adam uses learning rate 0.001, betas (0.9,0.999), epsilon 1e-8, global-measure batches of 1024, and clipping norm 10. All fitting runs use FP64 on CPU.

Adam plus L-BFGS is an established optimization choice, not a new method claim [@rathore2024loss]. L-BFGS sees fixed complete weighted observation components, accumulated in chunks as the true sum; each head contributes its original one-third factor. No resampling, adaptive weights, or gradient clipping occurs inside a closure. Every objective/gradient call, including repeated starts and line-search trials, consumes the explicit evaluation budget. Each accepted step must satisfy the Wolfe checks. Budget exhaustion during a trial restores both parameters and optimizer state to the last accepted step; a trial is never saved as the endpoint. Actual Adam moments are not used to reinterpret an L-BFGS endpoint.

The optional adapter adds a width-32, two-layer modified MLP to the existing temperature latent, using normalized raw coordinates and axis-aligned sine/cosine features. Frequencies are x=(0.5,1,2), z=(0.5,1), t=(0.5,1,2,4). Its final layer is initialized to zero, preserving the insertion-time function exactly. The complete temperature envelope remains unchanged. This is a deterministic, low-bandwidth adaptation inspired by Fourier-feature networks [@tancik2020fourier], rather than a reproduction of their random feature selection or an original feature-encoding claim. It adds 3201 parameters to the original 39939. Additional optimization and insertion are sequential development choices, so their separate causal benefits are not identified.

Only a fully admitted parent would branch into the new matched D_B/P_U experiment. The sole later electrical-block normalization would replace both the interior residual and homogeneous insulating flux, preserve complete parameter coupling, and require the prescribed R/N/G and conditional D_N controls. Neither the withdrawn fourth-power electrode lift nor any such physical branch is executed when fitting admission fails. The strong B_logit_waveform rules are supplied in the follow-up instruction and retained unchanged; their original LF11 status remains posthoc.

"""
    manuscript = manuscript.replace("## 4. Evaluation and decision rules", methods+"## 4. Evaluation and decision rules", 1)
    for n in range(5, 0, -1):
        manuscript = manuscript.replace(f"*Figure {n}. ", f"*Figure {n+1}. ")
    # The inserted new leading figure is Figure 1, not part of the old sequence.
    manuscript = manuscript.replace("*Figure 2. The new fixed S1", "*Figure 1. The new fixed S1")
    localized = sum(row["V_squared_error_fraction"] for row in evaluation["visible_error_localization"]["by_z"][:2])
    new_results = f"""### 5.6 A small envelope floor and a large, repairable fitting gap

**Evidence status: VERIFIED.** Of 29,106 visible positions, 343 lie outside the temperature envelope; all occur in heating strata. The largest excess is 0.0221523 at (x,z,t)=(0.0125,0.9125,0.28). The global normalized RMS lower bound is 0.0015038294; its heating counterpart is 0.0028834613 and its off counterpart is zero. The independently written analytic envelope agrees with the actual model expression to 4.44e-16. These values cannot explain the original visible temperature error of 0.178232659: the output interval does not preclude the declared 0.02 admission target, although exact fitting of every observation is impossible.

{visible}

*Table 7. Complete weighted visible errors. The intermediate base fit uses the original structure; the final endpoint includes the one permitted temperature adapter and further optimization. These are exposed training/development observations, not a holdout.*

The final visible temperature error decreases by 93.62%, and visible voltage error by 47.58%, relative to the original sparse parent. All three temperature requirements and both phase-preservation requirements pass. Voltage remains at 0.0082151003 versus 0.005, the only failed fitting requirement. The final full visible metrics are exactly repeatable. The run uses precisely 1200 Adam updates and 400 full weighted objective/gradient evaluations. Its four L-BFGS stages accept 38, 59, 19, and 78 steps; two budget-truncated line searches are rolled back to their last accepted states. There is no additional training after nominal reference evaluation.

![Temperature representation and voltage localization](figures/lf11-followup-localization.png)

*Figure 7. A pointwise temperature-envelope bound and spatial localization of visible voltage errors. Voltage heatmaps use the same full color scale. The two lowest visible z levels contain {100*localized:.2f}% of final weighted voltage squared error and 16.25% of the observation measure. This localization is posthoc analysis of visible data, not an extra training mask or proof of a unique boundary mechanism.*

**SUPPORTED_INTERPRETATION:** a substantial part of the former temperature deficit was repairable without changing the physical object, adding observations, or applying interior PDEs. This excludes the unchanged envelope as a sufficient explanation for the large former error. It does not distinguish the effects of more optimization and the adapter, prove global optimization, or establish the cause of the remaining voltage deficit. The largest residual visible voltage error is 0.0727930 at (-0.3875,0.1125,1.52), near the heater region.

### 5.7 Temperature repair does not complete phase or device reconstruction

**Evidence status: VERIFIED.** The fixed S1 endpoint is evaluated once on the same 160-by-80-by-1001 nominal reference grid after the training process exits. Original LF11 endpoints and direct baselines are reused as labeled historical evidence; their reference axes and native current/power traces are checked for equality. Additional power and bottom-current summaries are calculated from the already saved field-based readouts, not copied into any prediction.

{primary}

*Table 8. The fixed S1 endpoint and strong references. The two LF11 physical-comparison rows are historical; they are not the unexecuted new D_B/P_U branches. Temperature is normalized by 0.45; potential RMS remains raw, whereas visible voltage admission uses division by 0.72.*

ROI temperature error decreases from 28.22% to 1.75%; Joule-energy error decreases from 106.74% to 49.20%. Top-current NRMSE decreases from 8.04% to 7.22%, while power-trace NRMSE remains 57.61%. The unchanged phase head gives the same S and raw phase RMS as the original parent, with recalls 0.80475/0.82184 and absolute timing errors 0.03788/0.00215. Strict device accuracy is not achieved. The waveform baseline remains substantially better in voltage, current, energy, and raw phase error, although its S is larger than the parent's. A single favorable phase-set metric therefore does not establish a joint advantage.

{device}

*Table 9. Independent device diagnostics. Power-trace NRMSE is normalized by native Joule-power RMS; bottom-current NRMSE uses native terminal-current RMS. Values are ratios, not percentages. Near-zero denominators instead require absolute RMS. Current/power defects are kept as absolute quantities.*

A particularly strong counterexample remains: the final top-current NRMSE is 0.07218, but bottom-current NRMSE is 7.81254 and current-balance RMS is 4.05841. Even B_logit_waveform has bottom-current NRMSE 0.60787 despite top-current NRMSE 0.00428. These values show why a single terminal trace cannot certify electrical consistency. In the discrete face network, with node current defect d, sum(d)=I_bottom-I_top and P_J-U I_top=V^T d. The reported defects are related consistency diagnostics, not independent discoveries or continuum-convergence evidence.

**Execution disposition:** the new D_B/P_U and R/N/G/D_N branches are NOT_RUN_S1_VOLTAGE_FIT_ADMISSION_NOT_MET. No electrical-normalization effect, new physics increment, or boundary-subterm causal attribution is estimated. These unrun methods are neither failed numerical runs nor evidence against their potential value.

"""
    manuscript = manuscript.replace("## 6. Discussion", new_results+"## 6. Discussion", 1)
    manuscript = manuscript.replace("## 7. Conclusion", """### 6.4 What has been ruled out, and what remains

The follow-up rules out the temperature output interval as an explanation sufficient to account for the former large visible temperature error, and demonstrates a substantial bounded fitting repair. It does not rule out an optimization or finite-capacity voltage limitation, identify a conductivity-amplitude shortcut, or test electrical-block normalization. The failed voltage prerequisite prevents a new fair PDE comparison on the intended fitted parent. In the earlier local diagnostic, the boundary quantity aggregates several distinct conditions; a heater Dirichlet residual has no direct phase-head gradient under independent heads. Electric/boundary local harmful components also do not imply a harmful total update or a historical cause. These limitations prevent replacing the missing matched experiment with a gradient-based narrative.

The next proposed action is a voltage-head-only bounded fitting study from the retained final S1 state, preserving the now-admitted temperature and phase functions and the original sparse information. It should first use the unchanged full weighted observation objective and an explicit evaluation cap. Reaching voltage admission would permit the already specified matched physics question to become meaningful; changing a boundary representation or normalizing an electrical block requires its own evidence and authorization. Independent initializations, a second observation rule, and a complete new case remain a subsequent confirmation design, not completed evidence.

## 7. Conclusion""", 1)
    start, end = manuscript.index("## 7. Conclusion"), manuscript.index("## Data and code availability")
    manuscript = manuscript[:start]+"""## 7. Conclusion

The original matched sparse experiment does not establish independent gains from interior physics, importance-corrected interface sampling, or the calibrated phase measure. The follow-up makes a different, positive but limited advance: it quantitatively separates an output-interval lower bound from a repairable visible temperature-fitting deficit. Bounded sparse-only fitting repairs temperature on both observed coordinates and the fixed nominal reference grid while leaving phase unchanged. Voltage admission and device consistency remain unresolved, and the waveform-aware direct baseline remains strong. Because voltage fitting fails its declared prerequisite, the new PDE and electrical-normalization comparisons are not run. The resulting contribution is an evidence-supported refinement of the research mechanism and a reusable improved fitting state, not a new superior PINN solver or an independently confirmed material-device prediction.

"""+manuscript[end:]
    manuscript = manuscript[:manuscript.index("## Data and code availability")]+"""## Data and code availability

The repository is https://github.com/ghy001122/PINN-PCM-SCI. The inherited LF11 release is 6412dbf3c766207dfb5f586a94bac8eaa0f247d5; this follow-up is distributed with paper_v25 and identified by its containing Git commit. The [reproduction guide](reproducibility.md), [selected evidence](evidence/README.md), and [claim matrix](claim_evidence_matrix.md) identify the new fixed fitting state, actual per-stage optimizer states, budgets, telemetry, and saved evaluation. The old paper_v24 is preserved. The original sparse observations and historical evidence are reused from its evidence directory. Full prediction carriers and the named nominal reference remain local. No new observations, stress references, or experimental material data were used.
"""
    (paper/"manuscript.md").write_text(manuscript, encoding="utf-8")
    bib = (old/"references.bib").read_text(encoding="utf-8")+r"""

@inproceedings{rathore2024loss,
  title={Challenges in Training PINNs: A Loss Landscape Perspective},
  author={Rathore, Pratik and Lei, Weimu and Frangella, Zachary and Lu, Lu and Udell, Madeleine},
  booktitle={Proceedings of the 41st International Conference on Machine Learning},
  series={Proceedings of Machine Learning Research}, volume={235},
  pages={42159--42191}, year={2024},
  url={https://proceedings.mlr.press/v235/rathore24a.html}
}
@inproceedings{tancik2020fourier,
  title={Fourier Features Let Networks Learn High Frequency Functions in Low Dimensional Domains},
  author={Tancik, Matthew and Srinivasan, Pratul P. and Mildenhall, Ben and Fridovich-Keil, Sara and Raghavan, Nithin and Singhal, Utkarsh and Ramamoorthi, Ravi and Barron, Jonathan T. and Ng, Ren},
  booktitle={Advances in Neural Information Processing Systems}, year={2020},
  url={https://arxiv.org/abs/2006.10739}
}
"""
    (paper/"references.bib").write_text(bib, encoding="utf-8")
    return {"visible_table": visible, "primary_table": primary, "device_table": device, "events": events}


def delivery_documents(root, paper, result_tables):
    evidence = paper/"evidence"
    evidence.mkdir(exist_ok=True)
    selected = {
        "frozen-contract.json": "frozen_contract.json", "s0.json": "s0.json",
        "fit-plan.json": "s1/frozen_fit_plan.json", "base-fit-metrics.json": "s1/base_fit_metrics.json",
        "s1-result.json": "s1/result.json", "fit-telemetry.jsonl": "s1/telemetry.jsonl",
        "adapter-insertion.json": "s1/adapter-insertion.json", "fixed-fit-endpoint.pt": "s1/fixed_fit_endpoint.pt",
        "fixed-visible.npz": "s1/fixed-visible.npz", "s0-visible.npz": "s0-visible.npz",
        "evaluation.json": "evaluation.json", "evaluation-traces.npz": "evaluation-traces.npz",
        "evaluation-contract.json": "evaluation_contract.json", "compute-closure.json": "compute-closure.json",
        "execution-environment.json": "execution-environment.json",
        "visible-error-localization.json": "visible-error-localization.json",
        "training-source-identity.json": "training-source-identity.json",
    }
    for name in ("base_adam.pt", "base_lbfgs_V.pt", "base_lbfgs_T.pt",
                 "refinement_adam.pt", "refinement_lbfgs_V.pt", "refinement_lbfgs_T.pt"):
        selected["optimizer-states/"+name] = "s1/"+name
    for target, source in selected.items():
        (evidence/target).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(root/source, evidence/target)
    (evidence/"README.md").write_text("""# paper_v25 evidence

These are selected copies from the completed local follow-up. Original run root:
`outputs/runs/20260911-lf11-followup-fit-electric-block`.

The sparse observations and original parent are unchanged, available in
[paper_v24 input](../../paper_v24/evidence/input/sparse.npz) and
[paper_v24 parent](../../paper_v24/evidence/formal/warm_start/checkpoint.pt).
The new [fixed fitted state](fixed-fit-endpoint.pt) includes the adapter identity;
load it through `fit_model` in the follow-up fitting module.

[S0](s0.json) proves the visible interval-distance lower bound;
[S1](s1-result.json) records the actual fitting criteria, accepted endpoint,
evaluation counts and stop reason; [evaluation](evaluation.json) contains the
new endpoint and clearly labeled reused LF11 records. Every readout is based on
its own predicted fields. New scalar summaries of saved old traces do not imply
retraining or rerunning old methods.

The [optimizer states](optimizer-states/) include both base/refinement Adam
checkpoints and all four L-BFGS stage checkpoints. These are copies of the
actual accepted states, with their optimizer history. The original local run
is retained. Full-grid predictions and the archived nominal reference remain
local and are not included in this publication package.

[Training source identity](training-source-identity.json) was captured at
scientific closeout, before publication. The run manifest's published=false
field describes that capture time; the containing Git commit identifies this
later publication. Only presentation and packaging code changed for publication.

The current campaign used CPU only and started no cloud instance. Its own
[closure](compute-closure.json) records training completion before the first
new high-fidelity reference read; no old shutdown record is used as proof.

The full instruction remains in
[the authorized snapshot](../../../docs/notes/2026-09-11-lf11-followup-authorized-sprint-instructions.md).
The [cloud review handoff](../../../docs/notes/2026-09-12-lf11-followup-results-cloud-review-handoff.md)
maps this package to the research questions; its delivery message supplies the
verified release commit. A Git publication is not a new scientific result.
""", encoding="utf-8")
    (paper/"README.md").write_text("""# paper_v25：温度拟合修复与剩余电学瓶颈

**VERIFIED：温度拟合取得实质改善，但本轮未进入新的PINN物理比较。**

- 可见温度归一化RMS：17.8233% → 1.1375%；加热/关断为1.8357%/0.7219%，均通过拟合门。
- 完整固定参考网格ROI温度误差：28.2210% → 1.7475%。相态与双周期事件指标保持原父状态。
- 可见电势误差：1.5670% → 0.8215%，未达到0.5%准入；按指令停止D_B/P_U及电学归一化后续。
- 能量误差：106.7402% → 49.2006%；底部电流仍明显失真，不能只凭顶部电流7.2178%的NRMSE宣称器件可用。

温度包络下界仅0.1504%，排除了“该输出区间足以解释主要温度拟合缺口”。改进由有界优化和一次温度适配共同获得，尚无适配器独立归因或正面PINN方法优势。

- [完整英文初稿](manuscript.md)
- [主图 PNG](figures/lf11-followup-main.png) / [PDF](figures/lf11-followup-main.pdf)
- [误差定位图 PNG](figures/lf11-followup-localization.png) / [PDF](figures/lf11-followup-localization.pdf)
- [拟合准入表](tables/fit-admission.md)、[固定端点与强基线](tables/fixed-endpoints.md)、[CSV](tables/endpoint-metrics.csv)、[双周期](tables/events.md)
- [主张矩阵](claim_evidence_matrix.md)、[复现说明](reproducibility.md)、[证据](evidence/README.md)、[来源](method_sources.md)
- [本轮终局](../../docs/experiment/2026-09-12-phk-v23-lf11-followup-terminal-closeout.md)

paper_v24保留原样。独立初始化、观测规则变化、完整案例确认与formal OOD未执行；本轮为单nominal开发。CPU训练已结束，本轮未启动GPU实例。下一优先方案为仅修复V头并保留已达标T/phase，状态PROPOSED_NOT_AUTHORIZED。
""", encoding="utf-8")
    claims = [
        ["温度输出区间不足以解释原主要拟合缺口", "VERIFIED", "evidence/s0.json; 包络下界0.0015038294，原可见误差0.178232659", "不证明有限网络能精确拟合全部点；343点不可精确匹配"],
        ["可见温度拟合改善93.62%，相态保持", "VERIFIED", "evidence/s1-result.json; fit-telemetry.jsonl", "训练/开发误差；优化与适配器未独立消融"],
        ["完整nominal参考上温度和能量误差也改善", "VERIFIED", "evidence/evaluation.json; tables/fixed-endpoints.md", "既有已观察nominal，不是盲测或OOD"],
        ["剩余V误差偏向底部", "VERIFIED / SUPPORTED_INTERPRETATION", "最低两z层贡献53.17%平方误差、占16.25%测度", "分布事实已验证；边界/优化/表达的唯一根因未证明"],
        ["顶部电流不能替代双电极与耗散一致性", "VERIFIED", "顶部NRMSE0.07218，底部7.81254，能量误差0.49201", "固定离散读出；相关指标不能重复包装为独立物理发现"],
        ["新的PDE/归一化方法获得增量", "UNKNOWN / NOT_RUN", "S1仅V拟合门未过，全部后续未运行", "不是已运行失败，也不支持否定这些方法"],
        ["Fourier适配器有独立方法创新", "UNKNOWN", "只有顺序开发结果，无等预算无适配反事实", "通用技巧算共同底座，不列独立创新"],
        ["氧化物材料实验或formal OOD已验证", "UNKNOWN / NOT_ESTABLISHED", "本轮无对应证据", "保持合成二维对象身份"],
    ]
    (paper/"claim_evidence_matrix.md").write_text("# 主张—证据—边界\n\n"+markdown_table(["主张", "状态", "证据", "界限"], claims)+"\n", encoding="utf-8")
    (paper/"method_sources.md").write_text("""# Method sources and adaptations

- **A: established optimization.** [Rathore et al., ICML 2024](https://proceedings.mlr.press/v235/rathore24a.html) motivates considering Adam plus L-BFGS rather than interpreting one weak optimizer endpoint as a method limit. Its results do not establish success on this wall-cell. No NNCG method or implementation is copied.
- **A: PyTorch optimizer implementation.** Runtime is torch 2.5.1+cpu. The [version-matched L-BFGS source](https://github.com/pytorch/pytorch/blob/v2.5.1/torch/optim/lbfgs.py) and [upstream license](https://github.com/pytorch/pytorch/blob/v2.5.1/LICENSE) were inspected. Existing installed public optimizers are called; no upstream source is redistributed in this follow-up. Local adaptation adds exact evaluation counting, deep parameter/optimizer rollback and accepted-step Wolfe checks. This is experiment correctness, not scientific novelty.
- **A-prime: smooth temperature latent adapter.** [Tancik et al., NeurIPS 2020](https://arxiv.org/abs/2006.10739) and its [author page](https://bmild.github.io/fourfeat/) supply the Fourier-feature motivation. The project adaptation uses a single deterministic axis-aligned low-bandwidth feature set, a zero-output additive latent branch and the unchanged temperature envelope. It reuses the repository ModifiedMLP rather than copying the author's JAX code. Feature selection, head restriction and insertion are adaptations, not a claim of Fourier-feature priority.
- **Inherited project components.** The LF11 sparse measure, full phase-logit definition, potential transform, physical contract and common face-flux readout remain unchanged. Their source/reference map is preserved in [paper_v24](../paper_v24/README.md).

Only the fitting combination has an executed development result. No equal-budget adapter ablation, new physics comparison, normalized electrical block, changed hard boundary, or new material model was executed. No external assets or source code were copied from the literature sites.
""", encoding="utf-8")
    (paper/"reproducibility.md").write_text("""# LF11 follow-up reproduction

Actual environment: Python 3.11.9, torch 2.5.1+cpu, NumPy 2.1.1, FP64 and four CPU threads on Windows. Existing project dependencies were used; no new installation or cloud instance was needed.

The original LF11 source release is 6412dbf3c766207dfb5f586a94bac8eaa0f247d5. The follow-up modules are included with this paper_v25 release:

- `pinn_pcm_sci/phk_v23_lf11_followup.py`: visible envelope lower bound and original-parent audit.
- `pinn_pcm_sci/phk_v23_lf11_followup_fit.py`: the actual bounded fitting and accepted-state rollback.
- `pinn_pcm_sci/phk_v23_lf11_followup_evaluate.py`: one post-training fixed endpoint; only nominal reference access.
- `pinn_pcm_sci/phk_v23_lf11_followup_report.py`: tables, figures, manuscript and selected evidence from saved outputs.

Run root: `outputs/runs/20260911-lf11-followup-fit-electric-block`. Its frozen contract and fit plan are copied into [evidence](evidence/README.md). The same sparse bundle and original parent are resolved first from the original local LF11 run, falling back to paper_v24/evidence. S0 records their exact identities once. No complete medium field is opened by the fitting process.

The complete visible targets are already exposed by the inherited parent. They are training/development data. Heating/off metrics use conditional global quadrature; the global V/T metrics include the separately declared analytic IC weight. Phase raw RMS uses positive-time global weights; the logit objective retains the half-global/half-interface measure. In S1 phase is held fixed while the independent V/T observation components are optimized; no PDE gradient routing or old phase-freeze protocol is used.

The following are reproduction recipes for a **fresh directory**, not commands to overwrite the completed run or authorization for a new scientific experiment:

```powershell
.\\.venv\\Scripts\\python.exe -m pinn_pcm_sci.phk_v23_lf11_followup --root outputs/reproduction/lf11-followup-new --stage s0
.\\.venv\\Scripts\\python.exe -m pinn_pcm_sci.phk_v23_lf11_followup_fit --root outputs/reproduction/lf11-followup-new
```

S1 is allowed only when S0 does not preclude its temperature admission criteria. The actual run used 1200 Adam updates plus exactly 400 fixed complete component objective/gradient evaluations. L-BFGS calls are counted directly, including repeats and rejected trials; they are not equated with Adam updates or equal compute. Per-head optimizer snapshots are preserved as `s1/base_lbfgs_V.pt`, `base_lbfgs_T.pt`, `refinement_lbfgs_V.pt`, and `refinement_lbfgs_T.pt`; the two Adam checkpoints and fixed final state are also retained. Intermediate states are development checkpoints, not selected using high-fidelity feedback.

The final saved checkpoint can be inspected without training: read its config, model_state_dict and temperature_adapter flag, then call `fit_model(config, state, adapter)` from the fitting module. The final file does not claim to contain a joint Adam state after L-BFGS; actual per-stage optimizer states are in their separately named checkpoint files, also copied into [the publication package](evidence/optimizer-states/).

Before any full nominal evaluation, the training process must have ended and a current `compute-closure.json` plus `evaluation_contract.json` must exist. The actual receipts identify CPU-only execution and zero cloud instances. For the completed run:

```powershell
.\\.venv\\Scripts\\python.exe -m pinn_pcm_sci.phk_v23_lf11_followup_evaluate --root outputs/runs/20260911-lf11-followup-fit-electric-block
```

The evaluator refuses an existing adjudication. It uses the original nominal extra-fine file named in `phk_v22r_evaluator.NOMINAL_REFERENCE`; it never calls a stress control. It predicts its own full V/T/phase fields, compares the frozen coordinate axes and uses the unchanged LF11 event/readout implementation. Older endpoints and baselines are reused from their saved records/traces. Additional power and bottom-current scores use those traces and the unchanged native scales. No old teacher current/power becomes a prediction.

To rebuild presentation artifacts from saved results without training or reference reads:

```powershell
.\\.venv\\Scripts\\python.exe -m pinn_pcm_sci.phk_v23_lf11_followup_report --root outputs/runs/20260911-lf11-followup-fit-electric-block
```

The five targeted CPU tests cover zero-envelope interval distances, weighted chunk gradients against the actual model, budget-exhaustion rollback, evaluated accepted endpoints, and zero-output adapter insertion. Full training was run once, not repeated for verification. New D_B/P_U/R/N/G/D_N did not run because the final voltage criterion failed. No claim of reproducibility on an untested backend or statistical independence is made.
""", encoding="utf-8")
    closeout = ROOT/"docs/experiment/2026-09-12-phk-v23-lf11-followup-terminal-closeout.md"
    closeout.write_text("""# LF11后续：温度拟合修复，电势准入未满足

状态：LF11_FOLLOWUP_THERMAL_FIT_REPAIRED_VOLTAGE_ADMISSION_NOT_MET。执行已按预声明停止条件结束。

用户明确要求执行 [完整Sprint指令](../notes/2026-09-11-lf11-followup-authorized-sprint-instructions.md)。本轮继承6412dbf3，保留LF11、paper_v24、物理、观测、指标与stress边界。没有自动Git写入、云端发布或跨会话发送。

## 新增科学证据

**VERIFIED：包络的定量下界远小于旧拟合误差。** 343个可见点的温度超过原输出上界；全局/加热归一化RMS下界为0.0015038294/0.0028834613，关断为0。最坏差距0.0221523；原父模型可见温度RMS为0.178232659。因此“输出区间足以解释主要温度误差”被排除；不声称区间内任意函数均可由该有限网络表示，也不裁剪观测。

**VERIFIED：温度拟合修复已完成。** 可见T：17.8233%→1.1375%；加热1.8357%、关断0.7219%，三项均过门。V：1.5670%→0.8215%，仍高于0.5%，是唯一未满足的拟合条件。phase参数和可见指标完全不变。

**VERIFIED：改善延伸至固定nominal参考网格，尚未闭合器件。** ROI T误差28.2210%→1.7475%，能量误差106.7402%→49.2006%；顶部电流NRMSE8.0388%→7.2178%，底部仍为781.2535%。S=0.001188671875、raw Ephi=0.027268375553保持原父状态；双周期timing为0.03788/0.00215，严格器件门未过。B_logit_waveform仍为强对照。

**VERIFIED的定位事实 / SUPPORTED_INTERPRETATION的路线建议：** 最低两个可见z层占16.25%测度、贡献53.17%最终V平方误差。下一步应只研究剩余电势拟合；这还没有证明边界条件、优化或有限表示中的唯一根因。

## 实际执行与归因限制

先原网络600 Adam；完整固定V/T观测L-BFGS各80/120次评估。随后按预定触发添加唯一T头平滑残差，插入时输出完全不变；再600 Adam及V/T各40/160次评估。合计1200 Adam、400目标/梯度评估。四次L-BFGS接受38/59/19/78步，两个预算中断的线搜索退回最后接受状态。未使用未计数重跑、额外优化或高保真选模。

S1只优化独立V/T观测目标，phase保持原父状态；最终检查点恢复所有参数的可训练属性，但没有执行任何PDE阶段。温度适配与进一步优化未作等预算独立消融，不能单独计为创新。

新D_B/P_U及R/N/G/D_N均为NOT_RUN_S1_VOLTAGE_FIT_ADMISSION_NOT_MET，不是执行失败。双电极四次方hard lift、phase latent、焓、专家、filter和新物理均未运行。没有S2多节点归因结果，不以历史Adam状态解释新L-BFGS端点。

本轮全部CPU执行，训练进程已正常结束；没有启用GPU实例，因此没有本轮待关闭实例，也没有沿用旧关机凭据。本轮训练结束后才首次读取完整高保真参考。所有高保真反馈都属于已观察nominal的开发评价，无未见留出、独立seed或formal OOD。

## 图稿和复现

- [paper_v25](../../paper/paper_v25/README.md)：整合完整方法、实际结果、主张矩阵、局限性、主图及定位图。
- [固定端点与基线](../../paper/paper_v25/tables/fixed-endpoints.md)、[拟合表](../../paper/paper_v25/tables/fit-admission.md)。
- [选定证据](../../paper/paper_v25/evidence/README.md)、[复现说明](../../paper/paper_v25/reproducibility.md)、[来源](../../paper/paper_v25/method_sources.md)。
- 完整原产物：outputs/runs/20260911-lf11-followup-fit-electric-block；原始优化状态与全场预测保持本地。

## 唯一优先的下一步（PROPOSED_NOT_AUTHORIZED）

从本轮固定父状态仅修复V头，保持已达标T与phase函数不变、原观测目标和信息边界不变；建议先给固定全观测V目标最多200次L-BFGS评估，不改物理或表示、不移动0.5%门。达标后另按原S2设计检验D_B/P_U；未达标则用V头证据再决定表示改动，不能默认重启被撤回hard lift或直接开电学归一化。此处是新预算建议，未执行或授权。

首个可信匹配PINN信号后再安排两个新初始化、一个预声明观测规则及一个完整新协议案例的最小确认；不把本轮改进当成这些确认。
""", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=RUN)
    args = parser.parse_args()
    paper = ROOT/"paper/paper_v25"
    figures(args.root, paper)
    tables = write_paper(args.root, paper)
    delivery_documents(args.root, paper, tables)


if __name__ == "__main__":
    main()
