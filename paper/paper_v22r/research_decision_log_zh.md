# PHK-V2.2R 冲刺研究决策记录与后续路线

状态：`TERMINAL_NO_GO_CURRENT_ROUTE_CLOSED`
后续路线状态：`PROPOSED_NOT_AUTHORIZED`

## 一、研究问题如何收缩

本轮最初要检验的是：场选择多频表示与 phase–Joule 物理采样能否在固定
电—热—相态二维对象上，以相近训练成本改善局域双脉冲相变事件。为了避免在看到
结果后不断增加模块，最终把问题收缩为四臂：强 raw、仅多频、仅 sampler、两者组合。
只有组合臂允许晋级，且必须先过事件 competence，再谈相对增益。

此前两个候选方向没有进入本轮：strict PHA 在 100-update profile 中虽通过 1.8 倍
成本门，但相对组合臂的 primary 改善为 0，未达到 10%，因此按预注册规则退出；
generic RAR 未在截止时间前形成稳定、可冻结实现，因此启动四臂 fallback。Route B/C、
功能型 pivot、换 seed 和延长训练均被排除。

## 二、为什么先做 P0 v1.1

旧 runner、决策和 freeze 顺序仍混有 pilot、Route B 与 equal-compute 旧逻辑，若直接
运行会导致“执行了什么”与“论文声称什么”不一致。P0 因此只做必要对齐：冻结两份
机器合同、四臂 runner、full-only 决策机、六载体后才能最终 freeze 的顺序、云端
run card 与论文登记表。聚焦测试 16/16、组合回归 47/47、文档一致性门禁均通过后，
才启动 nominal。

## 三、执行结果与判断过程

四臂均在 V100 上完成 1000 次 FP64 Adam 更新，PDE loss 均下降，且没有 NaN、OOM
或越界相场。这说明实现和优化循环确实工作，但不等于科学任务成功。

本地 nominal 评价给出更关键的事实：四臂相场最大值都停留在约 0.03 的初始种子
水平，从未超过 0.5 阈值；参考的两次 ROI 峰值分别达到 0.06870 与 0.06198，而四臂
始终为 0。于是每臂都同时缺失两次事件，并在每周期触发 event missing、ROI peak
不足、recovery failure 三项失败。

四臂 primary 都是 0.00515，并不意味着它们同样优秀。因为预测活动集合始终为空，
对称差就是参考事件本身；事件只占很小的时空体积，所以平均值看起来很小。若不把
event competence 放在 scalar ranking 前面，就会把“完全漏检”错误地判成“高精度”。

决策机因此返回 `MVP_NO_GO_NO_BASIC_COMPETENCE`。没有候选、没有 strongest eligible
comparator，也不允许生成 confirmation 训练。两份 stress reference 继续密封未读。

## 四、当前可写结论

- `VERIFIED`：四臂有限执行且 PDE loss 下降；四臂均未产生两次局域相变事件。
- `SUPPORTED_INTERPRETATION`：在本合同下，训练落入近初始相态吸引子；loss 收敛与
  小的全域平均误差不能作为事件 competence 证书。
- `UNKNOWN`：问题究竟由 phase 残差尺度、梯度流、窗口开启、优化预算、表示或它们
  的耦合造成。本轮没有证据区分这些机制。
- `UNKNOWN`：换 seed、延长、continuation、L-BFGS 或新架构是否可恢复事件；这些都
  是新研究轴，不能作为本轮救援。
- `UNKNOWN`：stress case 表现、formal OOD、统计稳健性、实验与连续体有效性。

## 五、后续研究路线（新合同，尚未授权）

### R0：competence 失效诊断

目标不是再跑完整方法，而是定位“相场为何不离开初始种子”。新 runner 应记录每个
causal window 的 phase 最大值、ROI 活动比例、三类 PDE RMS、各 loss 对参数的梯度
范数、相场 head 更新量与 sampler 候选分布。基线只用原 `STRONG_RAW`，保持 nominal
对象、seed 17 与 reference-blind 训练。先做短 smoke，再做一次有上限的诊断 pilot。

通过条件：能把失败归到一个可复现层，例如 phase 梯度被热/电损失压制、窗口切换后
梯度消失，或 logit 变换在当前尺度下形成近零更新。停止条件：诊断量仍无法区分机制，
或任何方案需要 reference label 才能激活事件。

### R1：单一干预的 raw competence 恢复

只允许根据 R0 选择一个干预轴，例如预冻结的 loss 平衡规则、无标签 phase-activation
curriculum，或优化器/continuation 中的一项；不得同时改变多个因素。对照为原 raw，
消融为“raw + 唯一干预”。仍先在 nominal、seed 17、scratch 下执行。

晋级条件：两次事件、峰值、恢复、局域性、有限值全部通过，且温度/电流不发生灾难性
退化。若 raw competence 仍失败，立即收口，不引入多频或 sampler。

### R2：重新建立归因矩阵

只有 R1 成功后，才在新版本合同下重建 raw、MF-only、sampler-only、full 四臂矩阵。
先以 seed 17 做开发，再以至少 3 个冻结 seed 做确认。比较必须同时报告 fixed-update
与 measured-time，并保留参数量差异。full 仍需相对 strongest competent component 与
raw 同时过门。

### R3：实体级确认与 stress 开封

候选、comparator 和参数匹配/实测时间 raw 的身份先冻结；两个 stress case × 三角色的
六份预测全部生成并核验后，才允许一次性开封。若未来沿用当前两份 sealed reference，
必须先确认其未被任何新开发过程读取。结果只支持 case-specific robustness，不能自动
升级为 formal OOD。

### R4：论文升级条件

只有以下证据齐全，当前负面初稿才可升级为正向 Method-MVP：raw competence、full 的
可归因增益、参数/时间公平对照、至少三 seed、两 stress case、完整 adverse metrics、
可复现代码与 claim audit。否则保留本轮负面结果，并把新研究作为独立版本报告。

### 建议预算、基线与停止表

| 阶段 | 固定基线/消融 | 数据与拆分 | 建议硬上限 | 立即停止条件 |
|---|---|---|---:|---|
| R0 | 原 `STRONG_RAW`，只增加诊断记录，不改训练语义 | nominal development，seed 17 | 1 GPU-hour / 5 元 | 诊断量仍不能区分机制，或需要 reference label 才能激活 |
| R1 | 原 raw vs `raw + 单一干预` | nominal development，seed 17 | 3 GPU-hours / 10 元 | 任一臂非有限，或干预后仍缺任一事件 |
| R2 | raw、MF-only、sampler-only、full；同时报告 fixed-update 与 measured-time | nominal 开发 seed 17；冻结后 seeds 29/43 确认 | 15 GPU-hours / 40 元 | raw competence 不稳定，或 full 不胜 strongest competent component/raw |
| R3 | selected、strongest comparator、参数匹配/实测时间 raw | 两个完整 stress 实体 × 三角色；六载体先冻结 | 15 GPU-hours / 40 元 | 六载体身份不全、任一 hard guard 失败或预算接近上限 |

总建议新预算不超过 95 元；启动前必须按当时实时单价重新投影。该预算不是现有 150 元
授权的自动余额，也不允许把失败阶段的余额转成新的救援轴。

## 六、预算与权限

上述 R0–R4 不是当前授权的延伸。本轮实例已经关闭，累计估算 4.8101 元。任何新 GPU
运行、合同修改或 stress 解封都需要新的明确授权和独立预算；不得覆盖当前 run ID、
decision 或论文中的 No-Go 证据。
