## S12. Limited material mapping and remaining validation

The application inspiration is the coupled wall-cell PCM model of Miquel et al. [8]. Its material is Ge-rich GST, not an oxide. The mapping below identifies shared modeling roles and concrete omissions; it does not transfer its calibrated parameters into this synthetic calculation. The evidence label for the present physical coefficients remains a frozen numerical design, not experimental validation.

| Component | Present numerical object | Source relationship and missing evidence |
| --- | --- | --- |
| State variables | Reduced T and one bounded scalar phase φ | [8] couples multiple phases and composition. Our φ is not a calibrated crystallinity, metallic fraction or chemical population. |
| Geometry and boundaries | Two-dimensional wall cell, top electrode, grounded partial bottom, Robin cooling | [8] supplies device-model motivation; dimensional dimensions, contact resistances, material interfaces and packaging are not identified here. |
| Conductivity | Smooth exp[0.25T + log(8)φ²(3-2φ)] | The feedback role is shared; this formula and its coefficients are synthetic. Measured phase/temperature-dependent transport is absent. |
| Heat and latent contribution | Fixed reduced diffusivity, cooling and latent ratio 0.05 | A quantitative device claim requires mutually consistent heat capacity, conductivity, latent heat and boundary calibration. None is inferred from the present fits. |
| Phase kinetics | A scalar nonconserved temperature-driven phase equation | It omits multi-phase nucleation/composition and oxide electronic/structural order parameters. Theoretical isothermal VO2 switching [14] is a counterexample to assigning every oxide transition solely to our Joule-heating route. |
| Validation quantities | Synthetic current, power, local heating and phase events | Experimental switching trajectories, optical/structural phase observations and material parameters would require independent validation. Algebraic current balance does not provide it. |

Kaltenbacher [13] treats reduced and all-at-once formulations in inverse problems; that is useful context for eliminating a state variable, not a convergence theorem for this neural representation. PINN-Proj [12] enforces specified integral constraints by projection, whereas the present electrical layer solves a local quasi-static boundary problem coupled to T and φ. Neither source makes elimination or differentiable constraints novel in themselves. The contribution must rest on the explicitly defined interface and matched reconstruction evidence.

The current revision includes a separately authorized clean-parent thermal/phase-residual ablation; its outcome must be reported from completed evidence rather than inferred from the historical head experiment. Both temporal- and spatial-reference sensitivity have been executed. Neither establishes geometry transfer, material calibration, arbitrary pulse generalization or predictor-readout grid independence.
