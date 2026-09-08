#!/usr/bin/env bash
set -euo pipefail

: "${LF8_SOURCE_IDENTITY:?LF8_SOURCE_IDENTITY is required}"
: "${LF8_DEPLOYMENT_ROOT:?LF8_DEPLOYMENT_ROOT is required}"
: "${LF8_OUTPUT_ROOT:?LF8_OUTPUT_ROOT is required}"

export PYTHONPATH="${LF8_DEPLOYMENT_ROOT}"

case "${LF8_OUTPUT_ROOT}" in
  /root/autodl-tmp/lf8-run-*) ;;
  *)
    echo "LF8 cannot start: LF8_OUTPUT_ROOT is outside the frozen campaign namespace" >&2
    exit 42
    ;;
esac

if [[ -e "${LF8_OUTPUT_ROOT}" ]]; then
  if [[ ! -d "${LF8_OUTPUT_ROOT}" ]] || [[ -n "$(find "${LF8_OUTPUT_ROOT}" -mindepth 1 -maxdepth 1 -print -quit)" ]]; then
    echo "LF8 cannot start: output root is not an empty directory" >&2
    exit 43
  fi
else
  mkdir -p -- "${LF8_OUTPUT_ROOT}"
fi

MEDIUM="${LF8_DEPLOYMENT_ROOT}/outputs/runs/20260828T-phk-v21-s1-q-04-nominal-medium/result-intent-04.npz"
DEV_R="${LF8_DEPLOYMENT_ROOT}/outputs/runs/20260906T065434Z-phk-v23-lf6-event-frontier-pilot/dev_r/checkpoint.pt"
LEDGER="${LF8_DEPLOYMENT_ROOT}/outputs/runs/20260906T065434Z-phk-v23-lf6-event-frontier-pilot/cpu/materialized_ledger.npz"
LEDGER_MANIFEST="${LF8_DEPLOYMENT_ROOT}/outputs/runs/20260906T065434Z-phk-v23-lf6-event-frontier-pilot/cpu/materialized_ledger_manifest.json"
: "${LF8_CPU_QUALIFICATION:?LF8_CPU_QUALIFICATION is required}"

python "${LF8_DEPLOYMENT_ROOT}/cloud/phk_v23_lf8_autodl/preflight.py" \
  --source-identity "${LF8_SOURCE_IDENTITY}" \
  --deployment-root "${LF8_DEPLOYMENT_ROOT}" \
  --output-root "${LF8_OUTPUT_ROOT}" \
  --medium-carrier "${MEDIUM}" \
  --dev-r-checkpoint "${DEV_R}" \
  --materialized-ledger "${LEDGER}" \
  --ledger-manifest "${LEDGER_MANIFEST}" \
  --cpu-qualification "${LF8_CPU_QUALIFICATION}"

# One process owns the mandatory F* arm and any contract-authorized conditional
# schedule control. The launcher never creates a second arm or samples points.
python -m pinn_pcm_sci.phk_v23_lf8 \
  --output-root "${LF8_OUTPUT_ROOT}" \
  --medium-carrier "${MEDIUM}" \
  --initial-checkpoint "${DEV_R}" \
  --materialized-ledger "${LEDGER}" \
  --cpu-qualification "${LF8_CPU_QUALIFICATION}" \
  --source-identity "${LF8_SOURCE_IDENTITY}" \
  --device cuda:0

echo "LF8 scientific process finished. Recover and hash artifacts, verify zero training/GPU processes, then shut down the instance immediately."
