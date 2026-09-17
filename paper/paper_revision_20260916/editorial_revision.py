"""Evidence-preserving author revisions following the 2026-09-17 review.

This module changes manuscript prose and placement only. It does not calculate
scores, load models, mutate experiment rules, or run numerical solvers.
"""
import re


def replace_once(text, before, after):
    if text.count(before) != 1:
        raise ValueError(f"Editorial anchor is not unique: {before[:100]}")
    return text.replace(before, after, 1)


def between(text, first, last):
    return text[text.index(first):text.index(last)]


NUMERICS = r"""### S1.1 Reference time integration and nonlinear solution

The carrier and both references use cell-centered finite volumes and backward Euler in time. Let D_h be the phase no-flux Laplacian and D_Th the thermal Laplacian with the stated top Dirichlet and remaining Robin boundaries. At an accepted time step, the discrete equations include

$$\phi^{n+1}-\phi^n-\Delta t M(T^{n+1})[\epsilon^2D_h\phi^{n+1}-W_\phi(\phi^{n+1},T^{n+1})]=0. \quad (S5)$$

$$[(1+\gamma\Delta t)I-\alpha\Delta t D_{Th}]T^{n+1}=T^n-L(\phi^{n+1}-\phi^n)+\Delta t Qq^{n+1}. \quad (S6)$$

Starting from the previous accepted T and phase, each block evaluates conductivity, solves the electrical system at U(t_n+1), solves the phase equation with the current temperature iterate, and solves the linear thermal equation with that phase increment and electrical heat. Unit block relaxation is used. When the maximum scaled T/phase iterate change is at most 1e-8, the electrical field is recomputed from the new state and both final step-equation residuals must have infinity norm at most 1e-9. Otherwise iteration continues, up to 30 blocks. The thermal matrix is constant for a given grid and step, allowing one factorization per trajectory.

The phase subproblem uses Newton in the full logit variable with an analytic phase Jacobian followed by its sigmoid chain factor. Its infinity-norm step residual tolerance is 1e-10, with at most 30 Newton iterations. A trial logit step starts at one and is halved until the residual strictly decreases, down to 2^-20. Failure stops the trajectory. Outputs are not clipped and algorithms or time steps are not changed in response to event quality. These are algebraic tolerances for the implemented step equations; they are not bounds on continuum or learned-state error.

The implementation is specified by PhkV21OracleCase.solve in phk_v21_benchmark.py and _solve_logit_newton in phk_v21_solver.py, using the frozen object overlay. The new finite waveform and reference wrappers change the prescribed case and discretization only. The reference phase Laplacian is a grid operator, whereas training uses coordinate AD for phase and midpoint cell/face quadrature for heat. Shared electrical conductances help align that coupling interface but do not make the whole neural residual identical to the reference discretization. Halving dt tests one temporal perturbation of this numerical family; it neither supplies an independent solver nor establishes spatial convergence.

"""

NEIGHBORS = """Differentiable PDE-constrained layers are a closer architectural precedent: PDE-CL solves for a constrained combination of learned basis functions and differentiates that solution [15]. Hard-constraint PINNs also distinguish boundary parameterizations from penalty and augmented-Lagrangian enforcement of interior equations [16]. Our finite electric penalties are therefore specific tested comparators, not the entire class of soft or constrained optimization methods.

| Neighboring approach | Relevant precedent | Distinction of the present experiment |
| --- | --- | --- |
| Solver-in-the-Loop [3] | Learns corrections interacting with a numerical trajectory | Here the evolving fields are offline reconstructions; only the quasi-static electrical state is solved during learning. |
| Hybrid FEM-NN [4] and PDE-CL [15] | Couple learned components or bases to differentiable PDE constraints | Here a fixed face network maps learned T/phase to V and local heat; no parameter-to-solution operator is learned. |
| Integral projection [12] | Enforces prescribed integral quantities | The electrical layer enforces a local discrete boundary-value problem; this alone does not certify state accuracy. |
| hPINN [16] | Uses boundary constructions and penalty/augmented-Lagrangian formulations | Augmented-Lagrangian training is not an executed comparator here; no superiority to that method is asserted. |

This table positions the formulation, not a numerical ranking of those papers. The contribution is the defined electrothermal reconstruction interface and its matched repair controls, rather than a new principle of implicit differentiation or hard constraints.

"""

