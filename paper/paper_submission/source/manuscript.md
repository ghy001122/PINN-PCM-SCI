# Training-time electrical elimination improves sparse electrothermal phase-change reconstruction beyond post-training electrical repair

Authors: [author names and affiliations to be supplied]

Corresponding author: [name and email to be supplied]

## Abstract

Electrical consistency at inference does not establish that a learned electrothermal state is accurate. We investigate whether enforcing a quasi-static electrical subproblem during training improves sparse reconstruction beyond applying the same electrical repair after training. A partially eliminated hybrid physics-informed neural network represents temperature and phase continuously, solves for potential on a shared finite-volume face network, differentiates the electrical solution implicitly, and deposits Joule heat through the corresponding half-cell resistances. The comparator retains a trainable potential and a finite electrical penalty while sharing the thermal and phase residuals. Both learned states receive an identical electrical solve for evaluation; a same-solver interpolant provides a strong non-neural baseline. In a synthetic, dimensionless two-dimensional wall cell, two clean initialization pairs under each of two complete pulse protocols show lower current and power errors with training-time elimination. Relative reductions are 48.8–78.3%, while absolute current errors are 0.682–1.572% and power errors are 0.673–1.593%. Under the earlier second pulse, raw phase RMS decreases by 20.22% and 20.31% relative to the projected soft models. A separate full-spatial-penalty control does not remove the development-stage advantage. However, the remaining thermal/phase residuals have not demonstrated an independent predictive benefit, and no learned state passes all strict two-cycle event requirements. The results support the specified coupling method over the tested finite-penalty alternatives under case-specific adaptation, without establishing isolated implicit-gradient causality, continuum accuracy, or material-calibrated device performance.

Keywords: physics-informed neural network; differentiable electrical solve; electrothermal coupling; phase-field reconstruction; Joule heating; pulse history

## 1. Introduction

In a coupled phase-change system, a small error in potential may produce a large error in a contact current or in local heating. Conversely, repairing the electrical field can make terminal currents internally consistent while leaving an inaccurate temperature or phase distribution unchanged. These distinctions matter when a neural reconstruction is assessed through device quantities rather than field images alone. Our question is whether the electrical constraint should participate in learning the evolving state, or whether a final electrical solve is sufficient.

We examine this question in an observation-driven reconstruction task. Sparse potential, temperature and phase samples, the geometry, the drive and all constitutive parameters are known. This is deliberately not a claim that a neural model is necessary to solve a fully specified forward problem: a conventional coupled solver can do so without interior observations. The task instead provides a controlled setting for comparing how alternative physics interfaces assimilate the same limited field information. The reference is a fixed numerical trajectory, not an experiment or a continuum solution.

Physics-informed neural networks combine data with differential-equation residuals [1]. Such losses do not automatically ensure that every field, constraint and functional quantity improves together. Gradient imbalance and network parameterization can substantially affect optimization [2]. Differentiable numerical components offer another way to impose selected constraints. Solver-in-the-Loop trains neural corrections through a differentiable simulator and emphasizes how learning interacts with its numerical trajectory [3]. Hybrid finite-element/neural models instead embed neural constitutive components in a PDE-constrained formulation [4]. Modular implicit differentiation supplies a general means of differentiating a solution defined by an optimality or root condition [5]. These precedents motivate the tools used here; neither implicit differentiation nor inserting a solver into learning is claimed as a new principle.

Our setting differs in three respects. First, only the quasi-static electrical variable is eliminated; the transient temperature and phase fields remain neural functions constrained by observations and explicit residuals. Second, the electrical operator and local Joule deposition share the same face resistances, so the heat source used during learning is consistent with the electrical discretization. Third, the comparison gives the soft electrical model the same final electrical solve. This last control separates a benefit from learning with the constraint from a benefit explained entirely by correcting potential at evaluation. A full-spatial-penalty counterfactual and two clean initialization pairs further delimit the interpretation.

Control-volume PINNs have previously constructed residuals from integrated conservation laws, including additional regularization for hyperbolic systems [6]. We use a spatial cell-balance thermal residual with automatic differentiation at shared faces; we do not inherit a space-time entropy-stability guarantee. The phase dynamics are of nonconserved phase-field type [7]. The wall-cell layout and electric–thermal–phase feedback are inspired by multiphysics phase-change-memory modeling [8], but the present coefficients are dimensionless design values. In particular, that application source concerns Ge-rich GST, not an oxide calibration. Our numerical model omits its multi-phase composition, material interfaces and field-dependent switching physics.

