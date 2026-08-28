# Supplementary information

## S1. Evidence status and scope

This supplement supports the manuscript *When the Benchmark Fails Before the PINN*. All numerical results are synthetic and dimensionless. The target object is not calibrated to GGST, GST, VO$_2$, HfO$_2$, or another experimental material. No experimental data were used as training labels or validation truth.

The terminal status is:

~~~text
PHK_V2_ORACLE_NO_GO_EVENT_CONTRACT_AND_CONTROL_EXECUTION_FAILURE
PHK_V2_ORACLE_NO_GO_NO_PINN_OR_PHA_OR_KC_OR_FORMAL_EVIDENCE
~~~

“No PINN evidence” means no claim-bearing PINN training or evaluation was run. It does not mean a PINN underperformed.

## S2. Source-identity audit

### S2.1 Sharp-PINNs

The paper and current repository were frozen as separate identities. The paper identity contains staggered Allen–Cahn/Cahn–Hilliard residual minimization, random Fourier features, a modified MLP, a KKS-based hard output constraint, and gradient-norm loss weighting. The repository recipe adds causal/RAR configurations and substantially different epoch counts. Repository commit: `4b7029e3e1e0b82482d245ba12e3ec0945d87ed9`. License: GPL-3.0. The source was isolated and was not copied into the project package.

### S2.2 PF-PINNs

PF-PINNs supplies normalization, interface-oriented/refinement sampling, and random-batch NTK weighting. Repository commit: `a25f75b5fd40657e5ce98467d7afd0d0052464d1`. License: GPL-3.0. Sampling/support changes were preregistered as a separate budget axis rather than an architectural attribution arm.

### S2.3 PirateNet and jaxpi2

The original PirateNet jaxpi implementation uses a Penn custom license that permits non-profit research but restricts redistribution. The project did not import that source. The jaxpi2 repository, commit `77a5c1315a056388271822c35ad512a5a192b60d`, is Apache-2.0 and was used only for a minimal x64 CPU architecture smoke after full environment installation failed twice with Windows path-length errors. The smoke returned a finite output and 2,245 parameters; it did not reproduce a paper metric.

### S2.4 Physical source boundary

Miquel et al. informed the wall-cell topology and the electrical→Joule heat→phase causal checklist. Confidential composition, internal conductivity data, calibration/estimation, and the absence of open code prevent exact source reproduction. All PHK-V2 coefficients are engineering dimensionless values.

The full source audit is in `../docs/references/2026-08-27-phk-pinn-primary-source-baseline-audit.md`.

## S3. Machine contracts

### S3.1 Identities

| Contract | SHA256 |
|---|---|
| `configs/phk_v2/program_contract.json` | `0E1D89DD23F93C90160AC82ECE60ADA154410F4DDC33578CB892207FE8B445A8` |
| `configs/phk_v2/object_numerical_contract.json` | `3B3B9A369F4AFDFFB201394DD294E7196BAF04E5B36BAFE126291CA9CB3EA157` |
| `configs/phk_v2/case_split_manifest.json` file | `EBFDA2D59049AC989E8AA6C9622D92CF077D4B808961AB5807D178BF09DF57ED` |
| split internal identity | `55261CCA82ED2B71A9D3A81E28FC957B4873086CECB09D28EEE9B73B2CD73E09` |

### S3.2 Governing equations

For $(x,z)\in[-1,1]\times[0,1]$ and $t\in[0,2]$:

$$
\nabla\cdot(\sigma\nabla v)=0,
$$

$$
\partial_t\theta+L_r\partial_t\phi
=\alpha\nabla^2\theta-\gamma\theta+G\sigma|\nabla v|^2,
$$

$$
\partial_t\phi=M(\theta)(\epsilon^2\nabla^2\phi-\partial_\phi W),
$$

$$
W=B\phi^2(1-\phi)^2+A_T(\theta_{\rm tr}-\theta)\phi^2(3-2\phi),
$$

$$
\sigma=\exp\{\log(r_\sigma)\phi^2(3-2\phi)+g_T\theta\}.
$$

The numerical coefficient vector is

