#!/usr/bin/env bash
set -euo pipefail

: "${LF6_SOURCE_IDENTITY:?LF6_SOURCE_IDENTITY is required}"
: "${LF6_DEPLOYMENT_ROOT:?LF6_DEPLOYMENT_ROOT is required}"
: "${LF6_OUTPUT_ROOT:?LF6_OUTPUT_ROOT is required}"
: "${LF6_ALLOW_DEV_M_FALLBACK_INPUT:?LF6_ALLOW_DEV_M_FALLBACK_INPUT must record the explicit user decision}"

if [[ "${LF6_ALLOW_DEV_M_FALLBACK_INPUT}" != "1" ]]; then
  echo "LF6 cannot start: exact DEV-M fallback is required by carrier selection but needs explicit cloud-input authorization" >&2
  exit 42
fi

export PYTHONPATH="${LF6_DEPLOYMENT_ROOT}"
MEDIUM="${LF6_DEPLOYMENT_ROOT}/outputs/runs/20260828T-phk-v21-s1-q-04-nominal-medium/result-intent-04.npz"
INITIAL="${LF6_DEPLOYMENT_ROOT}/outputs/runs/20260904T150300Z-phk-v23-lf3-phase-latent-97a5b74/checkpoint-t0-step-1200.pt"
DEV_M="${LF6_DEPLOYMENT_ROOT}/outputs/runs/20260905T102817Z-phk-v23-lf4-interface-band-5dbde1d/checkpoint-dev-m-interface-band-mse-step-400.pt"
QUALIFICATION="${LF6_DEPLOYMENT_ROOT}/docs/experiment/artifacts/20260906T065434Z-phk-v23-lf6-cpu-qualification.json"
LEDGER="${LF6_DEPLOYMENT_ROOT}/outputs/runs/20260906T065434Z-phk-v23-lf6-event-frontier-pilot/cpu/materialized_ledger.npz"
LEDGER_MANIFEST="${LF6_DEPLOYMENT_ROOT}/outputs/runs/20260906T065434Z-phk-v23-lf6-event-frontier-pilot/cpu/materialized_ledger_manifest.json"

python "${LF6_DEPLOYMENT_ROOT}/cloud/phk_v23_lf6_autodl/preflight.py" \
  --source-identity "${LF6_SOURCE_IDENTITY}" \
  --deployment-root "${LF6_DEPLOYMENT_ROOT}" \
  --medium-carrier "${MEDIUM}" \
  --initial-checkpoint "${INITIAL}" \
  --dev-m-checkpoint "${DEV_M}" \
  --materialized-ledger "${LEDGER}" \
  --ledger-manifest "${LEDGER_MANIFEST}" \
  --cpu-qualification "${QUALIFICATION}" \
  --allow-dev-m-fallback-input

python -m pinn_pcm_sci.phk_v23_lf6 \
  --output-root "${LF6_OUTPUT_ROOT}" \
  --medium-carrier "${MEDIUM}" \
  --initial-checkpoint "${INITIAL}" \
  --dev-m-checkpoint "${DEV_M}" \
  --materialized-ledger "${LEDGER}" \
  --cpu-qualification "${QUALIFICATION}" \
  --source-identity "${LF6_SOURCE_IDENTITY}" \
  --device cuda:0
