# PHK-V2.3 LF9 equation-routed thermal control-volume prior-art closure

Date: 2026-09-08  
Scope: six primary papers and one associated author repository; the existing LF7/LF8 constrained-refinement closure remains in force  
Campaign object: LF9 equation-routed thermal control-volume competence-filtered refinement

## Frozen LF9 object reviewed

LF9 compares two matched, competence-filtered continuations from the exact LF6
`DEV-R` endpoint. Both compute the coupled electric, thermal, and phase equations
from one pre-step model state, route each equation and its BC/IC terms only to the
corresponding field network, and apply one optimizer step. `ER-S` retains all
three strong residuals. `ER-CV` changes only the thermal objective to the
space-time control-volume balance of

\[
H=T+\lambda_{\rm latent}\phi,
\]

including enthalpy change, conductive boundary flux, cooling, and Joule source.
The two arms otherwise share the model, start, equation routing, competence
filter, blockwise immutable rollback, dyadic learning-rate ladder, and frozen
evaluation rules.

The literature question is therefore not whether weak, variational,
control-volume, block-coordinate, staggered, enthalpy, or local-balance methods
already exist. They do. The bounded collision question is whether an inspected
source already combines all of the following functional roles:

1. a pretrained localized event carrier in a coupled electro-thermal phase-field
   problem;
2. equation-to-field-head gradient routing with coupled coordinate derivatives
   retained;
3. replacement of only the transient thermal strong residual by a
   space-time enthalpy control-volume residual;
4. low-fidelity event/field competence auditing without label gradients; and
5. immutable block rollback, same-batch replay, and dyadic retry.

## Verdict

```text
NO_EXACT_FUNCTIONAL_COLLISION_FOUND_WITHIN_BOUNDED_6_ITEM_SCOPE
NO_REQUIRED_EXTERNAL_DEPENDENCY_OR_LICENSE_BLOCKER
```

All load-bearing primitives have clear prior art. The exact LF9 composition was
not found in the six-item bounded search, but that is not a priority proof or a
freedom-to-operate opinion. A later collision would narrow originality and
require attribution; it would not invalidate an independently implemented
recovery pilot.

## Six-source collision map

