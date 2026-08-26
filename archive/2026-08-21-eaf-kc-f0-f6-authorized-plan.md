# Live plan：EAF-KC-v1 48小时内核心方法裁决

- `phase_id`: `EAF_KC_F0_F6_EXECUTION`
- `lifecycle_state`: `ACTIVE`
- `blocker_id`: `NONE`
- `authorization_state`: `USER_APPROVED_F0_F6_LOCAL_CPU`
- `execution_authorized`: `true`
- `claim_status`: `PROPOSED_METHOD_NO_NUMERICAL_EVIDENCE`

## 论文去向与公共 seam

- 论文只检验：结构场选择性动力学时钟能否相对强 raw、一般单调和动力学错位对照改善重复二维结构前沿。
- TDD 只覆盖已确认的 `FrontSourceMap`、`FrontFeasibilityReport`、二维前沿 case/artifact、`EventCompetenceReport` 与独立磁盘 evaluator。
- 完整 case 是开发与后续 formal 的不可拆单位；主训练不读取实验或 oracle 瞬态内部场标签。

## 固定执行顺序

1. `F0`：冻结一手来源、许可、几何、电极/衬底、脉冲和观测尺度；不唯一即 `FRONT_SOURCE_BLOCKED`。
2. `F1`：求解器前完成 Fourier 数、热扩散长度、前沿传播比例、界面网格和局部阈值选择性；无窗口即 `FRONT_FEASIBILITY_NO_GO`。
3. `F2`：测试先行实现最短电—热—结构前沿链，制造解只作 smoke；一次 raw/identity/KC 更新和磁盘评分必须通过。
4. `F3`：一个参考 case、一个 drive 标量、最多八次确定性二分；必须产生持续、连通、部分覆盖且可恢复的前沿，否则 `FINAL_FRONT_BENCHMARK_NO_GO`。
5. `F4`：最多七个空间/时间/容差/重放 run，按公共物理探针裁决前沿、连续相态、器件、温度和守恒；失败即 `EAF_ORACLE_INVALID`。
6. `F5`：固定 `4×64 tanh`、float64、Adam `1e-4`、seed 17、1500 updates、2 case×2 seed；强 raw 不解析事件即一次稀疏 η 诊断后 `RAW_EVENT_NOT_RESOLVED`。
7. `F6`：raw、activity-matched、identity、general-monotone、misaligned、KC 和 strongest-native 共享初始化、collocation、实际计算量、checkpoint 与 evaluator；必要比较失败即 `KC_SCIENTIFIC_NO_GO`。

## 时间与止损

- 4 小时内得到来源/尺度合同或明确 No-Go；24 小时内得到可信前沿或终止；48 小时内完成强 raw 裁决。
- 任一门失败立即落 manifest/index 并收口；不重开旧 substrate，不添加网络搜索、PHA、KC 组合、高场、力学或其他论文外工作。

## 未授权

- formal、GPU、外部付费计算、完整 Q‑POP transfer、提交/推送/PR，以及任何正面科学主张。

