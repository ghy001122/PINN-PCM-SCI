# G2 quota-recovery resume authorization, 2026-08-20

## Authority update

- `authorization`: `USER_EXPLICITLY_RESUMED_G2_AFTER_EXECUTION_QUOTA_RECOVERY`
- `supersedes_route_record`: `docs/experiment/2026-08-19-g2-terminal-disposition.md`
- `superseded_failure_class`: `EXECUTION_PLATFORM_QUOTA_EXHAUSTED_BEFORE_PREFLIGHT`
- `new_goal_scope`: `G2_ENVIRONMENT_VERIFY_AND_ONE_CONDITIONAL_NATIVE_SMOKE_ONLY`
- `claim_status`: `NO_SCIENTIFIC_CLAIMS`

The prior `G2_ENVIRONMENT_BLOCKED_FINAL` remains an immutable, accurate record
of the 2026-08-19 execution-platform stop. The user reported that the execution
quota has recovered and explicitly instructed continuation on 2026-08-20. This
new authority supersedes only that quota-caused route freeze; it does not erase
attempts 001–007 or authorize G3, PINN, GPU, formal work, a different oracle, or
scientific claims.

## Bounded continuation contract

1. Revalidate the existing static contract and perform a read-only WSL admission
   check against the clean prefix `/opt/qpop-cpc-v1-env-g2-final-001`.
2. If admission passes, pre-register one environment run and execute the frozen
   `resolve → preflight → build → verify` sequence in a new evidence root.
3. No dependency/config/source/ABI/compile/test/verify failure may be fixed and
   followed by a second integration build in this Goal. Such a failure closes
   the route immediately.
4. Only a proven method-external interruption may receive one byte-identical
   replay linked with `replay_of`; the original attempt remains recorded.
5. Only after environment verification may one canonical shortest Q-POP native
   smoke be registered and run. It must use the frozen disk converter and
   independent evaluator.
6. Every real attempt receives a prior intent and an immutable manifest/index
   entry. A read-only admission check is not a run.

The only possible terminal outcomes remain `G2_SMOKE_PASS` or a newly evidenced
`G2_ENVIRONMENT_BLOCKED_FINAL`.
