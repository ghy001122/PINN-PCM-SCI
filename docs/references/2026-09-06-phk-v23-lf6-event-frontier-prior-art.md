# PHK-V2.3 LF6 event-frontier rank-band prior-art closure

Date: 2026-09-06
Scope: six primary research works, with author code used only to verify implementation identity and license
Campaign object: LF6 cycle-resolved event-frontier rank-band alignment and safety-gated physics pilot

## Frozen LF6 object reviewed

The frozen evaluator defines a cycle event from the first saved-time interval in
which the teacher ROI active fraction crosses `q=0.02`.  At each endpoint, LF6
sorts teacher phase logits by descending value with ascending cell index as the
tie-break.  If the teacher active counts are `n_minus` and `n_plus`, the
event-frontier set is the fixed rank interval

```text
F_{c,s} = ranks n_minus+1, ..., n_plus,
```

which must contain `ceil(q N)`.  A same-cardinality control set `U_{c,s}` is
chosen once from `ROI \ F_{c,s}` using frozen seeds; it is not selected from
model predictions.  Both development arms reuse the same LF3 base and LF4
spatial-interface objectives, initialization, points, optimizer and 400-update
budget.  They differ only in the final endpoint-logit term:

```text
L_U  = (1/4) sum_{c,s} mean_{i in U_cs} [((z_theta-z_star)/D_epsilon)^2]
L_FR = (1/4) sum_{c,s} mean_{i in F_cs} [((z_theta-z_star)/D_epsilon)^2]

L_DEV-U = 0.50 L_base + 0.25 L_spatial + 0.25 L_U
L_DEV-R = 0.50 L_base + 0.25 L_spatial + 0.25 L_FR
```

Here `c` is cycle, `s` is the saved endpoint/direction role, and
`D_epsilon=36.84136146790473` is the already frozen clipped-logit span.  The
rank operation is teacher-side preprocessing: no rank, quantile or top-k
operator is differentiated.  A safety-qualified fixed endpoint may seed the
separate label-free `L_PDE + 5 L_BC + L_IC` continuation.

## Frozen verdict

`NO_EXACT_FUNCTIONAL_COLLISION_FOUND_WITHIN_BOUNDED_6_ITEM_SCOPE`

All load-bearing primitives have strong prior art.  Quantiles and order
statistics, differentiable ranking, top-k-specific losses, differentiable event
roots, differentiable temporal alignment, and interface-focused phase-field
PINN sampling are not original to LF6.  Within the frozen six-work search, no
source combines all of the following in one method:

- the exact downstream event functional (first saved-cadence crossing of a 2%
  ROI active fraction);
- a cycle/direction-resolved teacher bracket and its critical order-statistic
  cell interval;
- a same-cardinality, preselected generic-endpoint control differing only in
  cell identity;
- calibrated normalized phase-logit MSE added to an inherited spatial-interface
  continuation; and
- conditional label-free multiphysics refinement with a separate safety gate.

This negative search is not a priority proof.  LF6 remains an **attributed,
project-specific combination and solver-recovery pilot**.  An exact collision
found later would close headline originality but would not invalidate an
independently implemented, properly attributed recovery backbone.

## Six-item collision map

