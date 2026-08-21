# G2 quota-recovery closeout, 2026-08-20

## Disposition

- `route_disposition`: `G2_ENVIRONMENT_BLOCKED_FINAL`
- `lifecycle_state`: `BLOCKED`
- `failed_run_id`: `20260820T142429Z-smoke-g2-env-final-001`
- `failure_stage`: `resolve`
- `underlying_gate_outcome`: `G2_ENVIRONMENT_BLOCKED_FINAL`
- `failure_class`: `PYBIND11_SOURCE_ARTIFACT_UNEXPECTED_LAYOUT`
- `environment_verify_status`: `NOT_REACHED`
- `native_smoke_run_id`: `NOT_STARTED`
- `qpop_started`: `false`
- `claim_status`: `NO_SCIENTIFIC_CLAIMS`
- `supersedes_route_record`: `docs/experiment/2026-08-19-g2-terminal-disposition.md`
- `supersedes_only_failure_class`: `EXECUTION_PLATFORM_QUOTA_EXHAUSTED_BEFORE_PREFLIGHT`
- `next_route`: `NO_AUTOMATIC_RETRY`

The quota-recovery authorization was consumed by the single registered clean
environment integration run. The run completed OpenMPI 3.1.6 installation and
the frozen Python dependency installation, then stopped during `resolve`
because the pybind11 2.2.4 source artifact did not have the layout required by
the frozen provider contract. The predeclared stop rule therefore prohibited a
repair, a second integration run, `preflight`, `build`, `verify`, and native
Q-POP smoke.

Immutable evidence:

- run manifest:
  `docs/experiment/manifests/20260820T142429Z-smoke-g2-env-final-001.json`;
- stage failure:
  `outputs/environments/qpop-cpc-v1-ubuntu-20.04-source-stack-v2/g2-final-001/resolve.failure.json`;
- stage failure SHA-256:
  `5795c0877b15234be76c551c09750df19d0d591e92f6d0bac1b3cd27367f05a2`.

The 2026-08-19 quota stop remains an immutable historical fact; this record
supersedes only that quota-caused route freeze. Attempts 001–007 and the current
failed run remain preserved. This is an environment-integration route failure,
not Q-POP physics evidence and not evidence for or against the Structural
Kinetics-Clock hypothesis. No G3, PINN, GPU, or formal work is authorized.
