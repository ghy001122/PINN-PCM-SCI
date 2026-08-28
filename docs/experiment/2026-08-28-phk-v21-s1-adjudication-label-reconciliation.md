# PHK-V2.1 S1 terminal adjudication label reconciliation

- `record_id`: `PHK_V21_S1_COMPONENT_LABEL_CANONICALIZATION_002`
- `status`: `VERIFIED_LABEL_ONLY_ADJUDICATION_FIX_NO_SOLVER_RERUN`
- `effective_date`: `2026-08-28`
- `scientific_effect`: `NONE_UNTIL_TERMINAL_GATE_IS_RECOMPUTED`

全部 14 个 qualification solver intents 已完成。首次调用 terminal summary 在写 run directory、summary、floor、intent、manifest 或 ledger row 之前，以 `ValueError: medium_fine component order mismatch` fail-closed。

核验表明 comparator 依次返回 phase-field RMS、temperature RMS、current-trace RMS、two-cycle event-time RMS、time-averaged phase-region symmetric difference 和 two-cycle recovery RMS；值、公式与冻结 V2.1 endpoint 完全同序。缺陷仅是继承的 V2 短标签 `CURRENT_TRACE_RMS / EVENT_TIME / PHASE_REGION_SYMMETRIC_DIFFERENCE / RECOVERY` 没有映射到 V2.1 长标签。

[机器 amendment 002](../../configs/phk_v21/s1_adjudication_amendment_002.json) SHA256 为 `CEF8764CC58C69BB94B95E790E2D147CF41CDFE3A3A4215E9611187708A99648`。它链接 [amendment 001](../../configs/phk_v21/s1_implementation_amendment_001.json) SHA256 `B50BBADEC521F435EA1AFA923146237851D0B8F8C87922A97C3CBD974C98B6AE`，并把 runner 从 `F801B9F1EA89D2B09364BBC9AEDDBDED8FEDF8DAD125A6C6DB7F569192274E1F` 升级为 `82F300E002CDA045A307508EF4C9DF820A1A4F9132EFDBA1508221552277E501`。修复只按位置替换六个标签，不移动或重算 component values，不修改 object、PDE、solver、cases、阈值、收敛规则或 floor 公式。

任何 solver intent 重跑均被禁止。首次成功的 terminal summary 必须显式绑定两个 amendments，并保留第一次 summary attempt 的 fail-closed 身份。该修复本身不是 oracle PASS 或 No-Go；只有成功写出的 terminal adjudication carrier 才能裁决 S1。

