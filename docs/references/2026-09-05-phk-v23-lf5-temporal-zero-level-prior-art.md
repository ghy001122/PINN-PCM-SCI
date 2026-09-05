# PHK-V2.3 LF5 temporal zero-level prior-art closure

Date: 2026-09-05
Write-lock timestamp: `20260905T150045Z`
Scope: 8 primary sources; original papers, author repositories, and official framework documentation only
Campaign object: LF5 temporal zero-level mechanism pilot

## Frozen LF5 object reviewed

For teacher phase `phi_m`, define

```text
epsilon = 1e-8
D = 36.84136146790473
z* = logit(clip(phi_m, epsilon, 1-epsilon))
rho* = -z*_{i,k} / (z*_{i,k+1} - z*_{i,k})
r_theta = (1-rho*) z_theta(i,t_k) + rho* z_theta(i,t_{k+1})
```

An edge is one same-cell pair of adjacent saved times with a teacher sign crossing. The four fixed pools are `C1_ONSET`, `C1_RECOVERY`, `C2_ONSET`, and `C2_RECOVERY`, and

```text
L_TZL = (1/4) sum_C mean_{e in C} [(r_theta(e)/D)^2].
```

`DEV-T` starts from the exact LF3-T0 carrier, reuses the LF4 base and spatial-band objectives, performs 400 phase-only updates, and uses

```text
L_DEV-T = 0.50 L_base + 0.25 L_spatial + 0.25 L_TZL.
```

The later matched temporal-edge endpoint-MSE control is not part of this run. Its attribution role is frozen below.

## Frozen verdict

`NO_EXACT_FUNCTIONAL_COLLISION_FOUND_WITHIN_FROZEN_8_SOURCE_SCOPE`

No inspected source combines all of these operations in one method: extract same-cell adjacent saved-time sign crossings from teacher phase logits; compute a teacher secant crossing fraction `rho*`; force the student's two endpoint logits to have a zero-valued secant interpolant at that fixed fraction; normalize by the clipped-logit span `D`; balance onset and recovery separately across two cycles; and add that loss to the already-frozen LF4 base plus spatial interface-band continuation from the exact LF3-T0 carrier.

This is **not** a priority claim. Every load-bearing primitive has close prior art: moving interfaces as zero level sets; differentiable zero-crossing events; neural fields forced to vanish on known interface points; learned moving boundaries in PINNs; secant interpolation of sign-straddling neural-field samples; time-conditioned zero-level surfaces; level-set PINNs; and discrete temporal boundary supervision with class balancing. LF5 is therefore, before results, an **attributed project-specific combination pilot / solver-recovery screen**, not a new general loss family.

## Collision map

