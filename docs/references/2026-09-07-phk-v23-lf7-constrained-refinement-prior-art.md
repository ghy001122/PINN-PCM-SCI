# PHK-V2.3 LF7 competence-filtered refinement prior-art closure

Date: 2026-09-07  
Scope: six primary research works; author repositories were checked only when directly associated with a paper  
Campaign object: LF7 competence-filtered blockwise backtracking physics refinement pilot

## Frozen LF7 object reviewed

Both matched arms start from the exact LF6 `DEV-R` carrier and optimize the same
strong-form objective on the same pre-materialized 1,200-batch physics stream:

```text
J_train = L_PDE + 5 L_BC + L_IC
eta_0 = 1.25e-4
block size = 25 accepted updates
```

`P0-S` is a fixed-small-step control. `P0-F` additionally snapshots the complete
model, optimizer and random-number state before each block. A proposed block is
accepted only if it preserves the frozen full-medium function-space competence
conditions (finite/range/potential, event safety, and field/topology error ratios)
**and** strictly decreases the fixed-blind physics objective. Rejection restores
the exact snapshot, reuses the same 25 materialized batches and retries at the
dyadic scales `eta_0/{1,2,4,8,16}`. Medium labels enter only through the
accept/reject audit and contribute no training gradient.

This object is therefore not a conventional parameter-space trust-region method,
not a line search on one deterministic gradient direction, not a penalty/filter
SQP algorithm, and not label-free refinement. Its frozen identity is:

```text
ATTRIBUTED_CONSTRAINED_OPTIMIZATION_PRIMITIVES_WITH_PROJECT_SPECIFIC_EVENT_COMPETENCE_FILTER
```

## Frozen verdict

`NO_EXACT_FUNCTIONAL_COLLISION_FOUND_WITHIN_BOUNDED_6_ITEM_SCOPE`

The six sources establish strong prior art for every load-bearing primitive:
hard-constrained/trust-region PINN training; penalty-free filter acceptance;
feasibility restoration; backtracking step reduction; multifidelity preservation;
and constrained multifidelity model management. No inspected work combines the
exact LF7 sequence of a pre-trained event carrier, fixed 25-step Adam proposals,
full-state rollback, same-batch dyadic retry, a low-fidelity event-competence
auditor, and an independently fixed physics-decrease auditor.

This bounded negative search is not a priority proof. LF7 remains an attributed,
project-specific solver-recovery screen. An exact collision discovered later
would remove headline originality, but would not invalidate an independently
implemented and properly cited pilot.

## Six-item collision map

