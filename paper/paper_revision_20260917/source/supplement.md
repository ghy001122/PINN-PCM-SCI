# Supplementary material

## Training-time electrical elimination improves sparse electrothermal phase-change reconstruction beyond post-training electrical repair

This supplement consolidates implementation details, counterfactuals, complete event outcomes, reproducibility and evidence limits. It accompanies a fixed-reference numerical method study. O denotes the original protocol; S denotes the earlier second-pulse protocol. E is the eliminated method, F is the locked soft electrical PINN, and B_E is the shared same-solver interpolant. Unless marked network, electrical outputs are evaluated after the common solve. The historical development states are never pooled with clean initializations 29 and 43.

## S1. Numerical object and data construction

The main text states every physical coefficient and boundary condition. S1.1 below specifies the executed numerical reference algorithm. All quantities are dimensionless. Geometry and the electrothermal phase-feedback motif were inspired by wall-cell modeling; the current single scalar phase, smooth conductivity law and numerical coefficients do not reproduce the multi-material, compositional or switching model of reference [8]. The model is not calibrated to an oxide device, and the physical association cannot be strengthened merely by adding material citations.

The base numerical contract is `configs/phk_v2/object_numerical_contract.json`; its later object overlay is `configs/phk_v21/object_numerical_contract.json`. These files are not interchangeable: the overlay changes coefficients and the original time/pulse specification. The final two-pulse intervention is defined by `configs/phk_v23/lf11_protocol_sprint.json` and the case specification in `paper/paper_v32/evidence/case-and-budget.json`. Reproduction must apply the overlay and explicit finite pulse starts, not infer a periodic third pulse from a legacy period field.

The initial phase is analytic. The support mask is fixed before observing the new case's fields: each axis selects indices 0,4,8,… and the last index without duplicate endpoints. Spatial cell-center coordinates therefore need not lie on physical boundaries. The support trajectory has 80 × 40 cells; the fixed-reference trajectory has 160 × 80. Support output is sampled every 0.005 time units before the sparse time mask, giving sparse spacing 0.02 with the terminal point included. Reference output spacing is 0.0025. The final observation mask is 21 × 11 × 126, including 231 analytic initial positions and 28,875 positive-time locations. All three fields are observed at those locations. This is sparse relative to the full space-time trajectory, not evidence for an experimentally minimal sensor arrangement.

Support and reference trajectories use the inherited coupled block and logit-Newton numerical algorithms without output clipping or case replacement. The new support/reference generation required 1000/4000 main steps. Internal linear solves totaled 14,476/46,027, respectively. These are different counters and are not represented as 5000 identical-cost solves. Generator summaries reside under `paper/paper_v32/evidence/reference-generation/`. Matching-resolution prefixes before the intervention agree to roundoff, with maximum recorded field difference 7.22 × 10⁻¹⁵. This checks the finite-pulse implementation; it does not prove continuum convergence.

### S1.1 Reference time integration and nonlinear solution

The carrier and both references use cell-centered finite volumes and backward Euler in time. Let D_h be the phase no-flux Laplacian and D_Th the thermal Laplacian with the stated top Dirichlet and remaining Robin boundaries. At an accepted time step, the discrete equations include

$$\phi^{n+1}-\phi^n-\Delta t M(T^{n+1})[\epsilon^2D_h\phi^{n+1}-W_\phi(\phi^{n+1},T^{n+1})]=0. \quad (S1)$$

$$[(1+\gamma\Delta t)I-\alpha\Delta t D_{Th}]T^{n+1}=T^n-L(\phi^{n+1}-\phi^n)+\Delta t Qq^{n+1}. \quad (S2)$$

Starting from the previous accepted T and phase, each block evaluates conductivity, solves the electrical system at U(t_n+1), solves the phase equation with the current temperature iterate, and solves the linear thermal equation with that phase increment and electrical heat. Unit block relaxation is used. When the maximum scaled T/phase iterate change is at most 1e-8, the electrical field is recomputed from the new state and both final step-equation residuals must have infinity norm at most 1e-9. Otherwise iteration continues, up to 30 blocks. The thermal matrix is constant for a given grid and step, allowing one factorization per trajectory.

The phase subproblem uses Newton in the full logit variable with an analytic phase Jacobian followed by its sigmoid chain factor. Its infinity-norm step residual tolerance is 1e-10, with at most 30 Newton iterations. A trial logit step starts at one and is halved until the residual strictly decreases, down to 2^-20. Failure stops the trajectory. Outputs are not clipped and algorithms or time steps are not changed in response to event quality. These are algebraic tolerances for the implemented step equations; they are not bounds on continuum or learned-state error.

The implementation is specified by PhkV21OracleCase.solve in phk_v21_benchmark.py and _solve_logit_newton in phk_v21_solver.py, using the frozen object overlay. The new finite waveform and reference wrappers change the prescribed case and discretization only. The reference phase Laplacian is a grid operator, whereas training uses coordinate AD for phase and midpoint cell/face quadrature for heat. Shared electrical conductances help align that coupling interface but do not make the whole neural residual identical to the reference discretization. Halving dt tests one temporal perturbation of this numerical family; it neither supplies an independent solver nor establishes spatial convergence.

## S2. Exact learning interfaces

### S2.1 Architecture and admissible outputs

Each field starts with an independent 64-wide, four-hidden-layer modified MLP using smooth tanh transformations. The gated combination of two input feature projections follows the architectural construction in Wang et al. [2]; the project implements its own modules and does not claim that architecture as original. E freezes the potential head; F jointly trains it with the temperature, phase and adapter parameters.

The temperature adapter adds to the temperature latent a 32-wide, two-hidden-layer modified MLP with 21 inputs: three normalized coordinates and sine/cosine pairs at nine fixed frequency vectors. The vectors are (0.5,0,0), (1,0,0), (2,0,0), (0,0.5,0), (0,1,0), (0,0,0.5), (0,0,1), (0,0,2), (0,0,4); angles are 2π times the coordinate–frequency product. Its output weights and bias are zero at initialization. The adapter is present in every clean parent and both branches. There is no matched ablation establishing an independent adapter contribution.

