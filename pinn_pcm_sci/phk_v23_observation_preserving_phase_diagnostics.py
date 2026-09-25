"""Fixed-support necessary bound; reference use is isolated from training."""
from pathlib import Path
import importlib.util
import json
import numpy as np
from .phk_v23_b1_metrics import interval_weights

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT/'outputs/runs/20260924-observation-preserving-phase'


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def feasibility():
    RUN.mkdir(parents=True, exist_ok=True)
    target = RUN/'fixed-support-bound.json'
    if target.exists():
        raise FileExistsError('The fixed-support bound already exists; reuse it')
    archive = ROOT/'outputs/submission-rescore-20260921'
    spec = importlib.util.spec_from_file_location('frozen_phase_completion_reader', archive/'portable/readout_rescore.py')
    r = importlib.util.module_from_spec(spec); spec.loader.exec_module(r)
    manifest = read(archive/'manifest.json'); desc = manifest['protocols']['shorter']
    cfg = read(archive/desc['config'])
    physics = r.s.Physics(protocol='shorter', **desc['physics'])
    grid = r.s.geometry(archive, manifest)
    reference, _ = r.load_ref(archive, desc, 'old', grid, physics)
    b1 = ROOT/'outputs/runs/20260921-b1-second-cycle-phase-gap'
    item = next(x for x in read(b1/'readout-manifest.json')['objects'] if x['id']=='shorter/29/E')
    fields, _ = r.s.arrays(ROOT/item['prediction'])
    times = reference.time
    weights = interval_weights(times, [(1.01,2.02)])
    # Evaluate the declared gate itself. Endpoints with g=0 stay immutable.
    s = (times-1.36)/(2.02-1.36)
    gate = np.where((times>1.36)&(times<2.02), 64*s**3*(1-s)**3, 0.)
    dark = gate>0
    roi_cfg = cfg['qualification_event']['roi']; g = reference.grid
    roi = ((abs(g.cell_x)<=roi_cfg['abs_x_max']) &
           (g.cell_z>=roi_cfg['z_min']) & (g.cell_z<=roi_cfg['z_max']))
    threshold = cfg['qualification_event']['phase_threshold']
    series = dict(Ephi=np.mean((fields['phase'][:,roi]-reference.phase[:,roi])**2, axis=1),
                  S=np.mean((fields['phase']>=threshold)!=(reference.phase>=threshold), axis=1))
    answer = {}
    for key, values in series.items():
        mutable = float((weights*dark)@values)
        fixed = float((weights*~dark)@values)
        total = float(weights@values)
        np.testing.assert_allclose(mutable+fixed, total, rtol=1e-12, atol=1e-14)
        base = (total/weights.sum())**(.5 if key=='Ephi' else 1)
        ideal = (fixed/weights.sum())**(.5 if key=='Ephi' else 1)
        absolute = cfg['decision']['absolute_tolerance'][key]
        required = max(.1*base, absolute)
        answer[key] = dict(D_unnormalized_contribution=mutable, fixed_unnormalized_contribution=fixed,
            total_unnormalized_contribution=total, mutable_fraction=mutable/total, base=base,
            optimistic_lower_bound=ideal, required_reduction=required, absolute_tolerance=absolute,
            necessary_condition_passed=bool(base-ideal>=required))
    result = dict(task_id='PCM-20260924-OBSERVATION-PRESERVING-PHASE-01',
        status='FIXED_SUPPORT_NECESSARY_CONDITION_PASSED' if all(v['necessary_condition_passed'] for v in answer.values()) else 'FIXED_SUPPORT_CANNOT_MEET_PRIMARY_TARGET',
        base_prediction=item['prediction'], reference='existing original shorter reference',
        support=[1.36,2.02], window=[1.01,2.02], support_is_open=True,
        endpoint_nodes_mutable={str(t):bool(dark[np.argmin(abs(times-t))]) for t in (1.36,2.02)},
        window_duration=float(weights.sum()), mutable_time_weight=float(weights@dark), metrics=answer,
        reference_used_for='necessary feasibility bound only; no selection of support, weights or endpoint',
        model_evaluations=0, electrical_solves=0, optimizer_updates=0)
    target.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    np.savez_compressed(RUN/'fixed-support-traces.npz', time=times, weights=weights, gate=gate,
        phase_square_error=series['Ephi'], set_error=series['S'],
        reference_active=(reference.phase>=threshold).mean(1),base_active=(fields['phase']>=threshold).mean(1))
    print(json.dumps(result, allow_nan=False), flush=True)
    return result


if __name__=='__main__':
    feasibility()
