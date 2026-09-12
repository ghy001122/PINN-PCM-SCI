"""Targeted checks for history resumption and accepted-state stopping."""
import copy
import unittest
import torch
from pinn_pcm_sci.phk_v23_lf11_v_continue import continued_lbfgs

class ContinuationTests(unittest.TestCase):
    def test_first_accepted_gate_stops_before_optimum(self):
        p=torch.nn.Parameter(torch.tensor([4.],dtype=torch.float64))
        def obj():
            loss=(p-1).square().sum(); loss.backward(); return loss
        r,_=continued_lbfgs([p],obj,200,accepted_loss_gate=5.)
        self.assertEqual(r["termination"],"FIRST_ACCEPTED_V_FIT_GATE")
        self.assertEqual(r["evaluations"],2)
        self.assertEqual(r["accepted_steps"],1)
        self.assertEqual(float(p.detach()),3.)

    def test_nonempty_history_trial_budget_restores_every_state_tensor(self):
        p=torch.nn.Parameter(torch.tensor([3.,2.],dtype=torch.float64))
        def obj():
            loss=(p.square()*torch.tensor([1.,100.])).sum(); loss.backward(); return loss
        _,opt=continued_lbfgs([p],obj,7)
        state=copy.deepcopy(opt.state_dict()); before=p.detach().clone()
        self.assertTrue(state["state"][0]["old_dirs"])
        result,continued=continued_lbfgs([p],obj,1,optimizer_state=state)
        self.assertEqual(result["evaluations"],1)
        self.assertEqual(result["accepted_steps"],0)
        torch.testing.assert_close(p.detach(),before,rtol=0,atol=0)
        def equal(a,b):
            if torch.is_tensor(a): torch.testing.assert_close(a,b,rtol=0,atol=0)
            elif isinstance(a,dict):
                self.assertEqual(a.keys(),b.keys())
                for k in a: equal(a[k],b[k])
            elif isinstance(a,list):
                self.assertEqual(len(a),len(b))
                for x,y in zip(a,b): equal(x,y)
            else: self.assertEqual(a,b)
        equal(state,continued.state_dict())

if __name__=="__main__": unittest.main()