Coordinates supplied to every head are (x, 2z-1, 2t/2.5-1), mapping the physical domain to [-1,1]^3. Derivatives in the residuals are with respect to physical x,z,t, including this chain rule. Main equations (8)–(9) preserve the analytic initial temperature and phase, phase bounds and top thermal value. The temperature upper envelope is a representation constraint, not an experimental temperature limit. The soft potential transform preserves 0 ≤ V ≤ U and the top electrode exactly, but does not hard-enforce the grounded heater. Known electric boundary values enter its finite-volume residual. No extra potential fitting gate is imposed on the clean parents.

### S2.2 Observation measure and logit target

Let p_i be normalized sparse spatial dual-volume times trapezoidal-time weights. Potential and temperature use this global measure, not an uncorrected interface-oversampled mean. The phase target is the complete initial-logit increment

$$d_i=\operatorname{logit}(\phi_i^{\rm obs})-\operatorname{logit}(\phi_0(x_i,z_i)). \qquad (S3)$$

Logits use ε_logit = 10⁻⁸ for numerical clipping of their input only. The base-model increment is δ_θ = 8a(t)h_φ and is not divided by startup a(t). For the new heads, the same interface includes R_ξ or normalized gR_ξ in h_φ, so the observation and PDE paths both use the composed phase. With d_scale = 36.84136146790473,

$$L_{\rm obs}=(L_V+L_T+L_\phi)/3, \qquad (S4a)$$

$$L_V=\sum_i p_i((V_i-V_i^{\rm obs})/0.72)^2,\qquad L_T=\sum_i p_i((T_i-T_i^{\rm obs})/0.45)^2, \quad (S4b)$$

$$L_\phi=\sum_i p_i^\phi((\delta_i-d_i)/d_{\rm scale})^2. \qquad (S4c)$$

The phase measure averages two normalized measures with equal weight: the positive-time global measure and endpoints of visible space-time cells whose corner phase values straddle 0.5. Duplicate vertices accumulate their proper weights. If there are no such endpoints, it falls back to the global phase measure. This uses only observed values. No dense interface pool, teacher derivative, reference event ranking or reference current is supplied. Initial analytic data are counted separately and shared by all methods.

Adam samples four observation times from the half-global/half-phase temporal marginal proposal and applies its inverse-probability correction, including all visible spatial points at a sampled time. Fixed full-objective L-BFGS evaluates all observation groups with their original weights. The observations are already used for fitting and development; later subdivision of them would not constitute unseen validation.

### S2.3 Cell operators, boundaries and scales

Training uses the common 80 × 40 electrical grid, harmonic face conductances, half-cell electrode resistances and fractional heater overlap. The same forward factorization is reused only for its associated adjoint. The first-order VJP includes the dependence of both A and f on conductivity, as well as direct Joule derivatives. No thermal or phase trajectory is solved inside the network. CPU sparse factorization may be connected to GPU field evaluation without detaching the physical gradient.

The numerical source obeys the half-resistance deposition formula in the main text. In particular, an interface with unequal resistances deposits unequal shares. Electric face dissipation includes electrode contributions. A grounded, balanced electrical solution gives total deposited power equal to terminal input. For an arbitrary soft potential, total deposition still equals the face dissipation sum, but terminal equality need not hold. These statements are algebraic identities or electrical balance conditions, not separate learned-accuracy tests.

For each physical time, sampled cells obtain midpoint T and φ, their time derivatives, shared-face AD temperature gradients and the original phase Laplacian. Boundary gradients use the network's own values. With b_T = T on the top and b_T = ∂ₙT + 0.25T elsewhere,

$$L_{\rm BC}=\frac{1}{13}\sum_{s\in\{l,r,b,t\}}\left[\operatorname{mean}_s(b_T^2)+\operatorname{mean}_s((\partial_n\phi)^2)\right]. \quad (S5)$$

$$L_{\rm IC}=\frac{1}{3}\left[\operatorname{mean}(T_0^2)+\operatorname{mean}(((\phi-\phi_0)/0.03)^2)\right]. \quad (S6)$$

The historical denominators 13 and 3 are retained. Five omitted electric boundary subterms contribute zero; deleting them from the denominator would change the other terms' weights. All paired branches use the same definition. The electric, thermal and phase residual scales are 1, 4 and 5. The thermal/phase average retains divisor 3 despite containing two terms. No dynamic reweighting, autonomous energy-decay regularizer or adaptive rescue is introduced.

At the common fitted parent, a = L_obs,E is computed using the eliminated potential, and b = J_Tφ,E + 5L_BC + L_IC uses a fixed calibration pool. Both are floored at 10⁻¹² and shared within that pair. They are not recomputed separately for F. Thus a can differ from the full observation loss measured with the parent's original voltage head. Actual clean-parent fitting errors and scales are shown below; these are visible-data errors, not validation errors.

Table S1. Clean parent quality and shared calibration. O/S identify protocols; a and b are the actual eliminated-parent scales.

{{TABLE:parent-summary}}

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

Table S2. Development counterfactuals: electrical repair, the strong D_E control and the full-spatial/gradient-balanced soft alternatives. “Network” means the model's unsolved V; “projected” applies the common solve without changing T or phase. Device current in this consolidated table is the bottom-current error; using top current for an electrically unbalanced model would produce a different result. All entries are development states with a common historical parent, not extra clean seeds.

{{TABLE:historical-summary}}

The earlier fixed-state D_I-to-E0 replacement held T/phase and conductivity fixed and repaired severe electrical readout errors; its underlying record is in `paper/paper_v28/evidence/evaluation/results.json` together with the V27 comparator evidence. The main figures instead use directly paired F network/projected readouts, which more directly establish the relevant post-training-repair counterfactual. These are compatible but distinct controls. Potential volume accuracy alone is not a certificate for electrode flux accuracy.

Table S3. Remaining-PDE-strength counterfactual. D_C continues the control objective; P1 adds the original remaining PDE term; P_kappa adds it with κ = 92.84049, fixed from a complete-gradient norm ratio of 0.1077% at the shared parent. The original gradient calculation included the T/phase → conductivity → potential → heating chain. The scalar strengthened a measurable optimization effect, but did not establish the required predictive increment. Each state used 223 complete evaluations, with zero new Adam updates in that campaign; it is not comparable to a fresh 1500-update branch as an additional initialization.

