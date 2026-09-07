# PHK-V2.3 LF6 event-frontier pilot terminal closeout

- `phase_id`: `PHK_V23_LF6_EVENT_FRONTIER_RANK_BAND_AND_SAFETY_GATED_PHYSICS_PILOT_EXECUTE`
- `lifecycle_state`: `COMPLETE`
- `CPU_F_outcome`: `LF6_CPU_F_QUALIFICATION_PASS`
- `machine_outcome`: `LF6_P0_PRESERVATION_FAILED`
- `mechanism_outcome`: `NO_RANK_SPECIFIC_INCREMENT`
- `selected_role`: `DEV_R_EVENT_FRONTIER_RANK_BAND`
- `scientific_gpu_trajectories`: `3`
- `optimizer_updates`: `400 DEV-U + 400 DEV-R + 1200 P0 = 2000`
- `candidate`: `none`
- `next_research_execution_authorized`: `false`
- `unique_next`: `PHYSICS_FORGETTING_RESULT_NO_RESCUE`
- `stress_reference_status`: `TWO_STRESS_REFERENCES_SEALED_UNREAD`

## Terminal decision

The two matched development arms completed exactly 400 phase-only updates with
V/T bitwise frozen. DEV-U narrowly missed both recall minima and cycle-1 timing.
DEV-R crossed the safety recall gate and was the frozen safety-selected P0
input, but missed the strict cycle-1 timing gate. Neither arm passed the strict
gate, so the narrow rank-specific mechanism verdict is
`NO_RANK_SPECIFIC_INCREMENT`.

| full-medium endpoint | DEV-U | DEV-R |
|---|---:|---:|
| safety / strict | FAIL / FAIL | PASS / FAIL |
| phase weighted MSE | 0.0012066681 | 0.0011832624 |
| recall, cycle 1 / 2 | 0.896907 / 0.899274 | 0.917526 / 0.922868 |
| precision, cycle 1 / 2 | 0.926353 / 0.921004 | 0.896725 / 0.920362 |
| active-mass ratio, cycle 1 / 2 | 0.968213 / 0.976407 | 1.023196 / 1.002722 |
| event-time error, cycle 1 / 2 | 0.006900 / 0.001400 | 0.010533 / 0.001800 |
| recovery, cycle 1 / 2 | 1 / 1 | 1 / 1 |

## Conditional P0 result

P0 ran the exact 1200-step materialized physics stream with no medium labels,
replay, event loss or dynamic weighting. The step-550 identity check passed:
the phase parameters were bitwise unchanged, the phase optimizer state had zero
entries, the values were finite and the potential guard passed. The selected
DEV-R endpoint V/T MSEs were `0.00007147677/0.0007111887`; they had moved to
`0.0000824924/0.00245803` at P0 step 1 and to `0.00205528/0.0431605` by step
550. After phase unfreezing,
recall fell to `0.3428/0.2160` by step 600; cycle-1 event existence was gone by
step 800; at step 1200 both hard recalls were zero.

The endpoint remained finite and phase/potential-valid, but failed the frozen
preservation gate:

| selected DEV-R -> P0 ratio | value | limit |
|---|---:|---:|
| potential weighted MSE | 28.621202 | 1.20 |
| temperature weighted MSE | 52.600113 | 1.05 |
| phase weighted MSE | 25.836141 | 1.05 |
| topology weighted loss | 20.034179 | 1.05 |

P0 phase weighted MSE was `0.0305709339`; cycle 1 had no event, both hard
recalls and active masses were zero, and both recoveries failed. The fixed
blind objective nevertheless decreased from `4.9278721847` to `0.0631468705`,
for a ratio of `0.012814226536278206`. This is a valid negative Pareto result:
bulk physics minimization did not preserve the event-bearing multiphysics
solution.

## Post-shutdown nominal adjudication

Fine, extra-fine, direct `LF_ONLY` and the frozen evaluator were read only after
artifact recovery, zero process/GPU verification and shutdown. The selected
DEV-R endpoint passed the evaluator hard guards, with phase ROI RMS
`0.0323683`, temperature ROI RMS `0.0173618`, and current NRMSE `0.137297`.
P0 failed event guards and degraded phase ROI RMS to `0.157505` and temperature
ROI RMS to `0.151474`. Direct `LF_ONLY` remained stronger at phase ROI RMS
`0.00657038`, temperature ROI RMS `0.00180069`, and current NRMSE `0.00352214`.
Because preservation already failed, neither the single-seed PINN Pareto nor
the direct-baseline candidate level was reached.

## Engineering provenance and source identity

- start HEAD: `9d3c22674dc6279846fa341433d36f603a0854f1`
- activation HEAD: `55d552670ba0f727f781d4051b84efde474996f9`
- P0 prestep repair HEAD: `074eec7f76b4661deda1a622b5343bf992fa2715`
- development source: `LF6-BUNDLE-2A4DE4E45D48EDD11FC314D5F0525D9639966B2D728952FC0A83F7AE3096274A`
- P0 continuation source: `LF6-BUNDLE-760CAED377A5E32740CE07314FFF8AF4E216CB69FC71C00BD4E6B732DE5C10EC`

The first P0 launch failed before P0 optimizer construction because a dynamic
trainable-parameter count was compared as immutable architecture identity. The
targeted repair changed no scientific input, loss, stream, seed, budget or
gate. The P0-only retry verified all 12 development artifacts and did not rerun
DEV-U or DEV-R. This is engineering provenance, not a scientific increment.

## Recovery, shutdown and evidence boundary

All development and P0 checkpoints, predictions, ledgers, telemetry, gates and
exit records were recovered with remote/local size and SHA equality. The three
configured `console.log` paths were not separately persisted; execution output
is represented by telemetry, exit/gate records, the run summary and the Codex
transcript, and no console hash is invented. Training and GPU processes were
zero before shutdown. The endpoint then had a closed TCP port and SSH returned
`Connection refused`; that refusal is ordered before local adjudication, while
its exact observation time was not separately persisted. Local adjudication is
bound by SHA in the terminal artifact.

The campaign establishes neither an event-frontier-specific increment nor a
PINN Pareto, direct-baseline gain, candidate, multi-seed/OOD/stress conclusion,
SOTA claim or experimental validation. It does establish a bounded, two-stage
physics-forgetting result: V/T drift occurred while phase was frozen, followed
by event collapse after joint unfreezing. Stress remained sealed/unread.

See the [terminal artifact](artifacts/20260906T065434Z-phk-v23-lf6-terminal.json),
[terminal manifest](manifests/20260906T065434Z-phk-v23-lf6-terminal.json), and
[ADR 0066](../adr/0066-close-phk-v23-lf6-event-frontier-pilot.md).
