# Matched remaining-PDE contrast

VERIFIED: E0/D_E/P_E/B_E were evaluated on the fixed nominal grid.
P_E versus D_E passes reconstruction A: **False**; function B: **False**.
Against B_E the same full gates are A: **True** and B: **True**.
The separately frozen same-layer prerequisite for P_F is **False**.

| Metric | P_E | D_E | Relative P_E change |
|---|---:|---:|---:|
| S | 0.0008190625 | 0.00078703125 | +4.070% |
| Ephi | 0.015999677 | 0.015582121 | +2.680% |
| ET | 0.010662242 | 0.010714735 | -0.490% |
| EV | 0.0010848243 | 0.0011088374 | -2.166% |
| EI | 0.0069381868 | 0.0072425692 | -4.203% |
| bottom_current_NRMSE | 0.0069381868 | 0.0072425692 | -4.203% |
| power_trace_NRMSE | 0.0068173063 | 0.0072132284 | -5.489% |
| energy_error | 0.0021883069 | 0.0028819851 | -24.069% |
| local_joule_NRMSE | 0.043285871 | 0.042477184 | +1.904% |

[Complete fixed-endpoint table](fixed-endpoints.md) and [cycle records](cycle-events.csv) retain every role.
Figures show the phase–event–device comparison, phase fields and local Joule/temperature maps.
Conservation identities are consequences of the solve and are not counted as independent method increments.
A failed matched gate does not erase submetric effects, and those effects do not replace the frozen gate.

P_F was not triggered and was not run; it is not a failed endpoint.
