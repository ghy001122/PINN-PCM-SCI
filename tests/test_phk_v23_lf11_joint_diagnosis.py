"""Independent algebra checks for the amplitude split and outcome layers."""
import json
import unittest
import numpy as np
import torch

from tests import test_phk_v23_lf11_joint as fixtures
from pinn_pcm_sci.phk_v23_lf11 import ROOT, PhysicsSampler, tensor
from pinn_pcm_sci.phk_v23_lf11_joint import batch_components
from pinn_pcm_sci.phk_v23_lf11_joint_diagnosis import amplitude_surrogates
from pinn_pcm_sci.phk_v23_lf11_diagnosis import flatten_gradient
from pinn_pcm_sci.phk_v22r_pinn import interior_diagnostic_terms, boundary_residuals
from pinn_pcm_sci.phk_v22r_training import BOUNDARY_SCALES
from pinn_pcm_sci.phk_v23_lf11_joint_evaluate import functional_comparison, conditional_decision
from pinn_pcm_sci.phk_v23_lf11_evaluation import comparison


class DiagnosticAlgebra(unittest.TestCase):
    def test_product_rule_split_includes_original_boundary_weights(self):
        fixtures.JointObjectives.setUpClass(); fixture=fixtures.JointObjectives()
        cfg=fixture.config; data=fixture.data; model=fixture.model()
        sampler=PhysicsSampler(data,cfg,87,model.physics)
        pb,bc_ic=sampler.interior(),sampler.boundary_initial(); cal={'a_star':.07,'b_star':2.3}
        idx,ng=data.indices(np.random.default_rng(99),32)
        pieces,_=batch_components(model,data,cfg,cal,'P_U',500,idx,ng,pb,bc_ic)
        params=list(model.parameters()); amp=amplitude_surrogates(model,cfg,cal,pb,bc_ic)
        q,weight,mass=pb; terms=interior_diagnostic_terms(model,tensor(q)); sigma=terms['conductivity']
        shape={'electric':.1/(3*2.3)*torch.sum(tensor(mass*weight)[:,None]*sigma.detach().square()*(terms['electric_residual']/sigma).square()),
               'bc_insulation':torch.zeros((),dtype=torch.float64)}
        for window_mass,sides in zip(cfg['window_masses'],bc_ic[0]):
            residuals={side:boundary_residuals(model,tensor(q),side=side) for side,q in sides.items()}
            count=sum(len(v) for v in residuals.values())
            for side,values in residuals.items():
                q=tensor(sides[side]); fields=model(q)
                sigma=model.physics.conductivity(fields[:,1:2],fields[:,2:3])
                if side=='bottom': sigma=sigma[q[:,0].abs()>model.physics.heater_half_width]
                for name,r in values.items():
                    if 'insulating' in name:
                        shape['bc_insulation']=shape['bc_insulation']+.1*5*window_mass/(2.3*count)*torch.mean(
                            sigma.detach().square()*(r/sigma/BOUNDARY_SCALES[name]).square())
        for key in amp:
            original=flatten_gradient(pieces[key],params)
            split=flatten_gradient(amp[key],params)+flatten_gradient(shape[key],params)
            torch.testing.assert_close(original,split,rtol=2e-8,atol=2e-11)

    def test_function_signal_does_not_become_reconstruction_success(self):
        cfg=json.loads((ROOT/'configs/phk_v23/lf11_joint_sprint.json').read_text())
        values={k:1. for k in ('S','Ephi','ET','EV','EI','bottom_current_NRMSE','power_trace_NRMSE')}
        base={'valid':True,'metrics':values}; candidate={'valid':True,'metrics':dict(values,bottom_current_NRMSE=.8,power_trace_NRMSE=.8)}
        self.assertTrue(functional_comparison(candidate,base,cfg)['passed'])
        self.assertFalse(comparison(candidate,base,cfg['decision'])['passed'])
        for record in (base,candidate):
            record['metrics'].update(energy_error=1.,current_balance_rms=1.,power_defect_rms=1.)
        candidate['metrics']['Ephi']=1.2
        decision=conditional_decision({'D_B':base,'P_U':candidate},{'all_three_nodes_supported':False},cfg)
        self.assertTrue(decision['matched_damage']['Ephi']); self.assertFalse(decision['triggered'])


if __name__=='__main__': unittest.main()
