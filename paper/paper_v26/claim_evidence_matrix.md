# Claim–evidence matrix

| Claim | Status | Direct evidence | Boundary |
|---|---|---|---|
| Interface supervision exposure improves recall across three sampling streams | VERIFIED, inherited | paper_v23 / LF10 terminal | Same initialization; quality retained in two streams |
| LF11 four-arm PDE/sampling/phase metric has no declared joint increment | VERIFIED, inherited | paper_v24 original results and code | One nominal recipe; not all PINNs |
| Large temperature fitting gap is repairable within the unchanged envelope | VERIFIED, inherited | paper_v25 S0/S1 | Adapter and optimization not independently isolated |
| Resumed V-only fitting lowers the complete observation objective 53.23% | VERIFIED | evidence/v-result.json, v-telemetry.jsonl, endpoint-with-V-optimizer.pt | 200 evaluations, 99 accepted steps; no approximation-floor or convergence claim |
| V-only repair improves energy and power at identical conductivity | VERIFIED | evidence/evaluation.json and exact non-V state preservation | Controlled voltage-function effect; no phase or PDE gain |
| Boundary trace accounts for 99.41% of signed integrated bottom-current decrease | VERIFIED | evidence/electric-pre/post.npz and evaluation derived attribution | Exact finite-grid decomposition; not an RMS share or universal root cause |
| The soft contact trace materially affects this FV readout | SUPPORTED_INTERPRETATION | Current/power decomposition, fixed conductivity, known-contact baseline | No grid-refinement or junction singularity proof |
| Known heater endpoints improve same-observation direct device readout | VERIFIED | evidence/contact-baseline-check.json and evaluation.json | No new labels, training or PDE solve; unchanged T/phase |
| Strong-parent interior-PDE increment; conductivity-normalization benefit | UNKNOWN / NOT_RUN | evidence/compute-closure.json | V admission was not met; no negative method outcome is inferred |
| A compatible V boundary representation will repair the remaining problem | HYPOTHESIS | Motivated by current decomposition and contact control | Requires a separate approved comparison; no promised success |
| Robust method, formal OOD or calibrated oxide-device prediction | UNKNOWN | No new independent initialization, mask or case | Synthetic dimensionless nominal model only |

The next paper may incorporate successful matched methods only after their evidence exists. The present manuscript integrates diagnostic results without converting ordinary optimization or interpolation controls into a novel PINN.

