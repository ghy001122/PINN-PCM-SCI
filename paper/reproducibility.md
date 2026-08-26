# Local Reproducibility Guide

## 1. Supported scope

These instructions target Windows PowerShell, local CPython 3.11, and the repository virtual environment. They verify the frozen evidence and reproduce only the already completed Q0 zero-drive solve in memory. They do not create a new ledger intent, change a contract, access COMSOL, use a GPU, or rerun the consumed driven QN intent.

Use the repository root as the working directory:

```powershell
$PinnPcmSciRoot = 'E:\Python demo\PINN-PCM-SCI'
Set-Location -LiteralPath $PinnPcmSciRoot
```

The recorded runtime was CPython `3.11.9` with NumPy `2.1.1`, SciPy `1.14.1`, and h5py `3.12.1`. The exact direct dependency closure is [`requirements/syn-edt-oracle-cpu.lock`](../requirements/syn-edt-oracle-cpu.lock), SHA256 `8AF3857D5423C8E57C37661222EAEE763096DE1D7FDD366273FC22036B165516`.

```powershell
& .\.venv\Scripts\python.exe -c "import sys,numpy,scipy,h5py; print(sys.version); print('numpy',numpy.__version__,'scipy',scipy.__version__,'h5py',h5py.__version__)"
```

## 2. Verify immutable hashes before executing code

Run this read-only check first. It stops on any mismatch.

```powershell
$ExpectedEvidenceHashes = [ordered]@{
  'configs\goal_paper_one_shot_v1\s0_contract.json' = '947E737A255D27A7BB2553286809ADB98219FD4E48B932B170CB06608A2E3A75'
  'configs\goal_paper_one_shot_v1\s2_numerical_contract.json' = 'D059AA2261CC227C3B16B7965A75C461AD64110C2A20C3700B62E54FDE25E8E6'
  'outputs\runs\20260826T113537Z-goal-paper-one-shot-v1-s2-freeze-002\case-manifest-q-only.json' = 'EF093A5C2F2E798FF05E768C3D0837CF08C3E10FD6AE79B432F26585F0FCD09C'
  'docs\experiment\manifests\20260826T113537Z-goal-paper-one-shot-v1-s2-freeze-002.json' = '74B5CD92A5271FD481A134DD52A80DD22FC65DC6784F761C5B8B74B880AB2F35'
  'docs\experiment\manifests\20260826T113638Z-goal-paper-one-shot-v1-s2-intent-01-q0.json' = '6451DFC6C1E331A0AF86997FDCC74083CD4C8C781C96C2C2A156EB149504205E'
  'outputs\runs\20260826T113638Z-goal-paper-one-shot-v1-s2-intent-01-q0\case-q0-intent-01-coarse-coarse-full.h5' = '01F5DCF28E25A75E74C5EDBE612456A542ECA36EFFCB8CAFEC196AE4994F7A01'
  'outputs\runs\20260826T113638Z-goal-paper-one-shot-v1-s2-intent-01-q0\evaluation-q0-intent-01.npz' = 'F24439F92CBC70FDED7A24DE1D0B6272E59D14A169CCB86A1FAA888E21BDAE6B'
  'outputs\runs\20260826T113638Z-goal-paper-one-shot-v1-s2-intent-01-q0\report.json' = '0964E3B55431AA49CDE158FFF7F98F3478288865A6DE670CC88ABD9B7BF3D1A8'
  'docs\experiment\manifests\20260826T113752Z-goal-paper-one-shot-v1-s2-intent-02-qn-coarse-fine.json' = 'A1806D03A1D5F8687FCE252F66BA2CCE921DA78902EADA149B5A84C42CE0ECB8'
  'docs\experiment\intents\20260826T113752Z-goal-paper-one-shot-v1-s2-intent-02-qn-coarse-fine.json' = 'DC2A38B5BF9F560A2A64D78733647C02906CF225C8392699614E5DAC778D4AE5'
  'docs\experiment\intent_claims\s2-intent-02.json' = 'CF7FB0E8C8F5DF05C16F1E13F88C75C68FEE9F3D23F93427FA952A161C2A8B7C'
  'docs\references\2026-08-26-goal-paper-one-shot-v1-s1-source-legal-novelty-review.md' = '1CCEFFFCF743B2B0781AA004F096AFD49C07E79C27CB5D9D339FCF99EE79AF1C'
  'docs\experiment\2026-08-26-goal-paper-one-shot-v1-s2-terminal-closeout.md' = 'C780D66347A21D9DFD6495A7DFE7ECF9D3E9A6DA1DF9683AEE5F34855B8127B2'
}
foreach ($EvidenceEntry in $ExpectedEvidenceHashes.GetEnumerator()) {
  $ActualEvidenceHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $EvidenceEntry.Key).Hash
  if ($ActualEvidenceHash -ne $EvidenceEntry.Value) {
    throw "SHA256 mismatch: $($EvidenceEntry.Key) expected=$($EvidenceEntry.Value) actual=$ActualEvidenceHash"
  }
}
'evidence hashes: OK'
```

