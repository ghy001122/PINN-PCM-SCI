# Conditional electrical-block evidence

This directory records the actual conditional decision, once-only blind calibration, fixed endpoints and accepted optimizer states. The common parent and fixed pools are shared exactly with the main evidence one directory above; their duplicate binary copies are omitted here. Intermediate G/N states and full own-field predictions remain in the original run.

R reuses the exact original P_U Adam1000 state, then performs its own fresh 200 complete fixed L-BFGS evaluations. Reused Adam updates are not counted as new execution. G and N each start from the common parent, with fresh 1000-Adam/200-evaluation trajectories. A later D_N batch exists only if the saved R/G/N decision authorized it. Read the actual campaign and followup-decision files; implementation availability is not evidence that a branch ran or succeeded.

All full-reference endpoint evaluations follow termination of their training workers. No stress data, extra observations, new physics, or independent initialization are used. Results inherit the exposed nominal-case scope.

Rebuild the conditional figure and tables from this package without training or reference access:

```powershell
.\.venv\Scripts\python.exe -m pinn_pcm_sci.phk_v23_lf11_joint_conditional_report --root paper/paper_v27/evidence/conditional --paper outputs/reproduction/lf11-joint-conditional-figures
```