| # | Primary work and pinned identity | Relevant precedent | Collision identity | License / reuse decision |
|---:|---|---|---|---|
| 1 | Koenker & Bassett, *Regression Quantiles*, *Econometrica* 46(1), 33-50 (1978), DOI [`10.2307/1913643`](https://doi.org/10.2307/1913643), [publisher record](https://www.jstor.org/stable/1913643) | Establishes quantile regression through an asymmetric absolute-deviation objective and connects quantiles to order-statistic structure. | `DIRECT_FOUNDATIONAL_PARTIAL`: LF6 uses one fixed empirical order-statistic location to identify teacher cells; it neither estimates a conditional quantile nor optimizes pinball loss. | Published article; publisher/copyright terms apply. Citation only; no text, data, or code is imported. |
| 2 | Blondel, Teboul, Berthet & Djolonga, *Fast Differentiable Sorting and Ranking*, ICML 2020, PMLR 119:950-959, [PMLR version](https://proceedings.mlr.press/v119/blondel20a.html), arXiv DOI [`10.48550/arXiv.2002.08871`](https://doi.org/10.48550/arXiv.2002.08871), [author implementation](https://github.com/google-research/fast-soft-sort/tree/6a52ce79869ab16e1e0f39149a84f50f8ad648c5) | Makes sorting/ranking differentiable via regularized projections onto the permutahedron. | `DIRECT_RANKING_PARTIAL`: LF6 uses an exact stable sort of frozen teacher values offline.  It has no soft rank, permutahedron projection, differentiable sorting, or smoothing parameter. | Author code pinned at `6a52ce79869ab16e1e0f39149a84f50f8ad648c5`, Apache-2.0.  No code or dependency is imported. |
| 3 | Berrada, Zisserman & Kumar, *Smooth Loss Functions for Deep Top-k Classification*, ICLR 2018, [author page](https://www.robots.ox.ac.uk/~vgg/publications/2018/Berrada18/), arXiv DOI [`10.48550/arXiv.1802.07595`](https://doi.org/10.48550/arXiv.1802.07595), [author implementation](https://github.com/oval-group/smooth-topk/tree/12c1645f187e2fa0c05f47bf1fe48864d4bd2707) | Constructs smooth, non-sparse surrogate losses aimed directly at top-k classification error. | `DIRECT_TOP_K_PARTIAL`: LF6 also aligns supervision with a downstream order statistic, but uses fixed teacher frontier membership followed by ordinary squared logit error.  It does not optimize a top-k classification surrogate or introduce a smoothing temperature. | Author code pinned at `12c1645f187e2fa0c05f47bf1fe48864d4bd2707`, MIT.  No code or dependency is imported. |
| 4 | Chen, Amos & Nickel, *Learning Neural Event Functions for Ordinary Differential Equations*, ICLR 2021, [OpenReview version](https://openreview.net/forum?id=kW_zpEmMLdP), arXiv DOI [`10.48550/arXiv.2011.03902`](https://doi.org/10.48550/arXiv.2011.03902), [author event-handling implementation](https://github.com/rtqichen/torchdiffeq/tree/657943acefa826ef04c025ebeb1ff5e9d60dc268) | Treats an event as the first zero of a state-dependent event function and differentiates the returned event time through an ODE solve. | `DIRECT_EVENT_FUNCTIONAL_PARTIAL`: LF6 is likewise aligned to an event-defining functional, but its event is a saved-grid ROI count threshold and its loss supervises fixed teacher cells.  It does not learn an event function, solve a continuous root, or differentiate event time. | `torchdiffeq` pinned at `657943acefa826ef04c025ebeb1ff5e9d60dc268`, MIT.  No code or dependency is imported. |
| 5 | Cuturi & Blondel, *Soft-DTW: a Differentiable Loss Function for Time-Series*, ICML 2017, PMLR 70:894-903, [PMLR version](https://proceedings.mlr.press/v70/cuturi17a.html), arXiv DOI [`10.48550/arXiv.1703.01541`](https://doi.org/10.48550/arXiv.1703.01541), [author implementation](https://github.com/mblondel/soft-dtw/tree/1774bcd007acf22dfdb2a596944186d56ac434a6) | Provides a differentiable soft-min over temporal alignments and permits end-to-end sequence fitting under time shifts/dilations. | `ADAPTED_TEMPORAL_ALIGNMENT_PARTIAL`: LF6 targets fixed adjacent saved endpoints and forbids time warping.  It has no dynamic-programming path, soft minimum, alignment temperature, or variable-length sequence loss. | Author code pinned at `1774bcd007acf22dfdb2a596944186d56ac434a6`, BSD-2-Clause.  No code or dependency is imported. |
| 6 | Chen, Lucarini, Ma, Chen & Cui, *PF-PINNs: Physics-informed neural networks for solving coupled Allen-Cahn and Cahn-Hilliard phase field equations*, *Journal of Computational Physics* 529, 113843 (2025), DOI [`10.1016/j.jcp.2025.113843`](https://doi.org/10.1016/j.jcp.2025.113843), [author implementation](https://github.com/NanxiiChen/PF-PINNs/tree/f8a4980108504a984695b75d2665b27d5f26cc0b) | Uses adaptive sampling to focus PINN collocation on a moving diffuse interface in coupled phase-field equations. | `DIRECT_DOMAIN_PARTIAL`: this is the closest domain-specific interface-exposure precedent.  Its sampling is dynamically refreshed for physics residual training; it does not use a low-fidelity teacher's critical active-fraction rank band, a matched endpoint-data control, or carrier-to-physics gating. | Author code pinned at `f8a4980108504a984695b75d2665b27d5f26cc0b`, GPL-3.0.  LF6 must cite only and independently implement its frozen formulas; copying or linking GPL code is outside scope. |

## Functional-collision boundary

The inspected works separate into four primitive families that LF6 combines but
does not own:

1. **Order statistics:** Koenker--Bassett formalizes quantiles; Blondel et al.
   differentiates ranks; Berrada et al. directly targets top-k error.  LF6 does
   none of those optimizations.  It uses a deterministic teacher rank only to
   define which cells receive the same logit-MSE already used by its backbone.
2. **Event functionals:** Neural Event ODEs differentiate the time at which a
   continuous state-dependent root occurs.  LF6 instead accepts the frozen
   evaluator's discrete active-fraction event definition and aligns the cells
   that change its critical order statistic.
3. **Temporal alignment:** soft-DTW optimizes over many possible warping paths.
   LF6 fixes the teacher bracket and endpoint roles before training, so there is
   neither warping nor an alignment search.
4. **Moving-interface PINNs:** PF-PINNs confirms that interface-focused sampling
   is established and effective in phase-field PINNs.  LF6's narrower question
   is whether teacher-side event-functional frontier exposure adds information
   beyond a matched generic endpoint control before label-free refinement.

The phrase **event-frontier rank band** should therefore denote this frozen
project role, not a new general sorting, quantile, top-k, event-root, temporal
alignment, or interface-sampling algorithm.

## Attribution and claim boundary

Before results, permitted wording is:

> LF6 is a single-seed, nominal, matched solver-recovery screen that compares
> teacher-side event-critical rank-band endpoint supervision with an
> equal-information generic endpoint control, followed conditionally by
> label-free physics refinement.

If both arms are identity-valid and `DEV-R` alone passes the frozen strict gate,
the narrow mechanism statement `EVENT_FRONTIER_SUPPORTED` is defensible for the
frozen case and budget.  It does not establish a new differentiable ranking
loss, a general event-time method, or PINN value.  A PINN statement additionally
requires the separate P0 Pareto gate; a paper-positive claim additionally
requires the frozen direct-LF-only comparison and later confirmation defined by
the campaign contract.

If `DEV-U` also passes, the result is `GENERIC_TEMPORAL_ENDPOINT_SUFFICIENT`, not
rank-specific support.  If neither strict relation is met, the correct
mechanism result is `NO_RANK_SPECIFIC_INCREMENT`.  Historical LF3--LF5 arms are
context, not substitutes for the matched `DEV-U` counterfactual.

Never claim first use of quantiles, order statistics, ranking, top-k losses,
event functions, temporal alignment, interface-focused sampling, clipped
logits, or squared logit supervision.  Do not describe a teacher-selected
frontier as an unlabeled physics sample, and do not call the data-only
development arms PINNs.

## License decision

`NO_REQUIRED_EXTERNAL_DEPENDENCY_OR_LICENSE_BLOCKER`

LF6 requires no external package, model, dataset, weight, or copied source.  Its
frozen formulas are implemented independently using the existing project
runtime.  All six works are cited for concepts only.  In particular, the
GPL-3.0 PF-PINNs repository must not be copied, linked, vendored, or adapted in
this campaign; its inspection establishes only the domain prior-art boundary.

## Search boundary

The search stopped at the frozen maximum of six primary research works after
covering rank/quantile objectives, differentiable ranking, top-k-specific
training, event-function differentiation, temporal alignment, and
phase-field-PINN interface sampling.  Author repositories were inspected only
as companion records for version and license.  Secondary surveys,
third-party implementations, patents, and generic ranking applications were
excluded.  Absence of an exact collision in this bounded corpus is not evidence
of global novelty or legal freedom to operate.
