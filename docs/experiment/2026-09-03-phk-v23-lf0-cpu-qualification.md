# PHK-V2.3 LF0 CPU qualification

- `phase_id`: `PHK_V23_LF0_EXACT_TOP_WARMSTART_ATTRIBUTION_EXECUTE`
- `run_id`: `20260903T064928Z-phk-v23-lf0-cpu-qualification-28b2b9b`
- `source_commit`: `28b2b9bb216920f54c50f3ae1c9bf9313b88635d`
- `source_identity`: `LF0-BUNDLE-A30B661FF81059155EFDFDE908E3A21B53365BA5B7034E730BDD12AD0C758152`
- `gate_outcome`: `LF0_CPU_QUALIFIED`
- `next_research_execution_authorized`: `true`
- `next_action`: `RESTART_AUTODL_AND_EXECUTE_LF0_RUN_A`

## 结果

唯一 CPU/FP64 资格运行通过，未构造 neural model、未加载 checkpoint、未创建或调用 optimizer、未使用 GPU，也未读取 stress。medium、fine 与 extra-fine nominal development carriers 的 exact-top raw required latent 均 finite，且三者都通过独立 potential maximum-principle guard。

medium carrier 通过原两周期 competence gate。C0 官方 strong-form 子门保持为 residual/floor `1.9140757262 <= 2`、RHS sign agreement `1.0 >= 0.9`；没有采用会误判的 medium-only numerator。medium 相对 extra-fine 的 phase primary headroom 为 `0.000425 > 0.000145`，co-primary unnormalized headroom 为 `0.00656617 > 0.00229583`。

exact-top、A/B/条件 C 状态机、medium-only 数据边界和 frozen local adjudicator 的合并回归为 201/201 PASS；当前 document consistency 为 VALID。两份 stress references 继续 `SEALED_UNREAD`。

## 当前边界

该结果只准入 LF0 Run A，不是 solver competence、方法增量或论文正面证据。已知 AutoDL 端点当前不可达，因而 Run A 尚未启动，LF0 scientific GPU run count 仍为 0。用户重启实例后可在同一 campaign 授权下直接继续。

## 证据入口

- [compact qualification](artifacts/20260903T064928Z-phk-v23-lf0-cpu-qualification-28b2b9b.json)
- [run manifest](manifests/20260903T064928Z-phk-v23-lf0-cpu-qualification-28b2b9b.json)
- [deployed source manifest](../../cloud/phk_v23_lf0_autodl/deployed-source-manifest.json)
