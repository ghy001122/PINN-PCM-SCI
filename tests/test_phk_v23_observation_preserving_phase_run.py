"""Regression for the observed cloud-device propagation failure; no optimizer step."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from pinn_pcm_sci import phk_v23_observation_preserving_phase_run as runner


class TrainingPlacementTests(unittest.TestCase):
    def test_requested_device_reaches_factory_before_updates(self):
        class StopBeforeModelConstruction(Exception):pass
        calls=[]
        # Mandatory third argument catches the actual omission. The sentinel
        # stops before loading weights or constructing an optimizer.
        def factory(cfg,arm,device):
            calls.append((arm,device));raise StopBeforeModelConstruction
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/'qualification.json').write_text(json.dumps({'status':'READY_FOR_FIXED_THREE_ARM_DEVELOPMENT'}))
            with patch.object(runner,'RUN',root),patch.object(runner,'ARMS',('G',)),patch.object(runner,'inputs',factory):
                with self.assertRaises(StopBeforeModelConstruction):runner.train({},'cuda:0')
            self.assertEqual(calls,[('G','cuda:0')])
            self.assertFalse(any(root.rglob('*.pt')))
            self.assertFalse(any(root.rglob('*telemetry*')))


if __name__=='__main__':unittest.main()
