# PHK-V2.3 LF5 AutoDL deployment

This reference-blind bundle is buildable only after the frozen CPU-T artifact
authorizes GPU execution or the explicit post-qualification user override flag
is present. It runs one fixed 400-update DEV-T trajectory
from exact LF3-T0 and, only after the strict carrier gate passes, one 1200-update
label-free physics P0 continuation.

CPU-T returned `LF5_TZL_ALIGNMENT_NOT_SUPPORTED_CPU`. On 2026-09-06 the user
explicitly authorized the unchanged trajectory anyway. The launcher therefore
passes `--user-override-cpu-gate`, and every manifest/summary labels the run
`POST_QUALIFICATION_USER_OVERRIDE_EXPLORATORY`. This does not rewrite the CPU
gate or authorize any changed loss, stream, seed, budget, or follow-on arm.
