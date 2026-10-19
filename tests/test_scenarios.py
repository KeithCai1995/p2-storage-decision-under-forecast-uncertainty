from __future__ import annotations
import sys
import unittest
from pathlib import Path
import numpy as np
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from storage_decision.scenarios import QUANTILE_COLUMNS, generate_price_scenarios, generate_uniforms


class TestScenarioSampling(unittest.TestCase):
    def setUp(self):
        self.day = pd.DataFrame(np.tile(np.array([0., 10., 25., 50., 75., 90., 100.]), (24, 1)), columns=QUANTILE_COLUMNS)
        for mode, scale in [("static", 2.), ("adaptive", 3.)]:
            self.day[f"{mode}_lower"] = 50. - 40. * scale
            self.day[f"{mode}_upper"] = 50. + 40. * scale

    def test_common_uniforms_preserve_underlying_ranks_across_modes(self):
        uniforms = generate_uniforms(60, 24, 0.65, 19)
        samples = {mode: generate_price_scenarios(self.day, mode, 60, 0.65, 19, uniforms) for mode in ["raw", "static", "adaptive"]}
        np.testing.assert_allclose(samples["static"], 50. + 2. * (samples["raw"] - 50.), atol=1e-12)
        np.testing.assert_allclose(samples["adaptive"], 50. + 3. * (samples["raw"] - 50.), atol=1e-12)
        np.testing.assert_array_equal(samples["adaptive"], generate_price_scenarios(self.day, "adaptive", 60, 0.65, 19))

    def test_infinite_source_interval_is_explicitly_capped_and_scenarios_finite(self):
        self.day["adaptive_lower"] = -np.inf
        self.day["adaptive_upper"] = np.inf
        raw = generate_price_scenarios(self.day, "raw", 60, 0.65, 19)
        adaptive = generate_price_scenarios(self.day, "adaptive", 60, 0.65, 19)
        self.assertTrue(np.isfinite(adaptive).all())
        np.testing.assert_allclose(adaptive, 50. + 4. * (raw - 50.), atol=1e-12)

    def test_rejects_invalid_sampling_and_forecast_inputs(self):
        for n, loading, seed in [(0, .65, 1), (1.5, .65, 1), (60, np.nan, 1), (60, np.inf, 1), (60, .65, -1)]:
            with self.assertRaises(ValueError): generate_price_scenarios(self.day, "raw", n, loading, seed)
        for value in [np.nan, np.inf, -1.]:
            changed = self.day.copy()
            changed.loc[0, "q50"] = value
            with self.assertRaises(ValueError): generate_price_scenarios(changed, "raw", 60, .65, 1)


if __name__ == "__main__": unittest.main()
