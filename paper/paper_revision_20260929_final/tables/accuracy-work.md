Actual work for the fixed endpoints in the interface-effect comparison. Accuracy uses the unchanged common-reader errors in the adjacent effect table; the work below is not a wall-time speed comparison.

| Protocol/seed | Role | Adam | L-BFGS evaluations / accepted steps | Training forward / adjoint solves | Explicit face evaluations |
| --- | --- | --- | --- | --- | --- |
| Original/29 | E | 1500 | 300 / 145 | 19,612 / 19,612 | NR |
| Original/29 | F | 1500 | 300 / 147 | 0 / 0 | 7,800 |
| Original/43 | E | 1500 | 300 / 144 | 19,560 / 19,560 | NR |
| Original/43 | F | 1500 | 300 / 146 | 0 / 0 | 7,800 |
| Shorter/29 | E | 1500 | 300 / 145 | 19,608 / 19,608 | NR |
| Shorter/29 | F | 1500 | 300 / 147 | 0 / 0 | 7,800 |
| Shorter/43 | E | 1500 | 300 / 146 | 19,578 / 19,578 | NR |
| Shorter/43 | F | 1500 | 300 / 149 | 0 / 0 | 7,800 |
| Shorter/29 | F_cov | 1500 | 300 / 148 | 0 / 0 | 31,547 |
| Shorter/43 | F_cov | 1500 | 300 / 146 | 0 / 0 | 31,524 |

NR = not recorded in that log, not zero. Every arm completed 1500 Adam updates and 300 full L-BFGS evaluations; trial/repeated closures count, and budget interruption may roll back to the last accepted state. Sparse-solve counts and explicit face-operator calls are distinct work measures. A zero sparse-solve count does not mean zero electrical or AD work. Shorter-protocol E counters come directly from per-arm terminal records: 19608 and 19578, whose sum matches the frozen 39186 aggregate; no aggregate was divided between seeds.

| Separate stage | Recorded scope and work |
| --- | --- |
| Shared parents | Per protocol and seed: 2400 Adam + 600 full evaluations; charged once. F_cov reuses the shorter parents. |
| Shared calibration | 50 forward / 0 adjoint solves per parent; F_cov inherits the scales without recalibration. |
| Historical projected readout | Original E/F: 278 forward solves per endpoint. Shorter: 1390 aggregate across four endpoints and one B_E. These are not totals for the two later common readers. |
| F_cov common readout | 278 forward solves per grid and seed, 556 per endpoint; no adjoint solve. Coarse/fine grids remain separate. |
| Discarded readout work | F_cov seed 29: 0; seed 43: at most 1 in-flight solve. This is separate from completed work. |

Historical E records contain `elapsed_seconds_internal`; F records lack matching time fields. F_cov records `current_session_seconds` (3710.590 and 3742.518 s), excluding separately logged profiles and readout. These fields do not establish a common timing boundary or an acceleration ratio. The original clean-confirmation environment and F_cov environment identify a Tesla V100-PCIE-32GB, Python 3.11.9, Torch 2.5.1+cu118, NumPy 2.1.1 and SciPy 1.14.1; F_cov records four CPU threads. A complete comparable historical hardware/thread/timing record is not asserted. Raw timing fields, termination, and direct sources are retained in [accuracy-work-full.csv](accuracy-work-full.csv); stage boundaries and provenance are in [accuracy-work-stages.csv](accuracy-work-stages.csv).