## 3. Validate the append-only ledger

This command is read-only and checks index-to-manifest consistency.

```powershell
$LedgerValidation = @'
from pathlib import Path
from pinn_pcm_sci.ledger import ExperimentLedger
ExperimentLedger(Path('docs/experiment')).validate()
print('ledger: OK')
'@
& .\.venv\Scripts\python.exe -c $LedgerValidation
```

The final two relevant ledger rows must remain:

- Q0: `execution_status=COMPLETED`, `numerical_validity=PENDING_S2_CROSS_RUN_ADJUDICATION`.
- QN intent 2: `execution_status=FAILED`, `numerical_validity=NOT_EVALUATED`, `route_disposition=SYN_EDT_S2_EXECUTION_INVALID_STOP`.

## 4. Run the focused verification suite

```powershell
& .\.venv\Scripts\python.exe -m unittest tests.test_syn_edt_2d tests.test_syn_edt_evaluator tests.test_syn_edt_2d_runner tests.test_ledger -v
```

The verified repository state on 2026-08-26 ran `50` tests in this focused suite and returned `OK`. Tests validate implementation and evidence plumbing; they are not additional scientific results.

## 5. Reproduce only the existing Q0 result in memory

The command below calls the frozen solver directly. It does not invoke `syn_edt_2d_runner`, create a run directory, claim an intent, or append to the ledger.

```powershell
$Q0Reproduction = @'
import json
from pathlib import Path
import numpy as np
from pinn_pcm_sci.syn_edt_2d import (
    SynEdtCaseSpec,
    SynEdtControl,
    SynEdtOracleCase,
    SynEdtPhysicalContract,
    SynEdtResolution,
)

root = Path('.')
contract = SynEdtPhysicalContract.from_s0(
    root / 'configs/goal_paper_one_shot_v1/s0_contract.json',
    root / 'configs/goal_paper_one_shot_v1/s2_numerical_contract.json',
)
result = SynEdtOracleCase(
    contract=contract,
    case=SynEdtCaseSpec.qualification('Q0', contract),
    resolution=SynEdtResolution.from_levels('coarse', 'coarse', contract),
    control=SynEdtControl.FULL,
).solve()
persisted = json.loads((root / 'outputs/runs/20260826T113638Z-goal-paper-one-shot-v1-s2-intent-01-q0/report.json').read_text(encoding='utf-8'))

assert result.guard_report.passed
assert not result.event_report.applicable
assert result.solver_statistics == persisted['solver_statistics']
np.testing.assert_allclose(result.y, 0.5, rtol=0.0, atol=2e-13)
np.testing.assert_allclose(result.temperature_k, 300.0, rtol=0.0, atol=2e-12)
assert result.guard_report.relative_mass_drift_max == 0.0
assert result.guard_report.no_flux_residual_max == 0.0
assert result.guard_report.relative_heat_balance_residual_max == 0.0
assert result.guard_report.relative_terminal_current_mismatch_max == 0.0

print(json.dumps({
    'classification': 'VERIFIED_Q0_ZERO_DRIVE_REPRODUCTION_ONLY',
    'timesteps': result.solver_statistics['timesteps'],
    'y_min': result.guard_report.y_min,
    'y_max': result.guard_report.y_max,
    'temperature_min_k': result.guard_report.temperature_min_k,
    'temperature_max_k': result.guard_report.temperature_max_k,
    'final_transport_scaled_residual_max': result.solver_statistics['final_transport_scaled_residual_max'],
    'event_applicable': result.event_report.applicable,
}, indent=2, sort_keys=True))
'@
& .\.venv\Scripts\python.exe -c $Q0Reproduction
```

The only permissible interpretation is that the frozen zero-drive guard is reproducible. Q0 cannot establish a driven event, convergence floor, oracle qualification, or method result.

## 6. Do not replay the consumed QN intent

Do **not** invoke `pinn_pcm_sci.syn_edt_2d_runner run-case` with `--intent 2` under a new run ID. Also do not duplicate intent 1 through the ledger runner; Q0 reproduction is restricted to the direct in-memory command in §5.

Intent 2 is finalized as a failed, budget-consuming production intent. Its atomic claim forbids automatic replay, and the frozen contract forbids timestep, parameter, and solver-threshold rescue. Reproducing Q0 through the direct in-memory command above avoids falsifying the append-only intent sequence.

## 7. Run the diagnostic separately and label it non-scientific

The targeted regression test verifies only that the minimal driven fixture preserves the observed failure class:

```powershell
& .\.venv\Scripts\python.exe -m unittest tests.test_syn_edt_2d.SynEdtNonScientificFixtureTest.test_non_scientific_diagnostic_freezes_qn_first_step_newton_no_go -v
```

For the numerical half-step trace and finite-difference Jacobian check, use this independent in-memory diagnostic. It does not enter the ledger.

