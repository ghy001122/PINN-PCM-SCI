# G2 pybind11 provider correction authorization, 2026-08-20

## Decision

- `authorization`: `USER_CONFIRMED_GRILL_WITH_DOCS_OPTION_A`
- `scientific_route`: `RETAIN_QPOP_CPC_V1_AND_EXISTING_KC_CONTRACT`
- `implementation_change`: `SEPARATE_PYTHON_SDIST_FROM_CMAKE_PROVIDER_SOURCE`
- `environment_run_limit`: `ONE_CLEAN_INTEGRATION_RUN`
- `claim_status`: `NO_SCIENTIFIC_CLAIMS`
- `supersedes_route_record`: `docs/experiment/2026-08-20-g2-quota-recovery-closeout.md`

The user confirmed the shared execution contract after three dependency-ordered
decision rounds. The Python package remains the frozen PyPI
`pybind11-2.2.4.tar.gz`; the CMake provider must instead be built from the
official `v2.2.4` Git source at peeled commit
`9a19306fbf30642ca331d0ec88e7da54a96860f9`, with its archive identity frozen
before execution. This corrects an environment artifact role mismatch and does
not change the Q-POP physics, KC method, PhysicalContract target, benchmark, or
scientific claim boundary.

## Bounded execution contract

- provider implementation and local tests: at most 20 minutes;
- one fresh environment contract, prefix and evidence root; no compiled-state
  reuse, while immutable source archives may be reused only after identity
  validation;
- environment integration: CPU, two build jobs, at most 120 minutes;
- sequence: `resolve → preflight → build → verify`;
- native smoke: only after verify, at most 30 minutes;
- first dependency, source, configuration, ABI, compile, test, verify,
  conversion or evaluator failure stops the route and is recorded;
- only proven method-external execution damage may receive an exact replay;
- G3, PINN, pilot, GPU and formal remain unauthorized.
