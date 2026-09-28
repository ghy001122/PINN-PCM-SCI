import inspect
import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from run_cubic_energy_comparison import predict_cs

class FixedCubicTests(unittest.TestCase):
    def test_constant_linear_cubic_and_analytic_derivative(self):
        times=np.r_[np.arange(196)*102.4e-9,20e-6]
        x=times/1e-6
        query=np.r_[np.linspace(0,20e-6,1001),times]
        u=query/1e-6
        for values,expected,derivative in [(np.full(len(x),2.),np.full(len(u),2.),np.zeros(len(u))),
                 (1+.2*x,1+.2*u,np.full(len(u),.2e6)),
                 (1+.2*x-.003*x*x+.0001*x**3,1+.2*u-.003*u*u+.0001*u**3,(.2-.006*u+.0003*u*u)*1e6)]:
            out=predict_cs(times,values,[9.],12000.,1.4534619293e-10,query)
            np.testing.assert_allclose(out['voltage'][:,0],expected,rtol=1e-13,atol=2e-14)
            np.testing.assert_allclose(out['voltage_derivative'][:,0],derivative,rtol=2e-11,atol=1e-7)
            np.testing.assert_allclose(out['device_current'],out['load_current']-out['capacitor_current'],rtol=0,atol=0)
        self.assertEqual(len(times),197)
        self.assertAlmostEqual((times[-1]-times[-2])/1e-9,32.,places=10)

    def test_endpoints_scaling_and_forbidden_extrapolation(self):
        obs=np.array([0.,.4,.9,1.4,2.])*1e-6
        values=np.c_[1.+obs/1e-6,2.+2*obs/1e-6]
        a=predict_cs(obs,values,[9.,11.],12000.,1e-10,obs)
        b=predict_cs(obs,values,[9.,11.],12000.,1e-10,obs,time_scale=1.)
        np.testing.assert_allclose(a['voltage'],values,rtol=0,atol=1e-14)
        np.testing.assert_allclose(a['voltage_derivative'],b['voltage_derivative'],rtol=1e-13)
        with self.assertRaises(ValueError):predict_cs(obs,values,[9.,11.],12000.,1e-10,[-1e-12])
        with self.assertRaises(ValueError):predict_cs(obs,values,[9.,11.],12000.,1e-10,[2.1e-6])

    def test_no_hidden_scoring_fields_in_prediction_interface(self):
        self.assertEqual(list(inspect.signature(predict_cs).parameters),
            ['obs_time','obs_voltage','source_voltage','resistance','capacitance','query_time','time_scale'])
        with self.assertRaises(TypeError):
            predict_cs([0,1,2,3],[0,1,2,3],[1],1,1,[0,1],device_current=[0,1])

if __name__=='__main__':unittest.main()
