# Paper package index

This directory is the complete manuscript package for **“When the Reference Solver Fails First: Failure-Preserving Qualification Before PINN Training in an Electrothermal Defect-Transport Case Study.”** The selected package is publicly mirrored in the project repository; no journal submission has been performed.

## Manuscript deliverables

- [Manuscript](manuscript.md) — complete article draft.
- [Chinese manuscript](manuscript_zh.md) — complete Chinese version with the same evidence ceiling.
- [Plain-language Chinese story](plain_language_story_zh.md) — short and extended narratives, reviewer/mentor framing, claim limits, and one-slide story.
- [References](references.bib) — 13 reviewed source carriers in BibTeX form.
- [Main tables](tables.md) — observed run values and bounded diagnostic values only.
- [Supplementary information](supplement.md) — contracts, equations, qualification ladder, accounting, source carriers, diagnostics, and unreached gates.
- [Local reproducibility guide](reproducibility.md) — Windows/Python 3.11 hash, ledger, test, Q0-only reproduction, and separately labeled diagnostic steps.
- [Claim–evidence matrix](claim_evidence_matrix.md) — claim status, direct carrier, prohibited extrapolation, and reviewer-risk self-audit.
- [Package manifest](package-manifest.json) — byte length and SHA256 for every final file below; it explicitly excludes itself to avoid recursive self-reference.

## Final figures

| Figure | PNG | PDF | Evidence role |
|---:|---|---|---|
| 1 | [route gates](figures/figure-01-route-gates.png) | [route gates](figures/figure-01-route-gates.pdf) | Pre-registered route sequence and bounded S1 decisions |
| 2 | [source matrix](figures/figure-02-source-matrix.png) | [source matrix](figures/figure-02-source-matrix.pdf) | Source-contract qualification matrix |
| 3 | [S2 ladder](figures/figure-03-s2-ladder.png) | [S2 ladder](figures/figure-03-s2-ladder.pdf) | Q0 completion, intent-2 stop, intents 3–13 not reached |
| 4 | [Q0 guard](figures/figure-04-q0-guard.png) | [Q0 guard](figures/figure-04-q0-guard.pdf) | Actual zero-drive traces and guard values |
| 5 | [Newton diagnostic](figures/figure-05-newton-diagnostic.png) | [Newton diagnostic](figures/figure-05-newton-diagnostic.pdf) | Explicitly non-scientific reduced-fixture diagnostic |
| 6 | [claim boundary](figures/figure-06-claim-boundary.png) | [claim boundary](figures/figure-06-claim-boundary.pdf) | Evidence ceiling and actual compute accounting |

Figure metadata and reproducibility assets:

- [Captions and evidence boundaries](figures/captions.md)
- [Figure source manifest](figures/source-manifest.json)
- [Figure generator](figures/generate_figures.py)
- Plot-ready source CSVs:
  - [figure-01-route-gates.csv](figures/data/figure-01-route-gates.csv)
  - [figure-02-source-matrix.csv](figures/data/figure-02-source-matrix.csv)
  - [figure-03-s2-ladder.csv](figures/data/figure-03-s2-ladder.csv)
  - [figure-04-q0-circuit.csv](figures/data/figure-04-q0-circuit.csv)
  - [figure-04-q0-field.csv](figures/data/figure-04-q0-field.csv)
  - [figure-04-q0-guard-summary.csv](figures/data/figure-04-q0-guard-summary.csv)
  - [figure-05-newton-summary.csv](figures/data/figure-05-newton-summary.csv)
  - [figure-05-newton-trajectory.csv](figures/data/figure-05-newton-trajectory.csv)
  - [figure-06-claim-boundary.csv](figures/data/figure-06-claim-boundary.csv)
  - [figure-06-compute-accounting.csv](figures/data/figure-06-compute-accounting.csv)

## Core evidence boundary

- Route 1 closed because the required COMSOL research-use PASS was not established for this project route and the source contract remained incomplete. This is not a legal conclusion about the user or other license contexts.
- Route 2 closed because the reviewed PCMO carrier did not supply the required two-dimensional conservative, independently reproducible object.
- Q0 verifies only zero-drive conservation and the artifact chain. It is not an oracle or event PASS.
- The first driven QN intent failed under the frozen inner-Newton limit before case/evaluation/report publication. The bounded terminal disposition is `SYN_EDT_2D_V1_NUMERICAL_CONTRACT_NO_GO`.
- Intents 3–13 were not reached. Figure 5 and its CSVs are `NON_SCIENTIFIC_DIAGNOSTIC`, not production evidence.
- No driven oracle, event, PINN training, neural baseline, GPU development, OOD evaluation, formal comparison, reserve result, experimental validation, or method-performance claim exists in this package.

## Author metadata required before submission

The authors must complete and independently approve the title-page metadata in `manuscript.md`: author names and order, affiliations, corresponding-author details, and ORCID identifiers. Before any submission, also supply the target journal’s required author-contribution statement, funding and grant identifiers, conflict-of-interest declaration, acknowledgments, data/code availability statement, and any journal-specific graphical abstract, highlights, declarations, or cover letter.

Recheck all author approvals, institutional/legal requirements, bibliography style, figure-resolution rules, and repository/package licensing at submission time. Do not include or redistribute the deleted COMSOL vendor `.mph` asset. Submission, external upload, and journal correspondence remain outside this package and require separate human action.
