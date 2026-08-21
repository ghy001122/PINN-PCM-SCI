# G2 WSL environment preflight

- `gate`: `G2`
- `activity`: `environment_preflight`
- `execution_status`: `PAUSED_PENDING_WINDOWS_REBOOT`
- `gate_outcome`: `NOT_YET_EVALUATED`
- `claim_status`: `NO_NUMERICAL_EVIDENCE`

## VERIFIED

- Before installation, `wsl.exe --status` returned exit code 50 and stated that
  Windows Subsystem for Linux was not installed.
- The Q-POP upstream environment guide recommends Ubuntu 20.04. The approved
  administrator command therefore requested `Ubuntu-20.04` rather than the
  version-ambiguous default Ubuntu distribution.
- The administrator process for
  `wsl.exe --install -d Ubuntu-20.04 --no-launch` returned exit code 0.
- `wsl.exe --version` now reports WSL 2.7.12.0, kernel 6.18.33.2-2, and Windows
  10.0.26200.9168.
- Windows reports both `CBS RebootPending=true` and a pending file-rename
  operation. Before reboot, `wsl.exe --status` and distribution enumeration
  return `Wsl/EnumerateDistros/Service/E_ACCESSDENIED`.

## Required continuation

Restart Windows before any further G2 environment action. After restart, first
verify that Ubuntu 20.04 is registered as WSL 2 and record its exact release.
Only then may the frozen legacy Q-POP dependencies be installed. At the time of
this pause, no Q-POP process, nonlinear step, oracle output, or PINN run had
started and no run manifest had yet been created.

## Later ledger reconciliation

The subsequent environment-resolution attempts remained non-scientific, but
the project's attempt-level bookkeeping rule also covers failed infrastructure
attempts. Attempts 001–003 were therefore reconstructed from their immutable
stage failure records into manifests and appended to the experiment index. The
manifests explicitly state `RETROSPECTIVE_FROM_IMMUTABLE_STAGE_EVIDENCE`, do not
claim an unavailable exact dirty-worktree snapshot, and remain
`ENVIRONMENT_PREFLIGHT_ONLY / NOT_EVALUATED / NO_SCIENTIFIC_CLAIMS`.
