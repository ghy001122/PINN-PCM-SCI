# Supplementary Information

## S1. Scope and terminal identity

This supplement documents the evidence actually produced under `GOAL-PAPER-ONE-SHOT-V1`. It does not add results beyond the frozen contracts and recorded runs. The terminal disposition is:

- `SYN_EDT_2D_V1_NUMERICAL_CONTRACT_NO_GO`
- `NO_ORACLE_EVENT_OR_PINN_EVIDENCE`
- `NO_PRODUCTION_RERUN_NO_RESCUE`

The source review closed both source-aligned routes before activating the transparent synthetic benchmark. The synthetic route then passed its zero-drive guard but stopped at the first driven qualification intent because the frozen transport Newton solver exhausted its iteration allowance. Consequently, no cross-run convergence, event, thermal-effect, raw-PINN, architecture, OOD, or formal gate was reached. The authoritative detailed closeout is [the S2 terminal record](../../docs/experiment/2026-08-26-goal-paper-one-shot-v1-s2-terminal-closeout.md).

## S2. Machine contracts and immutable bindings

| Object | Role | SHA256 |
|---|---|---|
| [`s0_contract.json`](../../configs/goal_paper_one_shot_v1/s0_contract.json) | Physical, case, method, budget, and stopping contract frozen before new source audit or solve | `947E737A255D27A7BB2553286809ADB98219FD4E48B932B170CB06608A2E3A75` |
| [`s2_numerical_contract.json`](../../configs/goal_paper_one_shot_v1/s2_numerical_contract.json) | Discretization, nonlinear solver, evaluator, convergence ladder, and thermal-control contract | `D059AA2261CC227C3B16B7965A75C461AD64110C2A20C3700B62E54FDE25E8E6` |
| [`case-manifest-q-only.json`](../../outputs/runs/20260826T113537Z-goal-paper-one-shot-v1-s2-freeze-002/case-manifest-q-only.json) | Frozen Q-only case pool | `EF093A5C2F2E798FF05E768C3D0837CF08C3E10FD6AE79B432F26585F0FCD09C` |
| [`freeze-002` manifest](../../docs/experiment/manifests/20260826T113537Z-goal-paper-one-shot-v1-s2-freeze-002.json) | Effective freeze; explicitly supersedes `freeze-001` and binds the three hashes above | `74B5CD92A5271FD481A134DD52A80DD22FC65DC6784F761C5B8B74B880AB2F35` |

The S2 contract records `derived_from_s0_sha256` equal to the S0 hash. Every effective Q0 and QN intent/manifest also records the same S0, S2, freeze, and case-manifest identities. The manifests report a dirty working tree at revision `f2c727b382c2ebf245980140c768fb1ea188900e`; therefore the artifact and contract hashes, rather than the revision alone, are the immutable evidence bindings.

## S3. Primary-source carrier audit

The bounded S1 audit reviewed 13 primary carriers: 10 newly introduced to the project and 3 reused carriers; both available deep-review slots were used. The full legal and scientific boundary language is in the [S1 source, legality, and novelty review](../../docs/references/2026-08-26-goal-paper-one-shot-v1-s1-source-legal-novelty-review.md), SHA256 `1CCEFFFCF743B2B0781AA004F096AFD49C07E79C27CB5D9D339FCF99EE79AF1C`.

