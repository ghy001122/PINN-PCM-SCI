# 项目状态

更新时间：2026-09-12

- `phase_id`: `PHK_V23_LF11_V_CONTINUATION_AND_CONTACT_AUDIT_COMPLETE`
- `lifecycle_state`: `CLOSED`
- `blocker_id`: `NONE`
- `claim_status`: `VALID_V_ONLY_DEVICE_IMPROVEMENT_CONTACT_TRACE_ATTRIBUTION_NO_NEW_PINN`
- `next_research_execution_authorized`: `false`

## 最新VERIFIED

VERIFIED：200次V-only评估接受99步，可见V误差0.8215%→0.5618%，T/phase完全不变。固定参考能量误差49.20%→28.28%；带符号底流积分下降的99.41%来自边界迹项。零训练接触端点强基线能量误差2.187%→0.644%。原0.5%拟合门未达，新D_B/P_U及归一化未运行，不是失败方法。

本轮只有V参数更新；固定目标下降53.23%，停止原因为预算耗尽。温度全局/加热/关断误差仍为1.1375%/1.8357%/0.7219%。phase与双周期事件未改善，S=0.001188671875、raw Ephi=0.027268375553。

V-only正式top/bottom电流NRMSE为6.5030%/522.2628%，功率NRMSE30.7607%，能量误差28.2797%。接触强基线对应0.4278%/21.5140%、1.3776%、0.6443%。严格器件门仍未通过。

## 解释与未知

SUPPORTED_INTERPRETATION：固定函数和网格上的heater边界迹显著影响FV底流及V-only变化；内部耗散反而略升。这里是固定T/phase/σ的读出干预，不是自洽耦合求解或RMS贡献率。

UNKNOWN：拟合门之上PDE是否有增量、归一化机制、独立seed/mask/完整案例稳健性、实验材料有效性。唯一优先建议为先审查heater相容且邻接绝缘导数良好的V表示，再另批共同底座/PDE比较；不得自动追加200或重启旧hard lift。

[本轮终局](docs/experiment/2026-09-12-phk-v23-lf11-v-continuation-terminal-closeout.md)、[paper_v26](paper/paper_v26/README.md)、[复现](paper/paper_v26/reproducibility.md)。[paper_v25](paper/paper_v25/README.md)、[LF11四臂](docs/experiment/2026-09-11-phk-v23-lf11-terminal-closeout.md)和LF10历史证据保持原样。用户已另行授权本轮成果发布与[云端独立复评交接](docs/notes/2026-09-12-lf11-v26-results-cloud-review-handoff.md)，实际发布身份以所属Git提交及交付消息为准。CPU训练已结束，本轮未启动云实例，stress未读；没有新增科研执行授权。
