# PHK-V2.3 LF4 CPU-G qualification

- `phase_id`: `PHK_V23_LF4_THRESHOLD_ALIGNED_INTERFACE_BAND_MECHANISM_AND_CONDITIONAL_PHYSICS_PILOT_EXECUTE`
- `gate_outcome`: `LF4_CPU_QUALIFICATION_PASS`
- `scientific_optimizer_updates`: `0`
- `gpu_used`: `false`

## VERIFIED

- Exact medium, LF1-B0 identity, LF3-T0 checkpoint/prediction, contracts, and
  inherited LF3 qualification all matched their frozen SHA-256 bindings.
- The nonperiodic four-neighbour pools are nonempty: cycle-1 inner/outer
  counts `496/620`, cycle-2 `480/604`; their target-measure masses are
  `0.000310/0.0003875/0.000300/0.0003775`.
- On W1/W3, exact LF3-T0 has `TP=1785`, `FN=481`, `FP=227`, weighted
  Jaccard `0.716005`, and Dice `0.834502`. Graph distance zero contains
  `455/481` FN and `199/227` FP.
- The four pool hashes and all deterministic streams were frozen before GPU.
  Base draws 1201--1600 hash to `3870D0C1...62F692E4A`; full M0 through draw
  1600 to `ECD2605A...84001BD`; global-extra to `227244A6...A0123C48`;
  the shared DEV-M/DEV-C band stream to `4DB1728C...C69DEC4`.
- Phase-logit teacher values are finite and within the clip-derived span;
  startup identity is exact at `t=0`. No optimizer, physics sampler, GPU,
  fine, extra-fine, frozen evaluator, or stress reference was used.

## Interpretation boundary

The concentration of errors at graph distance zero supports testing explicit
boundary exposure. It does not establish boundary exposure or threshold
alignment as causal until the matched DEV-G/M/C endpoints satisfy their
preregistered differences and quality gates.

Evidence: [artifact](artifacts/20260905T082728Z-phk-v23-lf4-cpu-qualification.json),
[manifest](manifests/20260905T082728Z-phk-v23-lf4-cpu-qualification.json),
[prior-art closure](../references/2026-09-05-phk-v23-lf4-interface-prior-art.md),
and [ADR 0061](../adr/0061-activate-phk-v23-lf4-interface-band-pilot.md).
