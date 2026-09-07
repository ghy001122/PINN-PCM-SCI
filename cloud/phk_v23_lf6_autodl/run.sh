#!/usr/bin/env bash
set -euo pipefail

: "${LF6_SOURCE_IDENTITY:?LF6_SOURCE_IDENTITY is required}"
: "${LF6_DEPLOYMENT_ROOT:?LF6_DEPLOYMENT_ROOT is required}"
: "${LF6_OUTPUT_ROOT:?LF6_OUTPUT_ROOT is required}"
: "${LF6_ALLOW_DEV_M_FALLBACK_INPUT:?LF6_ALLOW_DEV_M_FALLBACK_INPUT must record the explicit user decision}"
: "${LF6_EXECUTION_MODE:?LF6_EXECUTION_MODE must explicitly select FULL_CAMPAIGN or P0_ONLY_PRESTEP_ENGINEERING_RETRY}"

if [[ "${LF6_ALLOW_DEV_M_FALLBACK_INPUT}" != "1" ]]; then
  echo "LF6 cannot start: exact DEV-M fallback is required by carrier selection but needs explicit cloud-input authorization" >&2
  exit 42
fi

export PYTHONPATH="${LF6_DEPLOYMENT_ROOT}"
EXPECTED_OUTPUT_ROOT="/root/autodl-tmp/lf6-run-20260906T065434Z"
if [[ "${LF6_OUTPUT_ROOT}" != "${EXPECTED_OUTPUT_ROOT}" ]]; then
  echo "LF6 cannot start: LF6_OUTPUT_ROOT differs from the frozen campaign root" >&2
  exit 43
fi

MEDIUM="${LF6_DEPLOYMENT_ROOT}/outputs/runs/20260828T-phk-v21-s1-q-04-nominal-medium/result-intent-04.npz"
INITIAL="${LF6_DEPLOYMENT_ROOT}/outputs/runs/20260904T150300Z-phk-v23-lf3-phase-latent-97a5b74/checkpoint-t0-step-1200.pt"
DEV_M="${LF6_DEPLOYMENT_ROOT}/outputs/runs/20260905T102817Z-phk-v23-lf4-interface-band-5dbde1d/checkpoint-dev-m-interface-band-mse-step-400.pt"
QUALIFICATION="${LF6_DEPLOYMENT_ROOT}/docs/experiment/artifacts/20260906T065434Z-phk-v23-lf6-cpu-qualification.json"
LEDGER="${LF6_DEPLOYMENT_ROOT}/outputs/runs/20260906T065434Z-phk-v23-lf6-event-frontier-pilot/cpu/materialized_ledger.npz"
LEDGER_MANIFEST="${LF6_DEPLOYMENT_ROOT}/outputs/runs/20260906T065434Z-phk-v23-lf6-event-frontier-pilot/cpu/materialized_ledger_manifest.json"

PREFLIGHT_ARGS=(
  --source-identity "${LF6_SOURCE_IDENTITY}"
  --deployment-root "${LF6_DEPLOYMENT_ROOT}"
  --medium-carrier "${MEDIUM}"
  --initial-checkpoint "${INITIAL}"
  --dev-m-checkpoint "${DEV_M}"
  --materialized-ledger "${LEDGER}"
  --ledger-manifest "${LEDGER_MANIFEST}"
  --cpu-qualification "${QUALIFICATION}"
  --allow-dev-m-fallback-input
)

RUN_ARGS=(
  --output-root "${LF6_OUTPUT_ROOT}"
  --medium-carrier "${MEDIUM}"
  --initial-checkpoint "${INITIAL}"
  --dev-m-checkpoint "${DEV_M}"
  --materialized-ledger "${LEDGER}"
  --cpu-qualification "${QUALIFICATION}"
  --source-identity "${LF6_SOURCE_IDENTITY}"
  --device cuda:0
)

case "${LF6_EXECUTION_MODE}" in
  FULL_CAMPAIGN)
    if [[ -n "${LF6_DEVELOPMENT_ARTIFACT_LOCK:-}" ]]; then
      echo "LF6 cannot start: development artifact lock is only valid for explicit P0-only retry" >&2
      exit 44
    fi
    ;;
  P0_ONLY_PRESTEP_ENGINEERING_RETRY)
    : "${LF6_DEVELOPMENT_ARTIFACT_LOCK:?LF6_DEVELOPMENT_ARTIFACT_LOCK is required for P0-only retry}"
    EXPECTED_DEVELOPMENT_ARTIFACT_LOCK="${LF6_OUTPUT_ROOT}/cloud/recovery_manifest.json"
    if [[ "${LF6_DEVELOPMENT_ARTIFACT_LOCK}" != "${EXPECTED_DEVELOPMENT_ARTIFACT_LOCK}" ]]; then
      echo "LF6 cannot start: development artifact lock path differs from the frozen recovery-manifest path" >&2
      exit 45
    fi
    PREFLIGHT_ARGS+=(
      --p0-only-prestep-engineering-retry
      --output-root "${LF6_OUTPUT_ROOT}"
      --development-artifact-lock "${LF6_DEVELOPMENT_ARTIFACT_LOCK}"
    )
    RUN_ARGS+=(
      --p0-only-prestep-engineering-retry
      --development-artifact-lock "${LF6_DEVELOPMENT_ARTIFACT_LOCK}"
    )
    ;;
  *)
    echo "LF6 cannot start: unsupported LF6_EXECUTION_MODE=${LF6_EXECUTION_MODE}" >&2
    exit 46
    ;;
esac

python "${LF6_DEPLOYMENT_ROOT}/cloud/phk_v23_lf6_autodl/preflight.py" "${PREFLIGHT_ARGS[@]}"
python -m pinn_pcm_sci.phk_v23_lf6 "${RUN_ARGS[@]}"
