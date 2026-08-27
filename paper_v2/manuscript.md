# When the Benchmark Fails Before the PINN: Pre-Registered Oracle Qualification for a Two-Cycle Electrothermal Phase-Field Case Study

## Abstract

Physics-informed neural networks (PINNs) inherit the validity of the differential equations, numerical reference, event definition, and data partition against which they are evaluated. In phase-changing electrothermal systems, these upstream assumptions are unusually fragile: localized Joule heating, diffuse interfaces, phase-dependent conductivity, latent heat, and repeated pulses create a coupled benchmark whose apparent numerical completion need not imply a repeatable event. We report a failure-preserving qualification study that was designed before any PINN training to decide whether a transparent two-dimensional electrothermal phase-field wall-cell could support a fair comparison of a strong phase-field PINN, a phase–hotspot-aware multi-frequency representation, and a field-selective kinetics clock. The source identities, dimensionless physical/numerical contract, 12-intent qualification ladder, 324 complete-case split, event thresholds, no-rescue rule, and method stop gate were frozen before the first benchmark solve. Manufactured-operator checks and a zero-drive guard passed. Nominal coarse, medium, fine, half-time-step, and exact-replay runs also passed the numerical hard guards; the replay differences were zero across all six frozen endpoint components. Nevertheless, the first-cycle recovery was only 0.22–0.24 against a preregistered minimum of 0.7, the second cycle produced no new upward event crossing, and the cycle-peak drift was 1.41–1.59 against a maximum of 0.2. A required phase-conductivity-feedback-off control then terminated when the phase Newton line search reached its frozen minimum step. The ladder therefore returned `PHK_V2_ORACLE_NO_GO_EVENT_CONTRACT_AND_CONTROL_EXECUTION_FAILURE` after 0.3663 recorded process CPU core-hours. No neural error floor was sealed and no strong-raw, multi-frequency, kinetics-clock, GPU, or formal comparison was run. The result is not a negative PINN finding. It is a reproducible demonstration that numerical guards, resolution checks, causal controls, and event qualification answer different questions, and that stopping before approximation prevents an unqualified reference trajectory from becoming neural evidence.

**Keywords:** physics-informed neural networks; phase-field model; electrothermal coupling; phase-change memory; benchmark qualification; numerical verification; negative results; reproducibility

## 1. Introduction

Physics-informed neural networks approximate solutions of differential equations by placing the governing residuals, initial conditions, boundary conditions, and sometimes data into a trainable objective [@raissi2019pinn]. Their most persuasive use is not merely that a neural network can fit a field, but that a physically structured learner can reach a useful accuracy–cost or generalization regime that a strong comparator does not. That claim has an upstream dependency: the object being solved, the reference process used for evaluation, and the quantities called “events” must themselves be qualified.

This dependency is easy to hide in a conventional PINN paper. A reference solver produces arrays; a network is trained against residuals and compared to those arrays; a relative error is reported. If the reference process is under-resolved, follows a different event branch, fails a coupled control, or never returns to a state from which a repeated event can occur, the neural comparison may still look numerically polished. In that case, the study has measured approximation to an unqualified computational trajectory rather than performance on the intended scientific task.

Phase-field and phase-change settings sharpen this risk. Recent phase-field PINNs address residual competition, sharp interfaces, sampling concentration, causality, and architectural depth. Sharp-PINNs combine staggered equation-block training, random Fourier features, a modified MLP, hard constraints, and gradient-based weighting for corrosion phase fields [@chen2025sharp]. PF-PINNs use normalization, interface-oriented refinement, and random-batch NTK weighting [@chen2025pf]. PirateNet grows a residual architecture from a shallow initialization and reports multi-seed results across demanding PDEs [@wang2024pirate]. Causality-respecting adaptive refinement expands the collocation support around evolving interfaces [@wang2026rbar], while adaptive pseudo-time targets spurious low-loss solutions through a homotopy that is distinct from warping physical time [@wang2026pseudotime]. Phase-change heat PINNs further show that weighting, attention, and sequence-in-time training can materially affect Stefan-type problems [@madir2025phasechange].

These methods suggest two plausible device-oriented extensions. A phase–hotspot-aware multi-frequency representation could allocate high-frequency capacity where phase gradients and Joule hotspots are expected. A field-selective kinetics clock could redistribute temporal resolution only for the phase branch while preserving physical-time evaluation and the full coordinate pullback. Those ideas, however, can only be tested after a reference object produces localized, resolved, repeatable events and passes required causal controls. The present work was initially designed as such a positive two-module study. Its preregistered gate stopped the study before the methods became scientifically admissible.

