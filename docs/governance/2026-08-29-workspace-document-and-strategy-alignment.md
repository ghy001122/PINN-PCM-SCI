# 2026-08-29 工作区文档与研究策略对齐

- `status`: `COMPLETED_DOCUMENT_AUDIT`
- `scope`: `FIRST_PARTY_DOCUMENT_INVENTORY_LIVE_AUTHORITY_REVIEW_AND_RECENT_STRATEGY_INTEGRATION`
- `scientific_execution`: `NONE`
- `claim_status`: `NO_NEW_SCIENTIFIC_EVIDENCE`
- `effective_phase`: `PHK_V22_ONE_WEEK_SPRINT_ACTIVE`

## 审查范围

本轮先按固定权威链逐项读取 `AGENTS.md → CODEX_CONTEXT.md → docs/README.md → norms → rules.md → active_phase.md → PROJECT_STATE.md → NEXT_ACTIONS.md`，再核对 V2.2R program/method contracts、ADR 0047、当前论文包、文档索引和历史归档。用户指定的实时会话 `6a8f9ed2-a678-83ee-ac63-3fc48de531f8` 已重新读取，近期方法组合、止损和论文故事讨论只在当前合同允许的范围内整合。

机器巡检覆盖项目一方的根文档、`docs/`、`paper/`、`archive/` 和 `configs/`，更新后共 207 个 Markdown 与 218 个 JSON。`.git`、`.venv`、外部 Skills、缓存、临时目录和无关未跟踪实验草稿不进入本次文档修订面；数量只说明扫描范围，不构成质量或科学证据。

## 当前状态核对

四个状态面 `active_phase.md`、`README.md`、`PROJECT_STATE.md` 与唯一 live plan 一致：

- phase：`PHK_V22_ONE_WEEK_SPRINT_ACTIVE`；
- blocker：`AUTODL_INSTANCE_ENDPOINT_PENDING_USER_ACTION`；
- plan：`ACTIVE_D0_FULLSHAPE_PREFLIGHT_VERIFIED_GPU_PROFILE_PENDING`；
- claim：`IMPLEMENTATION_VERIFIED_NEURAL_METHOD_RESULT_NOT_YET_ESTABLISHED`。

`PROJECT_STATE.md` 中的 13/13 V2.2R focused tests、44/44 扩展回归、两份 sealed stress reference 字节身份和五臂 full-shape CPU 非投票预检彼此相容。GPU profile、nominal 排序、方法增量、sealed confirmation 和最终论文分支仍未建立。当前状态文件无需重写；本轮没有用文档更新冒充科研进展。

## 发现与处置

### 1. CONTEXT 角色漂移与过期测试计数

`CONTEXT.md` 被文档地图定义为研究设定和论文口径源，却混入测试数量、封存求解和授权等易过期运行事实，其中 focused-test 数仍为 12，与当前 13/13 冲突。

处置：删除该运行事实段，不把 12 机械改成 13；新增 fixed-discretization reference、development/sealed case、functional pivot、candidate freeze、Method-MVP、device-QoI 和 A→A′ adaptation 等稳定术语。授权、状态和行动分别路由到 active phase、project state 与 live plan。

### 2. 近期研究讨论缺少固定入口

实时会话中的“开发功利、确认冻结”、功能槽替换、四类结果故事、十类止损和稿后扩展尚未形成项目内可追溯入口，后续执行容易只记住“追求正结果”而忽略冻结合同。

处置：新增 [PHK-V2.2R 近期研究策略整合](../notes/2026-08-29-phk-v22r-recent-research-strategy-integration.md)，并从 `README.md`、`CODEX_CONTEXT.md`、`CONTEXT.md`、本地图和 notes 索引路由。该笔记明确不新增授权、不移动结果门、不把会话当一手文献，并把 same-arm warm start、TEGNet/SyncNet、参数化模型等限定为条件 pivot 或稿后工作。

### 3. 历史归档链接失效

全量 Markdown 链接巡检发现 22 个真实失效链接，均来自两份计划移入 `archive/` 或论文迁入 `paper/paper_vxx/` 后仍使用旧目录深度。

处置：只修复 `archive/2026-08-27-goal-paper-one-shot-v1-complete.md` 与 `archive/2026-08-29-plan-phk-v21-completed.md` 的目标路径；历史状态、合同、预算、No-Go 和授权语义未改写。

### 4. 当前论文和历史证据边界

`paper/paper_v22r/` 仍将未测 profile、nominal、消融和 stress 结果登记为 `NOT_YET_MEASURED`，没有从实现测试或 CPU 预检预写正面结果。PHK-V2.1/V2/V1 与更早历史文档保留原状态，只修可达路径，不将旧 formal OOD、旧方法计划或历史授权重新激活。

## 最终验证

更新后的结果为：

~~~text
DOCUMENT_CONSISTENCY_VALID
AUTHORITY_STATUS_FIELDS_ALIGNED
ONE_LIVE_PLAN_ONLY
NO_BROKEN_FIRST_PARTY_MARKDOWN_LINKS
NO_UTF8_REPLACEMENT_CHARACTERS
ALL_218_SCANNED_JSON_DOCUMENTS_PARSE
NO_UNPORTABLE_CITATION_MARKER_LEAK_IN_CURRENT_SURFACES
~~~

全库三处标记字面命中均为有意说明：规范中的 `filecite/cite` 禁止示例两处，以及 2026-08-27 整合记录对 `chatgpt-content-reference` 不可下载事实的记录一处。它们不是正文引用泄漏，保持原样。

本轮没有求解、PINN 训练、GPU/云端运行、sealed reference 开封、来源检索、稿件结果填充或科学 verdict 变化。无关用户工作树改动未被编辑或纳入本轮更新。
