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
larger in both recovery pools. The plot uses a log scale for residuals and does
not report an executed LF5 optimizer trajectory.

## Figure 10. Timing-calibration conflict versus local alignment

LF4 DEV-M preserves low phase weighted MSE but misses the cycle-1 timing gate;
DEV-C passes aggregate timing while inflating phase error. LF5's local edge
audit shows that the latter endpoint is not a better initialization for the
proposed zero-level residual, so aggregate timing improvement cannot be treated
as evidence for per-cell temporal alignment.

## Figure 11. LF5 decision path

All temporal geometry, identity, direction-sign, and finite-gradient checks
passed, but the preregistered mechanism gate failed because DEV-C was worse in
both onset pools. DEV-T and conditional P0 were therefore not run. This is a
zero-update rejection of one mechanism premise, not a failed GPU model or a
PINN result.
