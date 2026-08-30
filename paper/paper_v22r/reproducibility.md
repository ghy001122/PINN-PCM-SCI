# Reproducibility guide

## Exact identities

- repository source commit: `69109cd324a6d5bf4690fe981086dc2f987eceed`;
- run ID: `20260830T112225-phk-v22r-v11-nominal-69109cd`;
- program contract SHA-256:
  `A413F56A2317CEFF15FFF2D3BD183C11D990F2E47E8BA33F7316F11567275272`;
- method contract SHA-256:
  `FEEFB36A4D86CACFA6CBAA8C263E7071421415CE88B4F7FBF6BA5F31B9B71D4F`;
- nominal reference SHA-256:
  `0CE36347433983DB3631C9CD92E3FBFDAEF5A692D3370736071696135FFB73CE`.

The tracked run manifest at
`docs/experiment/manifests/20260830T112225-phk-v22r-v11-nominal-69109cd.json`
binds all checkpoint, prediction, training-log, manifest, evaluation, summary,
and decision hashes.

## Environment

Training used Python 3.11.9, PyTorch 2.5.1+cu118, CUDA 11.8, FP64, a Tesla
V100-PCIE-32GB, and `OMP_NUM_THREADS=1`. The four arms used seed 17 and the exact
configuration in the v1.1 contracts. Large run artifacts remain under
`outputs/runs/20260830T112225-phk-v22r-v11-nominal-69109cd/` and are intentionally
not committed.

## Local verification

From the repository root, the engineering and evaluator regression suite is:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_phk_v21_benchmark tests.test_phk_v21_design tests.test_phk_v21_design_runner tests.test_phk_v21_engineering tests.test_phk_v21_evaluator tests.test_phk_v21_runner tests.test_phk_v21_solver tests.test_phk_v22r_pinn
```

The four nominal evaluations are reproduced locally with the
`pinn_pcm_sci.phk_v22r_evaluator` module using `--control FULL`, one prediction
carrier per arm, and a new output path. The terminal decision is reproduced with
`pinn_pcm_sci.phk_v22r_decision decide`, supplying the four evaluation paths in
the fixed raw, MF-only, sampler-only, and combined roles.

Do not pass either stress control to the evaluator. Stress access is not
authorized because no final candidate freeze exists.

## Figure reproduction

The five main figures and their CSV extracts are generated from the hash-bound
summary, evaluations, prediction carriers, decision, and nominal reference:

```powershell
python paper\paper_v22r\figures\generate_figures.py
```

The figure runtime requires NumPy and Matplotlib but does not require PyTorch.
`figures/source-manifest.json` records the generator, input, CSV, PNG, and PDF
hashes and explicitly records `stress_references_read=false`.

## Scientific replay boundary

Re-running training is not part of package verification. The terminal contract
forbids a seed change, extension, or rescue run after nominal No-Go. A future
scientific rerun requires a new versioned contract and new authorization; it must
not overwrite or supersede the evidence identity above silently.
