# Supplementary material

## Training-time electrical elimination improves sparse electrothermal phase-change reconstruction beyond post-training electrical repair

This supplement consolidates implementation details, counterfactuals, complete event outcomes, reproducibility and evidence limits. It accompanies a fixed-reference numerical method study. O denotes the original protocol; S denotes the earlier second-pulse protocol. E is the eliminated method, F is the locked soft electrical PINN, and B_E is the shared same-solver interpolant. Unless marked network, electrical outputs are evaluated after the common solve. The historical development states are never pooled with clean initializations 29 and 43.

## S1. Numerical object and data construction

The main text states every physical coefficient and boundary condition. All quantities are dimensionless. Geometry and the electrothermal phase-feedback motif were inspired by wall-cell modeling; the current single scalar phase, smooth conductivity law and numerical coefficients do not reproduce the multi-material, compositional or switching model of reference [8]. The model is not calibrated to an oxide device, and the physical association cannot be strengthened merely by adding material citations.

The base numerical contract is `configs/phk_v2/object_numerical_contract.json`; its later object overlay is `configs/phk_v21/object_numerical_contract.json`. These files are not interchangeable: the overlay changes coefficients and the original time/pulse specification. The final two-pulse intervention is defined by `configs/phk_v23/lf11_protocol_sprint.json` and the case specification in `paper/paper_v32/evidence/case-and-budget.json`. Reproduction must apply the overlay and explicit finite pulse starts, not infer a periodic third pulse from a legacy period field.

The initial phase is analytic. The support mask is fixed before observing the new case's fields: each axis selects indices 0,4,8,… and the last index without duplicate endpoints. Spatial cell-center coordinates therefore need not lie on physical boundaries. The support trajectory has 80 × 40 cells; the fixed-reference trajectory has 160 × 80. Support output is sampled every 0.005 time units before the sparse time mask, giving sparse spacing 0.02 with the terminal point included. Reference output spacing is 0.0025. The final observation mask is 21 × 11 × 126, including 231 analytic initial positions and 28,875 positive-time locations. All three fields are observed at those locations. This is sparse relative to the full space-time trajectory, not evidence for an experimentally minimal sensor arrangement.

Support and reference trajectories use the inherited coupled block and logit-Newton numerical algorithms without output clipping or case replacement. The new support/reference generation required 1000/4000 main steps. Internal linear solves totaled 14,476/46,027, respectively. These are different counters and are not represented as 5000 identical-cost solves. Generator summaries reside under `paper/paper_v32/evidence/reference-generation/`. Matching-resolution prefixes before the intervention agree to roundoff, with maximum recorded field difference 7.22 × 10⁻¹⁵. This checks the finite-pulse implementation; it does not prove continuum convergence.

## S2. Exact learning interfaces

### S2.1 Architecture and admissible outputs

Each field starts with an independent 64-wide, four-hidden-layer modified MLP using smooth tanh transformations. The gated combination of two input feature projections follows the architectural construction in Wang et al. [2]; the project implements its own modules and does not claim that architecture as original. E freezes the potential head; F jointly trains it with the temperature, phase and adapter parameters.

The temperature adapter adds to the temperature latent a 32-wide, two-hidden-layer modified MLP with 21 inputs: three normalized coordinates and sine/cosine pairs at nine fixed frequency vectors. The vectors are (0.5,0,0), (1,0,0), (2,0,0), (0,0.5,0), (0,1,0), (0,0,0.5), (0,0,1), (0,0,2), (0,0,4); angles are 2π times the coordinate-frequency product. Its output weights and bias are zero at initialization. The adapter is present in every clean parent and both branches. There is no matched ablation establishing an independent adapter contribution.

Coordinates are normalized by the inherited physical-domain mapping. Main equations (8)-(9) preserve the analytic initial temperature and phase, phase bounds and top thermal value. The temperature upper envelope is a representation constraint, not an experimental temperature limit. The soft potential transform preserves 0 ≤ V ≤ U and the top electrode exactly, but does not hard-enforce the grounded heater. Known electric boundary values enter its finite-volume residual. No extra potential fitting gate is imposed on the clean parents.

### S2.2 Observation measure and logit target

Let p_i be normalized sparse spatial dual-volume times trapezoidal-time weights. Potential and temperature use this global measure, not an uncorrected interface-oversampled mean. The phase target is the complete initial-logit increment

$$d_i=\operatorname{logit}(\phi_i^{\rm obs})-\operatorname{logit}(\phi_0(x_i,z_i)). \qquad (S1)$$

Logits use ε_logit = 10⁻⁸ for numerical clipping of their input only. The model increment is δ_θ = 8a(t)h_φ and is not divided by startup a(t). With d_scale = 36.84136146790473,

$$L_{\rm obs}=(L_V+L_T+L_\phi)/3, \qquad (S2a)$$

$$L_V=\sum_i p_i((V_i-V_i^{\rm obs})/0.72)^2,\qquad L_T=\sum_i p_i((T_i-T_i^{\rm obs})/0.45)^2, \quad (S2b)$$

$$L_\phi=\sum_i p_i^\phi((\delta_i-d_i)/d_{\rm scale})^2. \qquad (S2c)$$

The phase measure averages two normalized measures with equal weight: the positive-time global measure and endpoints of visible space-time cells whose corner phase values straddle 0.5. Duplicate vertices accumulate their proper weights. If there are no such endpoints, it falls back to the global phase measure. This uses only observed values. No dense interface pool, teacher derivative, reference event ranking or reference current is supplied. Initial analytic data are counted separately and shared by all methods.

