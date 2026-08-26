# 使用 Q‑POP 热力学对齐的三场二维相场 benchmark

完整七未知量 Q‑POP PINN 与两个 reduced oracle 均未形成可辨别的 strong-raw 事件能力，而作者参考轨迹已证明目标结构事件真实存在。为优先验证论文的结构动力学时钟机制，采用 `QPOP-TAPF-v1`：保留二维电—热—结构闭环、串联电路、Q‑POP 几何/低中场范围及稳定极小值自由能差，只求解 φ、T、η，并由独立 SciPy oracle 与独立 PyTorch PINN 残差实现。该选择牺牲完整 Q‑POP 物理主张以换取事件可构造性、数值可资格化性和更快的 raw/KC 判别；旧 Q‑POP 负面结果继续保留，TAPF 不得表述为完整 Q‑POP 或实验真值。
