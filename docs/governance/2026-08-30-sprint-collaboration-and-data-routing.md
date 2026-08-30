# 2026-08-30 冲刺协作与数据路由

- `document_role`: `SPRINT_COLLABORATION_AND_DATA_ROUTING`
- `authority_effect`: `NONE`
- `scientific_evidence`: `false`
- `applies_to`: `PHK_V22R_V11_SPRINT`

本文件规定 Codex、ChatGPT、AutoDL、VSCode、PowerShell 与 GitHub 如何协同，以及不同文件
应存放在哪里。它不改变 `active_phase.md`、冻结合同、预算、证据门或科学主张。

## 单一职责

| 位置或工具 | 主要职责 | 不能替代什么 |
|---|---|---|
| 本地 Windows 仓库 `E:\Python demo\PINN-PCM-SCI` | 权威工作树、合同、代码、本地 reference、sealed evidence、下载后的完整 run 与本地评价 | 不能把未提交文件冒充 GitHub 快照 |
| AutoDL `/root/autodl-tmp/PINN-PCM-SCI` | 按精确 commit/白名单执行 reference-blind GPU 训练，临时保存可回收训练产物 | 不是长期档案；不得持有 nominal/stress reference 或本地评价 |
| GitHub | 保存经过验证、精确选择的代码、合同、测试、文档和小型可复现摘要 | 不是原始数据盘、密封证据库、密码库或实时运行监控器 |
| Codex | 在当前授权内审查、编辑、测试、选择性 Git 操作；连接可用时可部署、运行、监控、回收与关机 | 不能改变硬科学合同、替用户付费/授权第三方或提交论文 |
| ChatGPT | 读取已推送的 GitHub 快照，做解释、审查、方案建议和论文讨论 | 看不到未推送本地状态或 AutoDL 实时状态；不作为证据源 |
| VSCode Remote SSH | 人工查看/编辑远端文件和使用远端终端的主界面 | 终端断开不应决定训练寿命，界面也不是数据备份 |
| 本地 PowerShell + SSH | 独立备用登录、恢复 tmux、查看 GPU/日志和传输文件 | 登录前无需切到本地 E 盘；SSH 后再进入远端项目目录 |

GitHub 按“可能外部可见”处理：即使仓库设置为 private，也不提交密钥、令牌、账号、
sealed fields、未脱敏路径或不必要的原始结果。

## 完整闭环

1. **本地冻结与验证**：Codex/人工在本地权威工作树确认 `active_phase.md`、合同、run card、
   测试和预算；reference 与 sealed 数据始终留在本地。
2. **精确 Git 快照**：只显式暂存本轮文件，检查 staged diff、敏感信息和大文件，再
   commit/push。禁止用 `git add .` 或 `git add -A` 把脏工作树整体带入提交。
3. **部署精确身份**：把同一 Git commit 或经清单核验的白名单复制到 AutoDL，记录 commit、
   合同哈希、环境、run ID 和预计费用；云端不上传任何 reference。
4. **启动前实时复查**：查看 `tmux ls`、训练进程、`nvidia-smi`、磁盘和预算。已有
   `phk_train` 就接入，不存在才创建；一次只运行一个付费 nominal 任务。
5. **守护与监视**：训练在 tmux 内执行。VSCode 或 PowerShell 任一 SSH 客户端断开后，
   训练仍由远端 tmux 承载；另一客户端可重新登录并 attach。tmux 不能抵抗实例关机、回收
   或崩溃，因此日志、manifest 与 checkpoint 必须持续写盘。
6. **回收并停机**：下载完整 checkpoint、prediction、log、manifest、environment report 和
   cost ledger 到本地对应 run 目录；核验数量/哈希后执行关机，并由人工在 AutoDL 控制台确认
   实例状态和是否停止计费。
7. **本地评价**：只在本地把 prediction 与 nominal development reference 比较。若冻结门
   允许进入 confirmation，云端仍只生成 reference-blind carriers；六份 carrier 身份完整后才
   可按合同在本地一次性开封 stress references。