The contribution is therefore a bounded benchmark-qualification result rather than a positive PINN algorithm result:

1. We separate paper, repository, license, and reproducibility identities for the intended phase-field and general PINN comparators. In particular, the Sharp-PINNs paper identity is kept distinct from the current repository's causal/RAR long-budget recipes.
2. We define a transparent, dimensionless, two-dimensional electrothermal phase-field wall-cell and freeze its numerical scheme, two-cycle waveform, hard guards, event contract, convergence comparisons, causal controls, and no-rescue ladder before solving it.
3. We preserve the difference between implementation guards, numerical convergence/replay diagnostics, an event-bearing oracle, and a method benchmark. The nominal runs pass the first category and provide useful evidence in the second, while failing the third.
4. We release a complete terminal record: all completed and failed intents, not-reached stages, raw carriers, compute accounting, figures, and claim boundaries. No PINN result is inferred from an upstream stop.

The study asks three questions. First, can the proposed reduced object pass basic manufactured and zero-drive implementation guards? Second, does it produce two localized and recoverable events that remain stable under space, time, and replay checks while required causal controls execute? Third, only if both answers are positive, may strong PINN baselines and the proposed modules be tested. The answer to the first question is yes; the answer to the second is no under the frozen contract; the third question is consequently not reached.

![Pre-registered workflow from source identity through the Oracle Gate and the method-stage stop.](figures/figure-01-workflow.png)

**Figure 1.** Pre-result-frozen workflow. Source and license identities, the machine contracts, complete-case split, and 12-intent qualification ladder precede any neural training. The Oracle No-Go closes the method path; it does not imply a negative result for a PINN that was never run.

## 2. Source and baseline identities

### 2.1 A phase-field anchor is not a complete evidence baseline

Sharp-PINNs is the closest open phase-field method anchor because it addresses coupled phase-field residuals and sharp corrosion interfaces [@chen2025sharp]. Its paper-level method includes staggered Allen–Cahn/Cahn–Hilliard training, random Fourier features, a modified MLP, a corrosion-specific hard constraint, and gradient-norm weighting. The paper's reported 2D ablation uses a 1,000-Adam-step identity. The fixed official repository additionally contains causal weighting, residual-adaptive refinement, and much longer configurations. These are valuable engineering recipes, but merging them into the paper identity would turn a replication target into a moving best-method package.

We therefore preregistered two Sharp identities: a paper-specification comparator and a repository-recipe comparator at commit `4b7029e3e1e0b82482d245ba12e3ec0945d87ed9`. The latter was kept isolated because the source is GPL-3.0. PF-PINNs was similarly fixed at commit `a25f75b5fd40657e5ce98467d7afd0d0052464d1` and treated as a sampling/NTK support control rather than the sole baseline [@chen2025pf].

A strong general architecture was also necessary. PirateNet reports a five-seed architecture study and uses trainable residual coefficients initialized at zero [@wang2024pirate]. The original jaxpi code has a custom Penn non-profit research license and redistribution restrictions; it was not incorporated. Instead, the Apache-2.0 jaxpi2 tree was fixed at `77a5c1315a056388271822c35ad512a5a192b60d`. Adaptive pseudo-time was a mandatory control because it challenges the causal story of a learnable kinetics clock: a continuation method that avoids spurious solutions without changing physical time could explain an apparent temporal gain [@wang2026pseudotime].

The fixed external trees passed bounded CPU module checks, not paper-result replication. Sharp and PF forward/backward module smokes were finite. The full jaxpi2 dependency installation failed twice on Windows path-length limits; a minimal environment supported an x64 PirateNet architecture-only forward pass with 2,245 parameters. No paper accuracy, training trajectory, speed, or variance result was reproduced. This distinction matters because code importability is implementation evidence, not a scientific baseline.

### 2.2 Physical inspiration and its boundary

Miquel et al. provide a detailed wall-type phase-change-memory topology and couple phase-aware electrical and thermal transport, Joule heat, latent heat, thermal boundary resistance, and phase evolution [@miquel2024pcm]. That work is a useful causal-chain checklist. It is not an open exact reference for this study: the exact composition is confidential, some electrical properties come from internal measurements, multiple parameters are calibrated or estimated, and the author solver was not released.

