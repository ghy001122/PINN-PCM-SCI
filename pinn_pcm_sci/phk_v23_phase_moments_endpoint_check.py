"""Check the actually used quadrature order at locked endpoints, before scoring.

The required 16/32 audit cannot by itself establish agreement with the training
order. This bounded read adds one order-8 phase value/gradient pass on the same
independent panel pool per endpoint. No optimizer, new sampling, labels or
electrical solves; original metrics and prescribed 16/32 flags stay unchanged.
"""
import gc
import json
import torch
from .phk_v23_lf11 import ROOT, save_json
from .phk_v23_lf11_followup_fit import fit_model
from .phk_v23_lf11_elimination_physics import grid_for
from .phk_v23_phase_moments import ARMS, quadrature_comparison
from .phk_v23_phase_moments_run import read, phase_record


def main():
    run=ROOT/'outputs/runs/20260923-relative-phase-moments'
    if (run/'endpoint-used-order-audit.json').exists():
        raise FileExistsError('Reuse the completed used-order audit')
    assert not (run/'scoring/results.json').exists(), 'Perform this before reference scoring'
    assert read(run/'all-endpoints-locked.json')['status']=='ALL_EIGHT_FIXED_ENDPOINTS_LOCKED'
    audit=read(run/'endpoint-audits.json');cfg=read(run/'frozen-config.json')
    assert cfg['phase_panels']['order']==8
    torch.set_num_threads(cfg['cpu_threads'])
    pool=read(run/'phase-calibration-pool.json');result={}
    for arm in ARMS:
        target=run/arm/'endpoint-order8.json'
        if target.exists():
            record=read(target)
        else:
            state=torch.load(run/arm/'checkpoint.pt',map_location='cpu',weights_only=False)['model_state_dict']
            model=fit_model(cfg,state,adapter=True)
            for p in model.heads['potential'].parameters():p.requires_grad_(False)
            grid=grid_for(model.physics,*cfg['grid'])
            record,gradients=phase_record(model,grid,pool,8,cfg['phase_logit_epsilon'])
            save_json(target,record)
            del model,gradients,state;gc.collect()
        compare=quadrature_comparison(record,audit['arms'][arm]['quadrature']['16'])
        result[arm]=dict(order8=record,comparison_8_to_16=compare,
                        all_targets_pass=all(v['passed'] for v in compare.values()))
        print(json.dumps(dict(used_order_audit=arm,all_targets_pass=result[arm]['all_targets_pass'])),flush=True)
    save_json(run/'endpoint-used-order-audit.json',dict(
        status='COMPLETE_USED_ORDER_ENDPOINT_AUDIT',arms=result,optimizer_updates=0,
        reference_read=False,electrical_forward_solves=0,electrical_adjoint_solves=0,
        phase_derivative_positions=8*8*sum(len(p['cells']) for p in pool),
        phase_endpoint_coordinate_queries=8*2*sum(len(p['cells']) for p in pool),
        low_order_device='CPU FP64',high_order_device='CUDA FP64',
        comparison_rule='Existing 1% value / 5% gradient-norm numerical tolerances; no metric or training change',
        reason='16/32 consistency alone does not test the actual order8 used in training',
        frozen_16_to_32_flags_unchanged=True))


if __name__=='__main__':main()
