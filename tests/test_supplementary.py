from __future__ import annotations
import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
import numpy as np
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from storage_decision.battery import BatteryConfig, constraint_diagnostics, realised_profit
from storage_decision.scenarios import generate_nested_uniforms, generate_uniforms
from storage_decision.supplementary import idle_schedule, paired_action_differences, run_supplementary


class TestSupplementaryStudy(unittest.TestCase):
    def test_nested_uniforms_are_exact_prefixes_without_changing_legacy_sampler(self):
        nested = generate_nested_uniforms((60, 200), 24, .65, 20260817)
        np.testing.assert_array_equal(nested[60], nested[200][:60])
        np.testing.assert_array_equal(nested[200], generate_uniforms(200, 24, .65, 20260817))
        self.assertFalse(np.array_equal(nested[60], generate_uniforms(60, 24, .65, 20260817)))
        for counts in ((), (0, 200), (60, 60), (1.5, 200), (True, 200)):
            with self.assertRaises(ValueError):
                generate_nested_uniforms(counts, 24, .65, 1)

    def test_idle_is_feasible_and_zero_even_at_negative_prices(self):
        for terminal in (False, True):
            battery = BatteryConfig(terminal_soc_equal_initial=terminal)
            schedule = idle_schedule(battery)
            self.assertEqual(constraint_diagnostics(schedule, battery)["constraint_violations"], 0.)
            self.assertEqual(realised_profit(np.linspace(-150, 200, 24), schedule, 2.), 0.)

    def test_action_difference_uses_both_charge_and_discharge(self):
        small = pd.DataFrame({"seed": [1, 1], "strategy": ["static_cvar"] * 2, "issue_day": [337] * 2,
                              "hour": [1, 2], "n_scenarios": [60] * 2, "charge_mw": [1., 0.], "discharge_mw": [0., .8]})
        large = small.copy()
        large["n_scenarios"] = 200
        large["charge_mw"] = [0., 0.]
        large["discharge_mw"] = [0., 0.]
        pair = paired_action_differences(pd.concat([small, large]), (60, 200)).iloc[0]
        self.assertAlmostEqual(pair.mean_l1_action_change_mwh_per_day, 1.8)
        self.assertEqual(pair.mean_changed_hours_per_day, 2.)
        with self.assertRaises(ValueError):
            paired_action_differences(pd.concat([small, large.iloc[:1]]), (60, 200))

    def test_small_fresh_study_schema_and_metrics(self):
        with TemporaryDirectory(prefix="p2_supplementary_test_", dir=ROOT) as temporary:
            root = Path(temporary)
            (root / "data").mkdir()
            forecasts = pd.read_csv(ROOT / "data/p1_forecasts.csv").iloc[:48]
            forecasts.to_csv(root / "data/p1_forecasts.csv", index=False)
            config = root / "base.yaml"
            config.write_text((ROOT / "configs/base.yaml").read_text(encoding="utf-8"), encoding="utf-8")
            output = root / "fresh"
            result = run_supplementary(config, root, output, counts=(3, 6), seeds=(1, 2, 3), pilot_days=2)
            self.assertEqual(len(result["metrics"]), 12)
            self.assertEqual(len(result["pairs"]), 6)
            self.assertEqual(len(result["summary"]), 4)
            self.assertEqual(result["manifest"]["schedules_checked"], 26)
            self.assertEqual(result["manifest"]["constraint_violations"], 0.)
            self.assertTrue(result["manifest"]["pilot"])
            daily = pd.read_csv(output / "daily_results.csv")
            self.assertEqual(len(daily), 24)
            self.assertEqual(len(pd.read_csv(output / "all_schedules.csv")), 576)
            self.assertTrue(pd.read_csv(output / "sampling_audit.csv").nested_prefix_equal.all())
            for (seed, count, strategy), group in daily.groupby(["seed", "n_scenarios", "strategy"]):
                row = result["metrics"].loc[(result["metrics"].seed == seed) & (result["metrics"].n_scenarios == count) & (result["metrics"].strategy == strategy)].iloc[0]
                self.assertAlmostEqual(row.mean_daily_profit_eur, group.realised_profit_eur.mean(), places=9)
            self.assertEqual(json.loads((output / "study_manifest.json").read_text())["execution"], "fresh_run")
            with self.assertRaises(FileExistsError):
                run_supplementary(config, root, output, counts=(3, 6), seeds=(1,), pilot_days=1)


if __name__ == "__main__":
    unittest.main()
