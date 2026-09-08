# PHK-V2.3 LF9 equation-routed thermal-CV terminal closeout

- `phase_id`: `PHK_V23_LF9_EQUATION_ROUTED_THERMAL_CONTROL_VOLUME_REFINEMENT_EXECUTE`
- `lifecycle_state`: `COMPLETE`
- `CPU_outcome`: `LF9_CPU_QUALIFICATION_PASS`
- `machine_outcome`: `LF9_NO_SAFE_MIXED_FORM_SCREEN`
- `mechanism_outcome`: `NO_SAFE_MIXED_FORM_SCREEN`
- `scientific_gpu_trajectories`: `2 matched screens`
- `optimizer_updates`: `300 attempted; 50 accepted total`
- `ER_S`: `150 attempted; 25 accepted; valid prefix; screen fail`
- `ER_CV`: `150 attempted; 25 accepted; valid prefix; screen fail`
- `filtered_full_path`: `NOT_RUN_PREREQUISITE_NOT_MET`
- `accepted_schedule_control`: `NOT_RUN_PREREQUISITE_NOT_MET`
- `candidate`: `none`
- `next_research_execution_authorized`: `false`
- `unique_next`: `FINALIZE_NEGATIVE_SOLVER_DIAGNOSTIC_NO_MORE_RESCUE`
- `stress_reference_status`: `TWO_STRESS_REFERENCES_SEALED_UNREAD`

## Terminal decision

Both mandatory, identity-valid screens followed the same six-attempt pattern:
four higher-rate first blocks were rejected, the first block at `7.8125e-6`
was accepted, and the second block at that minimum frozen rate was rejected for
temperature preservation. Exact rollback retained one recoverable 25-update
safety prefix per arm. Neither arm reached the 200 accepted updates required for
screen selection, so the full filtered path and no-filter control were not run.

| metric | exact DEV-R | ER-S prefix | ER-CV prefix |
|---|---:|---:|---:|
| accepted / attempted updates | 0 / 0 | 25 / 150 | 25 / 150 |
| own blind objective | `4.9278722` | `4.8769838` | `4.8748021` |
| own ratio to DEV-R | `1.0` | `0.9896734` | `0.9897027` |
| strong blind `J_S` | `4.9278722` | `4.8769838` | `4.8769741` |
| mixed blind `J_M` | `4.9255217` | `4.8748116` | `4.8748021` |
| one-cell CV `CV1` | `0.01198043` | `0.01201197` | `0.01201168` |
| 2x2 CV `CV4` | `0.00829140` | `0.00829796` | `0.00829821` |

Both prefixes remained finite, potential/phase valid, and safety-valid. Phase
was unchanged: two-cycle recall was `0.917526/0.922868`, precision
`0.896725/0.920362`, mass ratio `1.02320/1.00272`, and recovery `1/1`.
Cycle-1 timing remained `0.0105333`, so neither endpoint was a strict carrier.

## Scientific interpretation

`VERIFIED`: under the equation-routed implementation, both arms admitted one
safe 25-step block without immediate catastrophic drift. However, replacing the
thermal strong residual with the normalized control-volume residual did not
extend the accepted path: ER-CV and ER-S stalled at the same point, for the same
temperature-preservation failure, with nearly identical field and blind metrics.

`SUPPORTED_INTERPRETATION`: the remaining obstruction is not resolved by the
tested local thermal-functional replacement. The evidence closes this bounded
mixed-form rescue family; it does not prove that all weak formulations or all
PINNs must fail.

`UNKNOWN`: multi-seed, sparse-information, OOD/stress and experimental behavior
remain untested. Full-path filtering and filter-versus-schedule attribution also
remain unknown because their frozen prerequisites were not reached.

## Post-shutdown nominal adjudication

Fine, extra-fine, direct `LF_ONLY`, and the frozen evaluator were read locally
only after verified recovery and shutdown. Both endpoints passed the event
guard but remained far behind direct `LF_ONLY`:

| local frozen metric | DEV-R | ER-S | ER-CV | direct `LF_ONLY` |
|---|---:|---:|---:|---:|
| phase primary | `0.00160984` | `0.00160984` | `0.00160984` | `0.000349531` |
| phase ROI RMS | `0.0323683` | `0.0323683` | `0.0323683` | `0.00657038` |
| temperature ROI RMS | `0.0173618` | `0.0172040` | `0.0172006` | `0.00180069` |
| current NRMSE | `0.137297` | `0.137092` | `0.137092` | `0.00352214` |

Neither `PRELOCAL_INTERNAL_PARETO` nor `COMPLETE_INTERNAL_PINN_PARETO` was
reached. Candidate remains none.

## Executed source, recovery, and shutdown

- starting HEAD: `f16ca9db66843c04d420c077679604dd553ac036`
- activation: `c38fa80d2fa2ceb0b1bd1fa9faf70440f2a07159`
- pre-step runtime fixes: `3ad2dcb302faca00bb60d1cbb1529b11061b6cca`, `bc3950a13935a9ded70d4a8b6cc2862deb4a3fd8`
- executed source: `LF9-BUNDLE-A8A03C2D2A049F2025793B6B9BA8C7C6412EDF594DBF2042BA3C59F1B9CE5D8B`
- source archive SHA-256: `0812EF2B6780AB88D20B23CD8CBF3199779FF02A08FD3DB352857FD2B65847EA`
- deployed manifest SHA-256: `861CE9AAA3EA4601B0EB5517EAB9019184AE1F88804D4CA8D9E177F3159B5D52`

All 15 configured cloud artifacts matched remote/local size and SHA. Training
and GPU process counts and GPU memory were zero before shutdown. TCP was closed
and SSH returned `Connection refused`; local adjudication followed shutdown.
The cloud read no fine/extra/direct-`LF_ONLY`/frozen evaluator/stress data, and
medium supplied no training gradient.

See the [terminal artifact](artifacts/20260908T145333Z-phk-v23-lf9-terminal.json),
[terminal manifest](manifests/20260908T145333Z-phk-v23-lf9-terminal.json), and
[ADR 0072](../adr/0072-close-phk-v23-lf9-equation-routed-thermal-cv-refinement.md).
