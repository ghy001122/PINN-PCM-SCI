# PHK-V2.2R terminal tables

## Table 1. Frozen evidence identity

| Item | Value |
|---|---|
| Run ID | `20260830T112225-phk-v22r-v11-nominal-69109cd` |
| Source commit | `69109cd324a6d5bf4690fe981086dc2f987eceed` |
| Program contract SHA-256 | `A413F56A2317CEFF15FFF2D3BD183C11D990F2E47E8BA33F7316F11567275272` |
| Method contract SHA-256 | `FEEFB36A4D86CACFA6CBAA8C263E7071421415CE88B4F7FBF6BA5F31B9B71D4F` |
| Run summary SHA-256 | `721D0ADC537F42622F66CFF7266A287D02A626967E8D9A95F1CFC906C26F03FA` |
| Nominal decision SHA-256 | `15F4D2B1BF53200872E4D05BDBEB832FB8AB7B04D7189C1B7B8286976C7A2943` |
| Nominal reference SHA-256 | `0CE36347433983DB3631C9CD92E3FBFDAEF5A692D3370736071696135FFB73CE` |
| Outcome | `MVP_NO_GO_NO_BASIC_COMPETENCE` |

## Table 2. Frozen nominal configuration

| Property | All arms |
|---|---|
| Case | `FULL` nominal development case |
| Precision | FP64 |
| Seed | 17 |
| Initialization | scratch |
| Optimizer | Adam, learning rate 0.001 |
| Updates | exactly 1000 |
| Points | 512 interior / 128 boundary / 128 initial |
| Causal windows | 4, with equal replay of prior windows |
| Frequency band | Band A where multi-frequency is active |
| Checkpoint | final only |
| Reference access during training | none |

## Table 3. Architecture and compute

| Arm | Trainable parameters | Multi-frequency | Physics sampler | Seconds/update | Wall seconds | Peak GPU memory (GB) | Final total loss |
|---|---:|---|---|---:|---:|---:|---:|
| `STRONG_RAW` | 39,939 | No | No | 0.486627 | 486.627 | 0.302 | 0.009918 |
| `MF_ONLY` | 54,915 | Yes | No | 0.538152 | 538.152 | 0.317 | 0.066177 |
| `SAMPLER_ONLY` | 39,939 | No | Yes | 0.487587 | 487.587 | 1.103 | 0.026678 |
| `MF_PLUS_SAMPLER` | 54,915 | Yes | Yes | 0.537702 | 537.702 | 1.158 | 0.075853 |

## Table 4. Nominal local-reference metrics

| Arm | Primary symmetric difference | Phase ROI RMS | Temperature ROI nRMSE | Current nRMSE | High-k phase error | Pulse-energy relative error |
|---|---:|---:|---:|---:|---:|---:|
| `STRONG_RAW` | 0.005150 | 0.110471 | 0.398675 | 0.286641 | 1.000307 | 0.505937 |
| `MF_ONLY` | 0.005150 | 0.110548 | 1.063750 | 0.956086 | 1.000442 | 0.990104 |
| `SAMPLER_ONLY` | 0.005150 | 0.110408 | 0.388095 | 0.234011 | 1.000654 | 0.638178 |
| `MF_PLUS_SAMPLER` | 0.005150 | 0.110528 | 0.982255 | 0.995063 | 1.001382 | 0.999920 |

## Table 5. Event-competence adjudication

| Guard | Strong raw | MF only | Sampler only | MF + sampler |
|---|---|---|---|---|
| Finite values | Pass | Pass | Pass | Pass |
| Phase range | Pass | Pass | Pass | Pass |
| Decreasing logged PDE loss | Pass | Pass | Pass | Pass |
| Cycle-1 event exists | Fail | Fail | Fail | Fail |
| Cycle-1 minimum ROI peak | Fail | Fail | Fail | Fail |
| Cycle-1 recovery | Fail | Fail | Fail | Fail |
| Cycle-2 event exists | Fail | Fail | Fail | Fail |
| Cycle-2 minimum ROI peak | Fail | Fail | Fail | Fail |
| Cycle-2 recovery | Fail | Fail | Fail | Fail |
| Eligible for ranking | No | No | No | No |

## Table 6. Cost accounting

| Quantity | CNY |
|---|---:|
| Prior plus profile closeout estimate | 3.6619446915 |
| Four-arm nominal stage estimate | 1.1481133733 |
| Cumulative estimate at shutdown | 4.8100580653 |
| Hard cap | 150.0000000000 |

These are runtime estimates at the displayed CNY 1.88/hour, not a billing
statement.
