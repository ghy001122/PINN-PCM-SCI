# 2026-08-30 PHK-V2.2R v1.1 nominal terminal closeout

- `status`: `MVP_NO_GO_NO_BASIC_COMPETENCE`
- `evidence_role`: `BOUNDED_SYNTHETIC_METHOD_MVP_NOMINAL_NEGATIVE_RESULT`
- `run_id`: `20260830T112225-phk-v22r-v11-nominal-69109cd`
- `source_commit`: `69109cd324a6d5bf4690fe981086dc2f987eceed`
- `device`: `Tesla V100-PCIE-32GB`
- `dtype`: `float64`
- `seed`: `17`
- `updates_per_arm`: `1000`
- `nominal_reference_role`: `LOCAL_DEVELOPMENT_SCORING_ONLY`
- `stress_reference_read`: `false`
- `confirmation_training_authorized`: `false`

## VERIFIED: execution and integrity

The frozen four-arm matrix completed on the authorized V100 with
`OMP_NUM_THREADS=1`. All cloud predictions were reference blind. The recovered
run contains 26 files and 860,924,050 bytes. The local SHA-256 values of the run
summary and all four prediction carriers matched the cloud values before the
instance was shut down. The shutdown command returned success and the subsequent
SSH probe was refused.

The run summary SHA-256 is
`721D0ADC537F42622F66CFF7266A287D02A626967E8D9A95F1CFC906C26F03FA`.
The local nominal decision SHA-256 is
`15F4D2B1BF53200872E4D05BDBEB832FB8AB7B04D7189C1B7B8286976C7A2943`.
Program and method contract SHA-256 values are respectively
`A413F56A2317CEFF15FFF2D3BD183C11D990F2E47E8BA33F7316F11567275272`
and
`FEEFB36A4D86CACFA6CBAA8C263E7071421415CE88B4F7FBF6BA5F31B9B71D4F`.

The displayed price was CNY 1.88/hour. Estimated nominal-stage spend was CNY
1.1481133733 and estimated cumulative spend was CNY 4.8100580653, well below the
CNY 150 hard cap. These are runtime estimates at the displayed price, not a
platform invoice.

## VERIFIED: nominal metrics

| Arm | s/update | Peak GPU GB | Final total loss | First -> final PDE loss | Primary | Phase ROI RMS | Temp. nRMSE | Current nRMSE | Hard guards |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| `STRONG_RAW` | 0.486627 | 0.302 | 0.009918 | 0.117633 -> 0.005137 | 0.005150 | 0.110471 | 0.398675 | 0.286641 | FAIL |
| `MF_ONLY` | 0.538152 | 0.317 | 0.066177 | 0.730313 -> 0.001452 | 0.005150 | 0.110548 | 1.063750 | 0.956086 | FAIL |
| `SAMPLER_ONLY` | 0.487587 | 1.103 | 0.026678 | 0.221026 -> 0.004885 | 0.005150 | 0.110408 | 0.388095 | 0.234011 | FAIL |
| `MF_PLUS_SAMPLER` | 0.537702 | 1.158 | 0.075853 | 1.033186 -> 0.006700 | 0.005150 | 0.110528 | 0.982255 | 0.995063 | FAIL |

All four predictions remained finite and in range, and all four logged PDE losses
decreased. None reproduced either reference-aligned phase event. Each arm had the
same six hard-guard failures:

- cycle-1 event missing, ROI peak below minimum, and recovery failure;
- cycle-2 event missing, ROI peak below minimum, and recovery failure.

The maximum phase value over each complete prediction carrier was approximately
0.029993, inherited from the initial seed; the predicted active fraction above
the frozen phase threshold 0.5 was zero throughout. The reference reached ROI
active fractions 0.068698 and 0.061983 in the two cycles. Consequently, the
apparently small and identical primary value 0.00515 is the time-averaged support
of the missed localized reference events, not evidence of competent
reconstruction. Event-time and interface-Hausdorff errors are undefined/infinite
because the predicted events do not exist.

## Terminal adjudication

The frozen decision machine returned:

```text
status=MVP_NO_GO_NO_BASIC_COMPETENCE
reason=ALL_FOUR_ARMS_FAILED_FROZEN_COMPETENCE_GUARDS
selected_arm=null
strongest_comparator=null
confirmation_training_authorized=false
stress_unseal_authorized=false
terminal_no_rescue=true
```

This closes the v1.1 Method-MVP route before candidate freeze. It prohibits a
new seed, additional updates, another module, raw-control calibration,
confirmation training, and stress-reference access within this sprint.

## Interpretation and boundary

- `VERIFIED`: finite V100 execution and decreasing physics loss did not produce
  either required phase event under the frozen 1000-update protocol.
- `SUPPORTED_INTERPRETATION`: the shared failure is a near-initial-phase
  attractor under this training budget and contract; physics-loss convergence
  alone was not a competence certificate.
- `UNKNOWN`: whether a different seed, longer training, loss reformulation,
  continuation, optimizer, or architecture would recover the events. Those are
  new research axes and were neither tested nor authorized as rescue actions.
- `UNKNOWN`: stress-case behavior. Both stress references remain
  `SEALED_UNREAD`; no robustness or formal-OOD claim is available.

This result is fixed-discretization, case-specific synthetic numerical evidence.
It is not experimental validation, continuum truth, a global failure of PINNs,
or a claim that field-selective representation and physics-aware sampling can
never work.
