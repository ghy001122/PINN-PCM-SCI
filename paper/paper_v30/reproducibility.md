# Reproduction: training-time electrical coupling versus post-hoc repair

Work root: `E:\Python demo\PINN-PCM-SCI`. Inherited released code: `59e3a5a5cd4c2224f4dbaab5f16de299b0607a9d`. The selected deployed-source manifest records the actual new runtime sources. This campaign was authorized for implementation, numerical work and a local paper update; it does not automatically authorize publication or another execution.

## Rebuild existing tables and figures without numerical experiments

```powershell
.\.venv\Scripts\python.exe -m pinn_pcm_sci.phk_v23_lf11_training_coupling_report --root paper/paper_v30/evidence
```

This consumes only saved JSON and plotting traces. It does not open scientific checkpoints or the full reference, train, or solve an electrical system. The authored manuscript and its historical qualifications are not overwritten by the report entry point. Each plot has a PNG and standalone PDF companion.

## Exact roles and inputs

The new F_raw and F_bal use the V28 E0 parent (`paper/paper_v28/evidence/parent.pt`), including original V/T/phase heads and final T adapter. All trainable parameters are opened jointly. Neither the V28 trained D_E parent nor a V29 endpoint is substituted. Optimizers start fresh. The sole label source is `paper/paper_v24/evidence/input/sparse.npz`. Calibration, L-BFGS and audit pools plus original aE/bE are copied unchanged from V28. E is the fixed V28 P_E endpoint; it is not retrained. D_E, B_E and E0 are reused, and V29 endpoints are explicitly different-history background.

The initial V function differs: E uses an electrical solution while F uses the original network head. This tests a complete training-method package, including different voltage-observation maps and active parameters. It does not isolate VJP alone. The existing sparse observations have already been exposed; neither new labels nor a clean holdout are created.

E enforces all 3200 electrical balances at a used training time. The current F electric penalty retains the original 128-cell sample even though the explicit face operation is computed over the full grid. This enforcement distinction is disclosed as part of the method package. It is not silently changed to a full-grid soft average during the comparison.

## Objective, numerical interface and one calibration

F_raw uses C_F+F_Tphi+E_e; F_bal changes only the coefficient of E_e. Here E_e=λ Eρ[(AσV−f)²/cell_volume²]/(3bE). Thermal and phase scales remain 4 and 5, electric scale is 1, and BC/IC denominators remain 13 and 3. Harmonic face conductances, heater overlap, half-resistance deposition and the thermal cell residual are common with E. The full explicit conductivity/Joule gradient is retained in F, with zero training linear solves or adjoints. The electrical boundary already enters this face network; a separate incompatible electrical BC average is not added.

At E0, λ=0.1 and the original calibration pool, one scan per actual weighted block computes gobs, gBCIC, gT, gphi and ge over all active F parameters. ηbal equals the root sum of the first four squared norms divided by ||ge||. The saved calibration includes all five full vectors, parameter layout, coefficient, scalar objectives and work counters. It is frozen once; no reference-based selection, clipping of the coefficient or dynamic balancing occurs. The numerical floor is 1e−12 and equivalence with one uses rtol 1e−6, atol 1e−12.

A small artificial 8×4 grid with an 8×2 network verifies the inherited η=1 target and complete gradient, the sum of weighted-block derivatives and a central full-parameter direction. This test uses no scientific checkpoint. A separate synthetic adjudication check prohibits mixing A against one control with B against another and prohibits victories over incomplete controls. These checks address new interfaces, not repeated physical qualification.

## Frozen optimization and counting

Each arm has up to 1500 Adam updates followed by 300 complete L-BFGS objective/gradient evaluations. Adam uses lr 1e−4, betas (0.9,0.999), eps 1e−8 and clipping norm 10. Both random streams and the 500/1000/1500 checkpoint nodes are shared. λ ramps over 200 updates to 0.1. Batch losses from different draws cannot be read as a common-objective convergence curve.

The fixed stage uses complete observations and the inherited 32-time integration pool with its original weights and 128 physical cells per time. L-BFGS is fresh, with strong Wolfe, lr 1, max_iter 1, history 50, gradient tolerance 1e−10 and change tolerance 1e−14. Every initial, repeated and line-search trial closure counts. No resampling, dynamic weighting or gradient clipping occurs in those closures. An interrupted trial restores both the model and optimizer to the last accepted state. The terminal stores actual accepted steps and the reason for stopping; Adam counters do not count L-BFGS updates.

The method predicate requires two numerically valid and complete controls. The local evaluator's completion definition was set during training before reference access: the full Adam budget plus either the complete fixed-stage cap or documented gradient convergence. An internal failed line search or no accepted progress may leave a finite diagnostic endpoint but cannot establish E's superiority. Missing controls are not counted as losses, and no arm-specific retry or reallocation is allowed.

F has no linear solve during training. Its explicit matrix-vector products, full-grid network evaluations, AD groups and observation groups are counted separately. At observation-only times, the direct V head needs no redundant full-grid electrical operation; the inherited objective and derivative are unchanged. Two soft configurations together are not described as equal compute to one E run. No wall-clock acceleration is claimed.

The inherited backend may record `forward_queries` and `zero_drive_queries` for analytic zero-drive returns. These are not numerical linear solves. Powered F groups use explicit face operations, accounted for in `statistics.explicit_work`; they do not pass through the solver-query counter. Actual factorization/forward-solve/adjoint-solve fields remain the relevant solve counts.

## Paired prediction and subsequent scoring

