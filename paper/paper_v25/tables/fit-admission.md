| Metric | Original parent | Base optimization | Final fit | Admission |
|---|---|---|---|---|
| T RMS / .45 (all) | 0.178232659 | 0.040357134 | 0.011374919 | <=0.02; PASS |
| T RMS / .45 (heating) | 0.259754951 | 0.063799821 | 0.018357409 | <=0.05; PASS |
| T RMS / .45 (off) | 0.136117861 | 0.026839631 | 0.007218596 | <=0.05; PASS |
| V RMS / .72 | 0.015670471 | 0.013247177 | 0.008215100 | <=0.005; FAIL |
| Visible phase RMS | 0.015015394 | 0.015015394 | 0.015015394 | <=1.05 x parent; PASS |
| Full phase-logit objective | 0.000331037651 | 0.000331037651 | 0.000331037651 | <=1.05 x parent; PASS |

These are training/development errors, not held-out validation. Base-to-final improvement includes further optimization and the single adapter; it is not an isolated adapter ablation.
