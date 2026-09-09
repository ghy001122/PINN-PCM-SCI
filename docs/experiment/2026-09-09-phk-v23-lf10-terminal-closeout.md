# PHK-V2.3 LF10 feasible-direction and headline-replication terminal closeout

- `phase_id`: `PHK_V23_LF10_EVENT_COMPETENCE_FEASIBLE_DIRECTION_AND_HEADLINE_EVIDENCE_REPLICATION_EXECUTE`
- `lifecycle_state`: `COMPLETE`
- `CPU_outcome`: `LF10_CPU_QUALIFICATION_PASS`
- `machine_outcome`: `LF10_FEASIBLE_DIRECTION_SCREEN_NEGATIVE_PAPER_STRENGTHENED`
- `mechanism_outcome`: `NO_EXTENDED_FEASIBLE_PATH_FOUND`
- `interface_replication_outcome`: `INTERFACE_EFFECT_STREAM_REPLICATED`
- `forgetting_replication_outcome`: `PHYSICS_FORGETTING_STREAM_REPLICATED`
- `candidate`: `none`
- `next_research_execution_authorized`: `false`
- `unique_next`: `FINALIZE_REPLICATED_INTERFACE_AND_FORGETTING_PAPER_NO_MORE_REFINEMENT_RESCUE`
- `stress_reference_status`: `TWO_STRESS_REFERENCES_SEALED_UNREAD`

## Direction-screen decision

Both mandatory matched screens were numerically and identity valid and retained
one recoverable safe prefix. Neither completed the 200 accepted updates required
for screen GO.

| metric | exact DEV-R | CTRL | PROJ |
|---|---:|---:|---:|
| accepted / attempted updates | `0 / 0` | `25 / 150` | `25 / 147` |
| accepted blocks | `0` | `1` | `1` |
| fixed-blind `J` | `4.9278722` | `4.8743140` | `4.8743140` |
| `J/J0` | `1.0` | `0.9891316` | `0.9891316` |
| final learning rate | n/a | `7.8125e-6` | `7.8125e-6` |
| last rejection | n/a | temperature preservation | projection infeasible under norm cap |

Both prefixes preserved the medium safety conjunction: two-cycle recall was
`0.917526/0.922868`, precision `0.896725/0.920362`, mass
`1.02320/1.00272`, and recovery `1/1`. Cycle-1 timing remained
`0.0105333`, so neither was a strict carrier. The result is not "no safe path";
it is `NO_EXTENDED_FEASIBLE_PATH_FOUND`, and the projected direction did not
extend the locally safe CTRL path. Full refinement and the conditional control
were `NOT_RUN_PREREQUISITE_NOT_MET`, not failed.

## Replicated headline evidence

The interface-band paired effect had `delta_Rmin` values
`0.089837/0.046278/0.025243` for streams 17/23/29. All three were positive;
the median exceeded `0.03`, and quality preservation held in two streams, so
`INTERFACE_EFFECT_STREAM_REPLICATED` passed.

Pure strong-physics forgetting produced fixed-blind `J/J0` values
`0.012814/0.005122/0.716689` for streams 17/23/29. Two streams crossed the
predeclared `0.50` physics threshold, while all three lost an event or had
minimum recall at most `0.50`, with no field-event Pareto. Therefore
`PHYSICS_FORGETTING_STREAM_REPLICATED` passed. The replication medium audit was
report-only and did not affect training, selection, stopping or checkpointing.

## Threshold and strong-baseline boundary

The 5x5 threshold grid did not alter any formal machine outcome. The new
interface and forgetting replications retained their directional result in all
25 evaluated grid cells per stream. Direct `LF_ONLY` led the
mean-symmetric-difference predicate in all 375 available role-grid comparisons;
this is not an all-metric claim. Historical LF4 threshold rows were explicitly
skipped because their predictions were unavailable; this does not alter the
new paired-stream result.

`VERIFIED`: identity-valid CTRL/PROJ screens, two retained 25-update safety
prefixes, both replication outcomes, threshold sensitivity, artifact recovery
and shutdown. `SUPPORTED_INTERPRETATION`: interface exposure is a reproducible
carrier-support mechanism on this nominal object, while strong-physics descent
reproducibly forgets the event carrier and the tested feasible projection does
not rescue long-path refinement. `UNKNOWN`: sparse, multiple independent model
seeds, formal OOD/stress and experimental behavior.

## Executed identity, recovery and shutdown

- activation: `f5e05f4dec416df2a3598e433d4edcb9f7ba299c`
- executed source: `LF10-BUNDLE-A0A6E9DB39FD33649E8B8E968A2713F90CDBB982E0B3E39D5CCBF7E6967702B2`
- source archive SHA-256: `EFF772B7FC6DAF63E38C28B133D434BBDD2EF9EEF6590BE00C78E4D1C3E43192`
- deployed manifest SHA-256: `60E65F20B35EC95C9DA60E9C7B899CC60E07F19C9C15A7DE755DD78603996296`
- run summary SHA-256: `987A264B2235CA9461717DA37D59C69AD2ED02160C135A8A8BA1809AD4E6830F`
- recovery manifest SHA-256: `3B1ED6EB5A626B7BF99D215BD450A23222B6710BAA0389C4771B07D1EF9A7645`
- shutdown proof SHA-256: `308760D54EA5231828EC22A6E625FE67F448402E5EB00309854CCB6087A7474B`
- local adjudication SHA-256: `F322212DF49E0F25BE9B06B360A08CDDA95EDB92A30BCC475777A978B82AC27D`

All 44 recovered files matched remote/local size and SHA; all 43 declared run
artifacts matched. Training and GPU process counts were zero before shutdown.
TCP was closed and SSH returned explicit `Connection refused` before local
adjudication. Fine/extra/direct/evaluator data were local-only after shutdown;
stress stayed sealed/unread.

## Paper package

`paper/paper_v23` is closed for LF10 as
`TERMINAL_REPLICATED_FAILURE_ANALYSIS_PACKAGE_COMPLETE`. The manuscript is
bound by SHA-256
`49B1D8B2EC4C23A4902D116D71BA16D1C2ED737BAA512AE2ED46E2C2A58EA6D1`;
the terminal metrics and figure source manifest are bound by
`B8CA792AB51F8CC1255C6D820A31BBDB9080F085A39D5FC5E2529C03443FF6E0`
and `3FED11474D888659D85FFD05F53DD32F7852D0A9B367A56D4D41332340FB1D8C`.
The package presents replicated failure analysis and bounded solver recovery,
not a positive PINN refinement or direct-baseline gain.

See the [terminal artifact](artifacts/20260909T101615Z-phk-v23-lf10-terminal.json),
[terminal manifest](manifests/20260909T101615Z-phk-v23-lf10-terminal.json), and
[ADR 0074](../adr/0074-close-phk-v23-lf10-feasible-direction-replication.md).