| # | Primary source | Direct precedent | Difference from frozen LF9 | Reuse decision |
|---:|---|---|---|---|
| 1 | Kharazmi, Zhang & Karniadakis, *Variational Physics-Informed Neural Networks For Solving Partial Differential Equations* (2019), [arXiv:1912.00873](https://arxiv.org/abs/1912.00873) | Introduces VPINNs through a Petrov--Galerkin variational residual and shows that integration by parts can lower the derivative order applied to the neural trial function. | LF9 is not a general VPINN or learned test-space method. Its thermal-CV loss uses fixed cell-indicator control volumes and fixed quadrature, while electric and phase equations remain strong form. | Citation only; no paper text, code, test functions, or implementation is copied. |
| 2 | Patel, Manickam, Trask, Wood, Lee, Tomas & Cyr, *Thermodynamically consistent physics-informed neural networks for hyperbolic systems*, JCP 449 (2022) 110754, [DOI 10.1016/j.jcp.2021.110754](https://doi.org/10.1016/j.jcp.2021.110754), [author manuscript](https://arxiv.org/abs/2012.05343) | Develops a least-squares space-time control-volume PINN in integral conservation form, including boundary flux handling and thermodynamic/entropy biases for hyperbolic systems. | This is the closest control-volume primitive, but LF9 targets one parabolic enthalpy equation inside a three-field electro-thermal-phase system, retains separate BC/IC losses, and adds equation routing plus an external event-competence filter and rollback. | Citation only; no external cvPINN code or dependency is used. |
| 3 | Gratton, Mercier, Riccietti & Toint, *A block-coordinate approach of multi-level optimization with an application to physics-informed neural networks*, COAP 89 (2024) 385--417, [DOI 10.1007/s10589-024-00597-1](https://doi.org/10.1007/s10589-024-00597-1), [arXiv:2305.14477](https://arxiv.org/abs/2305.14477) | Establishes a PINN application of block-coordinate/multilevel nonlinear optimization. | LF9 does not use resolution levels, coarse corrections, or the paper's complexity framework. Its blocks are field networks, and its update is a single pre-step, equation-routed Adam step with a post-block function-space competence audit. | Citation only; LF9 makes no block-coordinate convergence or complexity claim. |
| 4 | Chen, Cui, Ma, Chen & Wang, *Sharp-PINNs: staggered hard-constrained physics-informed neural networks for phase field modelling of corrosion*, CMAME 447 (2025) 118346, [DOI 10.1016/j.cma.2025.118346](https://doi.org/10.1016/j.cma.2025.118346), [author manuscript](https://arxiv.org/abs/2502.11942), [author code](https://github.com/NanxiiChen/sharp-pinns) | Alternately minimizes residuals of coupled phase-field equations and combines staggered training with hard output constraints. | Sharp-PINNs alternates PDE objectives and also changes architecture/embeddings. LF9 evaluates all coupled fields at one state, routes each equation to one existing independent head, performs one optimizer step, and changes no architecture. It also uses thermal CV balance and competence rollback, which Sharp-PINNs does not. | Paper citation only. The associated repository is GPL-3.0-licensed, but LF9 neither imports nor copies it. |
| 5 | Patra, Agrawal, Rath & Bhattacharya, *Physics informed neural network-based framework for two-dimensional phase change problems*, CPC 317 (2025) 109854, [DOI 10.1016/j.cpc.2025.109854](https://doi.org/10.1016/j.cpc.2025.109854) | Uses a diffuse-interface enthalpy formulation and a temperature-only PINN loss to recover transient temperature and moving phase-change interfaces. | It confirms that latent heat can be represented through enthalpy in a phase-change PINN, but it uses one temperature network and does not implement thermal control volumes, electric coupling, a learned independent phase head, event competence, equation routing, or rollback. | Citation only; no author code or reusable asset was located in this bounded check. |
| 6 | Shang, Zhang & Wang, *Local balance for energy-based physics-informed neural networks on phase-field models*, IJMS 324 (2026) 111790, [DOI 10.1016/j.ijmecsci.2026.111790](https://doi.org/10.1016/j.ijmecsci.2026.111790) | Shows that adding local balance to an energy-based PINN can be critical for avoiding trivial/nonphysical minima in non-convex phase-field steady-state problems. | This is the closest phase-field local-balance collision. It concerns direct steady-state prediction using mixed global energy and local balance, not transient thermal enthalpy control volumes, an electro-thermal causal chain, equation-to-head routing, or competence-filtered continuation from an event carrier. | Citation only; no external code or asset is used. |

## Primitive and terminology boundary

### Variational and control-volume identity

`VPINN` should be reserved for a variational/Petrov--Galerkin neural residual
with an explicit test space. `cvPINN` and finite-volume-informed PINN are also
established terms. LF9 may accurately say that its thermal objective is a
**fixed-quadrature space-time control-volume balance inspired by cvPINN/FVM
principles**. It should not claim the first weak-form, variational, conservative,
finite-volume, enthalpy, or local-balance PINN.

The LF9 formula is specifically the direct integral form of the already frozen
thermal equation. Replacing the full multiphysics model, introducing a learned
flux, changing coefficients, or adding entropy/TVD terms would create a
different method and is not licensed by this closure.

### Equation routing identity

The block-coordinate and staggered-PINN sources establish broad precedent for
separating parameter blocks and coupled equation objectives. They do not supply
the exact LF9 operation:

```text
same coupled pre-step state
-> grad_thetaV(L_V)
-> grad_thetaT(L_T)
-> grad_thetaPhi(L_phi)
-> write only the owning-head gradients
-> one optimizer step
```

Coordinate derivatives through `sigma(T,phi)`, mobility, Joule heating, and
latent coupling remain in the residual values, while cross-head parameter
gradients are suppressed. The defensible name is **equation-routed** or
**block-Jacobi-like gradient routing**. Do not call it a new block-Jacobi theory,
a monolithic solve, a staggered Sharp-PINN, or a general convergence method.

### Filter and rollback identity

LF7's existing six-source closure already attributes filter acceptance,
backtracking, restoration, multifidelity auditing, and catastrophic-forgetting
motivation. LF9 reuses those attributed primitives. It adds no claim of first
trust region, first filter, first rollback, or first constrained PINN optimizer.
Its potentially paper-relevant question is narrower: whether equation routing
is sufficient, or whether routing plus a thermal control-volume residual is
load-bearing for a preservation-compatible physics path.

## Permitted claims by possible result

- If `ER-S` passes and `ER-CV` does not, report that equation routing was
  sufficient under the frozen screen; thermal CV was not supported.
- If only `ER-CV` passes, report a bounded matched result supporting thermal CV
  as the load-bearing change.
- If both pass, use the preregistered multi-cell conservation comparison to
  determine whether CV adds a meaningful increment; do not infer novelty from
  the method name.
- If neither passes, retain the result as an equation-localized negative and
  close the present solver-recovery route. Do not generalize to all weak forms,
  all control volumes, or all PINNs.
- A successful single-seed nominal path remains within-architecture evidence.
  Direct `LF_ONLY`, multiple seeds, and the later sparse equal-information task
  remain necessary for a positive paper-value claim.

## Dependency and license disposition

LF9 implements its frozen formulas using the existing project runtime. It has
no required external package, model, dataset, weight, solver, or source-code
dependency. Publisher and arXiv manuscripts are citation sources only. The
Sharp-PINNs author repository is GPL-3.0-licensed but is not imported, linked,
vendored, or copied. Therefore no inspected source creates an execution or
redistribution blocker.

## Search boundary

The search stopped at the frozen maximum of six primary works after covering:
the VPINN/weak primitive; the space-time control-volume PINN primitive;
block-coordinate PINN optimization; staggered coupled phase-field training;
transient enthalpy phase-change PINNs; and phase-field local-balance PINNs.
Secondary surveys, patents, third-party reimplementations, and generic
finite-volume solvers were excluded. Searches combined `VPINN`, `cvPINN`,
`thermal control volume`, `enthalpy phase change`, `equation routing`,
`block-coordinate PINN`, `phase-field local balance`, `event competence`, and
`rollback`. No exact five-role functional composition listed above was found.

This is a bounded attribution and dependency closure for LF9, not a systematic
review, novelty guarantee, or global patent search.
