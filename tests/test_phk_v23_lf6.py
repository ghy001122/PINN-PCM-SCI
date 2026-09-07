from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest import mock

import numpy as np
import torch

from pinn_pcm_sci.phk_v22r_training import _checkpoint_payload, load_case_physics
from pinn_pcm_sci.phk_v23_lf1 import build_range_preserving_model
from pinn_pcm_sci.phk_v23_lf3 import T0_STAGE, TASK_ID as LF3_TASK_ID, build_training_config
from pinn_pcm_sci.phk_v23_lf6 import (
    DEV_M,
    DEV_R,
    DEV_U,
    EndpointBatch,
    array_sha256,
    endpoint_logit_loss,
    execute_p0_only_prestep_engineering_retry,
    load_contracts,
    mechanism_outcome,
    p0_preservation_gate,
    safety_gate,
    select_p0_candidate,
    semantic_ledger_sha256,
    strict_gate,
    _load_bound_model,
    verify_development_artifact_lock,
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


class LF6InheritedCheckpointTests(unittest.TestCase):
    def _checkpoints(self, root: Path, *, structural_drift: bool = False) -> tuple[Path, Path, object, object]:
        config = build_training_config("cpu")
        physics, physics_program_sha256, physics_object_sha256 = load_case_physics(config.case_control)
        initial_model = build_range_preserving_model(physics=physics, config=config).to(dtype=torch.float64)
        initial_optimizer = torch.optim.Adam(initial_model.parameters(), lr=1.0e-3)
        initial_payload = _checkpoint_payload(
            model=initial_model, optimizer=initial_optimizer, config=config, update=1200,
            program_contract_sha256="0" * 64, method_contract_sha256="1" * 64,
            physical_program_sha256=physics_program_sha256, physical_object_sha256=physics_object_sha256,
        )
        initial_payload["lf3"] = {
            "task_id": LF3_TASK_ID, "stage": T0_STAGE, "global_optimizer_step": 1200,
        }
        initial = root / "lf3-t0.pt"
        torch.save(initial_payload, initial)

        for field in ("potential", "temperature"):
            initial_model.encoders[field].requires_grad_(False)
            initial_model.heads[field].requires_grad_(False)
        phase_parameters = tuple(initial_model.encoders["phase"].parameters()) + tuple(initial_model.heads["phase"].parameters())
        selected_payload = _checkpoint_payload(
            model=initial_model, optimizer=torch.optim.Adam(phase_parameters, lr=1.0e-3),
            config=config, update=400, program_contract_sha256="0" * 64,
            method_contract_sha256="1" * 64, physical_program_sha256=physics_program_sha256,
            physical_object_sha256=physics_object_sha256,
        )
        if structural_drift:
            selected_payload["architecture"]["parameter_count"] += 1
        selected = root / "selected.pt"
        torch.save(selected_payload, selected)
        return initial, selected, physics, config

    def test_phase_only_checkpoint_loads_for_p0_and_restores_vt_trainability(self):
        with tempfile.TemporaryDirectory() as temporary:
            initial, selected, physics, config = self._checkpoints(Path(temporary))
            model, _ = _load_bound_model(
                selected, expected_sha256=hashlib.sha256(selected.read_bytes()).hexdigest().upper(),
                initial_checkpoint=initial, physics=physics, config=config, device=torch.device("cpu"),
            )
            self.assertTrue(all(parameter.requires_grad for field in ("potential", "temperature") for module in (model.encoders[field], model.heads[field]) for parameter in module.parameters()))

    def test_real_structural_architecture_drift_is_still_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            initial, selected, physics, config = self._checkpoints(Path(temporary), structural_drift=True)
            with self.assertRaisesRegex(PermissionError, "architecture drift"):
                _load_bound_model(
                    selected, expected_sha256=hashlib.sha256(selected.read_bytes()).hexdigest().upper(),
                    initial_checkpoint=initial, physics=physics, config=config, device=torch.device("cpu"),
                )


class LF6P0OnlyRecoveryTests(unittest.TestCase):
    def _locked_root(self, root: Path) -> Path:
        artifacts = {}
        for prefix, folder in (("DEV_U", "dev_u"), ("DEV_R", "dev_r")):
            directory = root / folder
            directory.mkdir()
            for role, name in (("telemetry", "telemetry.jsonl"), ("batch_ledger", "batch_ledger.jsonl"), ("checkpoint", "checkpoint.pt"), ("prediction", "prediction.npz"), ("gate", "gate.json"), ("exit", "exit.json")):
                path = directory / name
                path.write_bytes(f"{prefix}:{role}".encode("ascii"))
                artifacts[f"{prefix}_{role}"] = {
                    "path": path.relative_to(root).as_posix(), "size_bytes": path.stat().st_size,
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest().upper(),
                }
        (root / "p0").mkdir()
        lock = root / "recovery_manifest.json"
        lock.write_text(json.dumps({
            "schema_id": "phk-v23-lf6-development-artifact-lock-v1", "task_id": "PHK_V23_LF6_EVENT_FRONTIER_RANK_BAND_AND_SAFETY_GATED_PHYSICS_PILOT_EXECUTE",
            "development_source_identity": "LF6-BUNDLE-" + "A" * 64,
            "continuation_source_identity": "LF6-BUNDLE-" + "B" * 64,
            "remote_local_match": {"status": "VERIFIED_EXACT_MATCH", "basis": "OUTPUT_ROOT_RELATIVE_PATH_SIZE_SHA256", "artifact_count": 12},
            "artifacts": artifacts, "p0_prestep": {"directory_exists": True, "directory_empty": True, "optimizer_updates": 0},
        }), encoding="utf-8")
        return lock

    def test_recovery_lock_requires_all_twelve_exact_artifacts_and_empty_zero_step_p0(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            lock = self._locked_root(root)
            payload = verify_development_artifact_lock(root, lock, continuation_source_identity="LF6-BUNDLE-" + "B" * 64)
            self.assertEqual(len(payload["artifacts"]), 12)
            (root / "dev_r/gate.json").write_bytes(b"drift")
            with self.assertRaisesRegex(PermissionError, "artifact.*drift"):
                verify_development_artifact_lock(root, lock, continuation_source_identity="LF6-BUNDLE-" + "B" * 64)

    def test_recovery_lock_rejects_nonempty_or_missing_p0_before_any_update(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            lock = self._locked_root(root)
            (root / "p0/unexpected").write_bytes(b"0")
            with self.assertRaisesRegex(PermissionError, "P0 prestep"):
                verify_development_artifact_lock(root, lock, continuation_source_identity="LF6-BUNDLE-" + "B" * 64)

    def test_p0_only_path_selects_recovered_dev_r_without_rerunning_development_or_constructing_optimizer(self):
        baseline = _audit(); baseline["weighted_errors"] = {"potential": 1e-3, "temperature": 1e-3, "phase": 1e-3}
        dev_m = _audit(timing1=0.010533333333333339, timing2=0.004999999999999893, phase=0.0012096258776594536)
        dev_r = _audit(timing1=0.010533333333333339, timing2=0.0018, phase=0.0011832624059166495)
        false_gate = {"passed": False}; true_gate = {"passed": True}
        arms = {
            DEV_U: {"audit": _audit(), "safety_gate": false_gate, "strict_gate": false_gate, "numerical_valid": True, "executed_updates": 400},
            DEV_R: {"audit": dev_r, "safety_gate": true_gate, "strict_gate": false_gate, "numerical_valid": True, "executed_updates": 400},
        }
        qualification = {"partition_sha256": "PARTITION", "lf1_b0_full_medium_audit": baseline, "dev_m_full_medium_audit": dev_m, "dev_m_input_valid": True}
        contracts = {"data": {"LF4_DEV_M": {"sha256": "0" * 64}, "materialized_ledger": {"semantic_sha256": "1" * 64}}}
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); (root / "p0").mkdir()
            checkpoints = {DEV_U: root / "dev_u/checkpoint.pt", DEV_R: root / "dev_r/checkpoint.pt"}
            for checkpoint in checkpoints.values():
                checkpoint.parent.mkdir(); checkpoint.write_bytes(b"fixed-development-endpoint")
            with (
                mock.patch("pinn_pcm_sci.phk_v23_lf6.load_contracts", return_value=contracts),
                mock.patch("pinn_pcm_sci.phk_v23_lf6.read_cpu_qualification", return_value=qualification),
                mock.patch("pinn_pcm_sci.phk_v23_lf6.torch.cuda.is_available", return_value=True),
                mock.patch("pinn_pcm_sci.phk_v23_lf6.torch.cuda.get_device_name", return_value="Tesla V100-PCIE-32GB"),
                mock.patch("pinn_pcm_sci.phk_v23_lf6.torch.cuda.manual_seed_all"),
                mock.patch("pinn_pcm_sci.phk_v23_lf6.build_training_config", return_value=SimpleNamespace(case_control="FULL")),
                mock.patch("pinn_pcm_sci.phk_v23_lf6.load_case_physics", return_value=(object(), "2" * 64, "3" * 64)),
                mock.patch("pinn_pcm_sci.phk_v23_lf6.load_medium_dataset", return_value=SimpleNamespace(partition_sha256="PARTITION")),
                mock.patch("pinn_pcm_sci.phk_v23_lf6.MaterializedLedger", return_value=SimpleNamespace(streams={})),
                mock.patch("pinn_pcm_sci.phk_v23_lf6._load_recovered_development_arms", return_value=(arms, checkpoints, "LF6-BUNDLE-" + "A" * 64)),
                mock.patch("pinn_pcm_sci.phk_v23_lf6._run_development_arm") as development_runner,
                mock.patch("pinn_pcm_sci.phk_v23_lf6._load_bound_model", side_effect=RuntimeError("P0_PRE_OPTIMIZER_PROBE")) as selected_loader,
                mock.patch("pinn_pcm_sci.phk_v23_lf6.torch.optim.Adam") as optimizer,
            ):
                with self.assertRaisesRegex(RuntimeError, "P0_PRE_OPTIMIZER_PROBE"):
                    execute_p0_only_prestep_engineering_retry(
                        output_root=root, medium_carrier=root / "medium.npz", initial_checkpoint=root / "lf3.pt",
                        materialized_ledger=root / "ledger.npz", dev_m_checkpoint=root / "dev_m.pt",
                        cpu_qualification_path=root / "qualification.json", device_name="cuda:0",
                        source_identity="LF6-BUNDLE-" + "B" * 64, development_artifact_lock_path=root / "recovery_manifest.json",
                    )
            development_runner.assert_not_called()
            optimizer.assert_not_called()
            self.assertEqual(selected_loader.call_args.args[0], checkpoints[DEV_R])


if __name__=="__main__": unittest.main()
