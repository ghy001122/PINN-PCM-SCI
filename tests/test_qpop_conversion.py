from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

from pinn_pcm_sci.artifacts import CaseArtifact
from pinn_pcm_sci.qpop_conversion import (
    QPopConversionError,
    QPopConversionRequest,
    convert_qpop_run,
)


LOG_HEADER = (
    "#Step Time Time step Tfail Nfail Other fail Av. EOP norm Av. SOP norm "
    "Av. T (K) V (V) R (Ohm)"
)


def _write_ascii_vtu(path: Path, *, source_name: str, values: list[float]) -> None:
    path.write_text(
        """<?xml version="1.0"?>
<VTKFile type="UnstructuredGrid" version="0.1">
  <UnstructuredGrid>
    <Piece NumberOfPoints="3" NumberOfCells="1">
      <Points>
        <DataArray type="Float64" NumberOfComponents="3" format="ascii">
          0 0 0  1 0 0  0 1 0
        </DataArray>
      </Points>
      <Cells>
        <DataArray type="UInt32" Name="connectivity" format="ascii">0 1 2</DataArray>
        <DataArray type="UInt32" Name="offsets" format="ascii">3</DataArray>
        <DataArray type="UInt8" Name="types" format="ascii">5</DataArray>
      </Cells>
      <PointData Scalars="{name}">
        <DataArray type="Float64" Name="{name}" format="ascii">{values}</DataArray>
      </PointData>
    </Piece>
  </UnstructuredGrid>
</VTKFile>
""".format(name=source_name, values=" ".join(str(value) for value in values)),
        encoding="utf-8",
    )


def _write_native_fixture(root: Path, *, finished: bool = True) -> Path:
    native = root / "native"
    solution = native / "solution"
    source = native / "source"
    solution.mkdir(parents=True)
    source.mkdir()
    input_path = native / "input.xml"
    input_path.write_text(
        "<input><external><voltage unit='V'>9.0</voltage></external>"
        "<time><endtime unit='ns'>1e-6</endtime></time></input>\n",
        encoding="utf-8",
    )
    (source / "qpop-imt.py").write_text("# fixture qpop source\n", encoding="utf-8")
    (source / "customSolver.py").write_text("# fixture custom solver\n", encoding="utf-8")
    input_sha256 = hashlib.sha256(input_path.read_bytes()).hexdigest()
    source_identity = {
        "cpc_archive_sha256": "fixture-cpc-sha256",
        "qpop_git_commit": "fixture-qpop-commit",
        "script_sha256": "fixture-script-sha256",
    }
    (native / "qpop_run_metadata.json").write_text(
        json.dumps(
            {
                "schema_version": "qpop-native-run-metadata-v1",
                "source_identity": source_identity,
                "input_sha256": input_sha256,
            }
        ),
        encoding="utf-8",
    )
    rows = [
        "1 1.0e-1 1.0e-1 0 0 0 1.0 1.0 300.0 1.0 10.0",
        "2 5.0e-1 4.0e-1 0 0 0 1.0 1.0 301.0 2.0 11.0",
        "3 1.0e0 5.0e-1 0 0 0 1.0 1.0 302.0 3.0 12.0",
    ]
    trailer = "\nFinished computation, computation time: 1.000 s." if finished else ""
    (native / "log.txt").write_text(
        LOG_HEADER + "\n" + "\n".join(rows) + trailer,
        encoding="utf-8",
    )
    (solution / "eta.pvd").write_text(
        """<?xml version="1.0"?>
<VTKFile type="Collection" version="0.1"><Collection>
  <DataSet timestep="0.1" part="0" file="eta000000.pvtu" />
  <DataSet timestep="1.0" part="0" file="eta000001.pvtu" />
</Collection></VTKFile>
""",
        encoding="utf-8",
    )
    for index, values in enumerate(([0.0, 0.5, 1.0], [1.0, 0.5, 0.0])):
        stem = f"eta{index:06d}"
        (solution / f"{stem}.pvtu").write_text(
            """<?xml version="1.0"?>
<VTKFile type="PUnstructuredGrid" version="0.1">
  <PUnstructuredGrid GhostLevel="0">
    <PPointData Scalars="eta"><PDataArray type="Float64" Name="eta" /></PPointData>
    <Piece Source="{piece}" />
  </PUnstructuredGrid>
</VTKFile>
""".format(piece=f"{stem}_p0.vtu"),
            encoding="utf-8",
        )
        _write_ascii_vtu(solution / f"{stem}_p0.vtu", source_name="eta", values=list(values))
    return native


