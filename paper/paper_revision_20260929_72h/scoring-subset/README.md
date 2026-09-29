# Joint reconstruction: independent scoring subset

This directory is the completed portable **saved-array scoring** package for the new joint comparison only. Seed29 endpoints were recovered, locked and scored before source fields were packaged. It does not repeat the historical large data package. One actual scoring run in a separate directory passed with the research checkout denied; see `independent-verification.json` and `isolation-check.json`.

All three valid saved endpoints are retained: N/F completed 600 Adam updates and 100 L-BFGS evaluations each; S terminated after 187 evaluations and 75 accepted steps when the Wolfe check failed and the trial was rolled back. This optimizer stop is preserved in the original termination records and is not described as completion of 700 evaluations. The frozen development increment did not pass, so no seed43 result is invented or included.

After delivery, copy this entire directory to an independent location and run with Python 3.11 and NumPy 2.1.1:

```powershell
python score.py --root .
```

Every executable input path is relative to `--root`; an absolute path or a path escaping the root is rejected. Missing files or fields cause an error. Provenance paths name the original derivation locations only and are never runtime fallbacks. Neither Torch nor the original repository is imported.

The entry recomputes joint and individual-device current/temperature/voltage errors, finite-difference thermal and RC defects, observations at the original 197 times with their original weights, reversal events and the frozen peak summaries. It reproduces common-readout rows, native rows (including F), the known-parameter forward reference, and the unchanged 10% plus 10 microampere current improvement and 5% noninferiority decisions. Gate booleans, event identities and integer counts must agree exactly. Small declared FP64 arithmetic allowances apply to metric reproduction only and do not alter a scientific gate.

The capability boundaries are distinct:

- **Saved-array rescoring:** supported from native FP64 endpoint and comparison arrays.
- **Discrete residual recomputation:** supported from saved T/R/v using the original 0.5 ns differences and fixed physical parameters. No saved residual record substitutes for this calculation.
- **Common source RC readout:** the fixed discrete recurrence is recomputed from saved source R and legal initial voltage. Source temperature and hysteresis are not evolved again. Learned candidates use their already-saved common readout.
- **Checkpoint inference, neural AD residuals, gradient evaluation and retraining:** not provided by this subset. Accepted checkpoints remain in the separately delivered run directory recorded in `provenance.json`; they are not redundantly copied here.

The known-parameter source is an information-rich numerical forward reference, not an independent test. Source states and full currents entered endpoint scoring only after the endpoints were locked. This package does not turn development observations into formal OOD evidence, experimental validation or a universal PINN result. Original PCHIP/CS/conditional-temperature auxiliary evidence stays in its existing cited package; it is not recomputed or relabelled by this entry.

The included arrays are project numerical outputs from the pinned author model, not third-party experimental CSVs. Author-model source: Qiu et al. (2024), *Reconfigurable cascaded thermal neuristors for neuromorphic computing*, and [the author repository](https://github.com/yuanhangzhang98/collective_dynamics_neuristor/tree/217d4f0ed6bfc680240021b07142a121cb4963d1). The actual author-code MIT license (Copyright 2024 Yuanhang Zhang) is included as `UPSTREAM_AUTHOR_MODEL_LICENSE.txt`. This does not license publisher figures or experimental data, which are absent. No repository-wide license file for all new project code was found when assembling this subset; this package makes no blanket MIT or public-redistribution grant for those files.

This is a local delivery pending the user's publication decision and the next already-authorized remote synchronization opportunity. No instance is started for this small package. It does not close the older two-dimensional full-field P03 access item. `manifest.json` identifies the actual packaged files; `independent-verification.json` records the completed independent run and the retained proof. Only verified temporary copies are removed after recovery.

Existing auxiliary figure/table sources remain separately identified by `auxiliary-evidence-links.json`; these provenance links are not dependencies of the joint scorer. They retain their historical scores and interpretation boundaries.
