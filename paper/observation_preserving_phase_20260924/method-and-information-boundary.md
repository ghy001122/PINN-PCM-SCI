# Observation-preserving physics-informed phase completion

This is a development experiment on the existing synthetic two-dimensional device, short-spacing double pulse and B1 phase-observation gap. It uses the old B1 E/29 endpoint, including its temperature adapter and complete phase latent field, as a frozen base. The physical model, observations, geometry and original scoring definitions are unchanged. This is offline reconstruction with post-gap phase observations; it is not forecasting, formal OOD or experimental material validation.

## An observation-equivalent family

Let W=[1.01,2.02] be the existing phase-observation gap. Its intersection with the known strictly zero-voltage interval is D=(a,b)=(1.36,2.02). For s=(t−a)/(b−a), set

\[
g_D(t)=\begin{cases}64s^3(1-s)^3,&a<t<b,\\0,&\text{otherwise}.\end{cases}
\]

The gate and its first two time derivatives vanish at both endpoints. For the complete base latent variable ψ_base, define

\[
T_\eta=T_{\rm base},\qquad
\psi_\eta=\psi_{\rm base}+8g_D h_\eta,\qquad
\phi_\eta=\sigma(\psi_\eta).
\]

**VERIFIED analytical property under the stated observation and electrical assumptions.** With positive conductivity, grounding and zero applied voltage, the discrete electrical solve has V=0 and hence I=P=q=0. Outside D, the phase field is unchanged; inside D, phase labels are absent and the temperature field is fixed. Therefore the complete available-observation prediction O(u_eta) equals O(u_base), and all electrical ports remain unchanged for finite corrections. This preserves the base predictions, including any pre-existing observation error. It does not assert exact agreement with labels or uniqueness/nonuniqueness of solutions of the full coupled PDE.

The finite family is a model-specific adaptation of data-consistency ideas, with prior work explicitly identified in [SOURCES.md](SOURCES.md). It is not a linear projection of an arbitrary nonlinear observation operator. No global inverse-problem convergence result is claimed.

For a diagnostic only, δψ=±g_D[(1−x²)4z(1−z)]³ also preserves phase boundary values and normal derivatives. The actual E/29 checkpoint yields nonzero interior phase changes (maximum 0.01443 at t=1.55), with zero measured changes in visible phase predictions, boundary traces, T, V, q and ports. These manufactured finite perturbations are not claimed to solve the complete PDE or improve prediction accuracy. The trainable candidate does not impose this additional spatial factor, so its phase Neumann boundary penalty remains active.

## Fixed-temperature thermal restriction

The original finite-volume thermal residual remains

\[
r_{T,i}=\dot T_i+L\dot\phi_i+\gamma T_i-\alpha F_i(T)/|K_i|-\beta q_i,
\qquad L=0.05,
\]

where F_i is the inherited heat-face flux. On D, q=0. Fixed T and unchanged endpoint phase imply

\[
\int_a^b r_{T,i}\,dt=C_i
=T_i(b)-T_i(a)+L[\phi_i(b)-\phi_i(a)]
+\int_a^b[\gamma T_i-\alpha F_i(T)/|K_i|]dt,
\]

and Cauchy–Schwarz gives (b−a)^−1∫r_T,i²dt≥[C_i/(b−a)]². The exact local difference is r_T,new−r_T,base=L(φ_t,new−φ_t,base); omitting this latent contribution would change the problem.

**VERIFIED sampled diagnostic.** For 64 original-grid cells selected with seed 740329, the mean lower bound is 0.00292226, compared with the base mean raw thermal residual square 0.01351966 (64-point quadrature). The relative L2 change in C from 32 to 64 points is 2.66×10^−5. The observed latent-difference identity error is 4.22×10^−16. This is a fixed-cell, fixed-interval numerical diagnostic; it neither establishes continuum convergence nor proves the completion target infeasible.

## Physical objective and direct controls

