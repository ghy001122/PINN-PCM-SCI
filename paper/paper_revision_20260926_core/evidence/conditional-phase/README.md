# Conditional phase evidence

These are byte-identical copies of the completed run's compact records. [Publication map](publication-map.json) maps original local paths to these published files and their SHA-256 identities. Original runtime manifests retain their execution-time paths and identities.

- [Locked result](result.json), [numerical qualification](numerical-evaluation.json), [saved-array verification](saved-array-verification.json).
- [Coarse step history](coarse/steps.csv), [fine step history](fine/steps.csv), [common residual and heat components](common-components.csv).
- [Seams](endpoint-seams.csv), [reference scores](reference-evaluation.json), [reference traces](reference-traces.csv), [both active-support semantics](active-support-diagnostics.csv).
- [Runtime source identity](runtime-manifest.json), [frozen configuration](frozen-config.json), [recovery and shutdown](compute-closure.json).

Full internal-state arrays, temperature/AD caches, B0 checkpoint, reference arrays, deployment bundles and connection scripts remain local. These records permit inspection of reported numerical results but do not by themselves reproduce all model queries or array-level checks. P03 complete external data access remains open. No new scientific computation was performed for this publication.
