from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from types import SimpleNamespace
import unittest

import numpy as np
import torch

from pinn_pcm_sci.phk_v22r_training import ROOT, load_case_physics
from pinn_pcm_sci.phk_v23_lf2 import load_medium_dataset
from pinn_pcm_sci.phk_v23_lf4 import (
    ARM_C, ARM_G, ARM_M, BAND_POOL_NAMES, BandStream, InterfaceBandDataset,
    band_losses, development_gate, load_contracts, mechanism_decision,
    precompute_stream_identities, select_development_arm,
)


def _audit(recall: float = 0.9, precision: float = 0.9, phase_error: float = 1.0e-3):
    metric={"hard_recall":recall,"hard_precision":precision,"hard_active_mass_ratio":1.0,"event_time_absolute_error":0.001}
    topology={"peak_roi_fraction":0.05,"peak_full_domain_fraction":0.02,"peak_outside_roi_fraction":0.0,"recovery_fraction":1.0}
    return {"all_values_finite":True,"phase_range":{"passed":True},"potential_maximum_principle":{"passed":True},"two_cycle_events":True,"phase_maximum":0.95,"event_metrics":{"cycle_1":dict(metric),"cycle_2":dict(metric)},"event_topology_hard_guard":{"passed":True,"cycles":[dict(topology),dict(topology)]},"weighted_errors":{"potential":1e-4,"temperature":1e-3,"phase":phase_error},"topology_weighted_loss":1e-3}


class _MiniDataset:
    def __init__(self):
        self.time=np.asarray([0.1,1.3]); self.cell_x=np.tile(np.arange(3,dtype=float),3); self.cell_z=np.repeat(np.arange(3,dtype=float),3); self.cell_count=9
        phase=np.zeros((2,9)); phase[:,4]=1.0; self.fields={"phase":phase}
        self.window_time_masks={"W1":np.asarray([True,False]),"W3":np.asarray([False,True])}
        self.node_weights=np.full(18,1/18); self.coordinates=np.column_stack((np.tile(self.cell_x,2),np.tile(self.cell_z,2),np.repeat(self.time,9)))
        self.targets=np.column_stack((np.zeros(18),np.zeros(18),phase.reshape(-1))); self.partition_sha256="F"*64; self.node_count=18


class _BandModel(torch.nn.Module):
    def __init__(self):
        super().__init__(); self.weight=torch.nn.Parameter(torch.tensor(0.0,dtype=torch.float64))
    def read_only_output_diagnostics(self,coordinates):
        latent=torch.ones((coordinates.shape[0],1),dtype=coordinates.dtype,device=coordinates.device)*self.weight
        return SimpleNamespace(latents={"phase":latent})


class LF4GeometryAndLossTests(unittest.TestCase):
    def test_nonperiodic_four_neighbour_two_sided_pools(self):
        band=InterfaceBandDataset(_MiniDataset())
        self.assertEqual(tuple(band.pool_counts),BAND_POOL_NAMES)
        self.assertEqual(band.pool_counts,{"C1_INNER_POSITIVE":1,"C1_OUTER_NEGATIVE":4,"C2_INNER_POSITIVE":1,"C2_OUTER_NEGATIVE":4})
        left=3
        self.assertNotIn(5,band.neighbours[left])
        self.assertEqual(set(band.neighbours[4]),{1,3,5,7})

    def test_band_stream_is_deterministic_and_m_c_coordinate_identical(self):
        band=InterfaceBandDataset(_MiniDataset()); one=BandStream(band).draw(1); two=BandStream(band).draw(1)
        self.assertTrue(torch.equal(one.coordinates,two.coordinates)); self.assertEqual(one.batch_sha256,two.batch_sha256); self.assertEqual(one.coordinates.shape[0],256)

    def test_mse_and_threshold_losses_are_exact_four_pool_means(self):
        physics,_,_=load_case_physics("FULL"); band=InterfaceBandDataset(_MiniDataset()); batch=BandStream(band).draw(1); model=_BandModel()
        losses=band_losses(model,batch,physics=physics,device=torch.device("cpu"))
        self.assertTrue(torch.allclose(losses["mse"],sum(losses["pool_mse"].values())/4))
        self.assertTrue(torch.allclose(losses["classification"],sum(losses["pool_classification"].values())/4))
        losses["classification"].backward(); self.assertIsNotNone(model.weight.grad)


class LF4FrozenIdentityAndGateTests(unittest.TestCase):
    def test_contract_and_cpu_artifact_freeze_all_streams(self):
        contracts=load_contracts(); data=contracts["data"]
        self.assertEqual(contracts["program"]["hard_limits"]["maximum_scientific_gpu_trajectories"],4)
        self.assertEqual(contracts["program"]["hard_limits"]["maximum_optimizer_updates"],2400)
        self.assertEqual(len(contracts["decision"]["machine_outcomes_and_unique_next"]),13)
        self.assertTrue(data["band_stream"]["DEV_M_DEV_C_IDENTICAL"])
        artifact=json.loads((ROOT/"docs/experiment/artifacts/20260905T082728Z-phk-v23-lf4-cpu-qualification.json").read_text(encoding="utf-8"))
        self.assertEqual(artifact["stream_identities"]["base_window_1201_1600_sha256"],data["base_stream"]["development_window_sha256"])
        self.assertEqual(artifact["stream_identities"]["band_400_sha256"],data["band_stream"]["rolling_sha256"])

    def test_full_1201_to_1600_stream_reconstructs_exact_hashes(self):
        contracts=load_contracts(); physics,_,_=load_case_physics("FULL"); medium=ROOT/contracts["data"]["training_source"]["path"]
        dataset=load_medium_dataset(medium,physics=physics,contracts=contracts); identities=precompute_stream_identities(dataset)
        self.assertEqual(identities["base_window_1201_1600_sha256"],contracts["data"]["base_stream"]["development_window_sha256"])
        self.assertEqual(identities["global_extra_400_sha256"],contracts["data"]["global_extra_stream"]["rolling_sha256"])
        self.assertEqual(identities["band_400_sha256"],contracts["data"]["band_stream"]["rolling_sha256"])

    def test_entry_strict_and_selection_are_distinct_and_deterministic(self):
        baseline=_audit(0.75,0.9,0.002); candidate=_audit(0.82,0.9,0.0021)
        entry=development_gate(candidate,baseline,vt_unchanged=True,contract=load_contracts()["decision"]); self.assertTrue(entry["passed"])
        arms={}
        for name,recall,strict in ((ARM_G,0.82,False),(ARM_M,0.89,False),(ARM_C,0.895,False)):
            audit=_audit(recall,0.9,0.001); arms[name]={"audit":audit,"gate":{"passed":True,"Rmin":recall},"strict_gate":{"passed":strict},"numerical_valid":True}
        self.assertEqual(select_development_arm(arms),ARM_M)
        decision=mechanism_decision(arms); self.assertTrue(decision["boundary_exposure_supported"]); self.assertFalse(decision["threshold_aligned_supported"])


if __name__=="__main__": unittest.main()
