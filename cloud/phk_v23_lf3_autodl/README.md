# PHK-V2.3 LF3 AutoDL deployment

This bundle executes the sole V100/FP64/seed-17 LF3 combination pilot. T0 uses
only the exact medium carrier and LF1-B0 model weights. P0 is conditional on
the frozen T0 carrier gate and, if entered, uses the unchanged full physics
objective with zero label replay. Fine, extra-fine, direct LF_ONLY, the frozen
evaluator, and stress data are forbidden on the cloud instance.

Run the zero-update preflight before constructing an optimizer. After the
process ends, recover and hash-check every summary-bound artifact, terminate
training processes, shut down the instance, and verify SSH refusal before any
local nominal reference evaluation. GPU price and cost are outside this
campaign record; the scientific bound is one trajectory and at most 2400
optimizer updates.
