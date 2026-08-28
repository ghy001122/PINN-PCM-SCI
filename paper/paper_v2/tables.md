# Final tables

## Table 1. Evidence identities and transfer boundaries

| Source/asset | Primary role | Reproduction identity used | Transfer boundary | PHK-V2 result |
|---|---|---|---|---|
| Sharp-PINNs paper | phase-field domain anchor | paper modules only: staggered AC/CH, RFF, modified MLP, hard constraint, gradient-norm weighting | corrosion/KKS constraints require `A′`; paper and repository recipes remain separate | source audit + module smoke; no paper metric |
| Sharp repository | implementation reference | commit `4b7029e...` | GPL-3.0; isolated comparator only | CPU module smoke passed |
| PF-PINNs | sampling/NTK support control | commit `a25f75b...` | GPL-3.0; support expansion must be compute-matched | CPU module smoke passed |
| PirateNet/jaxpi2 | strong general architecture | jaxpi2 commit `77a5c13...` | minimal Apache-2.0 architecture smoke; original jaxpi Penn code not redistributed | x64 CPU architecture-only smoke passed |
| adaptive pseudo-time | KC falsification control | paper specification + fixed jaxpi2 identity | changes optimization homotopy, not physical time; must be independently budgeted | not reached |
| Miquel et al. | wall-cell and causal-chain inspiration | literature only | confidential/internal properties and no open code preclude exact reproduction | topology inspiration only |

## Table 2. Frozen reduced benchmark contract

| Category | Frozen PHK-V2 value |
|---|---|
| Domain | $(x,z)\in[-1,1]\times[0,1]$, $t\in[0,2]$ |
| Cycles | two identical unit-period unipolar trapezoids, amplitude 0.75 |
| Fields | potential $v$, reduced temperature $\theta$, phase fraction $\phi$ |
| Electric equation | $\nabla\cdot(\sigma(\theta,\phi)\nabla v)=0$ |
| Heat equation | $\partial_t\theta+L_r\partial_t\phi=\alpha\nabla^2\theta-\gamma\theta+G\sigma|\nabla v|^2$ |
| Phase equation | $\partial_t\phi=M(\theta)[\epsilon^2\nabla^2\phi-\partial_\phi W(\phi,\theta)]$ |
| Spatial discretization | cell-centered finite volume; harmonic electric faces |
| Time/coupling | backward Euler; fixed-point electric/thermal/phase; final residual recheck |
| Resolutions | $40\times20$, $80\times40$, $120\times60$ plus medium half-$\Delta t$ |
| Object identity | transparent dimensionless engineering benchmark; not material calibrated |

## Table 3. Qualification ladder

| Intent | Configuration | Status | Evidence |
|---:|---|---|---|
| 1 | manufactured operators | completed | implementation checks pass; no scientific field result |
| 2 | zero drive, medium | completed | all zero-drive hard guards pass |
| 3 | nominal coarse | completed | hard guards pass; event contract fails |
| 4 | nominal medium | completed | hard guards pass; event contract fails |
| 5 | nominal fine | completed | hard guards pass; event contract fails |
| 6 | nominal medium half-$\Delta t$ | completed | hard guards pass; event contract fails |
| 7 | exact fine replay | completed | all six component differences zero |
| 8 | Joule gain off | completed | bounded Joule causal effect established |
| 9 | phase-conductivity feedback off | failed/consumed | phase Newton line search reached frozen minimum step |
| 10–12 | latent-off, wide-heater, narrow-interface | not reached | stopped by frozen sequential ladder |

## Table 4. Nominal event diagnostics

| Resolution | First event time | Cycle-1 peak ROI fraction | Cycle-1 recovery | Cycle-2 pre-pulse ROI fraction | Cycle-2 event | Peak drift |
|---|---:|---:|---:|---:|---|---:|
| coarse | 0.212100 | 0.363636 | 0.227273 | 0.280992 | missing | 1.409091 |
| medium | 0.217800 | 0.345041 | 0.233533 | 0.264463 | missing | 1.586826 |
| fine | 0.219908 | 0.342516 | 0.238606 | 0.259871 | missing | 1.587131 |
| medium half-$\Delta t$ | 0.219467 | 0.345041 | 0.221557 | 0.268595 | missing | 1.568862 |
| fine replay | 0.219908 | 0.342516 | 0.238606 | 0.259871 | missing | 1.587131 |

Frozen thresholds: event ROI fraction 0.02; minimum recovery 0.7; maximum cycle-peak relative drift 0.2; two complete cycles required.

## Table 5. Convergence and replay component differences

Component order: phase-field ROI RMS, temperature ROI RMS, current-trace RMS, event time, phase-region symmetric difference, recovery.

| Comparison | Phase | Temperature | Current | Event | Region | Recovery |
|---|---:|---:|---:|---:|---:|---:|
| coarse–medium | 0.115296 | 0.0130288 | 0.0121576 | 0.00403051 | 0.0113184 | 0.0446725 |
| medium–fine | 0.0440896 | 0.00427422 | 0.00384497 | 0.00149082 | 0.00381858 | 0.0182278 |
| medium–half-$\Delta t$ | 0.0242407 | 0.00318648 | 0.00267207 | 0.00117851 | 0.00198254 | 0.00858333 |
| fine–exact replay | 0 | 0 | 0 | 0 | 0 | 0 |

## Table 6. Compute and claim accounting

| Item | Value |
|---|---:|
| Process CPU seconds | 1318.71875 |
| Process CPU core-hours | 0.3663107639 |
| Summed single-thread wall seconds | 1339.3720109 |
| Completed intents | 8 |
| Failed/consumed intents | 1 |
| Not-reached intents | 3 |
| Rescue/replacement intents | 0 |
| PINN training runs | 0 |
| GPU/formal runs | 0 |
| Neural floor seal | not created |

