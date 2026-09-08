# ADR 0069: Activate PHK-V2.3 LF8 identity-correct competence-filter completion

- `status`: `ACCEPTED_ACTIVE`
- `date`: `2026-09-08`
- `phase_id`: `PHK_V23_LF8_IDENTITY_CORRECT_COMPETENCE_FILTER_COMPLETION_AND_SCHEDULE_ATTRIBUTION_EXECUTE`
- `starting_head`: `95e448e36a659ac266b670667543b80ce467da53`

## Decision

Run one mandatory identity-correct competence-filtered strong-form refinement,
P0-F*, from the exact LF6 DEV-R endpoint. It uses a fresh Adam optimizer, the
frozen 1,200-step materialized physics stream, 25-update transactional blocks
and five non-increasing dyadic learning rates. A block is accepted only when
the blind physics objective strictly decreases while the frozen full-medium
field and event safety conjunction remains valid. Rejection restores model,
optimizer, Python/NumPy/Torch RNG, accepted-step count, learning rate and stage
from a non-aliased deep snapshot before replaying the same 25 batches.

If and only if P0-F* reaches 1,200 accepted updates with a valid safety endpoint
and lower blind objective, run one matched control from exact DEV-R that replays
the accepted learning-rate schedule without competence audits, rejection or
rollback. This separates schedule sufficiency from the load-bearing effect of
the filter. Medium labels participate only in P0-F* no-gradient acceptance
audits; neither arm uses them in the physics loss.

The CPU qualification demonstrated the previously unreachable nonempty-Adam
rollback path over two mutate/reject/restore cycles on the real three-head model
with zero scientific optimizer updates. It is engineering identity evidence,
not a performance premise. A valid stopped prefix is a scientific endpoint;
after a valid stall or completed path, no further strong-form learning-rate,
block-size, optimizer, replay, weighting, sampling or network rescue is
authorized. Sparse, weak/control-volume, new-seed, OOD/stress, PJGR/R2/SRPG and
submission work remain outside LF8.
