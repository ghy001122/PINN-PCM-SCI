# Training-time electrical elimination improves sparse electrothermal phase-change reconstruction relative to a post-repaired soft PINN

Editorial source blocks for the 21 September revision. These blocks state existing findings and the frozen B1 question; they are not a completed B1 paper. Final abstract and conclusion will be composed after the fixed B1 endpoints are scored.

## Problem and supported contribution

We study how electrical constraints participate in reconstructing transient temperature and phase from prescribed field observations. The task is an offline, known-model reconstruction benchmark: geometry, coefficients, initial and boundary conditions, and the complete drive are supplied. Each of the two protocols is fitted separately. Its original observation set contains 28,875 positive-time locations and 86,625 noiseless scalar labels for potential, temperature and phase. These locations constitute 1.8046875% of the 3,200 × 500 positive-time carrier positions; at each observation time, 231 spatial locations cover 7.21875% of the carrier cells. Noiseless labels still inherit the carrier's numerical discretization error. These experiments do not establish a minimal sensor arrangement, zero-shot transfer or calibrated material reconstruction.

The contribution is a specific coupling interface and a matched test of its reconstruction benefit. Neural temperature and phase determine a grounded finite-volume electrical solution. The same face resistances determine local Joule deposition in the thermal balance. Providing the same final electrical solution to the soft and interpolation controls tests whether final electrical repair explains the measured differences. The existing experiments support this training configuration relative to the tested soft comparator. They do not establish a new implicit-differentiation principle or an independent benefit from the additional thermal/phase interior residuals.

Differentiable constrained learning already includes solver-in-the-loop correction [3], hybrid FEM–NN models [4], PDE-constrained layers [15], and modular implicit differentiation [5]. Related approaches enforce hard boundary maps or constrained optimization [16], prescribed integral targets [12], differential-algebraic constraints [17], and local discrete projections [18]. Here the transient T/φ states remain neural, while the full grounded electrical subproblem is eliminated. This identifies a physical interface adaptation and its controlled comparison; it does not imply general superiority over all penalty or constrained-optimization methods. The method and information differences are documented in [the source verification](source-verification.md).

## Initial and boundary interpretation

The prescribed initial phase is

$$\phi_0(x,z)=0.02+0.01\exp\left[-\frac{1}{2}\left((x/0.18)^2+((z-0.12)/0.10)^2\right)\right].$$

At x=0 on the bottom boundary, its outward normal derivative is −0.12 exp(−0.72)=−0.0584102707151966. It is therefore not pointwise compatible with the phase Neumann condition at t=0. The reference applies the stated discrete no-flux operator during subsequent evolution; the neural representation retains the exact initial map and penalizes phase boundary residuals. We do not assume classical smooth compatibility on the closed space-time boundary.

Direct inspection of the twelve saved historical full-label calibration/L-BFGS/audit pools for the two protocols and two seeds finds no t=0 boundary node and hence zero boundary quadrature mass there. This finite-pool fact is distinct from a probabilistic argument about continuous random draws. The existing Adam rule generates boundary times from the four physical windows without explicitly inserting t=0; it does not mathematically exclude a zero random variate. The compatibility limitation is retained regardless. Its effect on the E/D_E ranking is unknown; neither the initial state nor the boundary rule has been changed.

## Matched E/F/D_E/B_E design

E learns T and φ through the electrical solve and includes the thermal/phase interior residuals, boundary terms and initial constraints. F retains a neural potential and the frozen finite electrical penalty; its endpoint receives the identical electrical readout used by E. D_E shares E's neural state mapping, temperature adapter, electrical solve, complete first-order conductivity feedback, voltage-observation loss, boundary/initial constraints, parent, calibration and optimization limits; only the thermal/phase interior package is removed. D_E is consequently a physics-containing ablation, not a data-only network.

B_E uses time-PCHIP and spatial-linear interpolation of the supplied T/φ observations, the original initial-logit restoration and known boundary extensions, followed by the same electrical solve. It is constructed once per protocol/information condition and does not use the V labels. The E/B_E comparison therefore measures practical competitiveness under the stated input utilization, not a strictly identical information-use intervention.

## Existing main result and adjacent counterexamples

