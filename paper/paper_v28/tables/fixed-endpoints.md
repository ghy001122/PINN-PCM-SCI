# Actual fixed-endpoint comparison

| Role | S | Ephi | ET | EV | EI | bottom_current_NRMSE | power_trace_NRMSE | energy_error | local_joule_NRMSE | Strict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| E0 | 0.0011285156 | 0.023414684 | 0.012423696 | 0.0038311927 | 0.025549044 | 0.025549044 | 0.026414636 | 0.012356181 | 0.11102462 | False |
| D_E | 0.00078703125 | 0.015582121 | 0.010714735 | 0.0011088374 | 0.0072425692 | 0.0072425692 | 0.0072132284 | 0.0028819851 | 0.042477184 | False |
| P_E | 0.0008190625 | 0.015999677 | 0.010662242 | 0.0010848243 | 0.0069381868 | 0.0069381868 | 0.0068173063 | 0.0021883069 | 0.043285871 | False |
| B_E | 0.0014084375 | 0.023769782 | 0.013278255 | 0.0025584499 | 0.017282289 | 0.017282289 | 0.017562293 | 0.01184941 | 0.098131903 | False |

All values are actual fixed nominal scores. Query-grid electrical solves count as inference, and the exposed nominal reference is not independent confirmation.
