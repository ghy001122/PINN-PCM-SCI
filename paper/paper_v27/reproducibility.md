# Reproduction of the specified-parent boundary/PDE comparison

The local run is `outputs/runs/20260912-lf11-joint-bc-pde` under the project root. Its frozen input configuration is `configs/phk_v23/lf11_joint_sprint.json`. The exact [execution instruction](../../docs/notes/2026-09-12-lf11-joint-authorized-sprint.md) takes precedence over the [advisory review](../../docs/notes/2026-09-12-lf11-v26-independent-review-plan.md), including the 1500-Adam/300-evaluation main-arm budgets. The inherited source release is `4c16ba2ece84d4dd0c561f22ff91fe5b4932cfc6`. The containing Git commit identifies this later, user-authorized paper_v27 release. Runtime manifests remain unchanged historical snapshots and are not rewritten to claim publication at execution time.

## Inputs and identity

- Actual parent: `outputs/runs/20260912-lf11-v-pde-increment/v_continue/checkpoint.pt`; its released equivalent is `paper/paper_v26/evidence/endpoint-with-V-optimizer.pt`.
- Actual sparse bundle: `outputs/runs/20260910-lf11-sparse-metric-sprint/input/sparse.npz`; its released equivalent is `paper/paper_v24/evidence/input/sparse.npz`.
- `fit_model(config, state, adapter=True)` loads the complete final model. The existing temperature adapter remains present. Each arm opens all parameters and starts fresh optimizers; the old V optimizer history is not inherited.
- The observation mask, equations, constitutive coefficients, output mapping, BC/IC terms, and original residual scales are unchanged. All old observations have training/development status.

`training-source.json` captures the relevant runtime source identity before the first update. `input-identity.json` identifies the actual parent and sparse bundle once. `calibration.json` contains exact full-observation `a_star` and one fixed unlabeled calibration `b_star`; no arm recalibrates them. `fixed-pools.pt` preserves distinct calibration, L-BFGS, and independent audit pools. Parent/endpoint audit ratios must use the same audit pool, not a calibration-pool denominator.

## Scientific path and entry points

These are reproduction instructions for a new empty destination, not permission to rerun this completed trajectory. The training entry refuses an already-started root. The default source configuration references original local input paths; a public-only checkout must supply the released equivalents at those paths or declare the path substitution in a separate reproduction configuration.

```powershell
.\.venv\Scripts\python.exe -m pinn_pcm_sci.phk_v23_lf11_joint --root outputs/reproduction/lf11-joint-new
```

The role directories save Adam checkpoints at 500/1000/1500, random-generator states, telemetry, the final model with accepted L-BFGS state, and actual evaluation counts. Every initial, repeated, and trial L-BFGS closure counts. Line-search interruption restores the accepted model and optimizer. Scientific training is not repeated to improve reference scores.

After the training process really exits, record `compute-closure.json` with its actual campaign PID and process-exit evidence. The postprocessor refuses reference evaluation without training completion and stopped-compute fields. Do not create a false closure for a live process. No cloud instance is needed for this CPU execution.

```powershell
.\.venv\Scripts\python.exe -m pinn_pcm_sci.phk_v23_lf11_joint_diagnosis --root outputs/reproduction/lf11-joint-new
.\.venv\Scripts\python.exe -m pinn_pcm_sci.phk_v23_lf11_joint_evaluate prepare --root outputs/reproduction/lf11-joint-new
.\.venv\Scripts\python.exe -m pinn_pcm_sci.phk_v23_lf11_joint_evaluate evaluate --root outputs/reproduction/lf11-joint-new
```

Diagnosis uses only the three saved P_U Adam states, their next batches, and the complete visible targets. It executes no optimizer step. The optional `--node 500` (or 1000/1500) computes a saved node once; the final diagnosis reuses these cached records and requires all three nodes. It may run during another fixed training stage because it reads no reference and does not affect training. The prospective Adam denominator, historical momentum, source components, and total proposal are recorded separately. Amplitude separation is a diagnostic product-rule calculation; training has no detached conductivity gradient.

`prepare` generates each valid endpoint's own full fields and boundary/AD audits without reference labels. The optional `prepare --roles D_I D_B` can do this for already fixed arms while P_U trains; it requires their completed result records and reads no reference. The final `prepare` reuses those own-field carriers. `evaluate` always requires actual complete-campaign closure, then reads the existing nominal reference and verifies the inherited identity and axes. Parent and strong-baseline metrics/traces are reused from the original v26 evaluation, with historical LF11 network roles explicitly prefixed to avoid name collisions. Only new fixed endpoints receive new reference evaluation. The reference peak times choose illustration snapshots, not checkpoints.

The current evaluator also expects the old v26 `evaluation.json`, trace arrays, parent own-field carrier, and contact-baseline carrier at their original local run paths. The inherited models/baseline implementation can regenerate their own fields without a teacher or retraining; the selected published package does not itself include all full-field carriers or the high-resolution reference. Consequently, a public-only checkout supports selected-evidence review and figure reproduction but does not by itself supply every array for a full numerical reevaluation.

