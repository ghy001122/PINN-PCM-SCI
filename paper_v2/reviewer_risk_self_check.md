# Reviewer-risk self-check

## Highest-risk questions

### 1. “Where is the PINN result?”

There is none. The paper is explicitly a benchmark/oracle-qualification and failure-preservation study. The preregistered gate required a repeatable event and completed causal controls before neural training. Those conditions failed. The manuscript must not be submitted to a venue expecting a positive new PINN architecture without reframing its scope or conducting a separately authorized new study.

### 2. “Is this a real phase-change-memory model?”

No. It is a transparent dimensionless electrothermal phase-field wall-cell inspired by the topology and causal chain in the PCM literature. It is not calibrated to a material, fitted to a device, or validated experimentally. This boundary appears in the title context, abstract, methods, limitations, figures, and claim matrix.

### 3. “Why is a first threshold crossing not enough?”

The frozen task required two formation–recovery cycles. Recovery after cycle 1 is only about 0.22–0.24 and the phase fraction remains above the event threshold before cycle 2. The second pulse therefore does not produce a new upward crossing. Changing to a cumulative-programming endpoint after seeing this would be outcome-adaptive task substitution.

### 4. “Could a smaller time step or finer grid rescue the event?”

The tested medium/fine and medium/half-time-step component differences decrease, exact replay is zero, and all configurations show the same qualitative event failure. This is bounded evidence, not a convergence theorem. Additional rescue is prohibited by the frozen ladder and would define a new study.

### 5. “Why stop after intent 9 rather than run the remaining controls?”

The ladder was sequential and a numerical exception consumed the scheduled intent. Running later controls after the terminal failure would violate the preregistered qualification identity and failed-compute accounting. Intents 10–12 are reported as not reached, not as scientific failures.

### 6. “Does the Joule-off result validate the physical mechanism?”

It validates only that the explicit synthetic Joule term causes a response above tested numerical uncertainty. It does not validate coefficients, material mechanisms, or experiments. Phase-conductivity and latent-heat necessity were not established.

### 7. “Are the external baselines really reproduced?”

No. Their source, commit, license, and module import/forward/backward identities were checked. Paper-level accuracy and cost were not reproduced. The manuscript says module smoke, never benchmark reproduction.

### 8. “Is the negative result merely a bad parameter choice?”

The coefficients are engineering values and may indeed be unsuitable for the intended repeated event. That is precisely why the object was required to qualify before becoming a neural benchmark. The claim is not that these coefficients are optimal; it is that the frozen object did not pass and was not rescued after observation.

## Submission-positioning boundary

This package is a complete local V2 draft, not a claim that the originally desired positive Q2 PINN method paper has been achieved. Plausible audiences are reproducible computational science, benchmark methodology, numerical verification, or negative-results venues. A positive PINN-method submission still requires a new qualified object, strong baselines, attributed modules, and sealed complete-case/OOD evidence.

## Internal consistency checklist

- [x] Every reported numerical value traces to an immutable result/report/summary.
- [x] Failed compute is included in gross accounting.
- [x] Not-reached stages are not shown as zero or failed methods.
- [x] Figure captions state the synthetic and no-PINN boundary.
- [x] Source-paper and repository identities are separated.
- [x] External license restrictions are recorded and source trees are not packaged.
- [x] No material, experimental, speedup, superiority, OOD, SOTA, or acceptance claim is made.
- [x] Future rescue options are identified only as new-study hypotheses.

