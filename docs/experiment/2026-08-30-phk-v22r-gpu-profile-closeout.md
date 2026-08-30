# 2026-08-30 PHK-V2.2R GPU profile closeout

- `status`: `COMPLETE_STRICT_PHA_REMOVED_FOUR_ARM_NOMINAL_PENDING`
- `evidence_role`: `GPU_ENGINEERING_PROFILE_AND_LOCAL_DEVELOPMENT_ROUTING_ONLY`
- `run_id`: `20260830T0122-phk-v22r-d1-gpu-profile-cf372713`
- `source_commit`: `cf3727135eb5f06d0443bbd78f07fd3b429995ff`
- `device`: `Tesla V100-PCIE-32GB`
- `dtype`: `float64`
- `updates_per_arm`: `100`
- `reference_role`: `NOMINAL_DEVELOPMENT_LOCAL_ONLY`
- `stress_reference_read`: `false`

## VERIFIED

| Arm | Seconds/update | Peak GPU memory (bytes) | Final loss | Status |
|---|---:|---:|---:|---|
| `STRONG_RAW` | 0.5496653291 | 302,376,960 | 0.0963784704 | `COMPLETE` |
| `MF_ONLY` | 0.5517378116 | 316,936,704 | 0.1522606092 | `COMPLETE` |
| `SAMPLER_ONLY` | 0.5203022824 | 1,103,145,984 | 0.0975472990 | `COMPLETE` |
| `MF_PLUS_SAMPLER` | 0.5672538270 | 1,158,073,856 | 0.1836570253 | `COMPLETE` |
| `STRICT_PHA_PROBE` | 0.8980283375 | 1,461,667,328 | 0.1972075925 | `COMPLETE` |

Environment identity was Python 3.11.9, PyTorch 2.5.1+cu118 and CUDA 11.8;
CUDA FP64 construction passed. The displayed price was CNY 1.88/hour. Estimated
profile spend was CNY 0.1619446910 and estimated cumulative spend including the
declared CNY 3.5 prior amount was CNY 3.6619446915.

The strict-PHA cost ratio to MF was 1.6276360232, below the frozen 1.8 maximum.
Its primary improvement relative to `MF_PLUS_SAMPLER` was 0 rather than the
required 0.10; both 100-update predictions also failed the development hard
guards. The frozen outcome is therefore
`STRICT_PHA_PRIMARY_GAIN_GATE_FAILED`, with action
`REMOVE_STRICT_PHA_FROM_CRITICAL_PATH_WITHOUT_GATE_TUNING`.

## Evidence boundary

This profile proves finite V100 execution, observed cost and memory, and the
strict-PHA routing disposition. It does not rank the four primary arms, establish
nominal competence, support attributable method gain, freeze a candidate or
authorize stress-reference access. The 100-update local evaluation used only the
nominal development reference; both stress references remain unread and sealed.

Source artifacts remain under
`outputs/runs/20260830T0122-phk-v22r-d1-gpu-profile-cf372713/` and are Git-ignored.
The profile `summary.json` SHA256 is
`5CE0768F7A7A1976D573846D05C244AD4E08E35D3B242292860A39BF097087DD`;
the local adjudication SHA256 is
`7F76F3AA12E9A32F21ECFAB083FB530AC39310C1C83198CB691F8F3A1224BB0E`.