Adam samples four observation times from the half-global/half-phase temporal marginal proposal and applies its inverse-probability correction, including all visible spatial points at a sampled time. Fixed full-objective L-BFGS evaluates all observation groups with their original weights. The observations are already used for fitting and development; later subdivision of them would not constitute unseen validation.

### S2.3 Cell operators, boundaries and scales

Training uses the common 80 × 40 electrical grid, harmonic face conductances, half-cell electrode resistances and fractional heater overlap. The same forward factorization is reused only for its associated adjoint. The first-order VJP includes the dependence of both A and f on conductivity, as well as direct Joule derivatives. No thermal or phase trajectory is solved inside the network. CPU sparse factorization may be connected to GPU field evaluation without detaching the physical gradient.

The numerical source obeys the half-resistance deposition formula in the main text. In particular, an interface with unequal resistances deposits unequal shares. Electric face dissipation includes electrode contributions. A grounded, balanced electrical solution gives total deposited power equal to terminal input. For an arbitrary soft potential, total deposition still equals the face dissipation sum, but terminal equality need not hold. These statements are algebraic identities or electrical balance conditions, not separate learned-accuracy tests.

For each physical time, sampled cells obtain midpoint T and φ, their time derivatives, shared-face AD temperature gradients and the original phase Laplacian. Boundary gradients use the network's own values. With b_T = T on the top and b_T = ∂ₙT + 0.25T elsewhere,

$$L_{\rm BC}=\frac{1}{13}\sum_{s\in\{l,r,b,t\}}\left[\operatorname{mean}_s(b_T^2)+\operatorname{mean}_s((\partial_n\phi)^2)\right]. \quad (S3)$$

$$L_{\rm IC}=\frac{1}{3}\left[\operatorname{mean}(T_0^2)+\operatorname{mean}(((\phi-\phi_0)/0.03)^2)\right]. \quad (S4)$$

The historical denominators 13 and 3 are retained. Five omitted electric boundary subterms contribute zero; deleting them from the denominator would change the other terms' weights. All paired branches use the same definition. The electric, thermal and phase residual scales are 1, 4 and 5. The thermal/phase average retains divisor 3 despite containing two terms. No dynamic reweighting, autonomous energy-decay regularizer or adaptive rescue is introduced.

At the common fitted parent, a = L_obs,E is computed using the eliminated potential, and b = J_Tφ,E + 5L_BC + L_IC uses a fixed calibration pool. Both are floored at 10⁻¹² and shared within that pair. They are not recomputed separately for F. Thus a can differ from the full observation loss measured with the parent's original voltage head. Actual clean-parent fitting errors and scales are shown below; these are visible-data errors, not validation errors.

Table S1. Clean parent quality and shared calibration. O/S identify protocols; a and b are the actual eliminated-parent scales.

| Case | Seed | Visible V / 0.72 (%) | Visible T / 0.45 (%) | a | b |
| --- | --- | --- | --- | --- | --- |
| O | 29 | 0.719889197 | 0.880380601 | 8.87621934e-05 | 0.467422111 |
| O | 43 | 1.06900324 | 0.877331139 | 0.000109200158 | 0.609241029 |
| S | 29 | 0.876705703 | 0.991722822 | 9.04666501e-05 | 0.427835437 |
| S | 43 | 1.34065664 | 0.979305193 | 8.73396772e-05 | 0.522223303 |

### S2.4 Sampling, optimization and comparator selection

The original physical windows are [0,0.35], [0.35,1.25], [1.25,1.60], [1.60,2.5], with target masses 0.14, 0.36, 0.14, 0.36. The earlier-pulse windows are [0,0.35], [0.35,1.01], [1.01,1.36], [1.36,2.5], with masses 0.14, 0.264, 0.14, 0.456. The masses sum to one and correspond to duration divided by 2.5. Adam takes one physical time per window and 128 sampled cells. Fixed calibration, L-BFGS and independent audit pools each have eight times per window, with separate seeds. The fixed L-BFGS target retains the same 128-cell spatial sampling; the F_full control alone replaces its electrical mean by the full 3200-cell volume mean. It retains the original random draws for the other terms.

Clean parents use 2400 Adam updates and 600 complete evaluations, split into 200 per field head. Branches use learning rate 10⁻⁴, Adam β₁/β₂ = 0.9/0.999, ε = 10⁻⁸ and gradient clipping at 10 during Adam. The weight schedule is λ(k) = 0.1 min(k/200,1). Each branch has 1500 updates followed by 300 complete L-BFGS evaluations. L-BFGS uses learning rate 1, history 50, strong-Wolfe search, gradient tolerance 10⁻¹⁰ and change tolerance 10⁻¹⁴. All trial/repeated closures count. Interrupting a line search restores the last accepted parameters and optimizer state. The closure sees a fixed complete target and uses the true gradient without clipping.

In the historical F_bal control, η is frozen from one parent gradient comparison: the root-sum-square norms of weighted observation, BC/IC, thermal and phase blocks divided by the electric block norm. All F parameters participate. This is a finite strengthening of the comparator, not a proposed adaptive algorithm. F_raw with η = 1 was locked for clean confirmation after the development controls; it is not claimed to be the globally optimal soft PINN. Seed 17 development states use a different training history and are not pooled with the fresh seeds.

### S2.5 Same-solver interpolation

B_E obtains T and phase from the existing B_logit rule: temporal PCHIP at visible spatial nodes; linear interpolation in space; phase interpolation in the full initial-logit increment, followed by restoring analytic φ₀ and applying the sigmoid. Known analytic initial conditions are restored exactly. Boundary extensions use nearest visible values, the analytic top temperature and the inherited Robin extrapolation. They are not new field observations. The interpolated V is discarded: the common electrical solve computes V and q from the interpolated T and φ. Earlier waveform/contact changes concerned only the discarded V interpolant and do not alter B_E. No teacher current, derivative or fine-grid field enters this baseline.

