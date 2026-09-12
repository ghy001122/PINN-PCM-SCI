# Selected release evidence

- [V result](v-result.json), [compatibility](v-compatibility.json), [accepted-state trace](v-telemetry.jsonl), [final model plus actual V L-BFGS state](endpoint-with-V-optimizer.pt).
- [Frozen config](frozen-contract.json), [compute closure and unrun branches](compute-closure.json), [contact baseline invariance](contact-baseline-check.json).
- [Finalized run manifest](run-manifest.json) and [runtime source identity](source-identity.json) link the scientific path to its actual implementation.
- [Pre audit](electric-pre.json) / [post audit](electric-post.json), with [pre signed arrays](electric-pre.npz) / [post signed arrays](electric-post.npz). Boundary traces, normal derivatives, both conductivity locations, edge/interior strata and signed cross terms are retained.
- [Evaluation](evaluation.json), [all saved device/event traces](evaluation-traces.npz), [normalization metadata note](evaluation-scale-note.json).
- [Numerical table](../tables/all-endpoint-metrics.csv), [manuscript](../manuscript.md), [reproduction](../reproducibility.md).

The inherited sparse bundle and parent/optimizer are in paper_v24/evidence and paper_v25/evidence; this package does not copy the entire historical run tree. Full predictions are saved locally in the new run as v_continue/prediction.npz and contact-prediction.npz. The nominal raw reference also remains local. The selected pack accompanies the paper_v26 release under the user's subsequent publication authorization. Its containing Git commit identifies the release. Execution-time publication fields in the frozen manifest/source identity retain their original historical values.

The checkpoint contains the complete final model with the T adapter and the actual V-only optimizer; its optimizer is not a joint Adam state. New D_B/P_U/G/N/D_N have no endpoints because their prerequisite was not met.
