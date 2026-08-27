# Reproducibility guide

## 1. What can be reproduced without new scientific execution

The current project authorization permits verification of existing artifacts, tests, figures, hashes, and documentation. It does not permit rerunning PHK solver intents or starting PINN/GPU/formal work. The commands in Sections 2–4 are therefore safe verification commands. Section 5 records the historical production interface for provenance only and must not be executed under the current phase.

Repository root used for this package:

~~~text
E:\Python demo\PINN-PCM-SCI
~~~

Primary environment recorded during PHK-V2:

~~~text
Python 3.11.9
PyTorch 2.5.1+cpu
CUDA available: false
CUDA device count: 0
nvidia-smi: unavailable
~~~

The PHK solver/evaluator uses NumPy and SciPy in float64. External baseline module smokes used isolated temporary environments and did not generate paper metrics.

## 2. Verify contracts and tests

From the repository root:

~~~powershell
.\.venv\Scripts\python.exe -m unittest tests.test_phk_contract tests.test_phk_benchmark tests.test_phk_evaluator tests.test_phk_runner -v
.\.venv\Scripts\python.exe -m pinn_pcm_sci.document_consistency --root .
~~~

Expected focused test result at package closeout: all 22 PHK tests pass. The document command must print `DOCUMENT_CONSISTENCY_VALID` after final status synchronization.

## 3. Verify machine identities

~~~powershell
Get-FileHash -Algorithm SHA256 configs\phk_v2\program_contract.json
Get-FileHash -Algorithm SHA256 configs\phk_v2\object_numerical_contract.json
Get-FileHash -Algorithm SHA256 configs\phk_v2\case_split_manifest.json
Get-FileHash -Algorithm SHA256 outputs\runs\20260827T-phk-v2-s2-q-terminal-summary\summary.json
~~~

Expected hashes:

~~~text
0E1D89DD23F93C90160AC82ECE60ADA154410F4DDC33578CB892207FE8B445A8
3B3B9A369F4AFDFFB201394DD294E7196BAF04E5B36BAFE126291CA9CB3EA157
EBFDA2D59049AC989E8AA6C9622D92CF077D4B808961AB5807D178BF09DF57ED
8964ACB687F1BDB4F03C2E0D33891EE3705D4C2ABD271085D0C82A2B4469EA78
~~~

The split JSON also stores internal canonical identity `55261CCA82ED2B71A9D3A81E28FC957B4873086CECB09D28EEE9B73B2CD73E09`.

## 4. Rebuild figures from existing numerical carriers

Figure generation reads existing `.npz`, JSON, and contract carriers and performs no solver or training work. Use any local Python environment satisfying `paper_v2/figures/requirements-figures.txt` (the recorded render used Python 3.8.4, NumPy 1.26.4, and Matplotlib 3.8.4):

~~~powershell
python paper_v2\figures\generate_figures.py
~~~

The generator rewrites only `paper_v2/figures/figure-01...figure-06` in PNG/PDF form and the derived CSV files in `paper_v2/figures/data/`. It verifies the terminal summary hash before drawing.

## 5. Historical production interface — provenance only

The runner interface used immutable intent-first execution:

~~~powershell
.\.venv\Scripts\python.exe -m pinn_pcm_sci.phk_runner qualify --run-id <run-id> --intent <1-12> --program configs\phk_v2\program_contract.json --object configs\phk_v2\object_numerical_contract.json --split configs\phk_v2\case_split_manifest.json
~~~

The terminal aggregation interface was:

~~~powershell
.\.venv\Scripts\python.exe -m pinn_pcm_sci.phk_runner summarize-q --run-id 20260827T-phk-v2-s2-q-terminal-summary --program configs\phk_v2\program_contract.json --object configs\phk_v2\object_numerical_contract.json --split configs\phk_v2\case_split_manifest.json
~~~

Do not rerun these commands under the current phase. Intent 9 is already consumed, intents 10–12 are formally not reached, and a replacement/rerun would violate the frozen ladder.

## 6. Evidence locations

| Evidence | Path |
|---|---|
| source/baseline audit | `docs/references/2026-08-27-phk-pinn-primary-source-baseline-audit.md` |
| S1 module smoke | `docs/experiment/2026-08-27-phk-v2-s1-baseline-acquisition-and-cpu-smoke.md` |
| program preregistration | `docs/governance/2026-08-27-phk-v2-s0-program-preregistration.md` |
| object/split freeze | `docs/governance/2026-08-27-phk-v2-s0b-object-and-split-freeze.md` |
| S2 closeout | `docs/experiment/2026-08-27-phk-v2-s2-terminal-closeout.md` |
| raw run outputs | `outputs/runs/20260827T-phk-v2-s2-intent-*` |
| finalized manifests | `docs/experiment/manifests/20260827T-phk-v2-s2-*.json` |
| terminal summary | `outputs/runs/20260827T-phk-v2-s2-q-terminal-summary/summary.json` |
| core solver | `pinn_pcm_sci/phk_benchmark.py` |
| evaluator | `pinn_pcm_sci/phk_evaluator.py` |
| immutable runner | `pinn_pcm_sci/phk_runner.py` |
| tests | `tests/test_phk_*.py` |

## 7. Artifact semantics

- `COMPLETED` means a runner finalized its artifacts; it does not automatically mean an oracle or event passed.
- `FAILED` means the scheduled compute failed and remains in accounting.
- `NOT_REACHED` means the preregistered sequence stopped earlier; it is not a failed method result.
- Result `.npz` files contain field arrays and immutable metadata. Reports contain guards, event diagnostics, and solver statistics. Manifests bind hashes and compute accounting.
- Exact replay has different metadata identity from the source run, so the file hash differs even though all numerical arrays and six endpoint differences match exactly.

## 8. External baseline boundary

The `.tmp/phk-v2/external/` trees are acquisition workspaces, not distributed paper assets. Sharp/PF are GPL-3.0; original jaxpi is Penn-restricted; jaxpi2 is Apache-2.0 but was only used in a minimal smoke. The paper package records fixed source SHAs and results without copying these trees.

## 9. Expected terminal verdict

Reading the terminal summary must yield:

~~~text
outcome = PHK_V2_ORACLE_NO_GO_EVENT_CONTRACT_AND_CONTROL_EXECUTION_FAILURE
method_route = STOP_BEFORE_PINN_TRAINING
oracle_qualified = false
replay_pass = true
thermal_effect_established = true
floor_disposition = NOT_SEALED_FOR_NEURAL_WORK_ORACLE_GATE_FAILED_BEFORE_METHOD_STAGE
~~~

These fields must not be replaced with a positive method verdict during reproduction or packaging.
