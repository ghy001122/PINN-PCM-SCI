"""Portable NumPy-only joint endpoint scoring; no repository fallback.

Recomputes finite-difference physical defects from saved endpoint arrays.
Does not run a neural model, evaluate AD residuals, replay hysteresis, or train.
"""
from pathlib import Path
from functools import lru_cache
import argparse
import csv
import json
import sys

import numpy as np

EPS = np.finfo(np.float64).eps
WINDOWS = {'full': (0., 20e-6), 'transient': (0., 10e-6), 'tail': (10e-6, 20e-6)}


def resolve(root, relative):
    root = Path(root).resolve()
    if Path(relative).is_absolute():
        raise ValueError('Runtime paths must be relative to the supplied package root')
    target = (root / relative).resolve()
    if not target.is_relative_to(root):
        raise ValueError('Runtime path escapes the supplied package root')
    return target


def read(root, relative):
    return json.loads(resolve(root, relative).read_text(encoding='utf-8'))


def arrays(root, relative, required):
    with np.load(resolve(root, relative), allow_pickle=False) as archive:
        missing = set(required) - set(archive.files)
        if missing:
            raise KeyError(f'{relative}: missing fields {sorted(missing)}')
        result = {key: archive[key] for key in archive.files}
    return result


def save(root, relative, value):
    path = resolve(root, relative)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n', encoding='utf-8')


def trap(t):
    h = np.diff(t)
    if len(t) < 2 or not np.all(np.isfinite(t)) or not np.all(h > 0.):
        raise ValueError('Finite, increasing native times are required')
    return np.r_[h[0]/2, (h[:-1] + h[1:])/2, h[-1]/2] / (t[-1] - t[0])


def rms(x, w):
    return float(np.sqrt(w @ np.mean(x*x, axis=1)))


def source_common_rc(resistance, settings):
    """Same fixed discrete RC readout; neither source T nor H is re-evolved."""
    p = settings['parameters_SI']
    alpha = settings['dt_s'] / p['C']
    vin = np.asarray(settings['Vin_V'], dtype=np.float64)
    voltage = np.empty_like(resistance)
    voltage[0] = settings['initial_voltage_V']
    coefficient = 1. - alpha * (1. / p['RL'] + 1. / resistance[:-1])
    drive = alpha * vin / p['RL']
    for n in range(len(voltage) - 1):
        voltage[n + 1] = coefficient[n] * voltage[n] + drive
    return voltage


def reversal_events(t, delta):
    events = []
    for device in range(delta.shape[1]):
        old = np.r_[1., delta[:-1, device]]
        indices = np.flatnonzero(delta[:, device] != old)
        events.append(dict(device=device, count=len(indices), native_indices=indices.tolist(),
                           times_s=t[indices].tolist(), from_delta=old[indices].tolist(),
                           to_delta=delta[indices, device].tolist()))
    return events


def detect_peaks(times, current):
    candidates = np.flatnonzero((current[1:-1] > current[:-2]) & (current[1:-1] >= current[2:])
                               & (current[1:-1] > .0015)) + 1
    chosen = []
    for i in sorted(candidates, key=lambda j: (-current[j], times[j])):
        if all(abs(times[i] - times[j]) >= .5e-6 - 1e-18 for j in chosen):
            chosen.append(int(i))
    return np.array(sorted(chosen), dtype=int)


def peak_matches(reference_times, prediction_times, max_gap=.25e-6):
    a, b = tuple(reference_times), tuple(prediction_times)
    tolerance = 8*EPS*max((max_gap, *map(abs, a), *map(abs, b)))

    @lru_cache(None)
    def solve(i, j):
        if i == len(a) or j == len(b):
            return ()
        choices = [solve(i+1, j), solve(i, j+1)]
        if abs(a[i]-b[j]) <= max_gap+tolerance:
            choices.append(((i, j),)+solve(i+1, j+1))
        return min(choices, key=lambda pairs: (-len(pairs), sum(abs(a[x]-b[y]) for x, y in pairs),
                                               tuple((a[x], b[y]) for x, y in pairs)))
    pairs = list(solve(0, 0))
    used_a, used_b = {x for x, y in pairs}, {y for x, y in pairs}
    return pairs, [i for i in range(len(a)) if i not in used_a], [j for j in range(len(b)) if j not in used_b]


