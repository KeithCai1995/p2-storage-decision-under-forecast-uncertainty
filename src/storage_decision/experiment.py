from __future__ import annotations

import json
import platform
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy
import yaml

from .battery import (
    BatteryConfig,
    constraint_diagnostics,
    empirical_cvar_loss,
    optimise_schedule,
    realised_profit,
)
from .scenarios import generate_price_scenarios


COLORS = {
    "navy": "#17324D",
    "blue": "#2F6B9A",
    "teal": "#2A9D8F",
    "gold": "#E9A23B",
    "red": "#C54B4B",
    "gray": "#6B7280",
    "purple": "#6D5AA7",
}


def _battery_from_config(values: dict) -> BatteryConfig:
    return BatteryConfig(**values)


def _configure_plotting() -> None:
    plt.rcParams.update(
        {
            "figure.dpi": 150,
            "savefig.dpi": 220,
            "font.size": 9,
            "axes.titlesize": 11,
            "axes.labelsize": 9,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "legend.frameon": False,
        }
    )


def _save(fig: plt.Figure, path: Path) -> None:
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def run(config_path: str | Path, root: str | Path) -> dict:
    root = Path(root)
    config = yaml.safe_load(Path(config_path).read_text(encoding="utf-8"))
    for folder in [root / "outputs" / "figures", root / "outputs" / "tables"]:
        folder.mkdir(parents=True, exist_ok=True)
    _configure_plotting()

    source = root / config["data"]["p1_forecasts"]
    forecasts = pd.read_csv(source, parse_dates=["issue_time", "target_time"])
    forecasts = forecasts.sort_values(["issue_day", "horizon"]).reset_index(drop=True)
    battery = _battery_from_config(config["battery"])
    n_scenarios = int(config["scenarios"]["n_scenarios"])
    common_factor_loading = float(config["scenarios"]["common_factor_loading"])
    cvar_alpha = float(config["risk"]["cvar_alpha"])
    cvar_weight = float(config["risk"]["cvar_weight"])
    seed = int(config["seed"])

    strategies = [
        "seasonal_naive",
        "median_risk_neutral",
        "raw_cvar",
        "static_cvar",
        "adaptive_risk_neutral",
        "adaptive_cvar",
        "oracle",
    ]
    daily_rows = []
    representative_schedules: dict[str, pd.DataFrame] = {}
    representative_day = int(
        forecasts.groupby("issue_day")["price_eur_mwh"].agg(lambda x: x.max() - x.min()).idxmax()
    )

    for day_index, (issue_day, day) in enumerate(forecasts.groupby("issue_day", sort=True)):
        day = day.sort_values("horizon").reset_index(drop=True)
        actual = day["price_eur_mwh"].to_numpy()
        scenario_sets = {
            mode: generate_price_scenarios(day, mode, n_scenarios, common_factor_loading, seed + day_index * 17 + offset)
            for offset, mode in enumerate(["raw", "static", "adaptive"], start=1)
        }
        schedule_results = {
            "seasonal_naive": optimise_schedule(day["seasonal_naive"].to_numpy(), battery),
            "median_risk_neutral": optimise_schedule(day["q50"].to_numpy(), battery),
            "raw_cvar": optimise_schedule(scenario_sets["raw"], battery, cvar_alpha, cvar_weight),
            "static_cvar": optimise_schedule(scenario_sets["static"], battery, cvar_alpha, cvar_weight),
            "adaptive_risk_neutral": optimise_schedule(scenario_sets["adaptive"], battery),
            "adaptive_cvar": optimise_schedule(scenario_sets["adaptive"], battery, cvar_alpha, cvar_weight),
            "oracle": optimise_schedule(actual, battery),
        }
        oracle_profit = realised_profit(actual, schedule_results["oracle"].schedule, battery.throughput_cost_eur_per_mwh)
        for strategy in strategies:
            result = schedule_results[strategy]
            profit = realised_profit(actual, result.schedule, battery.throughput_cost_eur_per_mwh)
            diagnostics = constraint_diagnostics(result.schedule, battery)
            daily_rows.append(
                {
                    "issue_day": int(issue_day),
                    "issue_time": day["issue_time"].iloc[0],
                    "regime": day["regime"].mode().iloc[0],
                    "strategy": strategy,
                    "realised_profit_eur": profit,
                    "oracle_profit_eur": oracle_profit,
                    "regret_eur": oracle_profit - profit,
                    "in_sample_expected_profit_eur": result.expected_profit,
                    "in_sample_cvar_loss_eur": result.scenario_cvar_loss,
                    **diagnostics,
                }
            )
            if int(issue_day) == representative_day:
                schedule = result.schedule.copy()
                schedule["actual_price_eur_mwh"] = actual
                schedule["median_price_eur_mwh"] = day["q50"].to_numpy()
                schedule["strategy"] = strategy
                representative_schedules[strategy] = schedule

    daily = pd.DataFrame(daily_rows)
    daily.to_csv(root / "outputs" / "tables" / "daily_results.csv", index=False)
    summary = _strategy_summary(daily, cvar_alpha)
    summary.to_csv(root / "outputs" / "tables" / "strategy_metrics.csv", index=False)

    representative = pd.concat(representative_schedules.values(), ignore_index=True)
    representative.to_csv(root / "outputs" / "tables" / "representative_schedule.csv", index=False)
    frontier = _risk_frontier(forecasts, battery, config)
    frontier.to_csv(root / "outputs" / "tables" / "risk_frontier.csv", index=False)
    sensitivity = _battery_sensitivity(forecasts, config)
    sensitivity.to_csv(root / "outputs" / "tables" / "battery_sensitivity.csv", index=False)

    _plot_schedule(representative_schedules, root / "outputs" / "figures" / "figure_1_representative_schedule.png")
    _plot_cumulative_profit(daily, root / "outputs" / "figures" / "figure_2_cumulative_profit.png")
    _plot_profit_distribution(daily, root / "outputs" / "figures" / "figure_3_profit_distribution.png")
    _plot_regret(summary, root / "outputs" / "figures" / "figure_4_decision_regret.png")
    _plot_frontier(frontier, root / "outputs" / "figures" / "figure_5_risk_frontier.png")
    _plot_sensitivity(sensitivity, root / "outputs" / "figures" / "figure_6_battery_sensitivity.png")

    manifest = {
        "project": "P2_forecast_to_storage",
        "data_status": "simulated_benchmark_not_field_data",
        "claim_boundary": "Research-training portfolio; not realised market revenue or a trading system.",
        "seed": seed,
        "source_file": str(source.relative_to(root)),
        "source_rows": int(len(forecasts)),
        "test_days": int(forecasts["issue_day"].nunique()),
        "battery": config["battery"],
        "risk": config["risk"],
        "scenario_count": n_scenarios,
        "software": {"python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__, "scipy": scipy.__version__},
        "config": config,
    }
    (root / "outputs" / "run_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return {"summary": summary, "frontier": frontier, "sensitivity": sensitivity, "manifest": manifest}


def _strategy_summary(daily: pd.DataFrame, cvar_alpha: float) -> pd.DataFrame:
    rows = []
    for strategy, group in daily.groupby("strategy", sort=False):
        profits = group["realised_profit_eur"].to_numpy()
        rows.append(
            {
                "strategy": strategy,
                "n_days": len(group),
                "total_profit_eur": float(profits.sum()),
                "mean_daily_profit_eur": float(profits.mean()),
                "fifth_percentile_profit_eur": float(np.quantile(profits, 0.05)),
                "empirical_cvar_loss_eur": empirical_cvar_loss(profits, cvar_alpha),
                "mean_regret_eur": float(group["regret_eur"].mean()),
                "median_regret_eur": float(group["regret_eur"].median()),
                "constraint_violation_rate": float(np.mean(group["constraint_violations"] > 0)),
                "mean_throughput_mwh": float(group["total_throughput_mwh"].mean()),
                "mean_simultaneous_throughput_mwh": float(group["simultaneous_throughput_mwh"].mean()),
            }
        )
    return pd.DataFrame(rows)


def _risk_frontier(forecasts: pd.DataFrame, battery: BatteryConfig, config: dict) -> pd.DataFrame:
    weights = [float(v) for v in config["evaluation"]["frontier_weights"]]
    n_scenarios = int(config["scenarios"]["n_scenarios"])
    common_factor_loading = float(config["scenarios"]["common_factor_loading"])
    alpha = float(config["risk"]["cvar_alpha"])
    seed = int(config["seed"]) + 5000
    rows = []
    grouped = list(forecasts.groupby("issue_day", sort=True))
    for weight in weights:
        profits = []
        for day_index, (_, day) in enumerate(grouped):
            day = day.sort_values("horizon").reset_index(drop=True)
            scenarios = generate_price_scenarios(day, "adaptive", n_scenarios, common_factor_loading, seed + day_index)
            result = optimise_schedule(scenarios, battery, alpha, weight)
            profits.append(realised_profit(day["price_eur_mwh"].to_numpy(), result.schedule, battery.throughput_cost_eur_per_mwh))
        profits_array = np.asarray(profits)
        rows.append(
            {
                "cvar_weight": weight,
                "mean_daily_profit_eur": float(profits_array.mean()),
                "fifth_percentile_profit_eur": float(np.quantile(profits_array, 0.05)),
                "empirical_cvar_loss_eur": empirical_cvar_loss(profits_array, alpha),
            }
        )
    return pd.DataFrame(rows)


def _battery_sensitivity(forecasts: pd.DataFrame, config: dict) -> pd.DataFrame:
    days = list(forecasts.groupby("issue_day", sort=True))[: int(config["evaluation"]["sensitivity_days"])]
    capacities = [1.0, 2.0, 4.0]
    efficiencies = [0.88, 0.94, 0.97]
    rows = []
    base = config["battery"].copy()
    for capacity in capacities:
        for efficiency in efficiencies:
            values = base.copy()
            values["energy_capacity_mwh"] = capacity
            values["charge_efficiency"] = efficiency
            values["discharge_efficiency"] = efficiency
            battery = _battery_from_config(values)
            profits = []
            for _, day in days:
                day = day.sort_values("horizon")
                result = optimise_schedule(day["q50"].to_numpy(), battery)
                profits.append(realised_profit(day["price_eur_mwh"].to_numpy(), result.schedule, battery.throughput_cost_eur_per_mwh))
            rows.append(
                {
                    "energy_capacity_mwh": capacity,
                    "round_trip_efficiency": efficiency**2,
                    "mean_daily_profit_eur": float(np.mean(profits)),
                }
            )
    return pd.DataFrame(rows)


def _plot_schedule(schedules: dict[str, pd.DataFrame], path: Path) -> None:
    chosen = schedules["adaptive_cvar"]
    hours = chosen["hour"].to_numpy()
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8.8, 5.8), sharex=True, gridspec_kw={"height_ratios": [1, 1.15]})
    ax1.plot(hours, chosen["actual_price_eur_mwh"], color=COLORS["navy"], marker="o", ms=3, label="Realised price")
    ax1.plot(hours, chosen["median_price_eur_mwh"], color=COLORS["gold"], lw=1.2, label="Median forecast")
    ax1.set(ylabel="EUR/MWh", title="Representative day: adaptive CVaR schedule")
    ax1.legend(ncol=2)
    ax2.bar(hours - 0.18, chosen["charge_mw"], width=0.36, color=COLORS["blue"], label="Charge")
    ax2.bar(hours + 0.18, chosen["discharge_mw"], width=0.36, color=COLORS["teal"], label="Discharge")
    ax2.plot(hours, chosen["soc_end_mwh"], color=COLORS["red"], marker="o", ms=3, label="End SOC")
    ax2.set(xlabel="Hour ahead", ylabel="MW / MWh")
    ax2.legend(ncol=3)
    _save(fig, path)


