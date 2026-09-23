# Relative phase dynamics and local temporal moments

Status: **VERIFIED bounded negative development result — NO_INCREMENT_WITHIN_SCREEN_BUDGET**. Independent method improvement was not established. This working section describes the actual implementation of task PCM-20260922-RELATIVE-PHASE-MOMENTS-01. The observation condition is offline reconstruction with the second-cycle phase labels removed; voltage and temperature observations remain visible. It is neither forecasting nor formal out-of-distribution testing.

The physical system, output representation and temperature adapter are unchanged. For the complete phase latent variable,

\[
\psi=\operatorname{logit}(\phi_0(x,z))+8\left(1-e^{-(t-t_0)/0.35}\right)h_\phi(x,z,t),\qquad \phi=\sigma(\psi),
\]

the initial phase is clipped exactly as in the inherited implementation. Differentiation includes the spatial initial field and the time-dependent startup factor. With \(s=\phi(1-\phi)\),

\[
F_\psi=M(T)\left\{\epsilon^2\left[\Delta\psi+(1-2\phi)|\nabla\psi|^2\right]-2B(1-2\phi)+6D(T-T_c)\right\},
\qquad r_\psi=\partial_t\psi-F_\psi.
\]

For a smooth finite latent field, the original phase residual satisfies \(r_\phi=s r_\psi\). This identity identifies a state-dependent weighting of relative dynamics; it does not identify the cause of an observed optimization failure. The complete latent residual was already proposed in the project's September 10 planning documents and is included here as a direct control.

To retain finite sensitivity beyond the existing observation transformation scale, the candidate uses

\[
\zeta_\delta=\log(\phi+\delta)-\log(1-\phi+\delta),\qquad
A_\delta=\frac{(1+2\delta)s}{s+\delta+\delta^2},\qquad
F_\zeta=A_\delta F_\psi,\qquad r_\zeta=A_\delta r_\psi.
\]

Here \(\delta=10^{-8}\) is the inherited numerical clipping scale for phase observations, not a sensor-noise model, material constant or event threshold. The implementation uses log-sigmoid and log-add-exp expressions instead of reconstructing the latent from a rounded phase value. All derivatives through \(A_\delta\), \(M(T)\) and the temperature head are retained. The original output phase and evaluation definitions do not change. Although the coordinate transformation has a positive derivative in exact arithmetic for finite latent values, weighting weakens again in the deep tails; no elimination of all near-zero spurious solutions is claimed.

For a fixed spatial point and interval \([a,b]\), let \(h=b-a\), \(\xi=(t-a)/h\), \(p_0=1\) and \(p_1=\sqrt3(2\xi-1)\). Unit-interval Gauss weights sum to one. For \(y=\phi\) or \(\zeta_\delta\), the endpoint form is

\[
D_0[y]=\frac{y_b-y_a}{h}-\sum_qw_qF_y(t_q),
\]

\[
D_1[y]=\frac{\sqrt3}{h}\left[(y_b-y_a)-2\sum_qw_q(y(t_q)-y_a)\right]
-\sum_qw_qp_1(\xi_q)F_y(t_q).
\]

