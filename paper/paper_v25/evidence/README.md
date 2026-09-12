# paper_v25 evidence

These are selected copies from the completed local follow-up. Original run root:
`outputs/runs/20260911-lf11-followup-fit-electric-block`.

The sparse observations and original parent are unchanged, available in
[paper_v24 input](../../paper_v24/evidence/input/sparse.npz) and
[paper_v24 parent](../../paper_v24/evidence/formal/warm_start/checkpoint.pt).
The new [fixed fitted state](fixed-fit-endpoint.pt) includes the adapter identity;
load it through `fit_model` in the follow-up fitting module.

[S0](s0.json) proves the visible interval-distance lower bound;
[S1](s1-result.json) records the actual fitting criteria, accepted endpoint,
evaluation counts and stop reason; [evaluation](evaluation.json) contains the
new endpoint and clearly labeled reused LF11 records. Every readout is based on
its own predicted fields. New scalar summaries of saved old traces do not imply
retraining or rerunning old methods.

The [optimizer states](optimizer-states/) include both base/refinement Adam
checkpoints and all four L-BFGS stage checkpoints. These are copies of the
actual accepted states, with their optimizer history. The original local run
is retained. Full-grid predictions and the archived nominal reference remain
local and are not included in this publication package.

[Training source identity](training-source-identity.json) was captured at
scientific closeout, before publication. The run manifest's published=false
field describes that capture time; the containing Git commit identifies this
later publication. Only presentation and packaging code changed for publication.

The current campaign used CPU only and started no cloud instance. Its own
[closure](compute-closure.json) records training completion before the first
new high-fidelity reference read; no old shutdown record is used as proof.

The full instruction remains in
[the authorized snapshot](../../../docs/notes/2026-09-11-lf11-followup-authorized-sprint-instructions.md).
The [cloud review handoff](../../../docs/notes/2026-09-12-lf11-followup-results-cloud-review-handoff.md)
maps this package to the research questions; its delivery message supplies the
verified release commit. A Git publication is not a new scientific result.
