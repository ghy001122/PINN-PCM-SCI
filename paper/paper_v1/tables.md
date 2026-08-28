# Main Tables

Only observed values are tabulated. Unexecuted ladder rows are omitted; no empty result row is used. Detailed contracts and `NOT_REACHED` gates are reported in the [Supplementary Information](supplement.md).

## Table 1. Recorded S2 execution accounting

| Run identity | Evidence role | Execution status | Solver intents | Failed intents | Wall time (s) | Process CPU (s) | CPU process core-hours |
|---|---|---|---:|---:|---:|---:|---:|
| `20260826T113537Z-goal-paper-one-shot-v1-s2-freeze-002` | Effective Q-case freeze | COMPLETED | 0 | 0 | `0.028080299962311983` | `0.03125` | `8.680555555555556e-6` |
| `20260826T113638Z-goal-paper-one-shot-v1-s2-intent-01-q0` | Q0 zero-drive, coarse/coarse | COMPLETED | 1 | 0 | `8.38404590007849` | `8.28125` | `0.0023003472222222223` |
| `20260826T113752Z-goal-paper-one-shot-v1-s2-intent-02-qn-coarse-fine` | First driven QN, coarse/fine | FAILED | 1 | 1 | `0.0984956999309361` | `0.09375` | `2.604166666666667e-5` |

The failed QN intent counts against the frozen budget and had zero rescue attempts. Q0 plus QN consumed `2` solver intents and `0.002326388888888889` CPU process core-hours. All runs were local float64 CPU executions with one declared CPU thread; peak RAM was not recorded and no GPU/VRAM compute was used.

## Table 2. Q0 zero-drive guard result

| Observable | Recorded value |
|---|---:|
| Timesteps | `400` |
| Total / maximum block iterations | `400 / 1` |
| Electrical linear solves | `801` |
| Thermal linear solves | `401` |
| Transport linear solves | `0` |
| Accepted-state consistency evaluations | `400` |
| Final transport scaled residual maximum | `0.0` |
| Defect fraction minimum / maximum | `0.5 / 0.5` |
| Temperature minimum / maximum | `299.9999999999985 / 300.00000000000034 K` |
| Relative mass drift maximum | `0.0` |
| No-flux residual maximum | `0.0` |
| Relative heat-balance residual maximum | `0.0` |
| Relative terminal-current mismatch maximum | `0.0` |
| Event applicable | `false` |
| Hard-guard outcome | `PASS` |

This table supports only zero-drive conservation and artifact-path verification. The manifest retains `PENDING_S2_CROSS_RUN_ADJUDICATION`; it is not an oracle or event PASS.

## Table 3. First driven QN execution failure

| Recorded field | Value |
|---|---|
| Intent | `2` |
| Case / resolution / control | `QN / coarse-fine / FULL` |
| Failure class | `RuntimeError` |
| Failure message | `transport Newton exceeded its frozen iteration limit` |
| Numerical validity | `NOT_EVALUATED` |
| Gate outcome | `SYN_EDT_S2_EXECUTION_FAILED` |
| Route disposition | `SYN_EDT_S2_EXECUTION_INVALID_STOP` |
| Failed intent consumed | `true` |
| Rescue attempts | `0` |
| Published case/evaluation/report artifacts | `0` |

The empty artifact count is observed: failure preceded case, evaluation, and report publication. It does not imply a physical zero or a qualified negative oracle result.

## Table 4. Reduced-fixture solver diagnostic

| Diagnostic quantity | Observed value |
|---|---:|
| Identity | `NON_SCIENTIFIC_DIAGNOSTIC` |
| Active cells | `12` |
| Fixture duration / endpoint voltage | `0.00125 s / 0.01125 V` |
| Initial scaled residual | `1.5106745331996967e-3` |
| Accepted inner steps | `20 × 0.5` |
| Residual after 20 steps | `1.4406930175716191e-9` |
| Measured residual ratio | `9.536753191437917e-7` |
| Ideal half-step ratio, $2^{-20}$ | `9.5367431640625e-7` |
| Largest initial residual compatible with `1e-10` after 20 ideal half steps | `1.048576e-4` |
| Centered-FD analytic-Jacobian relative infinity-norm discrepancy | `1.7339861280712171e-10` |
| Outer ideal half-decay after 12 steps, $2^{-12}$ | `2.44140625e-4` |
| Largest initial normalized mismatch compatible with `1e-8` after 12 ideal half steps | `4.096e-5` |

Table 4 diagnoses the frozen nonlinear-control combination on a reduced fixture. It must not be cited as a production device, oracle, event, PINN, or method result.

## Table 5. Evidence-qualified terminal outcomes

| Layer | Outcome | Evidence status |
|---|---|---|
| Source Route 1 | Required legal-research-use PASS not established; independent source-contract failure | Bounded verified review decision |
| Source Route 2 | Required 2D conservative source contract not closed | Bounded verified review decision |
| Synthetic Q0 | Zero-drive guard completed | VERIFIED, Q0 only |
| Synthetic driven QN | Frozen execution failed at inner Newton limit | VERIFIED execution failure |
| Synthetic S2 | `SYN_EDT_2D_V1_NUMERICAL_CONTRACT_NO_GO` | Bounded terminal disposition |
| Oracle/event/PINN/formal | No evidence produced | VERIFIED non-attainment |

Table 5 is categorical and contains no inferred method result. Claim-level evidence and prohibited extrapolations are given in the [claim–evidence matrix](claim_evidence_matrix.md).
