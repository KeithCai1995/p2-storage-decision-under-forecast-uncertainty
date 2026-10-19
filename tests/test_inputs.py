from __future__ import annotations
import copy
import sys
import unittest
from pathlib import Path
import numpy as np
import pandas as pd
import yaml
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from storage_decision.experiment import validate_inputs


class TestInputValidation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = yaml.safe_load((ROOT / "configs/base.yaml").read_text(encoding="utf-8"))
        cls.forecasts = pd.read_csv(ROOT / "data/p1_forecasts.csv", parse_dates=["issue_time", "target_time"]).iloc[:24].copy()

    def test_valid_corrected_input(self):
        validate_inputs(self.forecasts, self.config)

    def test_rejects_invalid_config_values(self):
        changes = [("risk", "cvar_alpha", np.nan), ("risk", "cvar_weight", np.inf),
                   ("scenarios", "n_scenarios", 0), ("scenarios", "n_scenarios", 1.5),
                   ("scenarios", "common_factor_loading", np.inf),
                   ("evaluation", "frontier_weights", [0., np.nan]),
                   ("evaluation", "sensitivity_days", 0), ("battery", "energy_capacity_mwh", np.nan)]
        for section, key, value in changes:
            config = copy.deepcopy(self.config)
            config[section][key] = value
            with self.assertRaises(ValueError): validate_inputs(self.forecasts, config)
        for value in [np.nan, -1, 1.5, True]:
            config = copy.deepcopy(self.config)
            config["seed"] = value
            with self.assertRaises(ValueError): validate_inputs(self.forecasts, config)

    def test_rejects_invalid_forecast_rows(self):
        for column, value in [("price_eur_mwh", np.inf), ("q50", np.nan), ("horizon", 2.), ("issue_time", pd.NaT), ("adaptive_lower", np.nan)]:
            forecasts = self.forecasts.copy()
            forecasts.loc[forecasts.index[0], column] = value
            with self.assertRaises(ValueError): validate_inputs(forecasts, self.config)
        with self.assertRaises(ValueError): validate_inputs(self.forecasts.iloc[:-1], self.config)


if __name__ == "__main__": unittest.main()