Accordingly, the present object is not a GGST model reproduction. It retains only the two-dimensional wall-cell cross-section and the electric-to-Joule-heat-to-phase causal sequence. All coefficients are declared dimensionless engineering contract values. Positive comparisons, had they been reached, would have applied only to this transparent synthetic benchmark.

![Method-source anatomy, transfer roles, and the difference between source anchoring and completed reproduction.](figures/figure-02-source-anatomy.png)

**Figure 2.** Source and baseline anatomy. `A` denotes a directly identified source module; `A′` denotes a PCM-oriented adaptation that would require independent testing. The rightmost status distinguishes source audit and module smoke from paper-metric reproduction and PHK method evidence.

## 3. Pre-registered benchmark and qualification protocol

### 3.1 Dimensionless wall-cell model

The domain is a Cartesian cross-section $(x,z)\in[-1,1]\times[0,1]$ over two unit-duration pulse cycles, $t\in[0,2]$. A centered bottom segment acts as the heater/electrical contact and the full top boundary is the opposite electrode. The fields are electrical potential $v$, reduced temperature $\theta$, and phase fraction $\phi$.

The quasistatic electrical equation is

$$
\nabla\cdot\left[\sigma(\theta,\phi)\nabla v\right]=0,
$$

with

$$
\sigma(\theta,\phi)=\exp\left[\log(r_\sigma)h(\phi)+g_T\theta\right],
\qquad h(\phi)=\phi^2(3-2\phi).
$$

The reduced thermal balance is

$$
\partial_t\theta+L_r\partial_t\phi
=\alpha\nabla^2\theta-\gamma\theta
+G\sigma(\theta,\phi)|\nabla v|^2,
$$

and the phase equation is

$$
\partial_t\phi=M(\theta)
\left[\epsilon^2\nabla^2\phi-\partial_\phi W(\phi,\theta)\right],
$$

where

$$
W=B\phi^2(1-\phi)^2
+A_T(\theta_{\mathrm{tr}}-\theta)\phi^2(3-2\phi),
$$

and $M(\theta)$ transitions smoothly from a cold to a hot mobility. The exact coefficients, boundary conditions, seed profile, waveform, and guards are recorded in the machine contract. The top temperature is fixed at zero reduced temperature; the sides and bottom use a Robin sink. All phase boundaries are no-flux. The unipolar voltage waveform ramps to 0.75 by $t=0.05$ within each cycle, holds through $t=0.30$, ramps down by $t=0.35$, and remains off for recovery.

The model is deliberately simple enough to be auditable and rich enough to close an electric–thermal–phase causal loop. It omits material calibration, threshold switching, crystallographic variants, stochastic nucleation, and an external circuit. These omissions define the claim boundary; they are not silently absorbed into fitted parameters.

### 3.2 Numerical contract

The solver uses a cell-centered finite-volume discretization. Electrical face conductivities are harmonic. The electric block is solved quasistatically within each coupled block. Heat diffusion and phase reaction–diffusion use backward Euler. The coupled electric, thermal, and phase blocks iterate to a frozen change and residual tolerance, followed by a final residual recheck. The phase Newton solve uses an analytic sparse Jacobian, a bound-preserving line search, maximum 30 iterations, initial full step, and a minimum line-search step of $2^{-12}$. Clipping is not an acceptance mechanism and cross-configuration warm starts are forbidden.

The spatial grids are $40\times20$, $80\times40$, and $120\times60$, with time steps 0.005, 0.0025, and 0.00125. An additional $80\times40$ run uses the fine time step. Saved physical times are aligned for comparisons. A fine run is executed once more as an exact replay.

### 3.3 Event contract

The event region of interest is $|x|\le0.55$ and $0\le z\le0.55$. A cell belongs to the active phase region when $\phi\ge0.5$. For each pulse cycle, the ROI phase fraction is the cell-volume-weighted active fraction. Event time is the first upward crossing of ROI fraction 0.02, linearly interpolated between saved times.

Qualification requires two complete cycles. For each cycle, the peak ROI fraction must be at least 0.02, the peak full-domain fraction at most 0.45, the peak outside-ROI fraction at most 0.10, and the peak excursion above the pre-cycle level at least 0.02. Recovery must be at least 0.7, the relative drift of the two cycle peaks at most 0.2, and each event must occupy at least three saved steps. The recovery requirement is load-bearing: a second pulse that begins from a persistently transformed state is not a new formation event merely because the phase remains above threshold.

### 3.4 Sequential qualification ladder

