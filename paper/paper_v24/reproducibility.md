# LF11 reproduction and evidence boundaries

The authoritative workspace is E:\Python demo\PINN-PCM-SCI. The inherited scientific source revision is 918985c88f98321c96e6952c9bdd725bd958ed0e, independently rechecked during the sprint. This version supplies the LF11 sources, configuration, manuscript, figures and selected completed-run evidence for repository review.

## Evidence available in a repository checkout

The [evidence directory](evidence/README.md) includes the selected sparse input, common parent, four fixed endpoint checkpoints with Adam states, telemetry, independent audits, calibration, original matched adjudication, full local direction diagnosis, posthoc waveform diagnostic and small readout traces. [The publication manifest](evidence/publication-manifest.json) maps these copies to the unchanged original run.

The original closeout manifest records the local-only status at scientific closure; its historical fields have not been rewritten to imply publication happened earlier. Large full-grid predictions, recovery archives and historical medium/high-fidelity references remain local. A fresh checkout can inspect the published numerical evidence and models. Full independent reference evaluation additionally needs those named archived nominal reference files; the selected package alone is not a complete reference-data release.

## Inputs and exact implementation

- Frozen scientific configuration: configs/phk_v23/lf11_sprint.json.
- Training and observation export: pinn_pcm_sci/phk_v23_lf11.py.
- Reuse of the completed CPU parent and fixed AD audits: pinn_pcm_sci/phk_v23_lf11_campaign.py.
- Independent branch entry: pinn_pcm_sci/phk_v23_lf11_branch.py.
- Common field-based current and power readout: pinn_pcm_sci/phk_v23_lf11_readout.py.
- Local nominal evaluation: pinn_pcm_sci/phk_v23_lf11_evaluation.py.
- Conditional local direction diagnosis: pinn_pcm_sci/phk_v23_lf11_diagnosis.py.
- Posthoc known-waveform baseline: pinn_pcm_sci/phk_v23_lf11_waveform_check.py.
- Rendering saved adjudication: pinn_pcm_sci/phk_v23_lf11_render.py.
- Run root: outputs/runs/20260910-lf11-sparse-metric-sprint.

The run root preserves the coordinate-only observation mask, selected sparse arrays, manifest, pre-update source identity, frozen configuration, shared calibration, common-parent checkpoint, every fixed branch endpoint and optimizer state, telemetry, independent AD audits, public-coordinate prediction carriers, current cloud recovery manifest, and local evaluation. The input archive plus the separately added existing benchmark-test source document the one missing deployment dependency. The first cloud launch stopped during physical-contract loading before any formal optimizer update. The CPU parent was retained.

Four arms run the identical frozen objective implementation. D_B remained in the original process; P_U/P_I/P_M used independent processes on the same GPU. The original coordinator's existing-directory guard subsequently prevented a duplicate P_U launch. The final campaign record is assembled from the actual individual endpoint records, not from that coordinator's exit code. This scheduling change does not add scientific trajectories or updates.

## Minimal fresh reproduction

Start in the authoritative project with its Python 3.11 environment and the LF11 sources supplied with this draft. The following is a recipe for a separate reproduction, not a command to overwrite the existing run.

~~~powershell
.\.venv\Scripts\python.exe -m pinn_pcm_sci.phk_v23_lf11_reproduce --root outputs/reproduction/lf11-new
~~~

This fixes and exports the sparse observations, trains the 1200-update CPU parent, and freezes the common calibration. The package intentionally refuses an existing output directory.

Transfer only the sparse input, parent, calibration, configuration, and required source/known-physics files to an isolated computation directory. The frozen physics loader also requires its existing benchmark-test source for an implementation binding check. It does not require execution of those historical tests or access to their reference data.

~~~text
python -m pinn_pcm_sci.phk_v23_lf11_campaign --root outputs/reproduction/lf11-new --device cuda
~~~

This reuses the CPU parent, performs all four fixed 1200-update branches, records common reference-free audits, and predicts on public evaluator coordinates. Independent branch scheduling may equivalently use the branch entry with separate role names; a role must never be launched twice. No high-fidelity reference is included in the training directory.

The executed parent used Python 3.11, torch 2.5.1+cpu, float64, and two CPU threads. The formal branches used Python 3.11.9, torch 2.5.1+cu118, float64, and two CPU threads on the same V100 environment. The campaign writes the reference-blind P_S gradient calibration before branch training. Reproducing on another backend can introduce numerical differences; the saved endpoint results remain the record of the executed experiment.

Recover and verify the actual outputs, confirm that scientific processes ended, close the actual cloud instance, and record the current closure. Only then run local evaluation:

