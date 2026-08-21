from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from pinn_pcm_sci.research_contracts import (
    BenchmarkContract,
    EvaluatorAudit,
    PhysicalContract,
    read_contract,
    write_contract,
)


class ResearchContractTest(unittest.TestCase):
    def test_physical_contract_round_trip_preserves_executable_closure(self) -> None:
        contract = PhysicalContract(
            contract_id="qpop-test-contract-v1",
            source_identity={"commit": "abc123", "license": "MIT"},
            independent_unknowns=("eta", "temperature", "circuit_current"),
            equations=("eta_balance", "heat_balance", "circuit_constraint"),
            constitutive_relations=("free_energy_derivative",),
            units={"time": "ns", "temperature": "K"},
            initial_conditions=("eta_initial", "temperature_initial"),
            boundary_conditions=("eta_robin", "electric_dirichlet"),
            interface_conditions=(),
            circuit_constraints=("series_resistor",),
            breakpoints=(10.0,),
            discretization={"space": "P1", "time": "adaptive_backward_euler"},
            conservation_checks=("integrated_heat_balance",),
        )
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "physical_contract.json"
            write_contract(path, contract)

            restored = read_contract(path, PhysicalContract)

        self.assertEqual(restored, contract)

    def test_absent_official_evaluator_is_explicit_and_project_evaluator_stays_separate(self) -> None:
        audit = EvaluatorAudit(
            status="ABSENT",
            disposition="OFFICIAL_EVALUATOR_NOT_PROVIDED",
            official_evaluator=None,
            frozen_project_evaluator="frozen-project-evaluator-v1",
        )
        benchmark = BenchmarkContract(
            benchmark_id="qpop-cpc-v1-author-case",
            source_identity={"doi": "10.17632/p3395559s6.1"},
            canonical_case_id="vo2-intrinsic-voltage-self-oscillation",
            input_contract={"input": "input.xml"},
            output_contract={"fields": ["eta", "temperature"]},
            preprocessing=(),
            metric_specs=(),
            evaluator_audit=audit,
        )

        self.assertEqual(benchmark.evaluator_audit.status, "ABSENT")
        self.assertIsNone(benchmark.evaluator_audit.official_evaluator)
        self.assertEqual(
            benchmark.evaluator_audit.frozen_project_evaluator,
            "frozen-project-evaluator-v1",
        )


if __name__ == "__main__":
    unittest.main()
