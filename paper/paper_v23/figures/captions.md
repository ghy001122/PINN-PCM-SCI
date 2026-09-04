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
