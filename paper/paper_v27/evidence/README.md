# Selected evidence for paper_v27

- [Campaign and actual counts](campaign.json), [frozen configuration](frozen-config.json), [once-only calibration](calibration.json), and [saved fixed pools](fixed-pools.pt).
- [Common parent](parent.pt), [complete visible audit](parent-visible.json), [independent physics audit](parent-physics-audit.json), [input identity](input-identity.json), and [pre-training source identity](training-source.json).
- D_I, D_B, and P_U directories contain results, telemetry, and final accepted model/optimizer states. P_U additionally contains the three actual Adam states used for diagnosis. The other arms' intermediate states remain in the original run.
- [Evaluation](evaluation.json), [device/event traces](evaluation-traces.npz), [display field snapshots](field-snapshots.npz), [three-node direction diagnosis](equation-head-diagnosis.json), and [conditional decision](conditional-decision.json).
- The electric_audit directory preserves own-model boundary traces, AD, signed FV current/power components and summaries. Parent arrays are exact copies of the previously saved v26 post audit, not a rerun.
- [Actual compute closure](compute-closure.json) records process termination before nominal reference evaluation. No cloud instance or stress data are involved.
- [Conditional evidence](conditional/README.md) supplies actual R/G/N endpoints, loss/gradient calibration, separate A/B decisions and its own process closure. D_N was not triggered. Main plus conditional execution totals 6500 new Adam updates and 1500 complete fixed evaluations; R's reused prefix is not double-counted.
- [Combined terminal summary](terminal-summary.json) and [finalized experiment manifest](terminal-manifest.json) record the actual full-campaign disposition, accounting and artifact routes.

This selected package is included in the user-authorized paper_v27 release. The sparse bundle remains at paper_v24/evidence/input/sparse.npz; the inherited final parent is also released in paper_v26. Full new own-field predictions and the full fixed nominal reference remain local to the original run/reference paths. Two reference peak snapshots are supplied for display only, not as a training carrier. Runtime publication fields remain historical snapshots; the containing Git commit identifies the later release.

Figures and tables can be rebuilt directly from this selected pack without a reference read, training, or an old run tree:

```powershell
.\.venv\Scripts\python.exe -m pinn_pcm_sci.phk_v23_lf11_joint_report --root paper/paper_v27/evidence --paper outputs/reproduction/lf11-joint-figures
```

The containing source files plus their saved runtime identity define the implementation. Numerical validity, matched effect, strict device capability and independent confirmation remain separate claims; consult the manuscript and claim matrix.
