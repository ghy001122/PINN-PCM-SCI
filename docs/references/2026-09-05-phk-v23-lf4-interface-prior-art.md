# PHK-V2.3 LF4 interface-band prior-art closure

Date: 2026-09-05
Scope: 12 primary sources; papers, author repositories, and official framework documentation only
Campaign: `PHK_V23_LF4_THRESHOLD_ALIGNED_INTERFACE_BAND_MECHANISM_AND_CONDITIONAL_PHYSICS_PILOT_EXECUTE`

## Frozen verdict

`NO_EXACT_FUNCTIONAL_COLLISION_FOUND_WITHIN_FROZEN_12_SOURCE_SCOPE`

No inspected source combines all of the following in one method: a teacher threshold at `phi=0.5`; nonperiodic four-neighbour extraction of the positive and negative sides of the interface; four cycle/side-balanced pools; a matched global-extra versus identical-coordinate interface-band MSE versus two-sided softplus-logit comparison; continuation from the startup-scaled LF3 phase-logit carrier; phase-only development updates; and conditional label-free coupled-physics refinement.

This is not a priority claim. The constituent ideas have strong prior art:

- concentrating samples or model capacity around phase-field interfaces is established in phase-field PINNs;
- supervising boundaries rather than bulk regions, and explicitly aligning predicted and reference boundaries, is established in segmentation;
- learning a threshold/zero-level interface from inside/outside labels is established in neural implicit representations;
- `softplus(-z)` for a positive label and `softplus(z)` for a negative label is ordinary binary logistic loss in logit space;
- a matched ablation is experimental attribution, not an algorithmic novelty.

Therefore LF4 may be described before results only as an **attributed, project-specific solver-recovery mechanism screen**. An exact collision found later would close an originality headline, but would not invalidate the already-authorized recovery pilot or prevent use as an attributed backbone. No inspected license requires importing external code, and LF4 should remain an independent implementation.

## Collision map

