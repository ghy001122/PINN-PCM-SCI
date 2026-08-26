# Figure captions and evidence boundaries

All six figures are bounded by the terminal status `NO_ORACLE_EVENT_OR_PINN_EVIDENCE`. “Verified” below applies only to the evidence explicitly named; it does not imply a qualified driven oracle, a device event, a PINN result, or experimental validation.

## Figure 1 — Pre-registered route gates

**Files:** `figure-01-route-gates.png`, `figure-01-route-gates.pdf`

**Caption.** Pre-registered source fallback and entry into the synthetic numerical route. S0 fixed the route order before S1 evidence was read. The bounded S1 review closed the COMSOL 6.4 route because the required research-use pass was not established and the source contract remained incomplete, then closed the PCMO reaction–drift fallback because the published object was a lumped point-device model dependent on an unpublished TCAD lookup table rather than a two-dimensional conservative defect field. These failures automatically activated the fully transparent, non-source-aligned `SYN_EDT_2D_V1` engineering benchmark and its pre-result-frozen S2 numerical contract. No COMSOL execution, source stitching, experimental identity, or synthetic validation claim is represented.

## Figure 2 — Source-route qualification matrix

**Files:** `figure-02-source-matrix.png`, `figure-02-source-matrix.pdf`

**Caption.** Bounded S1 source-route qualification matrix. Red cells are route-closing failures, amber cells are partial or unknown-not-pass findings, and green cells identify documented source components that do not by themselves admit a route. Blue cells denote explicit synthetic engineering specification, not empirical or numerical validation. Route 3 was activated at S1 precisely because both source-aligned routes failed their frozen admission requirements; its later numerical termination is shown separately in Fig. 3. The matrix does not make a global legal, novelty, or model-quality judgment about COMSOL, PCMO, or PINNs.

## Figure 3 — S2 qualification ladder and termination

**Files:** `figure-03-s2-ladder.png`, `figure-03-s2-ladder.pdf`

**Caption.** Frozen 13-intent S2 qualification ladder and the observed hard-stop location. Intent 1 (`Q0`, coarse/coarse, full coupling) completed and verified only the zero-drive guard and artifact chain. Intent 2 was the first driven case (`QN`, coarse/fine, full coupling) and terminated with `RuntimeError: transport Newton exceeded its frozen iteration limit` before case, evaluation, or report fields were produced. Under the pre-registered no-rescue rule, intents 3–13 were not started; consequently no cross-resolution convergence, driven event, floor seal, bracket, replay, or thermal-effect evidence exists.

## Figure 4 — Q0 zero-drive guard traces

**Files:** `figure-04-q0-guard.png`, `figure-04-q0-guard.pdf`

**Caption.** Actual H5 traces and frozen report summary for Q0 intent 1. Across 400 timesteps over 2 s, applied voltage and both terminal currents remained zero, the defect fraction remained exactly 0.5, relative active-mass drift was zero, and temperature differed from 300 K only at floating-point scale. The report records zero mass, no-flux, heat-balance, and terminal-current mismatch residuals with all Q0 hard guards passed. Event evaluation is contractually not applicable to the zero-drive case. These data verify zero-drive conservation and persistence only; they are not driven-event, convergence, or oracle-qualification evidence.

## Figure 5 — Non-scientific Newton diagnostic

**Files:** `figure-05-newton-diagnostic.png`, `figure-05-newton-diagnostic.pdf`

**Caption.** **NON-SCIENTIFIC DIAGNOSTIC:** deterministic iteration-budget incompatibility in the explicit 12-cell, one-step QN fixture, not the production mesh and not oracle evidence. The blue residual trace is recomputed from the current core’s private residual, Jacobian, and line-search seams after the unmodified Newton method is first required to reproduce the exact frozen terminal exception. All 20 accepted steps are 0.5; the scaled residual falls from approximately `1.5106745e-3` to `1.4406929e-9`, remaining above the frozen `1e-10` tolerance. An ideal half-step model requires 24 iterations, four more than the frozen maximum. The dashed curve is that analytic reference, not a substituted measurement. The Jacobian directional-error value and the latent outer-block admissibility bound in panel c are bounded diagnostic facts from the S2 terminal closeout; the latter is not an observed production outer-block failure.

## Figure 6 — Claim boundary and compute accounting

**Files:** `figure-06-claim-boundary.png`, `figure-06-claim-boundary.pdf`

**Caption.** Evidence ceiling and gross compute accounting at the frozen S2 stop. The bounded S1 review supports route-specific source dispositions, Q0 supports only zero-drive guards, and QN supports only the fact of execution failure under the frozen Newton limit. Convergence, event, thermal-floor, PINN, development, OOD, formal, reserve, and experimental layers were not reached. Two of the 40 CPU solver intents were consumed (one completed Q0 guard and one failed driven intent), totaling `0.002326388888888889 CPU_PROCESS_CORE_HOURS` for the two production solver intents; case-freeze administration is excluded. Q0 used 400 timesteps and 1202 linear solves. No neural forward/automatic-differentiation work, GPU allocation, rescue attempt, or post-failure production rerun is represented. Unused budget is not evidence.

## Reproduction and source map

From the repository root, the locally verified command is:

```powershell
python paper\figures\generate_figures.py
```

The script requires NumPy, h5py, and Matplotlib, verifies frozen carrier hashes before rendering, re-extracts the Q0 traces from the H5 file, and fails closed if the non-scientific Newton fixture no longer terminates with the frozen exception or diagnostic fingerprint. It does not invoke a production solver run or write to the research ledger. Exact input, source-data, PNG, and PDF hashes plus the render-library versions are recorded in `source-manifest.json`; plot-ready CSV files are under `data/`.
