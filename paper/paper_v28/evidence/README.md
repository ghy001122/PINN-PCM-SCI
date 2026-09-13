# Selected V28 evidence — completed research release

This package is copied from `outputs/runs/20260913-lf11-electrical-elimination`. It contains actual saved outputs, not proposed results. `selected-artifacts.json` lists every copied path. No training or reference recomputation occurred during copying. The selected files accompany the release containing this document; the older V27 parent and V24 sparse observations retain their published identities. Runtime manifests, terminal-summary and selected-artifacts retain their original unpublished/local fields as scientific-closeout snapshots. They are not current distribution metadata.

| Evidence | Location | Interpretation |
|---|---|---|
| Terminal status and actual computation | [terminal-summary.json](terminal-summary.json) | Two valid trained endpoints, two zero-training roles; P_F not triggered |
| All formal scores and separate A/B decision | [evaluation/results.json](evaluation/results.json), [conditional decision](evaluation/conditional-decision.json) | P_E−D_E A/B false, P_E−B_E A/B true |
| D_E−B_E and relative-change arithmetic | [endpoint-comparison-summary.json](endpoint-comparison-summary.json) | D_E−B_E also passes A/B; fixed-conductivity E0 vs historical D_I separated |
| Independent unlabeled fixed audit | [fixed-endpoint-unlabeled-audit.json](fixed-endpoint-unlabeled-audit.json) | Same remaining-PDE functional, zero optimizer/parameter-gradient updates; no holdout label claim |
| Plotting arrays | [traces.npz](evaluation/traces.npz), [snapshots.npz](evaluation/snapshots.npz) | Four roles and reference display data; reference-selected phase display times do not select endpoints |
| Actual D_E accepted endpoint | [D_E/checkpoint.pt](D_E/checkpoint.pt), [terminal](D_E/terminal.json) | 1500 Adam, 300 full evaluations, 147 accepted L-BFGS steps; optimizer included |
| Actual P_E accepted endpoint | [P_E/checkpoint.pt](P_E/checkpoint.pt), [terminal](P_E/terminal.json) | 1500 Adam, 300 full evaluations, 146 accepted steps; unaccepted final trial rolled back |
| Fixed development checkpoints and logs | `D_E/`, `P_E/` | Adam 500/1000/1500 checkpoints and optimizer/RNG states; both telemetry streams |
| Same-layer own readouts and inference counts | `E0/`, `D_E/`, `P_E/`, `B_E/` | `own-readout.npz` and `prediction.json`; actual fine-grid solve counts |
| Common parent and calibration | [parent.pt](parent.pt), [calibration](calibration.json), [input identity](input-manifest.json) | Parent chosen by no-interior-PDE role; one common aE/bE |
| Frozen config and pools | [frozen-config.json](frozen-config.json), `calibration-pool.json`, `lbfgs-pool.json`, `audit-pool.json` | Original target measures, physical windows, explicit budgets and guards |
| CPU and actual CUDA interface checks | [CPU](zero-update-checks-cpu.json), [CUDA](zero-update-checks-cuda-0.json) | Finite differences and linear residuals, not method-performance evidence |
| Actual deployment and shutdown | [cloud-deployment.json](cloud-deployment.json), [compute-closure.json](compute-closure.json) | Current authenticated runtime, recovered output, successful actual shutdown then refused connection before local reference scoring |
| Executed-source identity | [deployed-source-manifest.json](deployed-source-manifest.json) | Source selection used for training; inherited commit alone does not identify new implementation |

`preparation-summary.json` is the original zero-update snapshot, not a terminal budget record. Raw terminal/log files retain internal computation metadata; manuscript tables report optimizer and solve counts without a speed claim.

Full per-role `prediction.npz` arrays and full nominal high-fidelity reference fields are deliberately not duplicated into this compact package. They remain in the local outputs tree. The existing sparse input is [the unchanged V24 file](../../paper_v24/evidence/input/sparse.npz); E0's parent provenance is [V27 D_I](../../paper_v27/evidence/D_I/checkpoint.pt). No new labels, full thermal/phase trajectory solve, stress or independent case appears here. A reviewer can regenerate figures and inspect scores from this package; it does not by itself allow independently recomputing all scores without the retained raw reference and predictions.

See the [reproduction entry](../reproducibility.md) and [claim matrix](../claim_evidence_matrix.md). Source-level reproduction of learning is distinct from rendering already saved numerical evidence.
