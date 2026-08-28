# Field-Selective Phase–Joule-Aware Multi-Frequency PINNs for Localized Electro-Thermal Phase Dynamics

> Live Method-MVP manuscript. Status: `METHOD_PREWRITTEN_RESULTS_PENDING`.
> Bracketed result tokens are machine-fill targets and must not be replaced without
> an indexed run artifact.

## Abstract

Physics-informed neural networks (PINNs) face a particular imbalance in
electrically driven phase-change devices: the electric and thermal fields occupy
the full device, whereas the moving phase structure can be confined to a small
fraction of the space-time domain. We introduce a field-selective,
phase–Joule-aware anisotropic multi-frequency PINN (FS-PJAMF-PINN) for a coupled
two-dimensional electric, thermal, and phase-field system. The architecture gives
the potential a low-to-mid-frequency representation while assigning broader,
direction-dependent frequency bands to temperature and phase. A physics-only
collocation policy retains a nonzero quasi-random floor and combines residual,
phase-interface, and Joule-density scores, preventing the localized region from
being missed without using reference labels. Four causal windows preserve both
driven and recovery dynamics across two pulses. We evaluate the method against a
strong raw PINN, frequency-only and sampler-only ablations, and an equal-compute
raw control using fixed finite-volume reference carriers. [RESULT_SUMMARY]. The
study establishes [SUPPORTED_CLAIM], while explicitly limiting its evidence to
case-specific numerical robustness rather than experimental or continuum-level
validation.

## 1. Introduction

Physics-informed neural networks embed differential-equation residuals in the
training objective and have become a widely used mesh-free framework for forward
and inverse problems [1]. The difficulty of a multiphysics PINN is not determined only by the number of
equations. In electrically driven phase-change devices, current flows through the
whole domain, heat diffuses over a comparatively broad support, and phase change
may nevertheless occur in a narrow region near a heater. Uniform collocation and
a single shared spectral representation therefore spend most of their capacity on
the smooth bulk while undersampling the event that controls device behaviour.

Recent phase-field PINNs combine hard constraints, Fourier features, staggered
training, and adaptive sampling to address stiff interfaces [2,3]. Residual
adaptive networks [4], causal training [5], and interface-oriented causal
refinement [6] provide complementary optimization and support-allocation ideas.
However, electrically driven phase-change devices add a state-dependent elliptic
field and a localized Joule source to the thermal/phase coupling. Heat-conduction
phase-change PINNs [7] do not by themselves close this electric--thermal--phase
chain, while detailed phase-change-memory simulation [8] motivates treating the
local electrical and thermal support as part of the method design.

This work asks a deliberately bounded question: can a field-selective
representation and a label-free, physics-informed sampling mixture improve the
reconstruction of localized, two-pulse phase dynamics at comparable training
cost? We study a fixed two-dimensional wall-cell benchmark whose finite-volume
implementation produces a localized phase event, recovery, and a second event.
The reference is treated as a fixed discrete numerical target. Resolution
sensitivity is reported separately and is not relabelled as a continuum oracle.

Our contributions are:

1. a three-field PINN whose spectral allocation follows the expected regularity
   of potential, temperature, and phase instead of forcing one representation on
   all outputs;
2. a collocation mixture combining quasi-random coverage, PDE residual,
   phase-interface, and Joule-density priorities while maintaining a strict
   full-domain sampling floor;
3. a causal replay schedule aligned with pulse drive and recovery windows; and
4. an attribution-oriented evaluation against representation-only,
   sampling-only, strong raw, and equal-compute controls on development and sealed
   stress cases.

The claims are conditional on measured evidence. If the combined method does not
beat its strongest component under the frozen decision rule, the paper reports no
attributable combined gain rather than changing the method after viewing sealed
results.

## 2. Physical problem and numerical reference

### 2.1 Coupled device model

The rectangular device domain is

\[
(x,z)\in[-1,1]\times[0,1],\qquad t\in[0,2.5].
\]

The dimensionless potential \(v\), temperature \(\theta\), and phase field
\(\phi\) satisfy

\[
\nabla\!\cdot\!\left[\sigma(\theta,\phi)\nabla v\right]=0,
\]

\[
\theta_t+L_r\phi_t=\alpha\nabla^2\theta-\gamma\theta
+G\sigma(\theta,\phi)|\nabla v|^2,
\]

\[
\phi_t=M(\theta)\left[\epsilon^2\nabla^2\phi
-\partial_{\phi}W(\phi,\theta)\right].
\]

Conductivity is coupled to both temperature and phase,

\[
\sigma(\theta,\phi)=\exp\!\left[
\log(r_\sigma)\,\phi^2(3-2\phi)+a_T\theta
\right],
\]

and mobility changes smoothly around the transition temperature,

\[
M(\theta)=M_c+(M_h-M_c)
\operatorname{sigmoid}\!\left(
\frac{\theta-\theta_{\mathrm{tr}}}{w_M}
\right).
\]

The phase potential derivative is

