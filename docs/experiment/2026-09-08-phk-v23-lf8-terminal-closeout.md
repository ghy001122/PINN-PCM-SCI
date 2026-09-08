# PHK-V2.3 LF8 competence-filter completion terminal closeout

- `phase_id`: `PHK_V23_LF8_IDENTITY_CORRECT_COMPETENCE_FILTER_COMPLETION_AND_SCHEDULE_ATTRIBUTION_EXECUTE`
- `lifecycle_state`: `COMPLETE`
- `CPU_outcome`: `LF8_CPU_QUALIFICATION_PASS`
- `machine_outcome`: `LF8_FILTER_STALLED_WITH_VALID_PREFIX`
- `mechanism_outcome`: `MATCHED_ATTRIBUTION_UNAVAILABLE`
- `scientific_gpu_trajectories`: `1`
- `optimizer_updates`: `150 attempted; 25 accepted`
- `valid_prefix_updates`: `25`
- `conditional_control`: `NOT_RUN_PREREQUISITE_NOT_MET`
- `candidate`: `none`
- `next_research_execution_authorized`: `false`
- `unique_next`: `MIXED_WEAK_CONTROL_VOLUME_PLAN_REQUIRES_NEW_EXECUTE_VALID_PREFIX_RETAINED`
- `stress_reference_status`: `TWO_STRESS_REFERENCES_SEALED_UNREAD`

## Terminal decision

Mandatory P0-F* produced an identity-valid 25-update safety prefix and then
stalled at the smallest preregistered learning rate. It attempted six blocks:

| block | learning rate | decision | decisive failed gate | accepted total |
|---:|---:|---|---|---:|
| 1 | `1.25e-4` | reject/rollback | potential, temperature | 0 |
| 1 | `6.25e-5` | reject/rollback | potential, temperature | 0 |
| 1 | `3.125e-5` | reject/rollback | temperature | 0 |
| 1 | `1.5625e-5` | reject/rollback | temperature | 0 |
| 1 | `7.8125e-6` | accept | none | 25 |
| 2 | `7.8125e-6` | reject/rollback | temperature | 25 |

Every rejected block restored model, nonempty Adam state, RNG, stage and
accepted-step identity. No sixth rate, smaller block or scientific retry was
used. Because P0-F* did not reach 1,200 accepted updates, the conditional
accepted-schedule control was not triggered; it is `NOT_RUN`, not failed.

## Valid-prefix result

The accepted prefix retained all reference-blind safety gates and reduced the
fixed-blind objective by about 1.09%:

| metric | exact DEV-R | LF8 valid prefix | disposition |
|---|---:|---:|---|
| fixed-blind `J` | 4.9278721847 | 4.8743140406 | strict local decrease |
| fixed-blind `J/J0` | 1.0 | 0.9891315882 | far above complete-path `0.50` gate |
| potential weighted MSE | 7.14768e-5 | 7.10952e-5 | preserved |
| temperature weighted MSE | 7.11189e-4 | 7.24336e-4 | preserved |
| phase weighted MSE | 0.0011832624 | 0.0011832624 | unchanged |
| topology weighted loss | 0.0046144880 | 0.0046144880 | unchanged |

Phase was frozen throughout the retained prefix. It preserved two-cycle events,
potential/range validity, recall `0.917526/0.922868`, precision
`0.896725/0.920362`, active-mass ratios `1.02320/1.00272` and recovery `1/1`.
Cycle-1 timing remained `0.0105333`, so the prefix passed the safety gate but
not the strict carrier gate. This valid prefix proves that the corrected filter
can admit one locally safe strong-form descent block. Its failure to admit a
second block at the minimum frozen rate closes the tested long-path strong-form
route.

## Post-shutdown nominal adjudication

Fine, extra-fine, direct `LF_ONLY` and the frozen evaluator were read locally
only after verified recovery and shutdown. The LF8 prefix and DEV-R have the
same phase metrics because phase remained frozen; LF8 made only small V/T
changes.

| local frozen metric | DEV-R | LF8 valid prefix | direct `LF_ONLY` |
|---|---:|---:|---:|
| phase primary | 0.00160984 | 0.00160984 | 0.000349531 |
| phase ROI RMS | 0.0323683 | 0.0323683 | 0.00657038 |
| temperature ROI RMS | 0.0173618 | 0.0175681 | 0.00180069 |
| current NRMSE | 0.137297 | 0.137093 | 0.00352214 |
| event guard | PASS | PASS | PASS |

The prefix is noninferior to DEV-R by the frozen component-floor rule and
preserves T/current, but it is not a complete path and remains substantially
behind direct `LF_ONLY` in phase, temperature and current. Levels 2 and 3 are
therefore false; candidate remains none.

## Scientific interpretation

This is a substantive bounded negative result rather than another identity
failure. LF7's rollback defect is closed, the filter was exercised on a valid
nonempty-Adam trajectory, and a recoverable endpoint exists. The block history
shows that smaller strong-form steps progressively improve field preservation,
but temperature leaves the frozen envelope again on the very next block even at
the minimum rate. The evidence therefore supports a local feasible prefix and
a strong-form path stall; it does not isolate filtering from schedule because
the matched control prerequisite was not reached.

The frozen stop rule closes further strong-form learning-rate, block-size,
optimizer, replay, weighting, sampling and network rescue. The sole technical
recommendation is a separately authorized mixed weak/control-volume physics
objective that directly changes the failed continuation functional while
retaining DEV-R and the LF8 prefix as strong comparators.

## Executed source, recovery and shutdown

- starting HEAD: `95e448e36a659ac266b670667543b80ce467da53`
- activation HEAD: `70b4d30bc36cff0c745cc1eb0fc67f9081cd94f0`
- executed source: `LF8-BUNDLE-F9B2A84E8B3953D6BC5DC8F1D402D87EA6C060361FC9323785DF5CB46351E288`
- source archive SHA-256: `076131769CBE74AA35395D211F91742329D9054AD89FA9546769C98830688A37`
- deployed manifest SHA-256: `0F77AAD81CD41FA49BBEC55B79647C08219C4BB38F893E51595D9BBEDDF7DBFA`
- result archive SHA-256: `6FCC6EFBBE96422B09D9B716BF9988A961B7AD6C63A8430F0D13EDEE262FBE21`

All nine configured cloud artifacts matched remote/local size and SHA. Training
and GPU processes and GPU memory were zero before shutdown. TCP was closed and
SSH returned `Connection refused` at `2026-09-08T06:03:38Z`; local nominal
adjudication followed. The cloud read no fine/extra/direct-`LF_ONLY`/frozen
evaluator/stress data, and medium supplied no training gradient.

See the [terminal artifact](artifacts/20260908T050343Z-phk-v23-lf8-terminal.json),
[terminal manifest](manifests/20260908T050343Z-phk-v23-lf8-terminal.json), and
[ADR 0070](../adr/0070-close-phk-v23-lf8-competence-filter-completion.md).
