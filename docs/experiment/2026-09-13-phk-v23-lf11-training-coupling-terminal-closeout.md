# LF11 V30：训练期电学耦合与事后重求解终局

批次标识：2026-09-13；本地完成日期：2026-09-14（Asia/Shanghai）。

- `phase_id`: `PHK_V23_LF11_TRAINING_COUPLING_VS_POSTHOC_REPAIR_COMPLETE`
- `lifecycle_state`: `COMPLETE`
- `blocker_id`: `NONE`
- `claim_status`: `VALID_TRAINING_COUPLING_INCREMENT_OVER_POSTHOC_CONTROLS`
- `next_research_execution_authorized`: `false`

执行依据：[用户完整指令](../notes/2026-09-13-lf11-training-coupling-authorized-sprint.md)，设计解释：[独立复评](../notes/2026-09-13-lf11-v29-independent-review-training-coupling-plan.md)。继承提交59e3a5a5对应V29，本轮新科学代码及结果尚未自动发布。

VERIFIED：本轮用户授权的新协议已按终局收口；已核对当前实际实例回收与关机，之后本地读取 nominal 参考。训练/自身预测不读完整参考或 stress。旧 P_F 条件未触发的历史记录不改写。

## 实质结果与解释

VERIFIED：本轮获得**器件功能层B的训练方法包增量**。两种有效完整F/projected均使用与E相同的事后电学求解；E相对F_raw/projected的底部电流/功率误差降低35.2244%/35.9950%，相对F_bal/projected降低56.8459%/58.6963%，两组均满足原五项非劣条件。共同层B通过，层A未通过，不拼接不同层或比较者。

| 方法 | 底部电流NRMSE | 功率轨迹NRMSE | S | raw Ephi |
|---|---:|---:|---:|---:|
| E＝V28 P_E | 0.69382% | 0.68173% | 0.0008190625 | 0.0159996773 |
| F_raw/projected | 1.07111% | 1.06512% | 0.0008582031 | 0.0166913896 |
| F_bal/projected | 1.60777% | 1.65053% | 0.0008628906 | 0.0171664543 |

VERIFIED：事后修复本身作用很大。F_raw底流279.3000%→1.0711%、功率20.1181%→1.0651%；F_bal底流332.0882%→1.6078%、功率16.8942%→1.6505%。配对T/phase、S/Ephi/ET和全部事件逐项相同；它们是每个已训练模型的两种读出。E的局部q误差还分别低30.8108%/41.2717%。

SUPPORTED_INTERPRETATION：在本次比较中，E的收益不能全部解释为最后重求电学。双方相同电学读出后仍有功能差距，支持训练方法包对所学状态的作用。它仍包含初始V映射、可训练参数、V观测梯度与全网格硬约束/抽样软约束覆盖差异，不能只归因于VJP，也没有直接证明全局导电率场误差更低。

VERIFIED：相态层A未达10%增量，严格双周期未全过。E第一周期recall=0.882492，第二周期timing=0.00752857；两个F的第二周期timing=0.00252857/0.00489091反而更好，因此不能写成事件全面改善。UNKNOWN：热/phase残差独立必要性、新初始化/干净观测/完整案例稳健性、材料标定与加速。

当前可入稿的方法主体为“训练期电学约束＋一致焦耳接口”，以“原读出→固定状态电学修复→共同读出后的训练差异”组织证据。通用求解、隐式微分、优化器及一次标量校准各自不算原创。V28同层B_E收益与V29剩余PDE未获增量的结论完整保留。

下一步优先做一个全网格软电学反事实，再以两个从头初始化确认最近强控制并保留D_E；随后检验干净观测位置和一个完整新协议。它们均为待批新科学任务。条件数值敏感性未触发，不是运行失败。


## 实际执行与输入边界

实际新增 3000 Adam、600 完整固定目标评估、290 个接受步；一次五块梯度校准；训练电学正/伴随解 0/0；事后投影实际正解 557（有效保存556，修复前丢弃1，补充授权增加1次）；条件敏感性正解 0。

E为已完成的V28 P_E，父态按角色选定原E0。两种F共享同一父态、采样和原aE/bE，只改变预先校准的电学残差标量；eta_bal=0.0254939372458。新F均开放原V/T/phase及T适配器，完整显式梯度；E的初始V由求解给出，F由原V头给出，因此比较为训练方法包，不能单独归因于VJP。

每个F/network与F/projected严格保留同一T/phase；后者只求自身电学，不增加标签、训练或热/phase轨迹。两个读出不算独立模型。D_E/B_E保留在主表，V29三个端点只作不同训练历史背景。正式判据没有移动；无效、未完成或跨层拼接不能构成消元获胜。

原始派发连接在后台启动后超时，随后核实实际进程在运行，科学重执行为零。两组训练已完整完成，随后配对推理因字典别名错误地比较两种电势而报错，T/phase并未变化。回收后立即关闭当前实际实例；最小接口修复经隔离检查后，本地CPU逐点保存并补齐自身读出，再读取参考。原云任务退出1及其未完成标记保留，另存本地完成记录；已消耗但未保存的1次正解计入实际预算及补充授权。未复用旧关机凭据，也未重启GPU或训练。

## 论文与下一步

完整稿：[paper_v30](../../paper/paper_v30/manuscript.md)；主张矩阵、图表、最小复现与选定证据在其目录。终局机器记录：[manifest](manifests/20260913-lf11-training-coupling-terminal.json)。原始完整场在 outputs/runs/20260913-lf11-training-coupling；精简包不包含完整参考或stress。

条件数值检查：NOT_TRIGGERED_MAIN_METHOD_SIGNAL_ESTABLISHED。The frozen B layer passes against both valid complete projected controls. The predeclared numerical-sensitivity branch requires no main increment plus a next decision depending on the thermal interface; that prerequisite is false. Preserve the present interface and plan independent/strong-control confirmation instead.

后续优先方案见[唯一待批计划](../plans/NEXT_ACTIONS.md)。当前没有新初始化、新完整案例、材料标定或热/phase残差独立必要性确认。旧成功与负面结果按原边界保留，不把求解器、VJP、L-BFGS和标量校准各算原创。同类最小工程恢复按完整规范第56a条的用户持续授权处理，无需重复请示。没有自动commit/push/PR。
