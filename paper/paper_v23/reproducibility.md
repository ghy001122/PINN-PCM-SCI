# Reproducibility and evidence map

## Scope

This guide maps the LF3 baseline, LF4 matched mechanism screen, and LF5
zero-update temporal-edge premise test, figure extraction, and local terminal adjudication. It does not authorize another scientific GPU run,
opening stress references, or changing frozen contracts.

## Frozen identities

- starting commit: `6ec084cbffcbbd754da3aaff191ffb1862a20b0e`;
- activation commit: `97a5b74cf79332115397d07c83b400c942859fb4`;
- contracts:
  - `configs/phk_v23/program_contract_lf3_phase_latent_carrier.json`;
  - `configs/phk_v23/method_contract_lf3_phase_latent_carrier.json`;
  - `configs/phk_v23/data_contract_lf3_phase_latent_carrier.json`;
  - `configs/phk_v23/decision_contract_lf3_phase_latent_carrier.json`;
- runner: `pinn_pcm_sci/phk_v23_lf3.py`;
- qualification: `pinn_pcm_sci/phk_v23_lf3_qualification.py`;
- local adjudicator: `pinn_pcm_sci/phk_v23_lf3_evaluation.py`.

## CPU qualification

The raw qualification record is

```text
outputs/runs/20260904T150300Z-phk-v23-lf3-cpu-qualification-6ec084c/qualification.json
SHA256=A88B35037881BFD6D3A7934688C23DDC85ED4AC7D952F4D641C7BDBF0CDC5C76
```

It binds all contracts and inputs, verifies all 14 categories on 1,603,200
medium nodes, reproduces the 1200-draw stream hash, checks startup masking and
logit reconstruction, and performs a finite first-batch backward probe. The
compact record and manifest are under `docs/experiment/`.

## GPU trajectory and raw artifacts

```text
outputs/runs/20260904T150300Z-phk-v23-lf3-phase-latent-97a5b74/
```

The directory contains the step-1200 T0 checkpoint and prediction, seven audit
records, seven training-log records, 1200 T0 batch hashes, zero P0 physics batch
hashes, the carrier gate, start manifest, and summary. The summary SHA-256 is
`335DBF2194BA62C89E3E607941BA92B5FA14BB533B679330A7234A4466455D12`.
All seven summary-bound files match their declared size and SHA-256.

The remote and local console are empty with SHA-256
`E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855`.
The launcher exit record is intentionally preserved with SHA-256
`097D68F4988A2989D5C9F99B0BA328DFDE1067A3F9FA8C78C2583E828806DD96`;
it contains the literal `$?` plus newline rather than an integer. This is a
post-run logging defect, not a reconstructed exit code. Terminal summary
completion and all complete hash-bound artifacts are the independent completion
evidence.

## Recovery and local evaluation boundary

The recovery/shutdown proof is stored in git-ignored run storage at

```text
outputs/runs/20260904T160901Z-phk-v23-lf3-lifecycle/shutdown-proof.json
```

Before shutdown, remote and local summary, console, and exit-capture hashes
matched; no GPU compute or LF3 training process remained. After `sync` and
shutdown, SSH exited 255 with `Connection refused`. Only then was the nominal
local adjudicator run:

```powershell
.\.venv\Scripts\python.exe -m pinn_pcm_sci.phk_v23_lf3_evaluation `
  --output-directory outputs/runs/20260904T150300Z-phk-v23-lf3-local-adjudication-97a5b74-er1 `
  --run-directory outputs/runs/20260904T150300Z-phk-v23-lf3-phase-latent-97a5b74 `
  --cpu-qualification outputs/runs/20260904T150300Z-phk-v23-lf3-cpu-qualification-6ec084c/qualification.json
