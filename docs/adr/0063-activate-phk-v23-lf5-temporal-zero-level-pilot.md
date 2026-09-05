# ADR 0063: Activate PHK-V2.3 LF5 temporal zero-level pilot

- `status`: `ACCEPTED_WITH_POST_QUALIFICATION_USER_OVERRIDE_EXPLORATORY_GPU`
- `date`: `2026-09-05`
- `phase_id`: `PHK_V23_LF5_CYCLE_RESOLVED_TEMPORAL_ZERO_LEVEL_ALIGNMENT_AND_CONDITIONAL_PHYSICS_PILOT_EXECUTE`
- `starting_head`: `d86ddf1d206c611087a1b5284acda69efdfda9fa`
- `prior_art`: `NO_EXACT_FUNCTIONAL_COLLISION_FOUND_WITHIN_FROZEN_8_SOURCE_SCOPE`

## Decision

LF5 was authorized to test a calibration-preserving combination of the LF3
equal-category logit teacher, the LF4 spatial interface-band MSE, and a new
cycle-resolved saved-cadence temporal zero-level residual. Onset edges are the
first sign crossings in W1/W3; recovery edges are the first subsequent reverse
crossings in W2/W4 of the same cycle, with no cycle wrap.

The preregistered CPU-T mechanism gate runs before cloud deployment. It requires
the exact LF4 DEV-C checkpoint to have lower weighted mean absolute zero-level
residual than DEV-M in both onset pools, while DEV-M's residual sign must agree
with the observed early/late timing direction. Only a passing result authorizes
the fixed 400-update DEV-T and its conditional label-free physics P0.

## Executed pre-GPU disposition

The geometry, identity, stream, timing-presence, and finite-gradient checks all
passed, but DEV-C was worse than DEV-M in both onset pools. CPU-T therefore
returned `LF5_TZL_ALIGNMENT_NOT_SUPPORTED_CPU`. Under the frozen decision
contract, this activation is limited to evidence terminalization: no bundle,
SSH connection, GPU optimizer step, DEV-T, P0, or local nominal reference read
is permitted.

Machine semantics are frozen in the LF5 [program](../../configs/phk_v23/program_contract_lf5_temporal_zero_level.json),
[method](../../configs/phk_v23/method_contract_lf5_temporal_zero_level.json),
[data](../../configs/phk_v23/data_contract_lf5_temporal_zero_level.json), and
[decision](../../configs/phk_v23/decision_contract_lf5_temporal_zero_level.json) contracts.

## 2026-09-06 explicit user override

After reviewing the CPU-T result, the user explicitly authorized use of the
already-open V100 for the otherwise unchanged fixed DEV-T trajectory and its
original conditional P0. This is a higher-authority, post-qualification
override of the CPU stop condition; it does not rewrite the failed CPU result.
The resulting GPU evidence is labeled
`POST_QUALIFICATION_USER_OVERRIDE_EXPLORATORY` and cannot be presented as a
preregistered confirmation of the TZL premise. No loss, initialization, stream,
seed, budget, carrier gate, or P0 trigger was changed. The user also explicitly
added `README.md` and `docs/adr/README.md` to the exact LF5 write/stage
allowlist so the required consistency gate can pass.
