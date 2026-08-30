# PHK-V2.2R Claim-to-Artifact Registry

Status: `V11_PROFILE_INDEXED_FOUR_ARM_NOMINAL_PENDING`

| Claim or manuscript token | Required artifact | Current status |
|---|---|---|
| `PROFILE_TABLE` | Frozen five-arm 100-update V100 profile, local gain-gate adjudication, peak memory and seconds/update | `VERIFIED_PROFILE_ONLY` |
| `NOMINAL_ROUTE_RESULT` | Four v1.1 local evaluations and frozen nominal decision report | `PENDING_FOUR_ARM_NOMINAL` |
| `NOMINAL_METRICS_TABLE` | Local evaluator outputs against nominal extra-fine carrier | `PENDING_FOUR_ARM_NOMINAL` |
| `NOMINAL_FIELD_FIGURE` | Indexed field snapshots from nominal predictions and development reference | `PENDING_FOUR_ARM_NOMINAL` |
| `NOMINAL_QOI_FIGURE` | Current, Joule, phase-area and peak-temperature traces | `PENDING_FOUR_ARM_NOMINAL` |
| `ABLATION_TABLE` | Strong raw, MF-only, sampler-only and MF+sampler fixed-update comparison | `PENDING_FOUR_ARM_NOMINAL` |
| `CONFIRMATION_PLAN` | Passing nominal decision plus selected, strongest comparator and parameter-matched measured-time raw identities | `CONDITIONAL_ON_NOMINAL_PASS` |
| `CANDIDATE_FREEZE` | Six reference-blind stress carriers verified against the confirmation plan and byte seals | `CONDITIONAL_ON_NOMINAL_PASS` |
| `SEALED_STRESS_TABLE` | Frozen three-role evaluation on narrow-interface and wide-heater | `REFERENCES_HASH_SEALED_UNREAD` |
| `STRESS_FIGURE` | Indexed stress-case field and device-QoI panels | `CONDITIONAL_ON_FINAL_FREEZE` |
| `SUPPORTED_CLAIM` | Machine adjudication and evidence-bounded manuscript branch | `UNKNOWN` |

The profile source is
`outputs/runs/20260830T0122-phk-v22r-d1-gpu-profile-cf372713/` with profile
summary SHA256
`5CE0768F7A7A1976D573846D05C244AD4E08E35D3B242292860A39BF097087DD`
and local adjudication SHA256
`7F76F3AA12E9A32F21ECFAB083FB530AC39310C1C83198CB691F8F3A1224BB0E`.
It verifies finite GPU execution and removes strict PHA; it does not rank the
four active arms or populate a neural method result.

P0 v1.1 uses four arms, FP64, seed 17, Band A, scratch starts,
`512/128/128` points, Adam for exactly 1000 updates, and final checkpoint only.
A nominal PASS authorizes generation of six reference-blind confirmation
predictions but does not authorize stress-reference access. Only a final
`phk-v22r-candidate-freeze-v1-1` artifact with all six carrier identities and
hashes may open the sealed references locally.

No manuscript result may be populated from terminal output, memory, or an
unindexed scratch run. Every numeric statement must point to an immutable run ID,
configuration hash, prediction-carrier hash, reference hash, contract hash, and
evaluator version.
