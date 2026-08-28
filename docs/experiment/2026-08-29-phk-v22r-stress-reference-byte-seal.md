# 2026-08-29 PHK-V2.2R stress extra-fine byte seal

- `status`: `COMPLETE_BOTH_REFERENCES_SEALED_UNREAD`
- `evidence_role`: `REFERENCE_GENERATION_AND_BYTE_IDENTITY_ONLY`
- `program_contract_sha256`: `748B8D193697FC76154969DD5DEE8D7289BF59C0E054E3456BD4C4E939684DE6`
- `candidate_status`: `NOT_FROZEN`
- `field_or_metric_read`: `false`

## VERIFIED

| Control | Carrier | Bytes | Generation wall seconds | SHA256 | Seal status |
|---|---|---:|---:|---|---|
| `INTERFACE_WIDTH_0_025` | `outputs/sealed/phk_v22r/narrow_interface_extra_fine/reference.npz` | 154,751,976 | 2913.5202028 | `C2C01F31E23869DB1E54A5938F5DFCFC6491EA6583D49B8635C56678F09BD0CD` | `SEALED_UNREAD_PENDING_CANDIDATE_FREEZE` |
| `HEATER_WIDTH_0_50` | `outputs/sealed/phk_v22r/wide_heater_extra_fine/reference.npz` | 155,426,149 | 2532.2229943 | `1A72CD23B10E6E048BC72936A43A41F165A9B37758E012CD296574D50D27422A` | `SEALED_UNREAD_PENDING_CANDIDATE_FREEZE` |

两个 carrier 均由既有 PHK-V2.1 fixed solver 在 `extra_fine`（160 × 80、
`dt=0.000625`、`save_every=4`）上各执行唯一一次。runner 在求解前写入 intent，
求解完成后只写 carrier 和 byte seal。随后使用独立文件 SHA256 复核，实际值与 seal
声明值逐字节一致。

## 尚未授权的读取

本记录没有加载 NPZ 内任何 field、time trace、event、guard 或 metric。只有
`configs/phk_v22r/candidate_freeze.json` 以 `FROZEN` 状态形成后，本地 evaluator
才能打开两个 carrier；云端永远禁止接收它们。成功生成 reference 不是 neural
method、event robustness 或正面论文 claim 的证据。
