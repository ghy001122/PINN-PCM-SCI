# Figure captions

## Figure 1. Recovery ladder

Full-medium phase maxima and qualitative event states across the bounded recovery sequence. Scratch physics training remained in the cold state; LF0 supervision approached but did not cross the event threshold and violated potential admissibility; LF1 recovered overly broad events; LF2 target-measure calibration erased them; and LF3 recovered a valid, localized two-cycle field but missed the preregistered recall gate. The sequence is diagnostic and single-seed, not a monotone benchmark of interchangeable algorithms.

## Figure 2. Full-medium event metrics

Cycle-wise hard recall, precision, and active-mass ratio relative to the medium teacher. LF1-B0 covered most teacher-positive support but produced more than five times the target event mass and therefore had low precision. LF2 collapsed to zero event support. LF3 corrected the overbreadth, attaining precision above 0.86 and mass ratios near 0.888, but retained only 0.806 and 0.769 of the target support. Dashed lines and the shaded band show the frozen LF3 thresholds.

## Figure 3. Local error gap

Nominal extra-fine error ratios relative to direct medium interpolation (`LF_ONLY`; ratio 1). LF3-T0 substantially narrows the phase error gap relative to LF1 and LF2, while remaining roughly 5.8–5.9 times worse in the phase metrics and 9.6–39 times worse in temperature, potential, and current metrics. This strong-baseline comparison prevents solver recovery from being misreported as paper-positive accuracy.

## Figure 4. Phase-support snapshots

Reference and LF3-T0 phase fields at the two reference peak indices, with a threshold-support audit at \(\phi\ge0.5\). Green denotes overlap, red missed reference support, blue excess support, and gray inactive agreement. The visual pattern is consistent with the full-medium high-precision/low-recall diagnosis: the event is localized and correctly placed, but its boundary support is incomplete.

## Figure 5. Evidence gates

The preregistered three-level claim ladder and observed stopping point. T0 failed Level 1 only at cycle-wise recall, so the label-free P0 physics stage was not triggered. Level 2 PINN-specific Pareto value and Level 3 direct-baseline candidate value were consequently not tested; they cannot be inferred from T0.

## Figure 6. Interface-boundary geometry

Zero-update CPU-G localization of LF3-T0 support errors on the full medium teacher. Of 481 false-negative and 227 false-positive nodes in the two event windows, 94.6% and 87.7%, respectively, lie directly on the nonperiodic four-neighbour teacher interface. The boundary logit-margin distribution spans nearly zero to 3.50, motivating a matched exposure test without itself establishing a training mechanism.

## Figure 7. Matched LF4 development ablation

Fixed step-400 endpoints for equal-budget phase-only arms from identical LF3-T0 weights and common base batches. Replacing generic global extras with the teacher-interface band raises minimum two-cycle recall from 0.819 to 0.909 while slightly reducing phase weighted MSE. Two-sided BCE on the identical band raises recall to 0.942 and restores both timing gates, but increases phase error to 0.0297, above the frozen entry limit. This is a recall–fidelity trade-off, not a carrier pass.

## Figure 8. LF4 mechanism and physics-Pareto gate

The matched screen supports teacher-interface exposure relative to global-extra supervision (`ΔRmin=0.08984`) but rejects threshold-aligned BCE as a quality-preserving load-bearing mechanism. DEV-G failed timing, DEV-M failed cycle-1 timing, and DEV-C failed phase-error preservation. With no eligible development carrier, label-free P0 correctly remained unexecuted; no physics-objective ratio, PINN Pareto, or candidate signal exists.

## Figure 9. LF5 temporal-edge geometry and residual premise

CPU-T reconstructed four cycle- and direction-resolved saved-cadence crossing
pools with 68/68/64/64 valid edges and zero invalid edges. Despite DEV-C's
better aggregate event timing in LF4, its weighted mean absolute teacher-secanted
zero-level residual was larger than DEV-M in both onset pools and dramatically
larger in both recovery pools. The plot uses a log scale for residuals. This
valid zero-update evidence is distinct from the later user-overridden,
identity-invalid DEV-T trajectory.