{{TABLE:remaining-pde-controls}}

P1 and P_kappa improve raw phase error over D_C by approximately 0.65% and 0.73%, respectively. The stronger remaining-PDE term reduces the thermal-dominated residual but pays a current/power cost. Its second-cycle timing remains above 0.005. These controls prevent the manuscript from attributing the main advantage to an independently demonstrated necessity of the remaining residuals. They do not establish universal uselessness of thermal or phase physics, nor do they justify changing an old failed decision.

The full-grid soft control tests spatial integration/coverage at the existing physical times. It does not equalize the temporal constraint set with E, remove the finite penalty, equalize initial V, or isolate an adjoint pathway. No additional stop-gradient, hard-lift or voltage-pretraining control is implied by the present evidence. The claim is restricted to the implemented method package and tested comparators.

## S5. Complete event and pulse-history evidence

The following three tables partition the complete saved event record into readable groups without selecting favorable cycles. They include the shared baseline once per case. F denotes F/projected; phase events are identical for its network and projected readouts. For these historical tables using the original references, first-onset time is 0.2406 in both cases; S9 reports the refined-reference onsets separately. Reference second onsets are 1.4984 (O) and 1.2268 (S). All listed phases exhibit the two onsets; no case was replaced after observing its event status.

Table S4. Timing and support quality for every method/cycle. Neither timing nor recall replaces the other in the project-defined strict event requirements.

{{TABLE:event-quality}}

Table S5. Threshold fractions and recovery. A recovery fraction of one means no remaining above-threshold active fraction, not φ = 0 or T = 0.

{{TABLE:event-shape}}

Table S6. Integrated support masses. These are space-time measures, not independent sample counts. Recall is overlap/reference mass; precision is overlap/predicted mass.

{{TABLE:event-masses}}

None of the eight historical learned endpoints in Tables S4–S6 passes every strict criterion under the original references. The later gated endpoint and its reference-specific result are reported separately in S10–S11. In particular, the earlier-pulse E timing criteria pass but its first-cycle recall values are 0.866607 and 0.875507. On the original case, seed 43 E first-cycle recall is lower than F. Earlier-pulse F29 has better second-cycle timing and a slightly better prediction of the cross-protocol latency change. E has greater tail-phase RMS in both new pairs, and slightly worse second-cycle temperature error in seed 43. Complete later-window state and device values remain in `tables/second-cycle.csv`.

Table S7. Reference state immediately before each second pulse. Maxima and means use the specified ROI.

{{TABLE:history-summary}}

Table S8. Report-only second-onset latency change, calculated from saved event times. The reference shortening is 0.0316. This analysis introduces no training, selection rule or additional pass criterion.

{{TABLE:latency-summary}}

The state differences and the generator prefix agreement support a history-dependent response within the numerical equations. They do not separate thermal and phase mediation, and separately trained offline predictors need not coincide on the shared physical prefix. B_E is one deterministic reconstruction per case, even where it is displayed beside both seeds.

Table S9. Per-pulse power and energy for the earlier-pulse case. Absolute signed integral and integral of absolute power error are distinct; the latter cannot cancel in time. Units are dimensionless, except the normalized percentage column.

{{TABLE:pulse-summary}}

These signed results explain how a low total energy error can coexist with a larger trajectory error. For electrically projected states, current and power also share the identity P = UI, so they are different weighted views of related error rather than independent replications. Neither terminal balance nor total deposition ensures accurate local Joule density. The saved local-q NRMSE and balance diagnostics are retained in `tables/new-protocol-all-readouts.csv` without reinterpreting algebraic consistency as another empirical success.

## S6. Actual work and reproducibility scope

Each clean protocol uses two common parents and four branches, giving 10,800 Adam updates and 2400 complete objective/gradient evaluations. For the original clean branches, electrical forward/adjoint counts are 19,612/19,612 for seed 29 E and 19,560/19,560 for seed 43 E. F performs no electrical linear solve in training; it still evaluates and differentiates the full explicit face operator and neural potential. The original accepted branch L-BFGS steps are 145/147 (E/F, seed 29) and 144/146 (seed 43). These counters do not equate costs across methods.

Table S10. New-protocol actual counters and predeclared caps. Calibration and projected inference are separate from training. New-protocol aggregate accepted L-BFGS steps, including parents, total 1173.

{{TABLE:execution-budget}}

The 1390 projected inference solves are five roles times 278 nonzero-drive times: four neural states and one shared B_E. All 1001 times are still evaluated; zero-drive electrical outputs use their analytic values. Sparse direct solves and adjoints can reuse a single forward factorization for a common state, not across changed parameters. The published environment is Python 3.11, FP64, Torch 2.5.1 and SciPy 1.14.1. Network and sparse-solve placement may use different devices with a complete custom first-order VJP. No wall-time or acceleration conclusion is drawn from the work counters.

The original manuscript-only sprint read saved evidence and performed no new scientific execution. The phase-head and temporal-reference experiment in S9-S10 added six coupled PINN endpoints and two time-refined references. Its GPU outputs were recovered and the instance was shut down before local reference scoring. The separate spatial study in S15 adds two CPU reference trajectories, with all neural predictions fixed and no GPU use. Stress was not read. Figures are regenerated with NumPy/Matplotlib, while the manuscript PDF is typeset with the available ReportLab runtime. PDF generation does not execute the research modules.

## S7. Reproduction and source map

### S7.1 Rebuild the historical figures from saved evidence

From the repository root, run the project Python on `paper/paper_submission/build_analysis.py`. It reads the versioned V28–V32 tables and the V32 saved power traces; it writes deduplicated result/event tables, report-only latency arithmetic and six figure sources. It does not import any scientific model or evaluator. The exact input-to-figure mapping is `analysis-provenance.json`.

Next run `paper/paper_submission/prepare_document.py` with the same project Python. It expands table/reference includes into complete readable Markdown and renders display equations. Run `paper/paper_submission/build_pdf.py` with the bundled Python that has ReportLab. The README gives the actual local commands. The generated `manuscript.md` and `supplement.md` contain the resolved scientific text and all tables; editable templates are in `source/`. Bibliographic entries are supplied in both human-readable and BibTeX form.

