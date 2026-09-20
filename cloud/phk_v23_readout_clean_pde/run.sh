#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")/../.."
export PYTHONPATH="$PWD"
export OMP_NUM_THREADS=4
export MKL_NUM_THREADS=4
export OPENBLAS_NUM_THREADS=4
PYTHON_BIN=/root/autodl-tmp/envs/pinn-pcm-sci-py311/bin/python
"$PYTHON_BIN" -c 'import torch; assert torch.cuda.is_available(); assert torch.__version__.split("+")[0] == "2.5.1"'
"$PYTHON_BIN" -m pinn_pcm_sci.phk_v23_readout_clean_pde cloud --device cuda:0
