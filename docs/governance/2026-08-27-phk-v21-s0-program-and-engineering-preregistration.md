# PHK‑V2.1 S0 program 与工程沙盒预注册

- `date`: `2026-08-27`
- `phase_id`: `PHK_V21_E0_ENGINEERING_PREFREEZE`
- `record_status`: `PRE_NEW_ENGINEERING_AND_SCIENTIFIC_RESULT_CONTRACT_FROZEN`
- `scientific_evidence_status`: `NO_PHK_V21_SCIENTIFIC_EVIDENCE`
- `preserves`: `PHK_V2_COMPLETE_ORACLE_NO_GO_AND_ALL_PRIOR_EVIDENCE`

## 冻结输入

| 载体 | 作用 | SHA256 |
| --- | --- | --- |
| `E:/PINN-PCM/总体审查结论.md` | 用户批准的审查与新 GOAL 输入 | `7699E601DE20A968FA54F9E773D75F93D985019DE421A90829E211EEB27CD3F6` |
| `configs/phk_v21/program_contract.json` | 新路线、预算、方法门、统计与停止规则 | `B47CB3E131326077EF8D3EC50473B4F6A06D61E63B09861ECEF834901BE4D2A2` |
| `configs/phk_v21/engineering_contract.json` | P0 红色 fixture、求解候选、32-case 搜索和选择规则 | `DF835E701660E4BC91F585F4DFAA22075DBCAAA754B7716921E766066BD7605A` |
| `docs/adr/0046-adopt-phk-v21-independent-engineering-science-contract.md` | 授权解释与历史隔离 | `217929217D873379084779C852F3E911D17C3F6F91509826C56A670F8B09CDAA` |

`VERIFIED_PRE_E2_AMENDMENT`：`engineering_contract.json` 的初始 E1 freeze SHA256 为 `04F91EB90876773300426B80BEA5D6976E96545503C1642D47FC4870283124DA`。在任何 E2 candidate 结果产生前，只补充了原已批准 ranking 字段的精确定义、medium 唯一选择规则和六控制接受语义；当前 SHA256 如上。E1 结果及选择另见不可充当科学证据的 [`e1_solver_selection.json`](../../configs/phk_v21/e1_solver_selection.json)，SHA256 `A452D4E387A2C2E2AD0924D7CECD0E941A68088A48070F2F105AE81BF978A2DC`。

## 工程与科学的分界

E1–E2 是 `NON_VOTING_ENGINEERING_ONLY`。允许在冻结候选集合和 24 CPU core-hour 内修复求解器并选择对象；这些结果只决定新 scientific contract 的输入，不进入方法比较或论文正面结果。

进入 S0 science freeze 前必须同时满足：固定求解方案在最小红色 fixture、nominal/Joule-off/conductivity-off sentinel 和 exact replay 上通过；唯一候选在 coarse/medium 与全部六个 controls 上可执行，并满足两周期 event、recovery、drift 与 locality 门。随后必须生成新的 complete-case universe/split、oracle ladder、neural floor、baseline replication 和 method contracts。PHK‑V2 旧 split 禁止复用。

## 自动推进与停止

用户已授权在新合同预算与门内自动推进，无需逐阶段重新批准。任一门失败时不得通过降低 recovery/event 阈值、换 case、删 seed、增加预算或切换对象制造 PASS；按 machine contract 的 terminal route 完成有边界论文与复现包。

## 当前证据边界

`VERIFIED`：用户批准了独立 PHK‑V2.1 GOAL；旧 PHK‑V2 No-Go 被明确保留；工程搜索与科学 freeze 的职责已分开。

`UNKNOWN`：任何新 solver、可恢复对象、oracle、Sharp/PF 复现、neural floor、strong raw、PHA-MF、KC、组合或 formal 结果。
