# PHK-V2.2R Claim-to-Artifact Registry

Status: `IMPLEMENTATION_EVIDENCE_INDEXED_NO_NEURAL_METHOD_RESULT`

| Claim or manuscript token | Required artifact | Current status |
|---|---|---|
| `PROFILE_TABLE` | Per-arm 100-update profile, peak memory, seconds/update, AD-call ledger | `NOT_YET_MEASURED` |
| `NOMINAL_ROUTE_RESULT` | Frozen nominal decision report and candidate-freeze manifest | `NOT_YET_MEASURED` |
| `NOMINAL_METRICS_TABLE` | Local evaluator output against nominal extra-fine carrier | `NOT_YET_MEASURED` |
| `NOMINAL_FIELD_FIGURE` | Indexed field snapshots generated from prediction and reference carriers | `NOT_YET_MEASURED` |
| `NOMINAL_QOI_FIGURE` | Current, Joule, phase-area, peak-temperature time series | `NOT_YET_MEASURED` |
| `ABLATION_TABLE` | Raw, MF-only, sampler-only, MF+sampler, equal-compute raw | `NOT_YET_MEASURED` |
| `SEALED_STRESS_TABLE` | Frozen three-arm evaluation on narrow-interface and wide-heater | `SEALED_REFERENCES_NOT_GENERATED` |
| `STRESS_FIGURE` | Indexed stress-case field/QoI panels | `NOT_YET_MEASURED` |
| `SUPPORTED_CLAIM` | Machine adjudication from frozen decision contract | `UNKNOWN` |

Implementation-only evidence: `tests/test_phk_v22r_pinn.py` passes 12 focused
tests, including one real optimizer update and reference-blind prediction-carrier
generation. This does not populate any result token above.

No manuscript result may be populated from terminal output, memory, or an
unindexed scratch run. Every numeric statement must point to an immutable run ID,
configuration hash, prediction-carrier hash, reference hash, and evaluator version.
