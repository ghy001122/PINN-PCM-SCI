# Conditional evolution report

Task PCM-20260925-INTEGRATED-MANUSCRIPT-FEASIBILITY-02

## S23. Fixed-temperature conditional phase evolution

### S23.1 Question and frozen numerical contract

This supplementary development diagnostic asks whether phase evolution under the frozen B1 E/29 temperature can reduce the remaining uncertainty enough to justify searching the original correction family. It is not a neural training arm or an original-family feasibility certificate. The grid is 80 by 40, D=[1.36,2.02], and the exact initial network phase is used without clipping or smoothing. The original zero-flux operator and all B0 coefficients are retained: interface width 0.04, barrier scale 1, thermal drive 6, transition temperature 0.45, cold/hot mobility 0.5/5 and mobility width 0.08. The thermal diffusivity, cooling and latent ratio are 0.1, 4 and 0.05. Temperature is fixed; the whole interval has zero electrical drive.

The unchanged logit Newton solver uses backward Euler, FP64, its analytic Jacobian, at most 30 iterations and halving line search down to 2^-20. Each step takes its own previous accepted phase as both old state and initial guess. The bounds are 0 and 1 with a strictly interior initial guess. Acceptance is the unscaled defect norm at most 1e-10; its divided-by-dt upper limits are 1.6e-7 and 3.2e-7. No other trajectory or future/reference phase initializes a step. Two fixed step sizes, 0.000625 and 0.0003125, provide 1056 and 2112 steps. No third trajectory, refinement, rescue, electrical solve, reference generation or optimizer update was performed.

Both trajectories and all 1057/2113 internal states were saved and locked before reference access. Numerical qualification passed: the 265-node phase difference RMS is 3.921397e-05 (limit 1e-4), the right-end maximum difference is 0.00029046819 (limit 1e-3), and the main heat difference is 9.4162193e-08 (limit 0.00011034353). These are two-step sensitivity checks at a fixed spatial discretization, not continuum error bounds.

Table S23a. Actual accepted work and maximum unscaled/divided algebraic defects. Main steps and linear solves are distinct. Zero clipping and zero line-search rejections were recorded.

| Trajectory | Steps | Newton | Linear solves | Max defect | Max defect/dt | Solve s |
|---|---|---|---|---|---|---|
| coarse | 1056 | 2137 | 2137 | 9.4268526e-11 | 1.5082964e-07 | 50.629044 |
| fine | 2112 | 4224 | 4224 | 9.9636303e-11 | 3.1883617e-07 | 100.86376 |

### S23.2 Three residual layers and paired thermal budgets

The algebraic layer is recorded for every internal step. Independently, the common phase residual is D_h0(phi)-F_h(t,phi) on 1057 common nodes, with h0=0.000625. D_h0 is second-order centered in the interior and (-3u0+4u1-u2)/(2h0) and (3uK-4uK-1+uK-2)/(2h0) at the endpoints. Fine values are sampled at nested nodes. The full 3200-cell volume measure and normalized trapezoidal time weights are shared. Conditional arrays have no neural AD residual; no continuous reconstruction is introduced. In particular, RHS minus itself is not used as evidence of phase accuracy.

Table S23b. Common discrete phase-residual mean square and the separate network-AD layer.

| State | Common phase MS | Network AD layer |
|---|---|---|
| B0 | 0.079156244 | B0 endpoint derivatives only |
| coarse | 2.2984504e-07 | Not applicable |
| fine | 5.6974088e-08 | Not applicable |

The primary heat residual uses the conditional F_h phase rate and the B0 network AD phase rate. The cross-check uses D_h0 for all three states. Both use the same frozen T, AD temperature rate and shared face heat flux. Each convention recomputes its own B0 baseline and tau=max(1.05 J_B0,J_B0+1e-12), without historical pool values. Both are resolved within budget: no step-size pass/fail flip occurs and each fine-step margin exceeds its observed step difference. The conventions agree. This does not replace the original 5% qualification or establish continuous physical truth.

Table S23c. Full-support paired heat budgets. Margin is tau minus candidate J; delta is the absolute coarse/fine difference, not an error bound or confidence interval.

| Convention | State | B0 J | Candidate J | Upper tau | Margin | Delta |
|---|---|---|---|---|---|---|
| Conditional | coarse | 0.011034353 | 0.010400643 | 0.011586071 | 0.0011854279 | 9.4162193e-08 |
| Conditional | fine | 0.011034353 | 0.010400737 | 0.011586071 | 0.0011853337 | 9.4162193e-08 |
| Common FD | coarse | 0.011034352 | 0.010399973 | 0.01158607 | 0.0011860968 | 4.3027889e-07 |
| Common FD | fine | 0.011034352 | 0.010400403 | 0.01158607 | 0.0011856666 | 4.3027889e-07 |

