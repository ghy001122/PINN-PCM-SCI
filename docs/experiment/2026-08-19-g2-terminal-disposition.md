# G2 terminal disposition, 2026-08-19

## Disposition

- `route_disposition`: `G2_ENVIRONMENT_BLOCKED_FINAL`
- `lifecycle_state`: `BLOCKED`
- `failure_class`: `EXECUTION_PLATFORM_QUOTA_EXHAUSTED_BEFORE_PREFLIGHT`
- `claim_status`: `NO_SCIENTIFIC_CLAIMS`
- `legacy_environment_route`: `FROZEN_NO_AUTOMATIC_RETRY`
- `full_integration_build_count`: `0`
- `method_external_replay_count`: `0`
- `native_qpop_smoke_count`: `0`

This is a route-level decision record, not a run. The controlled Codex execution
platform rejected the first read-only WSL admission command before process
creation because the available execution quota was exhausted; its message gave
`2026-08-20 22:03` as the earliest recovery time. No WSL process, environment
mutation, integration build, Q-POP solver process, or scientific run started.
Consequently there is no run intent or manifest to add to the experiment ledger.

The six-agent-hour Goal requires an immediate terminal decision when its time or
execution budget cannot reach environment verify plus canonical native smoke.
The current legacy environment route is therefore closed as
`G2_ENVIRONMENT_BLOCKED_FINAL`; it must not generate attempt-009 automatically.
This is an execution-platform/environment-route failure, not evidence against
Q-POP physics or the Structural Kinetics-Clock hypothesis.

## Static closure completed before the stop

- Frozen environment spec: `qpop-cpc-v1-ubuntu-20.04-source-stack-v2`, clean
  prefix `/opt/qpop-cpc-v1-env-g2-final-001`.
- DOLFIN's source requirement is matched to pybind11 `2.2.4`; the source artifact
  is fixed at SHA-256
  `642abbbd2948ed5af28e69adfae1535347c7aa9eb0cdab130e20e1f198f8e1cf`, with an
  explicit source-built CMake provider path.
- Build admission requires offline/no-index/no-deps/no-build-isolation behavior,
  one- and two-rank MPI probes, all six OpenMPI executables, exact GNU 9 compiler
  wrappers, a single MPI ABI, a clean prefix, and source/spec/config identity.
- PETSc zero-exit logs containing root-launch refusals, `Possible error`, or
  `Possible problem` are rejected.
- Local acceptance: `88` tests passed, `0` skipped; Python 3.8 grammar check,
  `check-spec`, and `print-plan` passed; experiment ledger validation returned
  `LEDGER_VALID`.

Frozen file identities at closeout:

- `stack_spec.json`:
  `43aa42d901c26900189643529fa90808d3662a85254c777e91b25e86c2dcaba3`
- `pinn_pcm_sci/qpop_legacy_stack.py`:
  `a4a34ffd880825977b9cb02b835c364beeadcd06a76dee7bea40e22937408317`
- `tests/test_qpop_legacy_stack.py`:
  `2901cba374f973df07fb14fdbdace35ca3a1911475f8b8269cdd0331a7ed5480`

## Decision required

The next action is a user decision between terminating this oracle route or
separately approving a different reproducible medium. This Goal does not choose
an alternative, reopen the legacy route, or authorize G3, PINN, GPU, or formal
work.