def summarize_peaks(t, reference, prediction, gap=.25e-6):
    ir, ip = detect_peaks(t, reference), detect_peaks(t, prediction)
    result = {}
    for window, (lo, hi) in WINDOWS.items():
        r, p = ir[(t[ir] >= lo) & (t[ir] <= hi)], ip[(t[ip] >= lo) & (t[ip] <= hi)]
        pairs, ur, up = peak_matches(t[r].tolist(), t[p].tolist(), gap)
        result[window] = dict(
            reference_times_s=t[r].tolist(), prediction_times_s=t[p].tolist(),
            reference_heights_A=reference[r].tolist(), prediction_heights_A=prediction[p].tolist(),
            reference_count=len(r), prediction_count=len(p),
            pairs=[dict(reference_time_s=float(t[r[x]]), prediction_time_s=float(t[p[y]]),
                        signed_time_difference_s=float(t[p[y]]-t[r[x]]),
                        signed_height_difference_A=float(prediction[p[y]]-reference[r[x]])) for x, y in pairs],
            unmatched_reference_times_s=t[r[ur]].tolist(), unmatched_prediction_times_s=t[p[up]].tolist(),
            timing_RMS_s=float(np.sqrt(np.mean([(t[p[y]]-t[r[x]])**2 for x, y in pairs]))) if pairs else None,
            reference_first_peak_s=float(t[r[0]]) if len(r) else None,
            prediction_first_peak_s=float(t[p[0]]) if len(p) else None,
            reference_ISI_s=np.diff(t[r]).tolist(), prediction_ISI_s=np.diff(t[p]).tolist(),
            reference_frequency_Hz=float(1/np.mean(np.diff(t[r]))) if len(r) > 1 else None,
            prediction_frequency_Hz=float(1/np.mean(np.diff(t[p]))) if len(p) > 1 else None,
            matching_max_gap_s=gap, functional_state_prediction=None)
    return result


def evaluate(label, T, R, v, delta, source, observations, settings):
    p = settings['parameters_SI']
    time = source['time']; w = trap(time); h = settings['dt_s']
    Vin = np.asarray(settings['Vin_V'], dtype=np.float64)
    eta = settings['eta']
    K = p['Sth'] * np.array([[1., -eta], [-eta, 1.]])
    I = v/R
    heat = p['Cth']*np.diff(T, axis=0)/h + (T[:-1]-p['Tbase']) @ K.T - v[:-1]**2/R[:-1]
    rc = p['C']*np.diff(v, axis=0)/h - (Vin-v[:-1])/p['RL'] + v[:-1]/R[:-1]
    obs = np.stack([np.interp(observations['observation_time'], time, v[:, j]) for j in range(2)], axis=1)
    obs_error = obs-observations['observation_voltage']; ow = observations['observation_weights']
    row = dict(method=label, joint_current_RMS_A=rms(I-source['device_current'], w),
               joint_current_RMS_uA=1e6*rms(I-source['device_current'], w),
               temperature_RMS_K=rms(T-source['temperature'], w), observation_RMS_V=rms(obs_error, ow),
               thermal_RMS_W=float(np.sqrt(np.mean(heat*heat))), RC_RMS_A=float(np.sqrt(np.mean(rc*rc))),
               full_voltage_RMS_V=rms(v-source['voltage'], w), negative_power_samples=int(np.sum(v*I < 0.)),
               temperature_min_K=float(T.min()), temperature_max_K=float(T.max()),
               outside_constitutive_range_samples=int(np.sum((T < 305.) | (T > 370.))))
    events, sourceevents = reversal_events(time, delta), reversal_events(time, source['delta'])
    devices = []
    for j in range(2):
        devices.append(dict(device='AB'[j], current_RMS_A=float(np.sqrt(w@((I[:, j]-source['device_current'][:, j])**2))),
                            temperature_RMS_K=float(np.sqrt(w@((T[:, j]-source['temperature'][:, j])**2))),
                            voltage_RMS_V=float(np.sqrt(w@((v[:, j]-source['voltage'][:, j])**2))),
                            thermal_RMS_W=float(np.sqrt(np.mean(heat[:, j]**2))),
                            observation_RMS_V=float(np.sqrt(ow@(obs_error[:, j]**2))),
                            candidate_reversals=events[j], source_reversals=sourceevents[j],
                            peaks=summarize_peaks(time, source['device_current'][:, j], I[:, j])))
    return row, devices


