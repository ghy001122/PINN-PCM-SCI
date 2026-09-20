# Data availability and reproduction

This is a submission candidate, not a submitted article. The 2026-09-20 curated repository publication on `codex/paper-revision-results` includes this revision, numeric evidence, two clean D_E endpoints and their matched parents/calibration/pools, and the scientific/scoring source. The preceding curated release is `17ad7c9ccaf3f0ae0c4eea986005a772dd7a2184`. The complete fixed arrays and the full execution-runtime archive remain local; the commands below that require that package cannot be completed from the curated Git checkout alone. No persistent public dataset identifier or completed third-party retraining is claimed.

The PDFs, closeout and `delivery-status.json` retain their scientific-closeout dates and availability statements as of that date. The [publication note](../../docs/notes/2026-09-20-readout-clean-pde-results-release.md) records the later, separately authorized repository release. The public scoring source is under `portable/`; it is the same code used by the local array package, without bundling that package's large inputs.

## 1. Manuscript and figure reconstruction

The editable manuscripts are `source/manuscript.md` and `source/supplement.md`. Tables and finished figure assets are in `tables/` and `figures/`; `references.md` contains the bibliography. With the recorded Python environment, run `prepare_document.py` followed by `build_pdf.py` from this directory. These commands read only the included manuscript assets, render equations and typeset the PDFs. They do not read a private scientific run directory, load a model or solve a PDE. The numeric CSV tables retain more digits than the typeset display tables.

The saved-array analysis also includes figure-generation code. Regenerating the new scientific figures, rather than simply rebuilding the manuscript, requires the array-analysis results described below.

From the extracted array-package root, `python manuscript/report_results.py --archive-root . --score-dir isolated-rescore` regenerates the new tables and scientific figures from completed scores. It does not run a model or reference solver. The final production environment uses NumPy 2.1.1 and Matplotlib 3.11.1 for analysis/plots, ReportLab 4.4.9 for typesetting and pdfplumber 0.11.9 with Poppler for PDF review. GPU training environment metadata are recorded separately.

## 2. Fixed-array scoring

The workspace package is `outputs/submission-archive-20260918`. After the independent ZIP parts are extracted into one new directory, run:

```text
python -I portable/readout_rescore.py --root . --out my-rescore
```

Python 3.11 and NumPy are sufficient for this entry. Use an output directory that does not already contain completed scores. The entry imports no neural training library; it loads no checkpoint, performs no model inference and solves no electrical system. It recomputes finite-volume port traces algebraically from saved fields and evaluates the frozen metrics and complete decisions.

The package contains two protocols and three reference conditions: original, time-refined and space-refined. Eight historical learned states, two deterministic interpolants, six negative continuation states and two clean D_E states give eighteen scientific objects. Twelve objects have both 160×80 and 240×120 readers; the six continuation states keep their historical reader. There are thirty object/reader combinations and ninety object/reader/reference score records. Those records are not independent experimental replications.

T/phase and event comparisons use the original 160×80 measure. Fine potential is mapped with nonnegative exact-volume overlap weights for the original voltage guard; native fine current and power are retained. Fine local Joule density against the native spatial reference is separately named. The threshold is applied after reference-field restriction in the primary event score; a historical indicator-mapping diagnostic is kept separate. Each reference supplies its own normalization, with fixed-old-denominator diagnostics retained.

The historical sixteen-object evaluator is retained as `portable/rescore.py` and explicitly reads `historical-manifest.json`. It does not silently acquire the new objects. New full results are under `primary-rescore` and `isolated-rescore`. The latter is produced in a separate directory containing only packaged inputs; large immutable inputs may be hardlinked locally without altering their content. Agreement is checked at `rtol=2e-10, atol=2e-12`; Boolean decisions must match exactly. This is same-code arithmetic reproduction, not an independent implementation or a third-party scientific replication.

## 3. Training reproduction

Frozen inputs, matched parents, sparse observations, numerical coefficients, output transforms, calibration, sampling pools, actual source and environment records are separate from the array-only scorer. The new execution runtime is `training/new-execution-runtime.tar.gz`. It contains no reference fields. An opt-in helper stages it into a new empty workspace:

```text
python portable/reproduce_new_experiment.py --archive . --workspace NEW_WORKSPACE --action prepare
```

`--action execute` additionally runs the bounded GPU experiment and requires an appropriate environment and explicit compute authorization. It is not invoked by scoring or document building. Training consists of two clean D_E branches with 1500 Adam updates and at most 300 complete L-BFGS evaluations each, plus the declared fixed-weight readers. All line-search trials count, and the endpoint is the last accepted state. Public access to all files and training instructions is distinct from an external group actually reproducing the optimization.

## Provenance and licensing

All new reference and prediction arrays are generated by this project's synthetic numerical model. No human-subject, private experimental or named-material validation data are included. The code/configuration lineage and upstream conceptual sources are identified in the manuscript, frozen runtime and existing source/license records. The project uses established solver, differentiation and optimization tools without claiming their invention. NumPy, SciPy, PyTorch, Matplotlib and ReportLab retain their respective upstream licenses; no license for third-party source or literature is regranted by this archive.

The complete arrays are local and have not been publicly uploaded in this execution. Dataset release, a durable identifier and repository/data licensing appropriate for redistribution must be completed before the manuscript claims that all data are publicly available. Keep the published curated-evidence statement distinct from that future full release.

## Author and journal completion

The final journal, names, affiliations, correspondence, contributions, funding, conflicts and author approval must be supplied truthfully by the authors. The AI-use statement describes internal assistance and must be checked against the chosen journal's current official policy. The supplied cover letter is a draft and does not assert exclusive submission, approval of all authors or journal acceptance. No manuscript or data have been submitted by this revision.