## Figure 10. Timing-calibration conflict versus local alignment

LF4 DEV-M preserves low phase weighted MSE but misses the cycle-1 timing gate;
DEV-C passes aggregate timing while inflating phase error. LF5's local edge
audit shows that the latter endpoint is not a better initialization for the
proposed zero-level residual. The exploratory DEV-T point is shown only as
directional telemetry because its temporal stream identity drifted; it preserves
low phase error but still misses cycle-1 timing.

## Figure 11. LF5 decision path

All temporal geometry, direction-sign, and finite-gradient CPU checks passed,
but the preregistered mechanism gate failed because DEV-C was worse in both
onset pools. A later explicit override ran DEV-T for 400 updates; its temporal
ledger differed from the frozen SHA from step 1, so the endpoint was invalidated
before checkpoint writing. P0 was not run. Non-voting telemetry cannot establish
a carrier, PINN result, or candidate.

## Figure 12. LF6 event-frontier geometry

Zero-update CPU-F geometry for the medium-teacher two-percent active-count
functional. The 968-cell ROI gives critical rank 20. Adjacent saved endpoints
bracket the threshold in both cycles; stable teacher-logit sorting yields ranks
17--22 (six cells) for cycle 1 and ranks 17--20 (four cells) for cycle 2. The
frontier is frozen teacher-side preprocessing, not a differentiated rank loss or
a trained-model result.

## Figure 13. LF6 matched development endpoints

DEV-U and DEV-R use identical initialization, 400-update budget, base/spatial
streams, optimizer, and loss weights; only endpoint cell selection differs.
DEV-U minimum recall is 0.897 and fails safety. DEV-R minimum recall is 0.918
and passes safety, but its cycle-1 timing error 0.01053 exceeds the strict 0.005
gate. Since neither arm is strict, the frozen result is
`NO_RANK_SPECIFIC_INCREMENT`; DEV-R is only a safety near-carrier.

## Figure 14. LF6 physics-objective reduction versus preservation

The first 550 pure-physics updates keep phase bitwise frozen while potential and
temperature errors drift. After phase unfreezing, minimum recall falls to 0.216
by step 600 and reaches zero by the endpoint. The fixed blind physics objective
nonetheless falls from 4.9279 to 0.06315 (ratio 0.012814, pass). This is an
executed `P0_PRESERVATION_FAILED` result: residual reduction and event
competence diverge, with no PINN Pareto or candidate claim.

## Figure 15. LF7 matched continuation: valid small-step failure and incomplete filter screen

Panel A shows that identity-valid P0-S reduced the fixed blind objective from
4.9279 to 2.9719 (ratio 0.6031), missing the frozen 0.50 gate. Panel B separates
this reduction from carrier preservation: cycle 1 disappeared, while cycle-2
recall/recovery fell to 0.076/0.028. Panel C reports only P0-F's first-block
proposals: four rates were rejected for V/T preservation, and `eta0/16` passed.
Adam-state snapshot aliasing then caused rollback identity drift. P0-F has no
valid endpoint; the panel is partial diagnostic evidence, not filter efficacy,
PINN Pareto value, or a candidate result.

## Figure 16. LF8 identity-correct competence-filter path

Panel A shows all six identity-valid 25-update proposals relative to the frozen
DEV-R blind physics objective. Four larger rates were rejected and exactly
rolled back before `eta0/16` established a safety-valid 25-update prefix with
(J/J_0=0.98913). Panel B identifies temperature preservation as the
load-bearing gate: the next block at the same accepted rate reached a lower
proposed objective but raised relative temperature error to 1.292, above the
1.05 limit, and was exactly rolled back. Panel C records the resulting evidence
ladder. F* stalled at 25 accepted updates, so the conditional schedule control
was not triggered and matched attribution is unavailable. Medium competence
audits govern acceptance; the path is not label-free and supplies no PINN
Pareto, direct-baseline gain, or candidate result.
