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

## P0-only prestep engineering continuation

The original remote campaign completed the fixed DEV-U and DEV-R endpoints,
then stopped after creating an empty `p0/` directory and before constructing
the P0 optimizer.  The bounded engineering continuation must not rerun either
development arm.  It is enabled only with all of the following explicit
environment values:

- `LF6_EXECUTION_MODE=P0_ONLY_PRESTEP_ENGINEERING_RETRY`;
- `LF6_OUTPUT_ROOT=/root/autodl-tmp/lf6-run-20260906T065434Z`; and
- `LF6_DEVELOPMENT_ARTIFACT_LOCK=/root/autodl-tmp/lf6-run-20260906T065434Z/cloud/recovery_manifest.json`.

The recovery manifest uses schema
`phk-v23-lf6-development-artifact-lock-v1`.  It separates the original
`development_source_identity` from the new `continuation_source_identity`,
binds all twelve DEV-U/DEV-R files by output-root-relative path, byte size and
SHA-256, records an exact remote/local match, and attests that `p0/` exists but
is empty with zero P0 updates.  The preflight independently checks those fixed
records before allowing the core P0-only entrypoint.  It still verifies the
continuation deployment manifest, original activation inputs, complete
materialized ledger, exact V100 identity, duplicate-process absence, and the
reference-blind cloud boundary.
