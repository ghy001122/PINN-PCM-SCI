## S25. Circuit and history consistency in the separate neuristor model

### S25.1 Numerical identity and controls

This section combines the finite-voltage interpolation, energy and conditional-temperature analyses into one auxiliary numerical test. Its object is the fitted lumped VO2 neuristor model associated with Qiu et al. [19], using the author implementation at commit 217d4f0ed6bfc680240021b07142a121cb4963d1. It is separate from the synthetic two-dimensional phase-field object in the main paper. No experimental temperature, phase or history labels are available here. The single-device 9, 12.5 and 15.8 V conditions correspond to the fitted model used alongside experimental Figure 2A-C; the two-device 11/9.4 V excitation and 11/14 V inhibition cases correspond to author simulations in Figures S11D and S13D. They do not reproduce the different experimental voltages of Figure 5. Parameters fitted to published curves are not blind validation.

The frozen circuit has C=145.34619293 pF, R_L=12 kΩ, C_th=49.62776831 pJ/K, S_th=0.20558726 mW/K and T_b=325 K; the coupling factors are 0.12 and 0.10 for excitation and inhibition. The source resistance parameters are R_0=0.00535882879 Ω, E_a=5220.47417 K, β=0.252796285 K⁻¹, w=7.19357064 K, T_c=332.805839 K and γ=0.956269682. The static metallic resistance is 262.5 Ω and its dynamic multiplier is 4.90025335. Each system starts at v=0, T=325 K and the author's heating history initialized at 324.9 K. Noise is zero. The author code's 305-370 K constitutive clipping, 0.01 K joint-vector reversal trigger, denominator regularization and update order are retained; state temperature itself is not clipped. These assumptions are part of the model, not measured truth outside its fitted range.

Each of five systems has a saved 0-20 μs trajectory at both 1 and 0.5 ns. The finite-voltage inputs comprise the same 197 times, including both endpoints, at a nominal 102.4 ns spacing. P denotes the locked PCHIP and CS the locked not-a-knot cubic spline, both without smoothing, per-peak shifts, time warping or negative-power clipping. Their KCL device current is I_KCL=(V_in-p)/R_L-C dp/dt, distinct from the load current (V_in-p)/R_L and capacitor current C dp/dt. Source temperature, resistance, insulating fraction g, history and full current are scoring/control data only. The development records have been inspected; they are not a hidden test set. No experimental CSV or the sealed 4.1/3.9 V protocol enters this analysis.

The conditional heat responses use the same linear operator K, with diagonal S_th and off-diagonal -ηS_th for the pair. Q_ref uses the piecewise-linear saved power v I_device; V_ref uses the native-voltage piecewise-linear function. P and CS retain their locked polynomials. Four-point Gauss convolution on the union of native times and polynomial breakpoints produces the main results; one eight-point check per identical input gives a maximum temperature difference of 1.14×10⁻¹³ K against the prespecified 10⁻⁶ K numerical threshold. Forty main responses, forty checks, ten source-history checks and twenty prediction-history replays were completed in the earlier package; none was repeated for this manuscript revision. Source R, g and history were reproduced bitwise before interpreting candidate replays.

### S25.2 Storage partition and closure identities

For fixed positive C and C_th, constant T_b, the same K and a differentiable prescribed voltage p, define E_C=Cp²/2, θ=T-T_b, A=K/C_th and F=p(V_in-p)/R_L, componentwise in the two-device case. KCL-driven heating satisfies C_th dθ/dt+Kθ=p I_KCL=F-dE_C/dt. The transformed state y=C_th θ+E_C therefore obeys dy/dt+Ay=F+AE_C. State continuity is carried through every segment; the capacitor energy is subtracted when recovering T and is never added again as dissipative heating. Piecewise-smooth inputs use the same relation on each segment with continuous state.

For two reconstructions with the same coefficients and environment, δ denotes their signed pointwise difference. Then

$$\delta T=\frac{\delta y}{C_{\rm th}}-\frac{\delta E_C}{C_{\rm th}}. \qquad (S25.1)$$

This is an algebraic storage partition, not a new theorem or an independently identified causal attribution. For the common time inner product, its squared error retains the cross term: C_th² ||δT||²=||δy||²+||δE_C||²-2〈δy,δE_C〉. The component RMS values cannot be summed, and their ratios are not causal percentages. Small signed total-energy errors can coexist with large local discrepancies because timing, storage and cancellation matter.

