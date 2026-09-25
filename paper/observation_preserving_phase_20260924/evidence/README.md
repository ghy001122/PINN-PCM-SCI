# Evidence roles and source identity

These are condensed copies of the completed run records, not a standalone replication dataset. Paths under `outputs/` identify local provenance; they do not imply that those files are uploaded. The input manifest records the pre-training baseline and zero-update state; qualification records readiness before training; endpoint locks, audits, results and decision record the later completed state.

`executed-source/phk_v23_observation_preserving_phase_run.py` is a byte-preserving copy of the executed runner retained locally. Its omitted device argument caused CPU training. It is an archival source snapshot, not a standalone entrypoint; imports require the original package context. The current `pinn_pcm_sci/` runner includes the documented device propagation repair. Do not substitute that repaired runner when interpreting the recorded CPU trajectories. The full executed source archive SHA256 is recorded in `device-deviation.json`; that archive remains local.

`compute-closure-public.json` contains the recovery and shutdown facts without connection details. Full field arrays, reference arrays, checkpoints, optimizer states, deployment archives and machine-specific recovery scripts are not included. P03 remains open.

The package-level `build_report.py` needs the documented local run inputs. `finalize_record.py` is the historical one-time closeout builder and rewrites state documents; it is retained for provenance, not a repeatable publication command. The published figures, tables and narrative can be read directly without executing either script.
