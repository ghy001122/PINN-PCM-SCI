# Fixed-array reproduction and completed B1 delivery

## Publication addendum, 22 September 2026

The user separately authorized a curated repository publication on `codex/paper-revision-results`; its verified remote state is recorded in the [publication record](../../docs/notes/2026-09-22-b1-sprint-results-release.md). This adds the completed manuscript, compact results, source, two parents, six accepted endpoints, visible training input and fixed pools. See [the run excerpt](evidence/b1/README.md) for source-to-publication paths. Saved port/error traces are under `evidence/b1-port-traces/`; the `first-score/traces/` prefix in `tables/b1-port-trace-index.csv` maps to that directory. No scientific values or checkpoints were recomputed for publication.

The complete prediction/reference field arrays remain local. Public checkpoints, selected figure arrays and port traces do not make the full array-rescoring package externally available. The original local-delivery status below, the preparation snapshots and `published=false` in the execution manifest retain their historical timestamp; this addendum records the later publication separately.

## Scientific closeout snapshot

Status: local delivery, not a public data release. These paths are actual workspace paths. No license permission, controlled-reviewer access URL or DOI has been approved in this task.

## Existing science: portable saved-array package

The source archive remains `outputs/submission-archive-20260918`. The new portable distribution is `outputs/submission-rescore-20260921`. It uses relative paths, normal files (large arrays are local hard links, not symlinks), frozen NumPy scoring kernels and the actual original result records. It does not import Torch, load learned states, query neural networks or solve an electrical system. A copied directory remains portable; copying the underlying files does not require the original run directories.

Core scope is twelve objects: eight E/F endpoints, one B_E for each protocol and two clean shorter-protocol D_E endpoints. Each has three references and two readers: 72 records, not 72 independent repeats. The native 240×120 states/ports and q are retained; only V used by the original guard is volume-restricted, while T/φ/events retain the 160×80 measure. ROI, thresholds, time/volume coordinates, mappings, normalization denominators, advantage/noninferiority subpredicates, cycles and original scores are included.

The separately portable `extension/` subpackage preserves six E_C/E_R/E_I continuations and their 18 historical scores. No extension outcome is upgraded or discarded. Its expected records live in the same versioned original result structure. This task re-executes the requested core scope; the extension's historical scores are preserved and its input/entry validation is separate from a claim of newly rerunning all 18 scores.

From the repository root, the following commands were actually run successfully:

```powershell
.\.venv\Scripts\python.exe -I outputs/submission-rescore-20260921/portable/scope_rescore.py --root outputs/submission-rescore-20260921 --scope original43 --out check-original43
.\.venv\Scripts\python.exe -I outputs/submission-rescore-20260921/portable/scope_rescore.py --root outputs/submission-rescore-20260921 --scope core --out core-rescore
```

The first clean run covers E/F/B_E for original/43: 18 records and 1,893 compared scalar/identity/Boolean entries. The full core run covers 72 records and 8,868 entries. Both passed rtol=2e−10, atol=2e−12 and exact Boolean equality. Complete existing output directories cannot be overwritten by these commands; a genuinely needed recheck must name a new directory.

For a transferred package, use Python 3.11 with NumPy and run inside its root:

```text
python -I portable/scope_rescore.py --root . --scope core --out new-core-check
```

For the separately transferred extension, use `--scope extension`. Its files resolve within that extension root. The source-scoring implementation is reused, with only scope orchestration added; this is same-code arithmetic reproduction, not an independent implementation or from-zero training. The package records the actual NumPy/Python versions in its results. If the installed NumPy does not provide `numpy.trapezoid`, use the recorded compatible environment rather than silently changing the metric implementation.

Missing-file behavior was tested against a manifest in a clean directory without its arrays: it exits with code 2, reports `Missing saved input(s); no automatic regeneration`, and performs no regeneration. The required fixed input content was hashed once into `integrity.json`; the extension reuses the same hashes. No full-repository hashing was performed.

## Completed B1: training, readout and first array score

The actual fixed run is `outputs/runs/20260921-b1-second-cycle-phase-gap`. It contains both `seed-29/parent.pt` and `seed-43/parent.pt`, all six `E`, `D_E`, `F_raw` checkpoint/terminal pairs, their optimizer and work records, the visible training data, frozen configuration, calibration and pools. `all-endpoints-locked.json` and `readout-manifest.json` bind all accepted endpoints and fourteen readers. The runtime source bundle is `outputs/b1-runtime-20260921.tar.gz`; `deployment.json` records its already verified transfer identity. No old trained state or reference array was uploaded. The detached launch survived an SSH-client timeout; it was verified in progress and never relaunched. After successful scientific completion, the local recovery monitor required a parser correction for an exit-code file without a trailing newline. Four isolated format checks passed, and only packaging, transfer and shutdown resumed; no scientific computation was repeated.

