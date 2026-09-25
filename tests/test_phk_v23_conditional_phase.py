"""Small manufactured interface checks; no real trajectory or reference access."""
import unittest
import numpy as np
from pinn_pcm_sci.phk_benchmark import PhkGrid,_phase_residual_and_jacobian
from pinn_pcm_sci.phk_v21_solver import solve_phase_candidate,PhkV21PhaseAlgorithm
from pinn_pcm_sci.phk_v23_conditional_phase import (phase_rhs,phase_jet,common_derivative,
    time_weights,mean_square,thermal_decision,reference_direction)
from pinn_pcm_sci.phk_v23_spatial_comparison import CellRestriction

P=dict(interface_width=.04,barrier_scale=1.,thermal_drive=6.,theta_transition=.45,
       mobility_cold=.5,mobility_hot=5.,mobility_width=.08)

class ConditionalPhaseTests(unittest.TestCase):
    def setUp(self):self.g=PhkGrid.build(nx=8,nz=4,x_min=-1,x_max=1,z_min=0,z_max=1)
    def solve(self,old,T,dt):
        return solve_phase_candidate(algorithm=PhkV21PhaseAlgorithm.LOGIT_NEWTON_ANALYTIC_JACOBIAN,
            phase_old=old,initial_guess=old,temperature=T,grid=self.g,dt=dt,coefficients=P,
            interface_width=P['interface_width'],solver={'transport_newton_residual_tolerance':1e-10},
            lower_bound=0.,upper_bound=1.)
    def test_interior_equilibrium(self):
        x=np.full(self.g.cell_count,.5);T=np.full_like(x,.45);r=self.solve(x,T,.000625)
        np.testing.assert_allclose(r.phase,x,atol=2e-15,rtol=0)
        self.assertEqual(r.output_clipping_count,0)
    def test_nonuniform_manufactured_backward_step(self):
        g=self.g;star=.35+.04*np.cos(np.pi*(g.cell_x+1)/2)*np.cos(np.pi*g.cell_z)
        T=.45+.03*g.cell_x;dt=.000625
        # Manufactured old value creates a known nonuniform endpoint; no source is added to the real solver.
        old=star-dt*phase_rhs(star,T,g,P)
        r=self.solve(old,T,dt)
        np.testing.assert_allclose(r.phase,star,atol=2e-10,rtol=0)
        defect,_=_phase_residual_and_jacobian(r.phase,phase_old=old,temperature=T,grid=g,
            dt=dt,coefficients=P,interface_width=P['interface_width'])
        self.assertLessEqual(np.max(np.abs(defect)),1e-10)
        self.assertLess(abs(float(g.cell_volumes@(g.phase_laplacian@star))),1e-13)
    def test_rhs_jets_against_independent_directional_difference(self):
        g=self.g;x=.3+.04*g.cell_x;T=.44+.02*g.cell_z;Tt=.1-.02*g.cell_x
        v,acc=phase_jet(x,T,Tt,g,P);h=1e-6
        difference=(phase_rhs(x+h*v,T+h*Tt,g,P)-phase_rhs(x-h*v,T-h*Tt,g,P))/(2*h)
        np.testing.assert_allclose(acc,difference,rtol=3e-8,atol=2e-8)
    def test_common_derivative_endpoints_and_measure(self):
        t=1.36+np.arange(1057)*.000625;u=np.column_stack((t*t,3*t+2))
        np.testing.assert_allclose(common_derivative(u),np.column_stack((2*t,np.full_like(t,3))),atol=2e-12,rtol=0)
        self.assertAlmostEqual(time_weights(t).sum(),1.)
        self.assertAlmostEqual(mean_square(np.full((len(t),2),2.),t,np.array([1.,3.])),4.)
        fine=1.36+np.arange(2113)*.0003125
        np.testing.assert_array_equal(t,fine[::2]);self.assertEqual(len(t[::4]),265)
    def test_restriction_conserves_volume_and_indicator_semantics(self):
        op=CellRestriction(16,8,8,4);x=np.arange(128,dtype=float)[None]/127
        y=op(x);self.assertAlmostEqual(float(y.mean()),float(x.mean()))
        self.assertTrue(np.all((op(x>=.5)>=0)&(op(x>=.5)<=1)))
    def test_direction_resolution_and_zero_difference_nonidentity(self):
        self.assertEqual(thermal_decision(1.,1.049,1.051)['direction'],'UNRESOLVED')
        self.assertEqual(thermal_decision(1.,.90,.901)['direction'],'WITHIN_BUDGET')
        self.assertEqual(reference_direction(1.,.99,.999)['direction'],'UNRESOLVED')
        self.assertEqual(reference_direction(1.,.8,.801)['direction'],'IMPROVES')

if __name__=='__main__':unittest.main()