## S3. Metrics, frozen decisions and claim levels

All time integrals use global trapezoidal weights. Spatial means use cell volumes; uniform Cartesian cell volumes give the implemented cell mean. Raw phase RMS and normalized temperature RMS use the ROI; S and potential RMS use the full domain. Current and power NRMSE divide the time RMS error by the time RMS of the reference, with a 10⁻¹² denominator floor. Integrated energy error divides the absolute signed integral error by absolute reference energy. The mean local q error, when reported, is normalized by the full-domain space-time RMS of reference q. Numerical balance residuals are not interchangeable with that q error.

For candidate c and comparator b, the retained reconstruction advantage A requires b−c ≥ max(0.1b,τ) for both S and raw E_φ. Its noninferiority checks require c ≤ b + max(0.05b,τ) for E_T, E_I and E_V. Device advantage B requires the same gain rule for bottom-current and power NRMSE, with noninferiority for S, E_φ, E_T, E_V and top-current E_I. Absolute tolerances are 10⁻⁸ for S, 10⁻⁶ for E_φ/E_T/E_I and 10⁻⁷ for E_V; the extra device-normalized tolerance is 10⁻⁶. These rules define practical matched increments, not significance or equivalence tests. S/phase guards in the device rule and temperature/current/potential guards in the reconstruction rule are preserved without post hoc relaxation.

The original clean A/B outcomes are: seed 29 E versus projected F, pass/pass; seed 43, fail/pass (S gain insufficient). Against B_E, seed 29 passes both and seed 43 fails both (phase gain and current/power gains insufficient). The earlier-pulse E states pass both rules against both controls. Reverse comparisons are retained in the original adjudication CSVs. The earlier seed-43 S margin is 0.9 × 0.001197734375 − 0.001073515625 = 0.0000044453125. No reference-perturbation conclusion follows from its positive sign.

The strict endpoint criteria additionally require legal fields; maximum phase ≥ 0.9; a detected onset in each cycle; cycle peak ROI active fraction ≥ 0.02; peak full-domain/outside-ROI fractions ≤ 0.45/0.10; and recovery ≥ 0.70, defined as (peak fraction − end fraction)/(peak fraction − pre-cycle fraction). Both cycles must satisfy recall ≥ 0.9, precision ≥ 0.8, mass ratio between 0.8 and 1.2, and onset error ≤ 0.005. The original cycles end at 1.25 and 2.5. The earlier cycles end at 1.01 and 2.02; the tail to 2.5 is not silently added to second-cycle recovery. Support overlap integrates the two heating windows using the original global time weights restricted to each window.

There are two physical protocols, two initialization values and four paired comparisons. Grid points, saved times, multiple output metrics and reused B_E values are not independent experimental replicates. We report each effect without confidence intervals or claims of population success probability. Threshold failure is not a proof of zero effect; a favorable direction is not automatically a frozen advantage.

## S4. Necessary development counterfactuals

Table S2 retains electrical repair, the strong D_E control and the full-spatial/gradient-balanced soft alternatives. “Network” means the model's unsolved V; “projected” applies the common solve without changing T or phase. Device current in this consolidated table is the bottom-current error; using top current for an electrically unbalanced model would produce a different result. All entries are development states with a common historical parent, not extra clean seeds.

| Method | S | Phase RMS | Current (%) | Power (%) | Energy (%) |
| --- | --- | --- | --- | --- | --- |
| E0 | 0.00112851563 | 0.0234146837 | 2.55490439 | 2.64146359 | 1.23561814 |
| D_E | 0.00078703125 | 0.0155821211 | 0.724256918 | 0.721322841 | 0.288198505 |
| P_E | 0.0008190625 | 0.0159996773 | 0.693818679 | 0.681730628 | 0.218830694 |
| B_E | 0.0014084375 | 0.0237697822 | 1.72822894 | 1.7562293 | 1.184941 |
| F_raw/network | 0.000858203125 | 0.0166913896 | 279.3 | 20.1181324 | 19.2658977 |
| F_raw/projected | 0.000858203125 | 0.0166913896 | 1.07111197 | 1.06512066 | 0.249371223 |
| F_full/network | 0.000905078125 | 0.0172242878 | 38.7535687 | 6.61059161 | 6.51455473 |
| F_full/projected | 0.000905078125 | 0.0172242878 | 1.18664464 | 1.19018446 | 0.03617151 |
| F_bal/projected | 0.000862890625 | 0.0171664543 | 1.60777035 | 1.65053011 | 0.677478353 |

The earlier fixed-state D_I-to-E0 replacement held T/phase and conductivity fixed and repaired severe electrical readout errors; its underlying record is in `paper/paper_v28/evidence/evaluation/results.json` together with the V27 comparator evidence. The main figures instead use directly paired F network/projected readouts, which more directly establish the relevant post-training-repair counterfactual. These are compatible but distinct controls. Potential volume accuracy alone is not a certificate for electrode flux accuracy.

Table S3 retains the subsequent remaining-PDE-strength counterfactual. D_C continues the control objective; P1 adds the original remaining PDE term; P_kappa adds it with κ = 92.84049, fixed from a complete-gradient norm ratio of 0.1077% at the shared parent. The original gradient calculation included the T/phase → conductivity → potential → heating chain. The scalar strengthened a measurable optimization effect, but did not establish the required predictive increment. Each state used 223 complete evaluations, with zero new Adam updates in that campaign; it is not comparable to a fresh 1500-update branch as an additional initialization.

