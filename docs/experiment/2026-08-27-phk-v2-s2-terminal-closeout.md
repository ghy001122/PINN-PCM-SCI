# PHK-V2 S2 Oracle Gate terminal closeout

**Date:** 2026-08-27  
**Status:** `VERIFIED_TERMINAL_NO_GO`  
**Supersedes current-stage interpretation of:** S0/S0B pre-execution descriptions only  
**Preserves:** all preregistration contracts, immutable intents, run manifests, raw numerical carriers, failures, and prior project No-Go records

## 1. Terminal disposition

The preregistered PHK-V2 qualification ladder stopped at intent 9 with:

~~~text
PHK_V2_ORACLE_NO_GO_EVENT_CONTRACT_AND_CONTROL_EXECUTION_FAILURE
METHOD_ROUTE=STOP_BEFORE_PINN_TRAINING
CLAIM_STATUS=PHK_V2_ORACLE_NO_GO_NO_PINN_OR_PHA_OR_KC_OR_FORMAL_EVIDENCE
~~~

This is a bounded result for `PHK_REDUCED_WALL_CELL_2D_V1_NUMERICAL_V1`. It does not show that phase-field PINNs, PHA-MF, kinetics clocks, electrothermal phase-field models, or other numerical contracts fail in general. It also does not establish a calibrated material or experimentally validated device.

The authoritative machine result is [`summary.json`](../../outputs/runs/20260827T-phk-v2-s2-q-terminal-summary/summary.json), SHA256 `8964ACB687F1BDB4F03C2E0D33891EE3705D4C2ABD271085D0C82A2B4469EA78`. Its finalized run manifest is [`20260827T-phk-v2-s2-q-terminal-summary.json`](manifests/20260827T-phk-v2-s2-q-terminal-summary.json), SHA256 `29A570BC990D350FD85EF7A4B288FF703B83D8F6E54DE6BCB7742597FF5889DC`.

## 2. Frozen identities

| Carrier | Identity |
|---|---|
| Program contract | `0E1D89DD23F93C90160AC82ECE60ADA154410F4DDC33578CB892207FE8B445A8` |
| Object/numerical contract | `3B3B9A369F4AFDFFB201394DD294E7196BAF04E5B36BAFE126291CA9CB3EA157` |
| Complete-case split manifest file | `EBFDA2D59049AC989E8AA6C9622D92CF077D4B808961AB5807D178BF09DF57ED` |
| Internal split identity | `55261CCA82ED2B71A9D3A81E28FC957B4873086CECB09D28EEE9B73B2CD73E09` |
| Terminal summary | `8964ACB687F1BDB4F03C2E0D33891EE3705D4C2ABD271085D0C82A2B4469EA78` |

The physical object is a transparent dimensionless two-dimensional Cartesian wall-cell cross-section with a quasistatic electrical equation, transient heat balance, and Allen–Cahn-type phase fraction. Its coefficients are engineering contract values. The object is literature-inspired, not an author-model reproduction, GGST calibration, experimental truth, or open material oracle.

## 3. Intent-by-intent evidence

| Intent | Frozen role | Execution | Scientific interpretation |
|---:|---|---|---|
| 1 | Manufactured operators | `COMPLETED` | Operator checks passed; no scientific field result. |
| 2 | Zero drive, medium | `COMPLETED` | 800 steps passed zero-drive numerical guards; no event qualification. |
| 3 | Nominal coarse | `COMPLETED` | Numerical guards passed; two-cycle event contract failed. |
| 4 | Nominal medium | `COMPLETED` | Numerical guards passed; two-cycle event contract failed. |
| 5 | Nominal fine | `COMPLETED` | Numerical guards passed; two-cycle event contract failed. |
| 6 | Nominal medium, half time step | `COMPLETED` | Numerical guards passed; two-cycle event contract failed. |
| 7 | Exact replay of intent 5 | `COMPLETED` | All six replay component differences were exactly zero. |
| 8 | Joule gain off, medium | `COMPLETED` | Bounded synthetic thermal causal control; no event by design/result. |
| 9 | Phase-conductivity feedback off, medium | `FAILED_CONSUMED` | `RuntimeError: PHK phase Newton line search reached its frozen minimum step`. No result-adaptive rescue. |
| 10 | Latent heat off | `NOT_REACHED` | Blocked by terminal intent 9; not a failed scientific comparison. |
| 11 | Wide heater | `NOT_REACHED` | Blocked by terminal intent 9. |
| 12 | Narrow interface | `NOT_REACHED` | Blocked by terminal intent 9. |

Manifest hashes for intents 1–9, in order, are:

