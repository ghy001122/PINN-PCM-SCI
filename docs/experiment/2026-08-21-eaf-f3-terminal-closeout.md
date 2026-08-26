# EAF-KC-v1 F3 终局收口，2026-08-21

## Disposition

- `route_disposition`: `FINAL_FRONT_BENCHMARK_NO_GO`
- `lifecycle_state`: `BLOCKED`
- `claim_status`: `PROPOSED_METHOD_NO_NUMERICAL_EVIDENCE`
- `F0`: `SOURCE_AUDIT_PASS_WITH_EXPLICIT_A_PRIME`
- `F1`: `FRONT_FEASIBILITY_PASS`
- `F2`: `EAF_F2_SMOKE_PASS`
- `F3`: `FINAL_FRONT_BENCHMARK_NO_GO`
- `F4_F6`: `NOT_STARTED`
- `next_route`: `NO_AUTOMATIC_RETRY_OR_NEW_SUBSTRATE`

## 已核验事实

1. F0 一手来源冻结了 600 nm VO₂ 深度、1 MHz/1.2 V/5 ns rise/90 ns pulse、`36±10 ns` 形成、`107±21 ns` 恢复、2.2 ns 分辨率、`4.54 nm/ns` 前沿及约 400 nm 后不再转变。横向电极间距、接触热/电阻与去嵌入端口电压保持 `UNKNOWN`；因此 `EAF-KC-v1` 是显式 `A_PRIME` benchmark，不是实验器件复现。
2. F1 run `20260821T134653Z-smoke-eaf-f1-feasibility-001` 得到 `Fo=0.5009015`、热扩散长度比例 `0.7077439509`、预测前沿覆盖比例 `0.681`、界面空间分辨 8 格和实验时间分辨下 4.0048 帧，裁决 `FRONT_FEASIBILITY_PASS`。
3. F2 run `20260821T140332Z-smoke-eaf-f2-pipeline-001` 通过控制流；随后发现 F3 所需局部成核种子在实现中只表现为 `Tc` 偏移，而 `tilt=0.30 < 2/(3√3)` 不能消除冷相势垒。该合同实现缺口以解析最小 hot-seed bias 修正，superseding F2 run `20260821T141141Z-smoke-eaf-f2-nucleation-correction-002` 再次通过：制造残差 `0.0013618201`、最大离散违规 `1.1368683772e-15`、raw/identity/KC 各一次更新及磁盘 evaluator 均完成。
4. 原 F3 run `20260821T140900Z-pilot-eaf-f3-front-001` 因上述种子缺口不具备 intended-contract 科学解释权，原 manifest 保留。superseding F3 run `20260821T141230Z-pilot-eaf-f3-front-nucleation-correction-002` 在修正合同下执行同一冻结 bracket；`0.6 V` 与 `2.4 V` 的形成时刻均未达到全局相区动态范围 0.20 的校准门，因此没有打开参考 case，裁决仍为 `FINAL_FRONT_BENCHMARK_NO_GO`。
5. 第二次 F3 已经消费唯一实现修正机会。继续扩大 drive、改变电极/接触几何、调 mobility/interface/seed、降低相区门、扩大网络或切换 substrate 都会成为结果导向救援，违反预声明合同。

## 解释边界

- `VERIFIED`：F0/F1/F2 工程与尺度链有效；修正后的固定 F3 bracket 内没有足够结构事件信号。
- `SUPPORTED_INTERPRETATION`：来源尺度本身允许部分前沿，但冻结 `A_PRIME` 横向/接触几何与确定性相场闭合不能把该尺度转换为满足主端点的 benchmark。
- `NOT_EVALUATED`：oracle 离散资格化、强 raw 能力、KC 增量、formal、实验验证、SOTA 和真实器件有效性。
- 本结果不否定结构动力学时钟 idea；它说明当前所有获批 synthetic substrate 都未建立可供该 idea 公平投票的合格移动前沿 oracle。

## 证据入口

- [F0 来源审计](../references/eaf_kc_front_source_audit_2026-08-21.md)
- [实验索引](INDEX.md)
- `outputs/runs/20260821T134653Z-smoke-eaf-f1-feasibility-001/`
- `outputs/runs/20260821T141141Z-smoke-eaf-f2-nucleation-correction-002/`
- `outputs/runs/20260821T141230Z-pilot-eaf-f3-front-nucleation-correction-002/`