After the D_I/D_B own-field audits showed aggregate BC improvement with a worse heater trace, a scalar BC-subterm split was added on the same already frozen endpoint audit pool. Its purpose is to distinguish a subcondition tradeoff from opposite heater trends under the pool and the complete contact curve. The parts reproduce the saved aggregate. It introduces no new pool, optimizer update, equation-by-head gradient node, or reference read, and cannot change a frozen endpoint. Each role's `boundary-subterms.json` records that scope.

## Conditional electrical-block stage

The completed main endpoints and the three cached Adam diagnostics determine the original trigger in `conditional-decision.json`. A trigger is an execution condition, not a method-success claim. The preparation entry refuses an untriggered or already prepared stage. It copies the original parent, `a_star/b_star`, and fixed pools, then calibrates the normalized block once without reference values. The global-scalar control matches its full-parameter gradient norm at that same parent.

For a separately authorized reproduction, the conditional entry points are:

```powershell
.\.venv\Scripts\python.exe -m pinn_pcm_sci.phk_v23_lf11_joint_conditional prepare --root outputs/reproduction/lf11-joint-new
.\.venv\Scripts\python.exe -m pinn_pcm_sci.phk_v23_lf11_joint_conditional launch --root outputs/reproduction/lf11-joint-new/conditional
```

R loads the exact main `P_U/adam-1000.pt` prefix and performs its own fresh 200 fixed L-BFGS evaluations. It is not the main 1500+300 P_U endpoint. G and N each start fresh at the original common parent and perform 1000 Adam updates plus 200 fixed evaluations. All accepted/trial evaluations count. Reused R Adam updates are recorded separately and are not new execution. Full differentiation through conductivity is preserved in N; the amplitude/shape decomposition is used only in the earlier diagnosis.

The conditional controller waits for and reaps every worker before writing its own `compute-closure.json`. Generate endpoint fields and audits using `phk_v23_lf11_joint_evaluate.prepare(Path(conditional_root))`, then run the conditional evaluator:

On this Windows run, the virtual-environment launcher PID and the actual Python PID differed. The saved closure includes both the controller's launcher IDs and the worker-reported Python IDs; one process snapshot confirmed all six were absent before reference evaluation. This is an actual execution record, not reuse of an earlier shutdown claim.

```powershell
.\.venv\Scripts\python.exe -c "from pathlib import Path; from pinn_pcm_sci.phk_v23_lf11_joint_evaluate import prepare; prepare(Path('outputs/reproduction/lf11-joint-new/conditional'))"
.\.venv\Scripts\python.exe -m pinn_pcm_sci.phk_v23_lf11_joint_conditional_evaluate --root outputs/reproduction/lf11-joint-new/conditional
```

Only a positive **same** claim layer for N against both R and G permits `prepare-dn` followed by a separate launch under `conditional/dn`. That stage retains normalized insulation BC and removes all interior PDEs, with 1000 Adam updates and 200 evaluations. Its own closure, preparation and evaluation are required. Missing D_N evidence must be read with the saved trigger; availability of its code is not an executed comparison. No additional conditional mechanism follows it.

Actual disposition: R/G/N are all valid, with 98/97/97 accepted L-BFGS steps and exactly 200 evaluations each. Every conditional contrast fails both A and B; D_N is untriggered and unrun. Together with main D_I/D_B/P_U, the total is **6500 new Adam updates and 1500 complete fixed evaluations**, with no scientific retry, extra label, PDE solve or cloud instance. R's reused 1000 updates remain counted only in the main trajectory.

## Figures without training or reference access

```powershell
.\.venv\Scripts\python.exe -m pinn_pcm_sci.phk_v23_lf11_joint_report --root paper/paper_v27/evidence
```

This command consumes saved endpoint metrics, event/device traces, field snapshots, and electric-audit arrays. It does not train or solve a PDE. The parent contact audit is reused from the original v26 run. The selected evidence README provides its packaged location and the other saved carriers.

The conditional figure and tables are regenerated with `phk_v23_lf11_joint_conditional_report --root paper/paper_v27/evidence/conditional`. Both report modules support a separate `--paper` destination. Their numerical carriers are saved evidence, not a reason to reload checkpoints or reference fields.

## Meaningful verification and limits

Targeted checks cover exact full observation values and chunk-invariant gradients; preservation of the original nested BC/PDE coefficients and 13-term denominator; a fixed complete objective directional derivative; the analytic electric/insulation amplitude-plus-shape gradient split; and separation of reconstruction/function outcomes and the all-three-node conditional rule. These checks validate implementation semantics, not a positive scientific outcome.

The final records must be read with their actual numerical validity and stopping disposition. Common update/evaluation counts are not equal compute cost. This study provides no additional initialization, unseen mask, complete-case holdout, formal OOD, solver speedup, continuum-convergence proof, or material calibration. Neither the old 0.5% voltage admission nor its old unrun branches is retroactively changed.
