# PHK-V2.1 精选 GitHub 同步边界

- `record_id`: `PHK_V21_SELECTED_GITHUB_SYNC_BOUNDARY_V1`
- `authorized_at`: `2026-08-28`
- `remote`: `https://github.com/ghy001122/PINN-PCM-SCI`
- `target_branch`: `main`
- `authorization`: 用户明确要求将最新交付结果同步到云端，并授予完成该同步所需权限
- `scientific_claim_effect`: `NONE`

## 精选纳入范围

- 当前权威状态、研究总览、唯一完成态计划、ADR 与归档指针；
- PHK-V2.1 program/engineering/object/split/oracle-floor/baseline/method 合同及两项 S1 amendment；
- E1/E2/S0/S1/S7 记录、14 个 qualification intents、intent claims、manifests 与 append-only 实验索引；
- PHK-V2.1 solver、design、benchmark、evaluator、runner 代码及对应测试；
- terminal summary、candidate floor carrier、E2 summary/case records 和每个 S1 intent 的小型 report；
- 完整 `paper_v21/`：英文/中文正文、通俗故事、补充、复现、表格、引用、claim audit、六份 CSV、六幅 PNG/PDF 及 package/figure manifests。

## 明确排除

- 14 个 S1 原始 `.npz` 场数组，合计约 492 MB；其中 extra-fine 单文件约 155 MB，超过 GitHub 普通单文件限制。其结果身份、摘要、report、manifest 与哈希仍由精选载体保留；
- `.agents/skills/academic-research-suite/`、`.j2/`、`.tmp/`、`ideaspark_run/`、`configs/eaf_kc_v1/`；
- 与 PHK-V2.1 无关的历史未跟踪 solver/module/test 文件；
- 缓存、`__pycache__`、虚拟环境、凭据、商业资产、外部 GPL/Penn 源码树和其他无关工作区文件；
- `docs/governance/EXTERNAL_SKILLS.md` 的并行未提交修改，因为它不属于本次 PHK-V2.1 交付。

## 安全与科学边界

本次同步只公开用户指定的最新研究交付与最小可读上下文，不包含凭据或商业原始资产。远端提交、推送成功或 CI 状态只证明工程可追溯性，不提升以下科学结论：

~~~text
PHK_V21_ORACLE_NO_GO_STOP_BEFORE_PINN
PHK_V21_ORACLE_NO_GO_STOP_BEFORE_PINN_NO_BASELINE_OR_METHOD_EVIDENCE
~~~

Sharp/PF、合格 neural floor、PINN、PHA-MF、KC、GPU 与 formal/OOD 仍为 `NOT_REACHED`。