| ID | Primary carrier | Audit role | Bounded outcome |
|---|---|---|---|
| C01 | [COMSOL Application 141181](https://www.comsol.com/model/memristor-141181) | Route-1 asset identity | Application identity verified; research-use PASS not established |
| C02 | [COMSOL 6.4 model PDF](https://www.comsol.com/model/download/1585101/models.semicond.memristor.pdf) | Route-1 model-tree deep review | Several load-bearing defaults and machine-readable outputs remained unclosed |
| C03 | [COMSOL 6.4 Software License Agreement](https://doc.comsol.com/6.4/doc/com.comsol.help.comsol/comsol_la_license.04.1.html) | Use and publication boundary | Current-route research-use PASS not established; not a finding that no license exists |
| C04 | [COMSOL academic licensed rights](https://www.comsol.com/legal/academic-licensed-rights) | Academic-user boundary | Institution, license type, term, and eligible-user identity remained unverified |
| C05 | [Saraswat et al., arXiv:2005.07398](https://arxiv.org/abs/2005.07398) | PCMO fallback deep review | Public model is point/lumped and depends on an unpublished Sentaurus LUT |
| C06 | [Kovacs et al., conditional PINNs](https://arxiv.org/abs/2104.02741) | Conditional-PINN prior art | Load-bearing conditional architecture precedent |
| C07 | [Belbute-Peres et al., HyperPINN](https://arxiv.org/pdf/2111.01008) | Hypernetwork prior art | Load-bearing parameter-to-weight precedent |
| C08 | [Cho et al., parameterized PINNs](https://arxiv.org/abs/2408.09446) | Parameterized-PDE prior art | Direct parameterized-PINN precedent |
| C09 | [McClenny and Braga-Neto, self-adaptive PINNs](https://arxiv.org/abs/2009.04544) | Adaptive weighting prior art | Precedent for learned weighting mechanisms |
| C10 | [Tseng et al., cusp-capturing PINN](https://arxiv.org/abs/2210.08424) | Cusp-feature prior art | Direct cusp/absolute-value feature precedent |
| C11 | [Wandel et al., Spline-PINN](https://arxiv.org/abs/2109.07143) | Spline-basis prior art | Direct spline representation precedent |
| C12 | [Wang et al., PI-BSNet](https://openreview.net/forum?id=x1TWOnfTX8) | Learned/fixed basis prior art | Direct B-spline network precedent |
| C13 | COMSOL vendor `memristor.mph`, official asset `1471921` | Exact build and solved-payload metadata | Temporary metadata-only audit; SHA256 `14A1A8356B6FDA3C2B2CCBC2F4458C0F610CD47C4EE924602D4DBD49C8983FA3`; deleted and excluded from the repository |

The route decisions were `LEGAL_RESEARCH_ACCESS_FAILURE + SOURCE_CONTRACT_FAILURE` for Route 1 and `SOURCE_CONTRACT_FAILURE` for Route 2. These labels mean that the required PASS was not established for this route. They do not allege unlawful access, absence of a user license, or a general prohibition on independent PDE research. The bounded prior-art search found no exact collision for the complete proposed CTH bundle, but its load-bearing ingredients had direct precedents; positive architecture novelty was therefore not cleared.

## S4. Transparent synthetic physical contract

`SYN_EDT_2D_V1` is an engineering benchmark, not a source-aligned model, fitted material law, or experimental validation. In an axisymmetric $(r,z)$ domain, the frozen fields obey

\[
\nabla\cdot \mathbf J_e=0,\qquad
\mathbf J_e=-\sigma(y,T)\nabla\phi,
\]

\[
\partial_t y+\nabla\cdot\mathbf j_y=0,\qquad
\mathbf j_y=-D(T)\left[\nabla y+\frac{e}{k_B T}y(1-y)\nabla\phi\right],
\]

\[
-\nabla\cdot(k\nabla T)=\sigma(y,T)|\nabla\phi|^2.
\]

The active mixed conductor occupies $0\le r\le80\,\mathrm{nm}$, $0\le z\le30\,\mathrm{nm}$. The bottom electrode occupies $0\le r\le80\,\mathrm{nm}$, $-15\le z\le0\,\mathrm{nm}$, and the centered top contact occupies $0\le r\le25\,\mathrm{nm}$, $30\le z\le45\,\mathrm{nm}$. The initial state is $y=0.5$, $T=300\,\mathrm K$, with fresh uniform history.

| Quantity | Frozen engineering value |
|---|---:|
| $D_0$ | `5e-16 m^2 s^-1` |
| Active conductivity scale | `500 S m^-1` |
| Active thermal conductivity | `1 W m^-1 K^-1` |
| Electrode conductivity | `5e6 S m^-1` |
| Electrode thermal conductivity | `20 W m^-1 K^-1` |
| Length scale $L_0$ | `3e-8 m` |
| Time scale $t_0$ | `1.8 s` |
| Thermal voltage | `0.02585 V` |
| Characteristic current | `2.4363051028588846e-6 A` |
| Characteristic particle flux | `1.6666666666666666e19 m^-2 s^-1` |

The full temperature-dependent forms are

\[
D(T)=D_0\exp\!\left[-\frac{0.18\,\mathrm{eV}}{k_B}\left(\frac1T-\frac1{T_0}\right)\right],
\]

\[
\sigma(y,T)=500\exp[2(y-0.5)]\exp\!\left[-\frac{0.04\,\mathrm{eV}}{k_B}\left(\frac1T-\frac1{T_0}\right)\right]\ \mathrm{S\,m^{-1}}.
\]

Electrical insulation applies outside the driven top and grounded bottom terminals. Every active defect boundary is no-flux. Electrical and thermal fields are continuous across material interfaces. The bottom underside and top-contact cap are held at `300 K`; other thermal boundaries are adiabatic.

Each of two consecutive 1 s cycles contains a 0.02 s positive ramp, a 0.30 s positive hold, a 0.04 s return, a 0.10 s zero hold, a 0.02 s negative ramp, a 0.30 s negative hold, a 0.04 s return, and a 0.18 s zero hold. State is carried between cycles. Q0 uses `0/0 V`; QL, QN, and QH use positive reset amplitudes `0.144/0.18/0.216 V` and the common set amplitude `-0.15 V`. Only QN has an event vote.

## S5. Numerical and evaluator contract

The solver is a masked, cell-centered, nonuniform finite-volume method in axisymmetric coordinates. Radial volumes and face areas retain their geometric weights and the $r=0$ face has exactly zero area. Shared face conductances impose interface continuity. Heterogeneous-face Joule power is partitioned by the two half-face resistances. Backward Euler advances the conservative defect equation in a logit variable without clipping $y$; the lattice-gas mobility uses a logarithmic mean. Saved cell fluxes include exterior no-flux faces as zero-normal contributions to the area-weighted reconstruction.

The electrical system uses sparse direct LU at each block iteration; the constant thermal matrix is factorized once. The frozen nonlinear controls are:

| Control | Value |
|---|---:|
| Outer block relaxation | `0.5` |
| Outer block maximum iterations | `12` |
| Outer relative-change tolerance | `1e-8` |
| Accepted-state transport residual tolerance | `1e-9` |
| Inner transport Newton initial step | `0.5` |
| Inner transport Newton minimum step | `0.0009765625` |
| Inner transport Newton maximum iterations | `20` |
| Inner transport scaled-residual tolerance | `1e-10` |
| Linear relative-residual tolerance | `1e-10` |

No timestep rescue, parameter rescue, or post-result threshold change is allowed. Coarse, medium, and fine active spacings are `4/2/1 nm`; contact-corner spacings are `1/0.5/0.25 nm`; maximum timesteps are `0.005/0.0025/0.00125 s`. Saved fields use a `0.0025 s` interval.

For cycle $k$, depletion is $d_k=[y_{\mathrm{pre},k}-y]/0.5$ in the top-contact ROI $r\le25\,\mathrm{nm}$, $24\le z\le30\,\mathrm{nm}$. The first upward ROI-mean crossing of `0.12` defines event time. Both cycles must satisfy peak depletion `0.12–0.55`, recovery at least `0.70`, adjacent-annulus relative depletion at most `0.50`, connected depleted thickness fraction `0.05–0.35`, partial coverage `0.0025–0.20`, cycle drift at most `0.20`, and all conservation, port, state, temperature, and heat guards.

The six ordered endpoint components are ROI concentration, vector defect flux, event time, connected gap thickness, recovery, and top-current trace. Per-cycle component errors form an unclipped RMS $E$; the case endpoint is $Z=\tfrac12\sum_{k=1}^2E_k/\tau_{\mathrm{comp},k}$. Component floors are the maximum of space, time, independent replay, source uncertainty (`0` for this synthetic object), and `2e-6`. None of these floors was estimable because the ladder stopped at intent 2.

## S6. Frozen qualification ladder and observed disposition

| Intent | Case | Space | Time | Control | Observed disposition |
|---:|---|---|---|---|---|
| 1 | Q0 | coarse | coarse | FULL | `COMPLETED`; zero-drive guard only |
| 2 | QN | coarse | fine | FULL | `FAILED`; consumed intent; terminal stop |
| 3 | QN | medium | fine | FULL | `NOT_REACHED` |
| 4 | QN | fine | coarse | FULL | `NOT_REACHED` |
| 5 | QN | fine | medium | FULL | `NOT_REACHED` |
| 6 | QN | fine | fine | FULL | `NOT_REACHED` |
| 7 | QL | medium | medium | FULL | `NOT_REACHED` |
| 8 | QH | medium | medium | FULL | `NOT_REACHED` |
| 9 | QN | medium | fine | DIRECT_T_TO_TRANSPORT_OFF | `NOT_REACHED` |
| 10 | QN | fine | fine | DIRECT_T_TO_TRANSPORT_OFF | `NOT_REACHED` |
| 11 | QN | medium | fine | FULL_ISOTHERMAL_COUPLING_OFF | `NOT_REACHED` |
| 12 | QN | fine | fine | FULL_ISOTHERMAL_COUPLING_OFF | `NOT_REACHED` |
| 13 | QN | fine | fine | FULL, independent exact replay | `NOT_REACHED` |

`NOT_REACHED` is an execution fact, not a missing result to be imputed. QL/QH cannot replace QN, and intent 13 was planned as an uncertainty audit rather than a replacement run.

## S7. Run accounting

| Run | Role | Status | Solver intents | Failed intents | Wall time (s) | Process CPU (s) | CPU process core-hours |
|---|---|---|---:|---:|---:|---:|---:|
| `20260826T113537Z-goal-paper-one-shot-v1-s2-freeze-002` | Effective case freeze | COMPLETED | 0 | 0 | `0.028080299962311983` | `0.03125` | `8.680555555555556e-6` |
| `20260826T113638Z-goal-paper-one-shot-v1-s2-intent-01-q0` | Q0 coarse/coarse | COMPLETED | 1 | 0 | `8.38404590007849` | `8.28125` | `0.0023003472222222223` |
| `20260826T113752Z-goal-paper-one-shot-v1-s2-intent-02-qn-coarse-fine` | QN coarse/fine | FAILED | 1 | 1 | `0.0984956999309361` | `0.09375` | `2.604166666666667e-5` |

Both solver runs declared one CPU thread on an `AMD64` machine reporting `12` logical CPUs and `Intel64 Family 6 Model 154 Stepping 4, GenuineIntel`. The environment was CPython `3.11.9`, NumPy `2.1.1`, SciPy `1.14.1`, and h5py `3.12.1`, with float64 CPU execution. Peak RAM was not captured (`null`); peak VRAM was `0`. Q0 plus the failed QN intent consumed `2` of the `40` CPU-solver-intent cap and `0.002326388888888889` CPU process core-hours. The failed intent counts against budget and had `rescue_attempts=0`.

The Q0 manifest is [`intent-01-q0.json`](../../docs/experiment/manifests/20260826T113638Z-goal-paper-one-shot-v1-s2-intent-01-q0.json), SHA256 `6451DFC6C1E331A0AF86997FDCC74083CD4C8C781C96C2C2A156EB149504205E`. Its case, evaluation, and report hashes are, respectively, `01F5DCF28E25A75E74C5EDBE612456A542ECA36EFFCB8CAFEC196AE4994F7A01`, `F24439F92CBC70FDED7A24DE1D0B6272E59D14A169CCB86A1FAA888E21BDAE6B`, and `0964E3B55431AA49CDE158FFF7F98F3478288865A6DE670CC88ABD9B7BF3D1A8`.

The failed QN manifest is [`intent-02-qn-coarse-fine.json`](../../docs/experiment/manifests/20260826T113752Z-goal-paper-one-shot-v1-s2-intent-02-qn-coarse-fine.json), SHA256 `A1806D03A1D5F8687FCE252F66BA2CCE921DA78902EADA149B5A84C42CE0ECB8`. The pre-solve intent and atomic claim hashes are `DC2A38B5BF9F560A2A64D78733647C02906CF225C8392699614E5DAC778D4AE5` and `CF7FB0E8C8F5DF05C16F1E13F88C75C68FEE9F3D23F93427FA952A161C2A8B7C`. Its run directory is empty because failure occurred before case, evaluation, or report publication.

## S8. Verified Q0 and bounded negative diagnostic

Q0 completed 400 timesteps. It used 400 total block iterations, 801 electrical solves, 401 thermal solves, no transport Newton solves, and 400 accepted-state consistency evaluations. The final transport residual maximum was exactly `0`. The state remained $y=0.5$; temperature ranged from `299.9999999999985` to `300.00000000000034 K`. Relative mass drift, no-flux residual, heat-balance residual, and terminal-current mismatch were all `0`. The event evaluator was correctly inapplicable to Q0. This establishes only the zero-drive conservation and artifact path.

The first driven QN intent raised `RuntimeError: transport Newton exceeded its frozen iteration limit`. A separately labeled, 12-active-cell, one-step fixture reproduced the failure class at the first QN ramp endpoint (`0.00125 s`, `0.01125 V`). This fixture is `NON_SCIENTIFIC_DIAGNOSTIC` and never entered the ledger. Its inner residual changed from `1.5106745331996967e-3` to `1.4406930175716191e-9` after 20 accepted steps, all of size `0.5`; the ratio `9.536753191437917e-7` matches $2^{-20}$. The threshold-compatible initial residual for 20 ideal half steps would be at most `1.048576e-4`. A centered finite-difference directional check gave an analytic-Jacobian relative infinity-norm discrepancy of `1.7339861280712171e-10`; it did not reveal a large mismatch in the tested direction, but it does not exclude errors in untested directions or states.

The outer combination `relaxation=0.5`, `maximum=12`, `relative-change tolerance=1e-8` is a latent contract risk: ideal first-order half-decay leaves `2^-12=2.44140625e-4`, requiring an initial normalized mismatch no larger than `4.096e-5`. Production never reached this outer failure mode because the inner solve stopped first.

## S9. Unknowns and gates not reached

- Whether the driven QN discrete problem can pass under a different, newly frozen solver contract is `UNKNOWN`.
- Spatial, temporal, and replay convergence floors are `UNKNOWN` and unsealed.
- The two-cycle local depletion/recovery event is `UNKNOWN`; no event evidence exists.
- QL/QH brackets and both thermal controls are `NOT_REACHED`; thermal-effect attribution is `UNKNOWN`.
- Strong raw competence, transport bottleneck, Stage 1, Stage 2, identity split, OOD, formal statistics, and reserve are `NOT_REACHED`.
- No PINN was trained. No GPU development or formal compute was used. No method comparison or architecture increment exists.
- No experimental validation, real-material calibration, COMSOL replay, or source-aligned numerical result exists.
- The finite-difference diagnostic does not establish Jacobian correctness on all production meshes or states.

These boundaries are audited claim by claim in [the claim–evidence matrix](claim_evidence_matrix.md). Reproduction instructions are isolated in [the reproducibility guide](reproducibility.md), and publication-facing numerical tables are isolated in [the tables file](tables.md).
