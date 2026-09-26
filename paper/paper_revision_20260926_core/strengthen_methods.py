"""One-time source revision from inspected executed code; no numerical reruns."""
from pathlib import Path
HERE=Path(__file__).resolve().parent
p=HERE/'source/supplement.md';text=p.read_text(encoding='utf-8')
assert 'S21.1 Executed parent' not in text
s21=r'''
### S21.1 Executed parent and common objective

This screen uses the B1 observation-only parent for seed 29, not the accepted B1 E endpoint and not the older full-label parent. Phase labels in W=[1.01,2.02] are excluded before normalization and sampling. All eight arms start from the same parent with fresh optimizer state. The trainable temperature and phase heads retain the original 64-wide, four-layer representation and initial-condition/startup transformation. The electrical potential is obtained by the same differentiable finite-volume solve. The original 80 by 40 training grid, thermal flux construction, latent heat, boundary conditions and observation scales remain fixed. The control D omits both interior thermal and phase penalties; it still uses the electrical solve, observations, boundary terms and initial condition. Consequently, a candidate-versus-D result alone is not an isolated phase-residual contrast; P is the direct raw-phase control.

Writing C for the common observation/boundary/initial objective, the actual objectives are

$$ C=L_{obs}/a+\lambda(5L_{BC}+L_{IC})/b. $$

$$ L_D=C,\qquad L_j=C+\lambda(J_T+c_jJ_j)/(3b). $$

The common scales inherited from the clean B1 parent are a=0.00014539990909531785 and b=0.502532227557215. They are not recalibrated at the accepted E endpoint or per arm. The thermal residual is divided by 4; the phase residual and moment defects below are divided by 5 before squaring. Adam uses 600 updates, learning rate 1e-4, betas (0.9,0.999), epsilon 1e-8 and one norm-10 clip after all groups accumulate. Lambda rises linearly to 0.1 over 200 updates. Each arm then uses at most 100 complete strong-Wolfe L-BFGS evaluations with no gradient clipping. All eight endpoints are retained; this is one-initialization development, with no formal OOD or independent confirmation.

### S21.2 Relative residuals and panel moments

Let psi be the complete phase latent and phi=sigmoid(psi). Derivatives include the spatial initial field and temporal startup factor. Define s=phi(1-phi), delta=1e-8 and zeta=log[(phi+delta)/(1-phi+delta)]. The implementation computes these with stable log-sigmoid expressions rather than dividing by a rounded phase. The phase sources and residuals are

$$ F_\phi=M(T)[\varepsilon^2\Delta\phi+\phi(1-\phi)\{-2B(1-2\phi)+6D(T-T_c)\}],\quad r_\phi=\phi_t-F_\phi. $$

$$ F_\psi=M(T)[\varepsilon^2\{\Delta\psi+(1-2\phi)|\nabla\psi|^2\}-2B(1-2\phi)+6D(T-T_c)],\quad r_\psi=\psi_t-F_\psi. $$

$$ A_\delta=(1+2\delta)s/(s+\delta+\delta^2),\quad F_\zeta=A_\delta F_\psi,\quad r_\zeta=A_\delta r_\psi. $$

For a panel [a_p,b_p] of width h and normalized coordinate xi, angle brackets denote its normalized Gauss integral. With y equal to phi or zeta, both panel endpoints remain differentiable:

$$ d_0=(y_b-y_a)/h-\langle F_y\rangle. $$

$$ d_1=\sqrt{3}\{y_b-y_a-2\langle y-y_a\rangle\}/h-\langle\sqrt{3}(2\xi-1)F_y\rangle. $$

Table S21m. Exact phase penalties and frozen calibration multipliers. P_y denotes the weighted mean square of r_y/5, and M_k the weighted mean square of d_k/5. The half coefficients are part of the implemented objectives, not additional tuning parameters.

| Arm | Phase penalty J_j | Multiplier c_j | Direct comparison purpose |
|---|---|---|---|
| D | absent; thermal penalty also absent | not applicable | data/electrical/boundary control |
| P | P_phi | 1 | raw phase control |
| L | P_psi | 0.00034233113105873697 | unregularized latent residual |
| R | P_zeta | 0.000733832633996526 | regularized relative residual |
| I | 0.5 P_phi + 0.5 M_0(phi) | 1.043615650726199 | raw integral increment |
| RI | 0.5 P_zeta + 0.5 M_0(zeta) | 0.0007402349322298227 | relative integral increment |
| RIM | 0.5 P_zeta + 0.5 M_0(zeta) + 0.5 M_1(zeta) | 0.0007341888677207234 | additional first Legendre moment |
| G | P_phi | 0.5083033609173053 | initial phase-gradient-norm control |

For L/R/I/RI/RIM, c_j is the parent raw-phase loss divided by the corresponding parent penalty. G instead matches the norm of the already value-scaled RIM phase gradient: c_G=norm(c_RIM grad J_RIM)/norm(grad P_phi). The recorded parent raw loss is 0.0002802072203780491; its phase-gradient norm is 0.008235460975060553 and the G target norm is 0.004186112492326587. This is a one-time calibration, not gradient balancing during training.

The four temporal windows have masses 0.14, 0.264, 0.14 and 0.456. Panels are split at all drive knots 0,0.05,0.27,0.35,1.01,1.06,1.28,1.36,2.5. Two target widths, 0.025 and 0.1, receive equal mass within each window; panel selection is proportional to length. Each panel draws 16 spatial cells uniformly with replacement. Adam draws one panel per window/scale; the complete phase support fixes eight per window/scale. Normalized Gauss weights integrate inside each panel; spatial means and panel mass then define the loss. These phase panels are separate from the unchanged thermal/boundary pool of 32 fixed times and 128 cells per time. The executed phase order is 8. Parent 8/16/32 and endpoint sensitivity checks, including the retained 16/32 and supplementary 8/16 comparisons, are numerical qualification rather than extra trained arms. The original tolerances and all adverse outcomes remain unchanged.

The definitions follow the actual phk_v23_phase_moments and phk_v23_phase_moments_run sources and frozen calibration. Interval regularization and Legendre testing are attributed to the original sources already listed in the references; their adaptation does not establish a new validated method. The single-parent comparison cannot turn eight objectives into eight independent replications.

### S21.3 Complete results
'''
s22=r'''
### S22.1 Correction family and information boundary

B0 is the accepted B1 E/29 endpoint. Its complete parameters are frozen. Every correction starts with zero output and changes only the phase latent: phi=sigmoid(psi_B0+delta_psi). N and S use D=(1.36,2.02), s=(t-1.36)/0.66, and the compact gate

$$ g_D(t)=64s^3(1-s)^3\quad(1.36<t<2.02),\qquad g_D(t)=0\quad\mathrm{otherwise}. $$

This gate and its first two derivatives vanish at the endpoints. N has delta_psi=8 g_D n_theta(x,z,t). The correction network has two 32-unit tanh hidden layers, three normalized inputs, one scalar output and 1217 parameters. Its output layer is zero-initialized using correction seed 2901. G uses the same network and amplitude but replaces g_D by the original global startup gate 1-exp[-(t-t0)/tau_start]. It is a global correction control, so it does not have N's dark-window observation invariance.

S uses delta_psi=8 g_D sum(c_ijk B_i(x)B_j(z)B_k(s)), with open clamped cubic bases of dimensions 41 by 21 by 9 and 7749 initially zero coefficients. The physical domains are x in [-1,1], z in [0,1], s in [0,1]. Only the four active bases per axis are evaluated; first derivatives and the spatial Laplacian include the gate and physical-coordinate chain factors. The spline is never evaluated outside its support. No smoothing, replacement temperature, future phase, or reference phase enters these parameterizations.

N/S preserve T everywhere and phase outside D. Because the drive is zero in D, their electrical readout is unchanged under the adopted quasi-static model. This is an observation/interface property, not proof of accurate phase, physics feasibility, online prediction, or acceleration. G can change phase during powered intervals and therefore requires the corresponding differentiable electrical solve. All methods retain the original latent heat and raw phase equation; there is no label declaring phase inactive after power-off.

### S22.2 Executed objective and independent qualification

G minimizes the full inherited objective at fixed lambda=0.1, with the unchanged B1 a and b stated in S21. N/S minimize only its variable D contribution: the raw thermal residual, raw phase residual and phase boundary penalty. The common form is

$$ H=L_{obs}/a+0.1\{5L_{BC}+L_{IC}+(J_T+J_\phi)/3\}/b. $$

The residual scales remain 4 and 5. Phase boundary penalties are summed over all four sides with the inherited division by 13; the entire bottom boundary is included. N/S omit only terms constant in their trainable coefficients. The measured constant offset is 0.2567872764924906: initial full H=0.2754486191841118 and restricted H=0.0186613426916212. Full-objective checks restore these constants. Minimizing their scalar sum can compensate one equation's deterioration by another term's decrease, so lower H alone is not physical qualification.

The time pool separates [0,0.35], [0.35,1.01], [1.01,1.36], D and [2.02,2.5], with weights equal to length/2.5. The D and complementary samplers have distinct fixed streams; the complete pool and independent D audit pool remain frozen. Each branch uses 600 Adam updates, learning rate 1e-4, norm-10 clipping, then at most 200 complete L-BFGS evaluations. Only correction coefficients are updated. All three branches actually trained on CPU after the original launch failed to propagate the requested device; later GPU audits and native readouts do not retroactively make that training GPU-based. The executed source snapshot, telemetry and deviations are retained.

The primary completion decision applies the original A_w improvement and noninferiority rules against B0. Independent D physics qualification separately requires at least 10% reduction of raw phase mean square, no more than 5% increase of raw thermal mean square, and no more than 5% increase of the phase boundary component, with original numerical floors retained. Numerical integration checks, interface invariance, predictive improvement, and equation-wise qualification are distinct. None may substitute for another or be added into a total score. All N/G/S arms failed the claimed completion increment and independent physical qualification; stage 4 was not triggered.

Visible training data and known physics are the optimization inputs. Saved reference fields were examined during development, feasibility assessment and interpretation, but were not used in these correction losses or for endpoint selection. The later zero-update diagnostic reused locked checkpoints. Its reported residual arrays permit reaggregation, not a claim that neural AD has been independently rerun. This distinction also applies to the transfer package.

### S22.3 Complete results and diagnosis
'''
text=text.replace('## S21. Complete relative-residual and time-moment development\n',
 '## S21. Complete relative-residual and time-moment development\n'+s21+'\n')
text=text.replace('## S22. Observation-preserving controls and saved-checkpoint diagnosis\n',
 '## S22. Observation-preserving controls and saved-checkpoint diagnosis\n'+s22+'\n')
p.write_text(text,encoding='utf-8')
p=HERE/'source/manuscript.md';text=p.read_text(encoding='utf-8')
old='The curated repository through [commit e2e14b5](https://github.com/ghy001122/PINN-PCM-SCI/tree/e2e14b5ce390de930646e1cba9a606a8191cff80) includes selected manuscript, B1, bounded-correction and diagnostic evidence. This integrated review version and its new conditional diagnostic are a subsequent local delivery.'
new='The curated repository through [commit 90508f05](https://github.com/ghy001122/PINN-PCM-SCI/tree/90508f05a6f233a485413c7589cc74420015cbea) includes the integrated manuscript and selected B1, bounded-correction, diagnostic and conditional-evolution evidence. The present revision and mixed-measure coverage comparison are subsequent local deliverables.'
assert old in text;text=text.replace(old,new)
p.write_text(text,encoding='utf-8')
print('ACTUAL_S21_S22_METHODS_AND_ACCESS_STATEMENT_REVISED')