The contribution is therefore a defined coupling method and a controlled evidence sequence. We first distinguish fixed-state electrical repair from remaining differences after a common repair. We then examine whether the benefit persists under fresh initialization and a finite change in pulse history. Finally, we report the event and energy counterexamples that constrain the method's usefulness. The aim is a testable computational-method claim, rather than a collection of individually named optimization techniques.

## 2. Two-dimensional model and reconstruction task

### 2.1 Governing equations

The computational cell is Ω = [−1,1] × [0,1], with coordinates x and z and time 0 ≤ t ≤ 2.5. Potential V, reduced temperature T and phase fraction φ obey

$$\nabla\cdot(\sigma(T,\phi)\nabla V)=0. \qquad (1)$$

$$T_t+L\phi_t=\alpha\Delta T-\gamma T+Q\sigma(T,\phi)|\nabla V|^2. \qquad (2)$$

$$\phi_t=M(T)\left[\epsilon^2\Delta\phi-\partial_\phi W(\phi,T)\right]. \qquad (3)$$

The conductivity, mobility and local phase potential are

$$\sigma=\exp[\beta T+\log(R)\phi^2(3-2\phi)], \qquad (4)$$

$$M(T)=m_c+(m_h-m_c)\operatorname{sigmoid}[(T-T_c)/w_M], \qquad (5)$$

$$W=B\phi^2(1-\phi)^2+D(T_c-T)\phi^2(3-2\phi). \qquad (6)$$

We use α = 0.10, γ = 4, L = 0.05, Q = 4, β = 0.25, R = 8, ε = 0.04, B = 1, D = 6, T_c = 0.45, m_c = 0.5, m_h = 5 and w_M = 0.08. Mobility multiplies the entire phase bracket; it is not moved inside a divergence. Because W depends on the externally evolving temperature, the model is not assigned an autonomous monotone free-energy constraint.

The full top electrode is driven by U(t); a centered bottom segment |x| ≤ 0.35 is grounded. All remaining electrical faces are insulating. The top temperature is zero; the other thermal boundaries satisfy ∂ₙT + 0.25T = 0. Phase satisfies ∂ₙφ = 0 on every boundary. Initially T = 0 and

$$\phi_0=0.02+0.01\exp\left[-\frac{1}{2}\left((x/0.18)^2+((z-0.12)/0.10)^2\right)\right]. \qquad (7)$$

These assumptions define a synthetic wall-cell benchmark. No dimensional material parameters, experimental memory operation, or oxide-specific constitutive identification are inferred from it.

### 2.2 Complete pulse protocols and information boundary

Each pulse rises linearly from zero to 0.72 over its first 0.05 time units, holds until local time 0.27, then falls to zero at 0.35. The original protocol starts two pulses at 0 and 1.25. The intervention changes only the second start to 1.01, leaving the pulse shape, total time, coefficients and boundaries fixed. The input contains exactly two pulses; it is not periodically extended to create a third pulse. Advancing the second pulse by 0.24 preserves its phase relative to the 0.02 observation spacing.

Support trajectories use 80 × 40 cells, a main time step of 0.0025 and saving every two steps. The spatial and temporal masks take indices 0,4,8,… and the last index, fixed independently of field values. The resulting 21 × 11 × 126 mask contains 231 analytic initial positions and 28,875 positive-time positions, with 86,625 scalar field labels. Training receives only these samples, coordinates and known physical laws. Dense support fields, reference fields, reference currents or heating, and sealed stress cases do not enter training or model selection.

The evaluation reference uses 160 × 80 cells, a main time step of 0.000625 and saving every four steps, giving 1001 times. These discretizations serve different roles; their existence alone is not a convergence study. Each protocol has its own observations and is fitted separately. The intervention is consequently a complete-case adaptation experiment, not zero-shot transfer or a formal out-of-distribution test. The two seed values are reused across protocols for paired reporting, not counted as four independent physical cases.

## 3. Partially eliminated hybrid PINN

### 3.1 Neural states and electrical elimination

