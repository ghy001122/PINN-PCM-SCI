# G2 environment resolution attempt 004

- `run_id`: `20260819T105458Z-smoke-g2-env-resolve-attempt-004`
- `tier`: `smoke`
- `scientific_role`: `oracle_qualification`
- `gate`: `G2`
- `activity`: `environment_resolution`
- `execution_status`: `FAILED`
- `gate_outcome`: `G2_ENVIRONMENT_BLOCKED`
- `route_disposition`: `BLOCKED_ADDITIONAL_AUTHORITY_REQUIRED`
- `claim_status`: `NO_SCIENTIFIC_CLAIMS`

## VERIFIED

- The attempt was registered before execution with an intent bound to user authorization and specification SHA-256 `5b56f745bb4b9e6c13316f34ca8dd120a95efa72cff71587bc8eeb7d42e1c828`.
- Focal installed `bison 2:3.5.1+dfsg-1` and `m4 1.4.18-4`, closing the attempt-003 dependency failure.
- PETSc 3.15.1 then stopped at its next explicit PTScotch dependency check: `PTScotch needs flex installed`.
- Focal offers `flex 2.6.4-6.2`; it was not installed during this attempt.
- Failure artifact: `outputs/environments/qpop-cpc-v1-ubuntu-20.04-source-stack-v1/attempt-004/resolve.failure.json`, SHA-256 `760c8701626a875b19465d9e3f8a0721b323a73741116bd5fcebaf04bfa8bf41`.
- The finalized manifest and append-only index entry preserve the replay link to attempt 003 and report zero Q-POP processes.

## Post-stop implementation boundary

After the failure was frozen, `flex` was added to the subsequent stack specification and the public validator was strengthened to reject a PTScotch download contract without it. The corrected specification SHA-256 is `139969e1dcaf5cd18e4445516633e20cba1b2322c1717657e64213ff6f7dde85`. This has not been executed. No build, verify, native Q-POP smoke, physical field, evaluator result, G3 activity, or PINN output exists.
