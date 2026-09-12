"""Exact FV readout identities and no-label interpolation invariance."""
import unittest
from types import SimpleNamespace
import numpy as np
from pinn_pcm_sci.phk_benchmark import PhkGrid
from pinn_pcm_sci.phk_v23_lf11 import build_model,tensor
from pinn_pcm_sci.phk_v23_lf11_readout import readout
from pinn_pcm_sci.phk_v23_lf11_electric_trace_audit import (
    bottom_decomposition,conductivity,normalized_voltage_contact)

class ElectricAuditTests(unittest.TestCase):
    def test_signed_decomposition_matches_official_fv_readout(self):
        physics=build_model(dict(seed=17,width=8,layers=2)).physics
        grid=PhkGrid.build(nx=10,nz=5,x_min=-1,x_max=1,z_min=0,z_max=1)
        rng=np.random.default_rng(515)
        v=rng.uniform(0,.5,(3,50));t=rng.uniform(0,.1,(3,50));p=rng.uniform(0,.7,(3,50))
        u=np.array([.72,.4,.1]);overlap=grid.bottom_overlap(physics.heater_width_fraction)
        b=np.full((3,np.count_nonzero(overlap)),.6)
        d=bottom_decomposition(v,b,conductivity(t,p,physics),grid,u,overlap)
        official=readout(v,t,p,grid,u,physics)
        for k in ("bottom_current","top_current","joule_power","input_power"):
            np.testing.assert_allclose(d[k],official[k],rtol=2e-14,atol=2e-14)
        np.testing.assert_allclose(d["current_identity_error"],0,atol=1e-12)
        np.testing.assert_allclose(d["power_identity_error"],0,atol=1e-12)
        self.assertTrue(np.all(d["P_cross"]<0))

    def test_contact_endpoints_preserve_visible_voltage(self):
        physics=build_model(dict(seed=17,width=8,layers=2)).physics
        x=np.array([-.9,-.39,-.29,.31,.41,.9]);z=np.array([.01,.3,.9])
        times=np.array([0,.08,.2,.4,1.33,1.45,1.8,2.5])
        u=physics.waveform(tensor(times)).numpy()
        q=(.2+.1*z[:,None]+.05*x[None,:])
        values=u[:,None,None]*q
        data=SimpleNamespace(arrays=dict(x=x,z=z,time=times),targets=np.column_stack([values.ravel(),np.zeros(values.size),np.zeros(values.size)]))
        actual=normalized_voltage_contact(data,x,z,times,physics)
        np.testing.assert_allclose(actual,values.reshape(actual.shape),rtol=1e-14,atol=1e-14)
        boundary=normalized_voltage_contact(data,np.linspace(-physics.heater_half_width,physics.heater_half_width,101),np.array([0.]),times,physics)
        np.testing.assert_array_equal(boundary,np.zeros_like(boundary))

if __name__=="__main__": unittest.main()

