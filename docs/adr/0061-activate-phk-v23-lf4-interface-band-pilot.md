# ADR 0061: Activate PHK-V2.3 LF4 interface-band pilot

- `status`: `ACCEPTED_EXECUTING`
- `date`: `2026-09-05`
- `phase_id`: `PHK_V23_LF4_THRESHOLD_ALIGNED_INTERFACE_BAND_MECHANISM_AND_CONDITIONAL_PHYSICS_PILOT_EXECUTE`
- `starting_head`: `7df29ef730ad60156dfae5abd4a3ef41fa69a109`
- `prior_art_disposition`: `NO_EXACT_FUNCTIONAL_COLLISION_FOUND_ATTRIBUTED_SOLVER_RECOVERY_SCREEN`

## Decision

Run three matched, fixed 400-update phase-only continuations from the exact
LF3-T0 endpoint. DEV-G controls for more generic target-measure supervision;
DEV-M changes only the extra sampling measure to the two-sided teacher
interface; DEV-C uses the identical interface coordinates but replaces the
extra regression term with a threshold-aligned two-sided softplus term. Only
an endpoint passing the preregistered entry gate may trigger the 1200-update,
label-free full-physics P0.

CPU-G found 481 false-negative and 227 false-positive W1/W3 nodes. Of these,
455 FN (94.6%) and 199 FP (87.7%) lie directly on the teacher interface graph.
This is executed support for an interface-localized residual error pattern,
not advance proof that DEV-M or DEV-C will succeed.

## Boundaries

The three arms share exact base draws 1201--1600, fixed endpoints, optimizer,
initial weights, and update count. DEV-M and DEV-C share exact band points.
Fine, extra-fine, direct LF_ONLY, the frozen evaluator, and stress remain off
cloud and unread until complete recovery and verified shutdown. No full-from-
LF1-B0 confirmation, new seed, OOD, stress, PJGR/R2, alternative architecture,
kinetic teacher, or submission is authorized.

Machine semantics are frozen in the LF4 [program](../../configs/phk_v23/program_contract_lf4_interface_band.json),
[method](../../configs/phk_v23/method_contract_lf4_interface_band.json),
[data](../../configs/phk_v23/data_contract_lf4_interface_band.json), and
[decision](../../configs/phk_v23/decision_contract_lf4_interface_band.json) contracts.