| # | Primary source | Relevant mechanism | Collision with LF4 | Code / license status |
|---:|---|---|---|---|
| 1 | Wight & Zhao, *Solving Allen-Cahn and Cahn-Hilliard Equations using the Adaptive Physics Informed Neural Networks*, CiCP 29 (2021), DOI [`10.4208/cicp.OA-2020-0086`](https://doi.org/10.4208/cicp.OA-2020-0086), [arXiv:2007.04542](https://arxiv.org/abs/2007.04542) | Space/time adaptive sampling for difficult phase-field PINNs; controlled comparisons of sampling strategies. | `PARTIAL`: establishes that phase-field event/interface exposure can be changed by sampling, but has no supervised teacher boundary, two-sided pools, logit margin loss, or LF3 carrier. | No author-linked implementation or reusable code license was identified in the bounded search; third-party reproductions were excluded. |
| 2 | Wu et al., *A comprehensive study of non-adaptive and residual-based adaptive sampling for physics-informed neural networks*, CMAME 403 (2023), DOI [`10.1016/j.cma.2022.115671`](https://doi.org/10.1016/j.cma.2022.115671), [author code](https://github.com/lu-group/pinn-sampling) | Fixed, resampled, residual-adaptive and residual-adaptive-distribution sampling, including Allen-Cahn. | `PARTIAL`: generic PINN exposure/sampling precedent. It is residual-driven rather than teacher-interface-driven and does not separate the two sides of a threshold. | Author repository: Apache-2.0. |
| 3 | Chen et al., *PF-PINNs: Physics-informed neural networks for solving coupled Allen-Cahn and Cahn-Hilliard phase field equations*, JCP 529 (2025) 113843, DOI [`10.1016/j.jcp.2025.113843`](https://doi.org/10.1016/j.jcp.2025.113843), [author code](https://github.com/NanxiiChen/PF-PINNs) | Dense initial-interface sampling and adaptive points selected by field gradients or PDE residuals to follow a moving diffuse interface. | `STRONG_PARTIAL` for boundary exposure: it directly establishes interface-localized point allocation in phase-field PINNs, but its points carry physics/IC residuals rather than balanced supervised positive/negative threshold labels. | Author repository: GPL-3.0. No code is copied into LF4. |
| 4 | Elfetni & Darvishi Kamachali, *PINNs-MPF: A Physics-Informed Neural Network framework for Multi-Phase-Field simulation of interface dynamics*, EABE 176 (2025) 106200, DOI [`10.1016/j.enganabound.2025.106200`](https://doi.org/10.1016/j.enganabound.2025.106200), [arXiv:2407.02230](https://arxiv.org/abs/2407.02230), [author code](https://github.com/SFETNI/PINNs_MPF--a-Physics-Informed-Neural-Network-for-Multi-Phase-Field-problems) | Adaptive mesh-free concentration at interfaces plus a denoising MSE that pushes identified grain and no-grain regions toward one and zero. | `STRONG_PARTIAL`: closest phase-field/PINN precedent for combining interface exposure with side/region-aware phase supervision. It supervises bulk grain/no-grain correctors and physics-driven dynamic regions, not the immediate four-neighbour sides of a teacher `0.5` contour, and not a matched softplus-vs-MSE test. | Current author repository: MIT; published lineage is retained in the repository. LF4 does not reuse its code. |
| 5 | Chen et al., *Sharp-PINNs: staggered hard-constrained physics-informed neural networks for phase field modelling of corrosion*, [arXiv:2502.11942](https://arxiv.org/abs/2502.11942), [author code](https://github.com/NanxiiChen/sharp-pinns) | Bounded/hard outputs, staggered AC/CH training, specialized representation, and component ablations for sharp phase-field structure. | `PARTIAL`: a close solver-family and ablation precedent, but no teacher-derived two-sided interface band or threshold logistic term. Its architecture and optimization changes are expressly outside LF4. | Author repository: GPL-3.0. No code is copied into LF4. |
| 6 | Lei et al., *Discontinuity-aware physics-informed neural network for phase-field method in three-phase flow with phase change*, [arXiv:2511.23102v2](https://arxiv.org/abs/2511.23102) | A discontinuity-aware architecture, local artificial viscosity, time marching and adaptive loss balancing for sharp phase interfaces. | `PARTIAL`: reinforces sharp-interface representation as an identified phase-field PINN bottleneck, but addresses it through architecture and physics optimization rather than supervised boundary-side classification. | No author-linked code repository or code license was identified in the bounded search. |
| 7 | Kervadec et al., *Boundary loss for highly unbalanced segmentation*, Medical Image Analysis 67 (2021) 101851, DOI [`10.1016/j.media.2020.101851`](https://doi.org/10.1016/j.media.2020.101851), [arXiv:1812.07032](https://arxiv.org/abs/1812.07032), [author code](https://github.com/LIVIAETS/boundary-loss) | Replaces or complements region losses with a contour-distance-derived regional integral to address extreme foreground/background imbalance. | `STRONG_ADAPTED_PARTIAL`: establishes interface-targeted loss as a response to small-region imbalance. It uses a signed-distance contour functional, not sampled adjacent sides or softplus margins, and is not a temporal physical field. | Author repository: MIT. |
| 8 | Wang et al., *Active Boundary Loss for Semantic Segmentation*, AAAI 36(2) (2022), DOI [`10.1609/aaai.v36i2.20139`](https://doi.org/10.1609/aaai.v36i2.20139), [arXiv:2102.02696](https://arxiv.org/abs/2102.02696), [author code](https://github.com/wangchi95/active-boundary-loss) | Explicitly aligns predicted and ground-truth boundaries via differentiable direction prediction. | `STRONG_ADAPTED_PARTIAL`: direct boundary-alignment supervision is established, but its directional boundary transport differs from LF4's fixed teacher-side logistic classification. | Author repository: Apache-2.0. |
| 9 | Mescheder et al., *Occupancy Networks: Learning 3D Reconstruction in Function Space*, CVPR 2019, DOI [`10.1109/CVPR.2019.00459`](https://doi.org/10.1109/CVPR.2019.00459), [paper](https://openaccess.thecvf.com/content_CVPR_2019/html/Mescheder_Occupancy_Networks_Learning_3D_Reconstruction_in_Function_Space_CVPR_2019_paper.html), [author code](https://github.com/autonomousvision/occupancy_networks) | Represents a surface as the continuous decision boundary of a classifier trained from occupied/unoccupied point labels. | `STRONG_PRIMITIVE_COLLISION`: threshold-defined interfaces and binary logit supervision are established. It has no phase dynamics, startup identity, four-neighbour band, per-cycle quotas, or PINN closure. | Author repository: MIT. |
| 10 | Park et al., *DeepSDF: Learning Continuous Signed Distance Functions for Shape Representation*, CVPR 2019, DOI [`10.1109/CVPR.2019.00025`](https://doi.org/10.1109/CVPR.2019.00025), [arXiv:1901.05103](https://arxiv.org/abs/1901.05103), [author code](https://github.com/facebookresearch/DeepSDF) | Learns a continuous field whose zero level set is the surface and whose sign labels the two sides; near-surface sampling controls interface fidelity. | `STRONG_PRIMITIVE_COLLISION`: two-sided interface supervision and interface-focused sampling are established, but via signed-distance regression in static 3-D geometry, not threshold-logistic supervision of a phase trajectory. | Archived author repository: MIT. |
| 11 | Lin et al., *Focal Loss for Dense Object Detection*, ICCV 2017, DOI [`10.1109/ICCV.2017.324`](https://doi.org/10.1109/ICCV.2017.324), [paper](https://openaccess.thecvf.com/content_ICCV_2017/html/Lin_Focal_Loss_for_ICCV_2017_paper.html), [arXiv:1708.02002](https://arxiv.org/abs/1708.02002) | Modulates cross entropy so sparse hard examples are not overwhelmed by easy negatives. | `PARTIAL`: establishes rare/hard-example classification as a standard response to imbalance. LF4 instead fixes equal side quotas and ordinary logistic loss; it must not claim focal-style weighting or hard-negative mining. | The paper points to Detectron; no external implementation is needed or imported for LF4. |
| 12 | PyTorch, [`BCEWithLogitsLoss`](https://pytorch.org/docs/stable/generated/torch.nn.BCEWithLogitsLoss.html) and [authoritative source](https://github.com/pytorch/pytorch/blob/main/torch/nn/modules/loss.py) | Numerically stable sigmoid plus binary cross entropy. For `y=1`, the per-example term is `softplus(-z)`; for `y=0`, it is `softplus(z)`. | `EXACT_PRIMITIVE_COLLISION`: LF4's two softplus terms are standard binary logistic loss. Division by `log(2)` merely normalizes the zero-margin value and is not a new loss family. | PyTorch's main project code is BSD-3-Clause; LF4 uses the existing project dependency, not copied source. |

## Claim boundary for LF4

### Claims permitted only if the frozen matched gates pass

1. If `Rmin(DEV-M)-Rmin(DEV-G) >= 0.03` with the frozen precision, mass, timing, locality, recovery and field-preservation constraints, LF4 may support:

   > Under the frozen single-seed nominal electro-thermal phase-transition problem, teacher-interface exposure improved minimum two-cycle event recall beyond an equal-budget global-extra supervision control.

   This is a system-specific **boundary-exposure** result, not a claim that interface sampling is new.

2. If `Rmin(DEV-C)-Rmin(DEV-M) >= 0.03` under the same constraints and identical band coordinates, LF4 may additionally support:

   > On the same exposed boundary coordinates, threshold-aligned two-sided logistic supervision improved minimum event recall beyond continuous logit-increment MSE.

   This is the load-bearing LF4 mechanism claim. It is an empirical attribution within the frozen carrier and cannot be generalized to all phase-field PINNs from one seed/case.

3. If conditional P0 then passes its preservation and fixed-physics Pareto gates, LF4 may support a **single-seed within-architecture solver-recovery/PINN pilot**. Direct-LF-only noninferiority and the later multi-seed/OOD program remain separate requirements for a candidate or paper-positive method claim.

### Claims not permitted

- first interface-aware, boundary-aware, rare-event-aware, two-sided, threshold, logistic, softplus, or phase-field PINN loss;
- first use of dense/adaptive interface sampling in phase-field PINNs;
- novelty of binary cross entropy, softplus margins, equal positive/negative quotas, or matched ablation;
- strict single-factor attribution to the earlier LF3 latent parameterization;
- general PINN superiority, strong-baseline gain, practical superiority, SOTA, or OOD robustness without their corresponding frozen evidence.

If DEV-G explains the improvement, the result is `MORE_UPDATES_OR_GENERIC_SUPERVISION_SUFFICIENT`. If DEV-M does not beat DEV-G by the frozen margin, no boundary-exposure mechanism claim is allowed. If DEV-C does not beat DEV-M by the frozen margin, no threshold-aligned-loss mechanism claim is allowed. A negative matched result remains publishable only as bounded failure analysis.

## Reuse and citation requirements

- Implement LF4 independently from its frozen equations. Do not copy GPL-3.0 PF-PINNs or Sharp-PINNs code.
- Cite PF-PINNs and PINNs-MPF when motivating interface exposure in phase-field PINNs.
- Cite Kervadec et al. and Wang et al. when discussing boundary-focused supervision.
- Cite Occupancy Networks or DeepSDF when describing the established inside/outside decision-boundary analogy.
- Describe the LF4 band term as balanced binary logistic/BCE-with-logits supervision, not as a newly invented softplus loss.
- Preserve the three matched arms and identical DEV-M/DEV-C band coordinates: without them, any positive outcome cannot distinguish generic extra supervision, interface exposure, and threshold-aligned loss.

## Search boundary

The search stopped at 12 primary sources after covering all five frozen collision questions: phase-field PINN interface exposure, rare-event/boundary imbalance, explicit boundary alignment, two-sided implicit-interface supervision, and softplus/logistic identity. It did not attempt an exhaustive systematic review, patent search, or proof of absolute priority. The verdict is therefore scoped to the sources and functional identity stated above.
