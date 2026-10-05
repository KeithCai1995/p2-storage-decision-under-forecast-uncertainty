from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from storage_decision.battery import BatteryConfig, constraint_diagnostics, optimise_schedule


class TestBatteryOptimisation(unittest.TestCase):
    def setUp(self) -> None:
        self.battery = BatteryConfig(
            energy_capacity_mwh=2.0,
            power_capacity_mw=1.0,
            charge_efficiency=0.94,
            discharge_efficiency=0.94,
            initial_soc_fraction=0.5,
            throughput_cost_eur_per_mwh=1.0,
        )

    def test_schedule_is_feasible_and_terminal_soc_is_restored(self) -> None:
        prices = np.array([20.0] * 8 + [90.0] * 8 + [35.0] * 8)
        result = optimise_schedule(prices, self.battery)
        diagnostics = constraint_diagnostics(result.schedule, self.battery)
        expected_soc_end = (
            result.schedule["soc_start_mwh"].to_numpy()
            + self.battery.charge_efficiency * result.schedule["charge_mw"].to_numpy()
            - result.schedule["discharge_mw"].to_numpy() / self.battery.discharge_efficiency
        )
        np.testing.assert_allclose(
            result.schedule["soc_end_mwh"].to_numpy(),
            expected_soc_end,
            atol=1e-8,
            rtol=0.0,
        )
        self.assertEqual(diagnostics["constraint_violations"], 0.0)
        self.assertLess(diagnostics["terminal_soc_error_mwh"], 1e-7)
        self.assertLess(diagnostics["simultaneous_throughput_mwh"], 1e-7)

    def test_cvar_schedule_is_feasible(self) -> None:
        rng = np.random.default_rng(5)
        base = np.array([30.0] * 8 + [70.0] * 8 + [25.0] * 8)
        scenarios = base + rng.normal(0, 18, size=(40, 24))
        result = optimise_schedule(scenarios, self.battery, cvar_alpha=0.9, cvar_weight=0.6)
        diagnostics = constraint_diagnostics(result.schedule, self.battery)
        self.assertEqual(diagnostics["constraint_violations"], 0.0)
        self.assertTrue(np.isfinite(result.expected_profit))
        self.assertTrue(np.isfinite(result.scenario_cvar_loss))

    def test_reported_cvar_matches_the_solved_objective(self) -> None:
        rng = np.random.default_rng(7)
        scenarios = np.tile(np.r_[np.full(8, 30.), np.full(8, 90.), np.full(8, 25.)], (60, 1)) + rng.normal(0, 15, size=(60, 24))
        result = optimise_schedule(scenarios, self.battery, cvar_alpha=0.9, cvar_weight=0.55)
        self.assertAlmostEqual(result.objective_value, -result.expected_profit + 0.55 * result.scenario_cvar_loss, places=8)


if __name__ == "__main__":
    unittest.main()
