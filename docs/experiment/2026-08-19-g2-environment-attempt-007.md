# G2 environment attempt 007

- `run_id`: `20260819T124542Z-smoke-g2-env-resolve-attempt-007`
- `tier`: `smoke`
- `scientific_role`: `oracle_qualification`
- `gate`: `G2`
- `execution_status`: `FAILED`
- `gate_outcome`: `G2_ENVIRONMENT_BLOCKED`
- `route_disposition`: `BLOCKED_ADDITIONAL_AUTHORITY_REQUIRED`
- `claim_status`: `NO_SCIENTIFIC_CLAIMS`

## VERIFIED

- The attempt was registered before execution under `USER_APPROVED_G2_ENVIRONMENT_ATTEMPT_007_2026-08-19`, builder SHA-256 `77341cd0d343e2c5730dd7bb8259176e47fe244aa61700eb8d8a745d09352134`, and unchanged specification SHA-256 `59d2b8442df0587808cbd66ef0340f23b3a7b24415ddb39213e25d84b292fe36`.
- Only `/opt/qpop-cpc-v1-env/src/dolfin/build` was removed after its real path and clean parent source checkout were verified. The DOLFIN source remained at commit `74d7efe1e84d65e9433fd96c50f1d278fa3e3f3f`.
- `resolve` reused the identical resolution lock SHA-256 `00a659a6b6cbd16a50bae16b9805da596a15f7984009d2ed086f467df6dbbe46`.
- The HDF5 isolation fix worked at runtime: the new cache has zero `/mnt/` path hits and records `HDF5_DIR-NOTFOUND`. DOLFIN C++ compiled to 100% and installed, so attempt-006's Windows Anaconda `ssize_t` failure did not recur.
- The build then failed in the DOLFIN Python binding. The frozen resolution lock contains `pybind11==2.2.3`, while DOLFIN's `setup.py` requests `pybind11==2.2.4`; pip downloaded and installed 2.2.4 during build, but no `pybind11Config.cmake` was present for the binding's CMake configure step.
- PETSc `make check` also returned zero while logging seven OpenMPI root-launch refusals and seven possible-problem/error records. It therefore cannot be treated as successful runtime validation.
- Build failure SHA-256: `56027b65aa1c010b411b74f921b64f78c14e11e05a5d45a8b0073ba1b5920859`. New CMake cache SHA-256: `e0ecffec9a2d4324c2f3f20b3d6efbadfc3480b5e401bda74a808e89a21fc333`.
- No verify command, Q-POP process, physical field, evaluator result, G3 activity or PINN output was created.

## Stop boundary

The authorized attempt is consumed. The primary failure class is `DOLFIN_PYTHON_PYBIND11_CMAKE_PACKAGE_MISSING`, with secondary `PYTHON_DEPENDENCY_DRIFT_DURING_BUILD` and `PETSC_MAKE_CHECK_ROOT_MPI_REFUSALS` findings. This is engineering preflight evidence only; it does not qualify Q-POP, invalidate the physical model, or support the kinetics-clock hypothesis. No attempt 008 or further environment correction is authorized by this record.