| Method | S | Phase RMS | Current (%) | Power (%) | Local q NRMSE (%) |
| --- | --- | --- | --- | --- | --- |
| D_C | 0.000781953125 | 0.0143587127 | 0.725526014 | 0.719509624 | 3.99023375 |
| P1 | 0.0007725 | 0.0142650985 | 0.729715416 | 0.725088576 | 3.95942824 |
| P_kappa | 0.00077140625 | 0.014253669 | 0.761998387 | 0.760610227 | 4.04053167 |

P1 and P_kappa improve raw phase error over D_C by approximately 0.65% and 0.73%, respectively. The stronger remaining-PDE term reduces the thermal-dominated residual but pays a current/power cost. Its second-cycle timing remains above 0.005. These controls prevent the manuscript from attributing the main advantage to an independently demonstrated necessity of the remaining residuals. They do not establish universal uselessness of thermal or phase physics, nor do they justify changing an old failed decision.

The full-grid soft control tests spatial integration/coverage at the existing physical times. It does not equalize the temporal constraint set with E, remove the finite penalty, equalize initial V, or isolate an adjoint pathway. No additional stop-gradient, hard-lift or voltage-pretraining control is implied by the present evidence. The claim is restricted to the implemented method package and tested comparators.

## S5. Complete event and pulse-history evidence

The following three tables partition the complete saved event record into readable groups without selecting favorable cycles. They include the shared baseline once per case. F denotes F/projected; phase events are identical for its network and projected readouts. Reference first-onset time is 0.2406 in both cases. Reference second onsets are 1.4984 (O) and 1.2268 (S). All listed phases exhibit the two onsets; no case was replaced after observing its event status.

Table S4. Timing and support quality for every method/cycle. Neither timing nor recall replaces the other in strict usability.

| Case | Seed | Method | Cycle | Onset | Onset error | Recall | Precision | Mass ratio |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| O | 29 | E | 1 | 0.234533333 | 0.00606666667 | 0.883731411 | 0.922172584 | 0.958314556 |
| O | 29 | E | 2 | 1.49196667 | 0.00643333333 | 0.983316733 | 0.892530229 | 1.10171813 |
| O | 29 | F | 1 | 0.2312 | 0.0094 | 0.838778729 | 0.908924429 | 0.922825597 |
| O | 29 | F | 2 | 1.5026375 | 0.0042375 | 0.90562749 | 0.909591097 | 0.99564243 |
| O | -- | B_E | 1 | 0.255871429 | 0.0152714286 | 0.792924741 | 0.98792813 | 0.80261379 |
| O | -- | B_E | 2 | 1.51337143 | 0.0149714286 | 0.772161355 | 0.993432645 | 0.777265936 |
| S | 29 | E | 1 | 0.237266667 | 0.00333333333 | 0.86660658 | 0.96403058 | 0.898940964 |
| S | 29 | E | 2 | 1.224025 | 0.002775 | 0.966148059 | 0.890341894 | 1.08514276 |
| S | 29 | F | 1 | 0.223933333 | 0.0166666667 | 0.833370888 | 0.859117305 | 0.970031546 |
| S | 29 | F | 2 | 1.2276375 | 0.0008375 | 0.959394768 | 0.883144476 | 1.08633955 |
| S | -- | B_E | 1 | 0.255871429 | 0.0152714286 | 0.792924741 | 0.98792813 | 0.80261379 |
| S | -- | B_E | 2 | 1.2481 | 0.0213 | 0.774320397 | 0.995603429 | 0.777739785 |
| O | 43 | E | 1 | 0.22922 | 0.01138 | 0.802726453 | 0.887629251 | 0.904348806 |
| O | 43 | E | 2 | 1.4931 | 0.0053 | 0.984063745 | 0.883128492 | 1.11429283 |
| O | 43 | F | 1 | 0.201525 | 0.039075 | 0.840581343 | 0.762182041 | 1.10286165 |
| O | 43 | F | 2 | 1.5048 | 0.0064 | 0.890189243 | 0.926285788 | 0.961030876 |
| S | 43 | E | 1 | 0.23711 | 0.00349 | 0.875506985 | 0.947105424 | 0.924402884 |
| S | 43 | E | 2 | 1.22236 | 0.00444 | 0.964951274 | 0.895304569 | 1.07779108 |
| S | 43 | F | 1 | 0.210366667 | 0.0302333333 | 0.873704371 | 0.806133056 | 1.08382154 |
| S | 43 | F | 2 | 1.24922 | 0.02242 | 0.813728843 | 0.952852853 | 0.853992135 |

Table S5. Threshold fractions and recovery. A recovery fraction of one means no remaining above-threshold active fraction, not φ = 0 or T = 0.

