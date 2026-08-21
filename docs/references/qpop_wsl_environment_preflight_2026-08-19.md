# Q-POP legacy WSL environment preflight, 2026-08-19

## Scope and disposition

- Gate: `G2`, environment preflight before any native Q-POP case launch.
- Current preflight disposition: `BLOCKED_ADDITIONAL_AUTHORITY_REQUIRED`.
- G2 gate outcome: `NOT_EVALUATED`; no Q-POP process or physics oracle was started.
- Scientific claim status: `NO_SCIENTIFIC_CLAIMS`.
- Downstream effect: G3-G6 remain closed. The environment is not qualified and the existing partial prefix must not be used for a Q-POP run.

This record supersedes the earlier reboot-pending execution status. It does not rewrite the source and legacy-environment audits, whose provenance conclusions remain unchanged.

## Attempt 001: original environment resolution

- Evidence root: `outputs/environments/qpop-cpc-v1-ubuntu-20.04-source-stack-v1/attempt-001/`
- Failure record: `resolve.failure.json`, SHA-256 `f993a31e11f0d1c265e396f74a72c1b3903b1cb8ca4e1445f62df56e00012e2d`.
- Failed at: `2026-08-19T09:56:59.789706Z`.
- Completed before failure:
  - dedicated Ubuntu 20.04 WSL2 distribution was available;
  - OpenMPI 3.1.6 was built and installed under `/opt/qpop-cpc-v1-env/openmpi-3.1.6`;
  - the Python 3.8 environment and source-built `mpi4py==3.0.3` were installed;
  - PETSc `v3.15.1` resolved to commit `09da24df01e50defd94bc4f7396f866a808ecea5`;
  - DOLFIN `2019.1.0.post0` resolved to commit `74d7efe1e84d65e9433fd96c50f1d278fa3e3f3f`.
- Exact failure: SOWING 1.1.26 `configure` found neither `gcc` nor `cc`, although the frozen versioned compiler `/usr/bin/gcc-9` existed.
- Diagnosis: the Ubuntu 20.04 default unversioned C launcher was absent from the system-package contract.

## Attempt 002: sole infrastructure-correction replay

- Evidence root: `outputs/environments/qpop-cpc-v1-ubuntu-20.04-source-stack-v1/attempt-002/`
- Failure record: `resolve.failure.json`, SHA-256 `7fae4533a60cbd3d9cd962f25cd63516142765d67f2e23c7448e0a9e7bf39897`.
- Failed at: `2026-08-19T10:05:14.239902Z`.
- Single applied correction: installed Focal `gcc 4:9.3.0-1ubuntu2` and its `cpp` dependency. This supplies the unversioned launcher while retaining GNU 9.
- Progress beyond attempt 001: SOWING configuration completed and its build started.
- Exact failure:
  - the SOWING log reports `checking for c++... no` and `checking for g++... no`;
  - its makefile therefore compiled and linked `.cc` sources with `gcc`;
  - the link failed on C++ runtime symbols including `operator new`, `operator delete`, and C++ ABI vtables.
- Diagnosis: the same contract defect also omitted Focal's unversioned `g++` launcher. This is not a PETSc, MPI, Q-POP, or scientific-model failure.

## Implemented but not executed correction

PETSc 3.15.1's own `config/BuildSystem/config/packages/sowing.py` registers `-download-sowing-cc=<prog>` and `-download-sowing-cxx=<prog>` and forwards them as SOWING's `CC` and `CXX`. The stack specification and validator now require the exact options:

- `-download-sowing-cc=/usr/bin/gcc-9`
- `-download-sowing-cxx=/usr/bin/g++-9`

This binds SOWING directly to the already-frozen GNU 9 identities and removes dependence on unversioned PATH aliases. The current corrected specification has SHA-256 `c50bcbcc0bceab15cc5d507151cda8cae83ae5cd796b19f65840ca7d422667de`.

The missing-binding condition is regression tested. Static and unit-test success only verifies the implementation contract; it does not qualify the WSL environment.

## Historical stop decision before attempt 003

The approved bounded workflow allowed the original resolution plus one causally justified infrastructure correction. Attempt 002 consumed that replay and still failed, so no attempt 003, PETSc build, DOLFIN build, ABI verification, or native Q-POP smoke was launched.

Resuming this subroute requires an explicit decision to authorize one additional environment-resolution attempt using the already-corrected explicit SOWING GNU 9 bindings. If that authority is not granted, `BLOCKED_RETRY_CAP_REACHED` is the terminal G2 disposition for this execution window.

## Superseding continuation: authorized attempt 003

The user explicitly authorized one additional environment-resolution attempt after the preceding stop. Attempt 003 used the corrected specification SHA-256 `c50bcbcc0bceab15cc5d507151cda8cae83ae5cd796b19f65840ca7d422667de` and the exact PETSc options:

- `-download-sowing-cc=/usr/bin/gcc-9`
- `-download-sowing-cxx=/usr/bin/g++-9`

Execution evidence shows SOWING completed configure, make, and install. PETSc then configured and installed METIS and ParMETIS and compiled FBLAS/LAPACK, so the attempt 001/002 SOWING root cause is operationally closed.

Attempt 003 then stopped during PTScotch configuration:

- PETSc console record: `PTScotch needs bison installed`.
- PETSc 3.15.1 source `config/BuildSystem/config/packages/PTScotch.py` resolves `bison` and raises that exact error if absent.
- Ubuntu Focal package metadata reports `bison` is not installed and offers candidate `2:3.5.1+dfsg-1` from `focal/main`.
- The frozen stack requests `--download-ptscotch` but its system-package list does not contain `bison`.

