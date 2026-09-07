# PHK-V2.3 LF7 competence-filtered refinement terminal closeout

- `phase_id`: `PHK_V23_LF7_COMPETENCE_FILTERED_BLOCKWISE_BACKTRACKING_PHYSICS_REFINEMENT_PILOT_EXECUTE`
- `lifecycle_state`: `COMPLETE`
- `CPU_outcome`: `LF7_CPU_QUALIFICATION_PASS`
- `machine_outcome`: `LF7_MATCHED_SCREEN_INCOMPLETE_IDENTITY_INVALID`
- `mechanism_outcome`: `MATCHED_SCREEN_INCOMPLETE_IDENTITY_INVALID`
- `scientific_gpu_trajectories`: `2 attempted`
- `optimizer_updates`: `1350 attempted; 1225 accepted`
- `candidate`: `none`
- `next_research_execution_authorized`: `false`
- `unique_next`: `RETAIN_VALID_ARM_NO_MECHANISM_ATTRIBUTION`
- `stress_reference_status`: `TWO_STRESS_REFERENCES_SEALED_UNREAD`

## Terminal decision

Both preregistered arms were attempted in one activation-bound GPU campaign.
P0-S completed 1,200 updates and is a numerically valid endpoint. P0-F accepted
one 25-update block, attempted 150 updates in total, then failed the post-step
rollback identity check. Under the frozen post-step rule it consumed its arm,
was not retried and has no valid endpoint. The matched screen is therefore
incomplete and cannot establish whether the competence filter is load-bearing.

## Valid P0-S result

P0-S used the exact 1,200-step materialized physics stream and no medium labels
or acceptance audit. The phase was bitwise frozen through step 550 with zero
phase optimizer-state entries. At the final endpoint, values and the
potential/phase range guards remained valid, but event competence collapsed:
cycle 1 had no event; cycle-2 recall was `0.0762250`, event-time error was
`0.1217`, and recovery was `0.0281690`.

| P0-S metric | value | disposition |
|---|---:|---|
| fixed-blind `J/J0` | 0.6030763369 | FAIL (`<=0.50` required) |
| potential MSE / DEV-R | 39.4672 | FAIL |
| temperature MSE / DEV-R | 48.1050 | FAIL |
| phase MSE / DEV-R | 22.4622 | FAIL |
| topology loss / DEV-R | 17.4118 | FAIL |

Thus, an 8-times-smaller fixed learning rate did not produce a local
accuracy-preserving physics path. It reduced the blind objective by about
39.7% while catastrophically losing the carrier, so it is a valid bounded
negative arm and not a PINN Pareto.

## Invalid P0-F endpoint and forensic finding

P0-F reused the same start, batches, optimizer family and initial learning rate,
with medium used only for accept/reject. It accepted its first block and then
raised `LF7 block rollback state identity drift`. No checkpoint or prediction
endpoint was written. Post-run forensic review identified aliasing of nonempty
Adam state tensors after `load_state_dict`: the later optimizer step mutated the
saved snapshot itself. The CPU toy began from empty optimizer state, so it did
not exercise this reachable failure.

A minimal deep-copy fix and nonempty-state regression were added only after the
run. They were not deployed or executed scientifically. The executed source is
the activation bundle; the fix is engineering-only and non-voting. No rerun is
authorized, and this arm cannot support a filter-mechanism conclusion.

## Post-shutdown nominal adjudication

Fine, extra-fine, direct `LF_ONLY` and the frozen evaluator were read locally
only after recovery and shutdown. DEV-R passed the event guard; P0-S did not.

| local frozen metric | DEV-R | P0-S | direct `LF_ONLY` |
|---|---:|---:|---:|
| phase primary | 0.00160984 | 0.00986590 | 0.000349531 |
| phase ROI RMS | 0.0323683 | 0.146895 | 0.00657038 |
| temperature ROI RMS | 0.0173618 | 0.145907 | 0.00180069 |
| current NRMSE | 0.137297 | 0.305674 | 0.00352214 |
| event guard | PASS | FAIL | PASS |

P0-S failed local PINN-Pareto and direct-baseline levels. P0-F has no valid
endpoint to adjudicate. Candidate remains none.

## Engineering incidents and executed source

The first cloud launch stopped before preflight because `python` was absent from
PATH. The second reached `REMOTE_LF7_PREFLIGHT_VALID` with no optimizer
constructed and zero updates, then failed on missing `h5py`. An isolated
`/root/autodl-tmp/lf7-venv --system-site-packages` environment with pinned
`h5py 3.12.1` and `scipy 1.14.1` resolved the dependency; no global environment
was modified. The same activation bundle and scientific identity then ran.

- activation HEAD: `1dbee129d8b958accc71b97bf2ade3201587b441`
- executed source: `LF7-BUNDLE-76111FA9EF195AFA28AAE43E68BD80F4471841A4FCACAED8FEDEAF1D078DACF9`
- source archive SHA-256: `5F0CDF5B2A1ABAF96842D6D537CF8C2B0160DE4D6376690D1C69EAEB6C34399F`
- deployed manifest SHA-256: `4C38C715CFB137FAC0C4E29F707085936FC98AAF3BE39BF541E8894EED7C29B9`

## Recovery, shutdown and evidence boundary

All 13 configured cloud artifacts matched remote/local size and SHA. The result
archive is `219740249` bytes with SHA-256
`37C2D51227953A96723809C956E7599CD6E0C69BEEEC47945E34A93009980466`.
Training and GPU processes and GPU memory were zero before shutdown. At
`2026-09-07T16:55:40Z` the endpoint TCP check was false and SSH returned
`Connection refused`; local adjudication followed.

LF7 preserves one valid negative small-step arm and one identity-invalid filtered
arm. It establishes no filter increment, PINN Pareto, strong-baseline gain,
candidate, multi-seed/sparse/OOD/stress result, SOTA or experimental validation.
Stress remained sealed/unread.

See the [terminal artifact](artifacts/20260907T144634Z-phk-v23-lf7-terminal.json),
[terminal manifest](manifests/20260907T144634Z-phk-v23-lf7-terminal.json), and
[ADR 0068](../adr/0068-close-phk-v23-lf7-competence-filtered-refinement.md).
