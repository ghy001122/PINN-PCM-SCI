"""Necessary coverage measure, gradient, stream and accepted-state checks."""
import copy
import unittest
import numpy as np
import torch
from pinn_pcm_sci.phk_v23_lf11_coverage import (
    RUN, load_experiment, merge_measure, accepted_lbfgs, ResourceStop, read,
)
from pinn_pcm_sci.phk_v23_lf11_elimination import TimeSampler, deserialize_pool
from pinn_pcm_sci.phk_v23_lf11_training_coupling import SoftExperiment, BLOCKS, gradient_vector


class CoverageChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(4)
        cls.folder=RUN/'seed-29'
        cls.cfg,cls.exp=load_experiment(cls.folder,'cpu')
        cls.cal=read(cls.folder/'calibration.json')
        complete=deserialize_pool(read(cls.folder/'lbfgs-pool.json'))
        t=next(iter(complete['times']))
        cls.pool=dict(initial=complete['initial'][:8],times={t:complete['times'][t]})

    def test_measure_normalization_multiplicities_and_support(self):
        exp=self.exp
        self.assertEqual(len(exp.powered_times),34)
        self.assertAlmostEqual(sum(exp.observed_measure().values()),1.)
        class Draw:
            def choice(self,*args,**kwargs):return np.array([1,1,1,2])
        old=exp.coverage_rng;exp.coverage_rng=Draw()
        actual=exp.observed_measure(True);exp.coverage_rng=old
        self.assertEqual(actual,{float(exp.powered_times[1]):.75,float(exp.powered_times[2]):.25})
        self.assertEqual(merge_measure({1.:.4,2.:.6},{1.:.75,3.:.25}),{1.:.575,2.:.3,3.:.125})
        full=deserialize_pool(read(self.folder/'lbfgs-pool.json'))
        self.assertEqual(len(full['times']),32)
        merged=merge_measure({t:v['mass'] for t,v in full['times'].items()},exp.observed_measure())
        self.assertEqual(len(merged),66);self.assertAlmostEqual(sum(merged.values()),1.)

    def test_original_random_streams_unchanged(self):
        a=np.random.default_rng(self.cfg['observation_seed']);b=np.random.default_rng(self.cfg['observation_seed'])
        sa=TimeSampler(self.cfg,self.exp.model.physics,self.exp.grid,self.cfg['sampling_seed'])
        sb=TimeSampler(self.cfg,self.exp.model.physics,self.exp.grid,self.cfg['sampling_seed'])
        for _ in range(3):
            ga=self.exp.obs.groups(a,4);pa=sa.sample()
            self.exp.observed_measure(True)
            gb=self.exp.obs.groups(b,4);pb=sb.sample()
            self.assertEqual(ga,gb);self.assertEqual(sa.rng.bit_generator.state,sb.rng.bit_generator.state)
            np.testing.assert_array_equal(pa['initial'],pb['initial'])
            self.assertEqual(set(pa['times']),set(pb['times']))

    def test_replacement_keeps_other_objective_and_gradient(self):
        exp=self.exp
        t=float(exp.powered_times[0]);groups={t:exp.obs.groups()[t]}
        exp.model.zero_grad(set_to_none=True)
        _,base=SoftExperiment.objective(exp,groups,self.pool,self.cal,.1,backward=True,
            blocks={k:1 for k in BLOCKS if k!='electric'})
        gbase=gradient_vector(exp)
        exp.model.zero_grad(set_to_none=True)
        _,new=exp.objective(groups,self.pool,self.cal,.1,backward=True,include_electric=False)
        np.testing.assert_array_equal(gradient_vector(exp),gbase)
        self.assertEqual(base,new)
        # Independent additive expression proves the old electrical term is absent.
        observed={t:1.}
        weights=merge_measure({q:v['mass'] for q,v in self.pool['times'].items()},observed)
        total=0.
        for q,w in weights.items():
            _,_,res=exp.electric(q,True)
            if res is not None:
                term=.1*w*(res/self.cfg['pde_scales']['electric']).square().mean()/(3*self.cal['bE'])
                term.backward();total+=float(term.detach())
        expected=gradient_vector(exp)
        exp.model.zero_grad(set_to_none=True)
        _,actual=exp.objective(groups,self.pool,self.cal,.1,backward=True,observed_measure=observed)
        np.testing.assert_allclose(gradient_vector(exp),expected,rtol=2e-12,atol=2e-12)
        self.assertAlmostEqual(actual['objective'],base['objective']+total,12)
        for k in ('observation','boundary','initial','thermal','phase'):
            self.assertEqual(actual[k],base[k])

    def test_lbfgs_interrupt_restore_history_and_resume(self):
        def objective(p):
            x,y=p
            value=100*(y-x*x)**2+(1-x)**2
            value.backward();return value
        p=torch.tensor([-1.2,1.],dtype=torch.float64,requires_grad=True)
        snapshots=[]
        class Halt(ResourceStop):pass
        def report(record,opt):
            snapshots.append((p.detach().clone(),copy.deepcopy(opt.state_dict()),record.copy()))
            if record['event']=='accepted' and record['accepted_steps']==2:raise Halt('test stop after accepted step')
        with self.assertRaises(Halt):
            accepted_lbfgs([p],lambda:objective(p),20,report=report)
        accepted,history,record=snapshots[-1]
        q=accepted.detach().clone().requires_grad_(True)
        trial_count=0;recovered=[]
        def broken():
            nonlocal trial_count
            trial_count+=1
            if trial_count==2:raise Halt('test interrupted trial')
            return objective(q)
        with self.assertRaises(Halt):
            accepted_lbfgs([q],broken,5,optimizer_state=history,
                report=lambda rec,opt:recovered.append((q.detach().clone(),copy.deepcopy(opt.state_dict()))))
        torch.testing.assert_close(q,accepted,rtol=0,atol=0)
        def same(a,b):
            if torch.is_tensor(a):torch.testing.assert_close(a,b,rtol=0,atol=0)
            elif isinstance(a,dict):
                self.assertEqual(a.keys(),b.keys())
                for k in a:same(a[k],b[k])
            elif isinstance(a,(tuple,list)):
                self.assertEqual(len(a),len(b))
                for x,y in zip(a,b):same(x,y)
            else:self.assertEqual(a,b)
        same(recovered[-1][1],history)
        r=accepted.detach().clone().requires_grad_(True)
        accepted_lbfgs([q],lambda:objective(q),6,optimizer_state=recovered[-1][1])
        accepted_lbfgs([r],lambda:objective(r),6,optimizer_state=history)
        torch.testing.assert_close(q,r,rtol=0,atol=0)
        rng=np.random.default_rng(960029);rng.choice(34,4);state=copy.deepcopy(rng.bit_generator.state)
        expected=rng.choice(34,4);rng.bit_generator.state=state
        np.testing.assert_array_equal(expected,rng.choice(34,4))


if __name__=='__main__':unittest.main()
