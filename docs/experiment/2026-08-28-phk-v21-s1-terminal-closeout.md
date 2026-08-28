# PHK-V2.1 S1 terminal closeout

- `record_id`: `PHK_V21_S1_TERMINAL_CLOSEOUT_V1`
- `phase_outcome`: `PHK_V21_ORACLE_NO_GO_STOP_BEFORE_PINN`
- `execution_status`: `COMPLETED_14_OF_14`
- `numerical_validity`: `VALID_BOUNDED_SYNTHETIC_NEGATIVE_QUALIFICATION`
- `claim_status`: `PHK_V21_ORACLE_NO_GO_NO_PINN_OR_METHOD_EVIDENCE`
- `effective_date`: `2026-08-28`

## Outcome first

`VERIFIED`：PHK-V2.1 的 14/14 个冻结 qualification intents 均完成，0 execution failures、0 hard-guard failures；nominal coarse、medium、fine、extra-fine、medium-half-dt、fine replay 和 pseudo-transient solver cross-check 均形成两周期 event，zero-drive 与 Joule-off 均无 event，fine exact replay 最大数组差为 `0.0`。但是 event-time 分量的空间差从 medium→fine 的 `0.0012067679515502204` 上升到 fine→extra-fine 的 `0.0016486829760616161`，违反逐分量空间单调收敛硬门。因此完整 S1 结果为：

~~~text
PHK_V21_ORACLE_NO_GO_STOP_BEFORE_PINN
PHK_V21_ORACLE_NO_GO_NO_PINN_OR_METHOD_EVIDENCE
~~~

该 No-Go 只关闭冻结的 PHK-V2.1 数值资格合同。它不是物理模型普遍失败、PINN 失败、PHA/KC 失败、真实材料结论或实验验证。

## Frozen identities

- S0 scientific freeze: [`2026-08-28-phk-v21-s0-scientific-contract-freeze.md`](../governance/2026-08-28-phk-v21-s0-scientific-contract-freeze.md)
- object contract SHA256: `BDC86AE4C1417E16A8772A88F7738B59D4F0D7BB3B272D1FFEC9E9572CF9CBDD`
- split file SHA256: `FC4F27D92618BBDF222961340C7BDA3FA8CB3FEF918D0CF343A48A5387F4BAB7`
- oracle/floor contract SHA256: `E596A5D50BB79A241928D98AC000BDCDD3AD7AF0B207BD5882F2D1C2EBB2E5FB`
- baseline contract SHA256: `195C039C181DCF012F94B77DA5D03EFF3244CDCA2F4A63FF5DEDB6FD7747EBC4`
- method contract SHA256: `F1E918E6C71557BF7ABBAE11519208BD3D042D04AC6AF04471F33CCB046A001D`
- terminal summary SHA256: `5E6343D3E8DFE63C1C3F2F031FCF04B455E8C53B5BF454F8AFA013D33C33A9C9`
- terminal manifest SHA256: `607CF2F5B58715F6B9335A4CF41379A311DAA9DF1C7CEA880F0A534AF5923455`
- candidate floor carrier SHA256: `3B71753CBAC720C1CF5F7937741FCF605693C5580988C848113AC9378F1A01F7`

The floor carrier records all component deltas but is not an admissible neural-floor seal because `floor_sealed_and_converged=false`. No downstream process may consume it as a qualified oracle floor.

## Intent accounting

| # | intent/control | execution | numerical guard | event identity | CPU s |
| ---: | --- | --- | --- | --- | ---: |
| 1 | manufactured operators | completed | n/a | n/a | 0.015625 |
| 2 | zero drive, medium | completed | pass | required no-event pass after immutable-carrier reconciliation | 47.359375 |
| 3 | nominal coarse | completed | pass | two-cycle pass | 19.359375 |
| 4 | nominal medium | completed | pass | two-cycle pass | 105.40625 |
| 5 | nominal fine | completed | pass | two-cycle pass | 512.125 |
| 6 | nominal extra-fine | completed | pass | two-cycle pass | 1915.8125 |
| 7 | nominal medium half-dt | completed | pass | two-cycle pass | 238.125 |
| 8 | fine exact replay | completed | pass | two-cycle pass; max array delta 0 | 556.40625 |
| 9 | Joule gain zero | completed | pass | required no-event pass | 54.265625 |
| 10 | conductivity phase ratio one | completed | pass | event retained; recorded only | 117.4375 |
| 11 | latent ratio zero | completed | pass | event retained; recorded only | 118.78125 |
| 12 | heater width 0.50 | completed | pass | cycle 2 missing; recorded geometry sensitivity | 114.453125 |
| 13 | interface width 0.025 | completed | pass | two-cycle pass; recorded only | 129.421875 |
| 14 | pseudo-transient solver cross-check | completed | pass | two-cycle pass | 133.6875 |

