# Reviewer-risk self-check

## 1. “There is still no successful PINN method.”

Correct. LF6 finally executed label-free physics, but preservation failed. The
paper must be positioned as failure analysis and bounded solver recovery, not a
positive methods paper.

## 2. “You call DEV-R a carrier even though it missed strict timing.”

We do not. DEV-R passed the preregistered relaxed safety entry used only to make
P0 testable. It failed strict cycle-1 timing and is called a safety near-carrier.

## 3. “Does DEV-R prove the event-frontier rank mechanism?”

No. DEV-U and DEV-R were matched except endpoint cell selection, but neither was
strict. The frozen mechanism outcome is `NO_RANK_SPECIFIC_INCREMENT`; DEV-R's
safety selection cannot be repurposed as attribution.

## 4. “A lower physics residual should mean a better solution.”

Not here. The fixed blind objective ratio was `0.012814`, yet the event carrier
failed and V/T/phase/topology preservation errors increased 28.6/52.6/25.8/20.0
times. The paper reports this divergence rather than treating residual reduction
as physical validation.

## 5. “Could the P0 failure be numerical or an engineering retry artifact?”

The final P0 was finite, phase-range valid, potential-admissible, exact-stream
matched, and complete at 1200 updates. A prestep checkpoint-identity comparison
bug was isolated and repaired without rerunning the completed DEV arms; P0 had
zero prior optimizer steps. The repaired P0-only path revalidated exact DEV
artifacts and input identities. The P0 result is therefore a valid scientific
negative, not an engineering failure.

## 6. “What exactly supports physics forgetting?”

At step 550, phase was bitwise unchanged and had no optimizer state, but V/T
errors had already drifted. Fifty updates after phase unfreezing, minimum recall
fell from 0.918 to 0.216; it reached zero by the endpoint. This supports the
observed two-stage forgetting trajectory, not a unique cause or universal law.

## 7. “Why is direct interpolation much stronger?”

The complete medium field is available, making direct `LF_ONLY` unusually
strong but scientifically honest. Neither DEV-R nor P0 is noninferior. No speed,
compression, sparse-data, inverse, or OOD advantage was measured, so none is
claimed retrospectively.

## 8. “The recovery sequence was adapted after every failure.”

Yes. Campaigns were separately preregistered and terminally closed. Historical
comparisons localize failure modes but are not a single factorial experiment.
Only LF4 and LF6 comparisons explicitly described as matched support matched
mechanism statements.

## 9. “Single-seed fixed-discretization evidence is insufficient.”

Agreed. There is no multi-seed, formal OOD/stress, continuum, material, or
experimental confirmation. Stress remains sealed and unread because no
candidate exists.

## 10. “Why not tune P0 or add replay now?”

That would be a new scientific identity selected after observing failure.
Replay or another preservation mechanism should be tested only in a separately
authorized matched continuation against this pure-physics endpoint.

## 11. “Is LF7 P0-F label-free?”

No. Medium labels do not enter its gradient, but medium-teacher competence
functionals decide whether each proposed block is accepted. We therefore call
it multifidelity competence-filtered PINN refinement, not label-free physics.

## 12. “Did LF7 establish a new optimization method?”

No. LF7 adapts attributed trust-region, filter, restoration, and backtracking
primitives. P0-S validly rejects smaller steps alone. P0-F rejected four unsafe
proposals and accepted one very small block, but Adam-state snapshot aliasing
then broke rollback identity. With no valid endpoint, neither success nor
failure of the filter mechanism can be inferred.

## 13. “Does the accepted P0-F block prove the filter works?”

No. It proves only that one `eta0/16` proposal passed the frozen block checks.
It cannot be extrapolated to later blocks, a terminal carrier, or a PINN Pareto
result. The forensic fix was not executed scientifically and does not repair the
evidence retrospectively.

## Submission-readiness verdict

```text
ADVISOR_DRAFT: YES
NEGATIVE_DIAGNOSTIC_PAPER_WITH_BOUNDED_MECHANISM_RESULT: PLAUSIBLE
POSITIVE_METHODS_SUBMISSION: NO
CAS_Q2_POSITIVE_METHOD_CLAIM: NOT SUPPORTED
CANDIDATE: NONE
LF7_RESULT: MATCHED_SCREEN_INCOMPLETE_IDENTITY_INVALID
LF7_FILTER_ATTRIBUTION: UNAVAILABLE
```