def _write_parallel_field_series(solution: Path, *, source_name: str, offset: float) -> None:
    (solution / f"{source_name}.pvd").write_text(
        """<?xml version="1.0"?>
<VTKFile type="Collection" version="0.1"><Collection>
  <DataSet timestep="0.1" part="0" file="{name}000000.pvtu" />
  <DataSet timestep="1.0" part="0" file="{name}000001.pvtu" />
</Collection></VTKFile>
""".format(name=source_name),
        encoding="utf-8",
    )
    point_sets = (
        ("0 0 0  1 0 0  0 1 0", (0, 1, 2)),
        ("1 0 0  1 1 0  0 1 0", (1, 3, 2)),
    )
    for snapshot in range(2):
        stem = f"{source_name}{snapshot:06d}"
        pieces = [f"{stem}_p{piece}.vtu" for piece in range(2)]
        (solution / f"{stem}.pvtu").write_text(
            """<?xml version="1.0"?>
<VTKFile type="PUnstructuredGrid" version="0.1">
  <PUnstructuredGrid GhostLevel="0">
    <PPointData Scalars="{name}"><PDataArray type="Float64" Name="{name}" /></PPointData>
    <Piece Source="{piece0}" /><Piece Source="{piece1}" />
  </PUnstructuredGrid>
</VTKFile>
""".format(name=source_name, piece0=pieces[0], piece1=pieces[1]),
            encoding="utf-8",
        )
        global_values = np.array([0.0, 1.0, 2.0, 3.0]) + offset + snapshot
        for piece_index, (points, global_indices) in enumerate(point_sets):
            values = " ".join(str(value) for value in global_values[list(global_indices)])
            (solution / pieces[piece_index]).write_text(
                """<?xml version="1.0"?>
<VTKFile type="UnstructuredGrid" version="0.1"><UnstructuredGrid>
  <Piece NumberOfPoints="3" NumberOfCells="1">
    <Points><DataArray type="Float64" NumberOfComponents="3" format="ascii">{points}</DataArray></Points>
    <Cells>
      <DataArray type="UInt32" Name="connectivity" format="ascii">0 1 2</DataArray>
      <DataArray type="UInt32" Name="offsets" format="ascii">3</DataArray>
      <DataArray type="UInt8" Name="types" format="ascii">5</DataArray>
    </Cells>
    <PointData Scalars="{name}"><DataArray type="Float64" Name="{name}" format="ascii">{values}</DataArray></PointData>
  </Piece>
</UnstructuredGrid></VTKFile>
""".format(points=points, name=source_name, values=values),
                encoding="utf-8",
            )


