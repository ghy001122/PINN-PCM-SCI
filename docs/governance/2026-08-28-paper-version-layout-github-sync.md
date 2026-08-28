# Paper version layout GitHub sync boundary

- `record_id`: `PAPER_VERSION_LAYOUT_GITHUB_SYNC_V1`
- `authorized_at`: `2026-08-28`
- `remote`: `https://github.com/ghy001122/PINN-PCM-SCI`
- `target_branch`: `main`
- `authorization`: user explicitly requested synchronization of the reorganized paper-version structure
- `scientific_claim_effect`: `NONE`

## Canonical layout

The repository-level `paper/` directory is the single paper-package root:

```text
paper/
  README.md
  paper_v1/
  paper_v2/
  paper_v21/
  paper_vxx/   # future versions
```

The former repository-root `paper/` package is renamed `paper/paper_v1/`. The former repository-root `paper_v2/` and `paper_v21/` packages move to `paper/paper_v2/` and `paper/paper_v21/`. Future versioned packages must be created below `paper/`.

## Included synchronization scope

- the three already-published paper packages at their canonical new paths;
- a version index at `paper/README.md`;
- path-sensitive package builders, validators, figure generators, manifests, and reproducibility commands;
- live documentation links and status references needed to resolve the new locations;
- Git rename/deletion records required to remove the obsolete repository-root layouts.

## Exclusions and claim boundary

This synchronization does not include unrelated untracked modules, caches, external skills, scratch directories, credentials, commercial assets, or raw large numerical arrays. Historical experiment manifests and execution records are not rewritten merely because the presentation packages moved.

The synchronization is an engineering traceability action only. It does not change any terminal scientific disposition and does not establish oracle, event, baseline, PINN, PHA-MF, KC, GPU, formal/OOD, or experimental evidence.
