from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import DEFAULT, patch

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from storage_decision import experiment
from storage_decision.battery import empirical_cvar_loss, profit_by_scenario
from storage_decision.scenarios import generate_price_scenarios, generate_uniforms


class TestExperimentRiskReporting(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temporary = TemporaryDirectory(prefix="p2_alpha_regression_", dir=ROOT)
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.root = Path(cls.temporary.name)
        (cls.root / "data").mkdir()
        cls.config = yaml.safe_load((ROOT / "configs/base.yaml").read_text(encoding="utf-8"))
        forecasts = pd.read_csv(
            ROOT / "data/p1_forecasts.csv", parse_dates=["issue_time", "target_time"]
        ).sort_values(["issue_day", "horizon"])
        cls.forecasts = forecasts.iloc[:48].reset_index(drop=True)
        cls.forecasts.to_csv(cls.root / "data/p1_forecasts.csv", index=False)
        cls.config["evaluation"]["frontier_weights"] = [0.0, 0.55]
        cls.config["evaluation"]["sensitivity_days"] = 2
        cls.runs = {}
        plotters = {
            name: DEFAULT
            for name in (
                "_plot_schedule", "_plot_cumulative_profit", "_plot_profit_distribution",
                "_plot_regret", "_plot_frontier", "_plot_sensitivity",
            )
        }
        # Exercise the real experiment, sampling and solver paths. Only plotting
        # is skipped; the release verifier separately renders all release plots.
        with patch.multiple(experiment, **plotters):
            for alpha in (0.80, 0.90, 0.95, 0.99):
                config = copy.deepcopy(cls.config)
                config["risk"]["cvar_alpha"] = alpha
                config_path = cls.root / f"alpha_{alpha:.2f}.yaml"
                config_path.write_text(yaml.safe_dump(config), encoding="utf-8")
                output = cls.root / f"run_{alpha:.2f}"
                result = experiment.run(config_path, cls.root, output)
                cls.runs[alpha] = {
                    "daily": pd.read_csv(output / "tables/daily_results.csv"),
                    "schedules": pd.read_csv(output / "tables/all_schedules.csv"),
                    "summary": result["summary"],
                    "manifest": result["manifest"],
                }

    def test_run_reports_configured_cvar_for_every_strategy(self) -> None:
        count = self.config["scenarios"]["n_scenarios"]
        loading = self.config["scenarios"]["common_factor_loading"]
        cost = self.config["battery"]["throughput_cost_eur_per_mwh"]
        for alpha, run in self.runs.items():
            self.assertEqual(run["manifest"]["risk"]["cvar_alpha"], alpha)
            for day_index, (issue_day, day) in enumerate(
                self.forecasts.groupby("issue_day", sort=True)
            ):
                day = day.sort_values("horizon").reset_index(drop=True)
                seed = experiment.scenario_seed(self.config["seed"], day_index)
                uniforms = generate_uniforms(count, 24, loading, seed)
                prices = {
                    "seasonal_naive": day["seasonal_naive"].to_numpy()[None, :],
                    "median_risk_neutral": day["q50"].to_numpy()[None, :],
                    "oracle": day["price_eur_mwh"].to_numpy()[None, :],
                }
                for mode in ("raw", "static", "adaptive"):
                    scenarios = generate_price_scenarios(
                        day, mode, count, loading, seed, uniforms
                    )
                    prices[f"{mode}_cvar"] = scenarios
                    if mode == "adaptive":
                        prices["adaptive_risk_neutral"] = scenarios
                for strategy, scenarios in prices.items():
                    with self.subTest(alpha=alpha, issue_day=issue_day, strategy=strategy):
                        schedule = run["schedules"].loc[
                            (run["schedules"]["issue_day"] == issue_day)
                            & (run["schedules"]["strategy"] == strategy)
                        ].sort_values("hour")
                        profits = profit_by_scenario(
                            scenarios, schedule["charge_mw"].to_numpy(),
                            schedule["discharge_mw"].to_numpy(), cost,
                        )
                        row = run["daily"].loc[
                            (run["daily"]["issue_day"] == issue_day)
                            & (run["daily"]["strategy"] == strategy)
                        ].iloc[0]
                        self.assertAlmostEqual(
                            row["in_sample_cvar_loss_eur"],
                            empirical_cvar_loss(profits, alpha), places=7,
                        )
            for strategy, rows in run["daily"].groupby("strategy", sort=False):
                with self.subTest(alpha=alpha, strategy=strategy, metric="summary"):
                    summary = run["summary"].set_index("strategy").loc[strategy]
                    self.assertAlmostEqual(
                        summary["empirical_cvar_loss_eur"],
                        empirical_cvar_loss(rows["realised_profit_eur"].to_numpy(), alpha),
                        places=7,
                    )

    def test_alpha_changes_risk_reporting_not_risk_neutral_decisions(self) -> None:
        baseline = self.runs[0.90]
        neutral = ("seasonal_naive", "median_risk_neutral", "adaptive_risk_neutral", "oracle")
        for alpha in (0.80, 0.95, 0.99):
            candidate = self.runs[alpha]
            for strategy in neutral:
                with self.subTest(alpha=alpha, strategy=strategy):
                    before = baseline["schedules"].loc[
                        baseline["schedules"]["strategy"] == strategy
                    ].reset_index(drop=True)
                    after = candidate["schedules"].loc[
                        candidate["schedules"]["strategy"] == strategy
                    ].reset_index(drop=True)
                    pd.testing.assert_frame_equal(before, after, atol=1e-8, rtol=0)
                    columns = ["realised_profit_eur", "regret_eur", "in_sample_expected_profit_eur"]
                    np.testing.assert_allclose(
                        baseline["daily"].loc[baseline["daily"]["strategy"] == strategy, columns],
                        candidate["daily"].loc[candidate["daily"]["strategy"] == strategy, columns],
                        atol=1e-8, rtol=0,
                    )
        baseline_risk = baseline["daily"].loc[
            baseline["daily"]["strategy"] == "adaptive_risk_neutral", "in_sample_cvar_loss_eur"
        ].iloc[0]
        changed_risk = self.runs[0.95]["daily"].loc[
            self.runs[0.95]["daily"]["strategy"] == "adaptive_risk_neutral", "in_sample_cvar_loss_eur"
        ].iloc[0]
        self.assertGreater(abs(changed_risk - baseline_risk), 1.0)


if __name__ == "__main__":
    unittest.main()