| Case | Seed | Method | Cycle | Pre ROI | Peak ROI | Peak full | Peak outside | Recovery |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| O | 29 | E | 1 | 0 | 0.069731405 | 0.02109375 | 0 | 1 |
| O | 29 | E | 2 | 0 | 0.0676652893 | 0.02046875 | 0 | 1 |
| O | 29 | F | 1 | 0 | 0.0661157025 | 0.02 | 0 | 1 |
| O | 29 | F | 2 | 0 | 0.0674070248 | 0.020390625 | 0 | 1 |
| O | -- | B_E | 1 | 0 | 0.0596590909 | 0.018046875 | 0 | 1 |
| O | -- | B_E | 2 | 0 | 0.0537190083 | 0.01625 | 0 | 1 |
| S | 29 | E | 1 | 0 | 0.0671487603 | 0.0203125 | 0 | 1 |
| S | 29 | E | 2 | 0 | 0.0779958678 | 0.02359375 | 0 | 1 |
| S | 29 | F | 1 | 0 | 0.0609504132 | 0.0184375 | 0 | 1 |
| S | 29 | F | 2 | 0 | 0.0800619835 | 0.02421875 | 0 | 1 |
| S | -- | B_E | 1 | 0 | 0.0596590909 | 0.018046875 | 0 | 1 |
| S | -- | B_E | 2 | 0 | 0.0643078512 | 0.019453125 | 0 | 1 |
| O | 43 | E | 1 | 0 | 0.0612086777 | 0.018515625 | 0 | 1 |
| O | 43 | E | 2 | 0 | 0.0707644628 | 0.02140625 | 0 | 1 |
| O | 43 | F | 1 | 0 | 0.0578512397 | 0.0175 | 0 | 1 |
| O | 43 | F | 2 | 0 | 0.069214876 | 0.0209375 | 0 | 1 |
| S | 43 | E | 1 | 0 | 0.0699896694 | 0.021171875 | 0 | 1 |
| S | 43 | E | 2 | 0 | 0.0790289256 | 0.02390625 | 0 | 1 |
| S | 43 | F | 1 | 0 | 0.0632747934 | 0.019140625 | 0 | 1 |
| S | 43 | F | 2 | 0 | 0.0777376033 | 0.023515625 | 0 | 1 |

Table S6. Integrated support masses. These are space-time measures, not independent sample counts. Recall is overlap/reference mass; precision is overlap/predicted mass.

| Case | Seed | Method | Cycle | Reference mass | Predicted mass | Overlap mass |
| --- | --- | --- | --- | --- | --- | --- |
| O | 29 | E | 1 | 0.0006934375 | 0.00066453125 | 0.0006128125 |
| O | 29 | E | 2 | 0.0006275 | 0.000691328125 | 0.00061703125 |
| O | 29 | F | 1 | 0.0006934375 | 0.000639921875 | 0.000581640625 |
| O | 29 | F | 2 | 0.0006275 | 0.000624765625 | 0.00056828125 |
| O | -- | B_E | 1 | 0.0006934375 | 0.0005565625 | 0.00054984375 |
| O | -- | B_E | 2 | 0.0006275 | 0.000487734375 | 0.00048453125 |
| S | 29 | E | 1 | 0.0006934375 | 0.000623359375 | 0.0006009375 |
| S | 29 | E | 2 | 0.00091390625 | 0.00099171875 | 0.00088296875 |
| S | 29 | F | 1 | 0.0006934375 | 0.00067265625 | 0.000577890625 |
| S | 29 | F | 2 | 0.00091390625 | 0.0009928125 | 0.000876796875 |
| S | -- | B_E | 1 | 0.0006934375 | 0.0005565625 | 0.00054984375 |
| S | -- | B_E | 2 | 0.00091390625 | 0.00071078125 | 0.00070765625 |
| O | 43 | E | 1 | 0.0006934375 | 0.000627109375 | 0.000556640625 |
| O | 43 | E | 2 | 0.0006275 | 0.00069921875 | 0.0006175 |
| O | 43 | F | 1 | 0.0006934375 | 0.000764765625 | 0.000582890625 |
| O | 43 | F | 2 | 0.0006275 | 0.000603046875 | 0.00055859375 |
| S | 43 | E | 1 | 0.0006934375 | 0.000641015625 | 0.000607109375 |
| S | 43 | E | 2 | 0.00091390625 | 0.000985 | 0.000881875 |
| S | 43 | F | 1 | 0.0006934375 | 0.0007515625 | 0.000605859375 |
| S | 43 | F | 2 | 0.00091390625 | 0.00078046875 | 0.000743671875 |

No learned endpoint passes all strict criteria. In particular, the earlier-pulse E timing criteria pass but its first-cycle recall values are 0.866607 and 0.875507. On the original case, seed 43 E first-cycle recall is lower than F. Earlier-pulse F29 has better second-cycle timing and a slightly better prediction of the cross-protocol latency change. E has greater tail-phase RMS in both new pairs, and slightly worse second-cycle temperature error in seed 43. Complete later-window state and device values remain in `tables/second-cycle.csv`.

Table S7. Reference state immediately before each second pulse. Maxima and means use the specified ROI.

| State | Original mean | Earlier mean | Original maximum | Earlier maximum |
| --- | --- | --- | --- | --- |
| temperature | 0.00652461267 | 0.0187461243 | 0.00789871133 | 0.0229086059 |
| phase | 0.000482908856 | 0.00397246303 | 0.0205550094 | 0.191788374 |

Table S8. Report-only second-onset latency change, calculated from saved event times. The reference shortening is 0.0316. This analysis introduces no training, selection rule or additional pass criterion.

| Seed | Method | Original latency | Earlier latency | Shortening | Absolute shift error |
| --- | --- | --- | --- | --- | --- |
| 29 | E | 0.241966667 | 0.214025 | 0.0279416667 | 0.00365833333 |
| 29 | F | 0.2526375 | 0.2176375 | 0.035 | 0.0034 |
| 43 | E | 0.2431 | 0.21236 | 0.03074 | 0.00086 |
| 43 | F | 0.2548 | 0.23922 | 0.01558 | 0.01602 |
| baseline | B_E | 0.263371429 | 0.2381 | 0.0252714286 | 0.00632857143 |

The state differences and the generator prefix agreement support a history-dependent response within the numerical equations. They do not separate thermal and phase mediation, and separately trained offline predictors need not coincide on the shared physical prefix. B_E is one deterministic reconstruction per case, even where it is displayed beside both seeds.

