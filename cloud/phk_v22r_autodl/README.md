# PHK-V2.2R AutoDL run card

This run card executes only reference-blind PINN work. Do not upload any file
under `outputs/runs/*extra-fine*` or `outputs/sealed/phk_v22r/` to the instance.

## Required instance

- Preferred: V100 32 GB; fallback: A100 40 GB.
- Python 3.11 and a CUDA-enabled PyTorch build with float64 support.
- Record the price displayed by AutoDL as `HOURLY_PRICE_CNY` before starting.
- The total instance ledger must stay at or below CNY 150.

## Environment check and 100-update profiles

From the repository root on the instance:

```bash
python -c "import torch, numpy, scipy; assert torch.cuda.is_available(); print(torch.__version__, torch.version.cuda, torch.cuda.get_device_name(0))"
python -m pinn_pcm_sci.phk_v22r_sprint \
  --mode profile \
  --output-root outputs/cloud/phk-v22r-profile-001 \
  --device cuda:0 \
  --hourly-price-cny "$HOURLY_PRICE_CNY" \
  --budget-cny 150 \
  --prior-spend-cny 0
```

The profile runs the four primary arms and exactly one strict-PHA 100-update
probe. It records seconds/update and peak allocated GPU memory. If strict PHA is
nonfinite, out of memory, or exceeds 1.8 times the MF cost, remove it from the
critical path without tuning its gate.

## Nominal pilot

After checking the profile projection:

```bash
python -m pinn_pcm_sci.phk_v22r_sprint \
  --mode pilot \
  --output-root outputs/cloud/phk-v22r-nominal-pilot-001 \
  --device cuda:0 \
  --hourly-price-cny "$HOURLY_PRICE_CNY" \
  --budget-cny 150 \
  --prior-spend-cny "$PROFILE_SPEND_CNY"
```

The pilot automatically writes a reference-blind extra-fine-axis prediction next
to each checkpoint. Download each checkpoint, prediction, training log, manifest,
environment report, and cost ledger. Predictions may be downloaded, but all
comparison to finite-volume fields must run locally.

The runner caps profile spend at 20% of the CNY 150 total and pilot spend at
30%. Enter the completed profile ledger value as `PROFILE_SPEND_CNY`; at least
50% of the total budget remains reserved for sealed confirmation.

## Upload allowlist

- repository source and configuration;
- physical coordinates, boundary definitions, and evaluation axes;
- medium anchors only if route B is machine-authorized;
- no extra-fine field, metric, mask, event time, or local comparison output.
