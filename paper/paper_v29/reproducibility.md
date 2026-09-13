# Reproduction of the completed fixed-parent experiment

Work root: `E:\Python demo\PINN-PCM-SCI`. Inherited release: `4bd28c126911ae521b0949b5bd59aa56d01388cd`. Actual deployed source identities are retained in [the source manifest](evidence/deployed-source-manifest.json). Core scientific sources and configuration did not change during training. The user subsequently authorized publication; the release identity is the Git commit containing this package. Historical runtime publication flags remain unchanged, as explained in the [evidence guide](evidence/README.md).

## Cheapest reproduction: existing evidence to figures and tables

```powershell
.\.venv\Scripts\python.exe -m pinn_pcm_sci.phk_v23_lf11_remaining_pde_report --root paper/paper_v29/evidence
```

This reads saved JSON and plotting arrays only, writes four PNG/PDF pairs and complete numerical tables, and preserves the authored manuscript. It does not train, solve or open the full nominal reference.

## Inputs and exact objective

The role-selected parent is V28 `D_E/checkpoint.pt`. Its T/phase heads and T adapter are retained; the V head stays inactive. Curvature histories are not inherited. The same sparse labels, 80x40 electric grid, half-resistance deposition, complete first-order implicit VJP, thermal cell balance and phase AD equation are used. No new full thermal/phase trajectory is solved. Original observation and boundary measures, denominators3/13, PDE scales4/5, aE/bE and all calibration/L-BFGS/audit pools remain fixed. Lambda is0.1, with no ramp.

C is the original weighted observation plus BC/IC package. F is0.1 J_Tphi/bE. D_C optimizes C; P1 optimizes C+F; P_kappa optimizes C+kappa F. The reference-blind rule on D_E's calibration pool gives kappa=92.8404908293. Eight complete weighted component-gradient scans cover E0/D_E and T-with-adapter/phase head summaries. They are first-order diagnostics, not Hessians, Adam-state attribution or finite trajectory interventions.

The execution prompt allowed at most300 complete evaluations per arm while retaining at most30000 forward and30000 adjoint training solves. One time-count check gives34/50/50 nonzero solves per D_C/P1/P_kappa evaluation. Therefore all three caps were frozen at223, for at most29882 forward and29882 adjoint solves. The report's26800 estimate was based on its earlier200-evaluation suggestion. No arm received spare evaluations after another stopped, and no Adam or extra continuation was run.

Each arm uses fresh PyTorch2.5.1 strong-Wolfe L-BFGS: lr1, max_iter1, history50, tolerance_grad1e-10, tolerance_change1e-14. Every initial, repeated and trial closure counts. Complete observations and the original fixed pool are used without resampling, changing weights or clipping gradients. An interrupted line search restores model and optimizer to the last accepted state. Checkpoints contain both states and the exact termination reason.

The inherited `updates` and `statistics.objectives.optimizer_updates` fields count Adam updates and therefore remain zero in these raw checkpoints. Actual optimization is recorded by `lbfgs_result.accepted_steps` and each terminal's `lbfgs` object: 107/108/108 accepted steps for D_C/P1/P_kappa. A zero legacy counter must not be interpreted as zero training. Raw scientific payloads are preserved rather than rewritten to change this schema.

## Actual environment, counts and lifecycle

Python3.11.9, PyTorch2.5.1+cu118, NumPy2.1.1 and SciPy1.14.1 were read from the actual V100 instance. FP64 neural operations use GPU; sparse CPU SuperLU retains the complete electrical adjoint. Two focused local checks address only new objective/gradient composition and the additional historical-control adjudication, without repeating V28 interface tests.

Actual new counts: 669 full evaluations, 323 accepted steps, zero Adam, 29882 forward and 29882 adjoint training solves. Diagnosis plus common-pool audits: 550 forward, 100 adjoint, eight component-gradient scans. The three fine-grid own predictions use834 forward solves, no adjoints; zero drive is skipped analytically. See [execution table](tables/execution-counts.md). Equal evaluations are not equal compute; no acceleration claim is made.

The job ran in its own selected-source directory. A local SSH dispatch connection remained open after successful background launch; only that local connection was released, and an independent recovery/shutdown supervisor was started. The remote scientific process was not interrupted or restarted. The [current receipt](evidence/compute-closure.json) records verified artifact recovery, authenticated shutdown and subsequent connection refusal. Full-reference scoring happened locally afterwards; no old shutdown receipt was reused.

`reference_read: false` in that receipt describes the recovery/shutdown instant. The later evaluation timestamp and terminal summary record the subsequent authorized local reference read; these are successive lifecycle records, not contradictory access claims.

## Interfaces for a separately authorized reproduction

Use an empty run directory and a new lifecycle receipt. These recorded interfaces do not authorize rerunning this completed campaign:

```powershell
.\.venv\Scripts\python.exe -m pinn_pcm_sci.phk_v23_lf11_remaining_pde all --root outputs/runs/NEW_AUTHORIZED_RUN --device cuda:0
# After that run's actual recovery and confirmed shutdown:
.\.venv\Scripts\python.exe -m pinn_pcm_sci.phk_v23_lf11_remaining_pde_evaluate --root outputs/runs/NEW_AUTHORIZED_RUN
```

Full scoring needs local reference and own-field arrays absent from the compact package. Old role metrics are explicitly reused. The formal A/B definitions, near-zero tolerances and strict event requirements are inherited unchanged. P_F is not automatically executed by any positive decision in this sprint. All observations belong to exposed nominal development, and no OOD or oxide calibration is claimed.
