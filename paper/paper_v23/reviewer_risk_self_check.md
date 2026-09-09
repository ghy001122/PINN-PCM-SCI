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

## 14. Does LF8 finally prove the competence filter works?

No. LF8 prospectively fixes rollback identity and verifies five exact rejected
block restorations. It retains one safety-valid 25-update prefix with blind
objective ratio 0.98913, then rejects the next same-rate block on temperature
preservation. This establishes a bounded valid-prefix stall, not completion,
Pareto value, or superiority.

## 15. Why was the schedule control not run?

The preregistered control required F* to complete 1200 accepted updates while
remaining safety-valid. F* stopped at 25 accepted updates. Running a 1200-step
schedule replay anyway would not be matched to the realized accepted path.
Therefore `MATCHED_ATTRIBUTION_UNAVAILABLE` is required, not a favorable filter
comparison.

## 16. Is LF8 label-free because medium labels supplied no gradient?

No. Medium-derived event and field functionals govern every accept/reject
decision. The correct identity is multifidelity competence-filtered PINN
refinement. It also remains far behind direct `LF_ONLY` and supplies neither a
PINN Pareto nor a strong-baseline gain.

## 17. Does implementing LF9 establish a new weak-form or control-volume PINN?

No. Variational, space-time control-volume, block-coordinate, staggered,
enthalpy phase-change, and phase-field local-balance PINNs all precede LF9. The
closed campaign is a matched test of a project-specific composition:
equation-to-owning-head gradient routing plus optional thermal-CV replacement
inside the existing competence filter. Both screens stalled after one safe
block, and their conservation audits were nearly identical. This rejects a
load-bearing thermal-CV increment in the frozen screen, not the prior-art
methods generally; no general novelty claim follows from either name.

## 18. Are the absent full and no-filter arms hidden failures?

No. Both were conditional. Full refinement required a screen arm to reach 200
accepted updates; neither exceeded 25. The no-filter control required a complete
internal Pareto path; none existed. Their zero updates are exact non-triggers,
not failed endpoints, and provide no filter attribution.

## Submission-readiness verdict

```text
ADVISOR_DRAFT: YES
REPLICATED_NEGATIVE_DIAGNOSTIC_PAPER_WITH_BOUNDED_MECHANISM_RESULT: PLAUSIBLE
POSITIVE_METHODS_SUBMISSION: NO
CAS_Q2_POSITIVE_METHOD_CLAIM: NOT SUPPORTED
CANDIDATE: NONE
LF10_RESULT: LF10_FEASIBLE_DIRECTION_SCREEN_NEGATIVE_PAPER_STRENGTHENED
LF10_MECHANISM: NO_EXTENDED_FEASIBLE_PATH_FOUND
LF10_INTERFACE: INTERFACE_EFFECT_STREAM_REPLICATED
LF10_FORGETTING: PHYSICS_FORGETTING_STREAM_REPLICATED
LF10_FULL_AND_CONTROL: NOT_RUN_PREREQUISITE_NOT_MET
LF10_NEXT: FINALIZE_REPLICATED_INTERFACE_AND_FORGETTING_PAPER_NO_MORE_REFINEMENT_RESCUE
```

## 19. Does LF10 establish model-seed robustness?

No. Streams 17/23/29 vary pre-materialized sampling while retaining one model
initialization and object. The result is sampling-stream replication only.

## 20. Does PROJ establish a feasible-direction method?

No. PROJ used medium-derived competence gradients, retained the same 25-update
endpoint as CTRL, and did not reach the 200-update screen. It is neither
label-free nor an incremental method result. Earlier projected constraint
changes motivate the test but do not override its negative endpoint.

## 21. Are full refinement and its control hidden failures?

No. Both were conditional on a screen reaching 200 accepted updates. Neither
screen exceeded 25, so both are `NOT_RUN_PREREQUISITE_NOT_MET`, not failed
trajectories. They provide no filter or schedule attribution.

## 22. Does the 5-by-5 threshold audit prove universal baseline dominance?

No. Direct `LF_ONLY` led the mean symmetric-difference predicate in 375/375
role-grid comparisons. These are not 375 distinct predictions, do not cover all
metrics, and include a role alias sharing the same prediction SHA. Historical
LF4 stream-17 threshold predictions were unavailable and remain `NA`.

## 23. What exactly replicated?

The paired interface recall effect was positive in 3/3 streams, with quality
preservation in 2/3. Strong-physics continuation degraded event competence in
3/3 streams; 2/3 crossed the residual-ratio gate and 0/3 achieved field-event
Pareto. This supports a replicated bounded failure-analysis narrative, not a
positive PINN method, causal proof, sparse/OOD claim, or submission-ready
candidate.