Let u_θ = (T_θ, φ_θ). Independent smooth modified-MLP heads [2] have width 64 and four hidden layers; the shared temperature architecture also includes a small additive latent adapter described in the Supplement. FP64 arithmetic and identical output mappings are used in both methods. With a(t) = 1 − exp(−t/0.35),

$$T_\theta=2.5a(t)(1-z)\operatorname{sigmoid}(h_T), \qquad (8)$$

$$\phi_\theta=\operatorname{sigmoid}[\operatorname{logit}(\phi_0)+8a(t)h_\phi]. \qquad (9)$$

The eliminated method, E, evaluates σ_θ from these states and solves the grounded electrical system

$$A(\sigma_\theta)v^*=f(U,\sigma_\theta). \qquad (10)$$

For an internal face e between cells i and j, the half-cell distances d and face area A_e define

$$R_{ei}=d_{ei}/(\sigma_i A_e),\quad R_{ej}=d_{ej}/(\sigma_j A_e),\quad g_e=(R_{ei}+R_{ej})^{-1}. \qquad (11)$$

Electrode faces use the corresponding half-cell resistance and the actual heater overlap. Insulating faces contribute no outward conductance. Positive conductivity and the grounded electrode yield a nonsingular discrete electrical problem. The implementation uses sparse factorization, not a dense inverse. For a scalar loss, the complete first-order derivative is obtained from

$$A^{\mathsf T}z=\partial\mathcal L/\partial v,\qquad d\mathcal L=d\mathcal L_{\rm direct}+z^{\mathsf T}(df-dA\,v^*). \qquad (12)$$

The direct term includes the explicit dependence of heating on conductivity. The right-hand side f also depends on electrode conductance, and its derivative is retained. A factorization may be reused for the adjoint of the same forward solve, but not after changing the state. This is an application of implicit differentiation [5], with no claim of a new differentiation theorem or support for arbitrary second-order derivatives.

### 3.2 Consistent local Joule deposition and remaining residuals

Given either the solved or neural potential, face current and deposition are

$$I_e=g_e(v_i-v_j),\qquad P_{e\to i}=I_e^2R_{ei},\qquad P_{e\to j}=I_e^2R_{ej}. \qquad (13)$$

Electrode power enters the neighboring boundary cell. For cell volume ω_i, q_i is its deposited power divided by ω_i. This allocation is not generally an equal split between adjacent cells. It gives

$$\sum_i\omega_iq_i=P_J, \qquad (14)$$

where P_J sums all internal and electrode dissipation. Equation (14) is an accounting identity for the shared face network, even when a neural potential violates electrical balance. Equality with terminal power UI additionally requires the electrical equations. Neither identity by itself establishes accuracy relative to the reference heating field.

The temperature residual uses a cell balance,

$$R_{T,i}=\partial_t(\bar T_i+L\bar\phi_i)+\gamma\bar T_i-\frac{\alpha}{\omega_i}\sum_f A_f(\nabla T_\theta)_f\cdot n_{if}-Qq_i. \qquad (15)$$

Cell means use midpoint quadrature. Temperature gradients are differentiated at shared face nodes with opposite normals for neighboring cells, including the model's own gradients on boundary faces. The same thermal boundary residual remains in both losses. The factor Q is applied once. The phase residual is

$$R_\phi=\phi_t-M(T)[\epsilon^2\Delta\phi-2B\phi(1-\phi)(1-2\phi)-6D(T_c-T)\phi(1-\phi)]. \qquad (16)$$

Thus the thermal interface is a spatial cell-balance residual and the phase interface is a pointwise AD residual. They are not claimed to equal the previous pointwise thermal formulation or the full space-time construction of [6]. At U = 0, E uses the analytic electrical solution v = q = 0 while thermal and phase evolution remain active.

### 3.3 Soft comparator and training objectives

The soft electrical PINN, F, trains all three field heads. Its potential is V_θ = U(t) exp(h_V)/[exp(h_V)+1−z], preserving the voltage range and the exact top value. It evaluates the same face operator and Joule deposition as E, but penalizes

$$r_{e,i}=(A(\sigma_\theta)V_\theta-f(U,\sigma_\theta))_i/\omega_i. \qquad (17)$$

