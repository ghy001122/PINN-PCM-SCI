# LF11 evidence supplied with paper_v24

This directory contains selected completed-run artifacts for cloud review. Scientific numbers are copied from the original run; publication adds no training, reference evaluation, or method claim.

## Read first

- [Original four-arm adjudication](local/results.json): all method metrics, cycle details, validity and matched comparisons.
- [Conditional direction decision](local/conditional-decision.json) and [complete equation-by-head calculations](local/equation-head-diagnosis.json).
- [Posthoc waveform control](local/waveform-diagnostic.json): separate from the frozen adjudication.
- [Original formal accounting](formal/campaign.json), [frozen configuration](formal/frozen_config.json), [common calibration](formal/calibration.json), and [reference-blind gradient calibration](formal/conditional_calibration.json).
- [Observation mask](input/observation_mask.json), [sparse manifest](input/sparse_manifest.json), and [sparse observations](input/sparse.npz).
- [Source identity](source_identity.json), [actual compute closure](compute-closure.json), and [recovery manifest](recovered/recovery-manifest.json).

The formal/warm_start, formal/D_B, formal/P_U, formal/P_I and formal/P_M directories each contain the fixed endpoint checkpoint, including optimizer state, and its result, telemetry and common independent AD audit. They permit inspection of the actual executed models. The original checkpoint and manifest paths refer to the run layout below.

## Original layout and reproduction boundary

Files retain their paths relative to the local run root:

outputs/runs/20260910-lf11-sparse-metric-sprint

[publication-manifest.json](publication-manifest.json) maps every supplied file to that original location and records its publication copy identity. These are selected copies; the full run, recovery archive, intermediate checkpoints and full-grid prediction carriers remain local. The historical medium and high-fidelity references and sealed stress fields are not included.

The sparse observations are sufficient for the recorded sparse training input. A fresh cloud checkout can review all published metrics and diagnostics and inspect endpoint weights; reproducing the full fine-grid adjudication still requires the named archived nominal references. Reading saved metrics is not an independent rerun. See the [reproduction guide](../reproducibility.md) for execution entries and prerequisites.

The original closeout manifest predates publication. Its historical local-only flag and original paths remain unchanged; this publication directory supplies the subsequent cloud access mapping.