def _plot_cumulative_profit(daily: pd.DataFrame, path: Path) -> None:
    selected = ["seasonal_naive", "median_risk_neutral", "raw_cvar", "static_cvar", "adaptive_cvar", "oracle"]
    palette = [COLORS["gray"], COLORS["gold"], COLORS["purple"], COLORS["blue"], COLORS["teal"], COLORS["navy"]]
    fig, ax = plt.subplots(figsize=(8.8, 4.1))
    for strategy, color in zip(selected, palette):
        group = daily[daily["strategy"] == strategy].sort_values("issue_time")
        ax.plot(pd.to_datetime(group["issue_time"]), group["realised_profit_eur"].cumsum(), label=strategy.replace("_", " "), color=color)
    ax.set(title="Cumulative realised profit", ylabel="EUR", xlabel="Issue day")
    ax.legend(ncol=3)
    _save(fig, path)


def _plot_profit_distribution(daily: pd.DataFrame, path: Path) -> None:
    order = ["seasonal_naive", "median_risk_neutral", "raw_cvar", "static_cvar", "adaptive_risk_neutral", "adaptive_cvar"]
    arrays = [daily.loc[daily["strategy"] == strategy, "realised_profit_eur"].to_numpy() for strategy in order]
    fig, ax = plt.subplots(figsize=(8.6, 4.2))
    box = ax.boxplot(arrays, tick_labels=[v.replace("_", "\n") for v in order], patch_artist=True, showfliers=False)
    for patch, color in zip(box["boxes"], [COLORS["gray"], COLORS["gold"], COLORS["purple"], COLORS["blue"], COLORS["teal"], COLORS["navy"]]):
        patch.set_facecolor(color)
        patch.set_alpha(0.65)
    ax.axhline(0, color=COLORS["red"], lw=0.8)
    ax.set(title="Distribution of realised daily profit", ylabel="EUR")
    _save(fig, path)


