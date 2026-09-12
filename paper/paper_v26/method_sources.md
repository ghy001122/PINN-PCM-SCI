# Sources and adaptations

| Component | Source / role | Adaptation in this execution |
|---|---|---|
| PINN, importance sampling, phase-field approaches | Inherited bibliography and paper_v24/paper_v25 source notes | Historical scientific context; not re-claimed as new |
| Adam/L-BFGS and temperature Fourier adapter | Inherited S1 implementation; Rathore et al. and Tancik et al. in references.bib | Adapter retained unchanged; no new optimizer-method claim |
| V L-BFGS continuation | Installed PyTorch 2.5.1 LBFGS; existing project rollback wrapper | Restore compatible V history, retain final T, stop only at an accepted gate; tests exercise real optimizer behavior |
| Contact-current / power split | Algebra applied to the existing harmonic FV face readout | Evaluate own boundary trace and AD; retain signed cross term and all official metrics |
| B_logit_waveform_contact | Existing SciPy PCHIP + linear-space waveform baseline | Insert known heater endpoints without new observations or training; no insulation-exactness claim |

The two user-supplied Deep Research reports are advisory provenance stored verbatim as TXT under the run inputs. Their internal chat citation markers are not used as manuscript citations or evidence. New quantitative claims are supported by this execution's saved outputs. The original report's proposed 1/h trace amplification is a conditional algebraic interpretation, not a newly observed refinement experiment.

PyTorch and SciPy are used through installed APIs; no external implementation was silently imported, installer run, or source priority claimed. Prior manuscript references are preserved in [references.bib](references.bib).

