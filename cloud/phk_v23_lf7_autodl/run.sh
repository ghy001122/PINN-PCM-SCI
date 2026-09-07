#!/usr/bin/env bash
set -euo pipefail

: "${LF7_SOURCE_IDENTITY:?LF7_SOURCE_IDENTITY is required}"
: "${LF7_DEPLOYMENT_ROOT:?LF7_DEPLOYMENT_ROOT is required}"
: "${LF7_OUTPUT_ROOT:?LF7_OUTPUT_ROOT is required}"

export PYTHONPATH="${LF7_DEPLOYMENT_ROOT}"
EXPECTED_OUTPUT_ROOT="/root/autodl-tmp/lf7-run-20260907T144634Z"
if [[ "${LF7_OUTPUT_ROOT}" != "${EXPECTED_OUTPUT_ROOT}" ]]; then
  echo "LF7 cannot start: LF7_OUTPUT_ROOT differs from the frozen campaign root" >&2
  exit 42
fi
if [[ -e "${LF7_OUTPUT_ROOT}" ]]; then
  if [[ ! -d "${LF7_OUTPUT_ROOT}" ]] || [[ -n "$(find "${LF7_OUTPUT_ROOT}" -mindepth 1 -maxdepth 1 -print -quit)" ]]; then
    echo "LF7 cannot start: frozen output root is not an empty directory" >&2
    exit 43
  fi
else
  mkdir -p -- "${LF7_OUTPUT_ROOT}"
fi

MEDIUM="${LF7_DEPLOYMENT_ROOT}/outputs/runs/20260828T-phk-v21-s1-q-04-nominal-medium/result-intent-04.npz"
DEV_R="${LF7_DEPLOYMENT_ROOT}/outputs/runs/20260906T065434Z-phk-v23-lf6-event-frontier-pilot/dev_r/checkpoint.pt"
QUALIFICATION="${LF7_DEPLOYMENT_ROOT}/docs/experiment/artifacts/20260907T144634Z-phk-v23-lf7-cpu-qualification.json"
LEDGER="${LF7_DEPLOYMENT_ROOT}/outputs/runs/20260906T065434Z-phk-v23-lf6-event-frontier-pilot/cpu/materialized_ledger.npz"
LEDGER_MANIFEST="${LF7_DEPLOYMENT_ROOT}/outputs/runs/20260906T065434Z-phk-v23-lf6-event-frontier-pilot/cpu/materialized_ledger_manifest.json"

python "${LF7_DEPLOYMENT_ROOT}/cloud/phk_v23_lf7_autodl/preflight.py" \
  --source-identity "${LF7_SOURCE_IDENTITY}" \
  --deployment-root "${LF7_DEPLOYMENT_ROOT}" \
  --output-root "${LF7_OUTPUT_ROOT}" \
  --medium-carrier "${MEDIUM}" \
  --dev-r-checkpoint "${DEV_R}" \
  --materialized-ledger "${LEDGER}" \
  --ledger-manifest "${LEDGER_MANIFEST}" \
  --cpu-qualification "${QUALIFICATION}"

# The core runner owns the frozen scientific sequence. It must complete P0-S,
# then reload exact DEV-R and construct a fresh optimizer before P0-F.
python -m pinn_pcm_sci.phk_v23_lf7 \
  --output-root "${LF7_OUTPUT_ROOT}" \
  --medium-carrier "${MEDIUM}" \
  --initial-checkpoint "${DEV_R}" \
  --materialized-ledger "${LEDGER}" \
  --cpu-qualification "${QUALIFICATION}" \
  --source-identity "${LF7_SOURCE_IDENTITY}" \
  --device cuda:0