The original manuscript-only snapshot is preserved. That earlier package was a local writing product, not a retroactive replacement for their manuscripts, judgments or endpoint identities. Figures 2–3 use the development table; Figure 4 uses four clean pairs; Figure 5 uses the saved event/reference/power data; Figure 6 retains adverse event and energy outcomes. Copies of broad historical run logs are unnecessary to rebuild those figures.

For this revision, build_revision_analysis.py consumes the completed portable scoring results; update_manuscript.py integrates those results into the complete sources, and prepare_document.py/build_pdf.py rebuild the final documents. The revision README gives the commands. The old snapshot and its numerical values are preserved.

### S7.2 Reproduce the historical numerical experiments separately

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

The labels below distinguish executed evidence from interpretation. VERIFIED means saved numerical evidence or an implementation identity checked against source, with the array-only reproduction in this revision identified separately from the original training and the six new continuations.

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
| The eight historical states meet the strict two-cycle requirements | Not supported; failures VERIFIED | All eight learned endpoints; Tables S4–S6 | Earlier-pulse first-cycle recall remains below 0.9 |
| Phase/event/function metrics uniformly rank E first | Contradicted by VERIFIED counterexamples | F29 latency, tail phase, original energy, F_full energy | Report each outcome rather than a universal ranking |
| The narrow S threshold remains stable under refined references | VERIFIED for the tested reference pair | Historical margin 4.4453125 × 10⁻⁶; actual new margin in S9 | Updated by the executed time-reference comparison in S9; not a spatial convergence result |
| The gated head has a reference-stable independent increment | Not established | No A/B increment under either reference; a strict increment only for seed 43 under the refined reference | The reference-specific strict contrast is VERIFIED; it is not stable across both references or clean-seed confirmation |
| Historical device advantages survive the tested time-step refinement | VERIFIED in 4/4 paired comparisons | Fixed arrays, both reference trajectories; main Figure 7 | Does not establish spatial convergence |
| Performance transfers to experimental oxide devices or arbitrary geometry | UNKNOWN | No calibrated material or cross-geometry evidence | Current object is a synthetic dimensionless wall cell |
| The model replaces or accelerates a traditional coupled solver | UNKNOWN | No fair solver-efficiency experiment | Known equations can be solved without interior observations |

## S9. Executed reference sensitivity and portable array reproduction

The fixed-model temporal refinement was executed on 16 September 2026. The 17 September review changes presentation and documentation only. Both references use 160 by 80 cells, time step 0.0003125, saving every eight steps and 8000 main steps. Original references and all original decisions remain separate. The actual algorithms, tolerances and no-clipping policy are unchanged. A descriptive metadata clarification corrects inherited window/reference labels; the executing trajectories used the correct pulse starts and step sizes, and the full 8001-point drive is unchanged by that correction. No reference trajectory is rerun for this documentation correction.

With fixed historical predictions, the device criterion against the projected soft control passes in 4/4 pairs under the original references and 4/4 under the refined references. The changed historical A/B decisions are: none across eight comparisons (four E/soft and four E/interpolant), or sixteen A/B decisions per reference. A changed gate limits that specific threshold claim; a retained direction or gate supports only the tested temporal perturbation. Full errors, each reference denominator and fixed-old-denominator diagnostics are retained in the scoring records. The original reference discrepancy is δ_S = 1.6875e-05 and ROI phase RMS δ = 0.00039034515. The shorter reference discrepancy is δ_S = 1.671875e-05 and ROI phase RMS δ = 0.00032183192. The historically narrow seed-43 S margin changes from 4.4453125e-06 to 7.9921875e-06. The sufficient triangle-bound condition alone cannot certify this narrow margin; its retention follows from actual rescoring of these two references, not from a continuum argument.

Table S11. Reference event changes, including both cycles and protocols.

{{TABLE:reference-events}}

The principal original/refined metrics and event measures for all sixteen objects are in tables/all-fixed-metrics.csv and tables/all-fixed-events.csv. The paired-effect-sizes.csv table separately reports each compared error, signed difference, percentage-point difference where the error is normalized, and relative error reduction; it distinguishes continuation from matched representation and historical method comparisons. The all-strict-failures.csv table names each failed original requirement, including any peak-phase failure. The complete portable results.json additionally retains all cycle peak/locality fields, validity checks and event-failure lists; the compact printed tables do not replace those records. The reference-margins table includes the same-norm triangle bounds; the JSON records distinguish reference-specific and fixed-original normalization. Old bottom-current scoring against the reference top current is preserved, while bottom-native errors are also supplied. A changed reference onset, event correspondence or threshold flag is a numerical sensitivity result, not retraining or a new physical event in a fixed predictor.

The local portable archive contains all scoring arrays and serialized geometry/ROI/rules. Python isolated mode runs portable/rescore.py in a clean extracted directory with NumPy only. It imports neither Torch nor SciPy, does not load checkpoints and performs zero linear solves. Its kernels preserve the original definitions; numerical metrics are compared at relative tolerance 2e-10 and absolute tolerance 2e-12, while categorical decisions must agree exactly. This tolerance concerns reproducibility arithmetic, not relaxed scientific effect gates.

The archive also supplies portable/reproduce_network.py as a separate opt-in entry. Its prepare action stages only the existing parent states, sparse observations and known-physics sources. Train repeats the specified six continuations; infer regenerates one selected fixed endpoint. Neither is invoked by the scoring or figure commands. Historical clean-parent retraining is a further, separate reproduction level.

## S10. Phase-head experiment, actual cost and complete outcomes

Neither added head satisfies a predefined phase, device or strict increment against E_C in either parent under the original reference. The additional equal-parameter gate criterion is met in neither parent under the original reference and in 43 under the refined reference. A result in only one parent or under only one reference is a bounded development signal. It is not a clean initialization confirmation or a reason to pool different categories across seeds. No independent gate contribution is established under the original reference. The gate is retained as a tested counterfactual rather than added to the main contribution list. The absence of an original-reference increment limits the proposed representation-efficiency explanation without proving that phase representation never matters. The reference-specific strict result is examined separately below.

