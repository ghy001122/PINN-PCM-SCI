# PHK-V2.3 event-competence recovery advisor draft

Status: `ADVISOR_DRAFT_UPDATED_LF6_P0_PRESERVATION_FAILED`

This package presents the bounded PHK-V2.2R--LF6 recovery sequence as a
failure-analysis and competence-first solver study. Its strongest positive
mechanism result remains LF4's matched teacher-interface exposure effect. LF6
does not establish a rank-specific increment: DEV-U failed the safety recall
gate, while DEV-R passed safety but missed strict cycle-1 timing. DEV-R was used
only as the deterministic safety near-carrier for the first executed label-free
P0 in the sequence.

P0 reduced the fixed blind physics objective from `4.927872` to `0.063147`
(`ratio=0.012814`, pass) but catastrophically failed preservation. V/T errors
drifted while phase was frozen; after joint unfreezing, event recall collapsed
to zero in both cycles. The terminal outcome is
`LF6_P0_PRESERVATION_FAILED`, candidate is none, and the unique next is
`PHYSICS_FORGETTING_RESULT_NO_RESCUE`.

## Package contents

- `manuscript.md`: English advisor-reviewable draft;
- `tables.md`: compact manuscript-ready evidence tables;
- `claim_evidence_matrix.md`: explicit claim audit;
- `reproducibility.md`: frozen identities and regeneration instructions;
- `reviewer_risk_self_check.md`: adversarial publishability assessment;
- `research_decision_log_zh.md`: Chinese research interpretation;
- `references.bib`: cited primary literature;
- `figures/`: fourteen PNG/PDF figures, frozen scalar data, generators, captions,
  and source manifests.

## LF6 evidence identity

- task: `PHK_V23_LF6_EVENT_FRONTIER_RANK_BAND_AND_SAFETY_GATED_PHYSICS_PILOT_EXECUTE`;
- activation commit: `55d552670ba0f727f781d4051b84efde474996f9`;
- engineering repair commit: `074eec7f76b4661deda1a622b5343bf992fa2715`;
- CPU-F: `20260906T065434Z-phk-v23-lf6-cpu-qualification`, zero updates, pass;
- DEV-U / DEV-R / P0 updates: `400 / 400 / 1200`;
- DEV-U: safety fail, strict fail;
- DEV-R: safety pass, strict fail only at cycle-1 timing;
- mechanism: `NO_RANK_SPECIFIC_INCREMENT`;
- P0: fixed-physics ratio pass, preservation fail;
- local extra-fine: DEV-R event guard pass; P0 event guard fail;
- direct `LF_ONLY` remains the strongest accuracy baseline;
- terminal outcome / candidate: `LF6_P0_PRESERVATION_FAILED` / none;
- stress: `TWO_STRESS_REFERENCES_SEALED_UNREAD`.

All nominal fine/extra-fine and direct-baseline evaluation occurred locally only
after artifact recovery, hash verification, instance shutdown, TCP closure, and
explicit SSH connection refusal. This package does not claim a strict LF6
carrier, rank-band attribution, PINN Pareto gain, strong-baseline improvement,
multi-seed reliability, sparse/OOD/stress performance, material calibration,
experimental validation, SOTA, or submission readiness.