No additional, differently averaged electric boundary loss is added: electrical boundary conductances already enter this residual. Let L_obs denote the common weighted observation loss, including the full initial-logit increment for phase, and let L_BC and L_IC be the common remaining boundary and initial losses. Their exact measures are specified in Supplement S2. With one calibration a,b at the shared parent and λ rising to 0.1,

$$J_{T\phi}=\frac{1}{3}\mathbb E_\rho[(R_T/4)^2+(R_\phi/5)^2], \qquad (18)$$

$$\mathcal L_E=L_{{\rm obs},E}/a+\lambda(5L_{\rm BC}+L_{\rm IC}+J_{T\phi,E})/b, \qquad (19)$$

$$\mathcal L_F=L_{{\rm obs},F}/a+\lambda(5L_{\rm BC}+L_{\rm IC}+J_{T\phi,F})/b+\frac{\lambda\eta}{3b}\mathbb E_\rho[r_e^2]. \qquad (20)$$

Here ρ is the uniform space-time target with the declared time-window quadrature. Scales a and b are shared within a pair and frozen, with a numerical floor of 10⁻¹². The primary F uses η = 1. A development control uses a one-time gradient-balanced η; a second control replaces the 128 sampled electrical cells by the volume mean over all 3200 cells at each physical time. The latter changes spatial integration, not the penalty by a factor of 25. Thermal and phase terms keep their original interfaces.

E freezes the unused potential head. Its voltage observations differentiate through conductivity and the solve, whereas F voltage observations act on its potential head. E enforces its constraint at powered observation and physics times; F penalizes it at physical residual times. Initial potential, active parameters, constraint strength and gradient maps consequently differ. These are explicit parts of the method-package comparison, not hidden evidence for an isolated VJP mechanism.

![Figure 1. Training and common inference interfaces.](figures/fig01-method.png)

Figure 1. Both methods use the same sparse observations and evolving-state architecture. Common inference freezes each learned T/phase state and solves the same electrical problem. The interpolant B_E also receives this solve. The schematic describes implemented interfaces, not a new experiment; implementation sources are mapped in Supplement S7.

## 4. Matched experiment and evaluation

### 4.1 Shared parents, fixed endpoints and strong controls

For each protocol, seeds 29 and 43 initialize fresh networks and a zero-output adapter, without loading trained weights, optimizer history or calibration. A common observation-only parent receives 2400 Adam updates [9] and 600 full-observation L-BFGS evaluations, 200 per field head [10]. E and F then start from that same fitted parent with fresh optimizers. Each branch receives 1500 Adam updates and at most 300 fixed complete-objective/gradient evaluations. Every line-search trial and repeated evaluation counts; budget termination restores the last accepted state. No reference score selects a checkpoint.

The learning rate, Adam parameters, clipping, observation stream, physical time windows and residual scales are shared. L-BFGS uses fixed data and quadrature, without resampling or gradient clipping inside its closure. Equal update and evaluation caps do not imply equal computation: E incurs sparse forward and adjoint solves, while F differentiates a potential network and its explicit residual. Actual work is retained in Supplement S6; no speedup is claimed.

B_E interpolates the same sparse temperature and full-logit phase information using fixed PCHIP and spatial interpolation rules, then solves the same electrical system. It is computed once per protocol and reused across seeds. Historical development controls include D_E, which omits the remaining thermal/phase interior residuals, and the balanced and full-spatial versions of F. They are reported separately, not pooled with clean repetitions. The primary soft recipe was locked before the clean confirmation rather than selected anew for each seed.

### 4.2 Common inference and distinct outcome measures

All final projected states use the same 160 × 80 electrical layer at the reference times. The unprojected F readout is retained separately. For a fixed F, projection changes V, q and electrical readouts while leaving T, φ and every phase event unchanged. The error measures distinguish these effects.

S is the space-time mean symmetric difference of active sets, where active means φ ≥ 0.5; it uses the full cell domain and global trapezoidal time weights. Raw E_φ is phase RMS on the ROI |x| ≤ 0.55, 0 ≤ z ≤ 0.55. E_T is ROI temperature RMS divided by 0.45, and E_V is unnormalized full-domain potential RMS. Device errors are

$$E_I=\frac{\|I-I_{\rm ref}\|_t}{\|I_{\rm ref}\|_t},\quad E_P=\frac{\|P_J-P_{J,{\rm ref}}\|_t}{\|P_{J,{\rm ref}}\|_t},\quad E_W=\frac{|\int(P_J-P_{J,{\rm ref}})dt|}{|\int P_{J,{\rm ref}}dt|}. \qquad (21)$$

