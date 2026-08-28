# Claim–evidence matrix

## Allowed manuscript claims

| ID | Claim | Status | Direct evidence | Ceiling / prohibited extension |
|---|---|---|---|---|
| C1 | Source paper, repository, and license identities were separated and fixed before PHK method work. | `VERIFIED` | R0 source audit; fixed SHAs | Does not prove paper-result reproduction. |
| C2 | The PHK object is a transparent dimensionless 2D electrothermal phase-field wall-cell. | `VERIFIED` | object contract; solver implementation | Not a GGST/PCM material calibration, author-model reproduction, or experimental device. |
| C3 | Program, object, numerical, split, event, guard, and stop contracts preceded the first PHK solve. | `VERIFIED` | S0/S0B governance records and hashes | Governance timing does not validate physics. |
| C4 | Manufactured electric/power checks and one phase-Jacobian direction met their checks. | `VERIFIED` | intent 1 report | Does not prove global implementation correctness. |
| C5 | The zero-drive medium run completed 800 steps and passed its numerical guards. | `VERIFIED` | intent 2 result/report/manifest | Not an event-bearing oracle or material validation. |
| C6 | Nominal coarse, medium, fine, half-dt, and replay runs passed hard numerical guards. | `VERIFIED` | intents 3–7 reports | Does not imply the event contract passed. |
| C7 | First-cycle event times approached about 0.22 under tested refinement. | `SUPPORTED_INTERPRETATION` | event reports + component comparisons | No asymptotic convergence theorem or external truth. |
| C8 | First-cycle recovery was 0.22–0.24, second upward events were missing, and peak drift was 1.41–1.59. | `VERIFIED` | intents 3–7 event reports | Bounded to frozen object/waveform/thresholds. |
| C9 | Fine exact replay produced zero difference for all six components. | `VERIFIED` | intent 5 vs 7 comparison | Determinism in tested environment only. |
| C10 | Turning off Joule gain changed peak temperature and phase response above tested joint uncertainty. | `VERIFIED` | intent 4 vs 8 thermal record | Synthetic causal effect only; not material validation. |
| C11 | Intent 9 failed at the frozen phase-Newton minimum line-search step and was consumed without rescue. | `VERIFIED` | failed manifest + accounting | Does not prove phase-conductivity feedback is physically necessary. |
| C12 | The Oracle Gate terminal outcome is a combined event-contract and required-control execution No-Go. | `VERIFIED` | terminal summary SHA `8964AC...EA78` | Not a global model, solver, or physics No-Go. |
| C13 | No neural floor was sealed and no PINN/PHA/KC/formal stage was reached. | `VERIFIED` | terminal summary; absence bound to ladder | Cannot be reported as zero gain or a negative method comparison. |
| C14 | Stopping before training prevents this unqualified trajectory from becoming claim-bearing neural reference data. | `SUPPORTED_INTERPRETATION` | preregistered dependency graph + terminal stop | Methodological interpretation, not proof that all benchmark studies fail. |

## Claims that remain unknown

| ID | Unknown | Why no estimate exists |
|---|---|---|
| U1 | Sharp/PF/jaxpi2 paper metrics under their full original budgets in this environment | only bounded module smokes were run |
| U2 | strong raw PINN competence on a qualified PHK object | no qualified oracle/floor |
| U3 | PHA-MF main effect | method stage not reached |
| U4 | field-selective KC main effect | method stage not reached |
| U5 | PHA×KC interaction | factorial stage not reached |
| U6 | adaptive pseudo-time versus KC | falsification control not reached |
| U7 | complete-case/OOD performance | D/I/F pools never opened |
| U8 | GPU cost or speedup | no GPU was available or authorized after the gate |
| U9 | experimental relevance | no calibration or experimental validation data |
| U10 | whether a changed object can recover twice | changing the contract requires a new study |

## Forbidden wording self-check

| Avoid | Use instead |
|---|---|
| “PINN failed” | “PINN evaluation was not reached because the Oracle Gate failed.” |
| “the model is invalid” | “the frozen object/numerical/event/control contract did not qualify for this study.” |
| “two switching cycles” | “one first-cycle upward crossing followed by insufficient recovery and no new second crossing.” |
| “Joule heating validates PCM physics” | “the synthetic Joule term produced a resolved effect within the frozen benchmark.” |
| “grid-converged oracle” | “tested space/time differences decreased and exact replay passed, while event qualification failed.” |
| “Sharp-PINNs reproduced” | “fixed-source Sharp module smoke passed; paper metrics were not reproduced.” |
| “PHA-MF/KC showed no benefit” | “PHA-MF/KC were not run and remain unknown.” |
| “formal failed” | “formal was not reached.” |
| “Q2-ready/accepted/SOTA” | “evidence-bounded local negative/limits manuscript; journal fit remains unknown.” |

