# PHK-V2.3 LF6 CPU-F qualification

- `phase_id`: `PHK_V23_LF6_EVENT_FRONTIER_RANK_BAND_AND_SAFETY_GATED_PHYSICS_PILOT_EXECUTE`
- `gate_outcome`: `LF6_CPU_F_QUALIFICATION_PASS`
- `scientific_optimizer_updates`: `0`
- `gpu_used`: `false`
- `prior_art`: `NO_EXACT_FUNCTIONAL_COLLISION_FOUND_WITHIN_BOUNDED_6_ITEM_SCOPE`

## VERIFIED

- All required medium, LF1-B0, LF3-T0, LF4 DEV-M, LF4 summary and telemetry
  inputs matched their frozen SHA-256 bindings. Fine, extra-fine, direct
  `LF_ONLY`, the frozen evaluator and stress were not read.
- The medium ROI has 968 cells, so the frozen two-percent event rank is 20.
  Cycle 1 first crosses between saved indices 47 and 48
  (`A*=0.0165289 -> 0.0227273`), producing ranks 17--22 at both endpoints.
  Cycle 2 first crosses between indices 298 and 299
  (`A*=0.0165289 -> 0.0206612`), producing ranks 17--20.
- The four event-frontier pools contain `6/6/4/4` cells. Their matched generic
  endpoint controls have the same counts and were selected once with PCG64
  seeds `17611..17614`, without replacement or model-result reselection.
- CPU-F materialized the complete 400-step base and spatial batches, both
  endpoint sets, all 1200 physics batches and the fixed blind physics pool.
  The inherited semantic identities exactly match:
  `3870D0C1...62F692E4A`, `4DB1728C...C69DEC4`,
  `536E6706...B7EC05C53`, and `FD285AFC...7AF0E64CF`.
- The content-addressed ledger SHA is
  `29E02DAF81A07BA4AF2B95B354126E75E9419AAE094E9486589455D31D2D6801`;
  its semantic SHA is
  `0E2F680D33C4489F6092CB5D01E87483F7ECDA8290CD3E2C24EBDD06B3DA2B7F`.
  The frontier and generic-endpoint identities are respectively
  `B72C891B...EE51724D` and `4A83CD0F...D03B8FE`.
- Exact historical DEV-M was reloaded read-only and remains a valid safety
  carrier (`recall=0.937285/0.909256`, `precision=0.909167/0.946176`,
  timing error `0.0105333/0.005`, phase weighted MSE `0.00120963`). The zero-step
  endpoint loss backward was finite and produced a nonzero phase gradient.

## Decision

CPU-F authorizes the fixed DEV-U and DEV-R screen. It contains no performance
premise gate and does not predict either arm's result. A conditional P0 is
required from the deterministic selected safety endpoint. Cloud execution must
consume the materialized arrays directly and verify the full ledger before an
optimizer exists; runtime Sobol generation is forbidden.

Evidence: [compact artifact](artifacts/20260906T065434Z-phk-v23-lf6-cpu-qualification.json),
[manifest](manifests/20260906T065434Z-phk-v23-lf6-cpu-qualification.json), and
[prior-art closure](../references/2026-09-06-phk-v23-lf6-event-frontier-prior-art.md).