~~~text
alpha=0.1, gamma=1.5, latent_ratio=0.15, joule_gain=4.0,
conductivity_phase_ratio=8.0, conductivity_temperature_gain=0.25,
interface_width=0.04, barrier_scale=1.0, thermal_drive=4.0,
theta_transition=0.45, mobility_cold=0.2, mobility_hot=5.0,
mobility_width=0.08.
~~~

The initial phase is a 0.02 background plus a 0.01 Gaussian seed centered at $(0,0.12)$ with standard deviations 0.18 and 0.10. This is a synthetic initialization, not a measured microstructure.

### S3.3 Boundary and waveform contract

- The full top boundary is the electrical electrode and fixed-temperature sink.
- A centered bottom segment of width fraction 0.35 is the opposite electrical contact/heater.
- Electrical side boundaries and bottom regions outside the heater are no-normal-current.
- Thermal sides and bottom use a Robin sink with Biot number 0.25.
- All phase boundaries are no-normal-flux.
- Each unit-period pulse ramps from 0 to 0.75 over 0.05 time units, holds to 0.30, ramps down to 0 at 0.35, and remains at zero until the next cycle.

### S3.4 Numerical scheme

| Element | Frozen choice |
|---|---|
| grid | cell-centered Cartesian finite volume |
| electric faces | harmonic coefficient |
| electric solve | quasistatic sparse linear solve per coupled block |
| heat | backward-Euler diffusion with iterated Joule/latent source |
| phase | backward-Euler nonlinear reaction–diffusion with analytic Jacobian |
| Newton tolerance / maximum | $10^{-10}$ / 30 |
| Newton initial step / reduction / minimum | $1$, $1/2$, $2^{-12}$ |
| coupled change / residual tolerance | $10^{-8}$ / $10^{-9}$ |
| coupled maximum blocks / relaxation | 30 / 1 |
| linear residual tolerance | $10^{-11}$ |
| dtype | float64 |
| clipping acceptance | prohibited |
| result-adaptive rescue | prohibited |

## S4. Complete-case split

The outcome-blind Cartesian candidate universe uses heater width, interface width, waveform amplitude, pulse hold, initial phase background, and constitutive branch. Complete cases, not points or time samples, are the units of partition. The frozen pool counts are:

| Pool | Count | Intended role | Opened? |
|---|---:|---|---|
| D | 48 | development | no |
| I1 | 19 | first attribution identity | no |
| I2 | 21 | second attribution identity | no |
| F_A | 26 | formal aligned | no |
| F_O | 150 | orthogonal geometry/interface holdout | no |
| R | 60 | reserve | no |
| Total | 324 | complete candidate cases | Q qualification only; method pools sealed |

The split was frozen before the first PHK solve. No method result was available to influence it.

## S5. Event and guard definitions

### S5.1 Event extraction

The ROI is $|x|\le0.55$, $0\le z\le0.55$. Let $a_i$ denote cell area and define

$$
f_{\rm ROI}(t)=
\frac{\sum_{i\in\mathrm{ROI}}a_i\mathbf{1}[\phi_i(t)\ge0.5]}
{\sum_{i\in\mathrm{ROI}}a_i}.
$$

The event time is the first upward crossing of $f_{\rm ROI}=0.02$, linearly interpolated between saved samples. A cycle requires peak ROI fraction at least 0.02, peak full-domain fraction no more than 0.45, peak outside-ROI fraction no more than 0.10, peak excursion at least 0.02, at least three saved event samples, recovery at least 0.7, and cross-cycle peak drift no more than 0.2. Both cycles must pass.

Recovery is evaluated from peak excursion to the cycle endpoint without clipping. A second cycle that begins above the threshold cannot create a new upward crossing until it first recovers below threshold.

### S5.2 Hard guards

The hard-guard thresholds are electric terminal-current balance $10^{-8}$ relative, thermal balance $10^{-6}$ relative, scaled phase residual $10^{-9}$, no-flux residual $10^{-8}$, replay component difference $10^{-12}$, and zero non-finite entries. Field bounds are $v\in[-10^{-12},1]$, $\theta\in[-0.02,2.5]$, and $\phi\in[10^{-8},0.99999999]$.

Event failures are not averaged into these guards. A hard-guard pass and an event fail can coexist.

## S6. Qualification results

### S6.1 Manufactured checks

