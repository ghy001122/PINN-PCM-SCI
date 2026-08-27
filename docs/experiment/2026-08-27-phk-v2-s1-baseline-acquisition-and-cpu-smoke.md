# PHK-V2 S1 fixed-identity baseline acquisition and CPU smoke

- `record_date`: `2026-08-27`
- `stage`: `S1_ORIGINAL_DOMAIN_REPRODUCTION`
- `record_status`: `MODULE_EXECUTABILITY_SMOKE_COMPLETE_R2_REPRODUCTION_NOT_YET_ESTABLISHED`
- `scientific_claim_status`: `NO_BASELINE_ACCURACY_OR_METHOD_ADVANTAGE_CLAIM`
- `device`: `CPU_ONLY`
- `formal_or_GPU_accessed`: `false`

## 1. Scope and source boundary

This record consumes the fixed identities and license findings in the [PHK-PINN primary-source baseline audit](../references/2026-08-27-phk-pinn-primary-source-baseline-audit.md). The external repositories remain under `.tmp/phk-v2/external/` and are not copied into the project package. Sharp-PINNs and PF-PINNs are GPL-3.0 isolated comparators; jaxpi2 is the Apache-2.0 general architecture/pseudo-time control. A successful module smoke establishes import, initialization, forward evaluation and differentiation only. It is not an official-case, figure, metric, ranking, or paper-result reproduction.

| Identity | Frozen commit | Working-tree observation at closeout | Local dependency root |
| --- | --- | --- | --- |
| Sharp-PINNs repo recipe | `4b7029e3e1e0b82482d245ba12e3ec0945d87ed9` | clean | `.tmp/phk-v2/envs/sharp-pf-site` |
| PF-PINNs support comparator | `a25f75b5fd40657e5ce98467d7afd0d0052464d1` | clean | `.tmp/phk-v2/envs/sharp-pf-site` |
| jaxpi2 | `77a5c1315a056388271822c35ad512a5a192b60d` | pinned source plus pip-generated untracked `build/`; source commit unchanged | `.j2` (minimal architecture-only import stack) |

## 2. Sharp-PINNs

The pinned module completed a CPU forward/backward smoke against the repository's current exact root configuration:

```text
input shape = (4, 4)
output shape = (4, 2)
finite = true
device = cpu
scalar smoke loss = 0.9613916873931885
```

The first 2D-shaped invocation failed with an input-matrix shape mismatch. This exposed a real identity seam: the pinned root `config.ini` is a 3D configuration, whereas the named 2D entrypoint expects a different coordinate identity. The 2D entrypoint also contains a hard-coded CUDA device at one flux-sampling site. Therefore:

- `VERIFIED`: the exact pinned architecture/configuration module can execute forward/backward on CPU;
- `NOT_ESTABLISHED`: an official 2D paper case, paper metric, or method ordering;
- `REQUIRED_NEXT`: freeze a separate `SHARP_PINNS_PAPER_REPLICATION_V1` configuration and a separate `SHARP_PINNS_REPO_RECIPE_4B7029E` configuration before R2 runs.

No result-adaptive source edit was made.

## 3. PF-PINNs

The pinned official module completed a CPU forward/backward smoke:

```text
input shape = (4, 2)
output shape = (4, 2)
finite = true
device = cpu
scalar smoke loss = 0.1847665160894394
```

This is a module-seam smoke only. It does not reproduce the official low-cost PDE case, reported error, NTK weighting behavior, RAR behavior, or paper ranking. Those remain R2 work.

## 4. jaxpi2 and bounded Windows dependency failure

The exact jaxpi2 package declares JAX, Flax, Optax, Orbax checkpointing, SOAP-JAX, W&B and plotting dependencies. Two complete project-local installation attempts failed with Windows `WinError 206` while copying Orbax's deeply nested compatibility-checkpoint fixtures. The second attempt used a short substituted drive and short project-local temporary directory; it failed at the same Orbax path class. The failed attempts are retained as environment evidence and were not re-labelled as model failures.

The preregistered low-cost requirement was an architecture CPU smoke, not checkpoint or training qualification. A bounded minimal stack was therefore installed into `.j2`: JAX `0.10.2`, jaxlib `0.10.2`, Flax `0.12.3`, ml-dtypes `0.6.0`, opt-einsum `3.4.0`, msgpack `1.2.1`, typing-extensions `4.16.0`, PyYAML `6.0.3`, treescope `0.1.10`, absl-py `2.5.0`, and Rich `15.0.0` with its text-rendering dependencies. Orbax, Optax, SOAP-JAX and W&B were deliberately not imported for this smoke.

Loading the pinned `jaxpi/archs.py` directly, with external logging disabled and `JAX_ENABLE_X64=true`, produced:

```text
architecture = PirateNet
num_layers = 2
hidden_dim = 16
out_dim = 3
Fourier embed_dim = 16
JAX = 0.10.2
device = cpu:0
x64 = true
output dtype = float64
output shape = (3,)
finite = true
parameter_count = 2245
output = [1.0426336919473602, -1.2534092013362903, 0.5765888381024163]
```

An earlier diagnostic invocation without `JAX_ENABLE_X64=true` emitted JAX's float64-to-float32 truncation warning. The explicit-x64 invocation is the applicable project smoke because the PHK object contract requires float64; both observations are reported rather than hiding the default-dtype seam.

- `VERIFIED`: the pinned jaxpi2 PirateNet architecture is CPU/x64 executable in the bounded minimal environment.
- `NOT_ESTABLISHED`: full package import, checkpointing, optimizer/training, adaptive pseudo-time behavior, official example accuracy, or five-seed method ordering.
- `DISPOSITION`: keep the complete-install failure; use the minimal architecture seam for clean-room inspection and create a separate fixed training environment only if the R2 paper-spec reproduction requires it. No open-ended dependency rescue is allowed.

## 5. Stage adjudication

```text
S1_MODULE_EXECUTABILITY = PASS_FOR_SHARP_PF_JAXPI2_ARCHITECTURE_SEAMS
S1_R2_PAPER_RESULT_REPRODUCTION = NOT_YET_ESTABLISHED
PHK_ORACLE_EVENT_METHOD_EVIDENCE = NONE_FROM_THIS_RECORD
```

The next admissible actions are the predeclared low-cost official/Paper-spec R2 reproductions and PHK S2 manufactured/zero-drive qualification. A later method comparison may only use a baseline identity whose configuration, seed, oracle, budget and reported endpoint have been fixed separately.
