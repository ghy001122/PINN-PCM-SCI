# Data access and reproduction boundary

This module records task PCM-20260924-OBSERVATION-PRESERVING-PHASE-01. On 2026-09-25 the user separately authorized publication of the curated source, manuscript modules and condensed evidence on `codex/paper-revision-results`. See the [publication record](../../docs/notes/2026-09-25-observation-preserving-phase-results-release.md). Complete field arrays, checkpoints and reference inputs remain local; the condensed Git publication does not close P03. No DOI or submission is claimed.

| Material | Actual access status | Role |
|---|---|---|
| Old B1 E/29 and D_E29 checkpoint/field/port arrays | Complete local files under `outputs/runs/20260921-b1-second-cycle-phase-gap/`; old readout manifest locates the arrays. | Frozen base and historical comparator; neither is a newly trained cost-matched branch. |
| Original reference and portable metric implementation | Local fixed-array package under `outputs/submission-rescore-20260921/`. | Necessary pre-training support bound, then reference scoring after endpoint lock. It is absent from the remote training archive. |
| New G/N/S corrections and native arrays | Local run root `outputs/runs/20260924-observation-preserving-phase/` after verified recovery and composition; exact objects in `readout-manifest.json`. | Full learned fields, ports, raw audits, optimizer endpoints and actual costs. No new reference solution is generated. |
| Earlier public source and condensed evidence | [Existing repository scientific baseline](https://github.com/ghy001122/PINN-PCM-SCI/tree/ac8c63686398399e0190ede5b78de5a1054be337). | Public source/condensed evidence; not complete arrays and not the new module's external publication. |

The new base arrays are never substituted for G. G evaluates its own composite fields at all 1001 times and performs 278 powered native electrical solves on the 160×80 grid. N and S evaluate their actual corrected dark-interval phase. Their complete composite arrays reuse the matching E/29 temperature, voltage, Joule density and port arrays only after four own-field time checks per arm (.27, 1.28, 1.55, 1.8) pass. Two powered checks per arm account for four further electrical solves. Each reused object has a composition-provenance record. These identical electrical arrays are a construction property, not independent evidence of improved electrical accuracy. Native readout totals 282 forward solves; independent raw audits are accounted separately.

## Executed source and runtime deviation

The actual training source is retained in `outputs/staging-observation-preserving-phase-20260924.tar.gz` (SHA256 `e0768c8e9802ce2810b45e0bfc1f30f48c555f450c09e4ed17bef12bc3a5e4f0`). It contains the imported project source closure and visible inputs, not full references. The executed runner is additionally preserved under the run's `executed-source/` directory and copied unchanged into [the published executed-source snapshot](evidence/executed-source/phk_v23_observation_preserving_phase_run.py). See [evidence roles](evidence/README.md). All three corrections trained on CPU because the original entrypoint omitted the device argument. That fact remains part of this run identity. The current local runner forwards the device correctly and is not retroactively identified as the executed version. The audit/native readout use the separate CUDA-capable entrypoint. No trajectories were repeated after detecting this engineering deviation.

Local G profiling first failed in Windows memory metadata after completing the objective/gradient, then suffered a partial RAM allocation failure. Those attempts had zero optimizer updates and are not hidden from preparation costs. Complete profiles on the existing cloud CPU passed. The partial attempt's full coordinate/electrical work is unknown; it is not silently assigned a zero cost. Recorded training and inference wall times are not a cloud billing estimate.

## Reusing the finished results

Existing JSON/CSV/NPZ results can be read without starting any training. The paper figures can be rebuilt from saved numerical arrays:

```powershell
.\.venv\Scripts\python.exe paper/observation_preserving_phase_20260924/build_report.py theory
.\.venv\Scripts\python.exe paper/observation_preserving_phase_20260924/build_report.py results
```

The `compose` and `score` entrypoints in `pinn_pcm_sci.phk_v23_observation_preserving_phase_evaluate` are one-time completion steps; they refuse to overwrite completed outputs. The native scorer reuses the frozen original thresholds, ROI, integration weights, event definitions and old normalizers. It checks the heating-window invariants separately from numerical improvement. Exact trajectory reproduction requires the archived source: its historical launch requested cuda:0 and passed the enabled-GPU resource gate, but the recorded entrypoint omission constructed CPU models. The repaired runner would actually use CUDA and therefore is not an exact replay of this CPU trajectory. Its existing resource gate rejects a CPU command; any future deliberate CPU replay needs an explicit new execution contract, not a bypass of that gate. Reproduction training is not authorized by this document.

The first local scoring process completed B0 and then ran out of memory while scoring D_E. The resumed process reuses those completed B0 scores and streams the original NPY members into read-only task-local memory maps. This storage adapter is bound only inside the isolated imported reader; the archived scoring functions and field values are unchanged. No GPU restart, model inference, training, electrical solve or reference solve is involved. The recovery record is `scoring-memory-recovery.json` in the local run.

The package is not a standalone public replication dataset: it depends on the explicitly identified local base/reference arrays. The user has not authorized publishing these complete arrays in this task. P03 remains open until the intended external reader can actually obtain the necessary material.
