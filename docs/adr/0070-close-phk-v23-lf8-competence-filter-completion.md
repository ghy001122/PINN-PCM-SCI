# ADR 0070: Close PHK-V2.3 LF8 with a valid-prefix strong-form stall

- `status`: `ACCEPTED_COMPLETE`
- `date`: `2026-09-08`
- `phase_id`: `PHK_V23_LF8_IDENTITY_CORRECT_COMPETENCE_FILTER_COMPLETION_AND_SCHEDULE_ATTRIBUTION_EXECUTE`
- `starting_head`: `95e448e36a659ac266b670667543b80ce467da53`
- `activation_commit`: `70b4d30bc36cff0c745cc1eb0fc67f9081cd94f0`
- `machine_outcome`: `LF8_FILTER_STALLED_WITH_VALID_PREFIX`
- `mechanism_outcome`: `MATCHED_ATTRIBUTION_UNAVAILABLE`
- `candidate`: `none`

## Decision

Close LF8 after the identity-correct competence filter accepted one 25-update
block at learning rate `7.8125e-6` and then rejected the next block at the same
minimum frozen rate. The retained prefix reduced the fixed-blind strong-form
objective from `4.9278721847` to `4.8743140406` (`J/J0=0.9891315882`) while
preserving the frozen safety conjunction. The five rejected attempts were
rolled back without identity drift; their recurring decisive failure was
temperature preservation. This is a valid scientific stall, not an engineering
failure or an invalid arm.

The path reached only 25 of 1,200 required accepted updates, so it did not form
a complete safety path, PINN Pareto result or candidate. The conditional
accepted-schedule control was therefore not run and cannot be called failed;
filter-versus-schedule attribution remains unavailable. The valid prefix is
retained as bounded evidence that a locally safe strong-form descent direction
exists only at the smallest frozen rate, but the same rate cannot support a
second 25-update block under the coupled field-preservation gates.

## Consequence and authority boundary

LF8 closes further strong-form rescue by smaller learning rates, shorter
blocks, optimizer/weight/sampling/network changes or replay. The unique next
recommendation is
`MIXED_WEAK_CONTROL_VOLUME_PLAN_REQUIRES_NEW_EXECUTE_VALID_PREFIX_RETAINED`:
replace the failed strong-form continuation function with a mixed weak or
control-volume physics objective while retaining the validated event carrier
and LF8 prefix as comparators. This is a recommendation only.

No filter mechanism increment, direct-`LF_ONLY` gain, sparse/OOD/stress result,
SOTA claim or experimental validation is established. Stress remains
`TWO_STRESS_REFERENCES_SEALED_UNREAD`, and
`next_research_execution_authorized=false`.

See the LF8 [terminal closeout](../experiment/2026-09-08-phk-v23-lf8-terminal-closeout.md),
[artifact](../experiment/artifacts/20260908T050343Z-phk-v23-lf8-terminal.json)
and [manifest](../experiment/manifests/20260908T050343Z-phk-v23-lf8-terminal.json).