All six arms together used 3600 Adam updates, 600 complete fixed-target evaluations, 41076 training forward solves and 41076 adjoint solves, followed by 1668 fine-grid projection solves. These quantities are not assumed to have equal unit cost. Trainable counts are 29827 for E_C and 31044 for E_R/E_I; each residual adds 1217. Total stored model counts, including the unused frozen V head, are 43140, 44357 and 57670, respectively. E_I additionally stores and evaluates 13313 frozen parent-phase parameters and differentiates that gate with respect to coordinates through second spatial derivatives. Its RMS amplitude normalization does not cancel this extra cost or match all gradients. No runtime acceleration claim is made.

Table S12. Actual matched work. Accepted L-BFGS steps and objective/gradient evaluation counts are different quantities.

{{TABLE:revision-execution}}

Table S13. All short-gap parent/control/candidate and soft metrics under both references. Percentages are normalized RMS errors times 100.

{{TABLE:phase-adapter-metrics}}

Table S14. All new-development support, timing, recovery and support masses. FN/FP masses are reporting diagnostics derived from fixed arrays.

{{TABLE:phase-adapter-events}}

Table S15. Potential, bottom current, energy and local Joule deposition for the same objects. A smaller integrated-energy error may coexist with a larger power-trajectory error; local q is a spatially resolved error, not an algebraic conservation check.

{{TABLE:phase-adapter-secondary}}

![Figure S1. All predeclared display times for seed 43.](figures/fig08-support-gate-seed43.png)

Figure S1. Same complete-domain times, colors and normalization as Figure S3. The gate depends only on the frozen parent, never on reference error. Complete time traces accompany the portable scores; no favorable crop or time was selected from dense truth.

## S11. Updated evidence limits

Strict two-cycle success holds for 0 of the sixteen objects under the original references and 1 under the refined references. Original-reference successes: none. Refined-reference successes: shorter/43/E_I. Historical and newly developed objects are not pooled to estimate a success probability, and a reference-induced status change is not new model capability.

Seed 29, E_R: original-reference increment = none; refined-reference increment = none.

Seed 29, E_I: original-reference increment = none; refined-reference increment = none.

Seed 43, E_R: original-reference increment = none; refined-reference increment = none.

Seed 43, E_I: original-reference increment = none; refined-reference increment = strict.

## S12. Limited material mapping and remaining validation

The application inspiration is the coupled wall-cell PCM model of Miquel et al. [8]. Its material is Ge-rich GST, not an oxide. The mapping below identifies shared modeling roles and concrete omissions; it does not transfer its calibrated parameters into this synthetic calculation. The evidence label for the present physical coefficients remains a frozen numerical design, not experimental validation.

| Component | Present numerical object | Source relationship and missing evidence |
| --- | --- | --- |
| State variables | Reduced T and one bounded scalar phase φ | [8] couples multiple phases and composition. Our φ is not a calibrated crystallinity, metallic fraction or chemical population. |
| Geometry and boundaries | Two-dimensional wall cell, top electrode, grounded partial bottom, Robin cooling | [8] supplies device-model motivation; dimensional dimensions, contact resistances, material interfaces and packaging are not identified here. |
| Conductivity | Smooth exp[0.25T + log(8)φ²(3-2φ)] | The feedback role is shared; this formula and its coefficients are synthetic. Measured phase/temperature-dependent transport is absent. |
| Heat and latent contribution | Fixed reduced diffusivity, cooling and latent ratio 0.05 | A quantitative device claim requires mutually consistent heat capacity, conductivity, latent heat and boundary calibration. None is inferred from the present fits. |
| Phase kinetics | A scalar nonconserved temperature-driven phase equation | It omits multi-phase nucleation/composition and oxide electronic/structural order parameters. Theoretical isothermal VO2 switching [14] is a counterexample to assigning every oxide transition solely to our Joule-heating route. |
| Validation quantities | Synthetic current, power, local heating and phase events | Experimental switching trajectories, optical/structural phase observations and material parameters would require independent validation. Algebraic current balance does not provide it. |

Kaltenbacher [13] treats reduced and all-at-once formulations in inverse problems; that is useful context for eliminating a state variable, not a convergence theorem for this neural representation. PINN-Proj [12] enforces specified integral constraints by projection, whereas the present electrical layer solves a local quasi-static boundary problem coupled to T and φ. Neither source makes elimination or differentiable constraints novel in themselves. PDE-CL [15] and hPINN [16] further delimit the constraint-learning precedents. They were not run as additional baselines. The contribution rests on the explicitly defined interface and matched reconstruction evidence.

The remaining thermal/phase-residual necessity experiment is deliberately deferred. Adding an interface head, if effective, would not answer that separate ablation. Likewise, the current temporal-reference exercise cannot certify geometry transfer, material calibration, or arbitrary pulse generalization.


## S13. Complete phase-head formulation and visual evidence

### S13.1 Phase representation and attribution

The main elimination study leaves incomplete first-cycle support recall despite accurate electrical readouts. We test the hypothesis that a limited phase parameterization contributes to this mismatch. The hypothesis does not establish sigmoid saturation as its cause, nor imply that adding parameters must help. The two final earlier-pulse E states are used as separate parents. This is subsequent development on two already trained states, not another pair of clean initialization confirmations.

An unchanged continuation, E_C, is compared with an ordinary residual head, E_R, and a parent-interface-modulated residual head, E_I. These identifiers denote methods; the current error in the evaluation equation is a separate functional quantity. Let the original complete logit be ell_θ = logit(φ₀) + 8a(t)h_φ,θ. The residual R_ξ takes the original normalized coordinates as input and uses a 3-32-32-1 tanh MLP with 1217 trainable parameters. The output weight and bias are initially zero. E_R and E_I use identical initial residual tensors, with seeds 916029 and 916043 for the two parents. Their complete initial fields exactly equal those of E_C.

For E_I, a frozen copy of the parent's complete phase function defines

$$g=0.25+0.75\,[4\phi_{\rm parent}(1-\phi_{\rm parent})],\quad c_g=\sqrt{\mathbb E_\rho[g^2]},\quad \hat g=g/c_g. \qquad (S7)$$

The positive floor leaves a correction path outside the parent's predicted interface, including possible missed regions. The scalar c_g is calculated once using the parent's original unlabeled calibration quadrature; it equals 0.2693107755 and 0.2705578194 for seeds 29 and 43. It controls an RMS amplitude, not every gradient norm or the effective optimizer step. The outputs are

