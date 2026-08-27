# ADR 0045：采纳 PHK-V2 强基线复现与双模块正向研究执行

- `status`: `ACCEPTED`
- `date`: `2026-08-27`
- `decision_scope`: `PHK_V2_S0_TO_S7_LOCAL_RESEARCH_EXECUTION`
- `supersedes`: `GOAL_PAPER_ONE_SHOT_V1_COMPLETE_AUTHORIZATION_SEMANTICS_ONLY`
- `preserves`: `ALL_PRIOR_NO_GO_FAILED_INTENTS_AND_V1_MANUSCRIPT`

## 背景

用户在完成第一版 failure-preserving reference-solver qualification 论文后，提供《后续研究总规划》并明确要求继续执行：全面剖析与复现相关 PINN 工作，提取可迁移创新，识别局限和改进空间，在相变器件领域从可行性开始分层验证，经公平且灵活的 baseline 改进形成 PHA-MF 与 field-selective KC 的可归因组合，最终完成第二版论文初稿。

R0 一手来源审查发现原规划需做四项承重修订：Sharp 正式论文身份与仓库 causal/RAR 长预算 recipe 必须分开；Sharp 只能是主 phase-field anchor 而非唯一 evidence baseline；GPL/Penn 代码不能直接并入拟公开主库；adaptive pseudo-time 必须成为反证 KC 是否只是通用优化技巧的 mandatory control。Miquel 等 GGST 工作因未公开物性、保密成分和无代码，只能启发透明 reduced object，不能成为开放 oracle。

## 决定

1. 接受 `PLAN-PHK-V2-V1` 作为唯一 live plan，并在其预算和前置门内授权 S0–S7 连续本地执行。
2. Sharp-PINNs 固定为 phase-field domain anchor，但把 paper replication 与 pinned repository recipe 分成两个实验身份；另以 jaxpi2/adaptive pseudo-time 和 paper-spec PirateNet 形成 general strong controls。
3. 主项目只做 clean-room 实现；GPL 与 Penn 限制源码只允许隔离 comparator，不直接复制分发。
4. 新对象为 `PHK_REDUCED_WALL_CELL_2D_V1`：透明二维电—热—相态 reduced benchmark，不声称 GGST 作者模型复现、实验校准或真实器件验证。
5. 只保留 PHA-MF 与 field-selective KC 两个 load-bearing 模块；sampling、causal、loss balancing、staggered schedule 和 continuation 是公共协议或控制。
6. PHA 与 KC 必须先独立通过；任一 standalone 失败不得由 full 组合掩盖。formal 只在 oracle、event、strong raw 和两模块归因门全部通过后开放。
7. complete case 是科学单位；formal 使用独立 sealed pools、paired case-level inference、预冻结 superiority/noninferiority margins、全失败计票和无 peeking/reseal。
8. 总预算固定为 CPU 128 core-hours、development GPU 64 exclusive hours、formal GPU 64 exclusive hours；GPU 仅限本地实际可用设备。付费/云端计算、外部上传、投稿和 Git 远程操作均不授权。

## 理由

该设计把“相关相场底座”“通用强训练系统”和“PCM 定向增量”分开，能防止用弱 Vanilla 或额外采样/参数/计算制造虚假涨点。它也让 adaptive pseudo-time、generic monotone clock、global MF、wrong gate、wider raw 与 extra-work raw 能直接杀死不成立的机制叙事。旧 No-Go 与第一版论文保持原证据身份，新路线失败时仍可形成有边界的 benchmark/limits 稿而不污染历史。

## 后果

- 当前只因 R0 完成而获得来源身份；没有官方复现、合格 PHK oracle/event、strong raw、PHA、KC、组合、GPU 或 formal 证据。
- 第一次 PHK 对象求解前必须冻结 machine-readable object/numerical contract；第一次方法训练前必须冻结 case manifest、evaluator 和 oracle floors。
- 本机无 CUDA 设备时只推进 CPU 可行阶段；不得自动转付费或云端。
- 只有 `F_A` superiority、`F_O` noninferiority、硬守卫与归因控制全部通过，才允许第二版写正面 PHK 方法主张。

