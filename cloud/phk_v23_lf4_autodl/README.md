# PHK-V2.3 LF4 AutoDL deployment

This reference-blind bundle runs three fixed 400-update, seed-17, FP64 V100
development arms from the exact LF3-T0 weights. If a frozen endpoint passes the
entry gate, it then runs the mandatory 1200-update label-free physics P0.

Only the medium carrier and exact LF3-T0 checkpoint may be uploaded. Fine,
extra-fine, direct LF_ONLY, the frozen evaluator, and both sealed stress
references remain local and inaccessible. Run `preflight.py` before any
optimizer is constructed. After completion, recover and hash-check all
summary-bound artifacts, stop the process, clear the GPU, shut down the
instance, and verify SSH refusal before local nominal evaluation.
