# Final manuscript consolidation contract

Task: PCM-20260929-FINAL-MANUSCRIPT-CONSOLIDATION-01. Authorized by the user's explicit implementation request. Scientific baseline: f4e6202487af65756c6fcea896dec353172a7902; 79542a0 records its publication only.

## Purpose

Explain whether a grounded electrical solve during neural state learning leaves thermal/phase and device differences that a common post-training electrical solve does not remove. Observations are described as discrete field observations; B1 provides the separate missing-phase extension. The interpretation remains bounded to the tested configurations and does not isolate VJP causality.

## Fixed sequence

1. Restructure the authoritative manuscript and full supplement; preserve physics, all adverse evidence, and the original thresholds and accepted endpoints.
2. Freeze the four comparison panels and compact difference/qualification table from full-precision CSVs. Add accuracy versus recorded algorithmic work, keeping parent, calibration, training and readout separate. Do not compare wall-clock speed across incomparable environments.
3. Conduct one formal five-question manuscript decision. Local wording/figure corrections are allowed; no new scientific route follows from this review.
4. Build and visually inspect the manuscript and full supplement DOCX/PDF from their Markdown sources.
5. Assemble and independently verify the core saved-array phase/current/power scoring package. This enhancement cannot block the manuscript. An unresolved package problem is recorded as an access limitation, not an invitation to run new science.

## Frozen comparison selection

- E/F: original and shorter protocols, seeds 29 and 43, spatial reference and fine electrical reader.
- E/F_cov: shorter protocol, seeds 29 and 43, spatial/fine.
- E/D_E: shorter protocol, seeds 29 and 43, spatial/fine.
- E/B_E: original protocol, seed 43, fine reader, old/refined/spatial references together.
- Metrics: original Ephi, bottom-current NRMSE and power-trace NRMSE; original A/B decisions remain attached to their complete criteria. Sensitivity rows are not independent repetitions.

## Phase scoring enhancement

Use ten candidate and two reference FP64 ROI phase arrays from existing saved fields, with the original 1001 times over 0 to 2.5, original 160 by 80 state grid, and ROI abs(x)<=0.55, 0<=z<=0.55 (3872 cells). Fine electrical scoring does not replace the original phase array. Use the existing spatial mapped reference, normalized ROI cell weights, and normalized trapezoidal time weights. The raw phase payload is approximately 355 MiB. No field inference, new reference restriction, solver or GPU is required. The entry must use only the package root and fail on missing inputs. Reproduce Ephi and I/P under original arithmetic tolerances; do not claim this reproduces every full A/B criterion, full-field metric, neural AD or checkpoint inference.

## Stop and delivery

Only a core numerical error or a substantive comparison defect sufficient to overturn E/F or E/F_cov interrupts manuscript closeout. Missing data-delivery inputs do not. New training, seeds, networks, objectives, reference trajectories, GPU, OOD, noise, materials, Deep Research, Git publication, public data upload and actual submission are excluded. P02/P03 and existing material/generalization limitations remain open. Frozen history and unrelated working-tree changes are preserved. New outputs await later authorized remote synchronization; no instance is started for document transfer.