The neural correction N is a tanh 3→32→32→1 network with 1217 trainable parameters, seed 2901 for its hidden layers and zero final weights/bias. G has the identical hidden initialization and frozen base, replacing g_D by 1−exp(−t/0.35). It is an ordinary full-time phase correction. S uses the same g_D as N and an open-clamped cubic tensor B-spline with 41×21×9 zero-initialized coefficients (7749 parameters). S is a deliberately expressive traditional control, not a teacher or a replacement method selected after scoring.

All use the original raw phase equation

\[
r_\phi=\phi_t-M(T)\{\epsilon^2\Delta\phi-2B\phi(1-\phi)(1-2\phi)
+6D_\theta(T-T_c)\phi(1-\phi)\},
\]

and the common objective

\[
\mathcal L=\mathcal L_{obs}/a_E+0.1/b_E\,[5\mathcal L_{BC}+\mathcal L_{IC}+(J_T+J_\phi)/3],
\quad J_T=\mathbb E(r_T/4)^2,\quad J_\phi=\mathbb E(r_\phi/5)^2.
\]

The original saved calibration is a_E=0.00014539990909531785 and b_E=0.502532227557215. No new calibration or ramp is applied. Physical time remains uniform on [0,2.5]; splitting at 0, .35, 1.01, 1.36, 2.02 and 2.5 preserves segment masses .14, .264, .14, .264 and .192. N/S may omit only terms constant in their correction parameters. Their fixed initial restricted objective is 0.01866134, with constant offset 0.25678728 to the complete initial objective 0.27544862. A lower reduced loss is not evidence of superior fitting. G recomputes powered-time V and q and retains the original electrical adjoint.

The base parameters are frozen while coordinate derivatives are retained. Cached base values are detached only after evaluating their derivatives. The composite derivatives use φ_t=φ(1−φ)ψ_t and Δφ=φ(1−φ)[Δψ+(1−2φ)|∇ψ|²], including the complete spatial initial field and startup. B-spline evaluation screens out-of-support times before evaluating the basis and combines only the 64 locally active tensor products. No corrected output clipping, reference teacher, residual-coordinate substitution or global model modification is introduced.

## Budget, validation and interpretation

The fixed execution order is G→N→S. Each branch starts from zero correction and receives 600 Adam updates followed by at most 200 complete strong-Wolfe L-BFGS objective/gradient evaluations. Line-search trials count and the last accepted state is restored at budget exhaustion. Each Adam batch has eight stratified times in D with 64 original-grid cells and four points per boundary side/time. G additionally samples two times in each complementary segment with 64 cells and the original four-time importance-weighted observation batch. The shared fixed D pool has 32×128 cells; the independent D audit has 64×256 cells. No reference-based stopping is allowed. The reference is used only for the pre-training necessary feasibility bound and for scoring after all endpoints are locked.

**VERIFIED implementation scope.** Twelve focused/inherited checks cover actual-checkpoint zero correction, finite observation invariance, complete latent derivatives, heat identity, original loss equality, full/reduced gradients, powered G adjoint, spline derivatives/coefficients, importance weights and L-BFGS accounting. Three complete zero-update profiles and a finite parameter intervention establish a nonzero physical gradient while N's observation gradient is exactly zero. Two local G profile attempts had engineering failures (metadata then RAM exhaustion); their records are retained and no optimizer step occurred in those attempts.

**Execution deviation.** The training entrypoint failed to forward the requested CUDA device. The already-started trajectories are retained, and all three branches train on the same cloud CPU with four Torch threads. A local entrypoint correction is kept separate from the executed source archive. CUDA is used by the later audit/readout entrypoint. Costs therefore describe this CPU training schedule, not GPU training speed. No trajectory was restarted to conceal the deviation.

The main A_w test requires both the W phase RMS and set error to fall by at least max(10% of control error, the inherited absolute tolerance), while ET/EI/EV retain their original noninferiority tests. Physical completion additionally requires at least 10% lower independent-D raw phase residual square and no more than max(5%,1e−12 absolute) degradation in thermal residual square or phase BC. The full original raw audit is reported separately. Heating-window onset/recall/precision remain unchanged for N/S, so the base's strict event failure cannot be repaired by this support. State gains, physical qualification, observational invariance and neural-specific benefit are distinct conclusions.
