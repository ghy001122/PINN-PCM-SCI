# G1 pipeline smoke fact record

- `run_id`: `20260819T054521Z-smoke-pipeline-fixture-001`
- `tier`: `smoke`
- `scientific_role`: `pipeline`
- `gate`: `G1`
- `gate_outcome`: `SMOKE_PASS`
- `evidence_identity`: `ENGINEERING_CONTROL_FLOW_ONLY`
- `claim_status`: `NO_NUMERICAL_EVIDENCE`

## VERIFIED

- The project-local Python 3.11.9 environment completed the fixed path
  `raw JSON -> CaseArtifact HDF5 -> one float64 CPU model update -> checkpoint
  + PredictionArtifact HDF5 -> evaluator subprocess -> metrics JSON`.
- The runtime recorded NumPy 2.1.1, h5py 3.12.1, and PyTorch 2.5.1+cpu.
  The direct requirements and their transitive closure are frozen under
  `requirements/`.
- Seventeen contract tests passed in the same project environment. They cover
  artifact round trips, disk-only evaluation, hand-computed metrics,
  deterministic replay, invalid units, missing fields, non-finite values,
  case/contract/split/time mismatches, empty cycle windows, and success/failure
  ledger behavior.
- Re-evaluating the finalized prediction from disk produced byte-identical
  metrics. Both files had SHA-256
  `EC51EE806AE1B0CB33326B23446442A8A1D047F167993AF1B82D5C0ED5B83626`.
- The finalized manifest and append-only index pass the one-to-one ledger
  validator.

The compact run record is
[20260819T054521Z-smoke-pipeline-fixture-001.json](manifests/20260819T054521Z-smoke-pipeline-fixture-001.json).
Raw artifacts remain under the manifest-recorded `outputs/runs/<run_id>/`
location.

## Claim boundary

The fixture is explicitly non-scientific, the tiny model is not a PINN, and the
reported metric values have no VO2, Q-POP, or kinetics-clock meaning. G1 proves
only that the engineering control flow and bookkeeping contract execute.