$$\phi_R=\operatorname{sigmoid}(\ell_\theta+8aR_\xi),\quad \phi_I=\operatorname{sigmoid}(\ell_\theta+8a\hat gR_\xi). \qquad (S8)$$

Only the gate's parameters are frozen. Its coordinate derivatives, including second spatial derivatives, remain in the phase residual. The two added residuals have equal trainable counts, but E_I has extra frozen parameters and extra function/coordinate-derivative evaluations; it is not equal to E_R in total model storage or work. No logit is recovered by inverting an already saturated phase prediction. One composed phase interface is used by the observation increment, conductivity, electrical solve, Joule deposition, thermal and phase equations, boundaries, initial conditions and inference. Thus the comparison changes representation while preserving the actual coupled PINN objective.

Residual parameterizations have established precedents [11], and gated mixing is already present in the modified-MLP background [2]. The present residual head is neither the original ResNet architecture nor a claim to invent gating. E_C-to-E_R assesses added capacity and its optimization effects. E_R-to-E_I assesses the particular frozen-gate parameterization, including its coordinate-derivative cost. A gain over E_C alone cannot establish an independent gate benefit.


### S13.2 Complete continuation and scoring protocol

For each earlier-pulse seed, all three continuation arms open the existing T/phase parameters and temperature adapter; E_R and E_I additionally open their residual parameters. The unused V head remains frozen. The original seed's a,b, observation measures, thermal/phase scales 4/5 and denominators 3/13 are unchanged. Lambda is fixed at 0.1 from the first update. Each arm receives 600 fresh-Adam updates at learning rate 0.0001 followed by at most 100 complete fixed-target L-BFGS evaluations. The six-arm ceiling is 3600 updates and 600 evaluations. All three arms share the same seed-specific observation and physical sampling streams. No arm is rescued using reference results.

The endpoint is the fixed-budget final accepted state or the optimizer's intrinsic stopping state. All line-search trials are counted and rejected trial states are rolled back. Electrical solve limits are 11400 forward and 11400 adjoint solves per arm. Complete evaluation uses all 126 observation times and the original 32 physical times; at most 34 observation times have nonzero drive. The six new projected predictions require at most 1668 electrical solves. Actual work, extra gate evaluation and coordinate differentiation are reported in Supplement S10.

A representation increment requires the original phase or device criterion against E_C and the corresponding noninferiority to the original E: temperature, top-current and potential errors for the phase criterion; S, phase, temperature, potential and top-current errors for the device criterion. Additional checks of all errors against the parent are reported separately, not added as new eligibility gates. Separately, a first complete strict two-cycle success may be reported when S, phase, temperature, potential, current and power errors remain within the original noninferiority limits against both controls; this does not retroactively pass a failed A/B criterion. Gate independence additionally requires the same kind of gain against E_R, which has the same trainable parameter count. Mixed seed outcomes remain a development signal, not a stable confirmation. The old projected soft models and B_E remain in the tables.

The old soft models do not receive this extra continuation budget. Their rows remain useful reference points, but a new head versus an old F is not an equal-budget network ablation. The new representation attribution comes from E_C/E_R/E_I, whereas the original clean E/F experiment retains its own matched budget and identity.

The independent scoring package contains all fixed arrays and serialized metric definitions. Its evaluator uses only NumPy: it does not load a neural checkpoint or execute a linear solver. It first reproduces the ten historical objects' saved metrics, events and decisions, then evaluates the six new objects and the refined references. Figure rebuilding, array-only rescoring and retraining are separate operations. No local archive is represented as a public dataset or assigned an invented identifier.



### S13.3 All matched results and predeclared maps

The six prescribed coupled PINN continuations and their own electrical projections were completed. Table S16 and Figure S2 retain the parent and continued control alongside both residual heads, which add the same number of trainable parameters. E_I additionally stores a frozen copy of the parent phase head. No new reference enters optimization or checkpoint selection.

Table S16. New-head decisions under the original and refined references. A strict capability gain is separate from the phase/device criteria. Gate independence additionally compares E_I with E_R, with equal trainable counts and the extra frozen-gate cost disclosed.

{{TABLE:phase-adapter-decisions}}

For seed 29, unchanged continuation changes raw phase RMS from 0.01900241 to 0.01754883. This control is necessary because the new heads receive additional optimization.

E_R changes phase RMS by +0.97% and power NRMSE by -3.59% relative to E_C (negative is improvement). Its cycle recalls are 0.886097/0.965721, with onset errors 0.005417/0.000275.

E_I changes phase RMS by -1.58% and power NRMSE by -7.54% relative to E_C (negative is improvement). Its cycle recalls are 0.864128/0.963498, with onset errors 0.001575/0.001525.

For seed 43, unchanged continuation changes raw phase RMS from 0.01861922 to 0.01696354. This control is necessary because the new heads receive additional optimization.

E_R changes phase RMS by -0.61% and power NRMSE by -4.43% relative to E_C (negative is improvement). Its cycle recalls are 0.892181/0.959395, with onset errors 0.003300/0.000783.

E_I changes phase RMS by +2.04% and power NRMSE by -7.24% relative to E_C (negative is improvement). Its cycle recalls are 0.898603/0.962301, with onset errors 0.003750/0.002287.

Neither added head satisfies a predefined phase, device or strict increment against E_C in either parent under the original reference. The additional equal-parameter gate criterion is met in neither parent under the original reference and in 43 under the refined reference. A result in only one parent or under only one reference is a bounded development signal. It is not a clean initialization confirmation or a reason to pool different categories across seeds. No independent gate contribution is established under the original reference. The gate is retained as a tested counterfactual rather than added to the main contribution list. The absence of an original-reference increment limits the proposed representation-efficiency explanation without proving that phase representation never matters. The reference-specific strict result is examined separately below.

![Figure S2. Fixed-budget phase-head comparison.](figures/fig07-phase-adapter.png)

Figure S2. Both parents are displayed separately. All metrics use the original reference; the two curves in the bottom rows show the two cycles. Dashed horizontal lines retain the original criteria. Update and complete-evaluation caps are matched. E_C retains the original trainable count; E_R/E_I each add 1217 trainable parameters, and E_I additionally evaluates and differentiates a frozen gate. Supplement S10 lists actual counts and both-reference tables.

