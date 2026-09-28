# PINN PCM standalone numerical handoff

This is the local research handoff for `PCM-20260926-CORE-REVISION-VO2-BRIDGE-01`, based on `90508f05a6f233a485413c7589cc74420015cbea`. It preserves the synthetic object's evidence and the separate author-model numerical reproduction. It is not a public dataset release.

The complete local package is `D:\Temp\PINN-PCM-Standalone-20260926`. Inputs are ordinary files below that root; local hard links reduce duplication without requiring the old checkout. Copying the directory to another disk preserves the files normally. Historical path strings inside provenance/configuration records are metadata, not fallback input locations.

## Actual independent execution

Python 3.11.9, NumPy 2.1.3 and SciPy 1.14.1 from a runtime outside the repository were used. The scorer process denies access to the original repository through a Python filesystem audit hook and validates all required relative inputs. The denial probe passed. Temporarily removing the required grid input produced an immediate error; the file was restored, with no replacement generation. Exact historical Boolean decisions and numeric tolerances `rtol=2e-10, atol=2e-12` were retained.

From the package root, use an independent Python environment with those dependencies:

```text
python -I recompute.py --validate-only
python -I -u recompute.py --fresh
```

`--fresh` creates a clean execution directory under `executions/`, links immutable package inputs locally, copies the source adapters, and recomputes the included scopes. It does not overwrite prior scores or launch any training, reference generation or new trajectory. `--fresh --validate-only` was separately checked. Running `--scope all` without `--fresh` reuses explicitly labelled completed verification records and executes only unfinished scopes; it must not be represented as a new complete recomputation.

Individual scopes are `core`, `extension`, `b1`, `s21`, `s22`, `s23`, `residuals`, `vo2`, and `fcov`. Output is under the execution root. A partial failed scope is retained for inspection; the entry never silently replaces inputs or relaxes tolerances to finish.

## Capabilities and limits

| Capability | Included behavior | Boundary |
|---|---|---|
| Saved-array rescoring | Core 72, historical continuation 18, B1 42 reference/reader rows; all eight S21 arms; B0/D_E/N/G/S; all 12 new F_cov reference/reader rows | These counts reuse endpoints across references/readers and are not independent repetitions |
| S23 reconstruction | Common residuals, both thermal conventions, endpoint seams, all internal algebraic defects, paired reference RMS and both active-support semantics | Reuses saved T derivatives and endpoint AD arrays; executes zero propagation steps and no new network query |
| Saved-residual reaggregation | Fixed-training, independent-D, common temporal/spatial pools and thermal-envelope records | Re-aggregates archived residual values; does not recompute neural AD |
| Author-model reanalysis | Both saved step sizes in five fixed cases, waveform/event/endpoint differences | Executes zero new system steps and certifies no quantitative experimental fit |
| Checkpoint inference | Accepted checkpoint files are retained where supplied, with configuration/source identity | Not certified by the array-only verification. Loading checkpoints or recomputing network AD requires a separate inference entry and dependencies; do not claim it has already been done |

The frozen numerical metric modules are included. The only scoring adapters are lossless temporary array storage, package-root resolution and a pure I/O replacement for the former S23 execution-driver import. The latter prevents a saved-array evaluation from importing model-query or propagation machinery. Scientific formulae and thresholds are unchanged. This is an independent execution location, not an independently invented scoring implementation.

Expected records remain separate from newly calculated results. Input inventory, `handoff.json`, `independent-verification.json`, `missing-input-verification.json` and per-scope verification reports provide the entry points. The F_cov expected record was frozen after the first post-lock scoring and checked by a second array-only execution: 4,586 values and exact Boolean decisions passed. All nine scopes have completed verification records; the summary preserves their separate execution identities.

## Source, rights and access

Synthetic candidates, references, coordinate/volume/time measures, original observation inputs, decision definitions and retained diagnostic arrays are project research artifacts. Public release has not been approved. The executed F_cov source bundle and its manifest preserve code provenance; their presence does not certify a new training or checkpoint-inference run. Pinned author-model source files, adaptation attribution and the original MIT code license are retained; the license does not automatically license third-party experimental records or publisher figures. The raw experimental CSV archive from the related Collective dynamics repository and the publisher PDF are not placed in this synthetic-data handoff.

No DOI, public object-store URL or controlled external reviewer link has been created. P03 remains OPEN until an external recipient can actually retrieve the complete approved inputs and run the entry. See the companion data-access plan for the proposed review/publication route.
