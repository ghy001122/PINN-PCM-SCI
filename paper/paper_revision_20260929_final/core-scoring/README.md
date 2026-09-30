# Core phase and port scoring subset

This local package independently recomputes 30 existing primary metrics for ten frozen endpoints: E/F on original and shorter protocols, seeds 29/43, and F_cov on shorter/29/43. It contains two existing spatial references. No endpoint is selected using these errors.

Run with Python >=3.11 and NumPy >=2.0:

```text
python -I score.py --root <this-package-directory>
```

Every runtime input resolves beneath the explicit root; missing or escaped inputs raise an error. There is no old-workspace fallback. Results appear in `recomputed/results.json`.

## Exact scope and measurement

- Ephi: original FP64 phase on 160×80 cells, retaining all 1001 times over 0–2.5 and all 3872 original ROI cells (|x|≤0.55, 0≤z≤0.55). Spatial averaging is uniform over ROI cells; time uses the normalized original trapezoid rule. The main fine electrical reader originally scored this saved coarse-grid phase; this package does not substitute restricted fine-grid phase.
- Electrical traces: saved native 240×120 common-readout bottom current and Joule power. The historical `bottom_current_NRMSE` compares candidate **bottom** current with reference **top** current, then divides by reference **top** RMS. This preserves `add_power_metrics`; it is not silently changed to bottom-versus-bottom. Reference bottom current is retained to make this distinction explicit.
- Power: RMS(candidate Joule power − reference Joule power) / reference Joule-power RMS.
- Geometry contains full ROI mask and indices, cell coordinates, ROI coordinates, original time vector, normalized spatial and temporal weights. FP64 values are retained without rounding or thinning and stored with lossless NPZ compression.

## Verification and limits

The required comparison tolerance is rtol=2e−10, atol=2e−12. `independent-verification.json` records the actual separate-directory test with both scientific source roots blocked, the runtime-only environment exception, and the missing-input negative check. The exact frozen A/B records are copied for context only; ET, EV, full-domain S, event guards and all qualifications are not recomputed. This is ROI/full-history saved-array rescoring, not full-domain validation, saved-residual reaggregation, neural AD recomputation, checkpoint inference, training, or a new reference solve.

## Access and provenance

Repository commit `545c51a` publishes this scorer, configuration, provenance, expected values and the completed verification/result records. It deliberately excludes `arrays/*.npz`; therefore the Git checkout alone cannot rerun the 30 metrics. The complete array package remains local and has no public DOI or reviewer URL. P03 remains **OPEN** because the release does not provide the full-paper arrays, checkpoints or all historical evaluation inputs. No extra ZIP copy is maintained. Source paths in provenance are archival identities, never runtime fallback paths. No GPU was used.

The arrays are project-generated synthetic numerical evidence. No third-party experimental records, publisher figures, author-model data or model checkpoints are included. Scoring code is project-authored; this local package does not grant a new public redistribution licence. NumPy is an external dependency and is not redistributed.