Now replay the source resistance law on the conditional temperature and its legal full history to obtain I_R=p/R(T,H). Define r_T,R=C_th dT/dt+K(T-T_b)-p I_R. For a conditionally exact KCL-driven heat response,

$$r_{T,R}=-p\,(I_R-I_{\rm KCL}). \qquad (S25.2)$$

The sign follows the residual convention above. With a nonzero KCL-driven thermal residual, the exact relation is r_T,R=r_T,KCL-p(I_R-I_KCL); numerical quadrature and discretization terms must not be silently discarded. Equation S25.2 does not prove that a more accurate I_R is a coupled electrothermal solution: I_R is a no-feedback diagnostic and has not been returned to the voltage or heat evolution. This identity is specific to the common voltage, temperature, history, coefficients and residual definition; it does not transfer a zero residual between different readouts.

### S25.3 Complete roles and the fixed 12.5 V display

Table S25a. Every fine-source role over the full 0-20 μs interval. Errors use normalized trapezoid weights and the same saved source. Temperature uses absolute K; current errors and closure are in μA. V_ref is an explanatory control. The all-window and both-source-step records remain available in the linked evidence package, and the two source step sizes are sensitivity conditions, not independent repetitions. P and CS device currents retain their original KCL definition.

{{TABLE:neuristor-all-roles}}

At 12.5 V, P/CS temperature RMS errors are 0.654351/0.761025 K and maximum errors are 6.472258/9.257625 K. The native-voltage control RMS is 0.018898 K. The saved-source 1 versus 0.5 ns temperature RMS difference is 0.194610 K, which exceeds the 0.106674 K P-versus-CS RMS gap; the table therefore describes rankings on each frozen numerical source rather than a certified continuous-solution ranking. The finite-observation contribution is nonetheless distinct from the two source representation terms: at 0.5 ns their RMS values are 0.649993/0.758883 K for P/CS minus V_ref, 0.021813 K for V_ref minus Q_ref, and 0.016209 K for Q_ref minus saved T. These three signed arrays sum pointwise to the total error; their RMS values do not sum.

The source has 13 temperature-history reversals at 12.5 V; P retains 13 and CS produces 25. Equality of a reversal count is insufficient: P still has closure RMS 223.271 μA. For inhibition B, CS reduces the diagnostic I_R error to 26.427 μA but leaves closure RMS 103.940 μA. CS improves temperature RMS for both inhibition roles and worsens it for the other dynamic roles. All fourteen CS role/source-step records have sampled negative KCL current and power; this is a constitutive-consistency cost of the reconstruction, not a numerical failure or evidence of active energy generation by the physical device. The nearly resting 9 V absolute errors are small and are not promoted by relative percentages.

![Prespecified 12.5 V voltage temperature and circuit closure](figures/neuristor-fixed-voltage-temperature-closure.png)

Figure S28. Prespecified 2.362-2.862 μs first-peak window at 12.5 V, reused without new selection. Top: saved voltage, the finite observed nodes and the locked P/CS functions. Middle: saved temperature, native-voltage control and the two conditional temperatures. Bottom: the signed I_R-I_KCL closure difference. The full-history and history/current views remain in the figure source index. No per-peak alignment, new threshold or smoothing is applied. These are numerical model quantities, not experimental thermal observations.

The published circuit energy score is kept unchanged. For example, the 12.5 V fine source total is 51.602131 nJ; P/CS signed errors are -0.010824/-0.025929 nJ while sums of absolute interval errors are 0.080346/0.079453 nJ. Native-voltage continuous RC energy is 51.572815 nJ, 0.029316 nJ below the saved-power reference; this representation difference motivates the explicit Q_ref/V_ref controls and never replaces the original denominator. Endpoint energy, local temperature, current, history and closure remain separate outcomes. No engineering-use tolerance has been supplied, so numerical qualification does not imply task sufficiency.

### S25.4 Joint reconstruction design and information boundary

The joint prototype uses only the existing 0.5 ns pair-excitation record at 11/9.4 V, η=0.12, and all 197 finite voltage nodes. Its full 20 μs grid has 40001 states. The initial function T⁰ is the already saved PCHIP conditional temperature obtained from those finite observations and fixed parameters. It is not a true-temperature label and introduces no fitting loss. Its own legal history gives a common conditionally integrated voltage v⁰. With a(t)=t/(20 μs), all three configurations start with zero correction from (T⁰,v⁰) and retain exact initial values.