All four clean E/F comparisons satisfy the complete device criterion under the three existing numerical references and both electrical readers. Thus, giving the soft comparator the same final electrical repair does not remove the configuration-level difference. These are four paired fits on two related protocols, not independent repetitions multiplied by the numbers of references, readers or saved time steps. Equal optimization limits also do not establish equal wall-clock cost or speedup over a conventional solver.

This robustness does not extend uniformly to B_E. For original-protocol seed 43 and the 240×120 reader, the full-precision records give:

| Reference | Current NRMSE: E / B_E (%) | Power NRMSE: E / B_E (%) | Relative current / power error reduction (%) | Original A / B |
|---|---|---|---|---|
| Original | 1.63105453176603 / 1.62000647877745 | 1.65740877994034 / 1.64642904691417 | −0.681975852153386 / −0.666881639797689 | False / False |
| Time-refined | 1.65327058574184 / 1.57045975439103 | 1.68185598884346 / 1.59608805202904 | −5.27303110565371 / −5.37363441229874 | False / False |
| Space-refined | 1.59784771955466 / 1.61120690603445 | 1.62155603440769 / 1.63659224471539 | +0.829141585090625 / +0.918751164577176 | False / False |

Negative reduction denotes larger E error. Under the time-refined reference the differences are +0.0828108313508116 and +0.0857679368144213 percentage points, respectively. Under the spatial reference E remains slightly better, below the prescribed practical margin. The first two comparisons already failed B, so the continuous reversals introduce no additional Boolean decision changes. Full-precision source fields and line locations are preserved in [the P04 table](tables/P04-original43-fine-continuous-effects.csv); these display values do not re-adjudicate thresholds.

In the two clean full-label residual ablations, D_E has lower phase, current and power errors than E across all three references and both readers. This supplies no positive evidence for an added predictive contribution from the thermal/phase interior package in that regime. Because D_E retains electrical physics and voltage feedback, this finding concerns the additional dynamic residual package. It proves neither equivalence nor universal redundancy. The temperature adapter and later phase heads likewise lack a demonstrated independent stable increment. Strict two-cycle reconstruction remains unestablished; the original event and signed-energy counterexamples stay alongside the main benefit.

## Frozen B1 question — results not yet available

The new observation condition removes phase labels on the complete second cycle W=[1.01,2.02] of the existing shorter protocol. V/T observations and phase outside W, including t>2.02, remain available. The exported data contain 17,094 positive-time phase labels and omit 11,781; V and T each retain 28,875. The original observed grid contains 1.02 through 2.02 within W, with no observed node at 1.01. The last preceding and first following visible times are 1.00 and 2.04. The analytic initial condition remains known.

Two new observation-only parents, seeds 29 and 43, will each initialize E, D_E and F under the frozen recipe. No complete-label trained state, calibration or interface pool is reused. Phase observation mass restricts the original coordinate quadrature before normalization. A threshold-straddling cell is admitted only when all its original adjacent corners remain visible. The primary question is whether E adds information over D_E in W, under the separately named A_w criterion. Whole-history A/B, strict events, outside-window costs and E/F/B_E comparisons remain separate. This is offline reconstruction of a developed protocol, not online forecasting or a wholly unobserved phase trajectory.

No B1 improvement, valid endpoint or scientific result is asserted in this revision block. An accepted conditional increment would concern the thermal/phase package in this observation regime; it would not establish a new architecture, a unique gradient mechanism, material validity or journal acceptance.

## Data and code availability

The curated repository release at commit 218bb66069da52b2ccfe9dd68ac519edbe4584d0 includes the 18 September manuscript revision, selected evidence, the two clean D_E endpoints with matched inputs, and scientific/scoring source. Scientific closeout occurred on 18 September 2026; curated publication occurred separately on 20 September. The complete fixed arrays and execution archives were not included in that public checkout.

The 21 September preparation constructs a local portable package for the twelve core objects and a separately indexed six-object negative extension. Its executable scope and actual verification status are stated in the preparation report. Local availability is distinct from approved public or controlled reviewer access; no new public URL, permission, license grant or DOI is claimed. Rebuilding the manuscript, rescoring arrays, regenerating predictions and retraining require different inputs. Author identity, affiliation, contributions, funding, conflicts and final disclosure/approval remain for truthful author completion.
