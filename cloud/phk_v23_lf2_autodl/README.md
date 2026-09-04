# PHK-V2.3 LF2 AutoDL deployment

This bundle runs exactly one seed-17 V100 FP64 trajectory for
`PHK_V23_LF2_MEASURE_CALIBRATED_FEASIBLE_PINN_EXECUTE`.

Only the hash-bound source archive, passed CPU qualification, medium carrier,
and exact LF1-B0 checkpoint may exist in the deployment root. Fine,
extra-fine, frozen-evaluator, and stress files are forbidden. Run the zero-step
preflight with the live hourly price before starting `pinn_pcm_sci.phk_v23_lf2`.

M0 performs 1200 target-measure data-only updates and never constructs or
advances the physics sampler. M1 is conditional on the frozen M0 full-medium
gate and, if entered, performs exactly 1200 full-physics updates with the LF1
stepwise-identical physics batches. No telemetry checkpoint selects the result.

After the process ends, recover every summary-bound artifact, verify all
hashes locally, then shut down the instance and verify SSH refusal before any
fine/extra-fine reference or frozen evaluator is read. A scientific retry is
not authorized after the first optimizer update.
