# PHK-V2.3 LF1 AutoDL run card

- Task: `PHK_V23_LF1_EVENT_PRESERVING_MULTIFIDELITY_PILOT`
- Device: `Tesla V100-PCIE-32GB`, FP64
- Seed: `17`
- Order: A, B, then conditional C
- Scientific GPU trajectory limit: three

The cloud bundle contains source plus the exact medium carrier only. Fine,
extra-fine, the frozen evaluator, old checkpoints/predictions, and stress data
remain local. Every arm must pass the zero-update preflight. After each arm,
recover and hash-check all summary-bound artifacts, shut the instance down,
verify shutdown, and only then run local nominal evaluation.

Run A uses 1200 physics updates. Run B uses 1200 event-balanced medium-only
updates; its fixed B0 gate must pass before 1200 physics-plus-0.1-replay
updates. Conditional C continues the exact B0 data optimizer and deterministic
data stream for another 1200 updates and requires the post-B local trigger.

No next research phase, new seed, PJGR/R2, or stress access is implied by this
run card or by a positive single-seed nominal result.
