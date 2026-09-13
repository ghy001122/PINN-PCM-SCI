# Selected V29 evidence

This user-authorized release package contains the actual fixed results, complete eight block-gradient vectors and their parameter ordering, frozen inherited normalizers and pools, all three final accepted models with L-BFGS states, telemetry, own electrical readouts, and current-instance closure receipt. Its release identity is the Git commit containing this package. Runtime `published: false` fields preserve the earlier scientific closeout snapshot, before the user's separate publication request; they are not the distribution status of this commit.

- [Terminal summary](terminal-summary.json) and [formal results](evaluation/results.json)
- [Complete first-order diagnosis](diagnosis.json), [gradient arrays](full-block-gradients.npz), and [both-pool endpoint audit](fixed-endpoint-common-audit.json)
- [Preserved calibration](calibration.json), [configuration](frozen-config.json), and [actual computation](endpoint-comparison-summary.json)
- [D_C](D_C/checkpoint.pt), [P1](P1/checkpoint.pt), [P_kappa](P_kappa/checkpoint.pt): accepted model and optimizer states; repeated/trial evaluations counted
- [Recovery and actual shutdown](compute-closure.json), [deployment](cloud-deployment.json), [deployed source manifest](deployed-source-manifest.json), [focused implementation checks](focused-implementation-checks.json)
- [Selected-file manifest](selected-artifacts.json), [plotting traces](evaluation/traces.npz), [plotting snapshots](evaluation/snapshots.npz)

Full own-field arrays remain in `outputs/runs/20260913-lf11-remaining-pde`; the full nominal reference is local and excluded. Old E0/D_E/P_E/B_E metrics in the result are explicit reuse from V28, not reruns. The unchanged sparse data remain at `paper/paper_v24/evidence/input/sparse.npz`. All observations are already exposed development data; no independent initialization, new case or stress is included. Reading or rendering these arrays does not independently reproduce training or full-reference evaluation.
