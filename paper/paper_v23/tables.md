# PHK-V2.3 advisor-draft tables

## Table 1. Frozen LF3 baseline evidence identity

| Item | Value |
|---|---|
| Task | `PHK_V23_LF3_MEASURE_DECOUPLED_STARTUP_SCALED_PHASE_LATENT_CARRIER_PILOT_EXECUTE` |
| Activation commit | `97a5b74cf79332115397d07c83b400c942859fb4` |
| Source identity | `LF3-BUNDLE-93BDB1F29B95BA757FC8756509E8C257FC296EE0DE6F04451E6E363E2D4BF63D` |
| GPU / dtype / seed | Tesla V100-PCIE-32GB / FP64 / 17 |
| T0 / P0 updates | 1200 / 0 |
| T0 stream SHA-256 | `6E9957E861BE0FD10E19A1585635C7B2C323077D89908159B1736734FB548F28` |
| Run-summary SHA-256 | `335DBF2194BA62C89E3E607941BA92B5FA14BB533B679330A7234A4466455D12` |
| Local-adjudication SHA-256 | `BB45AB4FAFE0A0ADC8E4F21A35E96E3A05B233594933C04AC0F3C58401B23378` |
| Outcome | `LF3_CARRIER_NOT_ESTABLISHED` |
| Candidate | none |
| Stress | `TWO_STRESS_REFERENCES_SEALED_UNREAD` |

## Table 2. Executed recovery ladder

| Stage | Key intervention | Phase maximum | Event outcome | Dominant failure or boundary |
|---|---|---:|---|---|
| V2.2R strong raw | Scratch full physics | 0.02999 | No event | Cold-state collapse despite loss decrease |
| LF0 B0 | Medium output supervision | 0.47758 | No threshold crossing | Potential maximum-principle invalid |
| LF1 B0 | Range-preserving potential + event-balanced output teacher | 0.75420 | Two cycles | Active mass 5.27/5.86×; low precision |
| LF1 final | Persistent replay + full physics | 0.66447 local | Two cycles | Physics decreased, phase/T preservation failed |
| LF2 M0 | Target-measure field losses + stochastic inequality AL | 0.02995 | No event | Lower field error but event erased |
| LF3 T0 | V/T target measure + 14-class phase-logit teacher | 0.99119 | Two localized cycles | Recall 0.806/0.769 below 0.90 |
| LF3 P0 | Conditional label-free physics | — | Not run | Correctly not triggered by T0 gate |
| LF4 DEV-G | Equal-budget global extra MSE | 0.98743 | Two cycles | Timing failed in both cycles |
| LF4 DEV-M | Teacher-interface-band MSE | 0.99222 | Two cycles | Boundary exposure supported; cycle-1 timing failed |
| LF4 DEV-C | Two-sided threshold BCE | 1.00000 | Two cycles | Timing/recall passed; phase error inflated |
| LF4 P0 | Conditional label-free physics | — | Not run | No development arm passed every entry condition |

The stages are a sequential diagnostic program, not a simultaneous factorial
benchmark. Historical comparisons do not isolate the LF3 logit teacher alone.

## Table 3. Full-medium LF3-T0 carrier gate

| Check | Frozen requirement | Cycle 1 / global | Cycle 2 | Result |
|---|---:|---:|---:|---|
| All values finite | true | true | true | Pass |
| Potential maximum principle | max excess ≤ `1e-6`, fraction 0 | 0 | 0 | Pass |
| Phase range | `[-1e-10, 1.0000000001]` | min `2.67e-9`, max `0.991187` | same field | Pass |
| Two events | required | present | present | Pass |
| Event-time error | ≤ 0.005 | 0.00485 | 0.00170 | Pass |
| Recall | ≥ 0.90 | 0.805842 | 0.768603 | **Fail / Fail** |
| Precision | ≥ 0.80 | 0.907157 | 0.866053 | Pass / Pass |
| Active-mass ratio | [0.80, 1.20] | 0.888316 | 0.887477 | Pass / Pass |
| ROI peak fraction | ≥ 0.02 | 0.072314 | 0.067149 | Pass / Pass |
| Full-domain peak | ≤ 0.45 | 0.021875 | 0.020313 | Pass / Pass |
| Outside-ROI peak | ≤ 0.10 | 0 | 0 | Pass / Pass |
| Recovery | ≥ 0.70 | 1.0 | 1.0 | Pass / Pass |

Only the two recall checks failed. The machine gate is conjunctive; the result
is therefore not a carrier pass.

## Table 4. Full-medium weighted field errors

| Role | Potential | Temperature | Phase | Phase ratio to LF1-B0 |
|---|---:|---:|---:|---:|
| LF1-B0 | 0.000295493 | 0.0112203 | 0.0566884 | 1.0000 |
| LF2-M0 | 0.0000759726 | 0.000734920 | 0.0154964 | 0.273361 |
| LF3-T0 | 0.0000714768 | 0.000711189 | 0.00187510 | 0.0330773 |

Lower weighted error did not substitute for event competence: LF2 had lower
errors than LF1 yet no event, while LF3 still failed recall despite a further
phase-error reduction.

## Table 5. Nominal extra-fine local evaluation