def _write_spec(root: Path, native: Path) -> Path:
    metadata = json.loads((native / "qpop_run_metadata.json").read_text(encoding="utf-8"))
    canonical_input = root / "canonical_input.xml"
    canonical_input.write_text(
        "<input><external><voltage unit='V'>9.0</voltage></external>"
        "<time><endtime unit='ns'>2e3</endtime></time></input>\n",
        encoding="utf-8",
    )
    spec = {
        "schema_version": "qpop-conversion-spec-v1",
        "conversion_spec_id": "fixture-qpop-conversion-v1",
        "case_id": "fixture-qpop-case",
        "physical_contract_id": "PROVISIONAL_G2_QPOP_CONTRACT",
        "evidence_identity": "NON_SCIENTIFIC_FIXTURE",
        "source_identity": metadata["source_identity"],
        "required_source_files": {
            "source/qpop-imt.py": hashlib.sha256(
                (native / "source" / "qpop-imt.py").read_bytes()
            ).hexdigest(),
            "source/customSolver.py": hashlib.sha256(
                (native / "source" / "customSolver.py").read_bytes()
            ).hexdigest(),
        },
        "canonical_input_path": "canonical_input.xml",
        "canonical_input_sha256": hashlib.sha256(canonical_input.read_bytes()).hexdigest(),
        "expected_input_sha256": metadata["input_sha256"],
        "allowed_input_differences": [
            {
                "xpath": "/input/time/endtime",
                "canonical_value": "2e3",
                "smoke_value": "1e-6",
                "unit": "ns",
            }
        ],
        "solution_directory": "solution",
        "mesh": {
            "coordinate_unit": "nm",
            "dimension": 2,
            "drop_axis": 2,
            "drop_tolerance": 0.0,
            "allowed_cell_types": [5],
        },
        "time_unit": "ns",
        "field_log_alignment": {
            "rtol": 5.1e-7,
            "atol": 5.1e-13,
            "auto_saveperiod": 2,
        },
        "protocol_breakpoints": [],
        "field_registry": {
            "eta": {
                "pvd": "eta.pvd",
                "source_name": "eta",
                "physical_symbol": "eta",
                "quantity_label": "structural_order_parameter",
                "unit": "1",
                "association": "point",
                "temporal_kind": "dynamic",
                "qualification_status": "SOURCE_EMISSION_ONLY_G2",
            }
        },
        "log_profile": {
            "profile_id": "qpop-cpc-v1-current-11-column",
            "normalized_header": LOG_HEADER,
            "column_keys": [
                "step",
                "time",
                "dt",
                "tfail",
                "nfail",
                "otherfail",
                "eop_norm",
                "sop_norm",
                "average_temperature",
                "reported_voltage_drop",
                "reported_resistance",
            ],
        },
        "circuit_registry": {
            "qpop_cpc_v1_reported_voltage_drop": {
                "source_column": "reported_voltage_drop",
                "unit": "V",
            },
            "qpop_cpc_v1_reported_resistance": {
                "source_column": "reported_resistance",
                "unit": "Ohm",
            },
        },
        "evaluator_audit": {
            "status": "ABSENT",
            "disposition": "OFFICIAL_EVALUATOR_NOT_PROVIDED",
        },
    }
    path = root / "conversion_spec.json"
    path.write_text(json.dumps(spec, indent=2), encoding="utf-8")
    metadata["conversion_spec_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    (native / "qpop_run_metadata.json").write_text(
        json.dumps(metadata), encoding="utf-8"
    )
    return path


def _bind_spec(native: Path, spec_path: Path) -> None:
    metadata_path = native / "qpop_run_metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["conversion_spec_sha256"] = hashlib.sha256(spec_path.read_bytes()).hexdigest()
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")


