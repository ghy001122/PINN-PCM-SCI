# PHK-V2.3 event-competence recovery advisor draft

Status: `ADVISOR_DRAFT_COMPLETE_LF3_CARRIER_NOT_ESTABLISHED`

This package is the first manuscript draft that integrates the bounded
PHK-V2.2R→LF3 solver-recovery sequence. It is deliberately written as a
failure-analysis and competence-gated recovery study. LF3-T0 recovered valid,
well-timed, localized two-cycle events, but failed the preregistered full-medium
recall gate (`0.805842/0.768603 < 0.90`). Conditional P0 therefore ran zero
updates. No PINN-specific gain or candidate was established.

## Package contents

- `manuscript.md`: English advisor-reviewable draft;
- `tables.md`: manuscript-ready evidence, metric, and decision tables;
- `claim_evidence_matrix.md`: explicit claim audit;
- `reproducibility.md`: exact code, input, run, and evaluation identities;
- `reviewer_risk_self_check.md`: adversarial assessment of publishability;
- `research_decision_log_zh.md`: concise Chinese interpretation and next-paper
  decision boundary;
- `references.bib`: primary literature cited by the draft;
- `figures/`: five PNG/PDF figures, captions, frozen scalar data, generator,
  and source manifest.

## Evidence identity

- activation source: `97a5b74cf79332115397d07c83b400c942859fb4`;
- GPU run: `20260904T150300Z-phk-v23-lf3-phase-latent-97a5b74`;
- local adjudication: `20260904T150300Z-phk-v23-lf3-local-adjudication-97a5b74`;
- outcome: `LF3_CARRIER_NOT_ESTABLISHED`;
- candidate: none;
- evidence: nominal, fixed-discretization, seed 17, one data-only T0 stage;
- not executed: label-free P0 physics refinement;
- not established: carrier success, PINN-specific value, superiority to direct
  `LF_ONLY`, multi-seed reliability, OOD/stress robustness, continuum truth,
  material calibration, experimental validation, or submission readiness.

The nominal fine/extra-fine reference and frozen evaluator were read locally
only after full recovery, hash verification, instance shutdown, and SSH
refusal. Both stress references remain `TWO_STRESS_REFERENCES_SEALED_UNREAD`.