def gates(rows, controls, settings):
    inc = settings['increment']; candidate = rows['N_dyn']; result = {}
    for name in controls:
        control = rows[name]
        gain = control['joint_current_RMS_A']-candidate['joint_current_RMS_A']
        current = gain >= max(inc['current_relative']*control['joint_current_RMS_A'], inc['current_absolute_A'])
        noninferior = {key: candidate[key] <= max(inc['noninferiority_factor']*control[key], control[key]+floor)
                      for key, floor in inc['absolute_floors'].items()}
        result[name] = dict(current_gain_A=gain,
                            current_relative_gain=gain/control['joint_current_RMS_A'] if control['joint_current_RMS_A'] else None,
                            current_pass=current, noninferiority=noninferior,
                            passed=current and all(noninferior.values()))
    return result


def score(root):
    config = read(root, 'config.json'); settings = config['settings']
    source = arrays(root, config['source'], ['time', 'voltage', 'device_current', 'temperature', 'resistance', 'delta'])
    observations = arrays(root, config['observations'], ['observation_time', 'observation_voltage', 'observation_weights'])
    outputs = {}; seed29_rows = None
    for item in config['seeds']:
        seed = item['seed']; joint = []; native = []; devices = {}; native_devices = {}
        for method in item['methods']:
            a = arrays(root, method['path'], ['T', 'R', 'common_voltage', 'delta'])
            role = method['method']
            vn = a['common_voltage'] if method['native_equals_common'] else a['native_voltage']
            row, dev = evaluate(role, a['T'], a['R'], a['common_voltage'], a['delta'], source, observations, settings)
            joint.append(row); devices[role] = dev
            nr, nd = evaluate(role+'_native', a['T'], a['R'], vn, a['delta'], source, observations, settings)
            native.append(nr); native_devices[role] = nd
        vsource = source_common_rc(source['resistance'], settings)
        source_label = 'known_parameter_forward_common_RC'
        sr, sd = evaluate(source_label, source['temperature'], source['resistance'], vsource,
                          source['delta'], source, observations, settings)
        joint.append(sr); devices[source_label] = sd
        sn, _ = evaluate('known_parameter_forward_native', source['temperature'], source['resistance'],
                         source['voltage'], source['delta'], source, observations, settings)
        native.append(sn)
        lookup = {row['method']: row for row in joint}
        if seed == 29:
            seed29_rows = lookup.copy()
        elif seed == 43:
            if seed29_rows is None:
                raise ValueError('Seed43 comparison requires the frozen seed29 S_dyn endpoint')
            lookup['S_dyn'] = seed29_rows['S_dyn']
        gate = gates(lookup, ['F_dyn', 'S_dyn'], settings) if item['all_valid'] else {}
        outputs[str(seed)] = dict(seed=seed, all_valid=item['all_valid'], joint_rows=joint,
                                  native_rows=native, devices=devices, native_devices=native_devices,
                                  gates=gate, joint_increment=bool(gate and all(x['passed'] for x in gate.values())))
    return outputs