DESIGN = """The comparison units and information paths are summarized below. All measurements are noiseless numerical samples from the stated carrier, and all learned reconstructions use observations spanning the full trajectory.

| Comparison family | What is held common | What the contrast can identify |
| --- | --- | --- |
| Four clean E/F pairs: two protocols × seeds 29/43 | Sparse V/T/phase, fitted parent, retained T/phase architecture, objective scales, update/evaluation caps, final electrical solve | The defined training-method package. Initial V, electrical enforcement times, active parameters, gradients and solve work still differ. |
| E versus one B_E per protocol | Available sparse carrier and final electrical solver | Benefit over this interpolation rule. B_E actually uses T/phase, not interior V; equal availability is not equal information utilization. |
| Historical D_E, balanced and full-grid F | Their original development parent and frozen recipes | Bounded residual/penalty/coverage alternatives; these are not extra clean repetitions. |
| Six later E_C/E_R/E_I states: three arms per earlier-pulse parent | Parent, data, retained physics and continuation caps | Continued fitting versus added capacity versus the specified gate. Old F states do not receive this extra budget. |

The fixed-array archive contains eight historical learned states, two deterministic interpolants and six later learned states: sixteen scoring objects, not sixteen independent models or cases. Historical E is compared with F and B_E in each of four protocol/seed pairs, giving eight comparisons and sixteen A/B decisions per reference. The separate NumPy scorer tests arithmetic reproducibility, not independent scientific validation.

"""

ABSTRACT = """A final electrical solve can repair terminal currents without correcting learned temperature or phase fields. We test whether imposing the same electrical constraint during training improves those evolving states. The proposed hybrid PINN learns temperature and phase, eliminates quasi-static potential through an implicitly differentiated finite-volume solve, and couples its local Joule deposition to thermal and phase residuals. A soft electrical PINN receives the same final solve; a same-solver interpolant provides an additional control. In a synthetic, dimensionless two-dimensional wall cell with noiseless sparse observations, two initialization pairs are fitted separately under each of two pulse protocols. Under the original numerical references and prescribed optimization budgets, electrical elimination reduces current and power NRMSE by 48.8–78.3% relative to projected soft controls; its current NRMSE is 0.682–1.572% and power NRMSE is 0.673–1.593%. Earlier-pulse phase RMS decreases by 20.22% and 20.31%. With predictions fixed, halving the reference time step preserves all four paired device advantages. Additional phase-head controls do not establish a reference-stable representation gain. The results support the specified training package beyond final electrical repair, while leaving the independent necessity of the remaining PDE residuals, spatial convergence, strict two-cycle capability and material-calibrated performance unresolved."""


