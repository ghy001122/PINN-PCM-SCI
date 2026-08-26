# EAF-KC-v1 experimental-front source audit

- `audit_date`: `2026-08-21`
- `scope`: experiment-timescale constraints for a bounded two-dimensional electrothermal structural-front benchmark
- `source_policy`: primary sources only
- `scientific_use`: source/admissibility constraints only; no experimental image, phase map, or transient trace may be used as a PINN training label or as the formal numerical oracle
- `exact_device_replication_status`: `BLOCKED_BY_UNKNOWN_LATERAL_AND_CONTACT_GEOMETRY`
- `bounded_benchmark_status`: `SOURCE_AUDIT_PASS_WITH_EXPLICIT_A_PRIME`

## 1. Source set and provenance

| Source | Pinned identity | Availability and license | Allowed role |
|---|---|---|---|
| Pofelski et al., *Switching speed limits in electrically driven VO2 structural Mott-Peierls transition* | Nature Communications 17, 3139 (2026), DOI [`10.1038/s41467-026-69904-0`](https://doi.org/10.1038/s41467-026-69904-0), version of record 2026-04-01 | Article and included material are [CC BY 4.0](https://www.nature.com/articles/s41467-026-69904-0#rightslink) unless a separate credit states otherwise | Direct experimental facts and admissibility anchors only |
| Publisher Supplementary Information | [`41467_2026_69904_MOESM1_ESM.pdf`](https://static-content.springer.com/esm/art%3A10.1038%2Fs41467-026-69904-0/MediaObjects/41467_2026_69904_MOESM1_ESM.pdf), 1,827,775 bytes, SHA-256 `4855e06d5c54577e40229dd6afe0d52a931b1d17155f6830e95d14bf05435013` | Supplement to the CC BY article; no separate contrary credit was found | Device cross-section, front-extraction method, image-processing caveats |
| Author UTEM raw data | Zenodo version DOI [`10.5281/zenodo.18554592`](https://doi.org/10.5281/zenodo.18554592), concept DOI `10.5281/zenodo.18554591` | Open dataset, `CC BY 4.0`; `UTEM_VO2_raw_data.zip`, 47,084,023 bytes, MD5 `a16e2c38a5194c1e9713412125c70fbc`, as recorded by the [Zenodo record API](https://zenodo.org/api/records/18554592) | Traceability and optional secondary visualization audit; prohibited as training labels or oracle fields |
| Author 4D-STEM phase-map code/data | Concept DOI [`10.5281/zenodo.14767722`](https://doi.org/10.5281/zenodo.14767722), resolved version DOI [`10.5281/zenodo.14767723`](https://doi.org/10.5281/zenodo.14767723) | Open computational notebook, `CC BY 4.0`; `CNN_4dstem_VO2.zip`, 313,569,691 bytes, MD5 `2aa04be5116fc9f263850a5d7166a643`, as recorded by the [Zenodo record API](https://zenodo.org/api/records/14767723) | Audit of the paper's GHz phase-map processing only; not a front oracle, evaluator, or label source |
| Q-POP-Modules official repository | `main` commit [`bcfad845e79cd5d0f827af8556d5029dcf500b0d`](https://github.com/DOE-COMMS/Q-POP-Modules/commit/bcfad845e79cd5d0f827af8556d5029dcf500b0d), committed 2025-11-13 | [MIT license](https://github.com/DOE-COMMS/Q-POP-Modules/blob/bcfad845e79cd5d0f827af8556d5029dcf500b0d/LICENSE) | Source-pinned candidate constitutive terms and material scales, not the experimental oracle |

The Nature article states that all supporting UTEM videos are supplied as supplementary movies and that the pre-video raw data and the Figure S3 phase-map code/data are available at the two Zenodo DOIs above ([Data and Code availability](https://www.nature.com/articles/s41467-026-69904-0#data-availability)).

## 2. Evidence classes

- `A`: a fact stated or displayed by a primary source without changing its scientific meaning.
- `A_PRIME`: a bounded project adaptation that is motivated by `A` but is not claimed to reproduce the experimental apparatus exactly.
- `ENGINEERING`: a numerical, discretization, training, or evaluation choice made by this project; it has no experimental-source status.
- `UNKNOWN`: not uniquely recoverable from the audited primary sources. It must not be guessed or silently promoted to `A`.

## 3. Direct experimental facts (`A`)

### 3.1 Material and device geometry

| Frozen fact | Status | Primary evidence and scope |
|---|---|---|
| VO2 film thickness is approximately `600 nm` | `VERIFIED / A` | The device description and Methods both give an approximately 600 nm textured polycrystalline VO2 film on sapphire ([article, device description and Methods](https://www.nature.com/articles/s41467-026-69904-0)). This is the film-depth direction, not a sourced lateral device width. |
| Substrate is R-plane sapphire | `VERIFIED / A` | The film-synthesis Methods identify an R-plane sapphire substrate ([article Methods](https://www.nature.com/articles/s41467-026-69904-0#Sec8)). |
| The UTEM specimen is a cross-sectional two-terminal device with lateral electrodes | `VERIFIED / A` | The article describes lateral electrodes and cross-sectional observation; Supplementary Fig. S1 shows VO2 over sapphire with electrodes on the top surface ([article](https://www.nature.com/articles/s41467-026-69904-0), [Supplementary Fig. S1](https://static-content.springer.com/esm/art%3A10.1038%2Fs41467-026-69904-0/MediaObjects/41467_2026_69904_MOESM1_ESM.pdf)). |
| Electron-transparent lamella thickness is approximately `150 nm` out of the cross-sectional image plane | `VERIFIED / A` | The fabrication Methods state that the lifted-out sample was left about 150 nm thick ([article Methods](https://www.nature.com/articles/s41467-026-69904-0#Sec9)). This is not the 600 nm VO2 depth. |
| A Ti layer of approximately `100 nm` was deposited before lift-out; the specimen was connected to Ti/Au chip lines using carbon/Pt deposition | `VERIFIED / A` | Fabrication Methods and Supplementary Fig. S1 identify these layers and connections ([article Methods](https://www.nature.com/articles/s41467-026-69904-0#Sec9), [Supplementary Fig. S1](https://static-content.springer.com/esm/art%3A10.1038%2Fs41467-026-69904-0/MediaObjects/41467_2026_69904_MOESM1_ESM.pdf)). |
| The chip has a `10 micrometre` SiN membrane window | `VERIFIED / A` | Stated in the device-fabrication Methods ([article Methods](https://www.nature.com/articles/s41467-026-69904-0#Sec9)). The window size is not the active VO2 lateral width. |
| Exact lateral electrode gap, electrode widths, contact footprint coordinates, and modeled lateral domain width | `UNKNOWN` | The text and supplementary scale-bar images establish topology but do not provide a unique numerical layout. Measuring a raster figure would not turn these quantities into sourced dimensions. This blocks exact-device replication. |

### 3.2 Electrical protocol and observation timing

| Frozen fact | Status | Primary evidence and scope |
|---|---|---|
| Low-frequency experiment uses a `1 MHz` periodic excitation | `VERIFIED / A` | The low-frequency Methods identify the synchronized 1 MHz sample excitation ([article Methods](https://www.nature.com/articles/s41467-026-69904-0#Sec11)). The period is therefore 1 microsecond. |
| Applied pulse amplitude was raised to `1.2 V`, with `5 ns` rise time | `VERIFIED / A` | Stated for the low-frequency sample excitation in the Methods ([article Methods](https://www.nature.com/articles/s41467-026-69904-0#Sec11)). This is the reported applied signal, not a separately de-embedded internal device voltage. |
| Audited pulse widths are `90 ns` and `150 ns`; `90 ns` is the reference front-imaging condition | `VERIFIED / A` | Methods report both widths, while Fig. 3 and Supplementary Fig. S8 associate the complete front sequence with the 90 ns condition ([article Fig. 3 and Methods](https://www.nature.com/articles/s41467-026-69904-0), [Supplementary Fig. S8](https://static-content.springer.com/esm/art%3A10.1038%2Fs41467-026-69904-0/MediaObjects/41467_2026_69904_MOESM1_ESM.pdf)). |
| Probe temporal resolution is `2.2 ns` | `VERIFIED / A` | Nucleation is reported as faster than the 2.2 ns probe resolution; the Methods also describe 2.2 ns electron-pulse generation ([article](https://www.nature.com/articles/s41467-026-69904-0)). |
| Each bright-field frame uses a `5 s` acquisition; the time series is stroboscopic and randomized in acquisition order | `VERIFIED / A` | Imaging Methods give the 5 s acquisition and state that time-series acquisitions were randomized; the article explains that each snapshot accumulates repeated cycles ([article Methods and imaging discussion](https://www.nature.com/articles/s41467-026-69904-0)). |
| Exact sequence of pump-probe delay points, or a uniform observational frame interval | `UNKNOWN` | The primary text says delays were controlled in nanoseconds and shows selected time stamps, but does not declare a single uniform delay grid. `2.2 ns` is temporal resolution, not evidence of a 2.2 ns frame interval. |

### 3.3 Structural event and front observables

| Frozen fact | Status | Primary evidence and scope |
|---|---|---|
| Monoclinic-to-rutile structural time constant is `36 +/- 10 ns` | `VERIFIED / A` | Estimated from the 1 MHz diffraction response in the approximately 400 nm selected area below the left electrode ([article Fig. 2 discussion](https://www.nature.com/articles/s41467-026-69904-0)). It is not a pointwise phase-field label. |
| Rutile-to-monoclinic recovery time constant is `107 +/- 21 ns` | `VERIFIED / A` | Estimated from the same diffraction experiment ([article Fig. 2 discussion](https://www.nature.com/articles/s41467-026-69904-0)). |
| Rutile nuclei appear immediately beneath the electrodes and then grow laterally and toward the substrate | `VERIFIED / A` | The bright-field sequence describes sub-electrode nucleation, growth, coalescence, stabilization, and dissolution ([article Fig. 3 discussion](https://www.nature.com/articles/s41467-026-69904-0)). |
| Main-text structural front velocity is `4.54 nm/ns` | `VERIFIED / A` | Obtained by fitting transition time versus film depth ([article Fig. 3d-e](https://www.nature.com/articles/s41467-026-69904-0)). Supplementary Fig. S5 reports `4.59 nm/ns` for the transposed fit and explains the approximately 1% difference with `R^2 = 0.9892`; the main-text `4.54 nm/ns` is the frozen reporting value ([Supplementary Fig. S5](https://static-content.springer.com/esm/art%3A10.1038%2Fs41467-026-69904-0/MediaObjects/41467_2026_69904_MOESM1_ESM.pdf)). |
| No structural transition is observed beyond approximately `400 nm`; the profile at `457 nm` remains monoclinic | `VERIFIED / A` | Directly stated in the depth-resolved front discussion ([article Fig. 3c-e](https://www.nature.com/articles/s41467-026-69904-0)). This is an observed range, not a hard material constant. |
| Growth is faster than dissolution, and increasing the width from 90 ns to 150 ns expands the filament farther toward the substrate and prolongs recovery | `VERIFIED / A` | Reported in the bright-field and duty-cycle sections ([article Fig. 3-4 discussion](https://www.nature.com/articles/s41467-026-69904-0)). |

### 3.4 Boundary physics and interpretation limits

| Frozen fact | Status | Primary evidence and scope |
|---|---|---|
| Electrodes and the nearby substrate act as heat sinks; geometry affects thermal dissipation | `VERIFIED / A` | Explicitly stated in the imaging and MRN discussions ([article](https://www.nature.com/articles/s41467-026-69904-0)). This supports explicit electrode/substrate thermal boundaries but does not supply numerical contact conductances. |
| Authors interpret propagation as predominantly non-equilibrium electrothermal, with the electric field assisting nucleation/growth | `SUPPORTED_INTERPRETATION / A` | This is the authors' evidence-based interpretation, not a directly measured decomposition ([article front-mechanism discussion](https://www.nature.com/articles/s41467-026-69904-0)). |
| Mechanical stress reaches the substrate within 2.2 ns but is not judged to dominate front propagation | `SUPPORTED_INTERPRETATION / A` | The article reports no measurable stress-transfer delay and distinguishes it from the slower structural front ([article](https://www.nature.com/articles/s41467-026-69904-0)). This justifies excluding mechanics only within the bounded first model, not a universal no-mechanics claim. |
| Exact electrode/VO2 and VO2/sapphire thermal contact conductances, electrical contact resistances, and internal voltage distribution | `UNKNOWN` | No unique values are given in the audited article or supplement. These quantities cannot be labeled experimental constants. |

## 4. Experimental image/data caveats

1. Bright-field contrast is not itself an absolute phase label. The article states that grain-dependent intensity prevents direct classification from absolute intensity and that a single threshold is unreliable because of noise ([article image-analysis discussion](https://www.nature.com/articles/s41467-026-69904-0)).
2. The displayed difference images and movies are mildly saturated for visualization. Supplementary Figs. S6-S8 additionally use registration, Gaussian/non-local-means denoising, noise-based thresholds, morphological closing, and filtering ([Supplementary Figs. S6-S8](https://static-content.springer.com/esm/art%3A10.1038%2Fs41467-026-69904-0/MediaObjects/41467_2026_69904_MOESM1_ESM.pdf)).
3. The Figure S3 CNN is a visualization classifier for GHz 4D-STEM maps, trained on 480 labeled/simulated patterns (2,816 after augmentation), with reported training accuracy 88.3%; its authors explicitly did not design it for generalization ([Supplementary Fig. S3](https://static-content.springer.com/esm/art%3A10.1038%2Fs41467-026-69904-0/MediaObjects/41467_2026_69904_MOESM1_ESM.pdf)). It is therefore not an official evaluator for EAF-KC-v1.
4. The paper's Mott Resistor Network uses arbitrary units and rescales space/time to experiment ([article MRN discussion](https://www.nature.com/articles/s41467-026-69904-0)). It must not be copied as a quantitative formal oracle.

**Frozen prohibition:** no raw UTEM frame, processed phase map, CNN output, extracted transient, or MRN state may enter the PINN loss, checkpoint selection, oracle construction, formal evaluator, or case split. Experimental observables may appear only as source-level scale constraints and independently reported secondary admissibility checks.

## 5. Q-POP facts and bounded use

At pinned commit [`bcfad845e79cd5d0f827af8556d5029dcf500b0d`](https://github.com/DOE-COMMS/Q-POP-Modules/tree/bcfad845e79cd5d0f827af8556d5029dcf500b0d), the official Q-POP README states that Q-POP-IMT is an open-source phase-field solver for coupled electrical and structural IMT responses. It exposes one structural order parameter `eta`, one electronic order parameter `psi`, a coupled Landau potential, structural/electronic transition time constants, gradient coefficients, carrier mobilities, heat capacity, thermal conductivity, and heat-dissipation parameters ([commit-pinned README](https://github.com/DOE-COMMS/Q-POP-Modules/blob/bcfad845e79cd5d0f827af8556d5029dcf500b0d/README.md)).

Classification for EAF-KC-v1:

- `A`: Q-POP's equations, units, parameter names, and values as implemented at the pinned commit.
- `A_PRIME`: transparently reducing Q-POP's full `eta/psi/carrier` system to a deterministic electrothermal structural equation, or transferring its material coefficients to the experiment-anchored geometry.
- `ENGINEERING`: any retuning of mobility, interface width, heat-transfer coefficients, electrical contact, or external circuit not already fixed by a cited source.

Q-POP remains a source-pinned constitutive/material reference. It is not evidence that EAF-KC-v1 reproduces the 2026 experiment, and its bundled `100 x 40 x 20 nm` DC example is not the geometry or drive protocol audited here.

## 6. Bounded mapping for the next gate

### 6.1 Permitted `A_PRIME` adaptations

The following adaptations are admissible only if frozen before solving and always labeled `A_PRIME`:

1. Use a two-dimensional cross-section with a `600 nm` VO2 depth because depth-resolved front propagation is the target observable.
2. Represent the top electrodes and bottom sapphire as distinct thermal-boundary segments. The topology is source-backed; their numerical dimensions and transfer coefficients are not.
3. Use the `1 MHz`, `90 ns`, 5 ns-rise experiment as the reference timescale while truncating a numerical off-window only after the modeled state has recovered. Such truncation is not the experimental protocol and must be recorded.
4. Use `36 +/- 10 ns`, `107 +/- 21 ns`, `4.54 nm/ns`, and the approximately 400 nm penetration range only as broad independent admissibility targets. They must not be optimization labels, checkpoint criteria, or formal method endpoints.
5. Use a deterministic independent PDE oracle even though the experimental system and the paper's MRN contain stochasticity. The paper's MRN fields and experimental frames remain outside the oracle.

### 6.2 Required `ENGINEERING` freeze before any solver run

These unresolved items must be chosen once, justified dimensionlessly, and recorded as engineering choices:

- lateral domain width and exact electrode gap/width/footprints;
- electrode, ambient, and sapphire thermal-transfer coefficients;
- electrical contact resistance and any series-resistor/capacitor circuit;
- structural mobility, gradient/interface coefficient, seed shape, and constitutive reduction from Q-POP;
- mesh, time step, nonlinear tolerances, output times, common probe grid, and front-connectivity definition;
- PINN architecture, collocation protocol, checkpoint selector, evaluator, and complete-case split.

None may be described as measured by Pofelski et al. unless a new primary-source audit supplies the missing value.

## 7. F0 disposition

- `VERIFIED`: source identity, article/supplement access, raw-data/code DOIs, licenses, 600 nm film depth, substrate/electrode topology, 1 MHz/1.2 V/5 ns-rise/90 ns protocol, structural time constants, 2.2 ns temporal resolution, front velocity/range, and the electrothermal heat-sink interpretation are directly traceable.
- `UNKNOWN`: exact lateral/electrode layout, contact thermal/electrical parameters, a uniform observation-delay grid, and a de-embedded device voltage.
- `BLOCKED`: an exact numerical replica of the experimental device cannot be defined from the audited sources.
- `PASS_WITH_BOUNDED_A_PRIME`: the sources are sufficient for an explicitly adapted experiment-timescale-constrained benchmark, provided the unknown quantities are frozen as `A_PRIME`/`ENGINEERING` before the feasibility calculation and the project makes no experimental-validation claim.

This audit does not qualify an oracle, validate a PINN, or support a KC effect. Those claims remain `UNKNOWN` until their respective numerical gates pass.
