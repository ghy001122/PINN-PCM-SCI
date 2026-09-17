# Curated revision evidence

Prepared 18 September 2026 for the user-authorized repository publication. This directory packages existing results; it performs no scientific computation. The latest manuscript remains the reviewed 17 September snapshot. The current publication status is supplied by [the release note](../../../docs/notes/2026-09-18-revision-results-release.md); older manuscript statements that results were local describe the pre-publication state.

## Contents and scope

- `phase-adapter/`: six final accepted model/optimizer checkpoints; original terminal evidence, shared pools, calibration, interface checks, execution summary and frozen configuration.
- `phase-runtime-source/`: the scientific source/configuration snapshot retained by the local array archive. It records the code used, not new permission to execute it.
- `temporal-reference/`: complete saved scalar scoring results for the original/time-refined comparisons, reference terminals and selected signed readout traces.
- `spatial-reference/`: complete saved scalar scoring results, native reference terminals, mapping/intent records and signed readout traces.
- `spatial-runtime-source/`: the source/configuration snapshot for the completed spatial experiment.
- `local-verification/`: saved reports of the already completed isolated array rescore and preparation-only training entry check.
- `local-array-manifest.json`: inventory of the local array archive, not a claim that every file it lists is in this repository.
- `publication-manifest.json`: original workspace-relative source for each copied asset and any treatment. Duration-only elapsed/wall fields are omitted from derived public JSON; scientific values and solve/update counts are retained. No checkpoint was deserialized during publication.

The public terminals and tables allow review of recorded outcomes, identities and calculation budgets. Final checkpoints enable subsequent authorized model inspection when their dependencies are supplied. Neither is a new independent rerun.

## What is not in this Git package

The complete approximately 4.96 GB temporal array ZIP, full space-time predictions, and the spatial native/mapped fields remain local. The 16-object independent NumPy rescore has been executed locally, but a new clone does not contain all its array inputs. No false public archive link or DOI is supplied. Cloud credentials, connection records, private shutdown proofs, and trial checkpoints are omitted.

## Rebuild the reviewed documents without scientific execution

The current `source/`, `tables/`, `figures/`, `references.md`, `prepare_document.py` and `build_pdf.py` in the parent directory are sufficient to typeset the supplied reviewed text. From the repository root, in a Python environment with the documented Matplotlib/ReportLab dependencies:

```text
python paper/paper_revision_20260917/prepare_document.py
python paper/paper_revision_20260917/build_pdf.py
```

These two steps expand saved tables and render the existing text. They do not call a scientific model or solver. Do not start by rerunning `spatial_report.py`, `reference_certificates.py` or source-assembly scripts unless their separately documented local inputs are present: those reproduce upstream analyses, a different layer of reproducibility.

Arrays-to-scores and from-parent training remain separate workflows. Frozen snapshots containing the historical execution flag do not override the repository's currently closed scientific phase or authorize additional compute.
