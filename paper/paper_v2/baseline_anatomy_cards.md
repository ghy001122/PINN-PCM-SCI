# Baseline anatomy cards and transfer boundaries

These cards summarize the primary-source audit used to design PHK-V2. They distinguish the original contribution (`A`), a possible PCM adaptation (`A′`), implementation-only engineering, and unresolved limitations. They do not report PHK method results: the PHK-V2 Oracle Gate stopped before PINN training.

## Card 1 — Sharp-PINNs

**Primary identity.** Chen et al., *Sharp-PINNs: A Physics-Informed Neural Network with Formalized Sharpness for Corrosion Modeling*, *Computer Methods in Applied Mechanics and Engineering* 447 (2025), 118346. Official repository fixed at `4b7029e3e1e0b82482d245ba12e3ec0945d87ed9`, GPL-3.0.

**Original problem and idea (`A`).** Coupled Allen–Cahn/Cahn–Hilliard corrosion phase fields suffer from competing residuals and sharp interfaces. The paper combines staggered AC/CH optimization, random Fourier features, a modified MLP, a KKS-based hard output constraint, and gradient-norm loss weighting.

**What the original evidence actually supports.** Its 2D double-pit table reports mean absolute L2 error `6.066e-4` for the full method and larger errors when individual components are removed. The reported 3D speed comparison uses an A40 GPU for PINN training and CPU FEniCS, so it is not a hardware-matched universal speed claim. The paper does not report a multi-seed uncertainty analysis sufficient for PHK thresholds.

**Identity hazard.** The paper's 1,000-step ablation identity and the current repository's causal/RAR configurations and up-to-800k-epoch recipes must be treated as separate comparators. Causal weighting and RAR are not silently part of the paper method.

**Potential PCM transfer (`A′`).** Replace AC/CH scheduling with electric/thermal/phase block scheduling; replace corrosion-specific hard constraints with exact wall-cell IC/BC and phase-range transforms; route high-frequency capacity using phase/hotspot indicators.

**Kill test.** Any gain must survive matched collocation support, parameter count, automatic-differentiation work, optimizer updates, and measured compute. A gain created only by extra support or steps is not a PHA/KC architectural contribution.

**PHK-V2 status.** Fixed-source module smoke only. No paper metric was reproduced and no PHK comparison was run.

## Card 2 — PF-PINNs

**Primary identity.** Cui et al., *PF-PINNs: Physics-informed neural networks for solving coupled Allen–Cahn and Cahn–Hilliard phase-field equations*, *Journal of Computational Physics* 529 (2025), 113843. Official repository fixed at `a25f75b5fd40657e5ce98467d7afd0d0052464d1`, GPL-3.0.

**Original problem and idea (`A`).** Min–max normalization, interface/initial-state refinement, residual-adaptive refinement, and random-batch NTK trace weights target coupled phase-field optimization and interface under-sampling.

**Likely limitation.** The sampling policy changes the support and therefore the compute. It cannot be mixed into an architectural attribution table without explicit equal-work controls. An oracle-derived interface mask would also leak labels in a sealed PHK evaluation.

**Potential PCM transfer (`A′`).** Use only training-time phase, temperature, Joule, and residual indicators to construct phase–hotspot sampling; keep a fixed-support architecture track and a separately budgeted best-method sampling track.

**PHK-V2 status.** Fixed-source module smoke only. No paper metric or PHK method endpoint was evaluated.

## Card 3 — PirateNet and jaxpi2

**Primary identities.** PirateNet is the JMLR 2024 gated residual architecture with zero-initialized trainable residual coefficients; its original jaxpi code uses a Penn custom non-profit research license that restricts redistribution. jaxpi2 is a later Apache-2.0 repository fixed here at `77a5c1315a056388271822c35ad512a5a192b60d` and accompanies the adaptive pseudo-time preprint.

**Original ideas (`A`).** PirateNet lets a network grow from shallow to deep during optimization and uses physics-informed output initialization. Adaptive pseudo-time adds a homotopy residual and estimates a local Jacobian scale to update the pseudo-time step.

