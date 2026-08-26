# 外部 Skill 登记

更新时间：2026-08-19

本文件登记进入项目自动发现目录的外部 Skill。它记录来源、许可、适配、启用边界和已知限制；其内容属于治理与工程状态，不构成学术研究证据。

## 当前登记完整性

- `registry_state`: `UNRECONCILED`
- `skills-lock.json` 当前另行管理来自 `mattpocock/skills` 的 25 个 Skill；`.agents/skills/` 中共发现 30 个 Skill 目录。
- 这 25 个 lockfile 管理的 Skill 尚未逐项纳入本登记。lockfile 中的来源路径和计算哈希只能作为当前安装清单线索，不能替代固定上游提交、许可、本地适配、依赖与运行期外联审查。
- 在单独完成对账前，不对这 25 个 Skill 补造来源或许可结论，也不把其存在视为研究授权或科学证据。
- 本次文档整理没有安装、删除、更新或执行任何 Skill，也没有修改 `.agents/` 或 `skills-lock.json`。

以下各节中的“本次”若未另行注明，均指相应 Skill 的原安装或适配任务，而不是 2026-08-18 之后的研究工作流或本次文档整理。

## Microsoft ResearchStudio

- `installation_state`: `PROJECT_LOCAL_ADAPTED`
- `activation_state`: `EXPLICIT_ONLY_AND_PHASE_GATED`
- `runtime_state`: `DEPENDENCIES_DEFERRED`
- `scientific_claim_status`: `NO_SCIENTIFIC_CLAIMS`
- 上游仓库：`https://github.com/microsoft/ResearchStudio.git`
- 固定提交：`6f1a1cc4c44c67bbc78f0717c8855823d3ad248a`
- 上游许可：MIT，`Copyright (c) 2026 Happy`
- 本地许可副本：`.agents/skills/ResearchStudio-LICENSE.txt`

### 已安装单元

| 本地路径 | 上游路径 | 用途 | 当前边界 |
| --- | --- | --- | --- |
| `.agents/skills/idea_spark/` | `ResearchStudio-Idea/skills/idea_spark/` | 候选 idea 生成工作流 | 只能作为候选生成器；输出默认是 `PROPOSED_NOT_AUTHORIZED` |
| `.agents/skills/paper_search/` | `ResearchStudio-Idea/skills/paper_search/` | 多来源文献检索 | 模型回忆只能作为 `UNVERIFIED_LEAD`；原始来源核验优先 |
| `.agents/skills/scoop_check/` | `ResearchStudio-Idea/skills/scoop_check/` | 特定 novelty claim 的碰撞检查 | 结论只覆盖声明的数据库、查询、时间窗和全文覆盖范围 |

未安装 `evaluation/idea_quality`：它不是上游生产安装单元，数值评分也不能替代本项目的实质判断。

### 本地适配 A′

本地目录是从上述固定提交形成的透明适配版本 A′；上游原件 A 可由仓库和提交号重建。本次适配没有改变研究结论，因为尚未执行研究。

- 为三个 Skill 增加项目权威链、阶段门、来源核验、唯一运行目录和 Windows 使用边界。
- 为三个 Skill 增加 `agents/openai.yaml`，设置 `allow_implicit_invocation: false`；只能显式调用，且显式调用仍不能越过 `active_phase.md`。
- 将 `.env` 自动发现改为双重安全边界：默认不读取；只有 `RESEARCHSTUDIO_LOAD_DOTENV=1` 时才读取，并且只接受 OpenReview、OpenAlex 和 Semantic Scholar 的连接器白名单键。
- 外部 shell LLM 命令默认禁用；只有进程环境显式设置 `RESEARCHSTUDIO_ALLOW_EXTERNAL_LLM_CMD=1` 才允许读取 `NOVELTY_LLM_CLASSIFY_FAST_CMD`。
- 补齐 `paper-search` 文档已要求但上游脚本缺失的 `--json <path>` 接口；JSON 保留未过滤记录、摘要、查询与来源命中信息。
- 禁止在原生 Windows 上直接执行 `scoop_check/scripts/fetch_paper.sh`；启用前需要安全的 Windows PDF 路径或经批准的 PDF 工具链。

### 未采用的上游安装行为

没有运行上游 `install.sh` 或 npm 安装器，也没有复制其 agent 设置。原因包括：它会删除同名目录、写入 `approval_policy=never` 和 `sandbox_mode=danger-full-access`、继承全部环境、可能明文写凭据，并尝试安装或升级全局/系统依赖；这些行为与本项目安全和最小修改原则冲突。

本次没有创建 `.env`，没有写入凭据，没有安装全局或系统依赖，没有调用论文数据库，也没有生成 idea、novelty verdict 或其他研究产物。

### Reel 延期决定

