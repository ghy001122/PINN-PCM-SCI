# Reproducibility and evidence map

## Scope

This guide reproduces the LF3 implementation checks, figure extraction, and
local terminal adjudication. It does not authorize another scientific GPU run,
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

## Non-reproducible-from-Git boundary

The compact terminal package does not embed the large checkpoint, prediction,
or raw run directory in Git. Their identity is hash-bound, but a checkout that
lacks the git-ignored files cannot independently recompute the local evaluator
or phase-snapshot figure. The current paper therefore distinguishes versioned
compact evidence from locally retained raw carriers.
