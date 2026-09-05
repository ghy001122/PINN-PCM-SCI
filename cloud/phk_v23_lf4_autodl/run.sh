#!/usr/bin/env bash
set -euo pipefail

: "${LF4_SOURCE_IDENTITY:?LF4_SOURCE_IDENTITY is required}"
: "${LF4_DEPLOYMENT_ROOT:?LF4_DEPLOYMENT_ROOT is required}"
: "${LF4_OUTPUT_ROOT:?LF4_OUTPUT_ROOT is required}"

export PYTHONPATH="${LF4_DEPLOYMENT_ROOT}"
MEDIUM="${LF4_DEPLOYMENT_ROOT}/outputs/runs/20260828T-phk-v21-s1-q-04-nominal-medium/result-intent-04.npz"
CHECKPOINT="${LF4_DEPLOYMENT_ROOT}/outputs/runs/20260904T150300Z-phk-v23-lf3-phase-latent-97a5b74/checkpoint-t0-step-1200.pt"
QUALIFICATION="${LF4_DEPLOYMENT_ROOT}/docs/experiment/artifacts/20260905T082728Z-phk-v23-lf4-cpu-qualification.json"

python "${LF4_DEPLOYMENT_ROOT}/cloud/phk_v23_lf4_autodl/preflight.py" --source-identity "${LF4_SOURCE_IDENTITY}" --deployment-root "${LF4_DEPLOYMENT_ROOT}" --medium-carrier "${MEDIUM}" --initial-checkpoint "${CHECKPOINT}"
python -m pinn_pcm_sci.phk_v23_lf4 --output-root "${LF4_OUTPUT_ROOT}" --medium-carrier "${MEDIUM}" --initial-checkpoint "${CHECKPOINT}" --cpu-qualification "${QUALIFICATION}" --source-identity "${LF4_SOURCE_IDENTITY}" --device cuda:0
