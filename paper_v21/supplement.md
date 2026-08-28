# Supplementary information for PHK-V2.1

## S1. Scope and evidence identity

PHK-V2.1 is an independent engineering-science route. It preserves without rewriting the prior PHK-V2 Oracle No-Go. Its benchmark is a transparent, dimensionless, literature-inspired synthetic two-dimensional Cartesian wall-cell electrothermal phase-field object. It is not an author-model reproduction and is not calibrated to a named material or experimental device.

This supplement reports the complete frozen S1 qualification. It contains no PINN-training result, no Sharp/PF metric reproduction, no PHA-MF/KC result, no GPU result, and no formal OOD result.

## S2. Engineering-stage separation

### S2.1 Control solver

The bounded E1 matrix compared six control-branch approaches against the same red fixture and sentinels: legacy damped Newton, trust-region reflective, logit analytic Newton, pseudo-transient Newton, smaller-step diagnostic, and Anderson outer coupling. The selected scientific solver was logit analytic Newton with analytic Jacobian.

| Quantity | Value |
| --- | ---: |
| phase residual tolerance | 1e-10 |
| maximum phase iterations | 30 |
| initial logit Newton step | 1.0 |
| line-search reduction | 0.5 |
| minimum line-search step | 9.5367431640625e-7 |
| maximum coupled blocks | 30 |
| coupled relative-change tolerance | 1e-8 |
| coupled residual tolerance | 1e-9 |
| coupled relaxation | 1.0 |

Dynamic solver switching, output clipping as acceptance, and result-adaptive time-step rescue were prohibited.

### S2.2 Bounded object selection

E2 completed 41/41 cases: the frozen coarse factorial, refinement cases, medium promotions, and final controls. The selected engineering identity was PHK_V21_E2_STAGE2_0A1813B1D968F573.

Engineering cases never entered Q, D, I, formal, or reserve pools and did not contribute to any oracle or method score.

## S3. Governing object

The spatial domain is x in [-1,1] and z in [0,1]. The final time is 2.5 with two pulses of period 1.25. The nominal heater is a centered segment on the bottom boundary with width fraction 0.35. The top electrode covers the complete upper boundary. Electrical side boundaries and the lower boundary outside the heater are no-normal-current. The thermal top is fixed at zero reduced temperature; sides and bottom use a Robin condition. The phase field has zero normal flux on all boundaries.

The inherited dimensionless governing equations are:

$$
\nabla\cdot\left[\sigma(\theta,\phi)\nabla v\right]=0,
$$

$$
\frac{\partial\theta}{\partial t}
+L_r\frac{\partial\phi}{\partial t}
=\alpha_\theta\nabla^2\theta-h_v\theta
+G_J\sigma(\theta,\phi)|\nabla v|^2,
$$

$$
\frac{\partial\phi}{\partial t}
=M(\theta)\left[\epsilon_\phi^2\nabla^2\phi-\frac{\partial W}{\partial\phi}\right].
$$

The free energy, conductivity, and mobility are:

$$
W=B\phi^2(1-\phi)^2
+G_\theta(\theta_{\mathrm{tr}}-\theta)\phi^2(3-2\phi),
$$

$$
\sigma=\exp\left[\log(r_\sigma)\,\phi^2(3-2\phi)+g_\sigma\theta\right],
$$

$$
M=M_c+(M_h-M_c)
\operatorname{sigmoid}\left(\frac{\theta-\theta_{\mathrm{tr}}}{w_M}\right).
$$

PHK-V2.1 overrides the inherited object with period 1.25, cooling 4.0, latent ratio 0.05, interface width 0.04, thermal drive 6.0, cold/hot mobility 0.5/5.0, waveform amplitude 0.72, and hold end 0.27. These are engineering dimensionless values, not material fits.

## S4. Spatial and temporal contracts

