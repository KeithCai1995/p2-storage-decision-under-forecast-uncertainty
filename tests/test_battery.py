from __future__ import annotations

import sys
import unittest
from dataclasses import replace
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

    def test_negative_price_regression_exposes_old_lp_cycle(self) -> None:
        battery = replace(self.battery, throughput_cost_eur_per_mwh=2.0)
        old = optimise_schedule(np.array([-100.0]), battery, formulation="lp_relaxation")
        corrected = optimise_schedule(np.array([-100.0]), battery)
        self.assertAlmostEqual(old.schedule.charge_mw.iloc[0], 1.0, places=8)
        self.assertAlmostEqual(old.schedule.discharge_mw.iloc[0], 0.8836, places=8)
        self.assertAlmostEqual(old.expected_profit, 7.8728, places=8)
        self.assertEqual(constraint_diagnostics(old.schedule, battery)["exclusivity_violations"], 1.0)
        self.assertAlmostEqual(corrected.expected_profit, 0.0, places=8)
        self.assertAlmostEqual(corrected.schedule.charge_mw.iloc[0], 0.0, places=8)
        self.assertAlmostEqual(corrected.schedule.discharge_mw.iloc[0], 0.0, places=8)
        self.assertAlmostEqual(corrected.schedule.soc_end_mwh.iloc[0], 1.0, places=8)
        self.assertEqual(constraint_diagnostics(corrected.schedule, battery)["constraint_violations"], 0.0)

    def test_full_diagnostics_detect_transition_continuity_and_negative_power(self) -> None:
        schedule = optimise_schedule(np.array([20., 90., 35.]), self.battery).schedule
        for column, row, value, diagnostic in [
            ("charge_mw", 0, -0.2, "nonnegative_violations"),
            ("soc_end_mwh", 0, 0.4, "soc_transition_violations"),
            ("soc_start_mwh", 1, 0.3, "soc_continuity_violations"),
            ("soc_start_mwh", 0, 0.2, "initial_soc_violations"),
            ("soc_end_mwh", 2, 0.2, "terminal_soc_violations"),
            ("soc_end_mwh", 0, 3.0, "soc_bound_violations"),
            ("charge_mw", 0, 2.0, "power_bound_violations"),
        ]:
            changed = schedule.copy()
            changed.loc[row, column] = value
            self.assertGreater(constraint_diagnostics(changed, self.battery)[diagnostic], 0, diagnostic)

    def test_rejects_nonfinite_and_empty_solver_inputs(self) -> None:
        for scenarios in [np.empty((0, 24)), np.array([]), np.array([np.nan]), np.array([np.inf])]:
            with self.assertRaises(ValueError): optimise_schedule(scenarios, self.battery)
        for field in ["energy_capacity_mwh", "power_capacity_mw", "charge_efficiency", "discharge_efficiency", "initial_soc_fraction", "throughput_cost_eur_per_mwh"]:
            for value in [np.nan, np.inf]:
                with self.assertRaises(ValueError): optimise_schedule(np.array([10.]), replace(self.battery, **{field: value}))
        for alpha, weight in [(np.nan, 0.), (np.inf, 0.), (0.9, np.nan), (0.9, np.inf)]:
            with self.assertRaises(ValueError): optimise_schedule(np.array([10.]), self.battery, alpha, weight)


if __name__ == "__main__":
    unittest.main()
