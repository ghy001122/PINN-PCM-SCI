# Q-POP IMT PhysicalContract source audit, 2026-08-21

## Status

- `VERIFIED_SOURCE_IDENTITY`: CPC v1 archive `9e0814d5...ced16`, embedded Git commit `6047117bb9f40355db260aae59ec427de2050b94`, `qpop-imt.py` SHA-256 `753dec7c...f5b5f`, MIT license.
- `VERIFIED_SOURCE_SEMANTICS`: the executable solves one coupled seven-unknown 2D field/circuit system; the items below are transcribed from the frozen source and canonical author input.
- `SUPPORTED_INTERPRETATION`: the displayed interior strong forms are the integration-by-parts counterparts of the executable weak forms and are the equations implemented by the transparent PyTorch PINN.
- `UNKNOWN`: full-case reproduction, discretization convergence, conservation tolerance, oracle error floor and final numerical qualification. Therefore this is a source-audited draft, not the immutable G3 `PhysicalContract`.

## Independent unknowns

The mixed finite-element state is

`(eta, mu, gamma_e, gamma_h, phi, T, Ib)`

with six spatial P1 fields and one global R0 circuit current. `n` and `p` in the emitted files are derived occupancies, not independent unknowns:

`n = NC F(gamma_e) UCVOL`, `p = NV F(gamma_h) UCVOL`.

## Interior equations

On each smooth protocol segment, the continuous strong-form counterpart is:

1. Structural Allen-Cahn equation

   `eta_t + 2 KN dfb_deta(T,eta,mu) - KN KAPPAN Laplacian(eta) = 0`.

2. Electronic-order equation

   `mu_t + 2 KU [dfb_dmu(T,eta,mu) + CHI mu (ne + nh - 2 ni)] - KU KAPPAU Laplacian(mu) = 0`.

3. Electron and hole continuity equations

   `d(ne)/dt + div(je) - R_eh = 0`,

   `d(nh)/dt + div(jh) - R_eh = 0`,

   where `R_eh = KEH0 mu^2 (ne_eq nh_eq - ne nh)`.

4. Poisson equation

   `-Laplacian(phi) - (ECHARGE/PERMITTIVITY)(nh-ne) = 0`.

5. Heat equation

   `CPV T_t - Q_Joule + dU/dt - THETA Laplacian(T) + (HTRAN/Lz)(T-Ts) = 0` in 2D,

   where `dU/dt = dfb_deta(0,eta,mu) eta_t + dfb_dmu(0,eta,mu) mu_t` and `Q_Joule` is the executable anisotropic carrier-flux quadratic form.

The carrier fluxes are exactly

`je = -ne (ME/ECHARGE) grad(KB T gamma_e + CHI mu^2/2 - ECHARGE phi)`,

`jh = -nh (MH/ECHARGE) grad(KB T gamma_h + CHI mu^2/2 + ECHARGE phi)`.

## Initial, boundary and circuit contract

- Canonical geometry: `Lx=100 nm`, `Ly=40 nm`, `Lz=20 nm`; crossed triangular `100 x 40` mesh; 2D mode.
- Canonical protocol: 9 V source, 500 kOhm series resistor, zero capacitor, 10 ns voltage ramp, nominal terminal time 2000 ns.
- Initial fields: `eta=1.119`, `mu=-1.293`, `T=300 K`; carrier gammas are intrinsic-equilibrium values; `phi` is linear through the film from the computed initial device voltage to zero; `Ib` is the corresponding initial circuit current.
- `eta` and `mu` use the executable Robin interaction with surroundings on the full boundary.
- Electron/hole electrochemical-potential conditions are enforced on `y=0` and `y=Ly` through the executable Nitsche terms; lateral carrier flux is natural zero.
- `phi=0` on `y=Ly`; the bottom boundary couples `phi`, `Ib`, the ramped drive, optional capacitance and integrated current density.
- Thermal loss is the 2D volumetric `HTRAN/Lz` term; remaining thermal boundary flux is natural zero.
- The physical breakpoint is the 10 ns drive-ramp end. Strong residual sampling excludes the breakpoint and evaluates one-sided segments.

## Evaluator and evidence boundary

- `ABSENT / OFFICIAL_EVALUATOR_NOT_PROVIDED`: neither the CPC package nor its source supplies an official benchmark scoring script.
- Project metrics are therefore a frozen project evaluator only. The structural primary is cycle-equal phase-region symmetric difference; the device diagnostic is the full reported voltage-drop trajectory error.
- CPC-bundled output ends at 512.0793 ns despite a 2000 ns input and lacks a native completion trailer. It is admissible only as an explicitly unqualified development oracle.
- Native run `20260821T021330Z-smoke-g2-qpop-authorcase-001` reached 252 accepted steps and 152.8157 ns, then hit its frozen 3600 s timeout. It establishes executable nonlinear behavior, not full-case reproduction or G3 qualification.

## Executable implementation mapping

- Frozen parameter and constitutive implementation: `pinn_pcm_sci/qpop_physics.py`.
- Full seven-unknown strong residual, IC/BC/circuit implementation: `pinn_pcm_sci/qpop_pinn.py`.
- Structural-only clock, complete derivative pullback and graph isolation: `pinn_pcm_sci/kinetics_clock.py`.
- Development runner uses no Q-POP transient field labels during training; the artifact is opened only for post-training disk prediction/evaluation.
