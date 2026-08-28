# PHK-V2.1 final tables

## Table 1. Route disposition

| Stage | Required evidence | Observed status | Disposition |
| --- | --- | --- | --- |
| E1 solver engineering | one fixed control-branch solver passes bounded sentinels | logit analytic Newton selected | PASS, non-voting |
| E2 object design | one localized, recoverable two-cycle candidate | 41/41 bounded cases completed; one candidate selected | PASS, non-voting |
| S0 freeze | object, split, oracle/floor, baseline and method contracts fixed before results | five contracts hashed | PASS |
| S1 execution | complete 14-intent ladder without replacement | 14/14 completed; 0 solver failures | PASS |
| S1 hard guards | every voting numerical guard passes | 0 hard-guard failures | PASS |
| S1 convergence/floor | all six components monotonically contract | event-time component fails | **NO-GO** |
| S2–S6 | baseline, PINN, attribution, formal OOD | no admissible oracle/floor | NOT_REACHED |

## Table 2. Frozen scientific identities

| Carrier | SHA256 |
| --- | --- |
| object/numerical contract | BDC86AE4C1417E16A8772A88F7738B59D4F0D7BB3B272D1FFEC9E9572CF9CBDD |
| complete-case split | FC4F27D92618BBDF222961340C7BDA3FA8CB3FEF918D0CF343A48A5387F4BAB7 |
| oracle/floor contract | E596A5D50BB79A241928D98AC000BDCDD3AD7AF0B207BD5882F2D1C2EBB2E5FB |
| baseline replication contract | 195C039C181DCF012F94B77DA5D03EFF3244CDCA2F4A63FF5DEDB6FD7747EBC4 |
| method contract | F1E918E6C71557BF7ABBAE11519208BD3D042D04AC6AF04471F33CCB046A001D |
| program contract | B47CB3E131326077EF8D3EC50473B4F6A06D61E63B09861ECEF834901BE4D2A2 |
| terminal summary | 5E6343D3E8DFE63C1C3F2F031FCF04B455E8C53B5BF454F8AFA013D33C33A9C9 |
| terminal manifest | 607CF2F5B58715F6B9335A4CF41379A311DAA9DF1C7CEA880F0A534AF5923455 |
| candidate floor carrier | 3B71753CBAC720C1CF5F7937741FCF605693C5580988C848113AC9378F1A01F7 |

The candidate floor is a retained diagnostic carrier, not an admissible neural floor.

## Table 3. Qualification intent accounting

| # | Intent/control | Execution | Numerical guard | Event status | CPU s |
| ---: | --- | --- | --- | --- | ---: |
| 1 | manufactured operators | completed | n/a | n/a | 0.015625 |
| 2 | zero drive, medium | completed | pass | required no-event pass | 47.359375 |
| 3 | nominal coarse | completed | pass | two-cycle pass | 19.359375 |
| 4 | nominal medium | completed | pass | two-cycle pass | 105.40625 |
| 5 | nominal fine | completed | pass | two-cycle pass | 512.125 |
| 6 | nominal extra-fine | completed | pass | two-cycle pass | 1915.8125 |
| 7 | nominal medium half-dt | completed | pass | two-cycle pass | 238.125 |
| 8 | fine exact replay | completed | pass | two-cycle pass; array delta 0 | 556.40625 |
| 9 | Joule gain zero | completed | pass | required no-event pass | 54.265625 |
| 10 | conductivity ratio one | completed | pass | two-cycle, recorded control | 117.4375 |
| 11 | latent ratio zero | completed | pass | two-cycle, recorded control | 118.78125 |
| 12 | heater width 0.50 | completed | pass | cycle 2 absent, recorded control | 114.453125 |
| 13 | interface width 0.025 | completed | pass | two-cycle, recorded control | 129.421875 |
| 14 | pseudo-transient cross-check | completed | pass | two-cycle pass | 133.6875 |

Total recorded S1 solver compute: 4062.65625 CPU seconds = 1.128515625 process CPU core-hours. No GPU work and no failed solver intent were recorded.

## Table 4. Nominal event times

| Resolution | Cycle 1 | Cycle 2 | Recovery 1 | Recovery 2 |
| --- | ---: | ---: | ---: | ---: |
| coarse | 0.2271 | 1.4871 | 1.0 | 1.0 |
| medium | 0.2378 | 1.4942 | 1.0 | 1.0 |
| fine | 0.2389833333 | 1.495975 | 1.0 | 1.0 |
| extra-fine | 0.2406 | 1.4984 | 1.0 | 1.0 |

## Table 5. Decisive component-wise convergence

| Component | Medium→fine | Fine→extra-fine | Monotonic | Strict contraction | Candidate U |
| --- | ---: | ---: | --- | --- | ---: |
| phase-field ROI RMS | 0.009164723390798192 | 0.0045916542647892284 | pass | pass | 0.0045916542647892284 |
| temperature-field ROI RMS | 0.0025375404500889136 | 0.001256919148376367 | pass | pass | 0.0017839022220207273 |
| terminal-current trace RMS | 0.002326069016938981 | 0.0012107207785293857 | pass | pass | 0.0020456785528971074 |
| two-cycle event-time RMS | 0.0012067679515502204 | 0.0016486829760616161 | **fail** | **fail** | 0.0016486829760616161 |
| time-averaged phase-region symmetric difference | 0.00030374999999999993 | 0.000145 | pass | pass | 0.000145 |
| two-cycle recovery RMS | 0 | 0 | pass | pass | 0.000001 |

## Table 6. Control interpretation

| Control | Observed event behavior | Bounded interpretation |
| --- | --- | --- |
| zero drive | no event; ROI peak 0 | implementation and no-drive guard pass |
| Joule gain zero | no event; ROI peak 0 | Joule heating is necessary within this frozen synthetic object |
| conductivity ratio one | two events | phase-dependent conductivity is not individually necessary under this control |
| latent ratio zero | two events | frozen latent term is not individually necessary under this control |
| heater width 0.50 | cycle 2 absent | selected object is heater-geometry sensitive |
| interface width 0.025 | two events | event retained under this interface control |

## Table 7. Downstream evidence boundary

| Item | Status | Allowed claim |
| --- | --- | --- |
| transparent synthetic object execution | verified | 14/14 intents completed |
| nominal two-cycle event existence | verified | event-valid under all nominal resolutions |
| oracle qualification | failed | frozen S1 contract No-Go |
| candidate floor carrier | retained, not qualified | diagnostic only |
| Sharp/PF author metrics | not reached | no reproduction claim |
| strong raw PINN | not reached | no competence claim |
| PHA-MF / KC / full | not reached | no positive or negative method claim |
| GPU / formal OOD | not reached | no generalization or superiority claim |
| experimental/material validation | absent | no real-device claim |
