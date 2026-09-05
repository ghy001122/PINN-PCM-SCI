# PHK-V2.3 LF5 CPU-T qualification

- `phase_id`: `PHK_V23_LF5_CYCLE_RESOLVED_TEMPORAL_ZERO_LEVEL_ALIGNMENT_AND_CONDITIONAL_PHYSICS_PILOT_EXECUTE`
- `gate_outcome`: `LF5_TZL_ALIGNMENT_NOT_SUPPORTED_CPU`
- `scientific_optimizer_updates`: `0`
- `gpu_used`: `false`

## VERIFIED

- All required medium, LF1-B0, LF3-T0, LF4 DEV-G/M/C, LF4 raw ledger,
  compact evidence, and contract hashes matched the frozen bindings.
- Cycle-resolved teacher geometry produced `68/68/64/64` edges for
  C1 onset/recovery and C2 onset/recovery. All 264 candidate edges were valid;
  invalid-edge fraction was `0`.
- The temporal Sobol stream used pool order
  `C1_ONSET,C1_RECOVERY,C2_ONSET,C2_RECOVERY`, seeds
  `17511..17514`, 32 edges per pool per step, and frozen 400-draw rolling SHA
  `8FD79D99...C9B3BD9`.
- Exact LF4 base and spatial-band streams reconstructed the frozen hashes
  `3870D0C1...62F692E4A` and `4DB1728C...C69DEC4`.
- DEV-M's weighted signed onset residuals were `+0.077064/-0.099958`, matching
  its cycle-1 early and cycle-2 late directions. The zero-step TZL backward was
  finite and nonzero (`loss=0.0006035145`, phase gradient norm `0.00487159`).
- The load-bearing comparison failed twice: C1 weighted mean absolute residual
  worsened from DEV-M `0.292071` to DEV-C `0.723760`; C2 worsened from
  `0.309983` to `0.604055`.

## SUPPORTED_INTERPRETATION

LF4 DEV-C's improvement in aggregate event time does not correspond to a
uniform improvement of teacher-anchored, per-cell onset secant residuals. Its
threshold classification loss can shift the aggregate active fraction while
worsening local temporal calibration. This supports rejecting DEV-C as an
empirical premise for the frozen LF5 TZL continuation; it does not prove that
all temporal-edge, derivative, or kinetic teachers fail.

## Stop disposition

The preregistered hard gate forbids GPU deployment. DEV-T and P0 are `NOT_RUN`,
not failed. Fine, extra-fine, direct LF_ONLY, the frozen evaluator, and stress
were not loaded by CPU-T.

## Post-qualification authorization boundary

On 2026-09-06, after this result was known, the user explicitly authorized the
otherwise unchanged fixed DEV-T trajectory and its original conditional P0.
That later run must be labeled `POST_QUALIFICATION_USER_OVERRIDE_EXPLORATORY`.
It does not change this gate to PASS and cannot be used as preregistered
confirmation of the CPU-T premise.

Evidence: [artifact](artifacts/20260905T150045Z-phk-v23-lf5-cpu-qualification.json),
[manifest](manifests/20260905T150045Z-phk-v23-lf5-cpu-qualification.json),
[prior-art closure](../references/2026-09-05-phk-v23-lf5-temporal-zero-level-prior-art.md),
and [ADR 0063](../adr/0063-activate-phk-v23-lf5-temporal-zero-level-pilot.md).
