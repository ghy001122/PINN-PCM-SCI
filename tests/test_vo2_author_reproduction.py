import importlib.util
import unittest
import numpy as np
from pinn_pcm_sci.vo2_author_reproduction import P,ROOT,Hysteresis,rhs,detect_peaks


class AuthorChecks(unittest.TestCase):
    def test_constant_conductance_rc_and_zero_input(self):
        R=20000.;G=1/R;Vin=9.;h=1e-9
        tau=P.C/(1/P.RL+G);steady=Vin/(1+P.RL*G);v=0.
        for _ in range(1000):v+=h*((Vin-v)/P.RL-G*v)/P.C
        expected=steady*(1-np.exp(-1000*h/tau))
        self.assertLess(abs(v-expected),.002)
        old=v
        for _ in range(1000):
            v+=h*(-v/P.RL-G*v)/P.C
            self.assertTrue(0<v<old);old=v

    def test_author_hysteresis_and_reversal_vector(self):
        import torch
        old=torch.get_default_dtype();torch.set_default_dtype(torch.float64)
        try:
            path=ROOT/'paper/paper_revision_20260926_core/literature/model.py'
            spec=importlib.util.spec_from_file_location('pinned_author_model',path)
            module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
            author=module.VO2(2);author.initialize(324.9);ours=Hysteresis(2)
            sequence=[[325,325],[325.005,325.012],[330,333],[341,343],[340,343.004],[338,343.02],[335,331],[337,333]]
            for T in sequence:
                T=np.asarray(T,dtype=np.float64);q=torch.from_numpy(T.copy())
                author.reversal(q);ours.reversal(T)
                for k in ('delta','reversed','Tr','gr','Tpr','T_last'):
                    np.testing.assert_allclose(getattr(ours,k),getattr(author,k).numpy(),rtol=2e-12,atol=2e-10)
                np.testing.assert_allclose(ours.resistance(T),1000*author.R(q).numpy(),rtol=2e-12,atol=2e-8)
            # The resistance clamp applies to its evaluation, never to T itself.
            T=np.array([300.,375.]);before=T.copy();ours.resistance(T)
            np.testing.assert_array_equal(T,before)
        finally:torch.set_default_dtype(old)

    def test_energy_and_mutual_exchange(self):
        v=np.array([7.,5.]);T=np.array([337.,329.]);R=np.array([4000.,17000.]);Vin=np.array([11.,9.4])
        dv,dT,Id,Il,q=rhs(v,T,R,Vin,.12)
        np.testing.assert_allclose(Il,Id+P.C*dv,rtol=0,atol=1e-18)
        self.assertAlmostEqual(float(q.sum()),0.,15)
        power=float(np.sum(Vin*Il-P.RL*Il**2-(1-.12)*P.Sth*(T-P.Tbase)))
        self.assertAlmostEqual(float(np.sum(P.C*v*dv+P.Cth*dT)),power,14)
        h=1e-9;vn=v+h*dv;Tn=T+h*dT
        delta=np.sum(.5*P.C*(vn*vn-v*v)+P.Cth*(Tn-T))
        np.testing.assert_allclose(delta,h*power+np.sum(.5*P.C*h*h*dv*dv),rtol=2e-10,atol=1e-23)

    def test_peak_spacing_no_alignment(self):
        t=np.arange(11)*.1e-6
        I=np.array([0,0,2,0,3,0,0,0,2,0,0])*.001
        np.testing.assert_array_equal(detect_peaks(t,I),[4])


if __name__=='__main__':unittest.main()
