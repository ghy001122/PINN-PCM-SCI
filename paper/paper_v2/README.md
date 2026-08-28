# PHK-V2 paper and reproducibility package

## Outcome first

PHK-V2 did **not** reach a PINN method comparison. Its preregistered Oracle Gate returned:

~~~text
PHK_V2_ORACLE_NO_GO_EVENT_CONTRACT_AND_CONTROL_EXECUTION_FAILURE
PHK_V2_ORACLE_NO_GO_NO_PINN_OR_PHA_OR_KC_OR_FORMAL_EVIDENCE
~~~

Manufactured and zero-drive guards passed. Nominal coarse/medium/fine/half-time-step/replay runs passed numerical hard guards and exact replay was zero across all six components, but the two-cycle recovery/event contract failed. Intent 9 then failed at the frozen phase-Newton minimum line-search step. No neural floor was sealed; strong raw, PHA-MF, KC, their 2×2 combination, GPU, formal, and OOD were not reached.

This package is a complete local benchmark/numerical-limits V2 draft. It does not satisfy the originally desired positive PINN-method evidence and does not promise a Q2 journal outcome or acceptance.

## Main deliverables

| Deliverable | File |
|---|---|
| English V2 manuscript | [`manuscript.md`](manuscript.md) |
| Chinese V2 manuscript | [`manuscript_zh.md`](manuscript_zh.md) |
| Plain-language Chinese story | [`plain_language_story_zh.md`](plain_language_story_zh.md) |
| Supplement | [`supplement.md`](supplement.md) |
| Reproducibility guide | [`reproducibility.md`](reproducibility.md) |
| Final tables | [`tables.md`](tables.md) |
| References | [`references.bib`](references.bib) |
| Baseline anatomy cards | [`baseline_anatomy_cards.md`](baseline_anatomy_cards.md) |
| Claim–evidence matrix | [`claim_evidence_matrix.md`](claim_evidence_matrix.md) |
| Reviewer-risk self-check | [`reviewer_risk_self_check.md`](reviewer_risk_self_check.md) |
| Figure captions and reproduction | [`figures/captions.md`](figures/captions.md) |
| Figure source manifest | [`figures/source-manifest.json`](figures/source-manifest.json) |
| Package manifest | [`package-manifest.json`](package-manifest.json) |

## Figures

Six final figures are supplied in PNG and vector PDF form:

1. `figure-01-workflow`
2. `figure-02-source-anatomy`
3. `figure-03-qualification-ladder`
4. `figure-04-event-trajectories`
5. `figure-05-convergence-controls`
6. `figure-06-causal-and-claim-boundary`

The generator reads only existing evidence and writes six derived CSV files. It verifies the terminal summary hash and performs no solver or training work.

## Authoritative evidence outside this folder

- [`../../docs/experiment/2026-08-27-phk-v2-s2-terminal-closeout.md`](../../docs/experiment/2026-08-27-phk-v2-s2-terminal-closeout.md)
- [`../../outputs/runs/20260827T-phk-v2-s2-q-terminal-summary/summary.json`](../../outputs/runs/20260827T-phk-v2-s2-q-terminal-summary/summary.json)
- [`../../configs/phk_v2/program_contract.json`](../../configs/phk_v2/program_contract.json)
- [`../../configs/phk_v2/object_numerical_contract.json`](../../configs/phk_v2/object_numerical_contract.json)
- [`../../configs/phk_v2/case_split_manifest.json`](../../configs/phk_v2/case_split_manifest.json)
- [`../../docs/references/2026-08-27-phk-pinn-primary-source-baseline-audit.md`](../../docs/references/2026-08-27-phk-pinn-primary-source-baseline-audit.md)

## Use boundary

This package does not redistribute fixed external Sharp/PF/jaxpi/jaxpi2 source trees. It records their identities, licenses, and bounded smoke results. The package itself does not authorize submission, external upload, release, or new Git remote operations. Traceability and publication are separate from scientific validity.