\[
\partial_\phi W=
2B\phi(1-\phi)(1-2\phi)
+6A_T(\theta_{\mathrm{tr}}-\theta)\phi(1-\phi).
\]

The top electrical boundary follows a two-pulse waveform. A localized grounded
heater occupies the lower boundary; the remaining electrical boundary is
insulating. Temperature is fixed at zero on the top and obeys Robin cooling on
the sides and bottom. The phase field has zero normal flux. The initial
temperature and potential are zero, and the initial phase contains a small smooth
seed near the heater. All numerical values and waveform breakpoints are fixed in
the machine-readable program contract.

### 2.2 Reference identity and separation of roles

Reference trajectories are generated by a Cartesian cell-centred finite-volume
solver with harmonic face conductivity. The nominal extra-fine trajectory is a
development-only target: it may score a candidate but is never provided to the
training loss, adaptive sampler, or network input. Narrow-interface and
wide-heater extra-fine trajectories are generated and hash-sealed before method
selection, then remain unread until the candidate and decision rule are frozen.

This protocol prevents stress-case feedback into architecture or hyperparameters.
Because the cases are preselected perturbations rather than samples from a
population, their evidence is described as case-specific robustness, not
out-of-distribution generalization.

## 3. Method

### 3.1 Field-selective anisotropic multi-frequency representation

Let \(\xi=(x,z,t)\) denote normalized coordinates. A shared low-frequency trunk
produces a base feature vector. The potential head receives low-to-mid-frequency
features because the elliptic field is spatially smooth away from material
transitions. Temperature and phase heads additionally receive anisotropic Fourier
features

\[
\Gamma_f(\xi)=
\left[\sin(2\pi B_f\xi),\cos(2\pi B_f\xi)\right],
\]

where the spatial and temporal scales in \(B_f\) are selected from a small,
predeclared candidate set. The phase head receives the broadest band; the thermal
head receives an intermediate band. This allocation is field-selective: a
high-frequency correction is not broadcast to all physical outputs.

Hard transformations enforce key initial and range structure. Temperature uses a
factor that is zero at \(t=0\) and at the top boundary. Phase is represented in
logit space relative to the prescribed initial seed, keeping \(0<\phi<1\) while
matching the initial condition. Remaining mixed boundary conditions are imposed
by residual losses.

### 3.2 Physics residual and automatic differentiation

The training objective contains the three strong-form residuals and the complete
mixed boundary conditions. Only the required diagonal second derivatives
\(v_{xx},v_{zz},\theta_{xx},\theta_{zz},\phi_{xx},\phi_{zz}\) are evaluated;
mixed Hessian entries are not part of this PDE. The electric residual is computed
in conservative differential form, so gradients of the state-dependent
conductivity remain in the graph. Joule density is

\[
q_J=\sigma(\theta,\phi)(v_x^2+v_z^2).
\]

No finite-volume field or label occurs in the physics-only objective.

### 3.3 Phase–Joule-aware collocation with a global floor

At each refresh, a quasi-random candidate pool is scored without reference data.
The next interior batch contains fixed fractions

\[
(w_u,w_r,w_\phi,w_J)=(0.35,0.25,0.25,0.15),
\]

for fresh Sobol points, high-residual points, high-interface points using
\(4\phi(1-\phi)\), and high-Joule points using \(q_J\), respectively. The Sobol
component is a nonzero global coverage floor; adaptive components cannot replace
it. Candidate ranking is detached from gradient optimization, while residuals at
the selected training points retain their complete differentiation graph.

### 3.4 Four-window causal replay

Training uses four physical windows,

\[
[0,0.35],\ [0.35,1.25],\ [1.25,1.60],\ [1.60,2.5],
\]

corresponding to first-pulse drive, recovery, second-pulse drive, and recovery.
Windows are introduced causally, but earlier windows retain an equal stratified
replay quota. This avoids the dilution of the first event when the time ceiling
expands.

### 3.5 Optional strict routed correction

A strict routed high-frequency correction is only a bounded feasibility probe,
not part of the critical path. Its differentiable gate combines a phase pilot
with a smooth heater-distance and pulse proxy. If used, the gate is part of the
reported predictor and its derivatives remain inside automatic differentiation;
no stop-gradient surrogate residual is permitted. The route is deleted if it
exceeds the predeclared cost ratio, becomes nonfinite, or fails its development
gain threshold.

## 4. Experimental protocol

### 4.1 Arms and route decision

The nominal development comparison contains: strong raw PINN, multi-frequency
only, physics sampler only, and multi-frequency plus physics sampler. The
sampler-only arm uses the raw representation, making representation and sampling
increments identifiable. A widened or update-matched raw network provides the
equal-compute fairness control. At most six nominal configuration identities and
two functional pivots are permitted.

Route A is physics-only. Sparse-reference route B is allowed only if every route-A
arm lacks basic physical competence. If route A is competent but the proposed
combination lacks attributable gain, the terminal status is
`MVP_NO_GO_NO_ATTRIBUTABLE_GAIN`; labels cannot rescue the story. If activated,
route B uses the same frozen 1% medium-grid anchors for all methods and reports
sparse-raw, data-only, and medium-interpolation controls.

