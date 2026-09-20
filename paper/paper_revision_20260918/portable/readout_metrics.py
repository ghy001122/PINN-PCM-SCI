"""Frozen NumPy-only metrics copied from the repository at paper revision.

No model loading, neural execution, linear solve, or private repository path.
The only adaptations inject serialized constants/grid and a NumPy waveform.
Scientific definitions retain the published LF11 semantics, including the
historical bottom-current comparison against the reference TOP current.
"""
from __future__ import annotations
from types import SimpleNamespace
from typing import Any
import numpy as np


def axis_weights(axis, lower=None, upper=None):
    edges = np.concatenate(([axis[0] if lower is None else lower],
                            .5 * (axis[:-1] + axis[1:]),
                            [axis[-1] if upper is None else upper]))
    weights = np.diff(edges)
    if np.any(weights <= 0):
        raise ValueError("nonpositive quadrature weights")
    return weights / weights.sum()

def _event_summary(
    phase: np.ndarray,
    *,
    time: np.ndarray,
    roi: np.ndarray,
    period: float,
    phase_threshold: float,
    event_fraction: float,
) -> dict[str, Any]:
    roi_fraction = np.mean(phase[:, roi] >= phase_threshold, axis=1)
    full_fraction = np.mean(phase >= phase_threshold, axis=1)
    outside_fraction = np.mean(phase[:, ~roi] >= phase_threshold, axis=1)
    cycles = []
    failures = []
    for cycle_index in range(2):
        start = cycle_index * period
        end = (cycle_index + 1) * period
        mask = (time >= start) & (time <= end if cycle_index == 1 else time < end)
        indices = np.flatnonzero(mask)
        values = roi_fraction[indices]
        peak_position = int(np.argmax(values))
        peak_index = int(indices[peak_position])
        crossing = None
        for before, after in zip(indices[:-1], indices[1:], strict=True):
            low = float(roi_fraction[before])
            high = float(roi_fraction[after])
            if low < event_fraction <= high and high > low:
                fraction = (event_fraction - low) / (high - low)
                crossing = float(time[before] + fraction * (time[after] - time[before]))
                break
        pre = float(values[0])
        peak = float(values[peak_position])
        excursion = peak - pre
        recovery = (
            float((peak - float(values[-1])) / excursion) if excursion > 0.0 else 0.0
        )
        cycle = {
            "cycle": cycle_index + 1,
            "event_time": crossing,
            "pre_roi_fraction": pre,
            "peak_roi_fraction": peak,
            "peak_full_domain_fraction": float(full_fraction[peak_index]),
            "peak_outside_roi_fraction": float(outside_fraction[peak_index]),
            "recovery_fraction": recovery,
            "peak_time_index": peak_index,
        }
        cycles.append(cycle)
        if crossing is None:
            failures.append(f"cycle_{cycle_index + 1}_event_missing")
        if peak < 0.02:
            failures.append(f"cycle_{cycle_index + 1}_roi_peak_below_minimum")
        if cycle["peak_full_domain_fraction"] > 0.45:
            failures.append(f"cycle_{cycle_index + 1}_false_global_transition")
        if cycle["peak_outside_roi_fraction"] > 0.10:
            failures.append(f"cycle_{cycle_index + 1}_locality_failure")
        if recovery < 0.70:
            failures.append(f"cycle_{cycle_index + 1}_recovery_failure")
    return {
        "cycles": cycles,
        "roi_fraction": roi_fraction.tolist(),
        "full_fraction": full_fraction.tolist(),
        "outside_fraction": outside_fraction.tolist(),
        "failures": failures,
        "passed": not failures,
    }