| Role | Frozen event guard | Phase ROI RMS | Phase symmetric difference | T ROI RMS | Current nRMSE | Potential RMS |
|---|---|---:|---:|---:|---:|---:|
| direct `LF_ONLY` | Pass | 0.00657038 | 0.000349531 | 0.00180069 | 0.00352214 | 0.000576128 |
| LF1-B0 | Pass | 0.163446 | 0.0174370 | 0.0545925 | 0.256194 | 0.0120797 |
| LF1-final | Pass | 0.214459 | 0.0205948 | 0.0793024 | 0.138757 | 0.0319292 |
| LF2-M0 | Fail (6) | 0.110564 | 0.0051500 | 0.0175980 | 0.146374 | 0.00616749 |
| LF3-T0 | Pass | 0.0390008 | 0.00202578 | 0.0173618 | 0.137297 | 0.00599662 |

The frozen evaluator's event guard is less stringent than the LF3
teacher-relative carrier gate. Its pass does not override the full-medium
recall failure.

## Table 6. Three-level adjudication

| Level | Question | Observed result | Claim status |
|---|---|---|---|
| 1. Carrier | Is T0 valid and quantitatively event-competent? | Failed recall in both cycles | `NOT_ESTABLISHED` |
| 2. PINN pilot | Does label-free P0 reduce physics objective while preserving T0? | P0 not triggered | `NOT_TESTED` |
| 3. Candidate | Does eligible P0 add value relative to direct `LF_ONLY`? | Not reached | `NOT_TESTED` |

## Table 7. Current paper evidence versus a positive methods submission

| Evidence item | Advisor draft | Positive methods submission minimum | Current state |
|---|---|---|---|
| Executed failure analysis | Required | Required | Available |
| Legal, localized neural event | Required | Required | Near-pass; strict recall failed |
| PINN-specific P0-vs-T0 Pareto | Optional for negative draft | Required | Not run |
| Direct `LF_ONLY` comparison | Required | Required | Available; large gap remains |
| Matched output-phase ablation | Optional if no component claim | Required for latent claim | Not authorized/run |
| Multiple seeds | Limitation stated | Required | Not run |
| Formal OOD/stress | Limitation stated | Required | Sealed/unread |
| Continuum/material/experimental evidence | Excluded | Depends on target claim | Not available |

## Table 8. Frozen LF4 execution identity

| Item | Value |
|---|---|
| Task | `PHK_V23_LF4_THRESHOLD_ALIGNED_INTERFACE_BAND_MECHANISM_AND_CONDITIONAL_PHYSICS_PILOT_EXECUTE` |
| Activation commit | `5dbde1d210b6f2ff15d0f341ee316e59b49a1074` |
| Source identity | `LF4-BUNDLE-EF532BCCF7FAC4482BEBD56A49DFAFE2D5F2FD4B2043540BD4414B6668CA644F` |
| GPU / dtype / seed | Tesla V100-PCIE-32GB / FP64 / 17 |
| DEV-G / DEV-M / DEV-C updates | 400 / 400 / 400 |
| P0 updates | 0 (`NOT_RUN_NO_DEVELOPMENT_ENTRY`) |
| Run-summary SHA-256 | `692833FA52787AE9B204A64AC84D11E9AA15352459498EF3A2D066F7CB313ED2` |
| Local-adjudication SHA-256 | `4301BEF71B49B17EA0EA164314A0FF5F9CBF11367C2EA92AF0509D75F0D94289` |
| Outcome / candidate | `LF4_NO_DEVELOPMENT_ENTRY` / none |
| Stress | `TWO_STRESS_REFERENCES_SEALED_UNREAD` |

## Table 9. Matched LF4 development endpoints

| Arm | Extra supervision | Recall C1/C2 | Precision C1/C2 | Mass ratio C1/C2 | Timing error C1/C2 | Phase weighted MSE | Entry result |
|---|---|---:|---:|---:|---:|---:|---|
| DEV-G | global normalized logit MSE | 0.8402 / 0.8194 | 0.8923 / 0.8674 | 0.9416 / 0.9446 | 0.01387 / 0.00616 | 0.001309 | Fail: both timing gates |
| DEV-M | identical-coordinate interface-band MSE | 0.9373 / 0.9093 | 0.9092 / 0.9462 | 1.0309 / 0.9610 | 0.01053 / 0.00500 | 0.001210 | Fail: cycle-1 timing |
| DEV-C | identical band, two-sided BCE-with-logits | 0.9416 / 0.9755 | 0.9133 / 0.9380 | 1.0309 / 1.0399 | 0.00190 / 0.00250 | 0.029667 | Fail: phase error |

All arms were finite, potential-admissible, phase-range valid, and preserved
the frozen potential/temperature heads bitwise. DEV-M improved minimum recall
over DEV-G by `0.08984`, exceeding the frozen `0.03` mechanism margin while
preserving precision, mass, timing, locality, recovery, and V/T quality.

## Table 10. LF4 attribution and claim ladder

| Question | Frozen comparison | Result | Claim status |
|---|---|---|---|
| Does teacher-interface exposure add value? | DEV-M − DEV-G, ΔRmin ≥ 0.03 plus quality preservation | ΔRmin `+0.08984`; pass | `BOUNDARY_EXPOSURE_SUPPORTED` |
| Does threshold-aligned BCE add value on the same points? | DEV-C − DEV-M, ΔRmin ≥ 0.03 plus quality preservation | ΔRmin `+0.03232`, but recovery/field quality not preserved | Not supported |
| Is an eligible carrier established? | All P0-entry checks conjunctively | No arm passed all checks | `LF4_NO_DEVELOPMENT_ENTRY` |
| Does label-free physics add a Pareto improvement? | P0 vs selected carrier | P0 not run | Not tested |
| Is there a direct-`LF_ONLY` candidate signal? | Full candidate gate | Not reached | No candidate |
