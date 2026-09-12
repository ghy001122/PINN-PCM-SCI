# LF11 follow-up reproduction

Actual environment: Python 3.11.9, torch 2.5.1+cpu, NumPy 2.1.1, FP64 and four CPU threads on Windows. Existing project dependencies were used; no new installation or cloud instance was needed.

The original LF11 source release is 6412dbf3c766207dfb5f586a94bac8eaa0f247d5. The follow-up modules are included with this paper_v25 release:

- `pinn_pcm_sci/phk_v23_lf11_followup.py`: visible envelope lower bound and original-parent audit.
- `pinn_pcm_sci/phk_v23_lf11_followup_fit.py`: the actual bounded fitting and accepted-state rollback.
- `pinn_pcm_sci/phk_v23_lf11_followup_evaluate.py`: one post-training fixed endpoint; only nominal reference access.
- `pinn_pcm_sci/phk_v23_lf11_followup_report.py`: tables, figures, manuscript and selected evidence from saved outputs.

Run root: `outputs/runs/20260911-lf11-followup-fit-electric-block`. Its frozen contract and fit plan are copied into [evidence](evidence/README.md). The same sparse bundle and original parent are resolved first from the original local LF11 run, falling back to paper_v24/evidence. S0 records their exact identities once. No complete medium field is opened by the fitting process.

The complete visible targets are already exposed by the inherited parent. They are training/development data. Heating/off metrics use conditional global quadrature; the global V/T metrics include the separately declared analytic IC weight. Phase raw RMS uses positive-time global weights; the logit objective retains the half-global/half-interface measure. In S1 phase is held fixed while the independent V/T observation components are optimized; no PDE gradient routing or old phase-freeze protocol is used.

The following are reproduction recipes for a **fresh directory**, not commands to overwrite the completed run or authorization for a new scientific experiment:

```powershell
.\.venv\Scripts\python.exe -m pinn_pcm_sci.phk_v23_lf11_followup --root outputs/reproduction/lf11-followup-new --stage s0
.\.venv\Scripts\python.exe -m pinn_pcm_sci.phk_v23_lf11_followup_fit --root outputs/reproduction/lf11-followup-new
```

S1 is allowed only when S0 does not preclude its temperature admission criteria. The actual run used 1200 Adam updates plus exactly 400 fixed complete component objective/gradient evaluations. L-BFGS calls are counted directly, including repeats and rejected trials; they are not equated with Adam updates or equal compute. Per-head optimizer snapshots are preserved as `s1/base_lbfgs_V.pt`, `base_lbfgs_T.pt`, `refinement_lbfgs_V.pt`, and `refinement_lbfgs_T.pt`; the two Adam checkpoints and fixed final state are also retained. Intermediate states are development checkpoints, not selected using high-fidelity feedback.

The final saved checkpoint can be inspected without training: read its config, model_state_dict and temperature_adapter flag, then call `fit_model(config, state, adapter)` from the fitting module. The final file does not claim to contain a joint Adam state after L-BFGS; actual per-stage optimizer states are in their separately named checkpoint files, also copied into [the publication package](evidence/optimizer-states/).

Before any full nominal evaluation, the training process must have ended and a current `compute-closure.json` plus `evaluation_contract.json` must exist. The actual receipts identify CPU-only execution and zero cloud instances. For the completed run:

```powershell
.\.venv\Scripts\python.exe -m pinn_pcm_sci.phk_v23_lf11_followup_evaluate --root outputs/runs/20260911-lf11-followup-fit-electric-block
```

The evaluator refuses an existing adjudication. It uses the original nominal extra-fine file named in `phk_v22r_evaluator.NOMINAL_REFERENCE`; it never calls a stress control. It predicts its own full V/T/phase fields, compares the frozen coordinate axes and uses the unchanged LF11 event/readout implementation. Older endpoints and baselines are reused from their saved records/traces. Additional power and bottom-current scores use those traces and the unchanged native scales. No old teacher current/power becomes a prediction.

To rebuild presentation artifacts from saved results without training or reference reads:

```powershell
.\.venv\Scripts\python.exe -m pinn_pcm_sci.phk_v23_lf11_followup_report --root outputs/runs/20260911-lf11-followup-fit-electric-block
```

The five targeted CPU tests cover zero-envelope interval distances, weighted chunk gradients against the actual model, budget-exhaustion rollback, evaluated accepted endpoints, and zero-output adapter insertion. Full training was run once, not repeated for verification. New D_B/P_U/R/N/G/D_N did not run because the final voltage criterion failed. No claim of reproducibility on an untested backend or statistical independence is made.
