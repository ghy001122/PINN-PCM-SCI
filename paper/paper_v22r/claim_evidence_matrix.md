# Claim–evidence matrix

| Proposed statement | State | Evidence | Allowed wording |
|---|---|---|---|
| Four arms completed finite V100 training | `VERIFIED` | run summary and four final manifests | Direct factual claim |
| Logged PDE loss decreased for every arm | `VERIFIED` | four training logs and evaluator trend checks | Direct factual claim |
| All four arms missed both phase events | `VERIFIED` | four local evaluations and phase carriers | Direct factual claim |
| A small primary score can mask sparse-event failure | `SUPPORTED_INTERPRETATION` | identical 0.00515 score plus zero predicted active support | Bounded to this metric and case |
| The combined method improves over components | `REJECTED` | no eligible arm; no comparison gate reached | Must not claim |
| The sampler is beneficial | `UNKNOWN` | sampler-only has lower some scalar errors but fails competence | Diagnostic observation only |
| Multi-frequency representation is harmful | `UNKNOWN` | one seed and fixed budget; all arms fail competence | Must not generalize |
| PINNs cannot model phase-change devices | `REJECTED_EXTRAPOLATION` | evidence is one synthetic fixed protocol | Must not claim |
| Stress robustness or OOD generalization | `UNKNOWN` | stress references remain sealed/unread | Must not claim |
| Experimental or material validity | `UNKNOWN` | no experimental data or calibration | Must not claim |
| Continuum accuracy | `UNKNOWN` | fixed discrete target only | Must not claim |
| Negative Method-MVP outcome | `SUPPORTED` | immutable decision artifact | `MVP_NO_GO_NO_BASIC_COMPETENCE` |

## Claim audit result

The draft contains one central scientific interpretation: under the frozen
single-seed 1000-update protocol, loss reduction and small space–time-averaged
error did not imply localized event competence. All positive method, sealed-case,
formal-OOD, continuum, and experimental claims are excluded.
