# Reviewer-risk self-check

## Major risks

1. **No positive method result.** The proposed method failed the competence
   gate. The draft is positioned as a bounded negative Method-MVP and diagnostic
   protocol, not as a successful new solver.
2. **Single seed and single nominal case.** No variance, significance, or
   generalization claim is made. Stress cases remain sealed.
3. **Fixed discrete target.** The finite-volume trajectory is not described as a
   continuum oracle or experimental truth.
4. **Budget dependence.** The result holds for exactly 1000 Adam updates and the
   final checkpoint. Longer or different optimization is unknown.
5. **Sparse metric pathology.** The primary value 0.00515 appears small despite
   complete event failure. The paper derives why and places event guards first.
6. **Attribution unavailable.** Scalar differences between sampler, MF, and raw
   are not converted into component claims because all arms are ineligible.

## Questions an adversarial reviewer may ask

### Did the networks really train?

Yes in the implementation sense: all arms completed, remained finite, and
reduced logged PDE loss. Figures and manifests bind the trajectories. This does
not imply scientific competence.

### Why not train longer or choose a better checkpoint?

The protocol froze 1000 updates and final checkpoint only. Changing that after
seeing failure would invalidate the comparison. It is a legitimate future study
with a new contract.

### Is the event target too small for the metric?

Yes, and that is precisely why the metric is subordinate to event guards. The
reference event is numerically resolved and crosses the preregistered ROI
threshold; the predictions never cross the phase threshold anywhere.

### Can the paper claim the sampler helped because some errors are lower?

No. Sampler only has lower phase, temperature, and current errors than some arms,
but it still misses both events. The claim audit prohibits a benefit statement.

### Were the stress cases hidden because they were adverse?

No. Access was cryptographically and procedurally gated on a nominal PASS. The
nominal decision failed, so the references were not opened and no stress metric
exists.

## Submission-positioning result

The package is advisor-reviewable and reproducible, but it is not presently a
positive Q2-target Method-MVP. Its strongest defensible story is a competence-
gated negative study of sparse-event failure. Any journal submission decision,
author metadata, or external contact remains outside the current authorization.