The implementation uses cell-centered finite volumes. Electrical face conductivity is harmonic. Electric solves are quasistatic within each coupled block. Thermal diffusion uses backward Euler with iterated Joule and latent sources. The phase equation uses backward Euler in a logit variable with analytic sparse Jacobian and final returned-state residual recheck. Calculations are float64 and cross-configuration warm starts are forbidden.

| Resolution | nx | nz | dt | save every |
| --- | ---: | ---: | ---: | ---: |
| coarse | 40 | 20 | 0.005 | 2 |
| medium | 80 | 40 | 0.0025 | 2 |
| fine | 120 | 60 | 0.00125 | 2 |
| extra-fine | 160 | 80 | 0.000625 | 4 |
| medium half-dt | 80 | 40 | 0.00125 | 4 |

## S5. Event contract

The ROI is |x| <= 0.55 and 0 <= z <= 0.55. A cell is phase-positive when phi >= 0.5. The ROI phase fraction is the area-weighted fraction of phase-positive cells.

For each pulse cycle:

1. the event time is the first upward crossing of ROI phase fraction 0.02, with linear interpolation;
2. peak ROI fraction must be at least 0.02;
3. peak minus the pre-cycle value must be at least 0.02;
4. the event must persist at least three saved steps;
5. recovery must be at least 0.70.

Across cycles, relative peak drift must not exceed 0.20. The peak full-domain fraction must not exceed 0.45 and the peak outside-ROI fraction must not exceed 0.10. Two new upward crossings are required for nominal qualification.

## S6. Complete-case split

Case identity is the SHA256 of canonical JSON containing geometry, constitutive branch, initial state, complete waveform, and complete history. The 128 selected cases were assigned before results:

| Pool | Count | Role |
| --- | ---: | --- |
| D | 24 | development only |
| I1 | 12 | first sealed identity gate |
| I2 | 12 | second sealed identity/attribution gate |
| F_A | 32 | waveform-axis formal OOD |
| F_O | 32 | whole-factor orthogonal OOD |
| R | 16 | unopened reserve |

The nominal candidate universe contained 243 combinations. SHA ordering selected D/I1/I2/F_A/R cases. Four whole-factor geometry values each contributed eight F_O cases. A case never crosses pools; engineering cases never enter the scientific split. Because S1 failed, D/I1/I2/F_A/F_O/R remained unopened.

## S7. S1 qualification ladder and accounting

All intents were preordered and were consumed whether they passed or failed:

| # | Identity | Role |
| ---: | --- | --- |
| 1 | Q_MANUFACTURED_OPERATORS | operator guard |
| 2 | Q_ZERO_DRIVE_MEDIUM | no-drive guard |
| 3 | Q_NOMINAL_COARSE | spatial hierarchy |
| 4 | Q_NOMINAL_MEDIUM | spatial hierarchy |
| 5 | Q_NOMINAL_FINE | spatial hierarchy |
| 6 | Q_NOMINAL_EXTRA_FINE | spatial hierarchy |
| 7 | Q_NOMINAL_MEDIUM_HALF_DT | temporal comparison |
| 8 | Q_NOMINAL_FINE_EXACT_REPLAY | exact replay |
| 9 | Q_JOULE_GAIN_ZERO_MEDIUM | Joule mechanism control |
| 10 | Q_CONDUCTIVITY_PHASE_RATIO_ONE_MEDIUM | conductivity control |
| 11 | Q_LATENT_RATIO_ZERO_MEDIUM | latent control |
| 12 | Q_HEATER_WIDTH_0_50_MEDIUM | geometry control |
| 13 | Q_INTERFACE_WIDTH_0_025_MEDIUM | interface control |
| 14 | Q_PSEUDO_TRANSIENT_SOLVER_CROSSCHECK_MEDIUM | independent solver cross-check |

The complete S1 record used 4062.65625 process CPU seconds and 4113.6542242 summed single-thread wall seconds. There were zero solver failures, zero replacement intents, and zero GPU hours.

