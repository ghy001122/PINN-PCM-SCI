# G2 environment attempt 006

- `run_id`: `20260819T120218Z-smoke-g2-env-resolve-attempt-006`
- `tier`: `smoke`
- `scientific_role`: `oracle_qualification`
- `gate`: `G2`
- `execution_status`: `FAILED`
- `gate_outcome`: `G2_ENVIRONMENT_BLOCKED`
- `route_disposition`: `BLOCKED_ADDITIONAL_AUTHORITY_REQUIRED`
- `claim_status`: `NO_SCIENTIFIC_CLAIMS`

## VERIFIED

- The attempt was registered before execution under `USER_APPROVED_G2_ENVIRONMENT_ATTEMPT_006_2026-08-19` and specification SHA-256 `59d2b8442df0587808cbd66ef0340f23b3a7b24415ddb39213e25d84b292fe36`.
- `resolve` completed and published resolution lock SHA-256 `00a659a6b6cbd16a50bae16b9805da596a15f7984009d2ed086f467df6dbbe46`.
- PETSc explicitly consumed retained MUMPS 5.3.5 archive `/opt/qpop-cpc-v1-env/downloads/petsc/MUMPS_5.3.5.tar.gz`; its first-resolution SHA-256 is `9cf89fcb5232560e807b7b1cc2adb7d0c280cbdfd3aa480de1d0b431a87187d3`.
- PETSc 3.15.1 and petsc4py built. DOLFIN configuration then selected `HDF5_DIR:PATH=/mnt/d/anaconda/Library/share/cmake/hdf5`, and compilation failed at 4% when `/mnt/d/anaconda/Library/include/H5public.h` redefined Ubuntu's `ssize_t`.
- Failure artifact SHA-256: `249eea69b396f7efe8cb30cdd9d2bab92ac82eb16f63e5caf88cb41d52ac71d1`. Raw copied CMake cache SHA-256: `998aea54e5088f2872deeaf4a59d190c288bd2503491e7105770e5b66160cf4e`.
- No verify command, Q-POP process, physical field, evaluator result, G3 activity or PINN output was created.

## Stop boundary

The authorized attempt is consumed. The terminal environment failure class is `DOLFIN_WINDOWS_ANACONDA_HDF5_PATH_CONTAMINATION`. This is engineering preflight evidence only; it does not qualify Q-POP, invalidate the physical model, or support the kinetics-clock hypothesis. No attempt 007 or environment correction is authorized by this record.
