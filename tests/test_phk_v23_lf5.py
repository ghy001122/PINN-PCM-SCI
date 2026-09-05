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
from pinn_pcm_sci.phk_v23_lf4 import load_contracts as load_lf4_contracts
from pinn_pcm_sci.phk_v23_lf5 import (
    PHASE_MSE_MAXIMUM,
    TEMPORAL_POOL_NAMES,
    TemporalEdgeDataset,
    TemporalEdgeStream,
    build_training_config,
    load_contracts,
    p0_preservation_gate,
    precompute_temporal_stream_identity,
    read_cpu_qualification,
    strict_carrier_gate,
    temporal_zero_level_terms,
)


class _MiniDataset:
    def __init__(self) -> None:
        self.time=np.asarray([0.0,0.1,0.2,0.3,0.5,1.0,1.25,1.4,1.5,1.6,1.8,2.2,2.5])
        self.cell_count=1; self.roi_cells=np.asarray([True]); self.partition_sha256="F"*64
        phase=np.asarray([[0.1],[0.2],[0.5],[0.8],[0.5],[0.1],[0.1],[0.2],[0.5],[0.8],[0.5],[0.1],[0.1]])
        self.fields={"phase":phase}; self.node_weights=np.full(self.time.size,1.0/self.time.size)
        self.coordinates=np.column_stack((np.zeros(self.time.size),np.zeros(self.time.size),self.time))


class _LogitModel(torch.nn.Module):
    def __init__(self) -> None:
        super().__init__(); self.weight=torch.nn.Parameter(torch.tensor(0.1,dtype=torch.float64))
    def read_only_output_diagnostics(self, coordinates: torch.Tensor):
        latent=self.weight*coordinates[:,2:3]
        return SimpleNamespace(latents={"phase":latent})


def _audit() -> dict:
    metric={"hard_recall":0.95,"hard_precision":0.9,"hard_active_mass_ratio":1.0,"event_time_absolute_error":0.001}
    topology={"peak_roi_fraction":0.05,"peak_full_domain_fraction":0.02,"peak_outside_roi_fraction":0.0,"recovery_fraction":1.0}
    return {"all_values_finite":True,"phase_range":{"passed":True},"potential_maximum_principle":{"passed":True},"phase_maximum":0.95,"two_cycle_events":True,"event_metrics":{"cycle_1":dict(metric),"cycle_2":dict(metric)},"event_topology_hard_guard":{"passed":True,"cycles":[dict(topology),dict(topology)]},"weighted_errors":{"potential":1e-4,"temperature":1e-4,"phase":1e-4},"topology_weighted_loss":1e-4}


class LF5TemporalGeometryTests(unittest.TestCase):
    def test_first_onset_recovery_no_wrap_and_zero_endpoint_rho(self):
        edges=TemporalEdgeDataset(_MiniDataset())
        self.assertEqual(tuple(edges.pool_counts),TEMPORAL_POOL_NAMES); self.assertTrue(all(value==1 for value in edges.pool_counts.values()))
        self.assertEqual(edges.invalid_edge_fraction,0.0)
        self.assertEqual(edges.records["C1_ONSET"]["rho"][0],1.0)
        self.assertEqual(edges.records["C1_RECOVERY"]["rho"][0],0.0)
        self.assertLess(edges.records["C1_RECOVERY"]["k"][0],edges.records["C2_ONSET"]["k"][0])
        for name in TEMPORAL_POOL_NAMES: self.assertAlmostEqual(float(edges.records[name]["probability"].sum()),1.0)

    def test_teacher_secant_is_zero_and_gradient_direction_is_finite(self):
        dataset=_MiniDataset(); edges=TemporalEdgeDataset(dataset); batch=edges.full_batch()
        phase=np.clip(dataset.fields["phase"],1e-8,1-1e-8); z=np.log(phase/(1-phase)).reshape(-1)
        for offset,name in enumerate(TEMPORAL_POOL_NAMES):
            k=int(edges.records[name]["k"][0]); k1=int(edges.records[name]["k1"][0]); rho=float(edges.records[name]["rho"][0]); self.assertAlmostEqual((1-rho)*z[k]+rho*z[k1],0.0,places=14)
        physics,_,_=load_case_physics("FULL"); model=_LogitModel(); terms=temporal_zero_level_terms(model,batch,physics=physics,device=torch.device("cpu")); terms["loss"].backward(); self.assertTrue(torch.isfinite(model.weight.grad)); self.assertNotEqual(float(model.weight.grad),0.0)

    def test_temporal_stream_order_and_hash_are_frozen(self):
        contracts=load_contracts(); lf4=load_lf4_contracts(); physics,_,_=load_case_physics(build_training_config("cpu").case_control); dataset=load_medium_dataset(ROOT/lf4["data"]["training_source"]["path"],physics=physics,contracts=lf4)
        identity=precompute_temporal_stream_identity(dataset); self.assertEqual(identity["rolling_sha256"],contracts["data"]["temporal_edge_stream"]["rolling_sha256"]); self.assertEqual(identity["pool_counts"],contracts["data"]["temporal_edge_geometry"]["pool_counts"])
        with self.assertRaises(ValueError): TemporalEdgeStream(TemporalEdgeDataset(dataset)).draw(2)


class LF5GateTests(unittest.TestCase):
    def test_strict_gate_adds_calibration_and_VT_identity(self):
        audit=_audit(); baseline=_audit(); baseline["weighted_errors"]={"potential":1e-3,"temperature":1e-3,"phase":1e-3}; gate=strict_carrier_gate(audit,baseline,vt_unchanged=True); self.assertTrue(gate["passed"])
        bad=deepcopy(audit); bad["weighted_errors"]["phase"]=PHASE_MSE_MAXIMUM*1.01; self.assertFalse(strict_carrier_gate(bad,baseline,vt_unchanged=True)["passed"])

    def test_p0_preservation_and_strict_are_separate(self):
        dev=_audit(); p0=_audit(); baseline=_audit(); baseline["weighted_errors"]={"potential":1e-3,"temperature":1e-3,"phase":1e-3}; result=p0_preservation_gate(p0,dev,baseline); self.assertTrue(result["passed"]); self.assertTrue(result["strict_gate"]["passed"])
        p0["event_metrics"]["cycle_1"]["hard_recall"]=0.85; result=p0_preservation_gate(p0,dev,baseline); self.assertTrue(result["passed"]); self.assertFalse(result["strict_gate"]["passed"])

    def test_cpu_artifact_freezes_negative_mechanism_result(self):
        artifact=json.loads((ROOT/"docs/experiment/artifacts/20260905T150045Z-phk-v23-lf5-cpu-qualification.json").read_text(encoding="utf-8"))
        self.assertEqual(artifact["status"],"LF5_TZL_ALIGNMENT_NOT_SUPPORTED_CPU"); self.assertFalse(artifact["gpu_execution_authorized_by_cpu_gate"]); self.assertFalse(artifact["checks"]["both_onset_DEV_C_strictly_better_than_DEV_M"]); self.assertTrue(artifact["checks"]["DEV_M_onset_sign_aligned"])

    def test_failed_cpu_artifact_requires_explicit_user_override(self):
        artifact=ROOT/"docs/experiment/artifacts/20260905T150045Z-phk-v23-lf5-cpu-qualification.json"
        with self.assertRaises(PermissionError): read_cpu_qualification(artifact)
        payload=read_cpu_qualification(artifact,allow_user_override=True)
        self.assertTrue(payload["post_qualification_user_override"])


if __name__=="__main__": unittest.main()