def readout(potential, temperature, phase, grid, voltage, physics):
    """Evaluate the frozen harmonic face network without solving its equations.

    Electrode currents and edge-dissipation power are independent observables.
    A nonzero discrete balance defect is reported rather than hidden by P/U.
    """
    first, second = grid.internal_first, grid.internal_second
    half, area = grid.internal_half_distance, grid.internal_area
    top = np.arange((grid.nz-1)*grid.nx, grid.nz*grid.nx)
    overlap = grid.bottom_overlap(physics.heater_width_fraction)
    bottom = np.flatnonzero(overlap > 0)
    records = {key: [] for key in ("top_current", "bottom_current", "joule_power",
                                    "input_power", "power_defect", "electric_fv_rms")}
    for v, t, ph, u in zip(potential, temperature, phase, voltage, strict=True):
        sigma = np.exp(physics.conductivity_temperature_gain*t+
                       np.log(physics.conductivity_phase_ratio)*ph**2*(3-2*ph))
        conductance = 1/(half/(sigma[first]*area)+half/(sigma[second]*area))
        dv = v[first]-v[second]
        current = conductance*dv
        gt = sigma[top]*grid.dx/(.5*grid.dz)
        gb = sigma[bottom]*overlap[bottom]/(.5*grid.dz)
        it = gt*(u-v[top]); ib = gb*v[bottom]
        power = np.sum(conductance*dv**2)+np.sum(gt*(u-v[top])**2)+np.sum(gb*v[bottom]**2)
        defect = np.zeros(grid.cell_count)
        np.add.at(defect, first, current); np.add.at(defect, second, -current)
        defect[top] -= it; defect[bottom] += ib
        records["top_current"].append(float(it.sum()))
        records["bottom_current"].append(float(ib.sum()))
        records["joule_power"].append(float(power))
        records["input_power"].append(float(u*it.sum()))
        records["power_defect"].append(float(power-u*it.sum()))
        records["electric_fv_rms"].append(float(np.sqrt(np.mean((defect/grid.cell_volumes)**2))))
    return {key: np.asarray(value) for key, value in records.items()}

def time_rms(values, times):
    return float(np.sqrt(np.trapezoid(values**2, times)/(times[-1]-times[0])))

def field_rms(predicted, reference, times, roi=None):
    error = predicted-reference
    if roi is not None: error = error[:, roi]
    return float(np.sqrt(np.trapezoid(np.mean(error**2, axis=1), times)/(times[-1]-times[0])))

def metrics(fields, reference, physics, config, device_override=None):
    time, grid = reference.time, reference.grid
    if not all(np.isfinite(v).all() for v in fields.values()):
        return {"valid": False, "strict_device_pass": False, "metrics": None,
                "cycles": [], "reason": "nonfinite predicted fields"}, {}
    # Read the authoritative ROI constants, not results or any additional case.
    ev = config["qualification_event"]
    rs = ev["roi"]
    roi = (np.abs(grid.cell_x) <= float(rs["abs_x_max"])) & (grid.cell_z >= float(rs["z_min"])) & (grid.cell_z <= float(rs["z_max"]))
    active = fields["phase"] >= ev["phase_threshold"]
    truth = reference.phase >= ev["phase_threshold"]
    sym = np.mean(active != truth, axis=1)
    voltage = physics.waveform(time)
    device = (device_override if device_override is not None else
        readout(fields["potential"], fields["temperature"], fields["phase"], grid, voltage, physics))
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

def functional_comparison(candidate,base,cfg):
    if not candidate['valid'] or not base['valid']:
        return {'passed':False,'reason':'numerical_validity_failure'}
    c,b=candidate['metrics'],base['metrics']; rule=cfg['functional_rule']
    keys=rule['gain']+rule['noninferior']
    if any(c.get(k) is None or b.get(k) is None for k in keys):
        return {'passed':False,'reason':'required_metric_not_identifiable'}
    atol=cfg['decision']['absolute_tolerance']
    gain={k:b[k]-c[k]>=max(.1*b[k],rule['extra_normalized_absolute_tolerance']) for k in rule['gain']}
    noninferior={k:c[k]<=b[k]+max(.05*b[k],atol[k]) for k in rule['noninferior']}
    return {'passed':all(gain.values()) and all(noninferior.values()),'gain':gain,'noninferior':noninferior,
            'relative_changes':{k:(c[k]-b[k])/max(b[k],atol.get(k,1e-6)) for k in keys},
            'claim_layer':'limited device-function signal; separate from phase reconstruction and strict usability'}
