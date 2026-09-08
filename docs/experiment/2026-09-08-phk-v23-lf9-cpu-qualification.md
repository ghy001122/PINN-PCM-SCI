# PHK-V2.3 LF9 CPU qualification

- `task_id`: `PHK_V23_LF9_EQUATION_ROUTED_THERMAL_CONTROL_VOLUME_REFINEMENT_EXECUTE`
- `gate_outcome`: `LF9_CPU_QUALIFICATION_PASS`
- `scientific_optimizer_updates`: `0`
- `device/dtype`: `CPU/FLOAT64`
- `evidence_identity`: `ENGINEERING_QUALIFICATION_ONLY`

## Verified qualification

The exact DEV-R checkpoint, medium audit carrier and inherited 1,200-step strong
ledger passed their frozen bindings. CPU materialization produced 1,200 × 16
training cell-slabs, 192 disjoint one-cell blind slabs and 192 disjoint 2×2-cell
blind slabs. Training patches follow the inherited accepted-step causal-window
schedule and are mutually disjoint from both blind supports at elementary
`(cell_x, cell_z, time_interval)` identity.

Constant, linear-time and quadratic-space control-volume identities passed. The
equation-routing check retained coupling-coordinate derivatives while assigning
only each equation's gradient to its owning field head. A real nonempty-Adam
two-cycle rollback test restored the full state exactly without a scientific
optimizer update.

## Frozen normalization and DEV-R blind baselines

- `r_cv0_rms = 0.7097646689156927`
- `L_T_strong0 = L_T_CV0 = 0.03258119801290102`
- `s_cv = 3.932157024118817`
- `J_S = 4.9278721846990505`
- `J_M = 4.925521658963255`
- `CV1 = 0.01198042763327962`
- `CV4 = 0.008291401447887748`

The compact [artifact](artifacts/20260908T145333Z-phk-v23-lf9-cpu-qualification.json)
and canonical [manifest](manifests/20260908T145333Z-phk-v23-lf9-cpu-qualification.json)
bind the CV ledger, its streams and array identities. Fine, extra-fine, direct
`LF_ONLY`, the frozen local evaluator and both stress references were not read.
This gate authorizes the two frozen GPU screens; it is not method evidence.
