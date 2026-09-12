"""Post-training fixed-endpoint evaluation; no optimizer or stress access."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import torch

from .phk_benchmark import PhkControl
from .phk_v22r_evaluator import load_reference
from .phk_v23_lf11 import ROOT, SparseData, save_json, tensor, now
from .phk_v23_lf11_evaluation import metrics, time_rms
from .phk_v23_lf11_followup import RUN, weighted_rms
from .phk_v23_lf11_followup_fit import fit_model


def add_power_metrics(record, traces, time, reference_current, reference_power):
    values = record["metrics"]
    for name, error, ref in (
        ("power_trace", traces["joule_power"]-reference_power, reference_power),
        ("input_power", traces["input_power"]-reference_power, reference_power),
        ("bottom_current", traces["bottom_current"]-reference_current, reference_current),
    ):
        absolute, scale = time_rms(error, time), time_rms(ref, time)
        values[name+"_rms_error"] = absolute
        values[name+"_NRMSE"] = absolute/scale if scale > 1e-12 else None


def visible_localization(root):
    """Coordinate-group summaries of already visible residuals, no new labels."""
    with np.load(root/"s0-visible.npz", allow_pickle=False) as f:
        old = {k: f[k] for k in f.files}
    with np.load(root/"s1/fixed-visible.npz", allow_pickle=False) as f:
        final = f["fields"]
    q, weight, targets = old["coordinates"], old["weights"], old["targets"]
    squared = (final-targets)**2
    groups = []
    for z in np.unique(q[:, 1]):
        mask = q[:, 1] == z
        groups.append({"z": float(z), "probability_mass": float(weight[mask].sum()),
                       "V_normalized_rms": weighted_rms(final[:, 0]-targets[:, 0], weight, mask)/.72,
                       "V_squared_error_fraction": float(np.dot(weight[mask], squared[mask, 0])/np.dot(weight, squared[:, 0])),
                       "T_normalized_rms": weighted_rms(final[:, 1]-targets[:, 1], weight, mask)/.45})
    idx = int(np.argmax(np.abs(final[:, 0]-targets[:, 0])))
    result = {"status": "POSTHOC_VISIBLE_ERROR_LOCALIZATION", "by_z": groups,
              "largest_V_error": {"xzt": q[idx].tolist(), "observed_V": float(targets[idx, 0]),
                                  "predicted_V": float(final[idx, 0]),
                                  "absolute_error": float(abs(final[idx, 0]-targets[idx, 0]))},
              "purpose": "identify the remaining head/region for a future plan; not used for more training in this run"}
    save_json(root/"visible-error-localization.json", result)
    return result


def evaluate(root=RUN):
    root = Path(root)
    if (root/"evaluation.json").exists():
        raise FileExistsError("fixed endpoint already evaluated; reuse it")
    proof = json.loads((root/"compute-closure.json").read_text())
    if not proof["compute_stopped_before_reference_read"]:
        raise ValueError("training must be stopped")
    fit = json.loads((root/"s1/result.json").read_text())
    torch.set_num_threads(4)
    checkpoint = torch.load(root/fit["checkpoint"], map_location="cpu", weights_only=False)
    config = checkpoint["config"]
    model = fit_model(config, checkpoint["model_state_dict"], checkpoint["temperature_adapter"])
    model.eval()
    from .phk_v22r_prediction import _evaluation_axes
    from .phk_v22r_training import PhkTrainingConfig
    x, z, time = _evaluation_axes(PhkTrainingConfig(arm="STRONG_RAW", case_control="FULL"))
    xx, zz = np.meshgrid(x, z, indexing="xy")
    space = np.column_stack([xx.ravel(), zz.ravel()])
    predicted = np.empty((len(time), len(space), 3), dtype=np.float64)
    with torch.no_grad():
        for it, value in enumerate(time):
            q = np.column_stack([space, np.full(len(space), value)])
            for lo in range(0, len(q), 8192):
                predicted[it, lo:lo+8192] = model(tensor(q[lo:lo+8192])).numpy()
            if it % 200 == 0:
                print(json.dumps({"fixed_prediction_time_index": it, "total": len(time)}), flush=True)
    fields = {name: predicted[..., col] for col, name in enumerate(("potential", "temperature", "phase"))}
    np.savez_compressed(root/"s1/fixed-prediction.npz", x=x, z=z, time=time, **fields)
    # First high-fidelity array read in this follow-up, after all training ended.
    reference, identity = load_reference(PhkControl.FULL)
    if not (np.array_equal(x, reference.grid.x_centers) and np.array_equal(z, reference.grid.z_centers) and np.array_equal(time, reference.time)):
        raise ValueError("reference and frozen prediction axes differ")
    fixed_record, fixed_trace = metrics(fields, reference, model.physics, config)
    legacy = ROOT/"paper/paper_v24/evidence/local"
    previous = json.loads((legacy/"results.json").read_text())
    waveform = json.loads((legacy/"waveform-diagnostic.json").read_text())
    records = {"S1_fixed_fit": fixed_record}
    traces = {"S1_fixed_fit": fixed_trace}
    with np.load(legacy/"traces.npz", allow_pickle=False) as f:
        if not np.array_equal(time, f["time"]):
            raise ValueError("historical traces use different times")
        if not (np.array_equal(reference.top_current, f["reference_current"]) and
                np.array_equal(reference.joule_power, f["reference_power"])):
            raise ValueError("historical and current reference traces differ")
        for name in ("warm_start", "D_B", "P_U", "P_I", "P_M", "B_L", "B_P", "B_logit", "dense_LF_ONLY", "native_reference_readout_check"):
            records[name] = previous["records"][name]
            records[name]["origin"] = "REUSED_LF11_FIXED_EVIDENCE"
            prefix = name+"__"
            traces[name] = {k[len(prefix):]: f[k] for k in f.files if k.startswith(prefix)}
    with np.load(legacy/"waveform-traces.npz", allow_pickle=False) as f:
        traces["B_logit_waveform"] = {k: f[k] for k in f.files if k != "time"}
    records["B_logit_waveform"] = waveform["record"]
    records["B_logit_waveform"]["origin"] = "LF11_POSTHOC_BASELINE_RULES_FROZEN_FOR_FOLLOWUP"
    for name, record in records.items():
        add_power_metrics(record, traces[name], time, reference.top_current, reference.joule_power)
    phase_same = all(abs(fixed_record["metrics"][k]-records["warm_start"]["metrics"][k]) <= 1e-12 for k in ("S", "Ephi", "phase_max"))
    if not phase_same:
        raise ValueError("unchanged independent phase head has changed phase metrics")
    localization = visible_localization(root)
    result = {"schema_id": "lf11-followup-fixed-evaluation-v1", "recorded_utc": now(),
              "reference_sha256": identity, "reference_identity_matches_LF11": identity == previous["reference_sha256"],
              "records": records, "phase_metrics_unchanged_from_parent": phase_same,
              "new_PINN_matched_comparison_executed": False,
              "unrun_branches": {k: "NOT_RUN_S1_VOLTAGE_FIT_ADMISSION_NOT_MET" for k in ("D_B", "P_U", "R", "N", "G", "D_N")},
              "visible_error_localization": localization,
              "scope": "one fixed S1 development endpoint; original LF11 comparison identities retained; no OOD or positive PINN method claim"}
    save_json(root/"evaluation.json", result)
    np.savez_compressed(root/"evaluation-traces.npz", time=time, reference_current=reference.top_current,
                        reference_power=reference.joule_power,
                        **{name+"__"+key: val for name, trace in traces.items() for key, val in trace.items()})
    print(json.dumps({"evaluation_complete": True, "S1_metrics": fixed_record["metrics"],
                      "phase_metrics_unchanged": phase_same, "localization": localization}, indent=2), flush=True)
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, default=RUN)
    evaluate(p.parse_args().root)


if __name__ == "__main__":
    main()
