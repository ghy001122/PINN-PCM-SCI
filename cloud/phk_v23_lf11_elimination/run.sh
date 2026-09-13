#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")/../.."
export PYTHONPATH="$PWD"
PYTHON_BIN="${LF11_PYTHON:-/root/autodl-tmp/envs/pinn-pcm-sci-py311/bin/python}"
RUN_ROOT="$PWD/outputs/runs/20260913-lf11-electrical-elimination"
"$PYTHON_BIN" -c 'import torch; assert torch.cuda.is_available(), "CUDA required for this deployment"; assert torch.__version__.split("+")[0] == "2.5.1", "retain the validated optimizer implementation"'
"$PYTHON_BIN" -m pinn_pcm_sci.phk_v23_lf11_elimination_predict check --device cuda:0
for role in D_E P_E; do
  "$PYTHON_BIN" -m pinn_pcm_sci.phk_v23_lf11_elimination train --role "$role" --device cuda:0
  "$PYTHON_BIN" -m pinn_pcm_sci.phk_v23_lf11_elimination_predict predict --role "$role" --device cuda:0
done
"$PYTHON_BIN" -c 'from pathlib import Path; import json; p=Path("outputs/runs/20260913-lf11-electrical-elimination"); (p/"cloud-compute-finished.json").write_text(json.dumps({"status":"MAIN_PROCESSES_FINISHED_RECOVERY_AND_SHUTDOWN_REQUIRED","roles":["D_E","P_E"],"reference_read":False}))'
echo 'Recover the fixed endpoints and own predictions, then shut down and confirm the actual instance before reference evaluation.'
