# N1–N3B terminal closeout, 2026-08-21

## Disposition

- `route_disposition`: `REDUCED_ORACLE_NO_SIGNAL`
- `lifecycle_state`: `BLOCKED`
- `claim_status`: `BOUNDED_NEGATIVE_DEVELOPMENT_RESULT_NO_FORMAL_EVIDENCE`
- `formal_pool_opened`: `false`
- `next_route`: `NO_AUTOMATIC_RETRY_OR_POSITIVE_RESULT_SEARCH`

## Executed evidence

| Gate | Run | Tier / role | Result |
|---|---|---|---|
| N1 engineering smoke | `20260821T062750Z-smoke-n1-strong-raw-001` | smoke / pipeline | One update, checkpoint/prediction/HDF5/independent evaluator/ledger passed. |
| N1 strong-raw screen | `20260821T062846Z-pilot-n1-strong-raw-001` | pilot / bottleneck audit | 4×200 screen plus 800-update extension; `RAW_EVENT_NOT_RESOLVED`. |
| N2 sparse η diagnostic | `20260821T064707Z-pilot-n2-sparse-anchor-001` | pilot / bottleneck audit | 4 snapshots ×82 nodes, 1000 updates; `REPRESENTATION_OR_RESIDUAL_BOTTLENECK`. |
| N3B reduced-oracle smoke | `20260821T070624Z-smoke-n3b-qpop-r3-001` | smoke / oracle qualification | Finite HDF5 artifact and maximum balance violation `6.2717409459e-10`; pass. |
| N3B signal attempt | `20260821T070733Z-pilot-n3b-qpop-r3-signal-001` | pilot / oracle qualification | Interrupted before one case completed because full μ search was repeated inside the Allen–Cahn iteration; retained as engineering failure. |
| N3B corrected signal matrix | `20260821T071847Z-pilot-n3b-qpop-r3-signal-002` | pilot / oracle qualification | Supersedes the interrupted attempt; 9/9 cases completed; `REDUCED_ORACLE_NO_SIGNAL`. |

## N1 and N2 results

- N1 selected `r1-grouped-joint`. After 1000 updates its oracle-blind checkpoint was step 400 with physics maximum `0.9987712318168883` and device NRMSE `0.9905035489245767`.
- N1 phase-fraction range remained `0.0`; structure symmetric difference remained `0.2290643041395406`. The raw event competence gate therefore failed.
- N2 used the nearest oracle snapshots to 130, 260, 390 and 494 ns and 82 nodes selected only by seed 17. It used η labels only, weight 1.0, with no tuning.
- N2 selected step 400 with anchor loss `0.09954509909257313` and physics maximum `1.0560337616228381`. Its phase-fraction range remained `0.0` and structure error remained `0.2290643041395406`.
- N2 therefore identifies a bounded representation-or-residual bottleneck. It is solver-assisted diagnostic evidence only and is not a formal method comparison.

## QPOP-R3-v1 result

- The independent SciPy finite-volume/implicit solver retained Q-POP bulk Landau coefficients, algebraic stable μ closure, intrinsic Fermi carrier mapping, anisotropic conductivity, circuit-coupled quasi-static conduction, Joule heating, thermal diffusion/loss, and structural Allen–Cahn dynamics.
- It explicitly removed transient carriers, Poisson space charge, and independent electronic-order-parameter dynamics. It does not reuse the PINN automatic-differentiation residual implementation.
- The frozen development matrix was voltage `{7.5, 9.0, 10.5} V` × series resistance `{300, 500, 700} kΩ`, using four 60 ns on/60 ns off pulses with 5 ns edges, a 50×20 grid, 1 ns steps, and the unmodified Q-POP heat-transfer coefficient.
- All 9 cases were finite. Their maximum balance violation was `9.87233858118162e-09`; peak temperatures ranged from `343.94644977987355 K` to `363.24323567431986 K`.
- Every case nevertheless had phase-fraction range `0.0` and zero non-degenerate formation–recovery cycles. Signal cases: `0/9`, below the required `3/9`.
- η showed bounded continuous relaxation but never entered the registered transformed phase: the global minimum across all nine artifacts was `0.9821696536`, well above the frozen phase threshold `0.5595005728`.

## Stop and claim boundary

- The predeclared N3B stop condition is met. No mesh/time/tolerance qualification, N4 KC pilot, formal freeze, formal run, GPU run, or positive result search is authorized or scientifically meaningful on this route.
- This is not experimental validation, not a SOTA result, and not evidence that structural clocks fail in general.
- The supported conclusion is narrower: under the frozen seven-unknown PINN implementation and then the frozen QPOP-R3-v1 reduced-oracle screen, the project did not establish a structurally dynamic, numerically qualified substrate on which KC could receive a fair confirmatory test.
- Q-POP and QPOP-R3-v1 are synthetic numerical sources, not experimental truth.

## Integrity

- Original failure manifests and artifacts remain immutable.
- The corrected signal run uses `supersedes=20260821T070733Z-pilot-n3b-qpop-r3-signal-001`; it is not mislabeled as an exact replay because the operator-splitting implementation changed.
- `ExperimentLedger.validate()` passed after all runs.
- Full local regression: 139 tests passed on 2026-08-21.
