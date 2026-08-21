# G2 environment resolution attempt 005

- `run_id`: `20260819T110859Z-smoke-g2-env-resolve-attempt-005`
- `tier`: `smoke`
- `scientific_role`: `oracle_qualification`
- `gate`: `G2`
- `activity`: `environment_resolution`
- `execution_status`: `FAILED`
- `gate_outcome`: `G2_ENVIRONMENT_BLOCKED`
- `route_disposition`: `BLOCKED_ADDITIONAL_AUTHORITY_REQUIRED`
- `claim_status`: `NO_SCIENTIFIC_CLAIMS`

## VERIFIED

- The attempt was registered before execution with an intent bound to user authorization and specification SHA-256 `139969e1dcaf5cd18e4445516633e20cba1b2322c1717657e64213ff6f7dde85`.
- Focal installed `flex 2.6.4-6.2`; PETSc completed configuration and passed the earlier bison/flex checks.
- The resolver stopped before publishing `resolution.lock.json` because cached `fblaslapack` did not repeat its URL in the current configure log. Its clean checkout identifies official origin `https://bitbucket.org/petsc/pkg-fblaslapack` and commit `e8a03f57d64cf01d987d4b4ce9b961c24765747d`.
- Failure artifact: `outputs/environments/qpop-cpc-v1-ubuntu-20.04-source-stack-v1/attempt-005/resolve.failure.json`, SHA-256 `9adb78cbfec75fab67159f00ebdad4e708bbf4f82335bd9254d61d5946917010`.
- The finalized manifest and append-only index preserve the replay link to attempt 004 and report zero Q-POP processes.

## Post-stop implementation boundary

A focused red→green test now verifies that cached Git-backed PETSc externals are locked from their actual checkout origin, commit, tree and deterministic archive hash rather than requiring a repeated console URL. Read-only application to the existing prefix covered all seven Git-backed required packages, then stopped at MUMPS because PETSc deletes its downloaded tarball after extraction. No MUMPS pre-download, attempt 006, build, verify, Q-POP process, physical field, evaluator result, G3 activity or PINN output was created.