Table S9. Per-pulse power and energy for the earlier-pulse case. Absolute signed integral and integral of absolute power error are distinct; the latter cannot cancel in time. Units are dimensionless, except the normalized percentage column.

| Role | Cycle | Power error (%) | Signed energy error | Abs. signed integral | Integral abs. power error |
| --- | --- | --- | --- | --- | --- |
| B_E | 1 | 1.71615019 | -0.00250732788 | 0.00250732788 | 0.0025077821 |
| B_E | 2 | 2.32253005 | -0.00402130047 | 0.00402130047 | 0.00402130047 |
| 29/E/projected | 1 | 1.30413581 | 0.00133420155 | 0.00133420155 | 0.00207001575 |
| 29/E/projected | 2 | 0.573139599 | -8.73294418e-05 | 8.73294418e-05 | 0.00090832181 |
| 29/F_raw/projected | 1 | 3.00312494 | 0.00418795806 | 0.00418795806 | 0.00489585308 |
| 29/F_raw/projected | 2 | 1.43205227 | -0.00112450252 | 0.00112450252 | 0.00231461441 |
| 43/E/projected | 1 | 0.886860848 | 0.00070988837 | 0.00070988837 | 0.00142824131 |
| 43/E/projected | 2 | 0.365884604 | -4.44735931e-06 | 4.44735931e-06 | 0.000621460215 |
| 43/F_raw/projected | 1 | 3.5564028 | 0.00511673951 | 0.00511673951 | 0.00562608652 |
| 43/F_raw/projected | 2 | 2.57794959 | -0.00400098578 | 0.00400098578 | 0.00400098578 |

These signed results explain how a low total energy error can coexist with a larger trajectory error. For electrically projected states, current and power also share the identity P = UI, so they are different weighted views of related error rather than independent replications. Neither terminal balance nor total deposition ensures accurate local Joule density. The saved local-q NRMSE and balance diagnostics are retained in `tables/new-protocol-all-readouts.csv` without reinterpreting algebraic consistency as another empirical success.

## S6. Actual work and reproducibility scope

Each clean protocol uses two common parents and four branches, giving 10,800 Adam updates and 2400 complete objective/gradient evaluations. For the original clean branches, electrical forward/adjoint counts are 19,612/19,612 for seed 29 E and 19,560/19,560 for seed 43 E. F performs no electrical linear solve in training; it still evaluates and differentiates the full explicit face operator and neural potential. The original accepted branch L-BFGS steps are 145/147 (E/F, seed 29) and 144/146 (seed 43). These counters do not equate costs across methods.

Table S10. New-protocol actual counters and predeclared caps. Calibration and projected inference are separate from training. New-protocol aggregate accepted L-BFGS steps, including parents, total 1173.

| counter | actual | cap |
| --- | --- | --- |
| adam | 10800 | 10800 |
| complete_evaluations | 2400 | 2400 |
| E_forward | 39186 | 54000 |
| E_adjoint | 39186 | 54000 |
| calibration_forward | 100 | 1000 |
| calibration_adjoint | 0 | 1000 |
| inference_forward | 1390 | 1390 |

The 1390 projected inference solves are five roles times 278 nonzero-drive times: four neural states and one shared B_E. All 1001 times are still evaluated; zero-drive electrical outputs use their analytic values. Sparse direct solves and adjoints can reuse a single forward factorization for a common state, not across changed parameters. The published environment is Python 3.11, FP64, Torch 2.5.1 and SciPy 1.14.1. Network and sparse-solve placement may use different devices with a complete custom first-order VJP. No wall-time or acceleration conclusion is drawn from the work counters.

The manuscript sprint itself reads only saved CSV/JSON/NPZ evidence. It performs zero optimizer updates, zero checkpoint loads or model evaluations, zero new electrical/reference solves and no stress access. No GPU instance is started for it. Figures are regenerated with NumPy/Matplotlib, while the manuscript PDF is typeset with the available ReportLab runtime. PDF generation does not execute the research modules.

## S7. Reproduction and source map

### S7.1 Rebuild this manuscript from saved evidence

From the repository root, run the project Python on `paper/paper_submission/build_analysis.py`. It reads the versioned V28-V32 tables and the V32 saved power traces; it writes deduplicated result/event tables, report-only latency arithmetic and six figure sources. It does not import any scientific model or evaluator. The exact input-to-figure mapping is `analysis-provenance.json`.

Next run `paper/paper_submission/prepare_document.py` with the same project Python. It expands table/reference includes into complete readable Markdown and renders display equations. Run `paper/paper_submission/build_pdf.py` with the bundled Python that has ReportLab. The README gives the actual local commands. The generated `manuscript.md` and `supplement.md` contain the resolved scientific text and all tables; editable templates are in `source/`. Bibliographic entries are supplied in both human-readable and BibTeX form.

The existing snapshots are preserved. This package is a new local writing product, not a retroactive replacement for their manuscripts, judgments or endpoint identities. Figures 2-3 use the development table; Figure 4 uses four clean pairs; Figure 5 uses the saved event/reference/power data; Figure 6 retains adverse event and energy outcomes. Copies of broad historical run logs are unnecessary to rebuild those figures.

### S7.2 Reproduce the numerical experiments separately

A full numerical reproduction requires a separate execution and complete trajectory generation; the manuscript build is not that reproduction. The fixed repository commit is `ea29be9a9d33497b075873bcdc7673df43db7221` on `codex/v32-research-results`. Curated evidence preserves the endpoint states, configurations, quadrature pools, selected traces/snapshots and result records. Full support/reference fields and full own-field predictions remain in local `outputs/runs/20260915-lf11-protocol-history`; they are not all present in the public selected-results package. The corresponding original clean records are under `paper/paper_v31/evidence/confirmation/seed-29` and `seed-43`.