```

The resulting `adjudication.json` has SHA-256
`BB45AB4FAFE0A0ADC8E4F21A35E96E3A05B233594933C04AC0F3C58401B23378`
and size 624,160 bytes. It evaluates five roles and returns
`LF3_CARRIER_NOT_ESTABLISHED`.

The first local report is retained in git-ignored storage and superseded only
because its fixed-physics block inherited LF2 role labels for the LF3-T0
checkpoint. The `-er1` evaluator repair changes those keys to
`LF3_T0_LATENT_CARRIER` and `P0_to_T0`; it does not change the fixed pool,
checkpoint, scalar value (`6.571589165588435`), reference metrics, or decision.

## Figure regeneration

From the repository root, run:

```powershell
python paper/paper_v23/figures/generate_figures.py
```

The generator reads the frozen scalar extract, LF3-T0 prediction, and nominal
extra-fine reference. It emits five PNG/PDF pairs and refreshes
`figures/source-manifest.json`. It does not read either stress reference.

LF4 figures 6–8 are generated independently so the historical LF3 source
manifest is not rewritten:

```powershell
python paper/paper_v23/figures/generate_figures.py --lf4-only
```

## LF4 matched mechanism screen

- starting commit: `7df29ef730ad60156dfae5abd4a3ef41fa69a109`;
- activation commit: `5dbde1d210b6f2ff15d0f341ee316e59b49a1074`;
- source identity: `LF4-BUNDLE-EF532BCCF7FAC4482BEBD56A49DFAFE2D5F2FD4B2043540BD4414B6668CA644F`;
- source archive SHA-256: `780BAC482BC1DD538FBAB33180EF15F2270A684908C1D7168320D20C045AFC2E`;
- run directory: `outputs/runs/20260905T102817Z-phk-v23-lf4-interface-band-5dbde1d`;
- run-summary SHA-256: `692833FA52787AE9B204A64AC84D11E9AA15352459498EF3A2D066F7CB313ED2`;
- local adjudication: `outputs/runs/20260905T102817Z-phk-v23-lf4-local-adjudication-5dbde1d/adjudication.json`;
- adjudication SHA-256: `4301BEF71B49B17EA0EA164314A0FF5F9CBF11367C2EA92AF0509D75F0D94289`.

The cloud runner used three fresh-Adam, phase-only, FP64 arms from the exact
LF3-T0 weights. Each arm used the same 400 base batches; DEV-M and DEV-C also
used the same interface-band coordinates. Their three checkpoints and the
1200-row batch ledger are bound by the run summary. The initial launch stopped
before importing the runner because the base interpreter lacked `h5py`; no
output directory, optimizer, GPU process, or update existed. The existing
`pinn-pcm-sci-py311` environment passed an isolated `torch+h5py+CUDA+V100`
check and the full zero-step preflight, after which the unchanged scientific
run completed once.

After recovery, every remote file matched the local SHA-256, no training or
GPU compute process remained, and shutdown was confirmed by a closed TCP port
and SSH `Connection refused`. Only then was the local adjudicator run:

```powershell
.\.venv\Scripts\python.exe -m pinn_pcm_sci.phk_v23_lf4_evaluation `
  --output-directory outputs/runs/20260905T102817Z-phk-v23-lf4-local-adjudication-5dbde1d `
  --run-directory outputs/runs/20260905T102817Z-phk-v23-lf4-interface-band-5dbde1d `
  --cpu-qualification docs/experiment/artifacts/20260905T082728Z-phk-v23-lf4-cpu-qualification.json
```

The local result is `LF4_NO_DEVELOPMENT_ENTRY`. No development prediction was
selected and P0 was not run, so no fixed-physics P0 ratio exists.

## Non-reproducible-from-Git boundary

The compact terminal package does not embed checkpoints or raw run directories
in Git. Their identity is hash-bound, but a checkout that
lacks the git-ignored files cannot independently recompute the local evaluator
or phase-snapshot figure. The current paper therefore distinguishes versioned
compact evidence from locally retained raw carriers.

## LF5 zero-update temporal-edge qualification

- starting commit: `d86ddf1d206c611087a1b5284acda69efdfda9fa`;
- compact qualification:
  `docs/experiment/artifacts/20260905T150045Z-phk-v23-lf5-cpu-qualification.json`;
- compact SHA-256:
  `89F2B95D8F72C14506DEA4D78AF69E748637EB397B6983ADA4E9FA957ED8CED4`;
- temporal stream SHA-256:
  `8FD79D99DAA0175026017BB0025BEFEF896BCB383F46F906A3E800427C9B3BD9`;
- pool counts: `68/68/64/64`, invalid edge fraction `0`;
- optimizer updates / GPU trajectories: `0 / 0`;
- result: `LF5_TZL_ALIGNMENT_NOT_SUPPORTED_CPU`.

Onset uses the first medium-teacher logit sign crossing in W1/W3; recovery uses
the first subsequent reverse crossing in W2/W4 of the same cycle, with no time
wrap. Each edge stores cell, adjacent saved-time indices, teacher crossing
fraction, and normalized trapezoid-cell weight. DEV-M and DEV-C checkpoints
were loaded read-only. The finite-gradient probe called backward once and took
no optimizer step. Fine, extra-fine, direct `LF_ONLY`, the frozen evaluator,
and stress were not opened by LF5.

Regenerate only the LF5 figures with:

```powershell
python paper/paper_v23/figures/generate_figures.py --lf5-only
```

The source identities and output hashes are recorded in
`figures/source-manifest-lf5.json`. Because the CPU gate failed, there is no LF5
bundle, cloud run, checkpoint, prediction, recovery record, shutdown proof, or
local nominal adjudication to reproduce.
