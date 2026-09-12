"""Numerical checks of the new matched objectives, without scientific updates."""
import copy
import json
from types import SimpleNamespace
import unittest

import numpy as np
import torch

from pinn_pcm_sci.phk_v23_lf11 import ROOT, SparseData, PhysicsSampler, boundary_initial_loss, pde_terms
from pinn_pcm_sci.phk_v23_lf11_followup_fit import fit_model, fit_metrics
from pinn_pcm_sci.phk_v23_lf11_joint import full_observation, batch_components, fixed_objective, boundary_components


class JointObjectives(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(2)
        cls.config = json.loads((ROOT/'configs/phk_v23/lf11_joint_sprint.json').read_text())
        cls.config.update(width=5, layers=1, interior_counts=[4]*4,
                          boundary_counts_per_side=[4]*4, initial_points=4,
                          full_observation_chunk=7, physics_chunk=5)
        q = np.array([[x,z,t] for t in (0.,.2,.7,1.5,2.) for z in (.1,.7) for x in (-.7,.1,.8)])
        cls.data = object.__new__(SparseData)
        cls.data.coordinates = q
        cls.data.targets = np.column_stack([.2*np.maximum(np.sin(q[:,2]),0), .1*q[:,1], .1+.1*q[:,1]])
        cls.data.prob = np.arange(1,len(q)+1,dtype=float); cls.data.prob /= cls.data.prob.sum()
        cls.data.endpoint_prob = ((q[:,0] == .1)&(q[:,2] > 0)).astype(float)
        cls.data.endpoint_prob /= cls.data.endpoint_prob.sum()
        cls.data.has_interface = True
        cls.data.arrays = {'cell_lower':np.empty((0,3)), 'cell_upper':np.empty((0,3))}

    def model(self):
        return fit_model(self.config, adapter=True)

    def test_full_measure_matches_existing_audit_and_chunked_gradient(self):
        model = self.model(); metrics = fit_metrics(model,self.data,self.config)
        expected=(metrics['V_normalized_rms']**2+metrics['T_normalized_rms']['all']**2+metrics['phase_logit_objective'])/3
        result=full_observation(model,self.data,self.config,backward=True,chunk=7)
        self.assertAlmostEqual(result['observation'],expected,places=13)
        first=torch.cat([(p.grad if p.grad is not None else torch.zeros_like(p)).flatten() for p in model.parameters()])
        model.zero_grad(set_to_none=True)
        full_observation(model,self.data,self.config,backward=True,chunk=1000)
        second=torch.cat([(p.grad if p.grad is not None else torch.zeros_like(p)).flatten() for p in model.parameters()])
        torch.testing.assert_close(first,second,rtol=1e-10,atol=1e-12)

    def test_matched_differences_reproduce_original_bc_pde_scales(self):
        model=self.model(); sampler=PhysicsSampler(self.data,self.config,617,model.physics)
        pb=sampler.interior(); bc_ic=sampler.boundary_initial()
        idx,ng=self.data.indices(np.random.default_rng(3),32)
        cal={'a_star':.07,'b_star':2.3}
        vals={}
        for role in ('D_I','D_B','P_U'):
            c,_=batch_components(model,self.data,self.config,cal,role,230,idx,ng,pb,bc_ic)
            vals[role]=float(sum(c.values()).detach())
        bc,ic=boundary_initial_loss(model,*bc_ic,self.config,'cpu')
        pde,_=pde_terms(model,pb,'cpu')
        self.assertAlmostEqual(vals['D_B']-vals['D_I'],float((.1*5*bc/2.3).detach()),places=12)
        self.assertAlmostEqual(vals['P_U']-vals['D_B'],float((.1*sum(pde.values())/(3*2.3)).detach()),places=12)
        self.assertAlmostEqual(float(sum(boundary_components(model,bc_ic[0],self.config).values()).detach()),float(bc.detach()),places=12)

    def test_fixed_complete_loss_gradient_direction(self):
        model=self.model(); sampler=PhysicsSampler(self.data,self.config,819,model.physics)
        pools={'pde':sampler.interior(),'bc_ic':sampler.boundary_initial()}
        cal={'a_star':.07,'b_star':2.3}
        params=list(model.parameters()); model.zero_grad(set_to_none=True)
        fixed_objective(model,self.data,self.config,cal,'P_U',pools)
        g=torch.cat([(p.grad if p.grad is not None else torch.zeros_like(p)).flatten() for p in params]); original=[p.detach().clone() for p in params]
        torch.manual_seed(99); d=torch.randn_like(g); d/=d.norm(); h=1e-5
        def shift(scale):
            offset=0
            with torch.no_grad():
                for p,initial in zip(params,original):
                    p.copy_(initial+scale*d[offset:offset+p.numel()].reshape_as(p)); offset+=p.numel()
            return float(fixed_objective(model,self.data,self.config,cal,'P_U',pools,backward=False))
        finite_difference=(shift(h)-shift(-h))/(2*h); shift(0)
        self.assertAlmostEqual(finite_difference,float(g@d),delta=1e-6*max(1.,abs(finite_difference)))


if __name__ == '__main__':
    unittest.main()
