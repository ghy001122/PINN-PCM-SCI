"""Conditional-kernel checks on the existing non-scientific fixture only."""
import unittest
import numpy as np
import torch
from tests import test_phk_v23_lf11_joint as fixture
from pinn_pcm_sci.phk_v23_lf11 import PhysicsSampler, tensor
from pinn_pcm_sci.phk_v22r_pinn import evaluate_fields, _gradient, boundary_residuals
from pinn_pcm_sci.phk_v22r_training import PDE_SCALES, BOUNDARY_SCALES
from pinn_pcm_sci.phk_v23_lf11_diagnosis import flatten_gradient
from pinn_pcm_sci.phk_v23_lf11_joint import fixed_objective as raw_fixed
from pinn_pcm_sci.phk_v23_lf11_joint_normalization import (
    normalized_pde, normalized_boundary, fixed_objective, calibrate, electrical_block)


class NormalizedElectricalBlock(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture.JointObjectives.setUpClass()
        cls.fixture=fixture.JointObjectives()
        cls.config=cls.fixture.config;cls.data=cls.fixture.data
        cls.cal={'a_star':.07,'b_star':2.3}

    def setup_case(self):
        model=self.fixture.model();sampler=PhysicsSampler(self.data,self.config,50123,model.physics)
        return model,{'pde':sampler.interior(),'bc_ic':sampler.boundary_initial(),'seed':50123}

    @staticmethod
    def accumulated(model):
        return torch.cat([(p.grad if p.grad is not None else torch.zeros_like(p)).ravel() for p in model.parameters()])

    def test_full_normalized_gradient_equals_analytic_log_conductivity_and_normal_flux(self):
        model,pools=self.setup_case();params=list(model.parameters());pb=pools['pde']
        value=normalized_pde(model,pb)['electric']
        bundle=evaluate_fields(model,tensor(pb[0]));v=bundle.values;p=model.physics
        s=p.conductivity_temperature_gain*v['temperature']+np.log(p.conductivity_phase_ratio)*v['phase'].square()*(3-2*v['phase'])
        gs=_gradient(s,bundle.coordinates)
        residual=bundle.diagonal_second['potential']['xx']+bundle.diagonal_second['potential']['zz']
        residual=residual+(gs[:,:2]*bundle.gradients['potential'][:,:2]).sum(dim=1,keepdim=True)
        direct=torch.sum(tensor(pb[1])*tensor(pb[2])*(residual.ravel()/PDE_SCALES['electric']).square())
        torch.testing.assert_close(value,direct,rtol=1e-12,atol=1e-13)
        torch.testing.assert_close(flatten_gradient(value,params),flatten_gradient(direct,params),rtol=1e-9,atol=1e-11)
        computed=normalized_boundary(model,pools['bc_ic'][0],self.config)['bc_insulation']
        expected=next(model.parameters()).new_zeros(())
        normals={'left':(-1,0),'right':(1,0),'bottom':(0,-1),'top':(0,1)}
        for mass,sides in zip(self.config['window_masses'],pools['bc_ic'][0]):
            count=sum(len(boundary_residuals(model,tensor(q),side=side)) for side,q in sides.items())
            for side,coords in sides.items():
                if side=='top':continue
                q=tensor(coords).requires_grad_(True);values=model(q)
                g=_gradient(values[:,0:1],q)
                r=normals[side][0]*g[:,0:1]+normals[side][1]*g[:,1:2]
                if side=='bottom':r=r[q[:,0].abs()>p.heater_half_width]
                scale=BOUNDARY_SCALES['bc_electric_insulating_bottom' if side=='bottom' else 'bc_electric_insulating_side']
                expected=expected+mass*(r/scale).square().mean()/count
        torch.testing.assert_close(computed,expected,rtol=1e-12,atol=1e-13)
        torch.testing.assert_close(flatten_gradient(computed,params),flatten_gradient(expected,params),rtol=1e-9,atol=1e-11)

    def test_parent_loss_and_full_gradient_calibration_and_raw_identity(self):
        model,pools=self.setup_case();normalization=calibrate(model,self.config,self.cal,pools)
        self.assertTrue(normalization['identifiable'])
        r=normalization['raw_parent_block_loss'];n=normalization['normalized_parent_block_loss_unscaled']
        self.assertAlmostEqual(r,normalization['N_loss_scale']*n,places=13)
        self.assertAlmostEqual(normalization['G_gradient_scale']*normalization['raw_parent_block_gradient_norm'],
                               normalization['N_loss_scale']*normalization['normalized_parent_block_gradient_norm_unscaled'],places=13)
        model.zero_grad(set_to_none=True)
        expected=raw_fixed(model,self.data,self.config,self.cal,'P_U',pools);g0=self.accumulated(model)
        model.zero_grad(set_to_none=True)
        actual=fixed_objective(model,self.data,self.config,self.cal,normalization,'R',pools);g1=self.accumulated(model)
        torch.testing.assert_close(expected,actual,rtol=1e-12,atol=1e-13)
        torch.testing.assert_close(g0,g1,rtol=1e-10,atol=1e-12)

    def test_D_N_removes_all_interior_equations_and_retains_normalized_boundary(self):
        model,pools=self.setup_case();normalization={'N_loss_scale':1.7,'G_gradient_scale':.65}
        results={};grads={}
        for role in ('N','D_N'):
            model.zero_grad(set_to_none=True)
            results[role]=float(fixed_objective(model,self.data,self.config,self.cal,normalization,role,pools))
            grads[role]=self.accumulated(model)
        pde=normalized_pde(model,pools['pde'])
        difference=self.config['lambda_max']*(1.7*pde['electric']+pde['thermal']+pde['phase'])/(3*self.cal['b_star'])
        self.assertAlmostEqual(results['N']-results['D_N'],float(difference.detach()),places=12)
        torch.testing.assert_close(grads['N']-grads['D_N'],flatten_gradient(difference,list(model.parameters())),rtol=1e-9,atol=1e-11)


if __name__=='__main__':unittest.main()
