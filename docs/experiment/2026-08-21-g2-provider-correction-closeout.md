# G2 provider-correction closeout, 2026-08-21

## Disposition

- `route_disposition`: `G2_ENVIRONMENT_BLOCKED_FINAL`
- `lifecycle_state`: `BLOCKED`
- `failed_run_id`: `20260820T160113Z-smoke-g2-env-provider-final-002`
- `failure_stage`: `resolve`
- `gate_outcome`: `G2_ENVIRONMENT_BLOCKED_FINAL`
- `failure_class`: `PETSC_EXTERNAL_SOURCE_PTSCOTCH_NOT_UNIQUELY_HASHABLE_ZERO_ARCHIVES`
- `environment_verify_status`: `NOT_REACHED`
- `native_smoke_run_id`: `NOT_STARTED`
- `qpop_started`: `false`
- `claim_status`: `NO_SCIENTIFIC_CLAIMS`
- `supersedes_route_record`: `docs/experiment/2026-08-20-g2-quota-recovery-closeout.md`
- `next_route`: `NO_AUTOMATIC_RETRY`

## Bounded facts

- `VERIFIED_IMPLEMENTATION_ONLY`：pybind11 Python sdist 与官方 Git/CMake provider 已分离；91/91 本地测试、Python 3.8 语法、`check-spec`、`print-plan` 与 ledger 校验通过。
- `VERIFIED`：唯一获批 clean integration 成功构建 OpenMPI 3.1.6、Python/mpi4py、官方 pybind11 CMake provider，并完成 PETSc 3.15.1 及所需 PTScotch、SuiteSparse、ScaLAPACK、MUMPS、HYPRE 配置。
- `BLOCKED`：在发布 `resolution.lock.json` 前，证据锁生成器无法为 PETSc 实际消费的 PTScotch 回退 tarball 找到可保留归档，精确错误为 `PETSc external source for ptscotch is not uniquely hashable: 0 archives`。失败证据 SHA-256 为 `7c991b4161957b155355bb907ccc53e0a1e7c392f7c46d1e5da47cd9dda114fd`。
- `NOT_EVALUATED`：preflight、build、verify、native Q-POP、G3、PhysicalContract、PINN 与 KC 数值检验均未启动；本结果不是 Q-POP 物理失效或 KC 假设的科学否定。
- `BOUNDARY`：本次 A/A/A 授权已消费；不自动修复、重跑、切换 oracle 或启动后续研究执行。

Run evidence:

- `docs/experiment/manifests/20260820T160113Z-smoke-g2-env-provider-final-002.json`
- `outputs/environments/qpop-cpc-v1-ubuntu-20.04-source-stack-v3/g2-final-002/resolve.failure.json`