| # | Primary source | Relevant mechanism | Collision identity | Code / license status |
|---:|---|---|---|---|
| 1 | Osher & Sethian, *Fronts Propagating with Curvature-Dependent Speed: Algorithms Based on Hamilton-Jacobi Formulations*, JCP 79 (1988), DOI [`10.1016/0021-9991(88)90002-2`](https://doi.org/10.1016/0021-9991(88)90002-2), [author-hosted paper](https://math.berkeley.edu/~sethian/Papers/sethian.osher.88.pdf) | Represents and evolves a moving front implicitly as a level set, allowing topology changes. | `DIRECT_FOUNDATIONAL_PARTIAL`: establishes the zero-level moving-interface identity, but contains no neural teacher, saved-cadence crossing fraction, supervised loss, or event-pool balancing. | Paper only; no external code is required. Publisher copyright applies. |
| 2 | Chen, Amos & Nickel, *Learning Neural Event Functions for Ordinary Differential Equations*, ICLR 2021, [OpenReview](https://openreview.net/forum?id=kW_zpEmMLdP), [arXiv:2011.03902](https://arxiv.org/abs/2011.03902), [author code](https://github.com/rtqichen/torchdiffeq) | Defines a continuous-time event as the first zero of an event function and differentiates the event time through an ODE root solve. | `DIRECT_STRONG_PARTIAL`: the closest temporal zero-crossing precedent, but it differentiates a solver-located continuous root. It does not use a teacher's adjacent saved endpoints, a fixed secant fraction, phase logits, or four onset/recovery pools. | `torchdiffeq`: MIT. No code is imported into LF5. |
| 3 | Gropp et al., *Implicit Geometric Regularization for Learning Shapes*, ICML/PMLR 119 (2020), [paper](https://proceedings.mlr.press/v119/gropp20a.html), [arXiv:2002.10099](https://arxiv.org/abs/2002.10099), [author code](https://github.com/amosgropp/IGR) | Trains an implicit neural field to vanish on known surface samples, together with Eikonal regularization. | `ADAPTED_STRONG_PRIMITIVE_PARTIAL`: directly establishes zero-value supervision at a known interface location. Its interface is static and spatial; it does not infer a temporal crossing fraction from adjacent teacher frames. | No explicit reusable code license was identified in the bounded repository check; cite only and do not copy. |
| 4 | Chen et al., *Recovering Fine Details for Neural Implicit Surface Reconstruction (D-NeuS)*, WACV 2023, pp. 4330-4339, [CVF paper](https://openaccess.thecvf.com/content/WACV2023/html/Chen_Recovering_Fine_Details_for_Neural_Implicit_Surface_Reconstruction_WACV_2023_paper.html), [arXiv:2211.11320](https://arxiv.org/abs/2211.11320), [author code](https://github.com/fraunhoferhhi/D-NeuS) | Finds adjacent SDF samples with a sign change and uses differentiable linear interpolation to estimate a zero-crossing surface point along a ray. | `ADAPTED_CLOSEST_MATHEMATICAL_PARTIAL`: shares sign-straddling endpoints plus secant/linear zero localization. D-NeuS derives the crossing from the predicted spatial SDF and uses the point for rendering/feature consistency; LF5 fixes `rho*` from teacher temporal logits and penalizes the student's endpoint interpolant there. It is not an exact collision. | Author repository: MIT, including the stated NeuS lineage. LF5 independently implements its frozen equation. |
| 5 | Wang & Perdikaris, *Deep learning of free boundary and Stefan problems*, JCP 428 (2021) 109914, DOI [`10.1016/j.jcp.2020.109914`](https://doi.org/10.1016/j.jcp.2020.109914), [arXiv:2006.05311](https://arxiv.org/abs/2006.05311), [author code](https://github.com/PredictiveIntelligenceLab/DeepStefan) | Uses separate neural networks for the physical field and moving boundary and applies free-boundary/interface conditions at the learned boundary. | `DIRECT_PINN_PARTIAL`: establishes supervised/physics-constrained moving-interface timing and geometry in a PINN family. It has no phase-logit zero level, teacher secant target, adjacent saved-cadence edge, or balanced onset/recovery residual. | The author repository exposes no explicit license in the bounded check; cite only and do not copy. |
| 6 | Alblas et al., *Implicit Neural Representations for Modeling of Abdominal Aortic Aneurysm Progression*, FIMH 2023, DOI [`10.1007/978-3-031-35302-4_37`](https://doi.org/10.1007/978-3-031-35302-4_37), [arXiv:2303.01069](https://arxiv.org/abs/2303.01069) | Represents a surface over time as the zero level set of a time-conditioned neural SDF, supervised at sparse longitudinal observations with temporal-gradient regularization. | `ADAPTED_STRONG_PARTIAL`: establishes spatiotemporal zero-level alignment under sparse saved observations, but not an interval crossing fraction, onset/recovery event semantics, or PINN residual. | No author code or reusable code license was identified in the bounded search. The accessible manuscript is cited; no material is copied. |
| 7 | Mullins et al., *Physics-informed neural networks for solving moving interface flow problems using the level set approach*, Physics of Fluids 37 (2025) 107124, DOI [`10.1063/5.0289386`](https://doi.org/10.1063/5.0289386), [arXiv:2502.02440](https://arxiv.org/abs/2502.02440), [author code](https://github.com/m-mullins/LS-PINN) | Evolves a continuous level-set field with PDE, IC and optional Eikonal terms in a PINN, including strongly deforming interfaces. | `DIRECT_PINN_PARTIAL`: establishes level-set PINNs for moving interfaces, but contains no teacher crossing loss, adjacent saved-time secant, or event-timing pool balance. | The repository contains a `LICENSE` file, but its exact SPDX/text could not be resolved in the bounded fetch. Cite only; do not copy. |
| 8 | Lin et al., *BMN: Boundary-Matching Network for Temporal Action Proposal Generation*, ICCV 2019, DOI [`10.1109/ICCV.2019.00399`](https://doi.org/10.1109/ICCV.2019.00399), [CVF paper](https://openaccess.thecvf.com/content_ICCV_2019/html/Lin_BMN_Boundary-Matching_Network_for_Temporal_Action_Proposal_Generation_ICCV_2019_paper.html), [arXiv:1907.09702](https://arxiv.org/abs/1907.09702), [official PaddleVideo implementation](https://github.com/PaddlePaddle/PaddleVideo/blob/develop/docs/en/model_zoo/localization/bmn.md) | Predicts start/end boundary probabilities on a discretized timeline and uses balanced classification objectives for sparse temporal boundaries. | `ADAPTED_TEMPORAL_BOUNDARY_PARTIAL`: establishes saved-grid temporal-boundary supervision and imbalance handling, but not a physical zero-level field, secant root, moving phase interface, or PINN. | Official PaddleVideo implementation: Apache-2.0. No code is imported into LF5. |

## Functional collision boundary

The closest inspected fragments do not compose into an exact LF5 predecessor:

- Neural Event ODEs locate and differentiate an actual continuous solver root; LF5 supervises a teacher-derived **saved-cadence secant root** without invoking a root solver.
- D-NeuS supplies the closest interpolation algebra, but across predicted spatial SDF samples on a camera ray; LF5 applies it across teacher temporal phase logits at one physical cell and penalizes student logits.
- IGR and the AAA progression INR establish `f=0` supervision on known spatial or spatiotemporal surfaces; they do not define the teacher interval fraction used by LF5.
- DeepStefan and LS-PINN establish neural/PINN moving-interface models; neither uses this teacher edge residual.
- BMN establishes discrete temporal start/end supervision and balancing; it does not represent boundaries as roots of a continuous physical field.

An exact collision found later would close an originality headline but would not invalidate an independently implemented, properly attributed recovery backbone. The bounded negative search cannot establish absolute priority.

## Mathematical and terminology limits

`rho*` is only a first-order crossing estimate for one teacher sign-straddling saved interval. It requires finite endpoint logits, a nonzero denominator, and `0 <= rho* <= 1`; a single exactly-zero endpoint gives `rho*=0` or `1`, while two zero endpoints are rejected. Endpoint signs reveal only an odd number of crossings; they cannot identify multiple crossings inside one saved interval.

`r_theta=0` aligns the zero of the **linear secant through the two predicted endpoint logits** with the teacher's secant fraction. It does not evaluate `z_theta` at `t_k + rho* Delta t`, and therefore does not prove the continuous neural trajectory is zero at that time. Approximate residuals also need not guarantee a sign change; exact zero can be met by degenerate near-zero endpoints, and the residual alone does not encode onset versus recovery orientation. Those identities must remain guarded by the inherited field, spatial-band, event, precision, mass, timing, and recovery checks.

Accordingly, use **teacher-anchored saved-cadence secant zero-level alignment** or **temporal zero-level residual**. Do not call it an exact event-time loss, continuous-time root loss, kinetic law, or topology guarantee. `epsilon`, `D`, four-pool averaging, and phase-only continuation are fixed numerical/experimental choices, not standalone novelty.

## Why the later matched endpoint-MSE control is necessary

The LF5 residual is a linear combination of the same two student endpoint logits:

```text
grad_{z_k} r_theta = 1-rho*
grad_{z_{k+1}} r_theta = rho*.
```

Therefore a positive `DEV-T` could arise from extra edge-local supervision or endpoint-gradient reweighting rather than crossing-fraction semantics. The LF4 comparator does not control this new temporal-edge information.

The minimum future attribution arm must start from the exact same LF3-T0 checkpoint and reuse the same LF4 base/spatial term, four pools, exact edges, batch order, phase-only optimizer, 400 updates, total `0.25` temporal weight, and evaluation. It changes only `L_TZL` to the no-new-scale endpoint target:

```text
L_ENDPOINT = (1/4) sum_C mean_{e in C} [
  0.5 ((z_theta,k-z*_k)/D)^2 +
  0.5 ((z_theta,k+1-z*_{k+1})/D)^2
].
```

That arm is a future matched control, not authorized or executed here. Until it exists, any positive LF5 result is attributable only to the **combined temporal-edge supervision mechanism**, not uniquely to secant zero-level alignment.

## Permitted claim boundary

Before results, LF5 may be described only as an attributed single-seed nominal solver-recovery pilot.

If the frozen LF5 mechanism gate passes against its prespecified comparator, a bounded statement is permitted:

> Under the frozen nominal carrier, sampler and update budget, adding teacher-anchored saved-cadence temporal zero-level supervision to the existing base plus spatial-band objective improved the prespecified two-cycle timing/recall criterion.

Without the future endpoint-MSE control, do not claim that secant/root semantics rather than generic temporal-edge endpoint supervision caused the gain. Without multi-seed, strong-baseline and OOD evidence, do not claim general PINN superiority, robust event recovery, practical advantage, SOTA, or paper-ready candidate status.

Never claim first use of zero-level sets, event roots, linear/secant zero interpolation, moving-interface PINNs, temporal boundary supervision, class/event balancing, clipped logits, or normalized squared residuals. Negative or mixed results remain bounded evidence about this frozen composition only.

## Reuse and license decision

LF5 needs no external code or model asset: implement the frozen formulas independently and cite the conceptual precedents. Consequently there is **no license blocker for the current pilot**.

- MIT sources: `torchdiffeq`, D-NeuS.
- Apache-2.0 source: official PaddleVideo BMN implementation.
- IGR and DeepStefan: no explicit reusable repository license identified; code copying is prohibited.
- LS-PINN: license text unresolved in the bounded fetch; code copying is prohibited until independently resolved.
- Publisher/venue papers are references, not code assets; no text, data, weights, or implementation is imported.

## Search boundary

The search stopped at the frozen maximum of 8 primary sources after covering: foundational moving zero-level interfaces; differentiable temporal event roots; zero-valued neural-interface supervision; secant interpolation of sign-straddling neural fields; learned free boundaries in PINNs; sparse-time zero-level surface alignment; level-set PINNs; and saved-grid temporal boundary balancing. Secondary surveys, third-party reimplementations, patents, and unrelated generic alignment losses were excluded. This is a bounded nearest-neighbour closure, not an exhaustive systematic review or proof of priority.