~~~text
B367BE5D674279BC5FAEFC39E0A2631773E0698A7FAA80EF1B2464BA0764BCEE
044D961E8366DA8AC0C99D4FBA3DD94E2935812961EC3D28A7A8DEC96D9831B7
9FBD316028B91A16BB03A5189D60C52F863ECC6D460889170CF24F6F82BF2360
EAD60B25F1063F85EDE3C88953E675594BCE96303E3599187F5FD0C82B111198
D53EAC8C1128ACE7436576BDC5D27A0FD0042F66C91EB9A4613E9E81CE442A7E
FEC36C6632D2872A6514097A027790EB744305C19C7E5E9EFB8EACF2D45E40B5
B1BCC444F630996EF030ECAFA544CBA4D90D8C8DEEBC80CA4DAB03B208295CAB
A405304FAED9B4D4B2DEB227F9468147B00F3902E8048390D769D97C18DF2464
~~~

The first line corresponds to intent 1; the remaining lines correspond to intents 2–9. Intent 7's manifest hash is the sixth line. The order is retained here to avoid treating filenames or prose as the identity carrier.

## 4. Numerical observations

### 4.1 Manufactured and zero-drive checks

The manufactured checks included a linear electric solution error of `7.216e-16`, current-balance error `2.516e-15`, power-identity error `4.441e-16`, and phase-Jacobian directional error `6.252e-11`. These are implementation checks on manufactured states, not validation against an external physical source.

The zero-drive medium run completed 800 steps. Its maximum scaled phase residual was `9.820e-11`, maximum thermal residual `5.638e-18`, and all hard guards passed. The reduced temperature maximum was `0.001703`; the phase fraction remained between approximately `8.047e-5` and `0.029948`. This is a zero-drive implementation guard, not an event-bearing oracle.

### 4.2 Event failure on nominal resolutions

All nominal spatial/time configurations produced a first-cycle threshold crossing, but recovery was far below the frozen minimum `0.7`. No configuration produced the required new upward crossing in cycle 2 because the phase fraction had not recovered sufficiently before the second pulse.

| Configuration | First event time | Cycle-1 recovery | Cycle-2 event | Cycle-peak relative drift |
|---|---:|---:|---|---:|
| coarse | 0.212100 | 0.227273 | missing | 1.409091 |
| medium | 0.217800 | 0.233533 | missing | 1.586826 |
| fine | 0.219908 | 0.238606 | missing | 1.587131 |
| medium half-dt | 0.219467 | 0.221557 | missing | 1.568862 |
| fine exact replay | 0.219908 | 0.238606 | missing | 1.587131 |

The frozen cycle-drift maximum was `0.2`; observed values were approximately `1.41–1.59`. These are event-contract failures even though the numerical hard guards passed.

### 4.3 Convergence and replay diagnostics

The six component orders are phase-field ROI RMS, temperature ROI RMS, current-trace RMS, event time, phase-region symmetric difference, and recovery. Unclipped component differences were:

| Comparison | Six-component vector |
|---|---|
| coarse vs medium | `[0.1152960, 0.0130288, 0.0121576, 0.00403051, 0.0113184, 0.0446725]` |
| medium vs fine | `[0.0440896, 0.00427422, 0.00384497, 0.00149082, 0.00381858, 0.0182278]` |
| medium vs medium-half-dt | `[0.0242407, 0.00318648, 0.00267207, 0.00117851, 0.00198254, 0.00858333]` |
| fine vs exact replay | `[0, 0, 0, 0, 0, 0]` |

The replay check passed the frozen `1e-12` limit. Because the event contract and a required control failed, these differences were not converted into a neural floor seal.

### 4.4 Bounded Joule causal control

The nominal-medium minus Joule-off comparison gave a peak reduced-temperature difference of `1.075707`, above its joint space/time uncertainty `0.00239908`, and a peak ROI phase-fraction difference of `0.892562`, above `0.0251570`. This establishes a bounded causal effect of the synthetic Joule term within the frozen benchmark. It is not material validation and cannot repair the two-cycle event failure.

## 5. Failed-compute accounting

The qualification chain records `1318.71875` process-CPU seconds (`0.3663107639` process CPU core-hours) and `1339.3720109` summed single-thread wall seconds. One failed intent is retained. There were no rescue attempts, replacement cases, replacement seeds, cloud/GPU runs, or post-result parameter changes.

## 6. Consequences for the proposed PHK methods

No training-ready oracle or pre-neural floor seal exists. Accordingly:

- strong raw PINN was not trained;
- the Sharp/PF/jaxpi2 identities were not compared on PHK field errors;
- PHA-MF and field-selective KC were not implemented as claim-bearing PHK arms;
- the 2×2 attribution design, adaptive pseudo-time falsification control, complete-case development pools, formal-aligned and formal-orthogonal pools were not opened;
- no method superiority, noninferiority, OOD, GPU, speed, or SOTA claim is estimable.

This is `NOT_REACHED`, not a negative PINN result. The scientific value is the preservation of an upstream qualification failure before neural approximation could turn an unqualified reference trajectory into a benchmark label.

## 7. Remaining unknowns and stop rule

It remains unknown whether the proposed modules help on a different, independently qualified object; whether the fixed external papers reproduce under their full original budgets; and whether a changed wall-cell contract could recover between two pulses. Answering any of those questions would require a new preregistered contract and new authority. The current PHK-V2 result must not be rescued by moving coefficients, event thresholds, cases, or budgets after seeing these outcomes.

