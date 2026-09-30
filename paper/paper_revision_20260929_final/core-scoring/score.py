"""Recompute only the frozen primary Ephi/current/power metrics from this pack.

Usage: python -I score.py --root <package-directory>
Python >=3.11 and NumPy >=2.0; no project import, model, solver or path fallback.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


def locate(root: Path, relative: str) -> Path:
    if Path(relative).is_absolute():
        raise ValueError("Package input must be relative: " + relative)
    path = (root / relative).resolve()
    if not path.is_relative_to(root):
        raise ValueError("Input escapes package root: " + relative)
    if not path.is_file():
        raise FileNotFoundError("Missing package input: " + relative)
    return path


def read(root: Path, relative: str) -> dict:
    return json.loads(locate(root, relative).read_text(encoding="utf-8"))


def axis_weights(time: np.ndarray) -> np.ndarray:
    weights = np.empty_like(time)
    weights[0] = (time[1] - time[0]) / 2
    weights[-1] = (time[-1] - time[-2]) / 2
    weights[1:-1] = (time[2:] - time[:-2]) / 2
    return weights / (time[-1] - time[0])


def time_rms(value: np.ndarray, time: np.ndarray) -> float:
    return float(np.sqrt(np.trapezoid(value**2, time) / (time[-1] - time[0])))


def finite_fp64(value: np.ndarray, shape: tuple[int, ...], label: str) -> None:
    if value.dtype != np.dtype("float64") or value.shape != shape or not np.isfinite(value).all():
        raise ValueError("Wrong shape, precision or nonfinite array: " + label)


def score(root: Path) -> dict:
    root = root.resolve()
    config = read(root, "config.json")
    expected = read(root, "expected.json")
    # Fail before processing data when any required input is absent; no fallback.
    for path in [config["geometry"], *config["references"].values(),
                 *(item["path"] for item in config["candidates"])]:
        locate(root, path)
    with np.load(locate(root, config["geometry"]), allow_pickle=False) as saved:
        geometry = {name: saved[name] for name in saved.files}
    time = geometry["time"]
    finite_fp64(time, (1001,), "time")
    if time[0] != 0 or time[-1] != 2.5 or not np.all(np.diff(time) > 0):
        raise ValueError("Incorrect original full-history time support")
    roi = ((np.abs(geometry["cell_x"]) <= .55) & (geometry["cell_z"] >= 0)
           & (geometry["cell_z"] <= .55))
    np.testing.assert_array_equal(roi, geometry["roi_mask"])
    np.testing.assert_array_equal(np.flatnonzero(roi), geometry["roi_indices"])
    np.testing.assert_array_equal(geometry["cell_x"][roi], geometry["roi_x"])
    np.testing.assert_array_equal(geometry["cell_z"][roi], geometry["roi_z"])
    if len(roi) != 12800 or np.count_nonzero(roi) != 3872:
        raise ValueError("Unexpected original ROI")
    np.testing.assert_allclose(geometry["time_weights"], axis_weights(time), rtol=0, atol=1e-16)
    np.testing.assert_array_equal(geometry["space_weights"], np.full(3872, 1 / 3872))
    output = {}
    comparisons = []
    for protocol in ("original", "shorter"):
        with np.load(locate(root, config["references"][protocol]), allow_pickle=False) as saved:
            reference = {name: saved[name] for name in saved.files}
        np.testing.assert_array_equal(reference["time"], time)
        finite_fp64(reference["phase_roi"], (1001, 3872), protocol + "/reference/phase")
        for name in ("top_current", "bottom_current", "joule_power"):
            finite_fp64(reference[name], (1001,), protocol + "/reference/" + name)
        current_scale = time_rms(reference["top_current"], time)
        power_scale = time_rms(reference["joule_power"], time)
        if current_scale <= 1e-12 or power_scale <= 1e-12:
            raise ValueError("Original normalizer is not identifiable")
        for item in config["candidates"]:
            if item["protocol"] != protocol:
                continue
            with np.load(locate(root, item["path"]), allow_pickle=False) as saved:
                data = {name: saved[name] for name in saved.files}
            np.testing.assert_array_equal(data["time"], time)
            finite_fp64(data["phase_roi"], (1001, 3872), item["id"] + "/phase")
            for name in ("bottom_current", "joule_power"):
                finite_fp64(data[name], (1001,), item["id"] + "/" + name)
            error = data["phase_roi"] - reference["phase_roi"]
            metrics = {
                "Ephi": float(np.sqrt(np.trapezoid(np.mean(error**2, axis=1), time) /
                                      (time[-1] - time[0]))),
                # Exact historical convention: candidate bottom versus reference TOP,
                # with reference TOP RMS as denominator. Do not silently redefine.
                "bottom_current_NRMSE": time_rms(data["bottom_current"] - reference["top_current"], time) / current_scale,
                "power_trace_NRMSE": time_rms(data["joule_power"] - reference["joule_power"], time) / power_scale,
            }
            for metric, actual in metrics.items():
                frozen = expected["metrics"][item["id"]][metric]
                np.testing.assert_allclose(actual, frozen, rtol=2e-10, atol=2e-12,
                                           err_msg=item["id"] + "/" + metric)
                comparisons.append(dict(id=item["id"], metric=metric, actual=actual,
                                        expected=frozen, absolute_difference=abs(actual - frozen), passed=True))
            output[item["id"]] = dict(metrics=metrics,
                normalizers=dict(reference_top_current_RMS=current_scale, reference_joule_power_RMS=power_scale))
    if len(output) != 10 or len(comparisons) != 30:
        raise ValueError("Incomplete primary metric reproduction")
    report = dict(status="PASS_SAVED_ROI_AND_PORT_ARRAY_RESCORING", candidates=10,
        checked_metrics=30, reference="spatial", electrical_reader="fine", phase_grid=[160, 80],
        roi_cells=3872, saved_times=1001, time_window=[0, 2.5], rtol=2e-10, atol=2e-12,
        maximum_absolute_difference=max(row["absolute_difference"] for row in comparisons),
        records=output, comparisons=comparisons,
        frozen_A_B=expected["frozen_A_B"], qualification_action="copied frozen records only; not re-adjudicated",
        execution=dict(neural_calls=0, electrical_solves=0, new_reference_trajectories=0,
                       neural_AD_recomputation=False, numpy=np.__version__),
        public_access=False, P03="OPEN")
    destination = root / "recomputed"
    destination.mkdir(exist_ok=True)
    (destination / "results.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, type=Path)
    result = score(parser.parse_args().root)
    print(json.dumps({key: result[key] for key in ("status", "checked_metrics", "maximum_absolute_difference")}))