The numerical sequence is: reconstruct the specified finite case and inherited numerical contracts; generate support/reference trajectories; export the predeclared sparse mask; fit a fresh common parent for each seed; calibrate once; run the locked E/F branches with fixed caps; preserve final accepted states; perform the predeclared common projections; then score against the reference and render the saved results. Evaluation never selects an intermediate state. Full numerical reproduction should retain the published caps and information boundary and use a separate empty run directory, not overwrite accepted evidence.

| Component | Authoritative implementation or evidence |
| --- | --- |
| Electrical matrix, VJP, local Joule allocation | `pinn_pcm_sci/phk_v23_lf11_electric_layer.py` |
| Shared T/phase fields and cell residuals | `pinn_pcm_sci/phk_v23_lf11_elimination_physics.py` |
| Eliminated training and calibration | `pinn_pcm_sci/phk_v23_lf11_elimination.py` |
| Soft training and gradient-balanced control | `pinn_pcm_sci/phk_v23_lf11_training_coupling.py` |
| Full electrical spatial reduction | `pinn_pcm_sci/phk_v23_lf11_fullgrid.py` |
| Fresh initialization/common fits | `pinn_pcm_sci/phk_v23_lf11_clean_confirmation.py` |
| Finite new protocol and its evaluator | `pinn_pcm_sci/phk_v23_lf11_protocol.py`; `phk_v23_lf11_protocol_evaluate.py` |
| Formal field/event metrics | `pinn_pcm_sci/phk_v23_lf11_evaluation.py` |
| Functional comparison and local heating scores | `pinn_pcm_sci/phk_v23_lf11_elimination_evaluate.py` |
| Shared sparse interpolation | `pinn_pcm_sci/phk_v23_lf11_readout.py` |
| Saved original clean endpoints and scores | `paper/paper_v31/evidence/confirmation/` |
| Saved earlier-pulse endpoints and scores | `paper/paper_v32/evidence/` |

Historical executed source snapshots, not subsequently edited working files, determine the exact runtime behavior. V31 contains `runtime-sources` and `runtime-sources-stage-B`; V32 contains `runtime-sources` and `deployed-files.json`. Its `metadata-clarification.json` explains inherited unused template fields, including the old source identifier and effective per-seed role settings. Descriptive leftovers do not change the actual executed recipe. The file map above is a navigation aid; the preserved runtime snapshots resolve any later source drift.

### S7.3 Literature verification and reuse boundaries

The bibliography was checked selectively for claims that define this paper's contribution. Solver-in-the-Loop [3], hybrid FEM-NN [4] and modular implicit differentiation [5] were read in author-hosted full text, including the solver-coupling/root interfaces. They establish methodological precedents, not evidence for the present experiment. The source difference is partial quasi-static elimination for reconstruction with a common post-training projection control. No priority for solver coupling, adjoints or PDE-constrained optimization is asserted.

The modified-MLP equations in [2] and the control-volume loss in [6] were checked in full text. The former supplies architectural attribution; the latter is a neighboring integrated-residual formulation, not a source of entropy or convergence guarantees for this implementation. The device source [8] was checked in full text for geometry and electrothermal/phase feedback, including the materially richer model and parameter provenance. Its wall-cell idea does not turn the current synthetic coefficients into a calibration.

For [1] and [9], the accessible author preprint records support the general PINN and Adam roles. For [10], the author publication page supplies the L-BFGS reference. For [7], publisher metadata and abstract were accessible; a full-text derivation was not claimed as newly read. The present phase equation is specified explicitly by the project contract, not represented as an exact reproduction of that source. Publisher DOI pages for [4] and [6] did not load reliably; author full text and its bibliographic metadata were used instead. No quotation or source figure is reproduced. Source links in the References are direct primary-source URLs. No external code or asset is imported into the manuscript build, and the project source/attribution records retain responsibility for any earlier implementation provenance.

## S8. Claim-to-evidence matrix

The labels below distinguish executed evidence from interpretation. VERIFIED means saved numerical evidence or an implementation identity checked against source, not a new independent rerun during manuscript preparation.

| Statement | Status | Supporting evidence | Limit on the claim |
| --- | --- | --- | --- |
| Electrical projection can greatly repair device readouts at a fixed soft T/phase state | VERIFIED | Network/projected pairs; main Figure 2 | Does not improve phase or prove correct local q |
| The defined E package retains device advantages after the same projection | VERIFIED | Four clean E/F pairs; main Table 2 and Figure 4 | Two protocols and two seeds; specified finite soft recipes |
| Full-spatial electrical integration does not eliminate the development advantage | VERIFIED | Historical F_full; Figure 3 | Existing time sets, finite penalty and initial-V differences remain |
| The gain cannot be explained solely by withholding a final electrical solve from F | SUPPORTED_INTERPRETATION | Common solve for both learned states | Does not isolate a single training-gradient mechanism |
| The earlier-pulse case preserves paired phase and function gains against F and B_E | VERIFIED | Both new A/B outcomes and named metrics | Case-specific refitting, not zero-shot or formal OOD |
| Threshold recovery may coexist with continuous residual state and changed latency | VERIFIED | Reference history and event tables | The intervention does not separate T and phase mediation |
| Remaining thermal/phase PDE terms are independently necessary for the benefit | UNKNOWN | Strong D_E and negative matched residual-strength controls | Presence of residuals is not proof of their necessity |
| Complete implicit differentiation alone causes the observed improvement | UNKNOWN | No isolated VJP counterfactual | The evidence compares method packages |
| Strict two-cycle reliability has been achieved | Not supported; failures VERIFIED | All eight learned endpoints; Tables S4-S6 | Earlier-pulse first-cycle recall remains below 0.9 |
| Phase/event/function metrics uniformly rank E first | Contradicted by VERIFIED counterexamples | F29 latency, tail phase, original energy, F_full energy | Report each outcome rather than a universal ranking |
| The narrow S threshold remains stable under refined references | UNKNOWN | Fixed-reference margin 4.4453125 × 10⁻⁶ | No temporal refinement executed for this claim |
| Performance transfers to experimental oxide devices or arbitrary geometry | UNKNOWN | No calibrated material or cross-geometry evidence | Current object is a synthetic dimensionless wall cell |
| The model replaces or accelerates a traditional coupled solver | UNKNOWN | No fair solver-efficiency experiment | Known equations can be solved without interior observations |

