# Figure captions

## Figure 1 — `figure-01-workflow`

Pre-result-frozen workflow. Source and license identities, machine contracts, the complete-case split, and the 12-intent qualification ladder precede neural training. The Oracle No-Go closes the method path; it is not a negative result for an unrun PINN.

## Figure 2 — `figure-02-source-anatomy`

Source and baseline anatomy. Directly identified source modules (`A`), proposed PCM adaptations (`A′`), implementation/license boundaries, and PHK-V2 evidence status are separated. Fixed-source module smoke is not paper-metric reproduction.

## Figure 3 — `figure-03-qualification-ladder`

Frozen 12-intent qualification ladder. Intents 1–8 completed, intent 9 failed and was consumed, and intents 10–12 were not reached. Every PINN/PHA/KC/formal arm is downstream of the complete Oracle Gate.

## Figure 4 — `figure-04-event-trajectories`

Nominal event trajectories across the tested spatial/time resolutions. Every configuration produces a first ROI threshold crossing, followed by insufficient recovery and no new upward crossing in cycle 2. The event threshold and two-cycle rule were frozen before these results.

## Figure 5 — `figure-05-convergence-controls`

Unclipped six-component space, time, and replay differences. Medium-to-fine differences are smaller than coarse-to-medium differences, and exact replay is zero across all components. These numerical diagnostics do not override the failed two-cycle event contract.

## Figure 6 — `figure-06-causal-and-claim-boundary`

Nominal versus Joule-off synthetic causal control and final claim boundary. Joule heating produces a resolved thermal/phase effect within the engineering benchmark, while the full Oracle Gate fails because the event contract is false and a required control fails to execute. No material validation, neural floor, or PINN method result follows.

## Reproduction

From the repository root, figures are regenerated only from existing JSON/NPZ carriers using any Python environment satisfying `requirements-figures.txt`:

~~~powershell
python paper_v2\figures\generate_figures.py
~~~

The generator verifies the terminal summary SHA and writes six PNG/PDF pairs, six derived CSV files, and `source-manifest.json`. It performs no solver or training work.
