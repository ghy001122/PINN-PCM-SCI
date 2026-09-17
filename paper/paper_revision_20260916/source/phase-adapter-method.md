### 3.4 Matched development of the phase representation

The main elimination study leaves incomplete first-cycle support recall despite accurate electrical readouts. We test the hypothesis that a limited phase parameterization contributes to this mismatch. The hypothesis does not establish sigmoid saturation as its cause, nor imply that adding parameters must help. The two final earlier-pulse E states are used as separate parents. This is subsequent development on two already trained states, not another pair of clean initialization confirmations.

An unchanged continuation, E_C, is compared with an ordinary residual head, E_R, and a parent-interface-modulated residual head, E_I. These identifiers denote methods; the current error in the evaluation equation is a separate functional quantity. Let the original complete logit be ell_θ = logit(φ₀) + 8a(t)h_φ,θ. The residual R_ξ takes the original normalized coordinates as input and uses a 3-32-32-1 tanh MLP with 1217 trainable parameters. The output weight and bias are initially zero. E_R and E_I use identical initial residual tensors, with seeds 916029 and 916043 for the two parents. Their complete initial fields exactly equal those of E_C.

For E_I, a frozen copy of the parent's complete phase function defines

$$g=0.25+0.75\,[4\phi_{\rm parent}(1-\phi_{\rm parent})],\quad c_g=\sqrt{\mathbb E_\rho[g^2]},\quad \hat g=g/c_g. \qquad (21)$$

The positive floor leaves a correction path outside the parent's predicted interface, including possible missed regions. The scalar c_g is calculated once using the parent's original unlabeled calibration quadrature; it equals 0.2693107755 and 0.2705578194 for seeds 29 and 43. It controls an RMS amplitude, not every gradient norm or the effective optimizer step. The outputs are

$$\phi_R=\operatorname{sigmoid}(\ell_\theta+8aR_\xi),\quad \phi_I=\operatorname{sigmoid}(\ell_\theta+8a\hat gR_\xi). \qquad (22)$$

Only the gate's parameters are frozen. Its coordinate derivatives, including second spatial derivatives, remain in the phase residual. The two added residuals have equal trainable counts, but E_I has extra frozen parameters and extra function/coordinate-derivative evaluations; it is not equal to E_R in total model storage or work. No logit is recovered by inverting an already saturated phase prediction. One composed phase interface is used by the observation increment, conductivity, electrical solve, Joule deposition, thermal and phase equations, boundaries, initial conditions and inference. Thus the comparison changes representation while preserving the actual coupled PINN objective.

Residual parameterizations have established precedents [11], and gated mixing is already present in the modified-MLP background [2]. The present residual head is neither the original ResNet architecture nor a claim to invent gating. E_C-to-E_R assesses added capacity and its optimization effects. E_R-to-E_I assesses the particular frozen-gate parameterization, including its coordinate-derivative cost. A gain over E_C alone cannot establish an independent gate benefit.

### 3.5 Fixed-prediction reference perturbation

Both protocols receive an additional reference with the original algorithms and tolerances, the same 160 by 80 spatial grid, and half the integration step: 0.0003125 with saving every eight steps. Original references remain available. The 1001 saved times, predictions, ROI and event definitions are identical between the two scoring passes; no prediction is interpolated or reselected. New references are excluded from training and method selection. Each normalized error uses its own reference denominator, with a fixed-old-denominator diagnostic reported separately.

For an error in one common weighted norm, the reverse triangle inequality gives |e_new - e_old| <= δ, where δ is the norm of the reference difference. Consequently, the relative-gain margin obeys

$$m=0.9e_F-e_E,\qquad |m_{\rm new}-m_{\rm old}|\leq 1.9\delta. \qquad (23)$$

The same bound applies to active-set symmetric difference using δ_S, the measure of the two reference sets' symmetric difference. Normalized device margins use a fixed denominator for this bound; a changed denominator is reported separately. These bounds contextualize a narrow margin and do not prove that every threshold decision is robust. Temporal refinement alone does not establish spatial convergence or continuum accuracy.
