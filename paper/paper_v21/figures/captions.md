# PHK-V2.1 figure captions

## Figure 1 — Failure-preserving route outcome

The independent PHK-V2.1 route repaired the control solver, selected one engineering object, and froze five scientific contracts before the first voting solve. All 14 qualification intents completed, but the event-time component failed the frozen spatial-convergence gate. Author-metric replication and all PINN stages were therefore not reached.

## Figure 2 — Qualification ladder

All 14 preregistered intents completed without replacement. Zero-drive and Joule-off correctly produced no event; the wide-heater control lost its second-cycle event but was only required to complete and pass numerical guards. The terminal decision was not an execution failure: it was made after the complete convergence comparison.

## Figure 3 — Nominal event behavior

Coarse, medium, fine, and extra-fine nominal solutions all produced two localized events with complete recovery. Their event times and peak ROI phase fractions appear stable enough for a qualitative plot, illustrating why event existence alone is not sufficient to qualify an oracle.

## Figure 4 — Controls

Peak ROI phase fractions for nominal and five mechanistic/geometric controls. Zero-drive and Joule-off eliminate both events. Conductivity-ratio-one and latent-off retain both events. The wide-heater control retains only the first event, while the narrow-interface control remains two-cycle event-positive. These are bounded properties of the transparent synthetic object.

## Figure 5 — Decisive convergence gate

For each component, the plotted ratio is the fine-to-extra-fine difference divided by the larger of the medium-to-fine difference and the declared component tolerance. Ratios at or below one pass the monotonic rule. Five components pass; the two-cycle event-time ratio exceeds one and independently closes the oracle route.

## Figure 6 — Claim boundary and accounting

Evidence accumulated through engineering selection and 14 completed qualification intents. The qualified-oracle layer returned No-Go, leaving Sharp/PF author-metric replication, neural-floor sealing, PINN/PHA/KC training, and formal OOD not reached. Recorded S1 solver compute was 1.128515625 CPU core-hours, with no GPU work and no failed solver intent.

## Reproduction

From the repository root, run:

~~~powershell
.\.venv\Scripts\python.exe paper_v21\figures\generate_figures.py
~~~

The generator verifies the immutable terminal-summary SHA256, reads only existing S1 evidence, performs no solver or training work, and rewrites six PNG/PDF figures plus six CSV source tables and `source-manifest.json`.

