# G2 environment resolution attempt 003

- `tier`: `smoke`
- `scientific_role`: `oracle_qualification`
- `gate`: `G2`
- `activity`: `environment_resolution`
- `execution_status`: `FAILED`
- `gate_outcome`: `NOT_EVALUATED`
- `route_disposition`: `BLOCKED_ADDITIONAL_AUTHORITY_REQUIRED`
- `claim_status`: `NO_SCIENTIFIC_CLAIMS`

## VERIFIED

- The user explicitly authorized this one additional environment-resolution attempt.
- The attempt ran from `2026-08-19T10:25:43.449078Z` to `2026-08-19T10:27:58.937924Z` in the dedicated `PINN-PCM-SCI-Ubuntu-20.04` WSL2 distribution.
- PETSc consumed the frozen `/usr/bin/gcc-9` and `/usr/bin/g++-9` SOWING bindings. SOWING completed configure, make, and install; METIS, ParMETIS, and FBLAS/LAPACK also progressed beyond their configuration stages.
- Resolution failed before build/verify at PTScotch because `bison` was absent. PETSc 3.15.1 explicitly requires that executable for the requested `--download-ptscotch` path.
- Failure artifact: `outputs/environments/qpop-cpc-v1-ubuntu-20.04-source-stack-v1/attempt-003/resolve.failure.json`, SHA-256 `5d13758369875d94564ab91b8e611744437807b9ca238f13b66085cfae000d2e`.

## Boundary

This was an environment-resolution activity, not a Q-POP solver run. It produced the stage failure record above rather than a scientific run artifact; no Q-POP process, physical field, circuit trajectory, evaluator result, or PINN output exists.

After the failure was frozen, Focal `bison 2:3.5.1+dfsg-1` was added to the subsequent stack specification and the public static validator was strengthened to reject a PTScotch download contract without it. The corrected specification SHA-256 is `5b56f745bb4b9e6c13316f34ca8dd120a95efa72cff71587bc8eeb7d42e1c828`. This change has not been executed; a new attempt still requires an explicit user decision.

The attempt is indexed as `20260819T102543Z-smoke-g2-env-resolve-attempt-003`. Its manifest is a transparent retrospective reconstruction from the immutable stage evidence, links back to attempt 002 through `replay_of`, and carries no numerical or scientific validity claim.
