# 固定CS/PCHIP与能量评分子集

本目录可整体复制到独立位置；已经实际完成一次隔离评分。评分入口只对保存数组重评分，不重新拟合；包内附固定CS预测及合成测试代码，无ODE/PDE或神经推理/AD能力。输入是本项目已有作者模型数值复算数据，不是第三方实验CSV。用户已批准将本子集纳入精选Git成果；这只闭合本子集的Git获取，全论文P03外部访问仍开放。

在本目录运行（Python3.11、NumPy2.1.1、SciPy1.14.1）：

```powershell
python scripts/run_cubic_energy_comparison.py --root . --config config.json --mode score
python -m unittest discover -s tests -p "test_cubic_energy_comparison.py" -v
python -m unittest discover -s tests -p "test_circuit_energy_tools.py" -v
```

`inputs/`每个系统保存一次time、voltage、device/load/capacitor_current与observation_time/voltage；角色在同一数组的列上。`predictions/PCHIP`和`predictions/CS`分别保存锁定预测、电压导数、三支电流、多项式系数/断点/时间变换；运行时与共享输入合并字段，不重新拟合。config逐个声明十个系统的设备角色、SI单位、C/RL/Vin及身份。缺输入报错，无历史绝对路径回退。provenance原路径是来源说明，不作可执行回退。

`results/`含全部波形、峰、分解、电荷、能量和敏感性；undefined值用null。`expected-pchip-results.json`用于核对历史标量及峰。两方法全段/两个辅助窗口均报告，能量另含196个固定观测区间。不生成温度或迟滞，不评价实验CSV。基线1/0.5ns是保存来源步长，不是重复实验。

代码来源为本项目现有评分函数及明确新增能量函数；原参数/离散实现来自Qiu论文和作者仓库217d4f0ed6bfc680240021b07142a121cb4963d1。代码许可见仓库LICENSE（若分发时改变代码集合，须随同保留相应来源）。第三方实验数据和出版社图片未包含；代码许可不自动授权这些第三方资产。本次精选Git发布已由项目作者批准；扩大到历史全量包、第三方资产或其他渠道仍须另行确认范围与权利。

本目录中的预测和源数组保持FP64及全部原生时间点；不应为节省空间降精度或删点。实际输入和代码传输清单见transfer-manifest.json；它记录独立评分时复制的输入集合，后来追加的报告/结果不冒称已经包含在那次输入传输中。
