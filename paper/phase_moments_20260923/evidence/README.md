# Public evidence subset

This directory preserves the compact, reviewable evidence for
`20260923-relative-phase-moments`. It contains the frozen decision, endpoint
identities and work counts; complete scoring; calibration and quadrature
audits; focused test output; and a sanitized compute-closure record.

The files preserve the immutable local run content, subject only to Git text
line-ending normalization, except `compute-closure-public.json`, which removes
the cloud address, remote working directory and machine-local archive path. The
recovery checksum and shutdown facts remain visible.

The eight native 160x80 space-time arrays, model checkpoints, optimizer states,
deployment/recovery archives and connection material remain local. Therefore
this subset supports review of the reported tables, gates, costs and numerical
validity, but does not by itself support complete array-level rescoring or
endpoint replay.
