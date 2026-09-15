# V31 reproduction and information boundary

Use the accepted fixed endpoints, full-gradient optimizer states and frozen configurations in evidence. Stage A's original E0, sparse data and unchanged integration pools remain in V28/V24; the two fresh initial states and common parent fits are in evidence/confirmation. This campaign uses only known physics and the established visible sparse observations for learning. Full fields and reference data stay in local run storage. Current runtime receipts and raw operational metadata remain local; a derived public summary distinguishes them from scientific evidence.

Render saved results without training or solving:

```powershell
.\.venv\Scripts\python.exe -m pinn_pcm_sci.phk_v23_lf11_fullgrid_report --root paper/paper_v31/evidence --confirmation paper/paper_v31/evidence/confirmation
```

The selected package includes phase-figure-input.npz, containing only the saved phase snapshots used by the historical comparison figure. This makes figure rendering independent of the full local historical run directories. It does not contain a full reference trajectory. New-pair metrics, decisions, traces, common fits and accepted endpoints are in evidence/confirmation.

Separately authorized reproduction in an empty run directory uses phk_v23_lf11_fullgrid all with lf11_fullgrid_sprint.json; clean pairs use phk_v23_lf11_clean_confirmation with the locked-soft-selection.json generated after Stage A. Every complete/trial L-BFGS evaluation is counted. Training explicitly retains the original 128-cell RNG draws even though the electric term uses all 3200 cells. No new electric times, labels or thermal trajectories enter the comparison. Existing V30 defaults remain sampled. The source manifest identifies the actually deployed implementation; later local evaluation/report code does not retroactively replace it.

After recovery and actual instance shutdown, the fullgrid_evaluate module scores the fixed paired predictions. It uses the original metrics, electrical readout, A/B rules and event criteria. Clean confirmation used phk_v23_lf11_clean_confirmation after the unique comparator selection; both actually executed pairs are recorded under confirmation/seed-29 and confirmation/seed-43. No trained historical checkpoint entered the clean-parent fit, and reference results were not read between the two seed runs. New parent scales are shared within each pair, with one frozen per-parent calibration. All seed history, events and failures are retained. The two new seeds are not pooled with the historical seed.

The clean-stage configuration inherits the Stage A template. Its top-level budget and parameter_change text describe Stage A; the effective clean-stage limits are the confirmation block, the per_E_forward_limit of 27000, and the user-authorized two-pair protocol. Actual per-seed counts are reported separately. Stage A exact executed sources are retained in runtime-sources; Stage B separately deployed sources are retained in runtime-sources-stage-B. Neither current local source edits nor a later renderer replace those execution snapshots.

Generic optimizers, sparse solves, implicit differentiation, volume quadrature and the scalar balancing rule remain attributed tools. This package records a bounded method experiment, not new solver theory or experimental device validation.
