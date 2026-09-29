"""No-feedback replay of the unchanged, source-pinned VO2 history implementation.

This module does not evolve an RC or thermal system and never reads files. The
caller supplies temperatures, then separately supplies source arrays for scoring.
The source check must pass before interpreting a prediction's history replay.
"""
from __future__ import annotations

from collections.abc import Mapping
import numpy as np

from pinn_pcm_sci.vo2_author_reproduction import HKEYS, Hysteresis, P, Parameters


REPLAY_FIELDS = ("resistance", "g", *HKEYS)
DISCRETE_FIELDS = ("delta", "reversed")
DEFAULT_WINDOWS = {"full": (0.0, 20e-6), "transient": (0.0, 10e-6),
                   "tail": (10e-6, 20e-6)}


def _matrix(value, name):
    array = np.asarray(value, dtype=np.float64)
    if array.ndim != 2 or array.shape[0] < 1 or array.shape[1] not in (1, 2):
        raise ValueError(f"{name} must have shape (native times, 1 or 2 devices)")
    if not np.isfinite(array).all():
        raise ValueError(f"{name} has nonfinite values")
    return array


def replay_temperatures(temperature, parameters: Parameters = P):
    """Record source-exact same-time R/g/H for a supplied temperature history.

    Every call creates a fresh legal history object (324.9 K for frozen P).
    Reversal uses the original joint vector trigger; dynamic resistance and g
    use the original 305--370 K constitutive clipping. The input temperature
    itself is neither clipped nor modified. No currents feed this replay back.
    """
    temperatures = _matrix(temperature, "temperature")
    history = Hysteresis(temperatures.shape[1], parameters)
    result = {key: np.empty_like(temperatures) for key in REPLAY_FIELDS}
    for index, current in enumerate(temperatures):
        history.reversal(current)
        result["resistance"][index] = history.resistance(current, dynamic=True)
        result["g"][index] = history.g(np.clip(current, 305.0, 370.0))
        for key in HKEYS:
            result[key][index] = getattr(history, key)
    if not all(np.isfinite(value).all() for value in result.values()):
        raise FloatingPointError("nonfinite history replay; no interpretation")
    return result


def verify_source_replay(saved: Mapping, replayed: Mapping):
    """Check all native source rows; missing required fields raise immediately.

    Branch flags must be exact. Other differences may only be FP64 arithmetic
    roundoff: 64 eps * max(1, max(abs(saved field))). This is an implementation
    reproduction threshold, not a physical accuracy or engineering tolerance.
    """
    fields = {}
    shape = _matrix(saved["temperature"], "saved temperature").shape
    for key in REPLAY_FIELDS:
        reference = _matrix(saved[key], f"saved {key}")
        candidate = _matrix(replayed[key], f"replayed {key}")
        if reference.shape != shape or candidate.shape != shape:
            raise ValueError(f"shape mismatch in {key}")
        difference = candidate - reference
        tolerance = (0.0 if key in DISCRETE_FIELDS else
                     64.0 * np.finfo(np.float64).eps *
                     max(1.0, float(np.max(np.abs(reference)))))
        worst = np.unravel_index(np.argmax(np.abs(difference)), shape)
        fields[key] = {
            "bitwise_equal": bool(np.array_equal(candidate.view(np.uint64),
                                                   reference.view(np.uint64))),
            "max_abs_difference": float(np.max(np.abs(difference))),
            "rms_difference": float(np.sqrt(np.mean(difference ** 2))),
            "tolerance": tolerance,
            "passed": bool(np.max(np.abs(difference)) <= tolerance),
            "worst_native_index": int(worst[0]), "worst_device": int(worst[1]),
            "different_entries": int(np.count_nonzero(difference)),
        }
    return {
        "passed": all(record["passed"] for record in fields.values()),
        "all_bitwise_equal": all(record["bitwise_equal"] for record in fields.values()),
        "native_rows": shape[0], "devices": shape[1], "fields": fields,
        "tolerance_scope": "source arithmetic replay only, not physical qualification",
        "reversal_rule": "unchanged joint-vector max(abs(dT)) > 0.01 K",
    }


def _time_vector(time, count):
    time = np.asarray(time, dtype=np.float64)
    if (time.ndim != 1 or len(time) != count or not np.isfinite(time).all()
            or np.any(np.diff(time) <= 0)):
        raise ValueError("native times must be finite and strictly increasing")
    return time


def _weights(time):
    if len(time) < 2:
        raise ValueError("window requires at least two native times")
    delta = np.diff(time)
    weights = np.concatenate(([delta[0] / 2], (delta[:-1] + delta[1:]) / 2,
                              [delta[-1] / 2]))
    return weights / (time[-1] - time[0])


def _error_metrics(value, reference, weights):
    difference = value - reference
    return {"rms": float(np.sqrt(weights @ (difference ** 2))),
            "max_abs": float(np.max(np.abs(difference))),
            "signed_mean": float(weights @ difference),
            "end_difference": float(difference[-1]),
            "candidate_end": float(value[-1]), "source_end": float(reference[-1]),
            "candidate_range": [float(np.min(value)), float(np.max(value))],
            "source_range": [float(np.min(reference)), float(np.max(reference))]}


def _sampled_intervals(time, mask):
    """Inclusive native-sample ranges only; no invented crossing times."""
    switches = np.diff(np.r_[False, mask, False].astype(np.int8))
    return [{"first_native_index": int(start), "last_native_index": int(stop - 1),
             "first_sample_s": float(time[start]), "last_sample_s": float(time[stop - 1]),
             "sample_count": int(stop - start)}
            for start, stop in zip(np.flatnonzero(switches == 1),
                                   np.flatnonzero(switches == -1))]