Both endpoint values are evaluated by the current network and differentiated. They are not labels or frozen teacher values. The formulas are adapted from interval residual regularization; the first-moment term uses a Legendre test function. Interval residuals already have a direct precedent in [Feng et al., §3.1, equations 10–20](https://arxiv.org/html/2503.23729v1), and Legendre testing and integration by parts have precedent in [VPINNs](https://arxiv.org/abs/1912.00873). This implementation does not reproduce either paper in full.

Writing \(P_y=\sum_qw_q(r_y/5)^2\), the full phase target is

\[
M_\zeta=\tfrac12P_\zeta+\tfrac12\big[(D_0[\zeta]/5)^2+(D_1[\zeta]/5)^2\big].
\]

With exact integration, \(D_\ell=h^{-1}\int_a^bp_\ell r_y\,dt\). Orthogonality and Bessel's inequality give \(P_\zeta/2\le M_\zeta\le P_\zeta\). This is a continuous residual-norm relation. It is not a device-error bound, an improvement in nonlinear conditioning, or a guarantee for finite collocation. A second Legendre mode has zero zeroth and first moments, which motivates retaining the local squared residual. The method continues to use time and second-order spatial automatic differentiation. Numerical quadrature is checked independently; random panel/space sampling estimates the specified discrete Gauss objective. [Saleh et al.](https://proceedings.mlr.press/v235/saleh24a.html) motivate distinguishing an unbiased integral estimator from the loss obtained by squaring it.

The eight arms retain common observation, boundary and initial losses. D removes only internal thermal/phase terms while retaining electrical elimination and feedback. P adds the inherited thermal term and raw phase residual on the new shared panel support. L and R use complete and finite logit coordinates, respectively; I uses a raw zeroth-moment mixture; RI combines the finite coordinate and zeroth moment; RIM also includes the first moment. G rescales raw phase pressure by a fixed scalar chosen to match RIM's initial phase-gradient norm. L/R/I/RI/RIM match raw phase loss values at the same legal parent. Those scalar calibrations are fixed, reference-blind and do not imply matched Adam updates.

The panel boundaries follow known waveform knots. Two prescribed maximum widths, 0.025 and 0.10, carry equal mass, with the original four physical-window masses retained. Panels are sampled in proportion to duration, and spatial points are uniform original-grid cell centers. No interface prediction, hidden label or reference field controls the panels. The new phase evaluations require no additional electrical solves. The inherited thermal balance, including latent heat and local Joule deposition, remains intact.

For exact reproduction, panel counts use the implemented FP64 ceiling of each segment-length/width ratio. In particular, (1.06−1.01)/0.025 evaluates just above two, so that segment contains three equal fine-scale panels. The maximum-width and mass rules still hold; every arm uses this same frozen discretization and the stored panel coordinates. No panel boundaries are changed after training starts.

The development comparison uses one initialization and a fixed budget of 600 Adam updates and at most 100 complete L-BFGS objective/gradient evaluations per arm. Every line-search trial counts; an interrupted trial is rolled back. The original missing-window improvement test, full-history tests, event definitions and outside-window costs are reported separately. Numerical readout levels and reference variants do not increase the number of independent trainings. Any positive mechanism attribution still requires the separately approved confirmation stage.

The related operator-conditioning analysis of [De Ryck et al.](https://arxiv.org/abs/2310.05801) does not supply a convergence guarantee for this nonlinear, state-dependent residual metric. A method contribution here would require an independently reproducible improvement beyond D, the matched raw control and the nearest mechanism controls, with explicit added cost.

Numerical qualification and interpretation of the fixed calibration: **VERIFIED.** The legal parent and a fixed manufactured smooth field passed the prescribed 8/16/32-point quadrature checks, retaining eight points for all phase arms. At the parent, the largest 8-to-16 change was approximately 8.2×10⁻⁸ in objective value and 8.6×10⁻⁷ in gradient norm. Twenty-one focused and inherited tests passed, including the complete latent chain rule, finite-coordinate derivatives, endpoint moment identities and preservation of the thermal block.

On the independent full optimization pool with λ=0.1, the weighted phase contribution was 5.4308×10⁻⁵ for P and 2.1918×10⁻⁵ for RIM, respectively 0.00510% and 0.00206% of their complete objectives. Initial loss-value matching applies to the calibration pool, not every independently drawn pool. These percentages describe loss values; they are not gradient fractions or evidence that the phase terms cannot affect optimization. The prescribed normalization was retained throughout the screen.

On the parent calibration pool, the zeroth- and first-moment squares represented approximately 98.2702% and 1.6328% of the finite-coordinate point residual square, giving uncalibrated Mζ/Pζ≈0.999515. Thus, these short-panel targets are already numerically close at the parent. This is a diagnostic of the declared discretization and state, not proof that their gradients or training paths coincide. Neither the initial scale nor the moment decomposition licenses a post-hoc weight or panel-width search.

Data-availability wording for the next working manuscript: **The September 22 repository release includes selected B1 results, code and manuscript evidence. Complete native space-time arrays remain locally archived and have not been publicly deposited. The present phase-moment development results are local until separately authorized for publication.** This updates availability without altering frozen experimental results.


## Completed development result

All eight fixed endpoints and native 160×80 readers completed, with 600 Adam updates and 100 complete L-BFGS evaluations per arm. RIM reduced missing-window phase RMS error by 1.918% and set error by 2.202% relative to D; the corresponding reductions relative to the matched raw control P were 2.264% and 2.633%. Neither comparison passed the original simultaneous 10% improvement criterion. The temperature/electrical noninferiority checks passed, and no outside-window cost flag was raised. All eight strict two-cycle tests failed.

RIM improved phase RMS by only 0.139% over L, 0.295% over RI and 0.718% over G. These one-initialization differences establish neither statistical significance nor the necessity of finite clipping or the first moment. The original phase-residual audit for RIM increased by approximately 0.450% relative to D and 0.586% relative to P. Both the prescribed endpoint 16/32 quadrature audit and a supplementary, pre-scoring 8/16 check passed; numerical invalidity is not the reason for the failed improvement gate.

For RIM, second-cycle onset error was 0.00035 and the original recovery fraction was 1, but recall, precision and active-mass ratio were 0.641734, 0.824945 and 0.777911. Its active-area peak occurred at 1.5425 instead of the reference 1.3475, and after-pulse false-positive area contributed 78.24% of its window set error. Near-correct onset therefore did not establish accurate phase evolution. These observations preserve the distinction between continuous reconstruction, limited electrical function and strict event capability.

The screen terminates without a confirmation candidate. The result is conditional on this physical proxy, observation condition, shared parent, fixed weighting, panel discretization and optimization budget. It does not establish that PINNs or interval residual methods are generally ineffective. The old B1 findings and full-label counterexamples remain separate evidence. See [complete tables and figures](results.md).
