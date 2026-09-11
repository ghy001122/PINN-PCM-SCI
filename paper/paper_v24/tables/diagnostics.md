# LF11 supplemental numerical tables

VERIFIED: derived from the saved adjudication, with no new training or metric evaluation.
All values refer to one nominal fixed-discretization case and initialization 17.

## Cycle-resolved results

| Method | Cycle | Recall | Precision | Active mass ratio | Abs timing | Recovery |
|---|---:|---:|---:|---:|---:|---:|
| warm_start | 1 | 0.8047543939 | 0.7629779962 | 1.054754394 | 0.03788 | 1 |
| warm_start | 2 | 0.8218376494 | 0.9330035336 | 0.8808515936 | 0.00215 | 1 |
| D_B | 1 | 0.8348355115 | 0.8023822415 | 1.040446147 | 0.03188 | 1 |
| D_B | 2 | 0.7396663347 | 0.9881902861 | 0.7485059761 | 0.01832 | 1 |
| P_U | 1 | 0.4583145561 | 0.9907452509 | 0.4625957639 | 0.038 | 1 |
| P_U | 2 | 0.4281623506 | 1 | 0.4281623506 | 0.04928333333 | 1 |
| P_I | 1 | 0.4621451104 | 1 | 0.4621451104 | 0.03833333333 | 1 |
| P_I | 2 | 0.4545567729 | 1 | 0.4545567729 | 0.04511666667 | 1 |
| P_M | 1 | 0.4628210906 | 1 | 0.4628210906 | 0.03833333333 | 1 |
| P_M | 2 | 0.4550547809 | 1 | 0.4550547809 | 0.04511666667 | 1 |
| B_L | 1 | 0.7778278504 | 0.9708901702 | 0.8011491663 | 0.008688888889 | 1 |
| B_L | 2 | 0.765064741 | 0.9639215686 | 0.7937001992 | 0.0078 | 1 |
| B_P | 1 | 0.7816584047 | 0.9694005868 | 0.8063316809 | 0.008485714286 | 1 |
| B_P | 2 | 0.7694223108 | 0.9617180205 | 0.8000498008 | 0.00732 | 1 |
| B_logit | 1 | 0.7929247409 | 0.9879281303 | 0.80261379 | 0.01527142857 | 1 |
| B_logit | 2 | 0.7721613546 | 0.9934326446 | 0.7772659363 | 0.01497142857 | 1 |
| dense_LF_ONLY | 1 | 0.985353763 | 0.9416451335 | 1.046417305 | 0.0025 | 1 |
| dense_LF_ONLY | 2 | 0.9937749004 | 0.9350984067 | 1.062749004 | 0.00295 | 1 |

## Independent uniform AD audits

Each row uses the same 4096-point reference-free integration; J is the mean of the three scaled MSEs.

| Method | Electric MSE | Thermal MSE | Phase MSE | J | BC | Observation |
|---|---:|---:|---:|---:|---:|---:|
| warm_start | 2.486088485 | 0.02856255232 | 0.003763407195 | 0.8394714817 | 0.1431274321 | 0.01036127372 |
| D_B | 1.90115213 | 0.02438769108 | 0.003878559334 | 0.6431394601 | 0.02182765268 | 0.008118317388 |
| P_U | 0.3547934329 | 0.02056260395 | 0.003297093089 | 0.12621771 | 0.02320800212 | 0.008183175996 |
| P_I | 0.3452450164 | 0.02016120934 | 0.00328563517 | 0.122897287 | 0.02296943544 | 0.00817230106 |
| P_M | 0.3454540094 | 0.02016235451 | 0.003286119202 | 0.1229674944 | 0.0229702275 | 0.008172287863 |

## Conditional direction decision

These are local prospective effects with actual Adam moments, not applied optimizer updates.

| Endpoint | Phase share of positive physical/BC phase-error effect | Phase to T error effect |
|---|---:|---:|
| P_U | 0 | -2.143433889e-09 |
| P_I | 0.004802810899 | -9.782437508e-10 |
| P_M | 0.003002777369 | -9.454631681e-10 |

Decision: NO_PHASE_METRIC_TRIGGER_NO_ADDITIONAL_TRAINING.
P_S/RAD/PF-GAR were not run because the positive matched-effect condition was not met.

## Complete machine-readable sources

- [Original metrics, cycles, validity, comparisons](../evidence/local/results.json)
- [All equation/head directions](../evidence/local/equation-head-diagnosis.json)
- [Conditional decision](../evidence/local/conditional-decision.json)
- [Posthoc waveform control](../evidence/local/waveform-diagnostic.json)

The waveform control keeps B_logit's phase, temperature, and cycle phase metrics unchanged.
Its posthoc status is retained separately from the frozen four-arm adjudication.