N_dyn writes T=T⁰+a h_θ, regenerates the complete legal history from T, and eliminates voltage by the source explicit-Euler RC recurrence. F_dyn has the same temperature correction and an independent v=v⁰+a h_ξ correction, with a penalty on exactly the same RC defect. N and F use width-64, four-hidden-layer tanh MLPs with normalized input 2t/(20 μs)-1, two outputs, matched temperature initialization for each seed and zero final correction layers. S_dyn replaces h_θ by a cubic B-spline correction whose fixed knots are the 197 observation times and their midpoints; all coefficients start at zero. It shares N's RC elimination, history and objective. The three methods have the same T⁰ representation. The traditional known-parameter forward solution remains a separate reference rather than being hidden or recast as an unknown-initial-state inversion.

At each native time, R_n is evaluated after the original same-time history update; q_n=v_n²/R_n. Each forward pass reinitializes the legal history and propagates continuously without resetting at observation blocks. The backward pass must not update that history a second time. The residuals are

$$r_{RC,n}=C\frac{v_{n+1}-v_n}{h}-\frac{V_{{in},n}-v_n}{R_L}+\frac{v_n}{R_n}, \qquad (S25.3)$$

$$r_{T,n}=C_{\rm th}\frac{T_{n+1}-T_n}{h}+K(T_n-T_b)-\frac{v_n^2}{R_n}. \qquad (S25.4)$$

N and S eliminate precisely S25.3; F penalizes it. The initial history, constitutive clipping and source branch decisions are identical, including selected-branch numerical dependencies in the derivative. Source T/R/g/H and complete currents are available only at locked-endpoint scoring. Observation voltages are linearly sampled from native nodes onto the original observation times, using their original time weights, equal device weights and V*=11 V. With I*=1 mA and P*=1 mW fixed before training,

$$L_N=L_S=L_{\rm obs}+\langle(r_T/P_*)^2\rangle, \qquad (S25.5)$$

$$L_F=L_{\rm obs}+\langle(r_T/P_*)^2\rangle+\langle(r_{RC}/I_*)^2\rangle. \qquad (S25.6)$$

The admission checks cover common zero-correction outputs, fixed-event directional derivatives, separately disclosed cross-reversal changes, and one complete objective/gradient resource measurement. The first seed is 29. N/F each have at most 600 Adam updates (learning rate 10⁻³, β=(0.9,0.999), ε=10⁻⁸, one global gradient clip at 10) and 100 full L-BFGS objective/gradient evaluations; deterministic S has at most 700 full L-BFGS evaluations. Line-search trials count against the full-evaluation cap and incomplete trials must roll back to the accepted state. No support change or alternate architecture is permitted. Failure to obtain a credible executable gradient within the eight-hour entry deadline stops this prototype while manuscript delivery proceeds.

After all three accepted endpoints are locked, each method receives the same full-history RC replay from its own T/H and the legal v₀. Temperature is not repaired; the reported thermal defect uses this replay's power. F's native network output is retained separately. The primary comparison is equal-device, full-current joint RMS. The prospective development rule requires N to improve on both F and S by at least 10% and 10 μA, with 5% noninferiority in temperature, finite-observation error and replayed thermal defect; the absolute numerical floors are recorded by the admission configuration. Only a valid complete seed-29 success permits N/F seed 43, with the same settings and no second deterministic S run. This is a development comparison on inspected synthetic records, not an independent validation or a claim of online prediction. Experimental measurements, the sealed protocol, a new spatial model and parameter fitting are outside this prototype.

### S25.5 Actual prototype execution and comparison

{{JOINT_RESULT_SECTION}}

### S25.6 Evidence access and reproducibility scope

The circuit voltage/current subset at commit 709b10fd28fc8fc80c9103acd68be02c35ac2816 and conditional-thermal package at d068bdf466ccc40f73a2b4c11e5ade7179fd9eeb are publicly accessible through the project repository. Their scoring inputs, fixed polynomial coefficients, saved response arrays and histories support the recorded array-based checks. The present revision's evidence map identifies each table and figure source. This revision does not rerun the historical source trajectories or conditional heat integrations. The new joint code, actual admission records, three accepted states and cost logs have their own identity and are supplied locally. Its portable saved-array scorer passed an actual isolated-directory run with access to the research checkout denied. It recomputes the discrete RC/thermal defects, metrics and exact Boolean decisions; it does not provide checkpoint inference, neural AD residuals or retraining. This local package is not claimed to have been publicly deposited. The separate two-dimensional full-field and checkpoint access gap remains open. Requests about actual experimental probe nodes, the 50 Ω branch, drive timing, gain/delay and capacitance still use the existing author-contact draft; it has not been sent and no reply is assumed.