The 12 intents were ordered before execution: manufactured operators; zero drive; nominal coarse, medium, fine, medium-half-time-step, and exact fine replay; Joule-off; phase-conductivity-feedback-off; latent-heat-off; wide heater; and narrow interface. Each intent had to complete before the next was claim-bearing. A numerical exception consumes the intent. There is no result-adaptive rescue, replacement case, threshold adjustment, coefficient tuning, or post-failure reordering.

Numerical hard guards cover finite values, potential/temperature/phase ranges, electric terminal balance, thermal balance, scaled phase residual, no-flux residual, and replay. Event criteria are separate. A numerically guarded trajectory can therefore fail scientific event qualification.

Before solving, a canonical complete-case universe was also partitioned into mutually exclusive development, identity, formal-aligned, formal-orthogonal, and reserve pools. The split contains 324 complete cases and is bound to the exact program and object contract hashes. None of these method pools was opened.

![Qualification ladder with completed, failed, and not-reached intents.](figures/figure-03-qualification-ladder.png)

**Figure 3.** Frozen 12-intent ladder. Intents 1–8 completed, intent 9 failed and was consumed, and intents 10–12 were not reached. The method stage is downstream of the entire Oracle Gate.

## 4. Results

### 4.1 Manufactured and zero-drive implementation guards

The manufactured electric linear-solution error was $7.216\times10^{-16}$, the current-balance error $2.516\times10^{-15}$, and the power-identity error $4.441\times10^{-16}$. A directional check of the phase Jacobian gave $6.252\times10^{-11}$. These tests show that selected operators and a tested Jacobian direction are internally consistent; they are not a proof of global implementation correctness or physical validation.

The zero-drive medium run completed 800 time steps. Its maximum scaled phase residual was $9.820\times10^{-11}$ and maximum thermal residual $5.638\times10^{-18}$. The maximum reduced temperature was 0.001703, the phase fraction stayed within its frozen bounds, and all hard guards passed. With no applied drive, the event guard is not evidence of a switching event. Intent 2 is therefore an implementation and artifact-chain check only.

### 4.2 Nominal runs are numerically guarded but do not recover

The coarse, medium, fine, and medium-half-time-step nominal runs completed without a hard numerical guard failure. They produced a localized first-cycle ROI crossing at times 0.2121, 0.2178, 0.219908, and 0.219467, respectively. The spatial/time sequence is consistent with an event time approaching approximately 0.22 under refinement.

That observation is insufficient for oracle qualification. The first-cycle recovery fractions were 0.2273, 0.2335, 0.2386, and 0.2216, all far below the frozen minimum 0.7. At the beginning of the second cycle, the ROI was already substantially transformed: the pre-cycle ROI fraction was 0.2810, 0.2645, 0.2599, and 0.2686. Consequently, no second upward crossing from below the event threshold occurred. Relative cycle-peak drift ranged from 1.409 to 1.587, compared with the maximum 0.2.

Figure 4 shows the mechanism directly. The first pulse drives a localized phase increase near the bottom heater. The off interval cools the domain but does not reverse enough of the phase transformation. The second pulse therefore grows an existing transformed region rather than producing a new formation–recovery event. Calling this “two switching cycles” would conflate persistent phase occupancy with repeated event formation.

![ROI phase fraction and reduced temperature over two cycles for the nominal resolutions.](figures/figure-04-event-trajectories.png)

**Figure 4.** Nominal event trajectories. All tested resolutions show a first threshold crossing, insufficient recovery during the off interval, and no new upward crossing in cycle 2. The dashed horizontal line marks the frozen event threshold; the dotted waveform and all thresholds were fixed independently of the result.

### 4.3 Space, time, and replay comparisons

Six predeclared comparison components were evaluated: ROI phase-field RMS, ROI temperature RMS, terminal-current RMS, event-time difference, phase-region symmetric difference, and recovery difference. Coarse-to-medium differences were `[0.115296, 0.0130288, 0.0121576, 0.00403051, 0.0113184, 0.0446725]`. Medium-to-fine differences decreased to `[0.0440896, 0.00427422, 0.00384497, 0.00149082, 0.00381858, 0.0182278]`. Medium-to-half-time-step differences were `[0.0242407, 0.00318648, 0.00267207, 0.00117851, 0.00198254, 0.00858333]`.

The exact replay of the fine nominal case returned zero for every component. The raw array values also matched exactly; the files differ only because the immutable metadata records a distinct replay control identity. This rules out replay variability above the frozen $10^{-12}$ component limit for this deterministic path.