Each fixed F model is evaluated on the original 160×80 grid and 1001 times. The network readout is retained unchanged. Projected inference reuses its exact T/phase arrays, solves voltage from their own conductivity and known boundaries, then uses the same FV current and Joule readout. No new field, derivative, current or power label is supplied. No parameter gradient or new thermal/phase trajectory is computed. The original cap is 278 nonzero-time solves per arm, 556 total; zero voltage uses the analytic zero solution. Any explicitly authorized one-solve recovery amendment is recorded separately without changing the frozen scientific configuration; actual successful and discarded inference counts are both retained.

The paired-readout identity asserts exact T/phase equality. Evaluation also requires identical S/Ephi/ET and complete cycle summaries. The changed q is not claimed to make the old T/phase functions dynamically consistent. Full numerical predictions stay in the local run; compact traces, event summaries, metrics and readout identities support the paper.

Both required projected controls must be beaten on the same frozen A or B layer. Original noninferiority tolerances and independent strict event gates are preserved. Layer-mixing, comparing only to network voltages, or choosing one favorable F configuration cannot establish the claim. Electrical residual, terminal equality and power conservation are related consequences of the same solved system, not independent empirical gains.

## Environment and lifecycle

The actual platform was read as Python 3.11.9, PyTorch 2.5.1+cu118, NumPy 2.1.1 and SciPy 1.14.1 on a V100. Network and differentiable explicit face work use FP64. Projected inference uses the existing sparse SuperLU backend; it requires no training adjoint.

The initial SSH dispatch connection timed out after the background job started. The actual remote process was confirmed alive, and no scientific restart occurred. A local supervisor watches only this isolated job, recovers its archive, verifies recovery, issues authenticated shutdown and confirms that the current endpoint refuses connections. Reference scoring happens locally afterwards. The receipt's `reference_read: false` describes its shutdown instant; the later evaluation timestamp records the subsequent reference access.

Source files in the cloud bundle exclude the full reference, stress and the local scoring module. The selected-source record and current compute-closure receipt are retained. Scientific training sources stayed frozen through both endpoints. The cloud inference then failed after one powered electrical solve because an inherited helper inserted potential into a shared dictionary and the wrapper inadvertently required network and projected voltages to be equal. Temperature and phase were unchanged. A copied mapping and an explicit T/phase key list fixed the assertion; a mocked regression with unequal voltages and identical T/phase passed without a solve or checkpoint. After verified recovery and actual shutdown, fixed-endpoint prediction was completed locally on CPU with per-time persistence. No training was repeated. The original cloud exit code 1 and its combined-job incomplete flag remain unchanged; the separate local completion receipt records the successful recovery. The discarded powered solve is counted, and its narrowly requested budget amendment is preserved separately. Reference scoring is allowed only after complete paired inference and verified GPU shutdown.

Publication scope: original deployment/shutdown receipts, raw cloud log and operational cloud wrappers remain local because they contain connection metadata. The public evidence instead includes an explicitly derived execution summary without destinations or key paths; it is not a copy of the original operational receipt. Scientific configuration, code, endpoint weights, gradients, numerical results and failure/completion facts are preserved. Runtime source manifests may name local-only wrapper files; those entries document actual deployment, not a promise that every operational file is published.

## Recover this documented inference interruption

The repaired prediction module provides `--recover --arm F_raw` and `--recover --arm F_bal` for the current run. It reuses saved per-time arrays; completed electrical points are never recomputed. Before a one-solve amendment is authorized, `--skip-lost-point` leaves the discarded first powered F_raw point visibly incomplete. The original failed cloud solve counts against the per-role cap. The separate completion receipt can be written only after both paired-readout identities exist and both frozen training terminals are retained. This recovery is inference only, with the actual GPU kept off.

## Interfaces for a separately authorized repeat

These interfaces describe reproduction and do not authorize rerunning a completed experiment. A repeat needs an empty run directory and its own recovery/shutdown receipt:

```powershell
.\.venv\Scripts\python.exe -m pinn_pcm_sci.phk_v23_lf11_training_coupling all --root outputs/runs/NEW_AUTHORIZED_RUN --device cuda:0
# Only after that run's actual recovery and confirmed shutdown:
.\.venv\Scripts\python.exe -m pinn_pcm_sci.phk_v23_lf11_training_coupling_evaluate --root outputs/runs/NEW_AUTHORIZED_RUN
```

Full scoring also requires the local reference and complete own-field predictions, absent from the compact evidence package. The current task never opens sealed stress. Any independent-initialization, clean-observation or complete-case confirmation is a separate proposed experiment, not an implicit continuation of this one.


## Actual terminal counts

| role | status | Adam | evaluations | accepted | forward | adjoint | projection | failed_projection | eta | full_grid_network | explicit_faces | thermal_phase_groups | observation_groups |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| F_raw | EVALUATION_BUDGET_EXHAUSTED_TRIAL_ROLLED_BACK | 1500 | 300 | 146 | 0 | 0 | 279 | 1 | 1 | 7800 | 7800 | 15600 | 43734 |
| F_bal | EVALUATION_BUDGET_EXHAUSTED_TRIAL_ROLLED_BACK | 1500 | 300 | 144 | 0 | 0 | 278 | 0 | 0.0254939372 | 7800 | 7800 | 15600 | 43734 |


## Conditional numerical check

NOT_TRIGGERED_MAIN_METHOD_SIGNAL_ESTABLISHED: The frozen B layer passes against both valid complete projected controls. The predeclared numerical-sensitivity branch requires no main increment plus a next decision depending on the thermal interface; that prerequisite is false. Preserve the present interface and plan independent/strong-control confirmation instead.
