# Portable array scoring and separate neural reproduction

The manifest identifies sixteen fixed objects: eight historical neural E/F states, one shared interpolant for each of two protocols, and six new phase-head continuations on the earlier-pulse case. Both the original and time-refined references are retained. This is a local submission archive candidate, not a public data release or a DOI.

Run from a clean directory containing this archive with Python 3.11 and NumPy 2:

The independent rescore is configured to use a fresh local virtual environment with only NumPy 2.1.1 installed as its scientific dependency; Torch and SciPy are absent. Its completion record is separate. The archive describes the environment but does not redistribute that installation.

```text
python -I portable/rescore.py --root . --output independently-rescored
```

The scorer is independent of a private checkout and uses only archive-relative paths. It reproduces the original metrics, events and A/B decisions before scoring the new heads and reference perturbation. It performs no neural inference, autodifferentiation, checkpoint loading or linear solve. The NumPy kernels are a frozen extraction of the original evaluator, with serialized geometry and known-physics constants; this is independent execution from the arrays, not an independently invented numerical method. `rescore-output/results.json` records the environment and each reproduced object.

The historical bottom-current gate compares predicted bottom current with the reference top current. That definition is retained for exact reproduction; a separately named bottom-native metric is also reported. Percentages mean normalized RMS errors times 100, not dimensional current errors. Each reference has its own denominator, and fixed-original-denominator diagnostics are stored separately. Both references use the same space grid; the experiment tests temporal sensitivity only.

`data/` contains sparse observations, the four references and the sixteen complete predictions/readouts. `definitions/` contains geometry, ROI, event thresholds, decision rules and frozen protocol definitions. `models/` contains accepted neural/optimizer states, parent states, quadrature/calibration, and deterministic adapter initialization. `training/runtime-source/` preserves the deployed numerical sources and their necessary contracts. Scientific telemetry is retained; connection details, credentials, operational logs, stress inputs and fonts are excluded.

Neural reproduction is separate and incurs scientific compute. The following entry stages a new workspace without executing a model:

```text
python portable/reproduce_network.py --archive . --workspace NEW_EMPTY_DIRECTORY --action prepare
```

Use a different empty directory with `--action train --device cuda:0` to repeat the six authorized continuations and their own projections, or `--action infer --seed 29 --role E_R --device cuda:0` to reproduce one archived endpoint's projection. These operations require the recorded Torch/SciPy environment, and neither is called by array scoring or figure rebuilding. Training uses only the archived short-gap sparse observations, the fixed parent checkpoints and known physics. Full reference arrays are not staged into the neural workspace. This entry does not claim to reproduce the historical clean parents from random initialization; those historical runs have their own repository sources and contracts.

The manuscript's figures are rebuilt from completed scoring JSON/NPZ tables. Rendering a figure, recomputing a score from saved arrays and retraining a neural model are three different reproduction levels.