These convergence-like observations do not override the event failure. They show that the inadequate recovery and missing second event are not artifacts that disappear in the tested refinement sequence. Because a required control also failed, no component floor was sealed for neural work.

![Six-component space, time, and replay diagnostics.](figures/figure-05-convergence-controls.png)

**Figure 5.** Unclipped six-component comparison vectors. Medium-to-fine differences are smaller than coarse-to-medium differences and exact replay is zero, yet the event contract remains false. Numerical refinement, determinism, and event suitability are distinct properties.

### 4.4 Causal control and terminal execution failure

Turning off Joule gain in the medium configuration removes the driven temperature rise and event. The nominal-minus-Joule-off peak reduced-temperature difference is 1.075707, compared with a joint space/time uncertainty of 0.002399. The peak ROI phase-fraction difference is 0.892562, compared with an uncertainty of 0.025157. Thus Joule heating has a resolved causal effect inside the synthetic model.

This control does not validate a material; it shows only that the frozen synthetic causal chain is active. Nor does it repair recovery. The next required control, which sets the phase conductivity ratio to one, failed before producing an evaluable result. The phase Newton line search reached its frozen minimum step. The failure was recorded as a consumed intent with 64.640625 process-CPU seconds. No coefficient, tolerance, time step, initial state, or intent order was changed afterward.

Intents 10–12 were not executed. The aggregate qualification cost was 1318.71875 process-CPU seconds, or 0.3663107639 process CPU core-hours, with 1339.3720109 seconds of summed single-thread wall time. One failed intent and zero rescues are recorded.

![Nominal versus Joule-off causal control and the final claim boundary.](figures/figure-06-causal-and-claim-boundary.png)

**Figure 6.** The synthetic Joule term has a resolved effect, but the benchmark fails the complete Oracle Gate because the event contract is false and a required control cannot execute under the frozen numerical contract. No neural floor or method result exists downstream.

## 5. Why no PINN was trained

The absence of a PINN table is not an omitted experiment. It is the outcome of the preregistered dependency graph. A PINN method comparison required a qualified traditional-solver trajectory, resolved and repeatable events, hard-guard compliance, completed causal controls, and sealed component floors. The event and control requirements failed. Training would therefore answer a different question: how accurately can a network approximate a trajectory that does not instantiate the preregistered two-cycle task?

That alternative might still be technically interesting, but it would not test the stated PHA-MF or field-selective KC hypothesis. PHA-MF was intended to allocate capacity near localized phase/hotspot structure across repeated events. KC was intended to redistribute phase-dynamics resolution across fast formation and slow recovery. Here the object does not recover enough to create the second event, and one control branch is numerically unavailable. Any apparent module gain could be dominated by persistent-state fitting, a changed task, or comparison to an inconsistent control.

Strong raw, global multi-frequency, generic monotone clock, adaptive pseudo-time, wider raw, extra-work raw, wrong-gate, and sampling controls were therefore all not reached. We do not report zero improvement, a failed hypothesis test, or a negative PINN result. The estimands do not exist under this run.

## 6. Discussion

### 6.1 Guard passing is not oracle qualification

The clearest lesson is that “the solver ran” is too coarse a status. Four layers must remain separate.

First, implementation checks test selected algebraic and discrete properties on manufactured or zero-drive states. Second, numerical checks test finite values, residuals, balances, resolution sensitivity, and replay. Third, event qualification asks whether the trajectory realizes the scientific task—in this case two localized formation–recovery events. Fourth, method evaluation asks whether a neural method improves on a qualified reference under fair splits and compute. PHK-V2 passes important parts of the first two layers, fails the third, and never enters the fourth.

This decomposition prevents two common interpretive errors. One is to call a first threshold crossing an oracle even though the repeated protocol begins its second cycle from a different branch. The other is to call a failed control a causal result. Here the Joule-off control is informative because it completes; the phase-conductivity-off failure is compute evidence, not a scientific comparison.

### 6.2 Negative qualification results constrain future design

The result identifies a concrete mismatch between the frozen object and task: phase relaxation is too weak relative to the one-unit period to support the requested formation–recovery repetition. It also identifies a numerical fragility in a constitutive control branch. These observations can guide a future contract, but they do not authorize one.

A future study could choose a longer recovery period, a reversible phase potential, a different mobility law, or a solver designed for the control branch. It could instead change the scientific task from repeated formation–recovery to cumulative programming. Each choice changes the object or event identity. It must therefore be preregistered as a new benchmark rather than used to retroactively rescue this one. The existing result remains valuable precisely because the thresholds and coefficients were not moved after observation.

