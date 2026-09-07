# ADR 0066: Close PHK-V2.3 LF6 with physics-preservation failure

- `status`: `ACCEPTED_COMPLETE`
- `date`: `2026-09-07`
- `phase_id`: `PHK_V23_LF6_EVENT_FRONTIER_RANK_BAND_AND_SAFETY_GATED_PHYSICS_PILOT_EXECUTE`
- `starting_head`: `9d3c22674dc6279846fa341433d36f603a0854f1`
- `activation_commit`: `55d552670ba0f727f781d4051b84efde474996f9`
- `engineering_commit`: `074eec7f76b4661deda1a622b5343bf992fa2715`
- `machine_outcome`: `LF6_P0_PRESERVATION_FAILED`
- `mechanism_outcome`: `NO_RANK_SPECIFIC_INCREMENT`
- `candidate`: `none`

## Decision

Close LF6 after the complete, hash-bound single-seed campaign. DEV-U and DEV-R
each completed 400 phase-only updates from the same LF3-T0 initialization.
DEV-U did not pass the safety or strict gate. DEV-R passed the safety gate but
failed the strict gate on cycle-1 timing, so the frozen selection rule admitted
DEV-R to the label-free P0 continuation. Because neither matched arm passed the
strict gate, the mechanism outcome is `NO_RANK_SPECIFIC_INCREMENT`; the
rank-band loss has not established a rank-specific benefit over the generic
endpoint control.

P0 completed all 1200 frozen physics-stream updates. The phase remained bitwise
frozen through step 550, while the potential and temperature fields had already
drifted. After joint unfreezing, event support collapsed. At the final endpoint,
the potential maximum-principle and numerical range remained valid, but the
selected carrier's potential, temperature, phase and topology errors increased
by `28.6212`, `52.6001`, `25.8361` and `20.0342` times, respectively. The fixed
blind physics objective ratio was nevertheless `0.0128142265`. The frozen
precedence therefore yields `LF6_P0_PRESERVATION_FAILED`, not a PINN Pareto or
candidate signal.

## Engineering incident

The original P0 launch stopped before constructing its optimizer because the
checkpoint loader treated the dynamic count of currently trainable parameters
as static architecture identity. Strict loading of all tensors and the other
architecture fields were valid. The repair reproduced the development-time
freeze state for identity comparison and restored the P0 trainability state.
Targeted regressions passed. A P0-only continuation then verified the exact 12
DEV-U/DEV-R artifacts and did not retrain either development arm. This is a
same-identity, pre-P0-step engineering retry; it is not an extra scientific arm
or a changed method.

## Evidence and authority boundary

The fixed blind physics reduction is real but is dominated by field and event
degradation, so it cannot support usefulness, direct-baseline gain or PINN
success. Direct `LF_ONLY` remains substantially better on the frozen nominal
metrics. The result supports a bounded physics-forgetting interpretation only.
No rescue, new seed, matched confirmation, sparse task, OOD, stress, PJGR/R2 or
submission action follows automatically. `next_research_execution_authorized`
is false and stress remains `TWO_STRESS_REFERENCES_SEALED_UNREAD`.

The complete record is in the LF6 [terminal closeout](../experiment/2026-09-06-phk-v23-lf6-terminal-closeout.md),
[artifact](../experiment/artifacts/20260906T065434Z-phk-v23-lf6-terminal.json)
and [manifest](../experiment/manifests/20260906T065434Z-phk-v23-lf6-terminal.json).