## S9. Single bounded future numerical item

Status: PROPOSED_NOT_AUTHORIZED; not executed in this manuscript sprint. If a target claim requires continuum-oriented accuracy or robustness of the narrow S margin, retain all eight existing neural states and both B_E reconstructions and compare against temporally refined references for both protocols. Use 160 × 80 cells, time step 0.0003125 and saving every eight steps so the saved reference time grid remains compatible. The maximum is two trajectories and 16,000 main time steps in total. Internal coupled/electrical/phase solve caps must be separately frozen before any execution; main-step count is not a sufficient compute cap.

This item permits only new references and re-scoring already saved predictions: zero new training, model gradients, model inference or electrical projection of learned states. Keep original and refined scores side by side; do not select a new checkpoint or change a gate. If a required saved prediction is unavailable, that absence is a scope issue rather than permission to regenerate it. Report changes in named errors, narrow-margin decisions and events even when unfavorable. A changed ranking would narrow the claim; stable scores would support only the tested temporal sensitivity, not spatial convergence or material validity. This optional item does not block a complete manuscript with the present fixed-discretization scope.

## References

[1] Raissi, M., Perdikaris, P., and Karniadakis, G. E. Physics-informed neural networks: A deep learning framework for solving forward and inverse problems involving nonlinear partial differential equations. Journal of Computational Physics 378 (2019), 686-707. [DOI: 10.1016/j.jcp.2018.10.045](https://doi.org/10.1016/j.jcp.2018.10.045). [Author preprint, Part I](https://arxiv.org/abs/1711.10561).

[2] Wang, S., Teng, Y., and Perdikaris, P. Understanding and mitigating gradient flow pathologies in physics-informed neural networks. SIAM Journal on Scientific Computing 43(5) (2021), A3055-A3081. [Author full text](https://arxiv.org/html/2001.04536). The preprint title omits the word “flow.”

[3] Um, K., Brand, R., Fei, Y. R., Holl, P., and Thuerey, N. Solver-in-the-Loop: Learning from Differentiable Physics to Interact with Iterative PDE-Solvers. Advances in Neural Information Processing Systems 33 (2020). [Author full text](https://arxiv.org/html/2007.00016). [Official project](https://ge.in.tum.de/publications/2020-um-solver-in-the-loop/).

[4] Mitusch, S. K., Funke, S. W., and Kuchta, M. Hybrid FEM-NN models: Combining artificial neural networks with the finite element method. Journal of Computational Physics 446 (2021), 110651. [DOI: 10.1016/j.jcp.2021.110651](https://doi.org/10.1016/j.jcp.2021.110651). [Author full text](https://arxiv.org/html/2101.00962).

[5] Blondel, M., Berthet, Q., Cuturi, M., Frostig, R., Hoyer, S., Llinares-López, F., Pedregosa, F., and Vert, J.-P. Efficient and Modular Implicit Differentiation. Advances in Neural Information Processing Systems 35 (2022). [Author full text](https://arxiv.org/html/2105.15183).

[6] Patel, R. G., Manickam, I., Trask, N. A., Wood, M. A., Lee, M., Tomas, I., and Cyr, E. C. Thermodynamically consistent physics-informed neural networks for hyperbolic systems. Journal of Computational Physics 449 (2022), 110754. [DOI: 10.1016/j.jcp.2021.110754](https://doi.org/10.1016/j.jcp.2021.110754). [Author full text](https://arxiv.org/html/2012.05343).

[7] Allen, S. M., and Cahn, J. W. A microscopic theory for antiphase boundary motion and its application to antiphase domain coarsening. Acta Metallurgica 27(6) (1979), 1085-1095. [DOI: 10.1016/0001-6160(79)90196-2](https://doi.org/10.1016/0001-6160(79)90196-2).

[8] Miquel, R., Cabout, T., Cueto, O., Sklénard, B., and Plapp, M. Multi-physics modeling of phase change memory operations in Ge-rich Ge2Sb2Te5 alloys. Journal of Applied Physics 136 (2024), 145102. [DOI: 10.1063/5.0222379](https://doi.org/10.1063/5.0222379). [Author full text](https://arxiv.org/html/2409.06463).

[9] Kingma, D. P., and Ba, J. Adam: A Method for Stochastic Optimization. International Conference on Learning Representations (2015). [Author preprint](https://arxiv.org/abs/1412.6980).

[10] Liu, D. C., and Nocedal, J. On the limited memory BFGS method for large scale optimization. Mathematical Programming 45 (1989), 503-528. [Author publication page and paper](https://users.iems.northwestern.edu/~nocedal/Abstracts/limited-memory.html).
