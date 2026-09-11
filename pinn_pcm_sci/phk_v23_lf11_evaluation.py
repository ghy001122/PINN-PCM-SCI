"""Local, post-compute nominal adjudication and publication figures for LF11."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import math

import numpy as np
import torch

from .phk_benchmark import PhkControl
from .phk_v22r_evaluator import load_reference, _event_summary
from .phk_v23_lf11 import SparseData, build_model, save_json, tensor, axis_weights, now, digest
from .phk_v23_lf11_readout import make_grid, readout, interpolate_sparse


def time_rms(values, times):
    return float(np.sqrt(np.trapezoid(values**2, times)/(times[-1]-times[0])))


def field_rms(predicted, reference, times, roi=None):
    error = predicted-reference
    if roi is not None: error = error[:, roi]
    return float(np.sqrt(np.trapezoid(np.mean(error**2, axis=1), times)/(times[-1]-times[0])))


def metrics(fields, reference, physics, config):
    time, grid = reference.time, reference.grid
    if not all(np.isfinite(v).all() for v in fields.values()):
        return {"valid": False, "strict_device_pass": False, "metrics": None,
                "cycles": [], "reason": "nonfinite predicted fields"}, {}
    # Read the authoritative ROI constants, not results or any additional case.
    from .phk_v22r_evaluator import _physical_contract
    ev = _physical_contract().payload["qualification_event"]
    rs = ev["roi"]
    roi = (np.abs(grid.cell_x) <= float(rs["abs_x_max"])) & (grid.cell_z >= float(rs["z_min"])) & (grid.cell_z <= float(rs["z_max"]))
    active = fields["phase"] >= ev["phase_threshold"]
    truth = reference.phase >= ev["phase_threshold"]
    sym = np.mean(active != truth, axis=1)
    voltage = physics.waveform(tensor(time)).numpy()
    device = readout(fields["potential"], fields["temperature"], fields["phase"], grid, voltage, physics)
    pred_events = _event_summary(fields["phase"], time=time, roi=roi, period=physics.period,
                                 phase_threshold=ev["phase_threshold"], event_fraction=ev["event_threshold_roi_fraction"])
    ref_events = _event_summary(reference.phase, time=time, roi=roi, period=physics.period,
                                phase_threshold=ev["phase_threshold"], event_fraction=ev["event_threshold_roi_fraction"])
    values = {
        "S": float(np.trapezoid(sym, time)/(time[-1]-time[0])),
        "Ephi": field_rms(fields["phase"], reference.phase, time, roi),
        "ET": field_rms(fields["temperature"], reference.temperature, time, roi)/.45,
        "EV": field_rms(fields["potential"], reference.potential, time),
        "EI": time_rms(device["top_current"]-reference.top_current, time)/max(time_rms(reference.top_current, time), 1e-12),
        "energy_error": abs(float(np.trapezoid(device["joule_power"]-reference.joule_power, time)))/max(abs(float(np.trapezoid(reference.joule_power, time))), 1e-12),
        "electric_fv_rms": time_rms(device["electric_fv_rms"], time),
        "current_balance_rms": time_rms(device["top_current"]-device["bottom_current"], time),
        "power_defect_rms": time_rms(device["power_defect"], time),
        "phase_max": float(fields["phase"].max()),
    }
    cycles = []
    time_weights = axis_weights(time)
    space_weights = grid.cell_volumes/grid.cell_volumes.sum()
    for i, (pred, ref) in enumerate(zip(pred_events["cycles"], ref_events["cycles"], strict=True)):
        # Preserve the existing W1/W3 full-domain event-support measure.
        # Timing and recovery still use the whole corresponding cycle above.
        lo, hi = config["windows"][2*i]
        mask = (time >= lo) & (time <= hi)
        pa, ra = active[mask], truth[mask]
        measure = time_weights[mask, None]*space_weights[None, :]
        tp = float(np.sum(measure*(pa & ra)))
        positive = float(np.sum(measure*pa))
        ref_positive = float(np.sum(measure*ra))
        timing = abs(pred["event_time"]-ref["event_time"]) if pred["event_time"] is not None and ref["event_time"] is not None else None
        cycles.append({**pred, "recall": tp/max(ref_positive, 1e-12),
                       "precision": tp/max(positive, 1e-12), "mass_ratio": positive/max(ref_positive, 1e-12),
                       "reference_event_time": ref["event_time"], "timing_absolute": timing,
                       "support_window": [lo, hi], "support_measure": "global trapezoid time times cell volume",
                       "teacher_active_target_mass": ref_positive, "predicted_active_target_mass": positive,
                       "true_positive_target_mass": tp})
    bounded = all(np.isfinite(v).all() for v in fields.values()) and fields["phase"].min() >= -1e-10 and fields["phase"].max() <= 1+1e-10
    bounded = bounded and fields["potential"].min() >= -1e-6 and float(np.max(fields["potential"]-voltage[:, None])) <= 1e-6
    strict = bool(bounded and values["phase_max"] >= .9 and pred_events["passed"] and all(
        c["recall"] >= .9 and c["precision"] >= .8 and .8 <= c["mass_ratio"] <= 1.2 and
        c["timing_absolute"] is not None and c["timing_absolute"] <= .005 for c in cycles))
    record = {"metrics": values, "cycles": cycles, "valid": bool(bounded), "strict_device_pass": strict,
              "event_failures": pred_events["failures"], "readout": config["evaluation"]["readout"]}
    traces = {**device, "roi_active_fraction": np.asarray(pred_events["roi_fraction"]),
              "symmetric_difference": sym}
    return record, traces


def comparison(candidate, base, rule):
    if not candidate["valid"] or not base["valid"]:
        return {"passed": False, "reason": "numerical_validity_failure"}
    c, b = candidate["metrics"], base["metrics"]
    gain = {k: b[k]-c[k] >= max(rule["relative_improvement"]*b[k], rule["absolute_tolerance"][k]) for k in ("S", "Ephi")}
    noninferior = {k: c[k] <= b[k]+max(rule["relative_noninferiority"]*b[k], rule["absolute_tolerance"][k]) for k in ("ET", "EI", "EV")}
    return {"passed": bool(all(gain.values()) and all(noninferior.values())), "gain": gain,
            "noninferior": noninferior, "relative_changes": {k: (c[k]-b[k])/max(b[k], rule["absolute_tolerance"][k]) for k in ("S", "Ephi", "ET", "EI", "EV")}}


def figures(records, traces, time, reference, directory):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
                         "savefig.dpi": 200, "font.family": "DejaVu Sans"})
    names = [n for n in ("B_L", "B_P", "B_logit", "D_B", "P_U", "P_I", "P_M", "P_S", "RAD", "PF_GAR", "LATENT", "GLOBAL_PHASE") if n in records and records[n]["metrics"] is not None]
    palette = plt.get_cmap("tab10")
    colors = {n: palette(i%10) for i,n in enumerate(names)}
    fig, axes = plt.subplots(2, 3, figsize=(12, 6.7), constrained_layout=True)
    for ax, metric in zip(axes.flat, ("S", "Ephi", "ET", "EI", "EV", "energy_error")):
        ax.bar(np.arange(len(names)), [records[n]["metrics"][metric] for n in names], color=[colors[n] for n in names])
        ax.set_xticks(np.arange(len(names)), names, rotation=45, ha="right")
        ax.set_title(metric); ax.set_ylim(bottom=0); ax.grid(axis="y", alpha=.2)
    fig.suptitle("LF11: matched sparse reconstruction at fixed endpoints", fontsize=13)
    for ext in ("png", "pdf"): fig.savefig(directory/f"lf11-matched-metrics.{ext}")
    plt.close(fig)
    fig, axes = plt.subplots(2, 2, figsize=(12, 7), constrained_layout=True)
    for name in names:
        ls = "--" if name.startswith("B_") else "-"
        axes[0,0].plot(time, traces[name]["roi_active_fraction"], ls, color=colors[name], label=name)
        axes[0,1].plot(time, traces[name]["top_current"], ls, color=colors[name], label=name)
        axes[1,0].plot(time, traces[name]["joule_power"], ls, color=colors[name], label=name)
        axes[1,1].plot([1,2], [c["recall"] for c in records[name]["cycles"]], "o-", color=colors[name], label=name)
    axes[0,0].axhline(.02, color="k", lw=.6, ls=":")
    axes[0,0].plot(time, traces["native_reference_readout_check"]["roi_active_fraction"], "k", lw=1.8)
    axes[0,1].plot(time, reference.top_current, "k", lw=1.8, label="native reference")
    axes[1,0].plot(time, reference.joule_power, "k", lw=1.8, label="native reference")
    for ax, title in zip(axes.flat, ("ROI active fraction", "Electrode current", "Independent Joule power", "Cycle recall")):
        ax.set_title(title); ax.grid(alpha=.2)
    axes[1,1].set_xticks([1,2]); axes[1,1].set_ylim(0,1.05)
    axes[0,1].legend(fontsize=7, ncol=3)
    for ext in ("png", "pdf"): fig.savefig(directory/f"lf11-events-and-device.{ext}")
    plt.close(fig)


def field_figure(snapshots, records, grid, times, directory):
    import matplotlib.pyplot as plt
    sparse = min((n for n in ("B_L", "B_P", "B_logit") if records[n]["metrics"] is not None),
                 key=lambda n: records[n]["metrics"]["S"])
    physics = min((n for n in ("P_U", "P_I", "P_M") if n in records and records[n]["metrics"] is not None),
                  key=lambda n: records[n]["metrics"]["S"], default=None)
    names = ["native_reference_readout_check", sparse, "D_B"]+([physics] if physics else [])
    fig, axes = plt.subplots(len(names), 3, figsize=(10.5, 2.2*len(names)), constrained_layout=True)
    for row, name in enumerate(names):
        ph = snapshots[name]["phase"]
        display_name = "Native reference" if name == "native_reference_readout_check" else name
        for col in range(2):
            artist = axes[row,col].imshow(ph[col].reshape(grid.nz,grid.nx), origin="lower", extent=(-1,1,0,1),
                                          vmin=0, vmax=1, cmap="viridis", aspect="auto")
            axes[row,col].set_title(f"{display_name}: phase at t={times[col]:.4f}", fontsize=8)
            axes[row,col].set_xlabel("x")
            axes[row,col].set_ylabel("z")
        error = np.abs(ph[0]-snapshots["native_reference_readout_check"]["phase"][0])
        err_artist=axes[row,2].imshow(error.reshape(grid.nz,grid.nx),origin="lower",extent=(-1,1,0,1),
                                    vmin=0,vmax=1,cmap="magma",aspect="auto")
        axes[row,2].set_title("Absolute phase error, first peak",fontsize=8)
        axes[row,2].set_xlabel("x")
        axes[row,2].set_ylabel("z")
    fig.colorbar(artist, ax=axes[:,:2], shrink=.7, label="Phase")
    fig.colorbar(err_artist, ax=axes[:,2], shrink=.7, label="Absolute error")
    fig.suptitle("Fields at reference cycle peaks; displayed sparse/physics arms selected by nominal S",fontsize=10)
    for ext in ("png","pdf"): fig.savefig(directory/f"lf11-phase-fields.{ext}")
    plt.close(fig)


def evaluate(root, receipt):
    root = Path(root)
    proof = json.loads(Path(receipt).read_text(encoding="utf-8"))
    if not proof.get("compute_stopped_before_reference_read"):
        raise ValueError("a current compute-closure receipt is required before reference access")
    if proof.get("mode") == "cloud" and not all(proof.get(k) for k in ("recovery_verified", "shutdown_requested", "connection_closed")):
        raise ValueError("incomplete cloud recovery/shutdown receipt")
    config = json.loads((root/"formal/frozen_config.json").read_text())
    physical = build_model(config).physics
    reference, reference_sha = load_reference(PhkControl.FULL)
    output = root/"local"
    output.mkdir(parents=True, exist_ok=True)
    records, traces, snapshots = {}, {}, {}
    from .phk_v22r_evaluator import _physical_contract
    ev = _physical_contract().payload["qualification_event"]
    rs = ev["roi"]
    roi = (np.abs(reference.grid.cell_x) <= rs["abs_x_max"]) & (reference.grid.cell_z >= rs["z_min"]) & (reference.grid.cell_z <= rs["z_max"])
    ref_events = _event_summary(reference.phase,time=reference.time,roi=roi,period=physical.period,
                                phase_threshold=ev["phase_threshold"],event_fraction=ev["event_threshold_roi_fraction"])
    peaks = [c["peak_time_index"] for c in ref_events["cycles"]]
    def add_record(name, fields):
        records[name], traces[name] = metrics(fields, reference, physical, config)
        snapshots[name] = {k: value[peaks].copy() for k,value in fields.items()}
        print(json.dumps({"evaluated":name,"valid":records[name]["valid"],"metrics":records[name]["metrics"]},allow_nan=False),flush=True)
    for runpath in [root/"formal", root/"conditional"]:
        if not runpath.exists(): continue
        for path in sorted(runpath.glob("*/prediction.npz")):
            with np.load(path, allow_pickle=False) as p:
                if not (np.array_equal(p["x"], reference.grid.x_centers) and np.array_equal(p["z"], reference.grid.z_centers) and np.array_equal(p["time"], reference.time)):
                    raise ValueError("prediction axes are not the frozen evaluator axes")
                fields = {name: p[name] for name in ("potential", "temperature", "phase")}
            add_record(path.parent.name, fields)
            audit = path.parent/"fixed_audit.json"
            if audit.exists(): records[path.parent.name]["fixed_ad_audit"] = json.loads(audit.read_text())
    data = SparseData(root/"input/sparse.npz")
    for name in ("B_L", "B_P", "B_logit"):
        fields = interpolate_sparse(data, reference.grid.x_centers, reference.grid.z_centers, reference.time, physical, name)
        add_record(name, fields)
    # Reuse only the historical direct comparator's fields. Its interpolated
    # teacher current/power traces are deliberately not loaded or consumed.
    direct = Path(__file__).resolve().parents[1]/"outputs/runs/20260903T092005Z-phk-v23-lf0-local-final-172ae2c/prediction-lf-only-medium-direct.npz"
    with np.load(direct, allow_pickle=False) as carrier:
        if not (np.array_equal(carrier["x"], reference.grid.x_centers) and np.array_equal(carrier["z"], reference.grid.z_centers) and np.array_equal(carrier["time"], reference.time)):
            raise ValueError("historical direct fields do not share evaluator axes")
        add_record("dense_LF_ONLY", {k: carrier[k] for k in ("potential","temperature","phase")})
    records["dense_LF_ONLY"].update(source_path=str(direct), source_sha256=digest(direct),
                                  comparison_role="more-information direct reference; no same-observation win claim")
    # Native carrier is a numerical reference with known physics, not a
    # same-observation training competitor or a zero-error claim of truth.
    ref_fields = {name: getattr(reference, name) for name in ("potential", "temperature", "phase")}
    add_record("native_reference_readout_check", ref_fields)
    comparisons = {}
    for candidate, baseline in (("P_U", "D_B"), ("P_I", "P_U"), ("P_M", "P_I")):
        if candidate in records and baseline in records:
            comparisons[f"{baseline}_to_{candidate}"] = comparison(records[candidate], records[baseline], config["decision"])
    for candidate in ("P_U", "P_I", "P_M", "P_S", "RAD", "PF_GAR", "LATENT", "GLOBAL_PHASE"):
        if candidate in records:
            comparisons[candidate+"_all_same_observation_baselines"] = {
                b: comparison(records[candidate], records[b], config["decision"])
                for b in ("D_B", "B_L", "B_P", "B_logit") if b in records}
    pair_keys = ("D_B_to_P_U", "P_U_to_P_I", "P_I_to_P_M")
    positive_pairs = [key for key in pair_keys if comparisons.get(key,{}).get("passed")]
    outcome = {"positive_matched_pairs": positive_pairs,
               "conditional_path": "MATCHED_POSITIVE_ATTRIBUTION" if positive_pairs else "EQUATION_BY_HEAD_DIAGNOSIS",
               "metric_signal": "P_I_to_P_M" in positive_pairs,
               "strong_baseline_winners": [name for name in ("P_U","P_I","P_M")
                   if name+"_all_same_observation_baselines" in comparisons and
                   all(c["passed"] for c in comparisons[name+"_all_same_observation_baselines"].values())]}
    save_json(output/"results.json", {"schema_id": "lf11-local-matched-adjudication-v1", "recorded_utc": now(),
        "reference_sha256": reference_sha, "reference_role": "fixed-discretization nominal reference; historic oracle no-go retained",
        "records": records, "comparisons": comparisons, "outcome": outcome, "strict_device_gate_is_separate": True,
        "scope": "single-initialization nominal development; no formal OOD or experimental validation"})
    with (output/"traces.npz").open("wb") as f:
        np.savez_compressed(f, time=reference.time, reference_current=reference.top_current,
                            reference_power=reference.joule_power,
                            **{name+"__"+key: value for name, trace in traces.items() for key,value in trace.items()})
    figures(records, traces, reference.time, reference, output)
    field_figure(snapshots, records, reference.grid, reference.time[peaks], output)
    lines = ["# LF11 fixed-endpoint results", "", "Nominal sparse reconstruction; strict usability reported separately.", "",
             "| Role | S | Raw Ephi | ET/0.45 | EI | EV | Energy error | Strict device |", "|---|---:|---:|---:|---:|---:|---:|---|"]
    for name, record in records.items():
        m = record["metrics"]
        if m is None:
            lines.append(f"| {name} | INVALID | — | — | — | — | — | False |")
            continue
        lines.append("| "+name+" | "+" | ".join(f"{m[k]:.8g}" for k in ("S","Ephi","ET","EI","EV","energy_error"))+f" | {record['strict_device_pass']} |")
    (output/"results.md").write_text("\n".join(lines)+"\n", encoding="utf-8")
    print(json.dumps({"status":"LOCAL_EVALUATION_COMPLETE", "roles":list(records), "comparisons":comparisons,"outcome":outcome}, allow_nan=False))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--compute-closure", type=Path, required=True)
    a=p.parse_args()
    torch.set_num_threads(2)
    evaluate(a.root, a.compute_closure)


if __name__ == "__main__": main()
