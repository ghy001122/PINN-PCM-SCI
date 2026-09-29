"""Small history-interface checks, without generating scientific trajectories."""
import numpy as np
import unittest

from scripts.conditional_history_tools import (
    REPLAY_FIELDS, history_diagnostics, replay_temperatures, reversal_events,
    verify_source_replay,
)
from pinn_pcm_sci.vo2_author_reproduction import HKEYS, Hysteresis, P


def check_same_time_readout_fresh_history_and_unclipped_input():
    temperature = np.array([[325.0], [332.0], [331.0], [371.0], [304.0]])
    original = temperature.copy()
    result = replay_temperatures(temperature)
    history = Hysteresis(1)
    assert history.T_last[0] == 324.9
    for index, current in enumerate(temperature):
        history.reversal(current)
        np.testing.assert_array_equal(result["resistance"][index], history.resistance(current, dynamic=True))
        np.testing.assert_array_equal(result["g"][index], history.g(np.clip(current, 305.0, 370.0)))
        for key in HKEYS:
            np.testing.assert_array_equal(result[key][index], getattr(history, key))
    for key in REPLAY_FIELDS:
        np.testing.assert_array_equal(result[key], replay_temperatures(temperature)[key])
    np.testing.assert_array_equal(temperature, original)
    np.testing.assert_array_equal(result["T_last"][-2:], [[370.0], [305.0]])


def check_original_joint_vector_trigger_and_all_reversal_count():
    temperature = np.array([[325.0, 325.0], [325.020, 324.999], [325.040, 325.002]])
    result = replay_temperatures(temperature)
    # Device B changes by less than 0.01 K, but device A triggers both histories.
    np.testing.assert_array_equal(result["delta"][:, 1], [1, -1, 1])
    np.testing.assert_array_equal(result["reversed"][:, 1], [0, 1, 1])
    events = reversal_events(np.array([0, 1, 2.0]), result)
    assert events[1]["count"] == 2
    assert events[1]["times_s"] == [1.0, 2.0]


def check_source_check_missing_inputs_and_roundoff_only():
    temperature = np.array([[325.0], [330.0], [329.0]])
    replayed = replay_temperatures(temperature)
    saved = {"temperature": temperature, **{key: value.copy() for key, value in replayed.items()}}
    assert verify_source_replay(saved, replayed)["all_bitwise_equal"]
    saved["g"][1, 0] += np.finfo(float).eps
    assert verify_source_replay(saved, replayed)["passed"]
    saved["g"][1, 0] += 1e-10
    assert not verify_source_replay(saved, replayed)["passed"]
    del saved["Tr"]
    with np.testing.assert_raises(KeyError):
        verify_source_replay(saved, replayed)


def check_diagnostics_no_feedback_and_sample_interval_reporting():
    time = np.array([0, 1, 2.0])
    temperature = np.array([[325.0], [371.0], [304.0]])
    replayed = replay_temperatures(temperature)
    voltage = np.ones_like(temperature)
    current = voltage / replayed["resistance"]
    saved = {"temperature": temperature, "device_current": current, **replayed}
    arrays, report = history_diagnostics(time, temperature, voltage, current,
                                        replayed, saved, {"full": (0.0, 2.0)})
    np.testing.assert_array_equal(arrays["r_close"], np.zeros_like(current))
    assert report["feedback"] is False
    assert report["rows"][0]["metrics"]["I_R"]["rms"] == 0.0
    outside = report["outside_constitutive_temperature"][0]
    assert outside["outside_sample_count"] == 2
    assert outside["outside_time_fraction"] == .75
    assert outside["above_370_K_intervals"][0]["first_native_index"] == 1
    assert outside["below_305_K_intervals"][0]["first_native_index"] == 2


class ConditionalHistoryTests(unittest.TestCase):
    def test_same_time_readout_fresh_history_and_unclipped_input(self):
        check_same_time_readout_fresh_history_and_unclipped_input()

    def test_original_joint_vector_trigger_and_all_reversal_count(self):
        check_original_joint_vector_trigger_and_all_reversal_count()

    def test_source_check_missing_inputs_and_roundoff_only(self):
        check_source_check_missing_inputs_and_roundoff_only()

    def test_diagnostics_no_feedback_and_sample_interval_reporting(self):
        check_diagnostics_no_feedback_and_sample_interval_reporting()


if __name__ == "__main__":
    unittest.main()