def revise(manuscript, supplement):
    # Preserve full new-head evidence before shortening its main-text treatment.
    head_method = between(manuscript, '### 3.4 Matched development', '### 3.5 Fixed-prediction')
    head_protocol = between(manuscript, '### 4.3 Phase-head continuation', '## 5. Results')
    head_results = between(manuscript, '### 5.6 Phase representation', '### 5.7 Fixed-model')
    event_figure = between(manuscript, '![Figure 10.', 'The clean-directory NumPy evaluation')

    # R3/R5: make the executed numerical interface reproducible from the text.
    supplement = replace_once(supplement, '## S2. Exact learning interfaces', NUMERICS+'## S2. Exact learning interfaces')
    supplement = replace_once(supplement, 'Coordinates are normalized by the inherited physical-domain mapping.',
        'Coordinates supplied to every head are (x, 2z-1, 2t/2.5-1), mapping the physical domain to [-1,1]^3. Derivatives in the residuals are with respect to physical x,z,t, including this chain rule.')
    manuscript = replace_once(manuscript, 'Positive conductivity and the grounded electrode yield a nonsingular discrete electrical problem.',
        'Positive conductances on the connected grid, with Dirichlet electrodes fixing its gauge, make the assembled electrical matrix nonsingular. Electrical enforcement means solving this discrete system to numerical precision; it is not an exact continuum solution.')
    manuscript = replace_once(manuscript, 'Neither identity by itself establishes accuracy relative to the reference heating field.',
        'Neither identity by itself establishes accuracy relative to the reference heating field. P_J denotes electrical dissipation; the reduced thermal source is Qq, so its integral is QP_J. This normalization and the temperature-dependent phase potential do not imply a general total-free-energy decay theorem.')
    manuscript = replace_once(manuscript, 'These discretizations serve different roles; their existence alone is not a convergence study.',
        'Both numerical trajectories use backward-Euler finite-volume steps with converged electrical/phase/thermal block iterations and logit Newton for phase, as specified in Supplement S1.1. Their algebraic convergence tolerances do not certify discretization accuracy. The grids serve different roles; their existence alone is not a convergence study.')

    # R4/R7/R8: keep contrast identities and event qualifiers explicit.
    manuscript = replace_once(manuscript, '### 4.2 Common inference and distinct outcome measures', DESIGN+'### 4.2 Common inference and distinct outcome measures')
    manuscript = replace_once(manuscript, 'The matched device criterion uses bottom current; top and bottom currents agree to solve accuracy for projected states.',
        'The matched device criterion compares predicted bottom current with the reference top-current trace, retaining the historical scoring convention. The top-current noninferiority guard uses the predicted top current. For projected states these terminal traces agree to solve accuracy; the archive also reports bottom-native errors as a separate diagnostic. Unprojected soft currents can disagree substantially and must not be interchanged.')
    for label, text in [('main', manuscript), ('supplement', supplement)]:
        fixed = text.replace('none in the four E/soft and E/interpolant comparisons',
            'none across the eight historical comparisons (four E/soft and four E/interpolant), comprising sixteen A/B decisions per reference')
        if label == 'main': manuscript = fixed
        else: supplement = fixed
    supplement = replace_once(supplement, 'No learned endpoint passes all strict criteria.',
        'None of the eight historical learned endpoints in Tables S4–S6 passes every strict criterion under the original references. The later gated endpoint and its reference-specific result are reported separately in S10–S11.')
    supplement = replace_once(supplement,
        '| A frozen interface gate adds a matched benefit over the ordinary residual | Not supported in this trial | Original-reference qualifying parent seeds: none; refined: [43] | These are trained-parent developments, not new clean confirmations |',
        '| The gated head has a reference-stable independent increment | Not established | No A/B increment under either reference; a strict increment only for seed 43 under the refined reference | The reference-specific strict contrast is VERIFIED; it is not stable across both references or clean-seed confirmation |')

    # R1: add two directly relevant primary-source comparisons.
    manuscript = replace_once(manuscript, 'Our setting differs in three respects.', NEIGHBORS+'Our setting differs in three respects.')

    # R2: move complete head development to the supplement, retaining every arm.
    manuscript = replace_once(manuscript, head_method, '')
    manuscript = manuscript.replace('### 3.5 Fixed-prediction reference perturbation', '### 3.4 Fixed-prediction reference perturbation')
    manuscript = replace_once(manuscript, head_protocol,
        '### 4.3 Bounded phase-head development\n\n'
        'After the clean comparison, each earlier-pulse E endpoint is continued in three arms: unchanged representation, ordinary residual capacity and a frozen parent-interface gate. They share the original data and coupled PINN objective, with 600 Adam updates and 100 complete L-BFGS evaluations per arm. The six endpoints are developments from trained parents, not independent confirmations. Full formulas, equal-trainable-parameter controls, fixed display times and actual solve counts are retained in Supplement S10 and S13. This experiment asks whether representation changes add an increment beyond continued fitting; it does not redefine the original E method.\n\n')
    manuscript = replace_once(manuscript, head_results, '')
    manuscript = manuscript.replace('### 5.7 Fixed-model reference sensitivity and array-only reproduction', '### 5.6 Fixed-model reference sensitivity')
    manuscript = replace_once(manuscript, event_figure, '')
    manuscript = replace_once(manuscript,
        'Sections 5.1-5.5 retain the historical results against the original fixed references. Section 5.6 adds the matched phase-head development, and Section 5.7 separately reports the new reference perturbation. No historical endpoint or decision is overwritten.',
        'Sections 5.1–5.5 report the matched elimination results against the original reference. Section 5.6 tests those fixed predictions with the refined reference; Section 5.7 summarizes a subsequent bounded representation experiment. Original endpoints and reference-specific decisions remain separate.')

    start = manuscript.index('Strict two-cycle success holds for')
    end = manuscript.index('Table 4. Reference discrepancies', start)
    manuscript = manuscript[:start]+(
        'The main device conclusion is more stable than the strict event threshold: a later gated endpoint passes the complete two-cycle rule only under the refined reference. Section 5.7 reports that limited result; none of the eight historical learned states achieves the strict capability under both reference choices.\n\n'
        )+manuscript[end:]
    start = manuscript.index('For shorter/43/E_I, cycle 1 recall')
    end = manuscript.index('The clean-directory NumPy evaluation', start)
    manuscript = manuscript[:start]+manuscript[end:]
    start = manuscript.index('The clean-directory NumPy evaluation')
    end = manuscript.index('## 6. Discussion', start)
    manuscript = manuscript[:start]+(
        'A separate NumPy-only scorer reproduces the ten historical objects’ saved metrics and decisions, then evaluates the six new states against both references. The sixteen objects comprise fourteen learned states and two interpolants, not independent replications. This is array-level reproducibility from a local archive, not third-party reproduction or independent solver validation.\n\n'
        '### 5.7 Added phase capacity gives mixed, reference-dependent effects\n\n'
        'Continued optimization alone lowers raw phase RMS by 7.65% and 8.89% in the two earlier-pulse parents. Neither an ordinary residual nor the interface-gated residual adds the prescribed phase or device increment over that continuation under either reference. For example, the gated head lowers power NRMSE by 7.54% and 7.24% relative to continuation under the original reference, while phase RMS changes by −1.58% and +2.04%. These mixed effects do not establish the gate as a new component of the confirmed method.\n\n'
        'The gated seed-43 endpoint nevertheless meets the complete strict rule and its accompanying noninferiority conditions under the refined reference only. Its first-cycle recall changes from 0.898602974 to 0.902063024 with exactly the same prediction. Reference active mass decreases from 0.0006934375 to 0.00068921875, while overlap also decreases from 0.000623125 to 0.00062171875. Thus a threshold can improve when its reference denominator changes, even without more overlap. The onset error changes from 0.003750 to 0.004583 and remains within its criterion. This is a real reference-specific outcome, not a reference-stable gain. All six arms, both cycles, both references and the predeclared full-domain maps remain in Supplement S10–S13.\n\n'
        )+manuscript[end:]
    # Only the reference-margin plot stays in the main text; retain asset names.
    manuscript = manuscript.replace('Table 4.', 'Table 3.').replace('Figure 9.', 'Figure 7.')
    manuscript = manuscript.replace('Section 5.7. It remains a fixed-spatial', 'Section 5.6. It remains a fixed-spatial')
    manuscript = re.sub(r'(?s)(## Abstract\n\n).*?(\n\nKeywords:)', lambda m:m.group(1)+ABSTRACT+m.group(2), manuscript, count=1)
    conclusion = """## 7. Conclusions

Training-time elimination of quasi-static potential, coupled through consistent local Joule deposition, improves the specified sparse reconstruction beyond giving a soft PINN the same final electrical solve. Four clean protocol/initialization pairs retain a device-function advantage under both tested temporal references, with mixed state and event outcomes reported separately. The result concerns the implemented coupling package under prescribed budgets; it does not isolate the implicit gradient or prove that the remaining thermal/phase residuals are necessary.

The representation controls and reference perturbation sharpen this conclusion. Additional phase capacity does not establish a reference-stable matched gain, and one strict two-cycle crossing changes with the reference alone. The present evidence therefore supports a bounded computational reconstruction method, with spatial-reference sensitivity and material-specific validation remaining distinct next questions.

"""
    manuscript = replace_once(manuscript, between(manuscript, '## 7. Conclusions', '## Data, code and declarations'), conclusion)
    manuscript = manuscript.replace('This is the local experimental revision dated 16 September 2026;',
        'The experiment was completed on 16 September 2026 and this manuscript was editorially revised on 17 September 2026 without new scientific execution;')

    # R9/R11: declarations and scope, without inventing human approval.
    ai_statement = """AI-assisted preparation: OpenAI Codex assisted with manuscript drafting and revision, research-code preparation, figure construction and source checking. Statements in this draft are linked to archived results and cited sources. AI assistance does not constitute independent peer review or scientific replication. Human authors must verify the final content, disclosures and interpretation and take responsibility for the submitted work; that final approval is not asserted by this draft.

"""
    manuscript = replace_once(manuscript, 'Funding: [to be supplied by the authors].', ai_statement+'Funding: [to be supplied by the authors].')
    # Main equation numbers remain sequential after relocation.
    for old, new in [(23,21),(24,22),(25,23)]:
        manuscript = manuscript.replace('\\qquad ('+str(old)+')$$', '\\qquad ('+str(new)+')$$')

    head_method = head_method.replace('### 3.4 Matched development of the phase representation', '### S13.1 Phase representation and attribution')
    head_method = head_method.replace(r'\qquad (21)$$', r'\qquad (S7)$$').replace(r'\qquad (22)$$', r'\qquad (S8)$$')
    head_protocol = head_protocol.replace('### 4.3 Phase-head continuation and independent array scoring', '### S13.2 Complete continuation and scoring protocol')
    head_results = head_results.replace('### 5.6 Phase representation: continuation, capacity and the frozen interface gate', '### S13.3 All matched results and predeclared maps')
    head_results = head_results.replace('Table 3', 'Table S16').replace('Figure 7', 'Figure S2').replace('Figure 8', 'Figure S3')
    head_results = head_results.replace('main Figure S3', 'Figure S3')
    event_figure = event_figure.replace('Figure 10', 'Figure S4')
    appendix = '## S13. Complete phase-head formulation and visual evidence\n\n'+head_method+'\n'+head_protocol+'\n'+head_results+'\n'+event_figure+'\n'
    supplement = replace_once(supplement, '## References', appendix+'## References')
    supplement = supplement.replace('main Figure 8', 'Figure S3').replace('Figure 9', 'main Figure 7')
    supplement = supplement.replace('The main text states every physical coefficient and boundary condition.',
        'The main text states every physical coefficient and boundary condition. S1.1 below specifies the executed numerical reference algorithm.')
    supplement = supplement.replace('The formerly proposed fixed-model temporal refinement is executed in this revision.',
        'The fixed-model temporal refinement was executed on 16 September 2026. The 17 September review changes presentation and documentation only.')
    supplement = replace_once(supplement,
        'The contribution must rest on the explicitly defined interface and matched reconstruction evidence.',
        'PDE-CL [15] and hPINN [16] further delimit the constraint-learning precedents. They were not run as additional baselines. The contribution rests on the explicitly defined interface and matched reconstruction evidence.')
    supplement = supplement.replace('Table S2 retains electrical repair,',
        'Table S2. Development counterfactuals: electrical repair,')
    supplement = supplement.replace('Table S3 retains the subsequent remaining-PDE-strength counterfactual.',
        'Table S3. Remaining-PDE-strength counterfactual.')
    equation_numbers = {'S5':'S1','S6':'S2','S1':'S3','S2a':'S4a',
        'S2b':'S4b','S2c':'S4c','S3':'S5','S4':'S6','S7':'S7','S8':'S8'}
    supplement = re.sub(r'(\\(?:qquad|quad) \()(S\d+[abc]?)(\)\$\$)',
        lambda match:match.group(1)+equation_numbers[match.group(2)]+match.group(3), supplement)
    return manuscript, supplement