def reversal_events(time, replayed):
    """All branch-sign changes, including any reversal at the initial sample.

    The sticky ``reversed`` flag is deliberately not used to count reversals.
    Its 0-to-1 change only identifies the first reversal, not later events.
    """
    delta = _matrix(replayed["delta"], "delta")
    time = _time_vector(time, len(delta))
    events = []
    for device in range(delta.shape[1]):
        old = np.r_[1.0, delta[:-1, device]]
        indices = np.flatnonzero(delta[:, device] != old)
        events.append({"device": device, "count": len(indices),
                       "native_indices": indices.tolist(),
                       "times_s": time[indices].tolist(),
                       "from_delta": old[indices].tolist(),
                       "to_delta": delta[indices, device].tolist()})
    return events


def history_diagnostics(time, temperature, voltage, current_kcl, replayed,
                        saved: Mapping, windows=None):
    """Score one no-feedback replay against qualified source R/g/H/current.

    Returns ``(diagnostic_arrays, report)``. The two diagnostic arrays are I_R
    and r_close in amperes; neither replaces the original KCL current. Errors
    use normalized trapezoidal time weights, separately in each native window.
    """
    temperature = _matrix(temperature, "conditional temperature")
    voltage = _matrix(voltage, "voltage")
    current_kcl = _matrix(current_kcl, "KCL current")
    shape = temperature.shape
    time = _time_vector(time, len(temperature))
    if voltage.shape != shape or current_kcl.shape != shape:
        raise ValueError("current/voltage/temperature shape mismatch")
    for key in REPLAY_FIELDS:
        if _matrix(replayed[key], key).shape != shape or _matrix(saved[key], key).shape != shape:
            raise ValueError(f"history shape mismatch in {key}")
    reference_current = _matrix(saved["device_current"], "source device current")
    if reference_current.shape != shape:
        raise ValueError("source current shape mismatch")
    current_r = voltage / replayed["resistance"]
    closure = current_r - current_kcl
    arrays = {"I_R": current_r, "r_close": closure}
    if not all(np.isfinite(value).all() for value in arrays.values()):
        raise FloatingPointError("nonfinite constitutive current")
    predicted_events = reversal_events(time, replayed)
    source_events = reversal_events(time, saved)
    rows = []
    for name, (begin, end) in (DEFAULT_WINDOWS if windows is None else windows).items():
        mask = (time >= begin - 1e-18) & (time <= end + 1e-18)
        weights = _weights(time[mask])
        for device in range(shape[1]):
            metrics = {key: _error_metrics(replayed[key][mask, device], saved[key][mask, device], weights)
                       for key in ("resistance", "g", *HKEYS)}
            metrics["I_R"] = _error_metrics(current_r[mask, device], reference_current[mask, device], weights)
            metrics["r_close"] = _error_metrics(closure[mask, device], np.zeros(np.count_nonzero(mask)), weights)
            predicted_delta = replayed["delta"][mask, device]
            source_delta = saved["delta"][mask, device]
            branch_difference = predicted_delta != source_delta
            fraction_difference = np.sign(replayed["g"][mask, device] - .5) != np.sign(saved["g"][mask, device] - .5)
            predicted = np.asarray(predicted_events[device]["times_s"])
            source = np.asarray(source_events[device]["times_s"])
            predicted = predicted[(predicted >= begin - 1e-18) & (predicted <= end + 1e-18)]
            source = source[(source >= begin - 1e-18) & (source <= end + 1e-18)]
            matched = min(len(predicted), len(source))
            differences = predicted[:matched] - source[:matched]
            rows.append({
                "window": name, "device": device, "metrics": metrics,
                "delta_mismatch_samples": int(np.count_nonzero(branch_difference)),
                "delta_mismatch_time_fraction": float(weights @ branch_difference),
                "g_half_branch_mismatch_samples": int(np.count_nonzero(fraction_difference)),
                "g_half_branch_mismatch_time_fraction": float(weights @ fraction_difference),
                "reversals": {
                    "candidate_count": len(predicted), "source_count": len(source),
                    "pairing": "native event order; no waveform alignment",
                    "paired_time_differences_s": differences.tolist(),
                    "paired_time_rms_s": float(np.sqrt(np.mean(differences ** 2))) if matched else None,
                    "paired_time_max_abs_s": float(np.max(np.abs(differences))) if matched else None,
                    "unmatched_candidate_times_s": predicted[matched:].tolist(),
                    "unmatched_source_times_s": source[matched:].tolist(),
                },
            })
    weights = _weights(time)
    outside = []
    for device in range(shape[1]):
        values = temperature[:, device]
        lower, upper = values < 305.0, values > 370.0
        outside.append({
            "device": device, "state_temperature_clipped": False,
            "range_K": [float(values.min()), float(values.max())],
            "outside_sample_count": int(np.count_nonzero(lower | upper)),
            "outside_time_fraction": float(weights @ (lower | upper)),
            "below_305_K_intervals": _sampled_intervals(time, lower),
            "above_370_K_intervals": _sampled_intervals(time, upper),
            "interval_semantics": "inclusive native sampled ranges; no off-grid crossing estimate",
        })
    return arrays, {
        "rows": rows, "candidate_reversal_events": predicted_events,
        "source_reversal_events": source_events, "outside_constitutive_temperature": outside,
        "current_units": "A", "resistance_units": "ohm", "temperature_units": "K",
        "history_state_units": {"delta": "1", "reversed": "1", "Tr": "K", "gr": "1", "Tpr": "K", "T_last": "K"},
        "metric_time_weights": "normalized native-time trapezoidal, each window separately",
        "feedback": False, "I_R_replaces_I_KCL": False,
    }
