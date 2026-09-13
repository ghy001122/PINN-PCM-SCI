"""One post-training common residual audit on the already frozen unlabeled pool."""
from __future__ import annotations
import json
import torch
from .phk_v23_lf11_elimination import RUN, ROOT, Experiment, SparseData, deserialize_pool
from .phk_v23_lf11 import save_json


def main():
    proof = json.loads((RUN/'compute-closure.json').read_text())
    if not proof.get('training_complete') or not proof.get('instance_shutdown_confirmed'):
        raise ValueError('finish and shut down the current cloud run first')
    target = RUN/'fixed-endpoint-unlabeled-audit.json'
    if target.exists():
        raise FileExistsError('reuse the completed audit')
    config = json.loads((RUN/'frozen-config.json').read_text())
    cal = json.loads((RUN/'calibration.json').read_text())
    pool = deserialize_pool(json.loads((RUN/'audit-pool.json').read_text()))
    data = SparseData(ROOT/config['sparse'])
    torch.set_num_threads(config['cpu_threads'])
    records = {}
    for role in ('E0', 'D_E', 'P_E'):
        path = RUN/'parent.pt' if role == 'E0' else RUN/role/'checkpoint.pt'
        checkpoint = torch.load(path, map_location='cpu', weights_only=False)
        # Evaluating the same P_E functional on every state is not retraining D_E.
        exp = Experiment(config, checkpoint['model_state_dict'], data, 'cpu', 'P_E')
        _, values = exp.objective(exp.obs.groups(), pool, cal, .1, backward=False)
        assert all(p.grad is None for p in exp.model.parameters())
        values['J_Tphi'] = (values['thermal']+values['phase'])/3
        values['weighted_terms_at_lambda_max'] = {
            'observation': values['observation']/max(cal['aE'], 1e-12),
            'boundary': .1*5*values['boundary']/max(cal['bE'], 1e-12),
            'thermal': .1*values['thermal']/(3*max(cal['bE'], 1e-12)),
            'phase': .1*values['phase']/(3*max(cal['bE'], 1e-12)),
            'initial': .1*values['initial']/max(cal['bE'], 1e-12)}
        records[role] = {'values': values, 'statistics': exp.statistics(),
                         'checkpoint_role': checkpoint['role']}
        print(json.dumps({'unlabeled_audit': role, 'values': values}), flush=True)
    save_json(target, {'status': 'COMMON_FIXED_ENDPOINT_UNLABELED_AUDIT',
        'records': records, 'pool': 'audit-pool.json', 'reference_fields_read': False,
        'parameter_gradient_evaluations': 0, 'optimizer_updates': 0,
        'objective_evaluations': 3,
        'meaning': 'Same full observations plus frozen independent unlabeled residual pool; post-training mechanism audit only, never endpoint selection or unseen validation.'})


if __name__ == '__main__':
    main()