`paper2assets`、`paper2poster`、`paper2blog`、`paper2video` 和 `paper2reel` 标记为 `DEFERRED_UNTIL_MANUSCRIPT_ASSETS`。它们属于论文完成后的传播链，当前不服务于预研究阶段；还涉及 LibreOffice、FFmpeg、Chromium、TTS、外部内容上传和具有递归清理行为的脚本。待论文初稿、图表和结果资产存在后，再按需逐项审计与安装。

### 一次性安装验证

- Python 3.11 对已安装目录中的 45 个 Python 文件完成语法解析。
- `paper-search --help` 已确认本地 `--json` 接口；IdeaSpark 命令入口可加载。
- IdeaSpark 单元测试 `51/51`、路由测试 `37/37` 通过；paper-search 后处理测试 `15/15` 通过。
- paper-search 上游运行时测试通过 15 项、失败 1 项：Windows 本机的 read-timeout 用例没有抛出预期异常。未重复运行；正式启用连接器前必须解决或界定该兼容问题。

以上只证明安装结构和离线辅助逻辑状态，不证明外部连接器、完整 Windows 工作流或任何学术结论有效。

### 正式启用前置条件

1. 用户批准与当时阶段相符的有界研究计划，并由 `active_phase.md` 明确授权相应检索或 idea 工作。
2. 使用项目隔离的 Python 3.11 环境，按实际使用单元安装并固定最小依赖；不得使用 `--user`、`--break-system-packages` 或全局升级。
3. 为每次运行声明唯一输出目录、查询/数据库范围、预算、停止条件和允许的外部连接。
4. 完成 Windows 路径、UTF-8、PDF 获取边界和上述 read-timeout 问题的针对性验证。
5. 凭据只通过明确授权的进程环境变量提供，不提交到仓库。

## HERO-Anti-OverDefense

- `installation_state`: `PROJECT_POLICY_ADAPTED`
- `activation_state`: `ALWAYS_LOADED_VIA_AGENTS_MD`
- `runtime_state`: `NOT_APPLICABLE_PLAIN_TEXT`
- `scientific_claim_status`: `NO_SCIENTIFIC_CLAIMS`
- 上游仓库：`https://github.com/wanshuiyin/HERO-Anti-OverDefense.git`
- 固定提交：`be64527c3cea55ccb7700ee9afaff094cceb40de`
- 上游许可：MIT，`Copyright (c) 2026 Ruofeng Yang`
- 本地许可副本：`docs/governance/licenses/HERO-Anti-OverDefense-MIT.txt`

### 安装形态

上游不是 OpenAI Agent Skill 目录：没有 `SKILL.md`、脚本、运行时依赖或注册入口。其官方 Codex 安装形态是把规范块写入仓库根 `AGENTS.md`。因此本项目没有创建一个需要显式唤起的伪 Skill，也没有把仓库整体复制到 `.agents/skills/`；HERO 以 `AGENTS.md` 中始终加载的项目适配 A′ 生效。

### 采用的最小适配 A′

- 新增检查前必须指出仍然存活的不确定性、具体可检失败及会改变的下一步；没有实质答案时停止添加检查。
- 局部工程失败采用局部修复；仅在科学语义变化或已消费正式结果需保持可复现时建立持久版本。
- 一个局部问题不自动推翻未受影响的研究方向；只有预声明停止条件被证据触发时才收口路线。
- 正确时明确说正确，不制造 finding；同时明确保留来源核验、防泄漏、数值有效性、必要复验和真实安全边界。

现有项目规范已经覆盖上游关于无效哈希、不可达边界、机械评分、重复审计、无关脚手架和高优先级安全/验证要求的主体内容，因此未重复粘贴完整规范块。

### 明确未安装的内容

- 未复制 `cases/` 案例库、`examples/` 量化研究示例、`hosts/` 多宿主说明或图片资产；这些不是运行所需能力，且上游明确反对把案例库放入每轮上下文。
- 未运行 README 中未固定版本的 `curl | awk >> AGENTS.md` Bash 命令；本次基于固定提交做了语义合并，避免重复追加和覆盖项目权威关系。
- 未创建 Hook、定时重注入、额外审阅 Agent、评分器、脚本、依赖、凭据或外部服务连接。

HERO 是可被更高优先级指令覆盖的自然语言约束，不是强制执行器。它只减少与论文目标无关的工程和审计消耗，不得被用来跳过会改变科学结论的检查或隐藏真实问题。

## KKKKhazix khazix-skills

- `installation_state`: `PROJECT_LOCAL_ADAPTED`
- `activation_state`: `EXPLICIT_ONLY_AND_PHASE_GATED`
- `runtime_state`: `NO_ADDITIONAL_DEPENDENCIES_INSTALLED`
- `scientific_claim_status`: `NO_SCIENTIFIC_CLAIMS`
- 上游仓库：`https://github.com/KKKKhazix/khazix-skills.git`
- 固定提交：`7a5c4934be4106ac740ffdb95280bb81b3f4b83c`
- 上游许可：MIT，`Copyright (c) 2026 数字生命卡兹克`
- 本地许可副本：`docs/governance/licenses/KKKKhazix-khazix-skills-MIT.txt`

