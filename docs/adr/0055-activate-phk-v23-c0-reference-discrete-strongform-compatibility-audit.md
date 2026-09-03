# ADR 0055：激活 PHK-V2.3 C0 reference/discrete/strong-form compatibility audit

- `status`: `ACCEPTED_ACTIVE`
- `date`: `2026-09-03`
- `phase_id`: `PHK_V23_C0_REFERENCE_DISCRETE_STRONGFORM_COMPATIBILITY_AUDIT_EXECUTE`
- `supersedes_authorization_only`: `PHK_V23_R1X_BOUNDED_CLEAN_COUPLING_CAMPAIGN_EXECUTE_COMPLETE`
- `preserves_scientific_evidence`: `V22R_R0A_R0B_R0C_R1A_R1X`

## 决定

执行一次本地 CPU/FP64 compatibility audit。审计使用 PHK-V2.1 nominal medium、fine、extra-fine、medium-half-dt、fine exact-replay development carriers，冻结的 R1X 2048-point readiness pool，以及已形成的 E2 prediction carrier。代码只输出 compact scalar statistics、hash、公式身份和机器结论。

该执行不构造或加载神经网络，不 forward/backward、不调用 optimizer、不重放 reference solver、不使用 GPU、不连接或关闭当前 AutoDL 实例，也不读取 stress。

## 科学问题

判断 event-competent fixed-discretization reference、R1X readiness、native FVM operator、PINN continuous strong form、初值/边界与 E2 hard output parameterization 是否属于可比较对象。特别区分：

- reference 自身不通过 readiness；
- deterministic pool 漏检；
- E2 场缺少局域驱动；
- native-discrete 与 saved-cadence strong-form 不相容；
- output transform 从数学上排除 reference event support。

## 冻结裁决

PRIMARY 只能是合同列出的五类 machine outcome。若多个问题并存，按冻结 threshold-normalized score 选择 PRIMARY，最多一个 SECONDARY；PRIMARY 唯一映射一个 next recommendation。2–10 倍 residual/floor 灰区在现有 carrier 缺少 cellwise internal-step state 时归入 exact-native-replay inconclusive，不得标为 compatible 或 dominant mismatch。

## 证据边界

C0 是 nominal local development diagnostic，不是 method、competence、continuum truth、formal OOD 或 stress evidence。任何下一路线均需新合同与新 `EXECUTE`；旧 No-Go 和历史产物不追溯改写。

精确合同见 [C0 compatibility contract](../../configs/phk_v23/c0_reference_discrete_strongform_compatibility_contract.json)。
