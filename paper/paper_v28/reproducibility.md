# Reproduction of the completed V28 experiment

Root: `E:\Python demo\PINN-PCM-SCI`. The published input base is `9c70031b6b561f3fd5a9a9684af41a40c0a422da`; it identifies the inherited inputs rather than the new implementation. `evidence/deployed-source-manifest.json` identifies the sources actually deployed. Core training sources and frozen configuration were unchanged during formal updates. Post-training report/diagnostic modules analyze fixed endpoints only. The new sources and selected results accompany the release containing this file, separately authorized after scientific closeout. Unpublished fields in original runtime records remain historical snapshots.

## Read or reproduce the principal artifacts

The compact [evidence package](evidence/README.md) includes actual results, endpoint states, optimizer states, frozen pools, own electrical readouts, plotting arrays and closure receipt. Full own-field arrays stay in `outputs/runs/20260913-lf11-electrical-elimination`, as do the original artifacts; the compact package does not include full reference fields. Manuscript numbers refer to fixed final endpoints, not the best saved Adam node.

The cheapest reproduction regenerates all four PNG/PDF figure pairs and endpoint/cycle/contrast tables from saved evaluation data; it does not train, solve or read full reference fields:

```powershell
.\.venv\Scripts\python.exe -m pinn_pcm_sci.phk_v23_lf11_elimination_report --root paper/paper_v28/evidence
```

The report writes figures and numerical tables, preserving the authored manuscript. `endpoint-comparison-summary.json` contains arithmetic relative changes and the separately evaluated D_E−B_E A/B gates. Underlying values are in `evaluation/results.json` and unchanged V27 evidence. `fixed-endpoint-unlabeled-audit.json` evaluates E0/D_E/P_E on the same frozen independent unlabeled pool and complete seen observations, with zero parameter-gradient evaluations and optimizer updates.

## Actual inputs and execution

Parent: `paper/paper_v27/evidence/D_I/checkpoint.pt`, selected by its control role; sparse labels: `paper/paper_v24/evidence/input/sparse.npz`. Full T/phase and the T adapter are retained. The inactive original V head remains in the checkpoint but is excluded from D_E/P_E optimization. There are 29,827 trainable parameters, 21×11×126 observed coordinates and 231 separately counted analytic initial positions. No new label or complete thermal/phase reference solve enters training. All old observations are seen development data.

CPU checks used Python 3.11.9 / PyTorch 2.5.1+cpu / NumPy 2.1.1 / SciPy 1.14.1. The actual V100 runtime was Python 3.11.9 / PyTorch 2.5.1+cu118 with the same NumPy/SciPy. FP64 neural work ran on GPU; a custom autograd bridge used CPU sparse SuperLU with complete implicit gradients. No framework migration or global dependency installation was required.

Five CPU tests and actual-parent directional checks passed. GPU joint T/phase directional relative errors were 3.64477e-9 / 1.02145e-10. The CPU zero-update power-gap report was corrected to evaluate its waveform in FP64; saved model predictions, finite-difference evidence and scientific trajectories did not change. That reporting correction remains recorded in the CPU JSON.

Preparation fixed `aE=5.937255597408733e-5`, `bE=1.160653895023754`, the 80×40 training grid, physical pools and time-grouping measures. Main arms each used 1500 Adam updates followed by 300 actual full fixed-objective/gradient evaluations. D_E/P_E accepted 147/146 L-BFGS steps. Both stopped at budget; P_E's final trial was rolled back. `checkpoint.pt` contains the complete accepted model and optimizer; `adam-500.pt`, `adam-1000.pt`, `adam-1500.pt` preserve fixed development checkpoints, optimizer and RNG state. They were never selected by reference quality.

| Count | D_E | P_E |
|---|---:|---:|
| Adam objective/gradient evaluations | 1500 | 1500 |
| Complete fixed L-BFGS evaluations, including repeats/trials | 300 | 300 |
| Accepted L-BFGS steps | 147 | 146 |
| Training sparse factorizations / forward solves | 11743 | 19543 |
| Training adjoint solves | 11743 | 19543 |
| Training analytical zero-drive skips | 31991 | 39791 |

Each of E0/B_E/D_E/P_E generated its own 160×80×1001 fields with 278 nonzero electrical solves and 723 zero-drive skips, zero inference adjoints. These 1,112 inference solves are separate from training. Preparation, derivative checks and the three fixed audit evaluations are separately counted in their JSON records. Equal optimizer/evaluation counts do not imply equal computation; no speedup is claimed.

## Lifecycle and reference boundary

`cloud/phk_v23_lf11_elimination/run.sh` performed actual CUDA checks, D_E/P_E training and own-field prediction in an isolated selected-source directory. The package excluded reference fields, dense teachers, stress and unrelated workspace files. `recover_when_finished.py` retrieved the completed job, verified recovery, issued the actual instance's shutdown command and observed subsequent SSH connection refusal. `evidence/compute-closure.json` records this current-instance sequence; `cloud-deployment.json` records the authenticated environment. Shutdown is complete, not inferred from an old receipt or isolated connection loss.

Only then did the local evaluator read the existing nominal reference and compute frozen comparisons. P_E−D_E A/B is false, so P_F was not run. No GPU branch or additional run is pending.

## Execution interfaces for a separately authorized reproduction

These are the actual entry points, **not instructions to rerun the completed campaign**. Use a separate empty run directory and freshly documented compute closure for a new reproduction; never overwrite frozen artifacts or reuse the old closure as evidence for a new job.

```powershell
.\.venv\Scripts\python.exe -m tests.test_lf11_electrical_elimination
.\.venv\Scripts\python.exe -m pinn_pcm_sci.phk_v23_lf11_elimination prepare --root outputs/runs/NEW_AUTHORIZED_RUN --device cpu
.\.venv\Scripts\python.exe -m pinn_pcm_sci.phk_v23_lf11_elimination_predict check --root outputs/runs/NEW_AUTHORIZED_RUN --device cuda:0
.\.venv\Scripts\python.exe -m pinn_pcm_sci.phk_v23_lf11_elimination train --root outputs/runs/NEW_AUTHORIZED_RUN --role D_E --device cuda:0
.\.venv\Scripts\python.exe -m pinn_pcm_sci.phk_v23_lf11_elimination train --root outputs/runs/NEW_AUTHORIZED_RUN --role P_E --device cuda:0
```

Own prediction uses `phk_v23_lf11_elimination_predict predict --root <run> --role <E0|B_E|D_E|P_E> --device <device>`; after recovery and actual shutdown, `phk_v23_lf11_elimination_evaluate --root <run>` reads the retained nominal reference. Prediction/calibration functions refuse accidental overwriting. Linux deployment uses the same module arguments with its validated Python path. This parameterization does not authorize P_F after a false trigger.

The fixed unlabeled diagnostic module is a campaign-specific post-training entry; reuse its saved report for this campaign. Reproducing full reference scores requires the original local high-fidelity reference and own-field arrays, explicitly absent from the compact package. Reproducing figures or reading published-inherited evidence must not be represented as independently rerunning training or all numerical scores.