#!/usr/bin/env bash
set -euo pipefail

: "${LF10_SOURCE_IDENTITY:?LF10_SOURCE_IDENTITY is required}"
: "${LF10_DEPLOYMENT_ROOT:?LF10_DEPLOYMENT_ROOT is required}"
: "${LF10_OUTPUT_ROOT:?LF10_OUTPUT_ROOT is required}"
: "${LF10_CPU_QUALIFICATION:?LF10_CPU_QUALIFICATION is required}"

export PYTHONPATH="${LF10_DEPLOYMENT_ROOT}"
PYTHON_BIN="/root/autodl-tmp/envs/pinn-pcm-sci-py311/bin/python"
if [[ ! -x "${PYTHON_BIN}" ]]; then
  echo "LF10 cannot start: frozen Python runtime is unavailable: ${PYTHON_BIN}" >&2
  exit 44
fi

case "${LF10_OUTPUT_ROOT}" in
  /root/autodl-tmp/lf10-run-*) ;;
  *)
    echo "LF10 cannot start: LF10_OUTPUT_ROOT is outside the frozen campaign namespace" >&2
    exit 42
    ;;
esac

if [[ -e "${LF10_OUTPUT_ROOT}" ]]; then
  if [[ ! -d "${LF10_OUTPUT_ROOT}" ]] || [[ -n "$(find "${LF10_OUTPUT_ROOT}" -mindepth 1 -maxdepth 1 -print -quit)" ]]; then
    echo "LF10 cannot start: output root is not an empty directory" >&2
    exit 43
  fi
else
  mkdir -p -- "${LF10_OUTPUT_ROOT}"
fi

MEDIUM="${LF10_DEPLOYMENT_ROOT}/outputs/runs/20260828T-phk-v21-s1-q-04-nominal-medium/result-intent-04.npz"
LF3_T0="${LF10_DEPLOYMENT_ROOT}/outputs/runs/20260904T150300Z-phk-v23-lf3-phase-latent-97a5b74/checkpoint-t0-step-1200.pt"
DEV_R="${LF10_DEPLOYMENT_ROOT}/outputs/runs/20260906T065434Z-phk-v23-lf6-event-frontier-pilot/dev_r/checkpoint.pt"
STRONG_LEDGER="${LF10_DEPLOYMENT_ROOT}/outputs/runs/20260906T065434Z-phk-v23-lf6-event-frontier-pilot/cpu/materialized_ledger.npz"
LF10_LEDGER="${LF10_DEPLOYMENT_ROOT}/outputs/runs/20260909T101615Z-phk-v23-lf10-feasible-direction-replication/cpu/materialized_lf10_ledger.npz"
LF10_LEDGER_MANIFEST="${LF10_DEPLOYMENT_ROOT}/outputs/runs/20260909T101615Z-phk-v23-lf10-feasible-direction-replication/cpu/materialized_lf10_ledger_manifest.json"

"${PYTHON_BIN}" "${LF10_DEPLOYMENT_ROOT}/cloud/phk_v23_lf10_autodl/preflight.py" \
  --source-identity "${LF10_SOURCE_IDENTITY}" \
  --deployment-root "${LF10_DEPLOYMENT_ROOT}" \
  --output-root "${LF10_OUTPUT_ROOT}" \
  --medium-carrier "${MEDIUM}" \
  --lf3-t0-checkpoint "${LF3_T0}" \
  --dev-r-checkpoint "${DEV_R}" \
  --strong-ledger "${STRONG_LEDGER}" \
  --lf10-ledger "${LF10_LEDGER}" \
  --lf10-ledger-manifest "${LF10_LEDGER_MANIFEST}" \
  --cpu-qualification "${LF10_CPU_QUALIFICATION}"

"${PYTHON_BIN}" -m pinn_pcm_sci.phk_v23_lf10 \
  --output-root "${LF10_OUTPUT_ROOT}" \
  --medium-carrier "${MEDIUM}" \
  --lf3-t0-checkpoint "${LF3_T0}" \
  --dev-r-checkpoint "${DEV_R}" \
  --strong-ledger "${STRONG_LEDGER}" \
  --lf10-ledger "${LF10_LEDGER}" \
  --lf10-ledger-manifest "${LF10_LEDGER_MANIFEST}" \
  --cpu-qualification "${LF10_CPU_QUALIFICATION}" \
  --source-identity "${LF10_SOURCE_IDENTITY}" \
  --device cuda:0

echo "LF10 scientific process finished. Recover and verify artifacts, confirm zero training/GPU processes, then shut down the instance immediately."