Total recorded qualification compute was `4062.65625` CPU seconds = `1.128515625` process CPU core-hours; sum single-thread wall time was `4113.6542242` seconds. All failed-attempt and amendment work remained local; no paid, cloud or GPU compute was used.

## Six-component convergence

| component | medium→fine | fine→extra-fine | monotonic | strict contraction | recorded candidate U |
| --- | ---: | ---: | --- | --- | ---: |
| phase-field ROI RMS | 0.009164723390798192 | 0.0045916542647892284 | pass | pass | 0.0045916542647892284 |
| temperature-field ROI RMS | 0.0025375404500889136 | 0.001256919148376367 | pass | pass | 0.0017839022220207273 |
| terminal-current trace RMS | 0.002326069016938981 | 0.0012107207785293857 | pass | pass | 0.0020456785528971074 |
| two-cycle event-time RMS | 0.0012067679515502204 | 0.0016486829760616161 | **fail** | **fail** | 0.0016486829760616161 |
| time-averaged phase-region symmetric difference | 0.00030374999999999993 | 0.000145 | pass | pass | 0.000145 |
| two-cycle recovery RMS | 0.0 | 0.0 | pass at declared tolerance | pass at declared tolerance | 0.000001 |

The event-time failure cannot be averaged away by the five passing components. The stored event times nevertheless remain finite and close: coarse `0.2271/1.4871`, medium `0.2378/1.4942`, fine `0.2389833/1.495975`, and extra-fine `0.2406/1.4984`. The frozen gate asks a stricter question than visual plausibility: whether the component-wise refinement error contracts monotonically under the specified hierarchy. It does not.

## Controls and bounded interpretations

- `SUPPORTED_INTERPRETATION`: Within this transparent synthetic object, Joule heating is necessary for the nominal switching event because nominal cases pass while Joule-gain-zero has exactly zero ROI peak and no event.
- `SUPPORTED_INTERPRETATION`: Phase-dependent conductivity and the frozen latent term are not individually necessary for the event under their specific controls, because those control cases remain event-positive.
- `SUPPORTED_INTERPRETATION`: The selected object is geometry-sensitive: heater width 0.50 loses the second-cycle event, whereas interface width 0.025 retains it.
- `UNKNOWN`: Whether a different, prospectively frozen numerical contract would restore monotonic event-time convergence. This GOAL does not alter or rerun the contract to answer that question.

## Reconciled implementation defects

Two implementation-layer defects were fixed without rerunning any scientific solver intent or changing a scientific value:

1. [intent 02 carrier reconciliation](2026-08-28-phk-v21-s1-intent-02-carrier-reconciliation.md): `dataclasses.asdict` preserved a tuple that a list-only no-event helper rejected. Original result/report/manifest remained immutable; the no-event Boolean was recomputed from the original two cycles.
2. [terminal label reconciliation](2026-08-28-phk-v21-s1-adjudication-label-reconciliation.md): inherited short component labels were mapped position-for-position to the V2.1 long labels. No values were reordered or recomputed. The first summary attempt wrote no summary, floor, intent, manifest or ledger row.

Both amendments are carried explicitly in the successful terminal summary. Neither amendment supplies scientific evidence.

## Downstream disposition

The following are `NOT_REACHED` and consume zero training/formal case intents:

- Sharp-PINNs and PF-PINNs author-metric replication;
- a qualified neural floor;
- strong raw PINN and its D/I1 competence gate;
- four-arm bottleneck diagnosis;
- PHA-MF, field-selective KC, their 2×2 attribution and all mechanism/capacity challengers;
- local GPU development;
- F_A/F_O formal OOD and statistical superiority/noninferiority tests;
- any positive second-version PINN method claim.

The approved route therefore transitions directly to the evidence-bounded terminal manuscript and reproducibility package. PHK-V2 and all earlier No-Go results remain unchanged.

