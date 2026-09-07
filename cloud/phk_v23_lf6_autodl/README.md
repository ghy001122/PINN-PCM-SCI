# PHK-V2.3 LF6 AutoDL deployment

This bundle is built only from the LF6 activation commit plus the exact,
hash-bound CPU-F qualification and materialized ledger.  The remote preflight
reads every ledger array and verifies its shape, dtype, content hash, stream
step hashes, aggregate hashes, and semantic aggregate before any optimizer is
constructed.  The GPU runner consumes those arrays directly; it must not
create training coordinates with Sobol or any other runtime sampler.

The scientific sequence is fixed: DEV-U, DEV-R, deterministic carrier
selection, then one conditional P0.  P0 uses the exact pre-materialized
physics ledger and no medium labels.

## DEV-M fallback authorization boundary

The LF6 scientific selection rule includes the exact LF4 DEV-M checkpoint as
a legal safety-qualified fallback, while the original LF6 cloud allowlist
omits that checkpoint.  The deployment tooling supports the exact checkpoint
only when the operator supplies both:

- `--allow-dev-m-fallback-input` to the bundle builder and preflight; and
- `LF6_ALLOW_DEV_M_FALLBACK_INPUT=1` to `run.sh`.

Those switches record the explicit 2026-09-07 continuation authorization in
the deployment manifest. The only admissible file is the frozen DEV-M path
with SHA-256
`16EEE20C6B1A2510ACB387E83894ADD64061D631422FAB4DAA9EC1F7194018B5`.

Fine, extra-fine, direct LF_ONLY, frozen evaluators, and stress material are
forbidden on the cloud.  Local reference adjudication begins only after all
cloud artifacts are recovered and verified and the instance is shut down.