def _plot_regret(summary: pd.DataFrame, path: Path) -> None:
    frame = summary[summary["strategy"] != "oracle"].sort_values("mean_regret_eur")
    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    ax.barh(frame["strategy"].str.replace("_", " "), frame["mean_regret_eur"], color=COLORS["blue"])
    ax.set(title="Mean decision regret relative to perfect foresight", xlabel="EUR/day", ylabel="")
    _save(fig, path)


def _plot_frontier(frontier: pd.DataFrame, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(5.8, 4.2))
    scatter = ax.scatter(frontier["empirical_cvar_loss_eur"], frontier["mean_daily_profit_eur"], c=frontier["cvar_weight"], cmap="viridis", s=85)
    for _, row in frontier.iterrows():
        ax.annotate(f"w={row['cvar_weight']:.2f}", (row["empirical_cvar_loss_eur"], row["mean_daily_profit_eur"]), xytext=(4, 4), textcoords="offset points", fontsize=8)
    ax.set(title="Empirical profit-risk frontier", xlabel="Empirical CVaR of loss (EUR)", ylabel="Mean daily profit (EUR)")
    fig.colorbar(scatter, ax=ax, label="CVaR weight")
    _save(fig, path)


def _plot_sensitivity(sensitivity: pd.DataFrame, path: Path) -> None:
    pivot = sensitivity.pivot(index="round_trip_efficiency", columns="energy_capacity_mwh", values="mean_daily_profit_eur")
    fig, ax = plt.subplots(figsize=(6.4, 4.0))
    image = ax.imshow(pivot.to_numpy(), cmap="Blues", aspect="auto")
    ax.set_xticks(range(len(pivot.columns)), [f"{v:.0f}" for v in pivot.columns])
    ax.set_yticks(range(len(pivot.index)), [f"{v:.2f}" for v in pivot.index])
    for i in range(len(pivot.index)):
        for j in range(len(pivot.columns)):
            ax.text(j, i, f"{pivot.iloc[i, j]:.1f}", ha="center", va="center", color="black", fontsize=8)
    ax.set(title="Battery sensitivity: mean daily profit", xlabel="Energy capacity (MWh)", ylabel="Round-trip efficiency")
    fig.colorbar(image, ax=ax, label="EUR/day")
    _save(fig, path)
