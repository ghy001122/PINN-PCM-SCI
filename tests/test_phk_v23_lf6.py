from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import unittest

import numpy as np
import torch

from pinn_pcm_sci.phk_v22r_training import load_case_physics
from pinn_pcm_sci.phk_v23_lf6 import (
    DEV_M,
    DEV_R,
    DEV_U,
    EndpointBatch,
    array_sha256,
    endpoint_logit_loss,
    load_contracts,
    mechanism_outcome,
    p0_preservation_gate,
    safety_gate,
    select_p0_candidate,
    semantic_ledger_sha256,
    strict_gate,
)
from pinn_pcm_sci.phk_v23_lf6_qualification import _stable_descending_order, event_frontier_geometry


class _GeometryDataset:
    def __init__(self) -> None:
        self.time=np.asarray([0.10,0.20,1.30,1.40],dtype=np.float64); self.cell_count=10
        self.roi_cells=np.ones(10,dtype=bool)
        phase=np.full((4,10),0.1,dtype=np.float64); phase[1,3]=0.6; phase[3,7]=0.7
        self.fields={"phase":phase}
        self.window_time_masks={"W1":np.asarray([True,True,False,False]),"W3":np.asarray([False,False,True,True])}
        x=np.arange(10,dtype=np.float64); z=np.zeros(10); self.coordinates=np.column_stack((np.tile(x,4),np.tile(z,4),np.repeat(self.time,10)))
        self.targets=np.column_stack((np.zeros(40),np.zeros(40),phase.reshape(-1)))


class _LogitModel(torch.nn.Module):
    def __init__(self) -> None:
        super().__init__(); self.weight=torch.nn.Parameter(torch.tensor(0.1,dtype=torch.float64))
    def read_only_output_diagnostics(self, coordinates: torch.Tensor):
        return SimpleNamespace(latents={"phase":self.weight*torch.ones((coordinates.shape[0],1),dtype=coordinates.dtype,device=coordinates.device)})


def _audit(*, timing1:float=0.001,timing2:float=0.001,phase:float=1e-4)->dict:
    metric=lambda timing:{"hard_recall":0.95,"hard_precision":0.90,"hard_active_mass_ratio":1.0,"event_time_absolute_error":timing}
    topology={"peak_roi_fraction":0.05,"peak_full_domain_fraction":0.03,"peak_outside_roi_fraction":0.0,"recovery_fraction":1.0}
    return {"all_values_finite":True,"phase_range":{"passed":True},"potential_maximum_principle":{"passed":True},"phase_maximum":0.95,"two_cycle_events":True,"event_metrics":{"cycle_1":metric(timing1),"cycle_2":metric(timing2)},"event_topology_hard_guard":{"cycles":[dict(topology),dict(topology)],"passed":True},"weighted_errors":{"potential":1e-4,"temperature":1e-4,"phase":phase},"topology_weighted_loss":1e-4}


class LF6FrontierTests(unittest.TestCase):
    def test_stable_rank_uses_cell_index_for_ties(self):
        values=np.asarray([1.0,2.0,2.0,0.0]); cells=np.asarray([8,5,3,1])
        self.assertEqual(_stable_descending_order(values,cells).tolist(),[2,1,0,3])

    def test_brackets_contain_critical_rank_and_controls_are_equal_information(self):
        geometry=event_frontier_geometry(_GeometryDataset())
        self.assertEqual(geometry["critical_rank_one_based"],1)
        for cycle in (1,2):
            record=geometry["cycles"][f"cycle_{cycle}"]
            self.assertLess(record["n_minus"],1); self.assertGreaterEqual(record["n_plus"],1)
        for name in ("C1_PRE","C1_POST","C2_PRE","C2_POST"):
            self.assertEqual(geometry["frontier"][name].size,geometry["uniform"][name].size)
            self.assertEqual(np.intersect1d(geometry["frontier"][name],geometry["uniform"][name]).size,0)
        second=event_frontier_geometry(_GeometryDataset())
        self.assertTrue(all(np.array_equal(geometry["uniform"][name],second["uniform"][name]) for name in geometry["uniform"]))

    def test_array_and_semantic_hash_bind_name_dtype_shape_and_content(self):
        one=np.asarray([[1.0,2.0]],dtype=np.float64); two=one.copy(); two[0,0]=3.0
        h1=array_sha256("one",one); self.assertEqual(h1,array_sha256("one",one.copy())); self.assertNotEqual(h1,array_sha256("one",two)); self.assertNotEqual(h1,array_sha256("two",one))
        self.assertEqual(semantic_ledger_sha256({"one":h1}),semantic_ledger_sha256({"one":h1}))

    def test_endpoint_loss_is_equal_mean_of_four_nonempty_pools(self):
        physics,_,_=load_case_physics("FULL"); coordinates=torch.tensor([[0.0,0.1,0.2],[0.0,0.1,0.2],[0.0,0.1,1.3],[0.0,0.1,1.3]],dtype=torch.float64); targets=torch.tensor([[0.0,0.0,0.2],[0.0,0.0,0.4],[0.0,0.0,0.6],[0.0,0.0,0.8]],dtype=torch.float64)
        model=_LogitModel(); terms=endpoint_logit_loss(model,EndpointBatch(coordinates,targets,(0,1,2,3,4),DEV_R),physics=physics,device=torch.device("cpu")); self.assertTrue(torch.allclose(terms["loss"],sum(terms["pool_losses"].values())/4)); terms["loss"].backward(); self.assertTrue(torch.isfinite(model.weight.grad))

    def test_remote_runner_has_no_runtime_sobol(self):
        source=(Path(__file__).resolve().parents[1]/"pinn_pcm_sci/phk_v23_lf6.py").read_text(encoding="utf-8")
        self.assertNotIn("SobolEngine",source)


