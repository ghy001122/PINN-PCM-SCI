# PHK-V2.1 paper and reproducibility package

## Outcome first

PHK-V2.1 completed its independent engineering stage and all 14 frozen oracle-qualification intents, then stopped before any PINN work:

~~~text
PHK_V21_ORACLE_NO_GO_STOP_BEFORE_PINN
PHK_V21_ORACLE_NO_GO_NO_PINN_OR_METHOD_EVIDENCE
~~~

Nominal coarse, medium, fine, and extra-fine solutions all produced two localized events with complete recovery. Zero-drive and Joule-off correctly produced no event, exact replay had zero saved-array difference, and the independent pseudo-transient solver cross-check produced two events. However, the event-time component increased from 0.0012067679515502204 at medium→fine to 0.0016486829760616161 at fine→extra-fine. The frozen component-wise convergence gate therefore failed.

The candidate floor carrier is retained but is not an admissible neural floor. Sharp/PF author-metric replication, strong raw PINN, PHA-MF, field-selective KC, their 2x2 attribution, GPU development, and formal OOD were NOT_REACHED.

## Main deliverables

| Deliverable | File |
| --- | --- |
| English manuscript | [manuscript.md](manuscript.md) |
| Complete Chinese manuscript | [manuscript_zh.md](manuscript_zh.md) |
| Plain-language Chinese story | [plain_language_story_zh.md](plain_language_story_zh.md) |
| Supplementary information | [supplement.md](supplement.md) |
| Reproducibility guide | [reproducibility.md](reproducibility.md) |
| Final tables | [tables.md](tables.md) |
| References | [references.bib](references.bib) |
| Baseline anatomy cards | [baseline_anatomy_cards.md](baseline_anatomy_cards.md) |
| Claim–evidence matrix | [claim_evidence_matrix.md](claim_evidence_matrix.md) |
| Reviewer-risk self-check | [reviewer_risk_self_check.md](reviewer_risk_self_check.md) |
| Figure captions and reproduction | [figures/captions.md](figures/captions.md) |
| Figure source manifest | [figures/source-manifest.json](figures/source-manifest.json) |
| Package manifest | [package-manifest.json](package-manifest.json) |

## Figures

Six final figures are supplied as high-resolution PNG and vector PDF:

1. route outcome;
2. 14-intent qualification ladder;
3. nominal event times and peaks;
4. mechanistic and geometry controls;
5. decisive six-component convergence gate;
6. claim boundary and compute accounting.

The generator verifies the immutable terminal-summary SHA256, reads only existing evidence, performs no solver/training work, and writes six derived CSV tables plus the figure source manifest.

## Authoritative evidence outside this folder

- [S0 scientific freeze](../docs/governance/2026-08-28-phk-v21-s0-scientific-contract-freeze.md)
- [S1 terminal closeout](../docs/experiment/2026-08-28-phk-v21-s1-terminal-closeout.md)
- [terminal summary](../outputs/runs/20260828T-phk-v21-s1-q-terminal-summary-001/summary.json)
- [object/numerical contract](../configs/phk_v21/object_numerical_contract.json)
- [complete-case split](../configs/phk_v21/case_split_manifest.json)
- [oracle/floor contract](../configs/phk_v21/oracle_and_floor_contract.json)
- [baseline replication contract](../configs/phk_v21/baseline_replication_contract.json)
- [method contract](../configs/phk_v21/method_contract.json)
- [intent 2 carrier reconciliation](../docs/experiment/2026-08-28-phk-v21-s1-intent-02-carrier-reconciliation.md)
- [terminal label reconciliation](../docs/experiment/2026-08-28-phk-v21-s1-adjudication-label-reconciliation.md)

## Rebuild and validate

From the repository root:

~~~powershell
D:\anaconda\python.exe paper_v21\figures\generate_figures.py
.\.venv\Scripts\python.exe paper_v21\build_package_manifest.py
.\.venv\Scripts\python.exe paper_v21\validate_package.py
~~~

The expected package verdict is PHK_V21_PACKAGE_VALID.

## Use boundary

This is a complete local bounded negative benchmark-qualification package. It is not the originally desired positive PINN-method V2, does not reproduce or beat Sharp/PF, and does not claim real-material calibration, experimental validation, formal OOD, Q2 placement, or journal acceptance.

The package contains no external GPL source tree, credential, commercial model asset, or experimental data. It does not authorize a production rerun, submission, external upload, release, or Git remote operation.