![Common residual and heat diagnostics](figures/conditional-residuals.png)

Figure S24. Residual mean squares in time on the common full-cell measure. The phase curve uses an independent time difference. The two heat panels use the separately paired conventions; near overlap of coarse and fine does not prove spatial or continuum convergence.

### S23.3 Endpoint seams and boundary interpretation

All seams compare the conditional a+ or b- evolution to B0 network AD. Velocity is F_h; acceleration is the fixed-phase partial time derivative plus the sparse Jacobian-vector product D_phi F_h F_h. Temperature and mobility time derivatives enter the partial derivative once. No dense 3200 by 3200 Jacobian or reference derivatives are used. The table includes RMS, maximum and the location of that maximum. Scaled RMS multiplies by (b-a)^order; full scaled maxima and vectors are retained in endpoint-seams.csv and endpoint-seam-vectors.npz.

Table S23d. The nonzero endpoint mismatches remain part of the result; no physical seam pass threshold is introduced.

| State | Side | Order | RMS | Max abs. | Scaled RMS | Max at (x,z) |
|---|---|---|---|---|---|---|
| coarse | left | 0 | 0 | 0 | 0 | (-0.9875, 0.0125) |
| coarse | left | 1 | 0.49770263 | 5.2604247 | 0.32848373 | (-0.4375, 0.0875) |
| coarse | left | 2 | 10.056184 | 143.3055 | 4.3804738 | (-0.2625, 0.0125) |
| coarse | right | 0 | 0.020566841 | 0.2785186 | 0.020566841 | (-0.3125, 0.0125) |
| coarse | right | 1 | 0.26351984 | 3.2741253 | 0.1739231 | (-0.3125, 0.0125) |
| coarse | right | 2 | 2.3457692 | 25.750126 | 1.0218171 | (-0.3875, 0.0125) |
| fine | left | 0 | 0 | 0 | 0 | (-0.9875, 0.0125) |
| fine | left | 1 | 0.49770263 | 5.2604247 | 0.32848373 | (-0.4375, 0.0875) |
| fine | left | 2 | 10.056184 | 143.3055 | 4.3804738 | (-0.2625, 0.0125) |
| fine | right | 0 | 0.020562588 | 0.27849917 | 0.020562588 | (-0.3125, 0.0125) |
| fine | right | 1 | 0.26349295 | 3.2741024 | 0.17390535 | (-0.3125, 0.0125) |
| fine | right | 2 | 2.3458266 | 25.745569 | 1.021842 | (-0.3875, 0.0125) |

The left input is identical for both step sizes. Accordingly, their left RHS jets agree exactly while the left first-derivative mismatch to B0 has RMS 0.49770263 and maximum 5.2604247. This mismatch cannot be removed by temporal refinement. The endpoint identity Delta phi_t = M epsilon^2 (L_h phi_B0 - L_AD phi_B0) - r_phi,AD has maximum reconstruction discrepancy 8.882e-16. It separates the spatial/boundary implementation difference from the original dynamic defect at that endpoint, without a global causal claim. Nonzero seams do not by themselves rule out a correction with residual tolerances; they also prevent treating this IVP as an exact C2-gated witness.

Table S23e. All boundary sides, including the full bottom. IVP boundary flux is imposed as zero by the discrete operator, whereas B0 quantities are network normal derivatives. These are distinct layers, so the zero is not a superiority claim.

| Side | Faces | B0 normal MS | B0 max abs. |
|---|---|---|---|
| left | 40 | 1.0193355e-14 | 6.2116535e-07 |
| right | 40 | 6.3945549e-15 | 1.080827e-06 |
| bottom | 80 | 0.88354715 | 8.8877495 |
| top | 80 | 3.815886e-15 | 3.2056063e-07 |

### S23.4 Locked development-reference analysis

Only after locking and numerical qualification were the saved original 160 by 80 reference values volume-restricted to the same 80 by 40 cells and scored at 265 D nodes. B0 uses the same frozen network's cached values. The ROI is |x|<=0.55 and 0<=z<=0.55. Ephi_D_80 is a raw phase-fraction RMS with separately normalized spatial/time weights, not the historical 160 by 80 W-window error. Both trajectories improve in both scopes by more than their observed step differences; the fine full-domain reduction is 69.0143%. This is development evidence on an already examined numerical reference, not a new formal A_w, independent confirmation or statistical significance claim.

Table S23f. The required B0 row and both trajectories on the same restricted reference. Gain is E_B0 minus E_IVP.

| Scope | State | Ephi_D_80 | Gain | Delta E |
|---|---|---|---|---|
| full | B0 | 0.066943576 | not applicable | 1.6633725e-05 |
| full | coarse | 0.020759591 | 0.046183985 | 1.6633725e-05 |
| full | fine | 0.020742957 | 0.046200619 | 1.6633725e-05 |
| roi | B0 | 0.12171559 | not applicable | 3.0243136e-05 |
| roi | coarse | 0.037744703 | 0.083970886 | 3.0243136e-05 |
| roi | fine | 0.03771446 | 0.08400113 | 3.0243136e-05 |