```powershell
$NonScientificDiagnostic = @'
from dataclasses import replace
from pathlib import Path
import json
import numpy as np
from scipy.sparse.linalg import spsolve
from pinn_pcm_sci.syn_edt_2d import (
    SynEdtCaseSpec, SynEdtControl, SynEdtPhysicalContract,
    SynEdtResolution, _OracleEngine, _stable_logit,
)

contract = SynEdtPhysicalContract.from_s0(
    Path('configs/goal_paper_one_shot_v1/s0_contract.json'),
    Path('configs/goal_paper_one_shot_v1/s2_numerical_contract.json'),
)
case = replace(
    SynEdtCaseSpec.qualification('QN', contract).as_fixture(total_duration_s=0.00125),
    active_radius_nm=50.0,
)
resolution = SynEdtResolution.fixture(
    active_h_max_nm=100.0, corner_h_max_nm=100.0,
    dt_max_s=0.00125, saved_field_interval_s=0.00125,
)
engine = _OracleEngine(contract, case, resolution, SynEdtControl.FULL)
y_old = np.full(engine.mesh.active_full.size, case.initial_y, dtype=np.float64)
theta = np.ones(engine.mesh.domain.size, dtype=np.float64)
psi, joule, *_ = engine._electric(y_old, theta, 0.01125)
theta_target, *_ = engine._thermal(joule)
relax = float(engine.numerics['block_relaxation'])
theta = (1.0 - relax) * theta + relax * theta_target
dt_hat = 0.00125 / contract.time_s
conductance, drive = engine._transport_coefficients(psi, theta)
w = _stable_logit(y_old)

r, jac, scaled0 = engine._transport_system(w, y_old, dt_hat, conductance, drive, jacobian=True)
direction = np.linspace(-1.0, 1.0, w.size)
direction /= np.linalg.norm(direction)
eps = 1e-6
rp, _, _ = engine._transport_system(w + eps * direction, y_old, dt_hat, conductance, drive, jacobian=False)
rm, _, _ = engine._transport_system(w - eps * direction, y_old, dt_hat, conductance, drive, jacobian=False)
fd = (rp - rm) / (2.0 * eps)
jv = jac @ direction
fd_relative_inf = np.linalg.norm(fd - jv, ord=np.inf) / max(
    np.linalg.norm(fd, ord=np.inf), np.linalg.norm(jv, ord=np.inf), 1e-300
)

steps = []
scaled = scaled0
for _ in range(20):
    r, jac, scaled = engine._transport_system(w, y_old, dt_hat, conductance, drive, jacobian=True)
    delta = np.asarray(spsolve(jac, -r), dtype=np.float64)
    step = float(engine.numerics['transport_newton_initial_step'])
    while step >= float(engine.numerics['transport_newton_min_step']) - 1e-15:
        candidate = w + step * delta
        _, _, candidate_scaled = engine._transport_system(candidate, y_old, dt_hat, conductance, drive, jacobian=False)
        if candidate_scaled < scaled:
            w, scaled = candidate, candidate_scaled
            steps.append(step)
            break
        step *= 0.5

print(json.dumps({
    'classification': 'NON_SCIENTIFIC_DIAGNOSTIC_DO_NOT_CITE_AS_ORACLE_OR_METHOD_EVIDENCE',
    'active_cells': int(w.size),
    'initial_scaled_residual': scaled0,
    'final_scaled_residual_after_20': scaled,
    'accepted_steps': steps,
    'fd_directional_relative_inf': fd_relative_inf,
}, indent=2, sort_keys=True))
'@
& .\.venv\Scripts\python.exe -c $NonScientificDiagnostic
```

Expected diagnostic values are `12` active cells, initial residual `1.5106745331996967e-3`, final residual `1.4406930175716191e-9`, twenty accepted `0.5` steps, and finite-difference discrepancy `1.7339861280712171e-10`. These values diagnose a frozen solver contract on a reduced fixture; they are not a scientific benchmark result.

## 8. Reproduce the final figures without a production rerun

The figure package has its own [source manifest](figures/source-manifest.json), plot-ready CSV files under [`figures/data/`](figures/data/), and a single [generator](figures/generate_figures.py). The recorded render environment was CPython `3.12.4`, NumPy `1.26.4`, h5py `3.11.0`, and Matplotlib `3.8.4`; those exact versions and all carrier/output hashes are stored in the source manifest. From the repository root, use a local Python environment providing those imports:

```powershell
python paper\figures\generate_figures.py
```

The generator re-extracts Q0 from the frozen H5 carrier, verifies the source hashes, and recomputes only the explicitly `NON_SCIENTIFIC_DIAGNOSTIC` Newton fixture used in Figure 5. It does not launch a production solve or write the experiment ledger. In the recorded render environment, the final source-manifest SHA256 is `15ADA73819AA8EAA493B324ADE79F3CC7FEF142C84A458F5BDA25F65CD3DD6BF`.

## 9. Expected stopping state

After the steps above, no new file should exist under `docs/experiment/intents`, `docs/experiment/intent_claims`, `docs/experiment/manifests`, or `outputs/runs`. The scientific disposition remains `SYN_EDT_2D_V1_NUMERICAL_CONTRACT_NO_GO`, with no oracle, event, PINN, OOD, or formal evidence.
