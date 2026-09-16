# Reproduction

Use Python3.11, FP64 and the established Torch2.5.1/SciPy1.14.1 environment. The new case is defined in `pinn_pcm_sci/phk_v23_lf11_protocol.py` and `configs/phk_v23/lf11_protocol_sprint.json`; all primary solver tolerances and material contracts remain unchanged.

1. `python -m pinn_pcm_sci.phk_v23_lf11_protocol_reference freeze` records the finite case and expanded solver budgets before fields are generated.
2. The `support` and `reference` actions each generate their one authorized local trajectory. The support action exports the frozen sparse mask; the reference process is separate from training. Do not send either full carrier to training.
3. Run `python -m pinn_pcm_sci.phk_v23_lf11_protocol_train --device cuda:0` in the selected code/contracts/sparse-only environment. It creates fresh parents, E/F branches and one new B_E. Existing scientific run directories are refused.
4. Recover fixed outputs, terminate the actual instance, and record current closure before running `python -m pinn_pcm_sci.phk_v23_lf11_protocol_evaluate` locally.
5. `python -m pinn_pcm_sci.phk_v23_lf11_protocol_paper` renders this manuscript, tables and figures from the saved scores; it performs no training or checkpoint selection.

New primary trajectories: 1000 support and 4000 reference main steps, with internal coupled/phase/electrical bounds separately expanded. Training caps are10800 Adam and2400 complete evaluations. E forward/adjoint caps are54000 each; calibration/audit are separate. Five projected inference roles use278 powered times each, total1390. Full actual counters and early optimizer stops are preserved. Fixed update caps do not establish equal actual compute or a speedup.

The original protocol/seed results are imported as already published evidence; historical seed17 is not pooled with seeds29/43. The final tail after2.02 is excluded from cycle2 recovery. Optional time refinement requires the original explicit trigger and cannot be used to retrain or choose a checkpoint.
