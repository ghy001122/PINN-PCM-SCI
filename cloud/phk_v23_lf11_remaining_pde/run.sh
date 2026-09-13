#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")/../.."
export PYTHONPATH="$PWD"
PYTHON_BIN=/root/autodl-tmp/envs/pinn-pcm-sci-py311/bin/python
"$PYTHON_BIN" -c 'import torch; assert torch.cuda.is_available(); assert torch.__version__.split("+")[0] == "2.5.1"'
"$PYTHON_BIN" -m pinn_pcm_sci.phk_v23_lf11_remaining_pde all --device cuda:0
