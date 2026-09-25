"""Focused checks on the actual E29 endpoint, not a manufactured substitute."""
import json
import unittest
from pathlib import Path
import numpy as np
import torch
from scipy.interpolate import BSpline
from pinn_pcm_sci.phk_v22r_pinn import _gradient
from pinn_pcm_sci.phk_v23_b1 import B1Electric
from pinn_pcm_sci.phk_v23_b1_observations import VisibleData
from pinn_pcm_sci.phk_v23_lf11_elimination_physics import fields,thermal_phase_residual,grid_for,coordinates
from pinn_pcm_sci.phk_v23_observation_preserving_phase import (
    Completion, CompletionExperiment, CompletionSampler, SplineCorrection,
    dark_gate,gate_derivatives,axis_basis,A,B)

ROOT=Path(__file__).resolve().parents[1]
OLD=ROOT/'outputs/runs/20260921-b1-second-cycle-phase-gap/seed-29'


class CompletionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(4)
        cls.c=json.loads((OLD/'frozen-config.json').read_text())
        cls.state=torch.load(OLD/'E/checkpoint.pt',map_location='cpu',weights_only=False)['model_state_dict']
        cls.data=VisibleData(ROOT/cls.c['sparse'])
        cls.cal=json.loads((OLD/'calibration.json').read_text())

    def close(self,a,b,rtol=1e-10,atol=1e-12):
        torch.testing.assert_close(a,b,rtol=rtol,atol=atol)

    def test_gate_and_visible_support(self):
        t=torch.tensor([0.,1.01,A,B,2.5],dtype=torch.float64,requires_grad=True)
        g=dark_gate(t);d=torch.autograd.grad(g.sum(),t,create_graph=True)[0]
        d2=torch.autograd.grad(d.sum(),t)[0]
        for v in (g,d,d2):self.close(v,torch.zeros_like(v),rtol=0,atol=0)
        visible=torch.as_tensor(self.data.coordinates[self.data.visible,2])
        self.assertEqual(torch.count_nonzero(dark_gate(visible)),0)
        m=Completion(self.c,self.state,'N')
        times=torch.linspace(0,2.5,1001,dtype=torch.float64)
        self.assertEqual(torch.count_nonzero(dark_gate(times)[m.physics.waveform(times)!=0]),0)
        t=torch.linspace(A+.01,B-.01,13,dtype=torch.float64,requires_grad=True)
        g,d,d2=gate_derivatives(t)
        self.close(torch.autograd.grad(g.sum(),t,create_graph=True)[0],d)
        self.close(torch.autograd.grad(d.sum(),t)[0],d2)

    def test_neural_identity_cache_and_complete_parameter_gradients(self):
        q=torch.tensor([[.05,.015,1.55],[.09,.1,1.8],[-.11,.2,1.2]],dtype=torch.float64,requires_grad=True)
        n=Completion(self.c,self.state,'N');g=Completion(self.c,self.state,'G')
        for a,b in zip(n.correction.parameters(),g.correction.parameters()):self.close(a,b,rtol=0,atol=0)
        f=n.fields(q,order=2);old=fields(n.base,q)
        self.close(f['phase'],old['phase'],rtol=0,atol=0);self.close(f['temperature'],old['temperature'],rtol=0,atol=0)
        with torch.no_grad():n.correction.net[-1].bias.fill_(.125);n.correction.net[-1].weight.fill_(.02)
        f=n.fields(q,order=2);full=n.complete_graph(q)
        dp=_gradient(full['phase'],q);lap=_gradient(dp[:,0],q)[:,0]+_gradient(dp[:,1],q)[:,1]
        self.close(f['phase_grad'],dp);self.close(f['phase_lap'],lap,rtol=1e-10,atol=2e-11)
        p=n.physics
        def residual(phase,temp,dt,lap):
            s=phase*(1-phase)
            return dt-p.mobility(temp)*(p.interface_width**2*lap-2*p.barrier_scale*s*(1-2*phase)-6*p.thermal_drive*(p.theta_transition-temp)*s)
        r=residual(f['phase'],f['temperature'],f['phase_grad'][:,2],f['phase_lap'])
        rr=residual(full['phase'],full['temperature'],dp[:,2],lap)
        self.close(r,rr)
        params=list(n.correction.parameters())
        a=torch.autograd.grad(r.square().sum(),params,retain_graph=True)
        b=torch.autograd.grad(rr.square().sum(),params)
        for x,y in zip(a,b):self.close(x,y,rtol=1e-10,atol=1e-11)
        self.assertTrue(all(not v.requires_grad for v in n.base.parameters()))

    def test_finite_observation_invariance_and_generic_control(self):
        vals=[]
        q=torch.tensor(self.data.coordinates[self.data.visible][::37],dtype=torch.float64)
        for arm in ('N','G'):
            m=Completion(self.c,self.state,arm)
            with torch.no_grad():m.correction.net[-1].bias.fill_(.125)
            f=m.fields(q);old=fields(m.base,q)
            loss=(f['delta_logit']-old['delta_logit']).square().sum()
            grad=torch.autograd.grad(loss,list(m.correction.parameters()))
            vals.append(float(loss))
            if arm=='N':
                self.close(f['phase'],old['phase'],rtol=0,atol=0)
                self.assertEqual(sum(float(x.abs().sum()) for x in grad),0)
        self.assertEqual(vals[0],0);self.assertGreater(vals[1],0)

    def small_pool(self,exp):
        sampled=CompletionSampler(self.c,exp.model.physics,exp.grid).sample()
        pairs=[next((t,p) for t,p in sampled['times'].items() if .05<t<.35),
               next((t,p) for t,p in sampled['times'].items() if A<t<B)]
        return dict(initial=sampled['initial'][:8],times={t:{**p,'cells':p['cells'][:8],
                'sides':{k:v[:2] for k,v in p['sides'].items()}} for t,p in pairs})

    def test_original_full_loss_and_restricted_gradient(self):
        n=CompletionExperiment(self.c,self.state,self.data,'N')
        pool=self.small_pool(n)
        groups={float(n.obs.times[10]):(10,1.),float(n.obs.times[-3]):(len(n.obs.times)-3,1.)}
        old=B1Electric(self.c,self.state,self.data,'cpu','P_E')
        a,parts=n.objective(groups,pool,self.cal,full=True)
        b,p2=old.objective(groups,pool,self.cal,.1)
        self.close(a,b,rtol=1e-10,atol=1e-12)
        for key in ('thermal','phase','boundary','observation','initial'):
            self.assertAlmostEqual(parts[key],p2[key],delta=max(1e-12,abs(p2[key])*1e-10))
        with torch.no_grad():n.model.correction.net[-1].bias.fill_(.1)
        n.objective(groups,pool,self.cal,backward=True,full=True)
        full=[p.grad.clone() for p in n.parameters]
        for p in n.parameters:p.grad=None
        n.objective(groups,pool,self.cal,backward=True,full=False)
        for a,p in zip(full,n.parameters):self.close(a,p.grad)
        t=next(t for t in pool['times'] if A<t<B);v=pool['times'][t]
        z=torch.zeros(n.grid.cell_count,dtype=torch.float64)
        new=n.residual(t,v,z);base=thermal_phase_residual(n.model.base,n.grid,t,v['cells'],z)
        q=coordinates(n.grid,t,cells=v['cells'],requires_grad=True)
        full=n.model.complete_graph(q);f0=fields(n.model.base,q)
        diff=.05*(_gradient(full['phase'],q)[:,2]-_gradient(f0['phase'],q)[:,2])
        self.close(new['thermal']-base['thermal'],diff,atol=2e-12)
        self.assertGreater(float(new['phase'].square().mean()),0)

    def test_generic_powered_electric_vjp(self):
        e=CompletionExperiment(self.c,self.state,self.data,'G')
        with torch.no_grad():e.model.correction.net[-1].bias.fill_(.1)
        t=1.28;v,q=e.electric(t);loss=v.square().mean()+q.square().mean()*1e-3
        grad=torch.autograd.grad(loss,e.model.correction.net[-1].bias)[0].item()
        old=e.model.correction.net[-1].bias.item();h=1e-5;values=[]
        for sign in (1,-1):
            with torch.no_grad():e.model.correction.net[-1].bias.fill_(old+sign*h)
            v,q=e.electric(t);values.append(float(v.square().mean()+q.square().mean()*1e-3))
        fd=(values[0]-values[1])/(2*h)
        self.assertGreater(abs(grad),1e-12)
        self.assertAlmostEqual(grad,fd,delta=max(2e-8,abs(fd)*2e-4))

    def test_spline_full_objective_and_finite_neural_intervention(self):
        spline=CompletionExperiment(self.c,self.state,self.data,'S');pool=self.small_pool(spline)
        groups={float(spline.obs.times[10]):(10,1.)}
        with torch.no_grad():spline.model.correction.coefficients.fill_(.1)
        spline.objective(groups,pool,self.cal,backward=True,full=True)
        full=spline.parameters[0].grad.clone();spline.parameters[0].grad=None
        spline.objective(groups,pool,self.cal,backward=True)
        self.close(full,spline.parameters[0].grad)
        gradients={};parts={};obs_grad={};phys_grad={}
        for arm in ('N','G'):
            e=CompletionExperiment(self.c,self.state,self.data,arm)
            with torch.no_grad():e.model.correction.net[-1].bias.fill_(.125)
            _,parts[arm]=e.objective(groups,pool,self.cal,backward=True)
            gradients[arm]=torch.cat([p.grad.ravel() for p in e.parameters])
            for p in e.parameters:p.grad=None
            t=next(iter(groups));v,_=e.electric(t);obs,_=e.observation(groups[t],v)
            obs.backward();obs_grad[arm]=float(torch.linalg.vector_norm(torch.cat([p.grad.ravel() for p in e.parameters])))
            for p in e.parameters:p.grad=None
            t=next(t for t in pool['times'] if A<t<B)
            r=e.residual(t,pool['times'][t],torch.zeros(e.grid.cell_count,dtype=torch.float64))
            phys=(r['thermal']/4).square().mean()+(r['phase']/5).square().mean();phys.backward()
            phys_grad[arm]=float(torch.linalg.vector_norm(torch.cat([p.grad.ravel() for p in e.parameters])))
        self.assertEqual(obs_grad['N'],0.)
        self.assertGreater(obs_grad['G'],0.)
        self.assertGreater(phys_grad['N'],1e-12)
        gap=float(torch.linalg.vector_norm(gradients['N']-gradients['G']))
        self.assertGreater(gap,1e-12)
        result=dict(status='FINITE_PARAMETER_INTERVENTION_VERIFIED',output_bias=.125,
            observation_gradient_norm=obs_grad,local_physics_gradient_norm=phys_grad,
            total_gradient_difference_norm=gap,
            gradient_cosine=float(torch.dot(gradients['N'],gradients['G'])/torch.linalg.vector_norm(gradients['N'])/torch.linalg.vector_norm(gradients['G'])),
            actual_objective_components=parts,pool='two fixed source-interface times, eight cells per time, two points per side, one existing visible observation time; not a full-pool profile or performance estimate',
            reference_read=False,optimizer_updates=0)
        out=ROOT/'outputs/runs/20260924-observation-preserving-phase/finite-intervention.json'
        out.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf-8')

    def test_spline_jets_and_coefficient_derivatives(self):
        s=SplineCorrection()
        q=torch.tensor([[.033,.022,1.53],[.314,.441,1.733],[0.,.2,0.],[0.,.2,A],[0.,.2,B]],dtype=torch.float64)
        zero=s.jet(q)
        for v in zero:self.assertEqual(torch.count_nonzero(v),0)
        with torch.no_grad():s.coefficients.copy_(torch.sin(torch.arange(7749,dtype=torch.float64))*.03)
        d,g,l=s.jet(q);eps=2e-5
        for axis in (0,1,2):
            plus=q.clone();minus=q.clone();plus[:,axis]+=eps;minus[:,axis]-=eps
            finite=(s.jet(plus)[0]-s.jet(minus)[0])/(2*eps)
            self.close(g[:2,axis],finite[:2],rtol=2e-5,atol=2e-7)
        lap=torch.zeros(2,dtype=torch.float64)
        for axis in (0,1):
            plus=q.clone();minus=q.clone();plus[:,axis]+=eps;minus[:,axis]-=eps
            lap+=(s.jet(plus)[0][:2]-2*d[:2]+s.jet(minus)[0][:2])/eps**2
        self.close(l[:2],lap,rtol=2e-5,atol=2e-5)
        self.assertEqual(torch.count_nonzero(d[2:]),0)
        # Independent dense SciPy tensor product, only for two bounded queries.
        v=q[:2].numpy();bs=[]
        for values,n,lo,hi in [(v[:,0],41,-1,1),(v[:,1],21,0,1),((v[:,2]-A)/(B-A),9,0,1)]:
            knots=np.r_[np.repeat(lo,4),np.linspace(lo,hi,n-2)[1:-1],np.repeat(hi,4)]
            bs.append(torch.tensor(BSpline(knots,np.eye(n),3)(values)))
        dense=8*dark_gate(q[:2,2])*torch.einsum('ni,nj,nk,ijk->n',*bs,s.coefficients.reshape(41,21,9))
        self.close(d[:2],dense)
        a=torch.autograd.grad(d[:2].square().sum(),s.coefficients,retain_graph=True)[0]
        b=torch.autograd.grad(dense.square().sum(),s.coefficients)[0]
        self.close(a,b)

    def test_sampling_masses_and_shared_dark_pool(self):
        m=Completion(self.c,self.state,'N');g=grid_for(m.physics)
        for fixed in (False,True):
            pool=CompletionSampler(self.c,m.physics,g).sample(fixed=fixed)
            self.assertAlmostEqual(sum(v['mass'] for v in pool['times'].values()),1.)
            self.assertAlmostEqual(sum(v['mass'] for t,v in pool['times'].items() if A<t<B),.264)
            self.assertEqual(sum(len(v['cells']) for t,v in pool['times'].items() if A<t<B),4096 if fixed else 512)


if __name__=='__main__':unittest.main(verbosity=2)
