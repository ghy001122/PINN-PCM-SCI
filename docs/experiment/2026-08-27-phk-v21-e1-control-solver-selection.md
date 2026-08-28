# PHK-V2.1 E1 control-solver engineering selection

- `date`: `2026-08-27`
- `stage`: `E1_CONTROL_SOLVER_DIAGNOSIS_AND_FIXED_SCHEME_SELECTION`
- `record_status`: `COMPLETED_NON_VOTING_ENGINEERING_SELECTION`
- `evidence_identity`: `NON_VOTING_ENGINEERING_ONLY`
- `scientific_claim_status`: `NO_OBJECT_ORACLE_EVENT_PINN_METHOD_OR_FORMAL_EVIDENCE`
- `preserves`: `PHK_V2_ORACLE_NO_GO_AND_FAILED_INTENT_09_BYTE_FOR_BYTE`

## Result

`VERIFIED`: the historical intent-9 phase failure was reduced to the frozen 2×2 snapshot in `engineering_contract.json`. The analytic Jacobian matched a centered directional finite difference to relative L2 error `6.698358367618657e-10`; its dense 2-norm condition number was `1.1014977808058877`. The actual root lies inside the physical interval `[0,1]` but outside the old artificial upper guard `0.99999999`: its maximum phase fraction is `0.9999999911341139`. The proximate failure is therefore bound exclusion, not a detected Jacobian sign error or an ill-conditioned 2×2 linearization.

Trust-region reflective, logit analytic Newton, and pseudo-transient Newton all solved the fixed snapshot without output clipping and with residual at or below `1e-10`. On the same coarse full-duration conductivity-off screen, logit used `3155` phase linear solves, compared with `3550` for pseudo-transient and `8724` for trust-region. The logit scheme was therefore promoted.

The promoted logit scheme then completed the old medium conductivity-off trajectory twice. Every stored state and diagnostic array was bitwise identical across the two executions. Both nominal and Joule-off coarse sentinels completed with all numerical guards passing. No dynamic solver switching, time-step rescue, equation change, or output clipping was used.

~~~text
PHK_V21_E1_SELECTION=LOGIT_NEWTON_ANALYTIC_JACOBIAN
PHK_V21_E1_VERDICT=PASS_FOR_NON_VOTING_ENGINEERING_OBJECT_SEARCH
PHK_V21_SCIENTIFIC_EVIDENCE=NONE
~~~

## Candidate disposition

| Candidate | Snapshot | Coarse conductivity-off | Disposition |
|---|---:|---:|---|
| Legacy damped Newton | expected line-search failure | historical medium failure preserved | ineligible |
| Trust-region reflective | pass | pass; 8724 phase solves | eligible, not selected |
| Logit analytic Newton | pass | pass; 3155 phase solves | selected |
| Pseudo-transient Newton | pass | pass; 3550 phase solves | eligible, not selected |
| Smaller time step | not needed after root cause | not run | diagnostic-only, ineligible |
| Anderson outer coupling | inner failure not addressed by itself | not promoted after fixed logit outer completion | eligible augmentation, not selected |

Anderson acceleration was not added merely to complete the candidate list: the observed failure was at the inner phase-bound seam, and the selected fixed inner scheme already completed the unmodified outer fixed point and exact replay. Adding another outer algorithm would not change the resolved uncertainty or the E1 selection.

## Mandatory selected-scheme checks

| Check | Observation |
|---|---|
| Minimized red fixture | pass; residual `3.021812361644421e-11` |
| Physical phase range | pass; no clipping |
| Directional Jacobian check | pass; `6.698358367618657e-10` |
| Full-duration conductivity-off | medium completed twice |
| Nominal/Joule-off sentinels | both completed; hard guards pass |
| Deterministic replay | all twelve stored array differences exactly `0.0` |

The old object's event report still fails recovery, second-cycle event, and cycle-drift requirements. That is expected and is not reinterpreted as a new object result. E1 authorizes only the preregistered E2 non-voting object search.

## Identity carriers

- Machine selection: [`e1_solver_selection.json`](../../configs/phk_v21/e1_solver_selection.json)
- Engineering contract: [`engineering_contract.json`](../../configs/phk_v21/engineering_contract.json)
- New solver implementation: [`phk_v21_solver.py`](../../pinn_pcm_sci/phk_v21_solver.py)
- Engineering harness: [`phk_v21_engineering.py`](../../pinn_pcm_sci/phk_v21_engineering.py)
- Historical PHK-V2 implementation SHA256 remains `B18AFA4F9005735EF46E3958F325C5BC40CECD0BF5E419854B140FAF76DF9645`.

Raw in-memory diagnostic arrays are non-voting and are not promoted to oracle artifacts. The exact snapshot, contract, implementation, tests, counts, and replay differences are sufficient to reproduce or challenge the engineering selection.
