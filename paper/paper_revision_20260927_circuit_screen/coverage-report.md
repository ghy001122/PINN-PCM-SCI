# 混合测度下的覆盖增强

VERIFIED: Against the mixed-measure coverage control F_cov, E satisfies the original whole-history A/B criteria in 12/12 and 12/12 reference/reader/initialization conditions. The device-criterion advantage is retained in all twelve sensitivity conditions. F_cov satisfies A/B against its historical F in 0/12 and 0/12 conditions, and satisfies the unchanged strict rule in 0/12. These are twelve sensitivity records for two new continuations, not twelve independent runs.

F_cov nevertheless reduces current and power error relative to F by 1.36-9.00% and 3.73-11.32% for seed 29, and 27.43-31.72% and 29.79-34.00% for seed 43. Its phase-set error S increases by 11.40-12.57% and 13.05-15.28%, respectively, violating the set-error noninferiority component in every condition. Thus the failed complete criteria coexist with continuous port improvements.

The phase RMS change also depends on initialization: seed 29 improves by 0.82-1.30%, while seed 43 worsens by 1.39-1.77%. Local Joule-density error worsens by 4.06-11.03% for seed 29 and improves by 15.08-21.29% for seed 43. All ranges use the six reference/reader conditions of the same endpoint, without combining training histories.

| Seed | Adam | Complete evaluations | Termination |
| --- | --- | --- | --- |
| 29 | 1500 | 300 | EVALUATION_BUDGET_EXHAUSTED |
| 43 | 1500 | 300 | EVALUATION_BUDGET_EXHAUSTED_TRIAL_ROLLED_BACK |

完整合同与表格见补充 S24；数值事实为 VERIFIED，配置鲁棒性解释为 SUPPORTED_INTERPRETATION。P02、严格双周期及材料／泛化主张仍未闭合。