Actual GPU commands used Python `/root/autodl-tmp/envs/pinn-pcm-sci-py311/bin/python` from `/tmp/pinn-b1-20260921`:

```text
python -u -m pinn_pcm_sci.phk_v23_b1 train --device cuda:0 --approval outputs/runs/20260921-b1-second-cycle-phase-gap/resource-approval.json
python -u -m pinn_pcm_sci.phk_v23_b1 readout --device cuda:0 --approval outputs/runs/20260921-b1-second-cycle-phase-gap/resource-approval.json
```

These commands describe completed execution, not authorization to rerun. The runner refuses an existing scientific trajectory. Exact versions are Python 3.11.9, Torch 2.5.1+cu118, NumPy 2.1.1 and SciPy 1.14.1; FP64 and the frozen finite optimizer/solve caps were retained. The user explicitly removed monetary limits for this fixed work. No monetary charge is inferred. Recovered outputs were transfer-verified once, the actual GPU instance was shut down and extraction completed before local reference scoring.

The separately portable NumPy-only package is `outputs/submission-rescore-20260921/b1`. Its 28 prediction/port files use ordinary hard links locally; transferred copies materialize normal files. References, weights, ROI, mappings, normalizers, old full-history kernels and B1 interval kernels are inside that package. Its actual first scoring command from the repository root was:

```powershell
.\.venv\Scripts\python.exe -I outputs/submission-rescore-20260921/b1/portable/score_b1.py --out outputs/submission-rescore-20260921/b1/first-score
```

For a transferred package, run `python -I portable/score_b1.py --out a-new-score-directory` inside its root. Existing outputs cannot be overwritten; missing inputs fail without regeneration. `first-score/results.json` and `expected-results.json` preserve the actual first 42-record result. This first B1 score is not presented as a second independent replication. Training-output `scoring/results.json` is an explicitly recorded copy of that same result, not another execution.

The full B1 record contains seven objects × three references × two readers, with 84 cycle rows, 126 interval records and 36 E/D_E, E/F, E/B_E comparisons. Native ports remain native; only fine V for the original guard is restricted. W, its two disjoint complementary segments and the full history each retain their own normalizers. Window-plus-outside unnormalized integrals reconstruct the full history. Complete full metrics agree with the inherited scorer at rtol=2e-10 and atol=2e-12 during the same score. No neural forward, electrical solve or reference generation occurs in array scoring.

The first score also saved all 42 complete port/error traces under `first-score/traces/`. `tables/b1-port-trace-index.csv` gives package-relative paths and fields. A final report-only export integrates those saved traces over the unchanged powered intervals [0,0.35] and [1.01,1.36], producing `b1-signed-pulse-energy.csv` (84 rows) and `b1-energy-summary.csv` (42 rows). Signed pulse sums agree with saved cumulative full-history errors, and their absolute normalized totals agree with the original energy scores at the inherited tolerances. No frozen score or decision is rewritten. Supplement Table S35 displays all seven spatial-reference/fine-reader objects, including cancellation.

## Rebuild the delivered figures and PDFs

Use the project Python with NumPy, Matplotlib and ReportLab 4.4.9. The following local commands were actually executed after completed scoring:

```powershell
.\.venv\Scripts\python.exe paper/paper_revision_20260921/report_b1.py
.\.venv\Scripts\python.exe paper/paper_revision_20260921/plot_physics.py
.\.venv\Scripts\python.exe paper/paper_revision_20260921/assemble_manuscript.py
.\.venv\Scripts\python.exe paper/paper_revision_20260921/prepare_document.py
.\.venv\Scripts\python.exe paper/paper_revision_20260921/build_pdf.py
```

For typesetting the delivered editable sources without replacing editorial changes, run only the last two commands. Assembly recreates the initial complete source from the completed score and historical text; it is not necessary for normal source editing. Physical plotting reads saved native arrays at fixed times 0.27/1.28, evaluates only algebraic deposition when q is absent, and adds no model inference or linear solve. All final pages were rendered with Poppler and visually checked; see `evidence/visual-qa.json` for actual counts and corrections. Historical assets copied from the 18 September snapshot retain their source identity.

## Access and licensing boundary

The curated Git release at 218bb66069da52b2ccfe9dd68ac519edbe4584d0 is still distinct from these local full-array and staging packages. Full public or controlled reviewer access needs an actual approved location, permissions and applicable license. Third-party software/literature licenses remain with their owners; this delivery does not regrant them. Local package success partly addresses P03 and does not close external accessibility.