| # | Primary source | Relevant precedent | Collision identity | License / reuse decision |
|---:|---|---|---|---|
| 1 | Cheng & Na, *Physics-Informed Neural Networks with Trust-Region Sequential Quadratic Programming* (2024), [arXiv:2409.10777](https://arxiv.org/abs/2409.10777) | Formulates PINN training as hard-constrained nonlinear optimization; a trust-region SQP step may be skipped when the trial point is worse. | `DIRECT_PINN_TRUST_REGION_PARTIAL`: trSQP-PINN uses linear-quadratic constraint models, a parameter-space radius and quasi-Newton/SQP machinery. LF7 instead proposes first-order Adam blocks and tests their realized function-space competence plus a blind physics objective. | Paper citation only; no author implementation or reusable code license was located in this bounded check. LF7 imports no code. |
| 2 | Fletcher & Leyffer, *Nonlinear Programming without a Penalty Function*, *Mathematical Programming* 91 (2002), DOI [`10.1007/s101070100244`](https://doi.org/10.1007/s101070100244) | Introduces trust-region SQP filter acceptance that treats objective reduction and constraint violation separately rather than collapsing them into a penalty merit function. | `DIRECT_FILTER_FOUNDATIONAL_PARTIAL`: LF7 likewise separates physics progress from competence, but requires both, keeps no Pareto filter, solves no SQP subproblem and has no convergence claim. | Published article; publisher copyright applies. Citation only. |
| 3 | Wächter & Biegler, *On the Implementation of an Interior-Point Filter Line-Search Algorithm for Large-Scale Nonlinear Programming*, *Mathematical Programming* 106 (2006), DOI [`10.1007/s10107-004-0559-y`](https://doi.org/10.1007/s10107-004-0559-y), [official article](https://link.springer.com/article/10.1007/s10107-004-0559-y), [official Ipopt code](https://github.com/coin-or/Ipopt) | Combines filter line search, rejected trials, step reduction and a feasibility-restoration phase in a large-scale constrained optimizer. | `DIRECT_FILTER_RESTORATION_BACKTRACKING_PARTIAL`: LF7 has no interior-point/KKT system, restoration phase or filter convergence claim; it restores an entire Adam block and retries the same batches. | Ipopt is EPL-2.0, but LF7 neither links nor copies it. Paper and code are cited only. |
| 4 | Armijo, *Minimization of Functions Having Lipschitz Continuous First Partial Derivatives*, *Pacific Journal of Mathematics* 16 (1966), DOI [`10.2140/pjm.1966.16.1`](https://doi.org/10.2140/pjm.1966.16.1), [journal PDF](https://msp.org/pjm/1966/16-1/pjm-v16-n1-p01-p.pdf) | Establishes variable step-size reduction/sufficient-decrease logic underlying deterministic backtracking. | `DIRECT_BACKTRACKING_FOUNDATIONAL_PARTIAL`: LF7 halves a learning rate after rejection, but replays a 25-update stochastic Adam block from a complete snapshot and asks only for fixed-blind strict decrease; it does not test an Armijo slope condition along one fixed direction. | Published article; citation only. No external line-search implementation is used. |
| 5 | Maddu, Sturm, Müller & Sbalzarini, *Inverse-Dirichlet Weighting Enables Reliable Training of Physics Informed Neural Networks*, *Machine Learning: Science and Technology* 3 (2022) 015026, DOI [`10.1088/2632-2153/ac3712`](https://doi.org/10.1088/2632-2153/ac3712), [arXiv:2107.00940](https://arxiv.org/abs/2107.00940), [author code](https://github.com/mosaic-group/inverse-dirichlet-pinn) | Identifies objective conflict and catastrophic interference/forgetting during sequential PINN training and mitigates it through dynamic inverse-Dirichlet loss weighting. | `DIRECT_PINN_PRESERVATION_MOTIVATION_PARTIAL`: LF7 targets the same broad physics-closure forgetting problem, but uses post-block function-space acceptance and rollback rather than gradient/loss reweighting. | No explicit repository license was identified in the bounded author-code check. Cite only; do not copy or depend on it. |
| 6 | Alexandrov, Dennis, Lewis & Torczon, *A Trust Region Framework for Managing the Use of Approximation Models in Optimization*, *Structural Optimization* 15 (1998), DOI [`10.1007/BF01197433`](https://doi.org/10.1007/BF01197433), [author-hosted paper](https://www.cs.wm.edu/~va/research/adlt.pdf) | Establishes trust-region model management in which proposed progress from an approximation is checked against the true objective and the trusted region is reduced when model agreement is inadequate. | `DIRECT_MULTIFIDELITY_ACCEPTANCE_PARTIAL`: LF7 also separates proposal generation from authoritative acceptance, but physics itself generates the update while medium data only audit competence; there is no corrected surrogate or actual/predicted model-agreement ratio. | Published paper; citation only. No model-management code, data or external model is imported. |

## Functional-collision and terminology boundary

The nearest PINN-specific optimization work is trSQP-PINN, but its trust region
bounds a linear-quadratic parameter step. LF7 has no trust-region subproblem or
model-agreement ratio: its “region” is an empirically accepted chain of neural
functions. The classical filter accepts objective improvement *or* feasibility
improvement, whereas LF7 requires competence preservation *and* physics decrease.
Wächter--Biegler supplies the closest restoration/rejection precedent, but LF7
has no restoration phase. Armijo supplies the step-reduction primitive, but LF7
recomputes 25 Adam updates and their moment trajectory rather than scaling one
direction. Inverse-Dirichlet PINN directly establishes the forgetting problem,
not LF7's acceptance-based remedy.

Accordingly, use **competence-filtered blockwise backtracking physics
refinement** or **CFBR** as the project-specific composition name. Do not call it
a new trust-region theory, SQP/filter algorithm, exact restoration method,
Armijo line search, or general multifidelity optimizer. The frozen event/field
gates and dyadic scale schedule are project choices, not standalone novelty.

The distinction from label-free refinement is load-bearing: medium predictions
do not create a gradient, yet they decide which optimizer blocks survive. The
scientifically accurate identity is therefore
`MULTIFIDELITY_COMPETENCE_FILTERED_PINN_REFINEMENT`.

## Permitted claim boundary

Before results, LF7 is a nominal, single-seed matched mechanism pilot. If the
small-step control fails its safety-Pareto gate while CFBR passes it, the bounded
statement is:

> Under the frozen carrier, physics stream, blind objective and update budget,
> function-space competence filtering with exact rollback and dyadic block
> backtracking preserved the prespecified event carrier while obtaining physics
> decrease that an equal-start fixed-small-step continuation did not preserve.

If `P0-S` also passes, small learning rate is sufficient and the filter is not
load-bearing. If CFBR stalls, the result is evidence only that no accepted block
was found under these five scales and frozen checks; it is not proof that no
preservation-compatible strong-form path exists. Without the direct `LF_ONLY`
gate, additional seeds and the future equal-information sparse task, no outcome
supports general PINN superiority, practical advantage, robustness, SOTA or
paper-ready candidate status.

Never claim first use of trust regions, filter methods, feasibility restoration,
rollback, backtracking, catastrophic-forgetting protection, multifidelity model
management or hard-constrained PINN optimization.

## Dependency and license decision

`NO_REQUIRED_EXTERNAL_DEPENDENCY_OR_LICENSE_BLOCKER`

LF7 implements the frozen logic independently with the existing project runtime.
It imports no external source, optimizer, model, weight, dataset or paper text.
The six works are conceptual precedents only. Sources whose code license was not
resolved remain citation-only and must not be copied, linked or vendored.

## Search boundary

The search stopped at the frozen maximum of six primary works after covering the
five requested families: constrained/trust-region PINNs; filter and restoration
methods; rollback/backtracking; continual physics-informed preservation; and
multifidelity acceptance/model management. Secondary surveys, third-party
reimplementations, patents and generic checkpointing utilities were excluded.
The closure determines attribution and dependency legality for this pilot only;
it is neither a systematic review nor a global novelty/freedom-to-operate claim.