**Why this is a mandatory falsification control.** Pseudo-time addresses spurious low-loss PINN solutions without warping physical time. If it removes the apparent temporal problem under an equal budget, a field-selective kinetics clock has no independent claim unless it still improves event/path/OOD endpoints.

**Potential PCM transfer (`A′`).** Apply residual growth or pseudo-time scales separately to electric, thermal, and phase blocks; retain physical-time evaluation and forbid oracle-dependent gates.

**PHK-V2 status.** The full jaxpi2 dependency install failed twice with Windows path-length errors. A bounded minimal Apache-2.0 environment produced a finite x64 CPU PirateNet architecture-only forward pass (2,245 parameters). This is not reproduction of any paper result.

## Card 4 — Causality-RBAR

**Primary identity.** arXiv:2410.20212v2.

**Original problem and idea (`A`).** Alternating causal training with residual-ranked adaptive refinement can move support toward an Allen–Cahn interface and avoid a low-loss stationary false solution.

**Limitation.** The complex example expands roughly 400 points per time step to about 4,000 and uses very long retraining; the gain may be support/compute-driven. The official code URL cited by the paper returned 404 during the audit, so code identity and license are unknown.

**Potential PCM transfer (`A′`).** Pulse-stage causal ordering and phase/hotspot residual refinement belong in a separately budgeted best-method track, not in the fixed-support factorial attribution.

**PHK-V2 status.** Literature anatomy only; no code reproduction.

## Card 5 — Re-spacing and phase-change heat PINNs

**Original ideas (`A`).** The re-spacing layer pretrains an encoder to regularize stiff coordinate/sample distributions. The phase-change heat PINN uses enthalpy regularization and compares static weighting, gradient-based weighting, soft attention, and sequential time training for a Stefan problem.

**Limitations.** Both are simpler than an electrothermal device loop; re-spacing has an extra pretraining budget, and sequence-in-time may propagate error. Author-code and license closure was not available from the audited primary pages.

**Potential PCM transfer (`A′`).** A re-spacing-like phase-only transform is a direct control for KC. Enthalpy/latent-heat and time-sequence ideas can inform thermal/phase coupling but cannot be relabeled as device-level validation.

**PHK-V2 status.** Literature controls only; not executed.

## Card 6 — Miquel et al. wall-cell multiphysics

**Primary identity.** Miquel et al., *A multiphysics framework for phase-change memory simulations*, *Journal of Applied Physics* 136 (2024), 145102.

**Original problem and idea (`A`).** A two-dimensional wall-type GGST cell couples multiphase fields, phase-dependent electrothermal transport, Joule and latent heat, thermal boundary resistance, and threshold/Poole–Frenkel conduction.

**Decisive openness limitation.** Exact GGST composition is confidential, some conductivity data are internal and unpublished, several parameters are calibrated or estimated, and no open solver was supplied. The paper cannot provide an open exact oracle.

**PHK adaptation (`A′`).** PHK-V2 retained only the wall-cell topology and the electric→Joule heat→phase causal checklist. Every coefficient and constitutive simplification is explicitly an engineering dimensionless contract value.

**PHK-V2 status.** Topology inspiration only; no author-model, material, or experimental reproduction claim.

## Attribution matrix that was preregistered but not reached

| Arm | PHA-MF | Field-selective KC | Purpose | PHK-V2 execution |
|---|---:|---:|---|---|
| Strong raw | 0 | 0 | qualified reference architecture/training baseline | not reached |
| PHA only | 1 | 0 | spatial routing main effect | not reached |
| KC only | 0 | 1 | phase-dynamics time allocation main effect | not reached |
| PHK full | 1 | 1 | combination and interaction | not reached |

The planned controls included global multi-frequency, generic monotone clock, adaptive pseudo-time, wider raw, extra-work raw, wrong-gate/shuffled-gate, and matched sampling tracks. None was opened because the upstream oracle/event gate failed. The absence of these runs is a controlled stop, not evidence that any arm underperforms.

