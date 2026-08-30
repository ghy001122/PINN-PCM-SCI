# Supplementary information

## S1. Evidence scope

The study concerns one transparent, dimensionless, fixed-discretization
two-dimensional electric–thermal–phase benchmark. The nominal finite-volume
carrier is a local development target. It is not experimental data, material
calibration, or continuum truth. Two stress carriers were generated and
hash-sealed before the neural run but were never opened because nominal
competence failed.

## S2. Pre-nominal route disposition

The 100-update V100 profile contained strong raw, MF only, sampler only,
MF + sampler, and one strict routed PHA probe. All runs were finite. The strict
probe required 0.8980 s/update versus 0.5517 s/update for MF only, a ratio of
1.6276 below the frozen 1.8 ceiling. Its primary improvement over MF + sampler
was 0 rather than the required 0.10. The strict probe was removed without gate
tuning. Generic RAR did not reach a stable frozen implementation by its P0
deadline, so v1.1 used the four-arm fallback. Neither exclusion is evidence that
the corresponding idea fails in general.

## S3. Frozen arm identities

Three physical outputs are produced by independent modified gated MLP heads.
There is no shared trunk. Raw heads receive normalized coordinates. The
multi-frequency heads receive fixed Band-A anisotropic Fourier features. The
sampler uses no reference values; it ranks a candidate pool using PDE residual,
predicted phase interface, and predicted Joule density while retaining a 35%
fresh Sobol floor.

| Arm | Parameters | Field-selective features | Adaptive physics sampler |
|---|---:|---|---|
| Strong raw | 39,939 | No | No |
| MF only | 54,915 | Yes | No |
| Sampler only | 39,939 | No | Yes |
| MF + sampler | 54,915 | Yes | Yes |

All arms started from scratch with the same seed, precision, optimizer, point
counts, causal windows, and update count. No early stopping or checkpoint
selection occurred.

## S4. Sampling and causal schedule

The sampler mixture was frozen to 0.35 Sobol, 0.25 residual, 0.25 phase
interface, and 0.15 Joule density. Candidate-pool refresh occurred every 250
updates. Four windows were opened at fixed fractions of training and retained an
equal replay quota from prior windows. The training log records the active-window
count and whether collocation was refreshed.

## S5. Training behavior

Each arm completed 1000 Adam updates and reduced its logged PDE loss:

| Arm | First PDE loss | Final PDE loss | Final/first |
|---|---:|---:|---:|
| Strong raw | 0.117633 | 0.005137 | 0.0437 |
| MF only | 0.730313 | 0.001452 | 0.0020 |
| Sampler only | 0.221026 | 0.004885 | 0.0221 |
| MF + sampler | 1.033186 | 0.006700 | 0.0065 |

Loss spikes coincide with scheduled window openings and sampling refreshes.
They remained finite. The final loss decrease is therefore an implementation
fact, but it is not a scientific success criterion.

## S6. Event evaluation

The frozen phase threshold was 0.5 and the event threshold was an active ROI
fraction of 0.02. The reference event times were 0.2406 and 1.4984. Reference
peak ROI fractions were 0.068698 and 0.061983, with full recovery after both
events. All four predictions had zero active ROI fraction at every saved time.

Because a predicted event was absent, event-time RMS and interface Hausdorff
distance were infinite/undefined. Hotspot width and location comparisons were
not available for arms whose temperature response did not form the required
hotspot. These adverse/undefined metrics were not suppressed.

## S7. Why the primary value is identical

Let \(A_p(t)\) and \(A_r(t)\) be the predicted and reference active sets above
\(\phi=0.5\). For every arm, \(A_p(t)=\varnothing\). The symmetric difference is
therefore

\[
A_p(t)\,\triangle\,A_r(t)=A_r(t).
\]

The primary score 0.00515 is the time average of the reference active-domain
fraction. It is identical across arms because all four make the same topological
error. A competence gate is necessary to prevent this sparse-event average from
being interpreted as high accuracy.

## S8. Decision-machine output

The decision artifact contains:

```text
eligible.STRONG_RAW=false
eligible.MF_ONLY=false
eligible.SAMPLER_ONLY=false
eligible.MF_PLUS_SAMPLER=false
selected_arm=null
strongest_comparator=null
confirmation_training_authorized=false
stress_unseal_authorized=false
terminal_no_rescue=true
```

No comparator ranking or combined-gain calculation is valid after universal
competence failure.

## S9. Reference-sealing boundary

The nominal development reference was opened only on the local workstation after
the four cloud predictions were complete. The cloud summary records
`reference_fields_read=false`. The two stress references require a passing
nominal decision and a final freeze with six verified prediction identities.
Neither prerequisite exists; both references remain sealed and unread.

## S10. Negative-result boundary

The result supports only the statement that the four frozen arms lacked basic
event competence under this specific single-seed 1000-update protocol. It does
not establish that PINNs, Fourier features, residual sampling, or the proposed
physics sampler fail in general. It does not compare alternative optimizers,
budgets, seeds, loss balances, or continuation strategies.
