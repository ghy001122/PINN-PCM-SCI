# Reproducibility and evidence map

## Scope

This guide maps the LF3 baseline, LF4 matched mechanism screen, LF5 bounded
premise rejection, and LF6 matched event-frontier screen plus executed P0,
figure extraction, and terminal adjudication. It does not authorize another
scientific GPU run, opening stress references, or changing frozen contracts.

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

## LF5 CPU-T and post-qualification exploratory trajectory

- starting commit: `d86ddf1d206c611087a1b5284acda69efdfda9fa`;
- compact qualification:
  `docs/experiment/artifacts/20260905T150045Z-phk-v23-lf5-cpu-qualification.json`;
- compact SHA-256:
  `89F2B95D8F72C14506DEA4D78AF69E748637EB397B6983ADA4E9FA957ED8CED4`;
- temporal stream SHA-256:
  `8FD79D99DAA0175026017BB0025BEFEF896BCB383F46F906A3E800427C9B3BD9`;
- pool counts: `68/68/64/64`, invalid edge fraction `0`;
- CPU optimizer updates / GPU trajectories: `0 / 0`;
- CPU result: `LF5_TZL_ALIGNMENT_NOT_SUPPORTED_CPU`.

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
`figures/source-manifest-lf5.json`. After the CPU result, the user explicitly
authorized the unchanged trajectory with evidence role
`POST_QUALIFICATION_USER_OVERRIDE_EXPLORATORY`. The executed source identity was
`LF5-BUNDLE-07D66D6D...273A0664` from commit
`eba0ffec8c20a23064488ad42adbaf4e2acc424f`.

The run directory is:

```text
outputs/runs/20260905T172640Z-phk-v23-lf5-temporal-eba0ffe/
```

It contains a 400-line DEV-T batch ledger, nine telemetry records, and the start
manifest. Base and spatial final hashes equal their frozen values. The temporal
hash is `48A0C6B48F6A606B9681E7C349CC5FB089D3D129EF6A40077564E08C9AAFB127`
rather than the frozen
`8FD79D99DAA0175026017BB0025BEFEF896BCB383F46F906A3E800427C9B3BD9`,
with the first mismatch at step 1. The runner raised after 400 updates and before
checkpoint writing. Hence the endpoint is identity-invalid, P0 was not run, and
fine/extra/direct-LF_ONLY evaluation was not executed. All three remote files
were recovered with matching size/SHA; GPU memory and compute processes were
zero before shutdown, TCP 28355 closed, and SSH returned `Connection refused`.

## LF6 matched development and executed physics continuation

- starting commit: `9d3c22674dc6279846fa341433d36f603a0854f1`;
- activation commit: `55d552670ba0f727f781d4051b84efde474996f9`;
- prestep engineering repair: `074eec7f76b4661deda1a622b5343bf992fa2715`;
- CPU compact artifact:
  `docs/experiment/artifacts/20260906T065434Z-phk-v23-lf6-cpu-qualification.json`;
- CPU compact SHA-256:
  `60996F3814BF7113E39925774EE9EAAC11091F466F10E7575AC55F2D731A1046`;
- raw root:
  `outputs/runs/20260906T065434Z-phk-v23-lf6-event-frontier-pilot/`.

CPU-F made zero optimizer updates. It materialized the event-frontier and
uniform endpoint sets, all 400 base/spatial batches, all 1200 P0 batches, and
the fixed blind pool before cloud execution. The materialized ledger SHA-256 is
`29E02DAF81A07BA4AF2B95B354126E75E9419AAE094E9486589455D31D2D6801`;
the stream identities are:

```text
base400       3870D0C1411B3DF6E04C5BA316B3F0F77233D94A73A19E84523D81B62F692E4A
spatial400    4DB1728CC543B1AB18BD3F74B83B29EBFE5F95624D98DAFEA615B0ECDC69DEC4
P0 physics    536E6706A0B68EBB1277A97F402D273AFA2EA1E0B27106F26CB4222B7EC05C53
blind pool    FD285AFC67C011CE9778E36C5FEE8FA7EAECB933690AF346993B7677AF0E64CF
```

