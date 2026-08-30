# PHK-V2.2R v1.1 AutoDL run card

- `status`: `V11_FOUR_ARM_NOMINAL_ENTRYPOINT_FROZEN`
- `profile_run_id`: `20260830T0122-phk-v22r-d1-gpu-profile-cf372713`
- `current_route`: `FOUR_ARM_FALLBACK`
- `nominal_updates`: `1000`

This card governs reference-blind cloud work. Never upload the nominal
extra-fine carrier, either sealed stress reference, a local evaluation, or any
file below `outputs/sealed/phk_v22r/`.

## Closed profile

The legacy five-arm profile is complete and must not be repeated. Strict PHA
passed only its cost gate and failed its frozen development gain gate; generic
RAR missed its P0 deadline. Neither appears in the v1.1 executable matrix.

## Exact nominal command

Run only after the local focused tests, combined regression, and document
consistency gate all pass. Replace `<RUN_ID>` and `<SOURCE_IDENTITY>` with the
predeclared immutable run ID and the selective P0 commit identity.

```bash
cd /root/autodl-tmp/PINN-PCM-SCI
OMP_NUM_THREADS=1 /root/autodl-tmp/envs/pinn-pcm-sci-py311/bin/python \
  -m pinn_pcm_sci.phk_v22r_sprint \
  --mode nominal \
  --output-root /root/autodl-tmp/PINN-PCM-SCI/outputs/runs/<RUN_ID> \
  --device cuda:0 \
  --hourly-price-cny 1.88 \
  --budget-cny 150 \
  --prior-spend-cny 3.6619446915 \
  --source-identity <SOURCE_IDENTITY>
```

The runner accepts no arm override and no legacy `profile` or `pilot` mode. It
executes, in order, `STRONG_RAW`, `MF_ONLY`, `SAMPLER_ONLY`, and
`MF_PLUS_SAMPLER`, all from scratch in FP64 with seed 17, Band A,
`512/128/128` points, Adam, exactly 1000 updates, and final checkpoint only.
Each arm emits its checkpoint, training log, start/final manifests, ledger, and
reference-blind prediction carrier.

Run the command in the existing `phk_train` tmux session with a launcher whose
exit trap calls `/usr/bin/shutdown`. Success, failure, or interruption must all
end in shutdown after allowed artifacts are recovered.

## Nominal adjudication boundary

Download the complete run directory and compare the four predictions with the
nominal development reference locally. A nominal PASS authorizes only the next
reference-blind confirmation preparations; it does not authorize stress
reference access.

If nominal is positive:

1. run one 100-update, width-76 parameter-matched raw timing calibration on the
   nominal physical case without a reference;
2. write `confirmation_plan.json`, freezing the selected method, strongest
   comparator, and raw update count derived by
   `floor(selected nominal wall seconds / raw calibration seconds per update)`;
3. train the three frozen roles from scratch on each of the two stress physical
   cases and generate six prediction carriers without any reference file;
4. download all six carriers and verify their config, checkpoint, contract, and
   byte identities locally;
5. only then write `candidate_freeze.json` and open the two sealed references
   once for local evaluation.

Nominal No-Go stops the cloud route immediately: no seed change, extension,
strict PHA, generic RAR, Route B/C, functional pivot, warm start, SIREN,
continuation, L-BFGS, or new module.

## Instance and budget

- Validated device: Tesla V100-PCIE-32GB.
- Environment: Python 3.11.9, PyTorch 2.5.1+cu118, CUDA 11.8.
- Displayed price: CNY 1.88/hour.
- Estimated cumulative spend at profile closeout: CNY 3.6619446915.
- Hard cumulative cap: CNY 150.
- `OMP_NUM_THREADS` must be explicitly set to a positive integer; use `1`.
- Stop new cloud work if actual or projected cumulative cost approaches the cap.
- Shut down after every paid training or recovery stage.

Allowed download: checkpoint, prediction, training log, manifest, environment
report, and cost ledger. Every comparison with nominal or sealed finite-volume
fields remains local.