The time norm is trapezoidal RMS over the complete interval. The matched device criterion uses bottom current; top and bottom currents agree to solve accuracy for projected states. Percentages below are 100 times normalized errors, not dimensional percentage errors in temperature or phase. All absolute, percentage-point and relative differences are provided in the unified tables.

Predeclared phase-reconstruction and device-function criteria require 10% improvements in their named primary metrics with 5% noninferiority guards and fixed absolute floors. They are retained in Supplement S3, rather than used as a substitute for reporting error magnitudes. Failure to cross an advantage threshold does not demonstrate equivalence. Strict event usability is separate: both cycles must meet onset error ≤ 0.005, recall ≥ 0.9, precision ≥ 0.8, mass ratio 0.8–1.2, and the specified peak, locality and recovery conditions. An onset is the linearly interpolated upward crossing of ROI active fraction 0.02. Support metrics integrate cell-volume overlap during each heating window.

For projected states, P_J = UI to electrical solve accuracy. Current and power errors thus differ in drive-dependent temporal weighting, but are not independent physical replications. Likewise, a small integrated energy error may reflect cancellation. We therefore retain the signed per-pulse errors, event metrics and local state errors even when global device criteria pass.

## 5. Results

### 5.1 Electrical repair is strong but does not explain the full method difference

The development comparison first demonstrates how misleading uncorrected electrical outputs can be (Figure 2). Holding the soft model's T and φ fixed, the final solve reduces F_raw current NRMSE from 279.30% to 1.071% and power NRMSE from 20.118% to 1.065%. The full-spatial soft model also improves substantially on projection, from 38.754% to 1.187% current error and from 6.611% to 1.190% power error. None of these changes is a phase-learning improvement: the phase field is unchanged.

After every state receives the common solve, E still has 0.694% current and 0.682% power error, lower than both soft models. Against projected F_raw, the absolute reductions are 0.377 and 0.383 percentage points, respectively. This remaining difference cannot be attributed entirely to withholding a final solver from the comparator. The values are nevertheless sub-percentage-point changes in a dimensionless numerical benchmark, not measured energy savings or yield gains in an experimental device.

![Figure 2. Same-state repair and the remaining common-projection difference.](figures/fig02-repair.png)

Figure 2. Panels a–b pair each fixed soft state before and after electrical re-solving; logarithmic vertical axes expose the large repair. Panel c compares projected endpoints, including E. T/phase and event metrics are unchanged within each repair pair. Source: the saved development-control table consolidated in Supplement S4; these states are not additional clean initialization repetitions.

### 5.2 Full spatial coverage does not remove the development signal

The full-grid electrical mean retains the same global scaling as the sampled mean. It tests whether sparse spatial enforcement alone explains the observed difference. In this development comparison, projected F_full remains worse than E in current and power, while its integrated energy error is better: 0.0362% versus 0.2188% (Figure 3). A single integrated quantity would therefore give a different ranking. The balanced penalty also does not outperform E on the functional metrics.

D_E is an important counterexample to a stronger interpretation. It obtains lower phase RMS than E, 0.01558 versus 0.01600, and nearby current/power errors of 0.724%/0.721%. A subsequent same-parent residual-strength study did not establish the frozen independent increment from the remaining thermal/phase PDE terms. The current hybrid PINN contains those residuals, but their necessity is not a supported contribution. The full-spatial experiment also leaves differences in enforcement times, finite versus exact constraints and initial V; it does not establish superiority to every sufficiently optimized soft formulation.

![Figure 3. Development counterfactuals and the strong no-interior-PDE control.](figures/fig03-controls.png)

Figure 3. All shown device outputs receive the common solve. D_E omits thermal/phase interior residuals; F_raw, F_bal and F_full retain them and vary the electric penalty. B_E is the same-solver interpolant. F_full integrates the electrical residual over all cells with a volume mean. Its favorable energy error and the strong D_E phase result delimit the claim. Sources and full metrics are in Supplement S4.

### 5.3 Clean pairs preserve device benefits under both protocols

