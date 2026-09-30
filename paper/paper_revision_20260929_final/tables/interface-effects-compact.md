| Comparison; protocol/seed | Δ phase RMS | Δ I / Δ P (pp) | Relative reduction: φ / I / P (%) | Original A / B |
| --- | --- | --- | --- | --- |
| E/F; original/29 | +0.003688 | +0.78407 / +0.81702 | +14.90 / +47.03 / +47.86 | Pass / Pass |
| E/F; original/43 | +0.002707 | +1.47699 / +1.56052 | +10.76 / +48.03 / +49.04 | Fail / Pass |
| E/F; shorter/29 | +0.004513 | +1.26123 / +1.31953 | +18.46 / +55.39 / +56.31 | Pass / Pass |
| E/F; shorter/43 | +0.004336 | +2.28332 / +2.39242 | +17.99 / +76.52 / +77.50 | Fail / Pass |
| E/F_cov; shorter/29 | +0.004218 | +1.13073 / +1.12968 | +17.46 / +52.68 / +52.46 | Pass / Pass |
| E/F_cov; shorter/43 | +0.004671 | +1.39378 / +1.39967 | +19.12 / +66.55 / +66.83 | Pass / Pass |
| E/D_E; shorter/29 | -0.000468 | -0.05746 / -0.05850 | -2.40 / -6.00 / -6.06 | Fail / Fail |
| E/D_E; shorter/43 | -0.000055 | -0.05751 / -0.07019 | -0.28 / -8.95 / -11.24 | Fail / Fail |
| E/B_E; original/43; original ref. | +0.002151 | -0.01105 / -0.01098 | +9.05 / -0.68 / -0.67 | Fail / Fail |
| E/B_E; original/43; time ref. | +0.001989 | -0.08281 / -0.08577 | +8.42 / -5.27 / -5.37 | Fail / Fail |
| E/B_E; original/43; space ref. | +0.000852 | +0.01336 / +0.01504 | +3.66 / +0.83 / +0.92 | Fail / Fail |

Δ = control error − E error; positive values favor E. Relative reduction is Δ/control. The current and power differences are percentage points, not relative percentages. A/B are the original full qualification decisions, copied from saved decision tables; they are not reconstructed from these three metrics. Rows A–C use the spatial reference and fine reader; the B_E boundary uses the original-protocol seed-43 fine reader under all three pre-existing references. Display rounding never changes a decision. Full-precision values and source lines: [interface-effects-full.csv](interface-effects-full.csv).