The support diagnostics show a tradeoff rather than uniform improvement. With the restricted native indicator, fine-step recall falls from 0.974612 to 0.763383 while precision rises from 0.410817 to 0.890215 and symmetric-difference mass decreases. Thresholding after restriction gives the same tradeoff (recall 0.982021 to 0.776968; precision 0.410832 to 0.899253). The ROI agrees. These descriptive D-window measures do not establish the original strict event criteria.

Table S23g. Active-support diagnostics retain both noncommuting reference semantics separately. Masses use normalized D time and the indicated spatial scope; symmetric difference uses fractional overlap for the restricted native indicator. These descriptive values do not replace original event or A_w decisions. The companion CSV includes all predicted, reference, overlap, false-positive and false-negative masses and precision.

| Scope | State | Reference semantics | Reference mass | Sym. diff. mass | Recall |
|---|---|---|---|---|---|
| full | B0 | native indicator | 0.0085907907 | 0.012225971 | 0.97461247 |
| full | B0 | threshold after restriction | 0.0085262784 | 0.012160866 | 0.98202138 |
| full | coarse | native indicator | 0.0085907907 | 0.0028444602 | 0.76279711 |
| full | coarse | threshold after restriction | 0.0085262784 | 0.0026485559 | 0.77627377 |
| full | fine | native indicator | 0.0085907907 | 0.0028415009 | 0.76338271 |
| full | fine | threshold after restriction | 0.0085262784 | 0.002643821 | 0.77696793 |
| roi | B0 | native indicator | 0.028399308 | 0.040416432 | 0.97461247 |
| roi | B0 | threshold after restriction | 0.028186044 | 0.040201211 | 0.98202138 |
| roi | coarse | native indicator | 0.028399308 | 0.0094031743 | 0.76279711 |
| roi | coarse | threshold after restriction | 0.028186044 | 0.0087555566 | 0.77627377 |
| roi | fine | native indicator | 0.028399308 | 0.0093933916 | 0.76338271 |
| roi | fine | threshold after restriction | 0.028186044 | 0.0087399042 | 0.77696793 |

![Conditional phase and restricted reference fields](figures/conditional-phase-fields.png)

Figure S25. B0, the fine conditional trajectory and the volume-restricted development reference at the initial, middle and final D times. The common [0,1] phase scale makes the spatial support visible. The fine trajectory is displayed as the smaller-step result, alongside the complete coarse/fine numerical and reference tables. The coarse trajectory remains available in full.

### S23.5 Outcome, actual work and limits

The numerical facts above are VERIFIED. The route output is CONDITIONAL_IVP_SUPPORTS_FURTHER_WITNESS_SEARCH, a SUPPORTED_INTERPRETATION: paired thermal and reference evidence now supports considering a bounded witness search in the original correction family, with the observed seams explicitly addressed. The original C2-family feasibility is UNKNOWN. This is the sole follow-on research recommendation; it requires a separate approved design. No A+, new optimization or independent confirmation has started.

Network queries took 114.794 s; the two phase solves took 151.493 s. The query/propagation process took 269.760 s, followed by 2.926 s numerical evaluation and 2.475 s reference evaluation. These measured stages are not an equal-work speedup comparison. Work was 3168 main steps, 6361 Newton iterations/linear solves and 16908 coordinate-query batches. The cache records separate temperature/phase head positions, first/second derivatives, shared-face and boundary queries. Model identity is unchanged, with zero training, electrical forwards, electrical adjoints or reference generation.

The instance was a V100 32 GB with a six-core CPU quota and 25 GiB container memory; four CPU threads and at most 1024 coordinates per query were used. The sampled process RSS peak was 0.889 GiB. The resource guards did not trigger. GPU peak allocation was not persisted and no value is inferred. The first deployment preflight omitted one original contract-identity fixture; it failed before any model query or scientific step. The unchanged fixture was included, six targeted checks and model loading passed, and the same frozen task ran once. Both preflight records remain available.

Results were recovered and archive integrity verified before shutdown was requested at 2026-09-25T14:30:19.899793+00:00. The shutdown command returned zero; subsequent SSH connection refusal was recorded at closure 2026-09-25T14:30:26.785254+00:00. A later local saved-array reconstruction reproduced the defects, exports, common residuals, both heat conventions and reference RMS scores without another model query or propagation. Complete runtime source identities, B0 path, physical coefficients, environment, work counters, numerical vectors and shutdown evidence accompany the run. P02 method value, strict two-cycle use, material validation and P03 full-array external access remain open.

