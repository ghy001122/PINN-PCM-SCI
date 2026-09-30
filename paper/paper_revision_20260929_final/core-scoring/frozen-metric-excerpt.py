# Provenance excerpt only; score.py is the independent executable entry.
import numpy as np

def time_rms(values, times):
    return float(np.sqrt(np.trapezoid(values**2, times)/(times[-1]-times[0])))

def field_rms(predicted, reference, times, roi=None):
    error = predicted-reference
    if roi is not None: error = error[:, roi]
    return float(np.sqrt(np.trapezoid(np.mean(error**2, axis=1), times)/(times[-1]-times[0])))

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