Tables 1–2 and Figure 4 report the two protocols and two initialization values individually. B_E appears once per case. Under the original protocol, E reduces current error relative to projected F by 49.15% and 48.80%, and power error by 50.07% and 49.85%. Under the earlier second pulse, these reductions are 56.20%/77.20% for current and 57.21%/78.26% for power. The corresponding absolute new-protocol reductions are 1.276/2.310 percentage points in current and 1.336/2.422 points in power.

Table 1. State reconstruction at the fixed endpoints. S and potential RMS are displayed after multiplication by 1000; phase RMS is raw. Temperature error is normalized by 0.45 and expressed as a percentage. All values are relative to the fixed numerical reference, not continuum truth.

{{TABLE:state-results}}

Table 2. Device reconstruction after a common electrical solve. Errors are percentages. Each interpolant is one shared deterministic baseline, not a separate seed-level experiment.

{{TABLE:device-results}}

All four E/soft pairs pass the prescribed device-function criterion. Both earlier-pulse pairs also pass the phase-reconstruction and device criteria against B_E. On the original protocol, seed 43 does not cross the strong-interpolant advantage gate: its phase, current and power reductions are only about 9.05%, 9.05% and 9.31%. This failure remains relevant despite favorable directions. The historical seed 17 used a different development history and is not pooled into these confirmations.

Raw phase reductions against projected F are 16.45% and 11.69% for the original protocol, and 20.22% and 20.31% for the earlier pulse. The earlier-pulse seed-43 S reduction is 10.3711%, leaving an absolute margin of only 4.4453 × 10⁻⁶ beyond the 10% criterion. That individual threshold decision has a narrow margin under this reference; it is not evidence of robustness to reference discretization. No significance test is based on the number of grid cells or times, and two initializations do not establish a population success probability.

![Figure 4. Clean paired reconstruction and device effects.](figures/fig04-clean-pairs.png)

Figure 4. Each group is a separately fitted E/F pair; the two cases reuse initialization identifiers. Dashed B_E values are repeated visually for comparison but counted once per case. The fourth panel gives relative reductions, while panels a–c retain absolute error scales. Sources: unified results and paired-effects tables; no newly selected checkpoint or rerun is included.

### 5.4 Threshold recovery does not imply a reset of the continuous state

The fixed numerical references agree before the intervention to a maximum reported field difference of 7.22 × 10⁻¹⁵ at matching resolution. Immediately before the second pulse, however, the earlier protocol has a warmer and less relaxed state: ROI mean T changes from 0.006525 to 0.018746, and mean φ from 0.0004829 to 0.0039725. Maximum pre-pulse φ increases from 0.02056 to 0.19179, still below the active threshold. The threshold-based recovery fraction is therefore compatible with appreciable continuous-state memory.

The reference second-event latency decreases from 0.2484 to 0.2168, a shortening of 0.0316, or 12.72% of the original latency. A report-only calculation from the saved event table gives predicted shortenings 0.027942 and 0.030740 for E29/E43, 0.035000 and 0.015580 for F29/F43, and 0.025271 for B_E. The corresponding absolute shortening errors are 0.003658, 0.000860, 0.003400, 0.016020 and 0.006329. F29 is slightly better than E29 on this difference, even though its device trajectories are worse.

Figure 5 connects residual states, timing changes and electrical response. The intervention supports a pulse-history effect within this model; it does not isolate thermal from phase-memory mediation. Each neural function is fitted offline using observations over its complete trajectory. Different neural predictions over the physically identical prefix therefore reflect separate reconstruction errors, not a violation of the generator's causal evolution.

![Figure 5. Continuous-state memory, event shift and signed power error.](figures/fig05-history.png)

Figure 5. Panels a–b show reference ROI means before the respective second pulses; panel c uses only saved event times and is report-only. Panels d–f show the earlier-pulse case for seed 43, including signed errors and their pulse integrals. The energy diamond is the sum, not the sum of absolute errors. Sources: saved reference-history, complete-events, per-pulse tables and power traces. No state or trajectory was generated for this figure.

### 5.5 Event and energy counterexamples remain consequential

Under the earlier pulse, E has first/second onset errors 0.003333/0.002775 for seed 29 and 0.003490/0.004440 for seed 43. All are below 0.005. First-cycle recalls remain 0.866607 and 0.875507, below 0.9, so neither model achieves strict two-cycle usability. F29 has a smaller second-cycle timing error, 0.0008375, than E29. E also has larger tail-phase RMS in both earlier-pulse pairs; seed 43 has a slightly larger second-cycle temperature error. Figure 6 displays these adverse outcomes together with the original-protocol event failures.