DEV-U and DEV-R each completed exactly 400 updates. Their checkpoint/prediction
SHA-256 values are respectively
`1DE231C2...B592C` / `77788477...9565` and
`7CFDD98E...F499` / `5F20FB6A...50EF`. The matched screen returned
`NO_RANK_SPECIFIC_INCREMENT`; DEV-R alone passed the relaxed safety gate and
was selected for P0.

The first P0 invocation stopped before its first optimizer step because a
checkpoint identity comparison treated frozen V/T parameters as an architecture
change. Strict state loading showed all 51 tensors compatible. The repair
reproduces the checkpoint's frozen state only for architecture comparison,
restores V/T trainability, and adds a P0-only mode that verifies all twelve
completed development artifacts. DEV-U and DEV-R were not rerun. The repair is
engineering evidence, not a new scientific arm.

P0 then completed exactly 1200 updates. Its batch ledger, checkpoint, gate,
prediction, telemetry, and run-summary SHA-256 values are:

```text
batch ledger  9B96F967544F70A879B86FFD8E91095176998176BAAEABC68751174F6A2B3756
checkpoint    8ED892EAFDF7F4C37D677B618079A2AE078CB4C5E5F24D09AEB676330CFAF864
gate          8351E5474BF2D2C790E8E3ACE32D847A9E59D9F0C1F85918BC59A1FD819BC694
prediction    A61DBC917BA28FF3059B42039390DB6044871E3B2DBECE602922F3469878B228
telemetry     6134D9B8331300C958E08843FA47B96B9FA1E8087274D102C819E7211F3D2932
run summary   31194B489131076445138A817956D30A1FC27FFBCEFDF5E9B2D2642EEED028F0
```

All recovered remote/local sizes and hashes matched. GPU memory and compute
processes were zero before shutdown; TCP was closed and SSH returned explicit
`Connection refused`. Only then did local evaluation read fine, extra-fine, and
direct `LF_ONLY`. The final local adjudication SHA-256 is
`8A8E27970D4C12840087D9FFBA3F27C920498C035071F48D7B265F7D7982AAAD`.
It returns `LF6_P0_PRESERVATION_FAILED`, candidate none, and
`PHYSICS_FORGETTING_RESULT_NO_RESCUE`.

Regenerate only the LF6 figures with a Python environment containing Pillow:

```powershell
python paper/paper_v23/figures/generate_figures.py --lf6-only
```

Input and output hashes are bound in `figures/source-manifest-lf6.json`. A Git
checkout without the git-ignored raw directory can verify the compact evidence
and frozen figure data but cannot independently reload the large checkpoints or
predictions. Stress remains sealed and unread.

## LF7 ACTIVE matched continuation scaffold

- starting commit: `e00f8767fc1d611b4cadcd0057720d1dd507f51c`;
- campaign timestamp: `20260907T144634Z`;
- exact LF6 DEV-R checkpoint SHA-256:
  `7CFDD98E3A03BE29BBE587042967BD44E72D140AE7AC3396CB35E0CF5748F499`;
- LF6 materialized-ledger SHA-256:
  `29E02DAF81A07BA4AF2B95B354126E75E9419AAE094E9486589455D31D2D6801`;
- P0 physics stream SHA-256:
  `536E6706A0B68EBB1277A97F402D273AFA2EA1E0B27106F26CB4222B7EC05C53`;
- fixed blind pool SHA-256:
  `FD285AFC67C011CE9778E36C5FEE8FA7EAECB933690AF346993B7677AF0E64CF`;
- raw root:
  `outputs/runs/20260907T144634Z-phk-v23-lf7-competence-filtered-refinement-pilot`.

At activation, the LF7 metrics file is deliberately `ACTIVE_RESULTS_PENDING`
with null arm outcomes. Running
`python paper/paper_v23/figures/generate_figures.py --lf7-only` must report a
safe skip and emit no LF7 figure until terminal evidence replaces the nulls.
P0-F uses medium competence only for block acceptance, not gradients, and is
not label-free. Fine, extra-fine, and direct `LF_ONLY` remain local-only after
recovery and shutdown; stress remains sealed and unread.