Evidence root: `outputs/environments/qpop-cpc-v1-ubuntu-20.04-source-stack-v1/attempt-003/`. The immutable failure record `resolve.failure.json` has SHA-256 `5d13758369875d94564ab91b8e611744437807b9ca238f13b66085cfae000d2e` and failure time `2026-08-19T10:27:58.937924Z`.

Current disposition is `BLOCKED_ADDITIONAL_AUTHORITY_REQUIRED`; G2 remains `NOT_EVALUATED`. No Q-POP process, nonlinear physics step, build stage, verify stage, G3 activity, or PINN run was launched. Adding `bison` and executing another resolution would change the frozen environment input and consume a new attempt, so neither action is authorized implicitly.

## Post-stop static contract correction

After preserving the attempt-003 failure, the bounded implementation contract was corrected without installing packages or launching another resolution:

- `bison` was added to `system_packages.install`.
- The public `check-spec/print-plan` seam now rejects a specification that requests `--download-ptscotch` without declaring `bison`.
- The two focused contract tests first failed against the old specification/validator and then passed after the minimal changes.
- The corrected, not-yet-executed specification has SHA-256 `5b56f745bb4b9e6c13316f34ca8dd120a95efa72cff71587bc8eeb7d42e1c828`.

This is `VERIFIED_IMPLEMENTATION_ONLY`, not environment qualification. The current WSL distribution still does not have `bison` installed, and attempt 004 remains unauthorized.

## Attempt-ledger reconciliation

The environment builder had preserved atomic failure records but had not entered attempts 001–003 in the experiment ledger. To meet the project-wide rule that failed and replayed attempts remain indexed, all three were reconstructed from those immutable records and appended in order. Their manifests use `evidence_identity = ENVIRONMENT_PREFLIGHT_ONLY`, explicitly mark the exact historical dirty-worktree snapshot as unavailable, preserve the replay chain, and carry `NOT_EVALUATED / NO_SCIENTIFIC_CLAIMS`. The ledger validates as a manifest/index bijection after reconciliation.

## Authorized attempt 004 and superseding stop

The user explicitly authorized attempt 004 using specification SHA-256 `5b56f745bb4b9e6c13316f34ca8dd120a95efa72cff71587bc8eeb7d42e1c828`. Focal installed `bison 2:3.5.1+dfsg-1` and transitive `m4 1.4.18-4`; PETSc therefore passed the prior bison check. Configuration then stopped at the immediately following PETSc 3.15.1 source check with `PTScotch needs flex installed`.

Primary local source evidence in `config/BuildSystem/config/packages/PTScotch.py` resolves `flex` immediately after `bison` and raises that exact error when absent. Ubuntu Focal reports `flex 2.6.4-6.2` as the candidate from `focal/main`; it is not installed. Attempt evidence is under `outputs/environments/qpop-cpc-v1-ubuntu-20.04-source-stack-v1/attempt-004/`; `resolve.failure.json` has SHA-256 `760c8701626a875b19465d9e3f8a0721b323a73741116bd5fcebaf04bfa8bf41`.

After freezing the failure, `flex` was added to `system_packages.install`, and the public `check-spec/print-plan` seam was strengthened to reject `--download-ptscotch` without flex. The corrected, not-yet-executed specification has SHA-256 `139969e1dcaf5cd18e4445516633e20cba1b2322c1717657e64213ff6f7dde85`. This is implementation evidence only. Current disposition is `BLOCKED_ADDITIONAL_AUTHORITY_REQUIRED`; G2 remains `NOT_EVALUATED` and no Q-POP process was launched.

## Authorized attempt 005 and superseding stop

The user explicitly authorized attempt 005 using specification SHA-256 `139969e1dcaf5cd18e4445516633e20cba1b2322c1717657e64213ff6f7dde85`. Focal installed `flex 2.6.4-6.2`; PETSc 3.15.1 then completed configuration with PTScotch 6.1.0, SuiteSparse 5.8.1, ScaLAPACK, MUMPS 5.3.5, Hypre 2.20.0, the frozen GNU 9/OpenMPI 3.1.6 toolchain, real double scalars, 32-bit indices and debugging disabled.

The environment resolver nevertheless rejected the run before publishing `resolution.lock.json`: its source-lock implementation required every external URL to recur in the current configure log. PETSc reused the existing clean `git.fblaslapack` checkout, so no URL was repeated. Direct read-only evidence identifies origin `https://bitbucket.org/petsc/pkg-fblaslapack` and commit `e8a03f57d64cf01d987d4b4ce9b961c24765747d`. Failure evidence is `outputs/environments/qpop-cpc-v1-ubuntu-20.04-source-stack-v1/attempt-005/resolve.failure.json`, SHA-256 `9adb78cbfec75fab67159f00ebdad4e708bbf4f82335bd9254d61d5946917010`.

After freezing the failure, one TDD slice changed the source-lock interface to derive Git-backed external identity from the actual clean checkout: origin, commit, tree and deterministic `git archive` SHA-256. Its focused test passed. A read-only application to the actual attempt-005 prefix successfully inventoried all seven required Git externals, then exposed the remaining archive-specific gap: PETSc retrieved MUMPS from `https://ftp.mcs.anl.gov/pub/petsc/externalpackages/MUMPS_5.3.5.tar.gz`, extracted it and removed `_d_MUMPS_5.3.5.tar.gz`, leaving no archive bytes for the required first-resolution hash.

This static correction is incomplete for a full resolution lock and has not been executed as a new attempt. A subsequent contract would need to pre-stage, retain and hash the MUMPS archive and make PETSc explicitly consume that exact local file. That changes the frozen environment input and requires new user authority. Current disposition is `BLOCKED_ADDITIONAL_AUTHORITY_REQUIRED`; build, verify, native Q-POP, G3 and PINN remain unopened.