![Figure S3. Fixed-time false-negative/false-positive maps and parent gate, seed 29.](figures/fig08-support-gate-seed29.png)

Figure S3. The four display times were fixed before training (0.20, 0.30, 1.21, 1.31); the complete domain is shown. Blue marks missed activity, rust marks false activity and white marks agreement. The final column is the frozen normalized gate. It is not selected from reference errors. The same complete plot for seed 43 appears in Supplement S10. These maps explain localization descriptively; they do not create an additional training or selection criterion.


![Figure S4. Both-reference event metrics for all new endpoints.](figures/fig10-event-reference-sensitivity.png)

Figure S4. Both cycles of all six fixed new endpoints are displayed. Paired points change the reference only, preserving the predicted fields, event times and active masses. Dotted lines are the original recall and timing requirements; passing these two quantities alone does not replace the complete strict rule. The trace for seed 43, gated head, cycle 1 shows the reference-sensitive crossing without suppressing the other endpoints.


## S14. Complete-rule reference perturbation bounds

### S14.1 Assumptions and sufficient conditions

The original margin plot separates individual error gains. A complete A/B rule also contains noninferiority guards and absolute floors. We now evaluate sufficient conditions for the whole rule from the already saved metrics and time-reference discrepancies; this analysis runs no neural model, reference solver or array rescoring. It neither changes the historical decisions nor supplies new spatial evidence.

For a candidate and comparator with fixed predictions, let e_c and e_b be their errors in the same unnormalized norm, and d > 0 their shared normalization. For S, the reference perturbation is measured by the symmetric-difference distance between reference active sets; for temperature absorb the fixed 0.45 divisor into the norm. Assume a changed reference changes either error by at most r δ, and d by at most r δ_d. The normalizer bound δ_d is zero for fixed normalizers; for current and power, it is set to the corresponding reference RMS discrepancy, which bounds the normalizer change by the reverse triangle inequality. The argument concerns a blockwise reference-distance bound, not a probability distribution. In particular, the bound on active-set distance is separate from the phase RMS bound: an RMS perturbation alone need not control threshold crossings.

$$ |e'_c-e_c|,\ |e'_b-e_b|\leq r\delta,\qquad |d'-d|\leq r\delta_d,\qquad d'>0.\qquad (S9) $$

A relative gain η together with an absolute normalized floor τ requires both inequalities below. Substitution of the worst allowed error changes gives a sufficient condition that retains the original max rule:

$$ (1-\eta)e_b-e_c\geq r(2-\eta)\delta,\qquad e_b-e_c-\tau d\geq r(2\delta+\tau\delta_d).\qquad (S10) $$

For a relative noninferiority allowance ν, either of the following inequalities is sufficient, because the permitted deterioration is the larger of the relative and absolute allowances:

$$ (1+\nu)e_b-e_c\geq r(2+\nu)\delta\quad\mathrm{or}\quad e_b-e_c+\tau d\geq r(2\delta+\tau\delta_d).\qquad (S11) $$

We use η = 0.1, ν = 0.05 and the unchanged metric-specific τ. For each gain the sufficient radius is the smaller branch radius from (S10); for each guard it is the larger branch radius from (S11). The minimum across all required components gives the reported whole-rule sufficient radius, with negative values reported as zero and an originally failed rule still marked failed. Positive-normalizer conditions are retained. This is a conservative guarantee from the chosen inequalities, not the largest true radius permitted by correlated reference errors.

### S14.2 What the saved evidence can and cannot certify

The reference distance at r = 1 is exactly the measured old-to-time-refined discrepancy for each metric block. Using its value to define a perturbation budget does not imply that an unknown spatial reference, the continuum solution or an experiment lies inside that budget. Empirical comparison against the actual refined reference remains the direct evidence.

Table S17. All eight historical comparisons and both rules. “Gain bound” covers the required gain components; “full bound” also requires every noninferiority guard and the absolute floors. Earlier denotes the earlier-pulse protocol; T guard is temperature noninferiority. A radius below one is not a failed empirical comparison or proof of instability.

{{TABLE:reference-certificates}}

All four E/F current-and-power gain pairs admit a certificate at r = 1. The full device rule admits one for the earlier-pulse pairs only. The original-protocol radii are 0.9546 (seed29) and 0.6950 (seed43), both limited by temperature noninferiority; the earlier-pulse radii are 1.5317 and 1.2435. The narrow earlier-pulse seed43 phase rule has radius 0.1399, limited by S, although that rule passes for both references actually evaluated. Across all controls, nine of the sixteen rule instances have a sufficient certificate at r = 1; these are algebraic checks on shared data, not sixteen independent validations.

![Complete device-rule perturbation bounds](figures/fig11-complete-reference-certificates.png)

Figure S5. Sufficient perturbation radii for E against F/projected. The dashed line is the observed temporal-reference distance used as a budget, not a confidence threshold. Current and power gain conditions alone allow larger radii than the complete device rule. The complete empirical rule passes under both actual references in all four pairs, including those whose conservative radius is below one. No new reference or learned prediction enters this figure.

The expanded calculation identifies the limiting criterion without selecting a new checkpoint, threshold or comparator. It motivates measuring spatial-reference differences directly and cannot substitute for that experiment. `reference_certificates.py` reproduces this table and the component CSV from the saved scalar records. The small synthetic interval-corner check tests the algebra against the original max rules, not the physical model or empirical success rates.

## S15. Fixed-prediction spatial-reference experiment

### S15.1 Numerical change and common comparison space

Both protocols are solved on 240 × 120 cells with dt = 0.0003125 over [0, 2.5], saving every eighth step. The reference numerical algorithm, coefficients, initial-state formula, contact geometry, tolerances and finite pulse histories are inherited unchanged. Each trajectory takes 8000 main steps with a separate limit of 200000 internal linear solves. These are new numerical references, not new neural training or new physical cases.

All sixteen predicted field arrays and their original 160 × 80 electrical readouts are unchanged. For fine cells c_i and scoring cells C_j, use the exact intersection-volume restriction W. If v_i and V_j denote cell volumes, the following identities preserve constants and domain integrals:

