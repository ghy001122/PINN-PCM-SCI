#!/usr/bin/env bash
set -euo pipefail

: "${LF9_SOURCE_IDENTITY:?LF9_SOURCE_IDENTITY is required}"
: "${LF9_DEPLOYMENT_ROOT:?LF9_DEPLOYMENT_ROOT is required}"
: "${LF9_OUTPUT_ROOT:?LF9_OUTPUT_ROOT is required}"
: "${LF9_CPU_QUALIFICATION:?LF9_CPU_QUALIFICATION is required}"

export PYTHONPATH="${LF9_DEPLOYMENT_ROOT}"

case "${LF9_OUTPUT_ROOT}" in
  /root/autodl-tmp/lf9-run-*) ;;
  *)
    echo "LF9 cannot start: LF9_OUTPUT_ROOT is outside the frozen campaign namespace" >&2
    exit 42
    ;;
esac

if [[ -e "${LF9_OUTPUT_ROOT}" ]]; then
  if [[ ! -d "${LF9_OUTPUT_ROOT}" ]] || [[ -n "$(find "${LF9_OUTPUT_ROOT}" -mindepth 1 -maxdepth 1 -print -quit)" ]]; then
    echo "LF9 cannot start: output root is not an empty directory" >&2
    exit 43
  fi
else
  mkdir -p -- "${LF9_OUTPUT_ROOT}"
fi

MEDIUM="${LF9_DEPLOYMENT_ROOT}/outputs/runs/20260828T-phk-v21-s1-q-04-nominal-medium/result-intent-04.npz"
DEV_R="${LF9_DEPLOYMENT_ROOT}/outputs/runs/20260906T065434Z-phk-v23-lf6-event-frontier-pilot/dev_r/checkpoint.pt"
STRONG_LEDGER="${LF9_DEPLOYMENT_ROOT}/outputs/runs/20260906T065434Z-phk-v23-lf6-event-frontier-pilot/cpu/materialized_ledger.npz"
STRONG_MANIFEST="${LF9_DEPLOYMENT_ROOT}/outputs/runs/20260906T065434Z-phk-v23-lf6-event-frontier-pilot/cpu/materialized_ledger_manifest.json"
CV_LEDGER="${LF9_DEPLOYMENT_ROOT}/outputs/runs/20260908T145333Z-phk-v23-lf9-equation-routed-thermal-cv/cpu/cv/materialized_cv_ledger.npz"
CV_MANIFEST="${LF9_DEPLOYMENT_ROOT}/outputs/runs/20260908T145333Z-phk-v23-lf9-equation-routed-thermal-cv/cpu/cv/materialized_cv_ledger_manifest.json"

python "${LF9_DEPLOYMENT_ROOT}/cloud/phk_v23_lf9_autodl/preflight.py" \
  --source-identity "${LF9_SOURCE_IDENTITY}" \
  --deployment-root "${LF9_DEPLOYMENT_ROOT}" \
  --output-root "${LF9_OUTPUT_ROOT}" \
  --medium-carrier "${MEDIUM}" \
  --dev-r-checkpoint "${DEV_R}" \
  --strong-ledger "${STRONG_LEDGER}" \
  --strong-ledger-manifest "${STRONG_MANIFEST}" \
  --cv-ledger "${CV_LEDGER}" \
  --cv-ledger-manifest "${CV_MANIFEST}" \
  --cpu-qualification "${LF9_CPU_QUALIFICATION}"

# One process owns both mandatory screens, the conditional continuation, and
# the conditional matched control. Arm-local failures are handled by the core
# campaign so that the unaffected mandatory screen still completes.
python -m pinn_pcm_sci.phk_v23_lf9 \
  --output-root "${LF9_OUTPUT_ROOT}" \
  --medium-carrier "${MEDIUM}" \
  --initial-checkpoint "${DEV_R}" \
  --strong-ledger "${STRONG_LEDGER}" \
  --cv-ledger "${CV_LEDGER}" \
  --cv-ledger-manifest "${CV_MANIFEST}" \
  --cpu-qualification "${LF9_CPU_QUALIFICATION}" \
  --source-identity "${LF9_SOURCE_IDENTITY}" \
  --device cuda:0

echo "LF9 scientific process finished. Recover and hash artifacts, verify zero training/GPU processes, then shut down the instance immediately."