class QPopConversionContractTest(unittest.TestCase):
    def test_public_interface_preserves_field_and_circuit_time_axes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            native = _write_native_fixture(root)
            spec = _write_spec(root, native)
            bundle = root / "bundle"

            report = convert_qpop_run(
                QPopConversionRequest(
                    native_run_dir=native,
                    conversion_spec_path=spec,
                    bundle_dir=bundle,
                )
            )
            artifact = CaseArtifact.read(bundle / "case.h5")
            expected_spec_sha256 = hashlib.sha256(spec.read_bytes()).hexdigest()

        self.assertEqual(report.status, "CONVERTED")
        self.assertEqual(report.conversion_spec_id, "fixture-qpop-conversion-v1")
        np.testing.assert_array_equal(artifact.field_time, np.array([0.1, 1.0]))
        np.testing.assert_array_equal(artifact.circuit_time, np.array([0.1, 0.5, 1.0]))
        self.assertEqual(artifact.time_unit, "ns")
        self.assertEqual(artifact.mesh_unit, "nm")
        self.assertEqual(artifact.field_registry["eta"]["source_name"], "eta")
        self.assertTrue(report.artifact_sha256)
        self.assertEqual(
            report.conversion_spec_sha256,
            expected_spec_sha256,
        )

    def test_field_time_alignment_respects_frozen_log_print_precision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            native = _write_native_fixture(root)
            eta_pvd = native / "solution" / "eta.pvd"
            eta_pvd.write_text(
                eta_pvd.read_text(encoding="utf-8").replace(
                    'timestep="0.1"', 'timestep="0.10000004"'
                ),
                encoding="utf-8",
            )
            spec = _write_spec(root, native)
            bundle = root / "rounded-time-bundle"

            convert_qpop_run(
                QPopConversionRequest(
                    native_run_dir=native,
                    conversion_spec_path=spec,
                    bundle_dir=bundle,
                )
            )
            artifact = CaseArtifact.read(bundle / "case.h5")

        self.assertEqual(artifact.field_time[0], 0.10000004)

    def test_complete_registry_merges_parallel_mesh_and_maps_mu_to_psi(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            native = _write_native_fixture(root)
            solution = native / "solution"
            source_fields = {
                "eta": ("eta", "eta", "structural_order_parameter", "1"),
                "psi": ("mu", "psi", "electrochemical_potential", "1"),
                "electron_occupancy": (
                    "n",
                    "n",
                    "qpop_native_electron_occupancy",
                    "QPOP_NATIVE_OCCUPANCY_UNQUALIFIED_G2",
                ),
                "hole_occupancy": (
                    "p",
                    "p",
                    "qpop_native_hole_occupancy",
                    "QPOP_NATIVE_OCCUPANCY_UNQUALIFIED_G2",
                ),
                "electric_potential": ("phi", "phi", "electric_potential", "V"),
                "temperature": ("T", "T", "temperature", "K"),
            }
            for offset, source_name in enumerate(
                (entry[0] for entry in source_fields.values())
            ):
                _write_parallel_field_series(
                    solution,
                    source_name=source_name,
                    offset=float(offset * 10),
                )
            spec_path = _write_spec(root, native)
            spec = json.loads(spec_path.read_text(encoding="utf-8"))
            spec["field_registry"] = {
                canonical: {
                    "pvd": f"{source}.pvd",
                    "source_name": source,
                    "physical_symbol": symbol,
                    "quantity_label": quantity,
                    "unit": unit,
                    "association": "point",
                    "temporal_kind": "dynamic",
                    "qualification_status": "SOURCE_EMISSION_ONLY_G2",
                }
                for canonical, (source, symbol, quantity, unit) in source_fields.items()
            }
            spec_path.write_text(json.dumps(spec), encoding="utf-8")
            _bind_spec(native, spec_path)
            bundle = root / "parallel-bundle"

            convert_qpop_run(
                QPopConversionRequest(
                    native_run_dir=native,
                    conversion_spec_path=spec_path,
                    bundle_dir=bundle,
                )
            )
            artifact = CaseArtifact.read(bundle / "case.h5")

        self.assertEqual(artifact.nodes.shape, (4, 2))
        self.assertEqual(artifact.cells.shape, (2, 3))
        self.assertEqual(set(artifact.fields), set(source_fields))
        self.assertNotIn("mu", artifact.fields)
        self.assertEqual(artifact.field_registry["psi"]["source_name"], "mu")
        np.testing.assert_array_equal(
            artifact.fields["psi"],
            np.array([[10.0, 11.0, 12.0, 13.0], [11.0, 12.0, 13.0, 14.0]]),
        )

    def test_incomplete_native_run_writes_rejection_report_without_case(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            native = _write_native_fixture(root, finished=False)
            spec = _write_spec(root, native)
            bundle = root / "rejected-bundle"

            with self.assertRaises(QPopConversionError) as caught:
                convert_qpop_run(
                    QPopConversionRequest(
                        native_run_dir=native,
                        conversion_spec_path=spec,
                        bundle_dir=bundle,
                    )
                )
            rejection = json.loads(
                (bundle / "conversion_report.json").read_text(encoding="utf-8")
            )

        self.assertEqual(caught.exception.code, "NATIVE_RUN_INCOMPLETE")
        self.assertEqual(rejection["status"], "REJECTED")
        self.assertEqual(rejection["error_code"], "NATIVE_RUN_INCOMPLETE")
        self.assertFalse((bundle / "case.h5").exists())

    def test_historical_ten_column_log_is_not_mistaken_for_current_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            native = _write_native_fixture(root)
            old_header = (
                "#Step Time Time step Tfail Nfail Other fail Av. EOP norm "
                "Av. T (K) VO2 V drop (V) VO2 R (Ohm)"
            )
            (native / "log.txt").write_text(
                old_header
                + "\n1 1e-6 1e-6 0 0 0 1.0 300.0 1.0 10.0\n"
                + "Finished computation, computation time: 1.0 s.",
                encoding="utf-8",
            )
            spec = _write_spec(root, native)
            bundle = root / "historical-log-rejection"

            with self.assertRaises(QPopConversionError) as caught:
                convert_qpop_run(
                    QPopConversionRequest(
                        native_run_dir=native,
                        conversion_spec_path=spec,
                        bundle_dir=bundle,
                    )
                )

        self.assertEqual(caught.exception.code, "LOG_PROFILE_MISMATCH")

    def test_success_trailer_must_match_the_frozen_record_exactly(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            native = _write_native_fixture(root)
            log_path = native / "log.txt"
            log_path.write_text(
                log_path.read_text(encoding="utf-8").replace(
                    "Finished computation, computation time: 1.000 s.",
                    "Finished computation after 1.0 seconds.",
                ),
                encoding="utf-8",
            )
            spec = _write_spec(root, native)

            with self.assertRaises(QPopConversionError) as caught:
                convert_qpop_run(
                    QPopConversionRequest(
                        native_run_dir=native,
                        conversion_spec_path=spec,
                        bundle_dir=root / "malformed-success-trailer",
                    )
                )

        self.assertEqual(caught.exception.code, "LOG_PROFILE_MISMATCH")

    def test_success_trailer_must_be_unique(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            native = _write_native_fixture(root)
            log_path = native / "log.txt"
            log_path.write_text(
                log_path.read_text(encoding="utf-8")
                + "\nFinished computation, computation time: 1.000 s.",
                encoding="utf-8",
            )
            spec = _write_spec(root, native)

            with self.assertRaises(QPopConversionError) as caught:
                convert_qpop_run(
                    QPopConversionRequest(
                        native_run_dir=native,
                        conversion_spec_path=spec,
                        bundle_dir=root / "duplicate-success-trailer",
                    )
                )

        self.assertEqual(caught.exception.code, "LOG_PROFILE_MISMATCH")

    def test_success_trailer_cannot_precede_accepted_steps(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            native = _write_native_fixture(root)
            log_path = native / "log.txt"
            lines = log_path.read_text(encoding="utf-8").splitlines()
            log_path.write_text(
                "\n".join([lines[0], lines[-1], *lines[1:-1]]),
                encoding="utf-8",
            )
            spec = _write_spec(root, native)

            with self.assertRaises(QPopConversionError) as caught:
                convert_qpop_run(
                    QPopConversionRequest(
                        native_run_dir=native,
                        conversion_spec_path=spec,
                        bundle_dir=root / "early-success-trailer",
                    )
                )

        self.assertEqual(caught.exception.code, "LOG_PROFILE_MISMATCH")

    def test_success_trailer_must_be_the_last_nonempty_record(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            native = _write_native_fixture(root)
            log_path = native / "log.txt"
            log_path.write_text(
                log_path.read_text(encoding="utf-8")
                + "\n4 2.0e0 1.0e0 0 0 0 1.0 1.0 303.0 4.0 13.0",
                encoding="utf-8",
            )
            spec = _write_spec(root, native)

            with self.assertRaises(QPopConversionError) as caught:
                convert_qpop_run(
                    QPopConversionRequest(
                        native_run_dir=native,
                        conversion_spec_path=spec,
                        bundle_dir=root / "post-trailer-accepted-step",
                    )
                )

        self.assertEqual(caught.exception.code, "LOG_PROFILE_MISMATCH")

    def test_metadata_cannot_hide_an_unapproved_input_change(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            native = _write_native_fixture(root)
            spec_path = _write_spec(root, native)
            input_path = native / "input.xml"
            input_path.write_text(
                "<input><external><voltage unit='V'>10.0</voltage></external>"
                "<time><endtime unit='ns'>1e-6</endtime></time></input>\n",
                encoding="utf-8",
            )
            changed_hash = hashlib.sha256(input_path.read_bytes()).hexdigest()
            metadata = json.loads(
                (native / "qpop_run_metadata.json").read_text(encoding="utf-8")
            )
            metadata["input_sha256"] = changed_hash
            (native / "qpop_run_metadata.json").write_text(
                json.dumps(metadata), encoding="utf-8"
            )
            spec = json.loads(spec_path.read_text(encoding="utf-8"))
            spec["expected_input_sha256"] = changed_hash
            spec_path.write_text(json.dumps(spec), encoding="utf-8")
            _bind_spec(native, spec_path)

            with self.assertRaises(QPopConversionError) as caught:
                convert_qpop_run(
                    QPopConversionRequest(
                        native_run_dir=native,
                        conversion_spec_path=spec_path,
                        bundle_dir=root / "unapproved-input",
                    )
                )

        self.assertEqual(caught.exception.code, "INPUT_DELTA_NOT_ALLOWED")

    def test_metadata_cannot_hide_a_changed_executed_source_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            native = _write_native_fixture(root)
            spec_path = _write_spec(root, native)
            (native / "source" / "qpop-imt.py").write_text(
                "# modified after metadata\n", encoding="utf-8"
            )

            with self.assertRaises(QPopConversionError) as caught:
                convert_qpop_run(
                    QPopConversionRequest(
                        native_run_dir=native,
                        conversion_spec_path=spec_path,
                        bundle_dir=root / "changed-source",
                    )
                )

        self.assertEqual(caught.exception.code, "SOURCE_IDENTITY_MISMATCH")

    def test_native_metadata_binds_the_exact_conversion_spec(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            native = _write_native_fixture(root)
            spec_path = _write_spec(root, native)
            spec = json.loads(spec_path.read_text(encoding="utf-8"))
            spec["case_id"] = "tampered-after-native-intent"
            spec_path.write_text(json.dumps(spec), encoding="utf-8")

            with self.assertRaises(QPopConversionError) as caught:
                convert_qpop_run(
                    QPopConversionRequest(
                        native_run_dir=native,
                        conversion_spec_path=spec_path,
                        bundle_dir=root / "tampered-spec",
                    )
                )

        self.assertEqual(caught.exception.code, "SOURCE_IDENTITY_MISMATCH")

    def test_invalid_spec_still_publishes_one_atomic_rejection_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            native = _write_native_fixture(root)
            spec_path = root / "invalid-spec.json"
            spec_path.write_text("{not valid json", encoding="utf-8")
            bundle = root / "invalid-spec-rejection"

            with self.assertRaises(QPopConversionError) as caught:
                convert_qpop_run(
                    QPopConversionRequest(
                        native_run_dir=native,
                        conversion_spec_path=spec_path,
                        bundle_dir=bundle,
                    )
                )

            rejection = json.loads(
                (bundle / "conversion_report.json").read_text(encoding="utf-8")
            )
            bundle_files = sorted(path.name for path in bundle.iterdir())

        self.assertEqual(caught.exception.code, "SOURCE_IDENTITY_MISMATCH")
        self.assertEqual(rejection["status"], "REJECTED")
        self.assertEqual(bundle_files, ["conversion_report.json"])


if __name__ == "__main__":
    unittest.main()
