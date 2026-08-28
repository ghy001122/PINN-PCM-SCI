# PHK-V2.1 E2 non-voting engineering object selection

- `date`: `2026-08-27`
- `run_id`: `20260827T-phk-v21-e2-engineering-search-001`
- `stage`: `E2_BOUNDED_NON_VOTING_OBJECT_DESIGN`
- `execution_status`: `COMPLETED`
- `gate_outcome`: `PHK_V21_E2_ENGINEERING_OBJECT_CANDIDATE_SELECTED`
- `evidence_identity`: `NON_VOTING_ENGINEERING_ONLY`
- `scientific_claim_status`: `NO_OBJECT_ORACLE_EVENT_PINN_METHOD_OR_FORMAL_EVIDENCE`

## Decision

`VERIFIED`: the complete preregistered campaign executed 16 stage-1 coarse cases, 16 stage-2 coarse refinements, three fixed medium promotions and six controls for one uniquely selected nominal case. All `41/41` records executed and passed numerical guards; no case was replaced, no threshold was moved, and no rescue solver or time-step switch was used.

The selected engineering candidate is:

| Field | Frozen candidate value |
|---|---:|
| case ID | `PHK_V21_E2_STAGE2_0A1813B1D968F573` |
| physical identity SHA256 | `0A1813B1D968F573764DBDBD0FFF149AA0A6F265AEAB08E5140741205EAF16AF` |
| parent | `PHK_V21_E2_STAGE1_5F35AFC141AD7800` |
| period | `1.25` |
| volumetric cooling | `4.0` |
| cold/hot mobility | `0.5 / 5.0` |
| thermal drive | `6.0` |
| waveform amplitude | `0.72` |
| pulse hold end | `0.27` |
| latent ratio | `0.05` |
| heater-width fraction | `0.35` |
| interface width | `0.04` |
| fixed phase solver | `LOGIT_NEWTON_ANALYTIC_JACOBIAN` |

This case is admitted only as the input to a new scientific freeze. It is not yet a qualified oracle or a paper result.

## Medium event observations

| Case | Event gate | Minimum recovery | Cycle-peak drift | Peak outside ROI | CPU s |
|---|---:|---:|---:|---:|---:|
| `0A1813...` | pass | `1.0` | `0.0588235294` | `0.0` | `123.46875` |
| `288E14...` | pass | `1.0` | `0.1290322581` | `0.0` | `122.484375` |
| `3DD735...` | fail: cycle drift | `1.0` | `0.3157894737` | `0.0` | `119.40625` |

The selected case had first/second upward event times `0.2378` and `1.4942`, ROI phase peaks `0.0702479339` and `0.0661157025`, full-domain peak fractions `0.02125` and `0.02`, recovery `1.0` in both cycles, and `92/87` saved samples at or above the event threshold. These are medium engineering observations only; spatial/time convergence and oracle uncertainty are not yet evaluated.

## Control disposition

| Medium control | Executed | Numerical guard | Event | Engineering interpretation |
|---|---:|---:|---:|---|
| zero drive | yes | pass | absent | required no-event sentinel passes |
| Joule gain zero | yes | pass | absent | required no-event sentinel passes |
| phase-conductivity ratio one | yes | pass | present | old failing branch is now executable; causal effect not yet adjudicated |
| latent ratio zero | yes | pass | present | executable; causal effect not yet adjudicated |
| heater width `0.50` | yes | pass | fails cycle-2 event | retained geometry sensitivity boundary |
| interface width `0.025` | yes | pass | present | executable; causal effect not yet adjudicated |

The wide-heater event failure is not hidden and does not invalidate the selected nominal case under the frozen E2 acceptance rule, which required all controls to execute and pass numerical guards while requiring no event specifically for zero/Joule-off. It must be represented in the new whole-factor split and cannot be called geometry robustness.

## Numerical and compute accounting

- Campaign process CPU: `1593.953125 s = 0.44276475694444445 core-hour`.
- Campaign wall time: `1612.5088280000055 s`.
- Failed case records: `0`.
- Selected nominal maximum current mismatch: `4.7658221515817719e-14`.
- Selected nominal maximum thermal residual: `9.6178731645579774e-10`.
- Selected nominal maximum phase residual: `9.8681963642266446e-10`.
- Selected nominal phase range: `[2.4768914759293673e-12, 0.9903678310484147]`.

## Immutable carriers

| Carrier | SHA256 |
|---|---|
| `outputs/runs/20260827T-phk-v21-e2-engineering-search-001/summary.json` | `DAC816914ABFC686CD26D93EC643F642031F4AB62B85E4CBE6B52496E2613E19` |
| `outputs/runs/20260827T-phk-v21-e2-engineering-search-001/case-records.jsonl` | `440024389FF5C16D20C4316D6D6AABB20EE5874095E9BB19366536E8B8CD0F28` |
| `docs/experiment/intents/20260827T-phk-v21-e2-engineering-search-001.json` | `545225053FBB94B547D9F53FBD132AAA00F9FB0DF8D88FA2534645D93265E0B3` |
| `docs/experiment/manifests/20260827T-phk-v21-e2-engineering-search-001.json` | `E54020DA3DB24378CADB0F878B250568A97224669BE0D73FDF3AD821471945F2` |

The ledger and authority consistency gate both passed after finalization. The next admissible step is to implement and hash an independent PHK-V2.1 benchmark, then freeze the new object, complete-case split, oracle/floor, baseline-replication and method contracts before any voting numerical or neural result.
