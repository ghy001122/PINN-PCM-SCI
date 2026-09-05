#!/usr/bin/env bash
set -euo pipefail

: "${LF5_SOURCE_IDENTITY:?LF5_SOURCE_IDENTITY is required}"
: "${LF5_DEPLOYMENT_ROOT:?LF5_DEPLOYMENT_ROOT is required}"
: "${LF5_OUTPUT_ROOT:?LF5_OUTPUT_ROOT is required}"

export PYTHONPATH="${LF5_DEPLOYMENT_ROOT}"
MEDIUM="${LF5_DEPLOYMENT_ROOT}/outputs/runs/20260828T-phk-v21-s1-q-04-nominal-medium/result-intent-04.npz"
CHECKPOINT="${LF5_DEPLOYMENT_ROOT}/outputs/runs/20260904T150300Z-phk-v23-lf3-phase-latent-97a5b74/checkpoint-t0-step-1200.pt"
QUALIFICATION="${LF5_DEPLOYMENT_ROOT}/docs/experiment/artifacts/20260905T150045Z-phk-v23-lf5-cpu-qualification.json"

python "${LF5_DEPLOYMENT_ROOT}/cloud/phk_v23_lf5_autodl/preflight.py" --source-identity "${LF5_SOURCE_IDENTITY}" --deployment-root "${LF5_DEPLOYMENT_ROOT}" --medium-carrier "${MEDIUM}" --initial-checkpoint "${CHECKPOINT}" --user-override-cpu-gate
python -m pinn_pcm_sci.phk_v23_lf5 --output-root "${LF5_OUTPUT_ROOT}" --medium-carrier "${MEDIUM}" --initial-checkpoint "${CHECKPOINT}" --cpu-qualification "${QUALIFICATION}" --source-identity "${LF5_SOURCE_IDENTITY}" --device cuda:0 --user-override-cpu-gate
