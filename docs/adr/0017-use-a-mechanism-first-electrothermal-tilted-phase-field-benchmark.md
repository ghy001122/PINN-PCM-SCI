# 先用电热倾斜相场 benchmark 裁决结构动力学时钟机制

`QPOP-TAPF-v1` 的工程链有效但其结构变量语义、温度边界和动态成核能力没有忠实闭合来源合同，固定事件门因此以 `0/9` 收口。为最快裁决论文核心方法，采用新的 `ETPF-KC-v1` 合成机制 benchmark：以归一化金属相坐标 `m∈[-1,1]`、显式 Q‑POP 结构量映射、倾斜双稳态 Allen–Cahn 动力学和二维电热反馈先完成事件、strong-raw 与 KC 门；只有 KC pilot 通过后才考虑完整 VO₂/Q‑POP transfer。旧 TAPF 不修改，ETPF 不得称为完整或合格 Q‑POP oracle。
