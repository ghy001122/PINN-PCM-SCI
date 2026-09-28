import inspect
import unittest
import numpy as np
from scripts.run_voltage_circuit_screen import (observation_times,experimental_indices,predict,
    prediction_charge,trap_weights,metrics,circuit_checks,decomposition,charge_accounting,
    peak_matches,branch_eligibility,allowed_experimental_member)

class CircuitScreenTests(unittest.TestCase):
    def test_sampling_endpoints(self):
        t=observation_times(0.,20e-6)
        self.assertEqual(len(t),197)
        self.assertEqual(t[-1],20e-6)
        self.assertAlmostEqual((t[-1]-t[-2])*1e9,32.,places=8)
        idx=experimental_indices(31250)
        self.assertEqual(len(idx),978)
        self.assertEqual(idx[-1]-idx[-2],17)

    def test_linear_constant_and_units(self):
        t=np.linspace(0,20e-6,21);query=np.linspace(0,20e-6,101)
        values=np.column_stack([2+1e5*t,np.full(len(t),3.)])
        for scale in [1e-6,1.]:
            out=predict(t,values,[9.,10.],12000.,1.45e-10,query,scale)
            np.testing.assert_allclose(out['voltage'][:,0],2+1e5*query,rtol=2e-14,atol=2e-14)
            np.testing.assert_allclose(out['voltage_derivative'],np.tile([1e5,0.],(len(query),1)),rtol=2e-13,atol=1e-7)
            ql,qd=prediction_charge(out,0,20e-6,[9.,10.],12000.,1.45e-10)
            expected=((np.array([9.,10.])*20e-6)-np.array([6e-5,6e-5]))/12000
            np.testing.assert_allclose(ql,expected,rtol=1e-13)
            np.testing.assert_allclose(qd,expected-1.45e-10*np.array([2.,0.]),rtol=1e-13)
        with self.assertRaises(ValueError):predict(t,values,[9,10],12000,1e-10,[-1e-6])
        self.assertEqual(set(inspect.signature(predict).parameters),{'obs_time','obs_voltage','source_voltage','resistance','capacitance','query_time','time_scale'})

    def test_kcl_decomposition_and_charge(self):
        t=np.arange(31)*1e-9;v=1+1e6*t;c=1e-10;rl=12000.;vin=9.
        load=(vin-v)/rl;cap=np.full(len(t),c*1e6);device=load-cap
        f,k,checks=circuit_checks(t,v,device,load,cap,vin,rl,c,64.)
        self.assertTrue(checks['pass'])
        pv=v+.002;pd=np.full(len(t),1.002e6);pi=(vin-pv)/rl-c*pd
        d=decomposition(t,v,device,pv,pd,pi,f,k,rl,c,64.)
        self.assertTrue(d['pass'])
        ch=charge_accounting(t,v,device,vin,rl,c,k,64.)
        self.assertTrue(ch['pass'])
        self.assertAlmostEqual(ch['trap_minus_left_C'],1e-9*(device[-1]-device[0])/2,places=25)
        wrong=device.copy();wrong[5]+=1e-5
        _,_,bad=circuit_checks(t,v,wrong,load,cap,vin,rl,c,64.)
        self.assertFalse(bad['pass'])
        # Initially zero device current is cancellation of nonzero load and C*dV/dt.
        v=1e6*t;vin=1.2;load=(vin-v)/rl;device=load-cap
        f,k,_=circuit_checks(t,v,device,load,cap,vin,rl,c,64.)
        pv=v.copy();pd=np.full(len(t),1e6*(1+1e-10));pi=(vin-pv)/rl-c*pd
        self.assertTrue(decomposition(t,v,device,pv,pd,pi,f,k,rl,c,64.)['pass'])

    def test_endpoints_weight_and_joint(self):
        t=np.array([0.,1.,3.]);np.testing.assert_allclose(trap_weights(t),[1/6,1/2,1/3])
        error=np.array([0.,0.,3e-3]);m=metrics(t,error,np.zeros(3))
        self.assertAlmostEqual(m['MSE_A2'],3e-6)
        mse=(metrics(t,np.ones(3)*1e-3,np.zeros(3))['MSE_A2']+metrics(t,np.ones(3)*3e-3,np.zeros(3))['MSE_A2'])/2
        self.assertAlmostEqual(np.sqrt(mse),np.sqrt(5)*1e-3)

    def test_peak_matching_missing_and_single(self):
        a=np.array([1,2,3])*1e-6;b=np.array([2.05,3.02])*1e-6
        pairs,unr,unp=peak_matches(a,b)
        self.assertEqual(pairs,[(1,0),(2,1)])
        self.assertEqual(unr,[0]);self.assertEqual(unp,[])
        self.assertEqual(peak_matches([1e-6],[1.2e-6])[0],[(0,0)])
        self.assertEqual(peak_matches([1e-6],[1.4e-6])[0],[])
        self.assertEqual(peak_matches([1e-6],[.9e-6,1.1e-6])[0],[(0,0)])

    def test_legal_branches_and_allowlist(self):
        q=dict(legal_voltage=True,interval_drive=True,load_resistance=True,equivalent_topology=True,
               capacitance_known=False,independent_load_measurement=True)
        self.assertEqual(branch_eligibility(q),{'predict_load':True,'score_load':True,'predict_device':False,'score_device':False})
        q['independent_load_measurement']=False
        self.assertFalse(branch_eligibility(q)['score_load'])
        q['legal_voltage']=False;self.assertFalse(branch_eligibility(q)['predict_load'])
        config={'experimental_development_allowlist':['dev.csv'],'sealed_member':'sealed.csv'}
        self.assertTrue(allowed_experimental_member('dev.csv',config))
        self.assertFalse(allowed_experimental_member('sealed.csv',config))

if __name__=='__main__':unittest.main()