8. **证据收口**：原始产物留在本地；把紧凑 manifest、哈希、成本、指标表、图表、真实
   PASS/No-Go 与论文文字写入受控文件，重新验证后选择性 commit/push。
9. **ChatGPT 复审**：只在推送完成后，让 ChatGPT 按明确 commit/文档入口读取最新状态并
   提建议；建议回到本地后仍须经过项目权威链、证据门和必要测试。

## 文件位置与生命周期

| 文件类型 | 权威位置 | AutoDL | GitHub |
|---|---|---|---|
| 源码、配置、测试、run card | 本地仓库 | 精确 commit/白名单副本 | 提交 |
| `.env`、SSH 私钥、token、账号信息 | 用户安全存储；不进入仓库 | 仅用平台 secret/既有登录机制 | 永不提交 |
| Python 环境与缓存 | 本地 `.venv/`；云端 `/root/autodl-tmp/envs/` | 运行环境 | 不提交；只提交锁定说明/版本清单 |
| nominal/stress reference 与 sealed fields | 本地 `outputs/sealed/` 或受控 reference 路径 | 禁止上传 | 永不提交原始场；只提交允许披露的哈希和角色说明 |
| 云端 checkpoint、prediction、log、manifest、cost ledger | 回收到本地 `outputs/runs/<RUN_ID>/` | 训练期间临时存在 | 默认不提交原始大包 |
| 本地 evaluator 输出与完整指标 | 本地 run/evaluation 目录 | 禁止上传 | 只提交紧凑、可追溯且允许披露的摘要 |
| 实验事实记录 | `docs/experiment/` | 无 | 提交小型记录、run ID、哈希、环境、成本与边界 |
| 稿件、表格、图源、复现说明 | `paper/paper_v22r/` | 不作为训练输入 | 在证据允许范围内提交 |
| 临时研究/工具目录 | `.tmp/`、`.j2/`、`ideaspark_run/` | 可再生时删除/重建 | `.gitignore` 排除 |

VSCode 和 PowerShell 是操作入口，不是新的文件权威位置。若从两者同时登录，同一个远端路径
和 tmux 会话可共享；不要各自启动一份训练。

## 人工与 agent 边界

**一定由人工完成或最终确认：**

- AutoDL 账号充值、租卡、价格/规格选择、控制台付费状态确认；
- GitHub/OAuth/SSH 公钥、私钥、令牌和其他第三方凭据的录入与授权；
- 改变科学硬合同、物理对象、sealed 规则、预算上限或研究主张范围；
- 作者联系、数据披露、期刊选择、投稿与对外发布；
- 永久删除、覆盖不可恢复数据或其他需要新权限的破坏性动作。

**agent 可在已有授权和连接条件下代为完成：**

- 本地代码/配置/文档修改、测试、哈希、manifest、图表和论文草稿；
- 精确白名单暂存、diff/敏感信息检查、commit/push；
- SSH 部署、环境复核、tmux 启动/接入、GPU/日志/费用监视、产物回收与自动关机；
- 按冻结 decision machine 做本地评价、PASS/No-Go 收口和状态文档更新。

agent 代操作不扩大授权。控制台最终计费状态、凭据操作和任何合同变更仍需人工负责。

## 省钱与故障规则

- 先在本地跑门禁，云端只做 GPU 有价值的冻结任务；不在付费实例上探索性改代码。
- 启动前估算剩余费用，运行中记录 wall time/cost ledger；接近 150 元硬上限即停止新任务。
- 每轮只保留一个训练进程；VSCode 断线后用 PowerShell/SSH attach tmux，不重复启动。
- 允许的产物完整回收并核验后立即关机；再由人工在控制台确认停止计费。
- 运行失败保留真实日志和 manifest，按预声明停止条件收口；不换 seed、加 updates 或救援式重跑。