~~~powershell
.\.venv\Scripts\python.exe -m pinn_pcm_sci.phk_v23_lf11_evaluation --root outputs/runs/20260910-lf11-sparse-metric-sprint --compute-closure outputs/runs/20260910-lf11-sparse-metric-sprint/compute-closure.json
~~~

The named historical dense LF_ONLY carrier contributes only its three fields. Its existing current and power arrays are not consumed. All readouts are recomputed from each method's own fields. The evaluator compares the native carrier's recomputed readout with its saved native traces, making a common-readout inconsistency visible.

If and only if the completed four-arm comparison has no matched increment, the one authorized local diagnostic entry is:

~~~powershell
.\.venv\Scripts\python.exe -m pinn_pcm_sci.phk_v23_lf11_diagnosis --root outputs/runs/20260910-lf11-sparse-metric-sprint
~~~

It reads the saved endpoint moments and local nominal diagnostic targets, regenerates each role's next stochastic batch, and performs no optimizer update. A positive route instead invokes the approved scalar and nearest-method controls within the separate conditional budget. All nominal-feedback follow-ups remain development/attribution.

The actual diagnosis did not trigger the latent alternative. P_S and RAD/PF-GAR were also not run because no matched increment passed. The separately labeled voltage diagnostic is reproduced from the already completed adjudication with:

~~~powershell
.\.venv\Scripts\python.exe -m pinn_pcm_sci.phk_v23_lf11_waveform_check --root outputs/runs/20260910-lf11-sparse-metric-sprint
~~~

Its saved output is local/waveform-diagnostic.json, with local/waveform-traces.npz. It preserves the original results.json, uses no optimizer update, and checks that phase and temperature metrics are identical. It is a posthoc development control.

For figures, install the pinned figure dependency into the project environment if absent, then render the saved adjudication:

~~~powershell
.\.venv\Scripts\python.exe -m pip install -r paper/paper_v24/requirements-figures.txt
.\.venv\Scripts\python.exe -m pinn_pcm_sci.phk_v23_lf11_render --root outputs/runs/20260910-lf11-sparse-metric-sprint
~~~

The completed local environment used NumPy 2.1.1 and Matplotlib 3.11.1. Matplotlib was absent when numerical evaluation completed; installing it locally allowed figures to be rendered from the saved metrics without repeating the formal numerical evaluation. The renderer accesses reference phase only for display snapshots and retains the saved adjudication. Figure copies and tables in this paper folder derive from the run's local outputs.

## Actual evidence locations

Paths below are relative to the original run root. The selected copies retain this layout under paper/paper_v24/evidence; prediction.npz and the large archives are local-only.

| Artifact | Location |
|---|---|
| Coordinate mask and training observations | input/observation_mask.json; input/sparse.npz; input/sparse_manifest.json |
| Frozen scientific design and common constants | formal/frozen_config.json; formal/calibration.json; formal/conditional_calibration.json |
| Formal endpoint accounting | formal/campaign.json |
| Common parent and each D_B/P_U/P_I/P_M endpoint | formal/ROLE/checkpoint.pt; formal/ROLE/result.json; formal/ROLE/telemetry.jsonl |
| Common reference-free audits and field carriers | formal/ROLE/fixed_audit.json; formal/ROLE/prediction.npz |
| Actual recovery and shutdown evidence | compute-closure.json; recovered/recovery-manifest.json |
| Original fixed adjudication and readout traces | local/results.json; local/traces.npz |
| Local Adam diagnosis and final conditional decision | local/equation-head-diagnosis.json; local/conditional-decision.json |
| Posthoc waveform diagnostic | local/waveform-diagnostic.json; local/waveform-traces.npz |

The user-supplied decision report and execution instruction are preserved in docs/notes/2026-09-10-lf11-deep-research-decision-report.md and docs/notes/2026-09-10-lf11-authorized-sprint-instructions.md. They are design/provenance inputs; computed result files supply the scientific evidence. The actual recovered archive was verified before shutdown. A current shutdown command returned successfully and a subsequent connection was refused; compute-closure.json records this evidence before the local nominal evaluation timestamp.

## What can and cannot be reproduced as a claim

The actual training count is 1200 shared-parent updates plus four times 1200 branch updates: 6000 total. Optional development and conditional updates are both zero, below the authorized total ceiling of 10200. CPU checks, residual-gradient calculations, the posthoc interpolation control, rendering and publication use zero optimizer updates. The supplied source and evidence mapping distinguish repository inspection from a future independent numerical reproduction.

The task is a single nominal sparse-reconstruction experiment. It has no entity-level split, independent model-seed replication, unseen protocol, stress read, material calibration, or experimental measurement. A fixed-discretization reference is not continuum truth. A methods gain, strict event/device checks, and a public candidate or publication claim are different evidence levels.