class LF6GateAndSelectionTests(unittest.TestCase):
    def setUp(self):
        self.baseline=_audit(); self.baseline["weighted_errors"]={"potential":1e-3,"temperature":1e-3,"phase":1e-3}

    def test_safety_and_strict_timing_are_distinct(self):
        audit=_audit(timing1=0.010,timing2=0.004)
        self.assertTrue(safety_gate(audit,self.baseline,vt_unchanged=True)["passed"]); self.assertFalse(strict_gate(audit,self.baseline,vt_unchanged=True)["passed"])

    def test_strict_U_precedes_R_and_safety_fallback_prefers_timing_then_mse(self):
        strict={"passed":True}; no={"passed":False}; safety={"passed":True}
        candidates={DEV_U:{"audit":_audit(),"strict_gate":strict,"safety_gate":safety,"numerical_valid":True},DEV_R:{"audit":_audit(),"strict_gate":strict,"safety_gate":safety,"numerical_valid":True},DEV_M:{"audit":_audit(),"strict_gate":no,"safety_gate":safety,"numerical_valid":True}}
        self.assertEqual(select_p0_candidate(candidates),DEV_U)
        candidates[DEV_U]["strict_gate"]=no; candidates[DEV_R]["strict_gate"]=no
        candidates[DEV_U]["audit"]=_audit(timing1=.010,timing2=.0049,phase=5e-4); candidates[DEV_R]["audit"]=_audit(timing1=.0104,timing2=.0049,phase=1e-5); candidates[DEV_M]["audit"]=_audit(timing1=.009,timing2=.004,phase=9e-4)
        self.assertEqual(select_p0_candidate(candidates),DEV_M)

    def test_arm_local_invalid_closes_attribution_but_not_valid_dev_m_fallback(self):
        no={"passed":False}; safety={"passed":True}
        candidates={DEV_U:{"audit":_audit(),"strict_gate":no,"safety_gate":safety,"numerical_valid":False},DEV_R:{"audit":_audit(),"strict_gate":no,"safety_gate":{"passed":False},"numerical_valid":True},DEV_M:{"audit":_audit(timing1=.009,timing2=.004),"strict_gate":no,"safety_gate":safety,"numerical_valid":True}}
        self.assertEqual(mechanism_outcome(candidates),"MATCHED_SCREEN_INCOMPLETE_IDENTITY_INVALID")
        self.assertEqual(select_p0_candidate(candidates),DEV_M)

    def test_mechanism_is_matched_and_p0_preservation_is_separate_from_strict(self):
        arms={DEV_U:{"numerical_valid":True,"strict_gate":{"passed":False}},DEV_R:{"numerical_valid":True,"strict_gate":{"passed":True}}}; self.assertEqual(mechanism_outcome(arms),"EVENT_FRONTIER_SUPPORTED")
        selected=_audit(); p0=deepcopy(selected); p0["event_metrics"]["cycle_1"]["event_time_absolute_error"]=0.008
        gate=p0_preservation_gate(p0,selected,self.baseline); self.assertTrue(gate["passed"]); self.assertFalse(gate["strict_gate"]["passed"])

    def test_contract_bounds_and_outcomes_are_frozen(self):
        contracts=load_contracts(); self.assertEqual(contracts["program"]["hard_limits"]["maximum_scientific_gpu_trajectories"],3); self.assertEqual(contracts["program"]["hard_limits"]["maximum_optimizer_updates"],2000); self.assertEqual(len(contracts["decision"]["machine_outcomes_and_unique_next"]),13)


if __name__=="__main__": unittest.main()
