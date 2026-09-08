# ADR 0072: Close PHK-V2.3 LF9 with no safe mixed-form screen

- `status`: `ACCEPTED_COMPLETE`
- `date`: `2026-09-09`
- `phase_id`: `PHK_V23_LF9_EQUATION_ROUTED_THERMAL_CONTROL_VOLUME_REFINEMENT_EXECUTE`
- `starting_head`: `f16ca9db66843c04d420c077679604dd553ac036`
- `activation_commit`: `c38fa80d2fa2ceb0b1bd1fa9faf70440f2a07159`
- `engineering_commits`: `3ad2dcb302faca00bb60d1cbb1529b11061b6cca`, `bc3950a13935a9ded70d4a8b6cc2862deb4a3fd8`
- `machine_outcome`: `LF9_NO_SAFE_MIXED_FORM_SCREEN`
- `mechanism_outcome`: `NO_SAFE_MIXED_FORM_SCREEN`
- `candidate`: `none`

## Decision

Close LF9 after both identity-valid matched screens accepted exactly one
25-update block at learning rate `7.8125e-6` and then stalled at the same
minimum frozen rate. ER-S and ER-CV each reduced its own blind objective by
about 1.03%, preserved the reference-blind safety conjunction, and failed the
same second-block temperature-preservation gate. Neither reached the frozen
200-update screen requirement, so no arm was selected.

The conditional filtered full path and accepted-schedule control were not run
because their prerequisites were not met; they are not failed trajectories.
The matched endpoints are numerically and identity valid, but the near-identical
ER-S/ER-CV behavior supplies no evidence that thermal control-volume routing
opens a longer safe continuation path.

## Consequence and authority boundary

LF9 closes the preregistered strong-form and thermal-CV rescue family for this
nominal carrier. The unique next action is
`FINALIZE_NEGATIVE_SOLVER_DIAGNOSTIC_NO_MORE_RESCUE`: consolidate the bounded
negative solver evidence and manuscript without another optimization rescue.
This recommendation does not authorize new training, sparse/OOD/stress work,
or a new method route.

No complete internal PINN Pareto, direct-`LF_ONLY` gain, candidate, SOTA claim,
or experimental validation is established. Stress remains
`TWO_STRESS_REFERENCES_SEALED_UNREAD`, and
`next_research_execution_authorized=false`.

See the LF9 [terminal closeout](../experiment/2026-09-08-phk-v23-lf9-terminal-closeout.md),
[artifact](../experiment/artifacts/20260908T145333Z-phk-v23-lf9-terminal.json),
and [manifest](../experiment/manifests/20260908T145333Z-phk-v23-lf9-terminal.json).