| Check | Value |
|---|---:|
| electric linear solution | $7.216\times10^{-16}$ |
| current balance | $2.516\times10^{-15}$ |
| power identity | $4.441\times10^{-16}$ |
| tested phase-Jacobian direction | $6.252\times10^{-11}$ |

These checks are bounded to the tested states and direction.

### S6.2 Zero drive

Intent 2 completed 800 steps. Maximum scaled phase residual: $9.820\times10^{-11}$. Maximum thermal residual: $5.638\times10^{-18}$. Maximum reduced temperature: 0.001703. Phase range: approximately $8.047\times10^{-5}$ to 0.029948. All zero-drive hard guards passed.

### S6.3 Event table

| Intent | First-cycle event | First recovery | Second event | Peak drift | Event verdict |
|---:|---:|---:|---|---:|---|
| 3 coarse | 0.212100 | 0.227273 | missing | 1.409091 | fail |
| 4 medium | 0.217800 | 0.233533 | missing | 1.586826 | fail |
| 5 fine | 0.219908 | 0.238606 | missing | 1.587131 | fail |
| 6 medium half-$\Delta t$ | 0.219467 | 0.221557 | missing | 1.568862 | fail |
| 7 fine replay | 0.219908 | 0.238606 | missing | 1.587131 | fail |

Every row above passed the numerical hard guards. Every row failed the two-cycle event contract.

### S6.4 Six-component comparisons

The component order is phase ROI RMS, temperature ROI RMS, terminal-current RMS, event time, phase-region symmetric difference, and recovery.

~~~text
coarse-medium    0.1152960305  0.0130287654  0.0121575772  0.00403050865  0.0113184080  0.0446724799
medium-fine      0.0440896453  0.0042742151  0.00384496681 0.00149081680  0.00381857855 0.0182278375
medium-half-dt   0.0242406527  0.0031864759  0.00267206765 0.00117851130  0.00198254364 0.00858333422
fine-replay      0             0             0             0             0             0
~~~

The replay result is deterministic under the tested environment. It does not imply an oracle pass.

### S6.5 Joule-off control

Nominal-medium minus Joule-off produced a peak reduced-temperature difference of 1.075707 versus joint uncertainty 0.00239908, and a peak ROI phase-fraction difference of 0.892562 versus 0.0251570. This supports only the bounded statement that the synthetic Joule term changes the synthetic thermal/phase response above tested numerical uncertainty.

### S6.6 Intent 9 failure

The phase-conductivity-feedback-off configuration ended with:

~~~text
RuntimeError: PHK phase Newton line search reached its frozen minimum step
~~~

The intent is retained as failed compute. There was no result file, parameter rescue, rerun, case substitution, or threshold change. Intents 10–12 are `NOT_REACHED`, not additional failures.

## S7. Compute accounting

| Quantity | Value |
|---|---:|
| process CPU seconds | 1318.71875 |
| process CPU core-hours | 0.3663107639 |
| summed single-thread wall seconds | 1339.3720109 |
| failed intents | 1 |
| rescue attempts | 0 |
| GPU hours | 0 |
| PINN optimizer updates | 0 |

The recorded process CPU total includes the failed intent. It does not include literature reading, document writing, or figure rendering.

## S8. Method stages not reached

The preregistered 2×2 methods were strong raw, PHA-MF only, field-selective KC only, and PHK full. Attribution controls included global multi-frequency, generic monotone clock, adaptive pseudo-time, wider raw, extra-work raw, wrong/shuffled gates, and separate sampling tracks. Development required complete-case isolation and formal required unopened aligned and orthogonal pools.

None was executed. No neural floor was sealed. There are no missing numerical entries to impute and no zeroes to enter into a method table.

## S9. Claim-boundary checklist

- The manuscript says “synthetic dimensionless benchmark,” not material-calibrated PCM.
- Manufactured and zero-drive checks are implementation evidence, not oracle validation.
- Resolution and replay diagnostics are numerical evidence, not event qualification.
- The Joule-off result is a bounded synthetic causal control, not experimental validation.
- Intent 9 is an execution failure, not proof that phase-conductivity feedback is necessary.
- Intents 10–12 and every PINN arm are not reached.
- No speedup, superiority, noninferiority, OOD, GPU, SOTA, or journal-acceptance claim is made.

