# LF11 V continuation and contact-control reproduction

The actual run is `outputs/runs/20260912-lf11-v-pde-increment` in the Windows project root. The inherited release is `8a0f1a0952db57de2b5d0907e26981dcd3264076`. This selected package accompanies the paper_v26 release under subsequent user authorization; its containing Git commit identifies the new release. The publication task does not rerun the scientific experiment.

The user explicitly authorized `E:/PINN-PCM/Prompt_for_Research_Sprint_20260912.md`; its exact copy is in `docs/notes/2026-09-12-lf11-v-pde-authorized-sprint.md`. The two advisory reports disagreed about loss recalibration. The execution instruction explicitly retains old LF11 a0/b0; the frozen config follows that choice. These scalars never enter the actual V-only objective, and no new PDE arm is executed.

## Actual scientific path

1. Read the original local final S1 checkpoint and last V-only optimizer state. The equivalent archived inputs are in paper_v25/evidence. Load the model through `fit_model(config, state, temperature_adapter)`; restore only the V optimizer history. Do not load its older complete model over final T.
2. Open only V parameters. Run the unchanged complete weighted V observation objective using FP64, four CPU threads and PyTorch L-BFGS with history50, lr1, max_iter1 and strong-Wolfe. All 200 actual objective/gradient calls count; 99 steps are accepted. The final objective is 1.0522112986674133e-5, above the gate 8.333333333333334e-6.
3. Keep the last accepted state and optimizer. Exact non-V state and visible phase/T metrics are retained. There is no additional fitting, PDE training, normalization, new observation, stress read or GPU instance.
4. Reuse the S1 model's already saved full predictions for pre-V fields and unchanged post-V T/phase; predict only the new V field. Model boundary traces and first derivatives are newly evaluated on the same fixed geometry without reference labels. Save exact signed current/power decompositions, including edge/interior strata.
5. Freeze and verify B_logit_waveform_contact before reference evaluation. New x columns use the old spatial interpolant; only known bottom-heater values change. The 5.55e-17 preservation error is numerical roundoff.
6. With training already stopped, evaluate the fixed nominal reference once. Reuse old baseline results and traces. The same original metrics and denominators are used. No checkpoint selection follows reference evaluation.

The config's unused `evaluation.normalization_floor=1e-14` metadata differs from the inherited evaluator's actual 1e-12 floor. The execution instruction specifies the inherited metrics, which were used. All relevant native reference scales are far above both floors; [evaluation-scale note](evidence/evaluation-scale-note.json) documents that no value or decision is affected. The original frozen file is retained, not silently rewritten.

## Entry points

These commands describe a fresh, separately authorized reproduction, not a request to rerun completed science:

```powershell
# First create an empty run directory and retain the original input paths in config.
.\.venv\Scripts\python.exe -m pinn_pcm_sci.phk_v23_lf11_v_continue --root outputs/reproduction/lf11-v-new
.\.venv\Scripts\python.exe -m pinn_pcm_sci.phk_v23_lf11_electric_trace_audit --root outputs/reproduction/lf11-v-new
```

The audit currently expects the original local S1 prediction carrier at the path in its source. It is an own-model prediction, not a teacher field. A fresh checkout must regenerate that carrier from the published S1 model or obtain the original local carrier; it need not retrain S1. Full-grid carriers and the reference are not part of the small selected package. Their absence limits a public-only full numerical rerun.

The actual evaluation source is `phk_v23_lf11_v_evaluate.py`. It checks compute closure and exact axes; it only opens the nominal control and refuses an existing evaluation. A replay to a different directory calls its `evaluate(root)` function with that directory after recording real training-process closure. Do not fabricate closure for a live training process.

Figures and tables can be rebuilt from saved records without training, a PDE solve, or new reference access:

```powershell
.\.venv\Scripts\python.exe -m pinn_pcm_sci.phk_v23_lf11_v_report
```

Targeted verification covered full weighted head objectives and derivatives, nonempty-history rollback, first-accepted-state stopping, exact signed FV decomposition including a negative cross term, and preservation of sparse observations by the new contact knots. Completed training was not repeated. No backend-transfer, independent-seed or generalization claim is made.