def expected_projection(original):
    details = original['details']; joint = original['joint_rows']
    roles = [row['method'] for row in joint if row['method'] in ('N_dyn', 'F_dyn', 'S_dyn')]
    source_name = 'known_parameter_forward_common_RC'
    return dict(seed=original['seed'], all_valid=original['all_valid'], joint_rows=joint,
                native_rows=[details[role]['native_metrics'] for role in roles]+[details[source_name]['native_metrics']],
                devices={row['method']: details[row['method']]['devices'] for row in joint},
                native_devices={role: details[role]['native_devices'] for role in roles},
                gates=original['gates'], joint_increment=original['joint_increment'])


def compare(expected, actual, path='$', differences=None):
    """Fixed small FP64 serialization allowance; booleans/counts stay exact.

    The RMS numerical floors here are at arithmetic scales, not scientific
    noninferiority floors. Scientific inequalities are recomputed unchanged.
    """
    if differences is None:
        differences = []
    if isinstance(expected, dict):
        if not isinstance(actual, dict) or set(expected) != set(actual):
            differences.append(dict(path=path, problem='keys differ')); return differences
        for key in expected:
            compare(expected[key], actual[key], path+'.'+key, differences)
    elif isinstance(expected, list):
        if not isinstance(actual, list) or len(expected) != len(actual):
            differences.append(dict(path=path, problem='length differs')); return differences
        for i, (e, a) in enumerate(zip(expected, actual)):
            compare(e, a, path+f'[{i}]', differences)
    elif isinstance(expected, bool) or expected is None or isinstance(expected, (str, int)):
        if type(expected) is not type(actual) or expected != actual:
            differences.append(dict(path=path, expected=expected, actual=actual))
    else:
        # Main learned rows share exactly saved readouts. Tiny deviations are
        # permitted only for floating arithmetic, especially the source's
        # mathematically zero defects after the independent RC recurrence.
        unit_floor = 1e-18
        if path.endswith('_K'):
            unit_floor = 1e-12
        elif path.endswith('_V'):
            unit_floor = 1e-13
        elif path.endswith('_uA'):
            unit_floor = 1e-10
        elif path.endswith('_Hz'):
            unit_floor = 1e-8
        tolerance = max(unit_floor, 64*EPS*max(abs(float(expected)), abs(float(actual))))
        if not np.isfinite(actual) or abs(expected-actual) > tolerance:
            differences.append(dict(path=path, expected=expected, actual=actual, tolerance=tolerance))
    return differences


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--output', default='recomputed')
    args = parser.parse_args(); root = args.root.resolve()
    config = read(root, 'config.json'); outputs = score(root); mismatches = []
    for item in config['seeds']:
        seed = str(item['seed'])
        expected = expected_projection(read(root, item['expected']))
        compare(expected, outputs[seed], '$.seed'+seed, mismatches)
        save(root, args.output+f'/seed-{seed}.json', outputs[seed])
        destination = resolve(root, args.output+f'/seed-{seed}-joint.csv')
        with destination.open('w', encoding='utf-8', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(outputs[seed]['joint_rows'][0]))
            writer.writeheader(); writer.writerows(outputs[seed]['joint_rows'])
    record = dict(passed=not mismatches, seeds=[x['seed'] for x in config['seeds']],
                  mismatches=mismatches, numpy=np.__version__, python=sys.version,
                  root_only_inputs=True, recomputed_discrete_residuals=True,
                  new_hysteresis_replay=False, new_source_thermal_evolution=False,
                  neural_inference=False, neural_AD=False, training=False,
                  gate_booleans_exact=True,
                  numerical_comparison='Fixed FP64 arithmetic allowance only; no scientific gates relaxed')
    save(root, args.output+'/verification.json', record)
    print(json.dumps(record, ensure_ascii=False))
    if mismatches:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