### 6.3 Implications for phase-field PINN studies

The source audit also shows why “use the strongest open paper as the baseline” requires more precision. Paper methods, current repositories, licenses, budgets, and hardware may define different identities. Sharp-PINNs is a strong domain anchor, but its paper and repository recipes differ. PF-PINNs changes sampling support. PirateNet supplies stronger multi-seed architecture evidence but has a restrictive original code license; jaxpi2 is more open but its pseudo-time results are a 2026 preprint and were produced on different hardware. A fair PHK study would need several matched controls rather than a single convenient baseline.

The proposed PHA-MF and KC modules remain hypotheses. Their most important controls are already identifiable: global multi-frequency versus routed capacity; generic monotone time mapping and re-spacing versus field-selective KC; adaptive pseudo-time versus physical-time warping; and wider/extra-work raw networks versus added complexity. The present stop prevents those good controls from being applied to a scientifically unsuitable trajectory.

### 6.4 What the bounded Joule control does and does not show

The Joule-off comparison confirms that the explicit source term drives a thermal and phase response well above the tested numerical uncertainty. This is useful evidence that the code contains an operative electric–thermal–phase chain. It does not show that the coefficients represent a particular oxide, that the current is calibrated, or that the synthetic phase fraction corresponds to a measured crystalline fraction. Nor does it show that latent heat or phase-dependent conductivity is necessary, because those controls were not both completed.

## 7. Limitations

The most important limitation is the intended one: no PINN method was evaluated. This manuscript cannot support claims about PHA-MF, KC, their interaction, adaptive pseudo-time, sample efficiency, GPU cost, OOD generalization, or state of the art.

The physical object is dimensionless and reduced. It lacks experimentally anchored transport, crystallization kinetics, threshold switching, nucleation statistics, thermal boundary resistance calibration, and circuit dynamics. It is a benchmark candidate, not a predictive device model.

The numerical qualification is bounded to the frozen finite-volume scheme, grids, time steps, controls, and tolerances. Passing manufactured and replay checks does not prove global code correctness. The Jacobian check probes a declared direction, not every state direction. The phase-conductivity-off failure may be specific to the frozen solver/control combination.

The external baseline work is source-identity and module-smoke evidence. Paper metrics, multi-seed uncertainty, and matched-hardware cost were not reproduced. The fixed code trees have different licenses; this package does not redistribute their source.

Finally, a negative benchmark-qualification paper is not equivalent to the originally targeted positive Q2-level PINN method paper. Its contribution is methodological transparency and reusable failure evidence. Journal fit and acceptance remain unknown.

## 8. Conclusion

We preregistered a positive phase-field PINN study with two PCM-oriented modules, but required the benchmark to qualify first. The transparent two-dimensional electrothermal phase-field object passed manufactured, zero-drive, balance, residual, refinement, and deterministic replay checks. It still failed the intended scientific task: recovery remained far below threshold, the second event was absent, cycle peaks drifted excessively, and a required constitutive control failed under the frozen phase Newton line search. The correct endpoint was therefore an Oracle No-Go before PINN training.

The result demonstrates a practical rule for physics-informed learning: approximation evidence should be downstream of object, numerical, event, and control qualification. When those gates disagree, the more specific scientific gate must decide the claim. Preserving that disagreement is more informative than converting an unqualified trajectory into a benchmark label.

## Data, code, and reproducibility

The local evidence package includes the machine-readable program, object, and split contracts; implementation and evaluator code; immutable intent manifests; numerical carriers for all completed field-producing runs; the terminal summary; tests; figure source data and generator; the supplement; and a claim–evidence matrix. Exact paths, commands, environment boundaries, and hashes are listed in `reproducibility.md` and `package-manifest.json`.

External repositories were used only as fixed, isolated source/module identities and are not redistributed in this package. The present package authorizes neither submission nor external publication. A repository synchronization event, if separately authorized, establishes traceability only and does not change the scientific claim ceiling.

## References

The machine-readable bibliography is provided in `references.bib`. Citation keys used in this manuscript are: `raissi2019pinn`, `chen2025sharp`, `chen2025pf`, `wang2024pirate`, `wang2026pseudotime`, `wang2026rbar`, `madir2025phasechange`, `miquel2024pcm`, `wang2024causal`, and `wang2022ntk`.
