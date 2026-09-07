# PHK-V2.3 LF7 CPU qualification

- `phase_id`: `PHK_V23_LF7_COMPETENCE_FILTERED_BLOCKWISE_BACKTRACKING_PHYSICS_REFINEMENT_PILOT_EXECUTE`
- `gate_outcome`: `LF7_CPU_QUALIFICATION_PASS`
- `scientific_optimizer_updates`: `0`
- `gpu_used`: `false`
- `prior_art`: `NO_EXACT_FUNCTIONAL_COLLISION_FOUND_WITHIN_BOUNDED_6_ITEM_SCOPE`

## VERIFIED

- Exact LF6 DEV-R was reloaded from its frozen checkpoint and reproduced the
  full-medium field, event and topology audit. Its fixed-blind strong-form
  objective is exactly `J0=4.9278721846990505` within the frozen FP64 tolerance.
- The inherited materialized ledger verified all 1,200 physics batches and the
  fixed blind pool, with rolling identities `536E6706...B7EC05C53` and
  `FD285AFC...7AF0E64CF`.
- The toy block transaction restored model, optimizer and RNG state bitwise,
  reused the same coordinates and halved the learning rate. A real DEV-R
  physics backward was finite and nonzero without an optimizer step.
- Medium data produced no gradients and is qualified only for P0-F
  accept/reject audits. Fine, extra-fine, direct `LF_ONLY`, the frozen local
  evaluator and stress were not read.
- All 24 zero-update qualification checks passed.

## Decision

CPU qualification authorizes the pre-registered matched sequence: fixed-small
step P0-S followed by a fresh exact-DEV-R P0-F. It is engineering/identity
evidence only and does not predict either arm's scientific result.

Evidence: [compact artifact](artifacts/20260907T144634Z-phk-v23-lf7-cpu-qualification.json),
[manifest](manifests/20260907T144634Z-phk-v23-lf7-cpu-qualification.json), and
[prior-art closure](../references/2026-09-07-phk-v23-lf7-constrained-refinement-prior-art.md).