$$ W_{ji}=|C_j\cap c_i|/V_j,\qquad W_{ji}\geq0,\qquad\sum_iW_{ji}=1,\qquad\sum_jV_jW_{ji}=v_i.\qquad(S12) $$

The fine V, T, phase and local Joule density are restricted by W. Their integral consistency is checked on the saved arrays. Terminal current and total power remain the native fine-reference outputs; recomputing them from restricted V would introduce another readout and is not done. The projected neural readouts also are not recomputed on a new grid. Thus the new comparison cannot establish neural electrical-readout grid independence or claim that the mapped fields solve the coarse discrete equations.

The physical heater edges align with faces at both resolutions. The two fine references are compared over the identical physical prefix before the earlier second pulse. Numerical validity and the actual solve counters are retained separately from prediction accuracy. Local deposition and total dissipation identities remain operator-consistency checks, not independent physical validation.

Table S18. Actual work in the two spatial references. O and S denote the original and earlier-pulse protocols. Counts are actual electric, thermal and phase linear solves; a main time step can contain multiple nonlinear blocks and solves. No model evaluation or new prediction projection is included.

{{TABLE:spatial-execution}}

Table S19. Spatial-reference differences from the time-refined 160 × 80 reference. Field discrepancies use the fixed scoring measure after restriction; terminal discrepancies use native reference traces. They are numerical differences, not bounds on continuum error.

{{TABLE:spatial-reference-deltas}}

### S15.2 Full endpoint comparisons and counterexamples

Table S20. Every fixed endpoint under the spatial reference, including both deterministic interpolants and all six continuations. Percentages multiply the corresponding normalized RMS errors by 100. Strict refers to the original rule evaluated with the mapped phase reference. It is not a native fine-grid qualification. Full S, voltage, bottom-current, local-heat errors and normalization data are in spatial-all-fixed-metrics.csv, which retains all three references and the separately reported errors using the original fixed denominators. Complete two-cycle records are in spatial-all-fixed-events.csv.

{{TABLE:spatial-fixed-endpoints}}

Table S21. All eight historical comparisons, both rules and all three references. The gain columns are relative error reductions under the spatial reference. The complete A/B flags include the original absolute floors and noninferiority tests. Rows are related comparisons, not independent statistical samples.

{{TABLE:spatial-historical-comparisons}}

Table S22. All phase-head continuation decisions under all three references. Matched A/B include the continued E_C control and the required parent noninferiority checks. A reference-specific strict crossing is kept separate from a reproducible matched phase or device gain. No threshold, endpoint or architecture is changed.

{{TABLE:spatial-continuation-decisions}}

Table S23. The previously reference-sensitive gated seed-43 continuation, with identical predicted fields and event times in all rows. The first-cycle recall requirement is 0.9 and the timing requirement is 0.005 for each cycle; these displayed components alone do not replace the complete strict rule. All other endpoint/cycle records remain in spatial-all-fixed-events.csv and their complete decisions in Table S22. The spatial result removes the earlier reference-specific strict crossing.

{{TABLE:spatial-strict-counterexample}}

![Native spatial-reference terminal trace differences](figures/fig13-spatial-native-traces.png)

Figure S6. Native fine-reference current and power minus the time-refined reference traces, with the original two protocols shown separately. Fields used for scoring are restricted, but the terminal quantities plotted here are not recomputed from those restricted fields. These traces contain no new model prediction.

### S15.3 Thresholding and restriction do not commute

The primary score thresholds W phi_h at 0.5. A separately named diagnostic restricts the fine active indicator instead. For the fixed coarse binary prediction P, define a = W 1(phi_h >= 0.5) and b = 1(W phi_h >= 0.5). The alternative support and symmetric difference integrate the fractional overlap with the same predicted set. The reverse triangle inequality gives the following bound in the fixed space-time measure mu:

$$ |S(P,a)-S(P,b)|\leq\int|a-b|\,d\mu.\qquad(S13) $$

This diagnostic interprets P as constant within each scoring cell. It does not evaluate the network on native fine points. The primary diagnostic reproduces the frozen scorer's S, overlap, predicted/reference support masses and recall before the alternative mapping is compared. Both mappings retain the original global trapezoidal time weights and heating-window selection. The alternative scores cannot replace a less favorable primary decision.

Table S24. Threshold-map discrepancy for every fixed object. S primary uses thresholded restricted phase; S indicator uses restricted fine active fraction. The common bound depends on the reference mapping, whereas the realized score change also depends on the fixed prediction. Full per-cycle masses and recall differences are retained in spatial-threshold-events.csv.

{{TABLE:spatial-threshold-mapping}}

![Threshold-map discrepancy and all cycle recall shifts](figures/fig14-spatial-threshold-mapping.png)

Figure S7. Report-only consequences of exchanging thresholding and restriction. All sixteen fixed objects are retained. Upper panel: observed S changes and the mapping bound. Lower panel: alternative-minus-primary recall changes in both cycles. These are not additional model results or new gate outcomes.

### S15.4 Reproduction and evidence boundary

The spatial extension is kept separately in outputs/runs/20260917-lf11-spatial-reference: native result files, mapped references, the restricted indicators, source snapshots, intents, terminal counters and complete scores. The original array archive remains unchanged. phk_v23_spatial_reference.py generates the two trajectories; spatial_analysis.py consumes only completed references and archived prediction arrays; spatial_report.py produces the tables and figures. No scientific execution occurs in the document build.

Two space resolutions at one fixed time step do not identify a reliable convergence order. Both use the same numerical algorithm, and field comparisons include a specified restriction. The experiment therefore extends the tested numerical-reference range without supplying an independent solver, continuum truth, zero-shot transfer or material validation. Stable strict capability, independent remaining-PDE necessity and isolated VJP causality remain separate claims.

The saved-data outcome is 4/4 complete historical E/F device passes under the spatial reference. Historical decision changes from the time-refined reference are: original seed 29, E/B_E, A: True to False; original seed 43, E/B_E, B: False to True; shorter seed 43, E/F, A: True to False. Spatial-reference strict objects are: none. Actual reference work totals 170979 internal linear solves across the two fixed trajectories. These statements are generated from the complete saved result tables, without selecting a favorable model or case.

## References

{{REFERENCES}}