## S8. Guards

Hard numerical guards included:

- electric terminal-current balance;
- thermal balance;
- scaled phase-equation residual;
- phase no-flux residual;
- nonfinite count;
- phase range [0,1];
- event duration, recovery, locality, and two-cycle identity;
- exact-replay maximum component difference <= 1e-12.

Intent completion and guard passage were recorded separately. A complete run could still fail oracle convergence, as occurred here.

## S9. Six endpoint components and convergence

Comparisons project the finer solution to common space/time support and compute phase-field ROI RMS, temperature ROI RMS, terminal-current RMS, two-cycle event-time RMS, time-averaged phase-region symmetric difference, and two-cycle recovery RMS.

The component floor rule was prospective:

$$
U_j=\max\left(\Delta_{j,\mathrm{space}},
\Delta_{j,\mathrm{time}},
\Delta_{j,\mathrm{replay}},
2\,\tau_{j,\mathrm{solver}}\right).
$$

Qualification required every component to contract from medium-to-fine to fine-to-extra-fine.

| Component | M-to-F | F-to-XF | Result |
| --- | ---: | ---: | --- |
| phase field | 0.0091647234 | 0.0045916543 | pass |
| temperature | 0.0025375405 | 0.0012569191 | pass |
| current | 0.0023260690 | 0.0012107208 | pass |
| event time | 0.0012067680 | 0.0016486830 | **fail** |
| phase region | 0.00030375 | 0.000145 | pass |
| recovery | 0 | 0 | pass |

The candidate U values were persisted for audit, but the record explicitly has floor_sealed_and_converged=false. It cannot be consumed as a neural floor.

## S10. Event and control details

| Resolution | Cycle 1 | Cycle 2 |
| --- | ---: | ---: |
| coarse | 0.2271 | 1.4871 |
| medium | 0.2378 | 1.4942 |
| fine | 0.2389833333 | 1.495975 |
| extra-fine | 0.2406 | 1.4984 |

All nominal recoveries are 1.0. Zero-drive and Joule-off have zero ROI peak and no event. Conductivity-ratio-one and latent-off retain both events. Wide-heater loses cycle 2; narrow-interface retains both. These controls were preregistered to be recorded, not all required to preserve the nominal event identity.

## S11. Implementation amendments

### S11.1 Intent 2 carrier reconciliation

The immutable result stored cycles as a tuple after dataclass serialization, while the no-event helper accepted only lists. The amendment retained the original result/report/manifest, used the original two-cycle values, recomputed only the Boolean no-event interpretation, and performed no solver rerun.

### S11.2 Terminal label reconciliation

An inherited comparator emitted short component labels while V2.1 expected long semantic labels. The amendment mapped labels position-for-position, preserved order and all values, performed no recomputation, and wrote no evidence during the failed first summary attempt.

## S12. Baseline and method stages not reached

Sharp-PINNs, PF-PINNs, PirateNet/adaptive pseudo-time, strong raw, the four-arm bottleneck diagnostic, PHA-MF, KC, the equal-budget 2x2, challengers, GPU development, and F_A/F_O formal OOD all remained unopened. Their planned identities are documented to show prospective discipline, not execution.

## S13. Environment

- Windows local workstation;
- scientific Python 3.11.9;
- float64 local CPU qualification;
- no CUDA/GPU;
- no paid/cloud compute;
- figure-only postprocessing with local Python 3.12 and Matplotlib 3.8.4.

## S14. Terminal interpretation

The outcome is a valid bounded negative qualification: PHK_V21_ORACLE_NO_GO_STOP_BEFORE_PINN and PHK_V21_ORACLE_NO_GO_NO_PINN_OR_METHOD_EVIDENCE.

It does not establish a universal numerical impossibility, a physics failure, a PINN failure, a PHA/KC failure, material behavior, experimental validation, or journal acceptance.