Energy integration introduces another non-equivalence. Earlier-pulse F43 has opposite signed pulse-energy errors, +0.00511674 and −0.00400099. Their cancellation gives only 0.25736% total energy error despite 3.09469% power-trajectory NRMSE. E43 also exhibits cancellation, so the phenomenon is not unique to the soft model. On the original protocol, F29 has a smaller energy error than E29 even though both current and power trajectories favor E. These observations justify retaining trajectory and signed per-pulse measures rather than interpreting integrated energy as a sufficient device score.

![Figure 6. Events and unfavorable outcomes.](figures/fig06-limits.png)

Figure 6. Dashed lines indicate the inherited recall and timing criteria, not revised thresholds. Tail errors refer to the earlier-pulse case after the second recovery cycle. The integrated-energy ranking reverses in the original seed-29 pair. All eight learned endpoints fail at least one strict event requirement. Complete precision, mass, peak, locality and recovery values accompany the event table in Supplement S5.

## 6. Discussion

The most direct interpretation is that how the electrical constraint participates in training affects the learned evolving state, even when electrical repair is available to every method at inference. The repair controls show that much of an unprojected soft model's apparent device error can disappear without changing phase. The residual advantage after common projection, its persistence against a full-spatial penalty in development, and the clean paired results together support the specified training package. They do not establish that an isolated implicit gradient, rather than differences in parameterization, enforcement times or optimization, is the unique cause.

This evidence is stronger than comparison with an uncorrected weak baseline, but narrower than a general claim that exact elimination always dominates soft penalties. Only a finite set of penalty recipes and a fixed optimization budget were tested. D_E also limits the role assigned to the remaining interior residuals. A coupled PINN can have an evidenced algorithmic advantage without every retained term having a demonstrated independent increment; the latter claim is explicitly withheld here.

The application scope is equally specific. Two-dimensional feedback, localized electrodes and pulse-dependent residual states make this a device-inspired computational test rather than an abstract one-variable example. They do not make it a calibrated oxide or chalcogenide memory model. A material-facing claim would require an internally consistent material model, parameter provenance and independent physical validation. Those are absent and are not supplied by citing a more detailed device study.

The measurements also have numerical limits. All formal comparisons use the fixed reference discretization and previously fixed selection rules. Shared conservation and dissipation identities express consistency of the numerical operator, not independent accuracy evidence. The narrow S margin and threshold-sensitive events especially should not be promoted to continuum claims. A bounded future sensitivity check could retain every learned state and compare both protocols with a temporally refined reference; no such result is included here. The present paper remains complete as a fixed-reference method study.

## 7. Conclusions

A partially eliminated hybrid PINN couples neural temperature and phase fields to an implicit quasi-static electrical layer and a consistent local Joule source. Under two complete pulse protocols and two clean initialization pairs, training-time elimination improves current and power reconstruction beyond a common post-training electrical solve. The comparison includes a same-solver interpolant and development counterfactuals that limit explanations based solely on readout repair or electrical spatial sampling. Continuous residual states also distinguish threshold recovery from complete relaxation. The supported benefit is conditional on the stated numerical task and training recipe: strict event reliability, independent necessity of the remaining PDE terms, isolated implicit-gradient causality and material-calibrated performance remain unestablished.

## Data, code and declarations

The versioned research evidence is available in the [PINN-PCM-SCI repository](https://github.com/ghy001122/PINN-PCM-SCI/tree/ea29be9a9d33497b075873bcdc7673df43db7221), including source, configurations, checkpoints, curated result tables and selected traces. The present manuscript package adds only local writing, saved-result arithmetic and figure generation; it has not been published automatically. Full dense reference and prediction arrays are retained locally and are not all included in the public curated package. Supplement S7 identifies the files needed to rebuild these manuscript figures without executing a scientific model and the separate scope of a full numerical reproduction. Complete dataset archival remains a submission preparation item.

Funding: [to be supplied by the authors]. Author contributions: [to be supplied by the authors]. Competing interests: [author declaration required]. No experimental or personal-subject data were collected for this numerical study.

## References

{{REFERENCES}}