### 已安装单元

| 本地路径 | 上游路径 | 用途 | 当前边界 |
| --- | --- | --- | --- |
| `.agents/skills/neat-freak/` | `neat-freak/` | 对齐受影响的项目文档、规则、获准记忆和工程状态 | 仅显式收尾；不得改变项目硬约束、扩大研究授权或把工程状态表述为科学证据 |
| `.agents/skills/leader/` | `leader/` | 把用户明确目标整理成有界、可验收的任务书 | 任务书从属于项目权威链；不得自行启动 goal、正式科研、长运行或外部写入 |

### 本地适配 A′

- 两个 Skill 均增加项目权威链、`active_phase.md` 阶段门和 `docs/governance/EXTERNAL_SKILLS.md` 前置读取要求，并通过 `agents/openai.yaml` 禁止隐式调用。
- `neat-freak` 改为只检查本次真实改动影响的事实面；禁止用全仓机械枚举、行数/字节/文件数、重复哈希或重复同类审计代替判断。Codex 生成记忆保持只读，只有用户明确要求时才使用宿主规定的 correction input。
- `leader` 生成的任务书是下游执行合同而非“唯一真理”；它不能覆盖系统、用户、项目硬约束或阶段授权。固定字符数、行数、轮数和文件模板只在真实工具限制或用户批准的任务合同时生效。
- 科学任务书必须继承论文去向、预期证据、强基线、关键消融、实体级拆分/formal OOD、预算和停止条件；涉及科学核心、物理拓扑、PDE/动力学、参数唯一性、正式预算或硬约束的决策仍交由用户。

### 明确未安装或未执行的内容

- 未安装仓库中的 `aihot`、`hv-analysis`、`khazix-writer`、`storage-analyzer` 或其他无关 Skill。
- 未保留 `neat-freak/evals/` 的评测夹具；它们不是运行能力，且含模拟工作区、模拟记忆与示例 `.env` 文件。
- 未保留 `neat-freak/scripts/audit-inventory.sh`；它依赖 Bash、面向全量盘点，并统计行数/字节/文件数，不符合本项目 Windows 默认环境与最小验证边界。需要盘点时使用受影响范围内的原生 Windows 只读检查。
- 未安装 Python、Node、系统或全局依赖，未写入凭据，未访问外部研究数据库，未创建 Codex goal，未修改记忆，未运行文献检索、idea 筛选、建模、训练或实验。

以上安装只证明项目级 Skill 文件、来源、许可和适配状态，不构成任何学术研究成果或科学结论。正式使用时仍以当次用户指令和 `active_phase.md` 为准。

## Matt Pocock engineering skills：本轮最小对账

- `reconciliation_scope`: `RESEARCH_AND_DOMAIN_MODELING_ONLY`
- `installation_state`: `PROJECT_LOCAL_LOCKFILE_MANAGED`
- `activation_state`: `TASK_TRIGGERED_AND_PHASE_GATED`
- `runtime_state`: `PROMPT_ONLY_NO_DEPENDENCIES`
- `scientific_claim_status`: `NO_SCIENTIFIC_CLAIMS`
- 上游仓库：`https://github.com/mattpocock/skills.git`
- 本轮固定核对提交：`6654f6b60cd9d5be8b54c6fafe44346dabeb3b76`
- 上游许可：MIT，`Copyright (c) 2026 Matt Pocock`
- 本地许可副本：`docs/governance/licenses/mattpocock-skills-MIT.txt`

本轮仅对 `.agents/skills/research/` 与 `.agents/skills/domain-modeling/` 做最小对账。`skills-lock.json` 将二者分别路由到上游 `skills/engineering/research/SKILL.md` 与 `skills/engineering/domain-modeling/SKILL.md`，并保存本地安装计算哈希。固定提交中的对应原文与本地语义一致；本地 `domain-modeling` 另保留 `CONTEXT-FORMAT.md` 与 `ADR-FORMAT.md` 作为格式附件。

- `research` 只要求把一手来源阅读委派给后台 agent，并形成单一带来源 Markdown 报告；它不提供数据库 verdict、物理判断或执行授权。
- `domain-modeling` 只用于更新项目术语和记录满足 ADR 门槛的路线决定；它不覆盖项目文档角色或权威顺序。
- 本轮不运行上游安装器、npm、脚本或外部 LLM 命令，不安装依赖、不读取凭据，也不把 Skill 输出直接升格为科学证据；所有来源结论仍由主 agent 对原始载体独立核验。

其余 lockfile 管理 Skill 仍保持 `UNRECONCILED`，本节不对其来源、许可或运行边界作补造结论。
