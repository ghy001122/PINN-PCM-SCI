# PHK-V2.3 event-competence recovery advisor draft

Status: `ADVISOR_DRAFT_UPDATED_LF5_EXPLORATORY_IDENTITY_INVALID`

This package is the first manuscript draft that integrates the bounded
PHK-V2.2R→LF4 solver-recovery sequence. It is deliberately written as a
failure-analysis and competence-gated mechanism study. LF4 adds a matched
global-extra/interface-band/threshold-BCE screen from the exact LF3-T0 weights.
Interface exposure raised minimum two-cycle recall from `0.8194` to `0.9093`
under the frozen quality controls, supporting a bounded boundary-exposure
mechanism result. Threshold-aligned BCE raised recall further but increased
phase error to `0.02967`, so it did not provide a quality-preserving increment.
No arm passed every entry condition; P0 ran zero updates and no PINN-specific
gain or candidate was established. LF5's preregistered CPU gate then rejected
the temporal-zero-level premise because DEV-C had larger mean absolute onset
residual than DEV-M in both cycles. After that result, the user explicitly
authorized the unchanged 400-step DEV-T as exploratory evidence. Its base and
spatial streams matched, but the temporal stream diverged from the frozen SHA
from the first batch. The 400 completed updates are therefore identity-invalid,
no checkpoint was written, and P0 remained unexecuted. Directional step-400
telemetry recovered recall to about 0.918 in both cycles while still missing
cycle-1 timing; it is reported only as non-voting evidence.

## Package contents

- `manuscript.md`: English advisor-reviewable draft;
- `tables.md`: manuscript-ready evidence, metric, and decision tables;
- `claim_evidence_matrix.md`: explicit claim audit;
- `reproducibility.md`: exact code, input, run, and evaluation identities;
- `reviewer_risk_self_check.md`: adversarial assessment of publishability;
- `research_decision_log_zh.md`: concise Chinese interpretation and next-paper
  decision boundary;
- `references.bib`: primary literature cited by the draft;
- `figures/`: eleven PNG/PDF figures, captions, frozen scalar data, generator,
  and source manifests for the LF3 and LF5 figure groups.

## Evidence identity

- LF4 activation source: `5dbde1d210b6f2ff15d0f341ee316e59b49a1074`;
- GPU run: `20260905T102817Z-phk-v23-lf4-interface-band-5dbde1d`;
- local adjudication: `20260905T102817Z-phk-v23-lf4-local-adjudication-5dbde1d`;
- outcome: `LF4_NO_DEVELOPMENT_ENTRY`;
- candidate: none;
- evidence: nominal, fixed-discretization, seed 17, three matched 400-update
  phase-only development arms;
- not executed: label-free P0 physics refinement;
- established only within the frozen screen: teacher-interface exposure improves
  minimum recall beyond equal-budget global-extra supervision;
- not established: threshold-BCE load-bearing value, carrier success,
  PINN-specific value, superiority to direct
  `LF_ONLY`, multi-seed reliability, OOD/stress robustness, continuum truth,
  material calibration, experimental validation, or submission readiness.

LF5 evidence identity:

- starting source: `d86ddf1d206c611087a1b5284acda69efdfda9fa`;
- CPU-T: `20260905T150045Z-phk-v23-lf5-cpu-qualification`;
- CPU outcome: `LF5_TZL_ALIGNMENT_NOT_SUPPORTED_CPU`;
- valid temporal pools: `68/68/64/64`, invalid-edge fraction `0`;
- DEV-M versus DEV-C onset mean absolute residual:
  `0.2921<0.7238` (cycle 1) and `0.3100<0.6041` (cycle 2);
- post-qualification role: `POST_QUALIFICATION_USER_OVERRIDE_EXPLORATORY`;
- DEV-T scientific optimizer updates / GPU trajectories: `400 / 1`;
- expected/actual temporal stream SHA: `8FD79D99...C9B3BD9` /
  `48A0C6B4...AAFB127`; base and spatial streams matched;
- terminal outcome: `LF5_NUMERICAL_OR_IDENTITY_INVALID`;
- DEV-T checkpoint/prediction: none; P0: not run because of the higher-priority
  identity failure;
- candidate: none; stress remains sealed/unread.

The nominal fine/extra-fine reference and frozen evaluator were read locally
only after full recovery, hash verification, instance shutdown, and SSH
refusal. Both stress references remain `TWO_STRESS_REFERENCES_SEALED_UNREAD`.