### 4.2 Metrics

The primary metric is the time-averaged symmetric difference of the thresholded
phase region. The co-primary metric is continuous phase-field RMS error inside the
phase ROI. Hard guards require finite values, physical field ranges, event
existence and ordering, recovery, and locality. Temperature and terminal current
are non-inferiority guards. Event-time error, interface Hausdorff distance,
hotspot width, high-wavenumber error, wall time, and peak memory are secondary.

The selected method must pass the hard guards and improve the same predeclared
primary/co-primary decision rule over the strongest eligible comparator. A gain
in an arbitrary secondary metric alone is not success.

### 4.3 Development and sealed confirmation

The nominal case is used for bounded development and route freezing. The Day-7
confirmation matrix contains the two sealed stress cases, one frozen seed, and
three neural arms: the selected method, its strongest component comparator, and
equal-compute raw. Stress results can support, qualify, or reject the frozen claim
but cannot trigger rescue tuning. Three-seed confirmation is reserved for work
after the advisor draft.

## 5. Results

### 5.1 Computational profile and route selection

[PROFILE_TABLE]

[NOMINAL_ROUTE_RESULT]

### 5.2 Nominal field reconstruction and event dynamics

[NOMINAL_METRICS_TABLE]

[NOMINAL_FIELD_FIGURE]

[NOMINAL_QOI_FIGURE]

### 5.3 Component attribution

[ABLATION_TABLE]

[ATTRIBUTION_INTERPRETATION]

### 5.4 Sealed stress cases

[SEALED_STRESS_TABLE]

[STRESS_FIGURE]

## 6. Discussion

The central interpretation will be chosen from the frozen outcomes:

- **combined gain:** representation and sampling jointly improve localized phase
  reconstruction while satisfying temperature/current guards;
- **component gain:** one component is useful but their combination has no
  attributable increment;
- **regime-aware/Pareto outcome:** phase localization improves with a bounded
  cost or non-inferiority trade-off; or
- **No-Go:** the proposed method lacks basic competence or reproducible
  attributable gain under the fixed budget.

[DISCUSSION_FROM_EVIDENCE]

The sampling design is intentionally label-free, but it is not cost-free: ranking
a candidate pool adds forward and derivative work. The comparison therefore
reports both fixed-update and measured-compute views. The field-selective design
is also benchmark-specific in motivation; broader validation is required before
claiming a universal multiphysics representation principle.

## 7. Limitations

All targets are synthetic finite-volume trajectories. No experimental device data
or continuum-limit oracle is used. The Day-7 matrix uses one seed per sealed case,
so variance estimates and broad statistical claims are deferred. The two stress
cases alter one geometric or interfacial factor at a time and do not establish
population-level generalization. Material parameters are dimensionless benchmark
parameters rather than a calibrated material identification. These limitations
bound the claim but do not alter the reproducibility of the numerical comparison.

## 8. Conclusion

[CONCLUSION_FROM_FROZEN_RESULT]

## Data and code availability

Code, configuration contracts, run manifests, metric tables, and non-sensitive
derived figures are versioned in the project repository. Extra-fine field carriers
remain local because their upload is explicitly prohibited; their hashes,
generation contracts, and scalar summaries are recorded for reproducibility.

## References

1. Raissi, M., Perdikaris, P. & Karniadakis, G. E. Physics-informed neural
   networks. *J. Comput. Phys.* **378**, 686--707 (2019).
2. Chen, N. et al. Sharp-PINNs: staggered hard-constrained physics-informed
   neural networks for phase field modelling of corrosion. *Comput. Methods
   Appl. Mech. Eng.* **447**, 118346 (2025).
3. Chen, N. et al. PF-PINNs: physics-informed neural networks for coupled
   Allen--Cahn and Cahn--Hilliard equations. *J. Comput. Phys.* **529**, 113843
   (2025).
4. Wang, S., Li, B., Chen, Y. & Perdikaris, P. PirateNets: physics-informed deep
   learning with residual adaptive networks. *J. Mach. Learn. Res.* **25**,
   1--51 (2024).
5. Wang, S., Sankaran, S. & Perdikaris, P. Respecting causality for training
   physics-informed neural networks. *Comput. Methods Appl. Mech. Eng.* **421**,
   116813 (2024).
6. Wang, W., Wong, T. P., Ruan, H. & Goswami, S. Causality-respecting adaptive
   refinement for PINNs. arXiv:2410.20212v2 (2026).
7. Madir, B.-E. et al. Physics informed neural networks for heat conduction with
   phase change. *Int. J. Heat Mass Transfer* **252**, 127430 (2025).
8. Miquel, R. et al. Multi-physics modeling of phase change memory operations in
   Ge-rich Ge2Sb2Te5 alloys. *J. Appl. Phys.* **136**, 145102 (2024).
9. Wang, S., Teng, Y. & Perdikaris, P. Understanding and mitigating gradient
   flow pathologies in physics-informed neural networks. *SIAM J. Sci. Comput.*
   **43**, A3055--A3081 (2021).
