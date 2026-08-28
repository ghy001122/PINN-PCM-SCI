# Baseline anatomy cards

These cards preserve the preregistered identities and scientific boundaries of the intended downstream comparators. Because the S1 oracle gate failed, none was executed as a voting baseline in PHK-V2.1.

## Card A. Evidence labels

Three identities are mutually exclusive:

| Label | Meaning | PHK-V2.1 status |
| --- | --- | --- |
| OFFICIAL_PAPER_METRIC_REPRODUCTION | original PDE, configuration, data/reference and evaluator compared with a declared paper figure/table | NOT_REACHED |
| PINNED_REPO_RECIPE_REPLICATION | one complete official repository SHA and one declared recipe, with paper drift reported | NOT_REACHED |
| CLEAN_ROOM_COMPARATOR_ADAPTATION | formula-derived reimplementation on the same PHK object, split, budget and evaluator | NOT_REACHED |

Running author code would not automatically establish paper-metric reproduction. A clean-room PHK adaptation would not be called an official reproduction.

## Card B. Sharp-PINNs phase-field anchor

### Original idea

Sharp-PINNs targets coupled Allen-Cahn/Cahn-Hilliard corrosion phase fields. The formal paper combines:

- staggered training across equation blocks;
- random Fourier features;
- a modified MLP;
- hard output constraints;
- gradient-norm weighting;
- periodic resampling.

### Intended reproduction target

- original-domain case: two-dimensional two-pits;
- paper identity: SHARP_PAPER_2D_2PITS_V1;
- primary point target: absolute L2 error 6.066e-4;
- visual target: contours at the four declared times;
- attribution target: full six-arm Table 2 ordering.

### Paper/repository drift

The fixed official repository at commit 4b7029e3e1e0b82482d245ba12e3ec0945d87ed9 adds causal weighting and residual-adaptive refinement and uses an 800,000-epoch recipe, whereas the paper reports a 1,000-step identity for the selected case. These identities cannot be silently merged.

### Limitations and migration opportunity

- main paper results do not provide a reusable multi-seed uncertainty protocol;
- reported timing mixes GPU PINN and CPU FEniCS;
- the method is phase-field relevant but does not contain an electrothermal hotspot router or field-selective kinetics clock;
- GPL-3.0 source must remain isolated unless redistributed under compatible terms.

### PHK status

NOT_REACHED. No author metric, repository recipe, seed, or PHK adaptation was run.

## Card C. PF-PINNs sampling and weighting anchor

### Original idea

PF-PINNs combines:

- variable scaling and de-scaling;
- initial/interface-local refinement;
- adaptive moving-interface sampling;
- random-batch NTK loss weighting.

### Intended reproduction targets

1. PF_PAPER_1D_ACTIVATION_V1:
   - Table 3 MSE/R2 values;
   - direction of random-batch NTK improvement over no weighting and full-gradient weighting;
   - actual batch ordering, without assuming larger batch is always better.
2. PF_PAPER_2D_SEMICIRCLE_V1:
   - average field MSE 6.658e-4;
   - interface-local error;
   - radius trajectory R2 0.988.

### Paper/repository drift

The fixed repository at commit a25f75b5fd40657e5ce98467d7afd0d0052464d1 changes several collocation, initial-condition, NTK batch, and epoch counts relative to the paper. The two official PF repositories cannot be source-stitched.

### Limitations and migration opportunity

- paper averages are primarily field/time averages, not seed uncertainty;
- global MSE may hide an interface displacement approaching order-one local error;
- adaptive sampling can imitate a representation gain unless the support is equalized;
- GPL-3.0 code remains an isolated comparator.

### PHK status

NOT_REACHED. Neither 1D nor 2D author-metric reproduction was run.

## Card D. PirateNet and adaptive pseudo-time control

### Original idea

jaxpi2 adaptive pseudo-time adds a residual-relaxation term between successive parameter iterates and combines it with collocation resampling. Its strong architecture is PirateNet with causal training and gradient-norm adaptation. The method is not a reparameterization of physical time.

### Intended role

The PHK clean-room control would keep the same strong-raw network, support, optimizer, seed, update budget and evaluator while adding only adaptive residual pseudo-time. It was designed to falsify an overly broad KC story:

> If generic residual continuation explains the same gain as field-selective KC, the kinetics-specific claim must shrink or fail.

### Limitations

- best fixed pseudo-time uses oracle-aware selection and is not a fair deployment default;
- main benchmark table values are point estimates;
- Allen-Cahn is near its reported float32 floor and is not a useful PHK headline target;
- official environment and dependencies must remain isolated and source-pinned.

### PHK status

NOT_REACHED. The fixed commit and source identity were audited, but no PHK voting control was run.

## Card E. Intended PHK equal-budget family

### Strong raw

The proposed raw baseline would already include strong common practices: residual-based sampling, frozen causal schedule where applicable, balanced losses, hard constraints, matched support, and the same complete-case split.

### Bottleneck diagnosis

Four arms were planned:

1. strong raw;
2. global multi-frequency;
3. phase-aware sampling;
4. global multi-frequency plus phase-aware sampling.

Only a super-additive representation pattern would admit the PHA routing headline. A sampling-only gain would be labeled support scarcity; across-arm failure would prioritize optimization/stiffness.

### PHA-MF

PHA-MF would route multi-frequency capacity using phase-interface and Joule-hotspot features. It had to beat global MF, wider raw, extra-work raw, phase-only/Joule-only/generic/shuffled gates, not merely vanilla PINN.

### Field-selective KC

KC would warp only the phase branch through a strictly monotone clock while preserving the physical-time pullback. It had to beat identity, parameter-matched generic monotone, random fixed, all-field warp, wrong-segment and adaptive pseudo-time controls.

### Full combination

The 2x2 family was raw, PHA-only, KC-only and PHK-full. Full could not hide a failed standalone module. At least one declared structural/device co-primary had to show a statistically supported gain over the strongest qualified baseline, while the other co-primary and all critical physical endpoints remained noninferior.

### PHK status

NOT_REACHED. No network was initialized, trained, selected, or evaluated.

## Final baseline boundary

This package documents what would have counted as a fair, strong comparison. It does not claim that any original paper metric was reproduced, that any comparator failed locally, or that PHA-MF/KC would improve a qualified benchmark.
