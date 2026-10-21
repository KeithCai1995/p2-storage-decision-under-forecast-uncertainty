"""A bounded fresh scenario-count study, separate from the seven-strategy release."""
from __future__ import annotations

import hashlib
import json
import platform
from pathlib import Path
from time import perf_counter

import numpy as np
import pandas as pd
import scipy
import yaml

from . import __version__
from .artifacts import prepare_output
from .battery import BatteryConfig, constraint_diagnostics, empirical_cvar_loss, optimise_schedule, realised_profit
from .experiment import scenario_seed, validate_inputs
from .scenarios import generate_nested_uniforms, generate_price_scenarios


def idle_schedule(battery: BatteryConfig, horizon: int = 24) -> pd.DataFrame:
    """The feasible no-transaction alternative, not an optimized trading policy."""
    battery.validate()
    if isinstance(horizon, bool) or not isinstance(horizon, int) or horizon < 1:
        raise ValueError("horizon must be a positive integer")
    return pd.DataFrame({"hour": np.arange(1, horizon + 1), "charge_mw": np.zeros(horizon),
                         "discharge_mw": np.zeros(horizon),
                         "soc_start_mwh": np.full(horizon, battery.initial_soc_mwh),
                         "soc_end_mwh": np.full(horizon, battery.initial_soc_mwh)})


def paired_action_differences(schedules: pd.DataFrame, counts: tuple[int, int]) -> pd.DataFrame:
    keys = ["seed", "strategy", "issue_day", "hour"]
    columns = keys + ["charge_mw", "discharge_mw"]
    small = schedules.loc[schedules.n_scenarios == min(counts), columns]
    large = schedules.loc[schedules.n_scenarios == max(counts), columns]
    paired = small.merge(large, on=keys, suffixes=("_small", "_large"), validate="one_to_one", how="outer", indicator=True)
    if not paired["_merge"].eq("both").all():
        raise ValueError("Every schedule must have a matched scenario-count pair")
    dc = np.abs(paired.charge_mw_large - paired.charge_mw_small)
    dd = np.abs(paired.discharge_mw_large - paired.discharge_mw_small)
    paired["l1_action_change_mwh"] = dc + dd  # one-hour periods
    paired["changed_hours"] = ((dc > 1e-7) | (dd > 1e-7)).astype(int)
    daily = paired.groupby(["seed", "strategy", "issue_day"], sort=True)[["l1_action_change_mwh", "changed_hours"]].sum()
    return daily.groupby(["seed", "strategy"], sort=True).mean().reset_index().rename(
        columns={"l1_action_change_mwh": "mean_l1_action_change_mwh_per_day", "changed_hours": "mean_changed_hours_per_day"})


def run_supplementary(config_path: str | Path, root: str | Path, output_root: str | Path,
                      counts: tuple[int, int] = (60, 200),
                      seeds: tuple[int, ...] = (20260817, 20260818, 20260819),
                      pilot_days: int | None = None, overwrite: bool = False) -> dict:
    root = Path(root).resolve()
    output = prepare_output(output_root, root, overwrite, kind="supplementary")
    config = yaml.safe_load(Path(config_path).read_text(encoding="utf-8"))
    source = root / config["data"]["p1_forecasts"]
    forecasts = pd.read_csv(source, parse_dates=["issue_time", "target_time"]).sort_values(["issue_day", "horizon"])
    validate_inputs(forecasts, config)
    if len(counts) != 2:
        raise ValueError("This paired study requires exactly two scenario counts")
    if not seeds or len(set(seeds)) != len(seeds):
        raise ValueError("Scenario seeds must be non-empty and distinct")
    loading = config["scenarios"]["common_factor_loading"]
    for seed in seeds:
        generate_nested_uniforms(counts, 24, loading, seed)
    if pilot_days is not None:
        if isinstance(pilot_days, bool) or not isinstance(pilot_days, int) or pilot_days < 1:
            raise ValueError("pilot_days must be a positive integer")
        days = forecasts.issue_day.drop_duplicates().iloc[:pilot_days]
        forecasts = forecasts.loc[forecasts.issue_day.isin(days)].copy()
    battery = BatteryConfig(**config["battery"])
    alpha, weight = config["risk"]["cvar_alpha"], config["risk"]["cvar_weight"]
    rows, schedules, audits = [], [], []
    start = perf_counter()
    for seed in seeds:
        for day_index, (issue_day, day) in enumerate(forecasts.groupby("issue_day", sort=True)):
            day = day.sort_values("horizon").reset_index(drop=True)
            uniforms = generate_nested_uniforms(counts, 24, loading, scenario_seed(seed, day_index))
            small, large = min(counts), max(counts)
            assert np.array_equal(uniforms[small], uniforms[large][:small])
            audits.append({"seed": seed, "issue_day": issue_day, "small_n": small, "large_n": large,
                           "nested_prefix_equal": True,
                           "small_uniforms_sha256": hashlib.sha256(uniforms[small].tobytes()).hexdigest(),
                           "large_uniforms_sha256": hashlib.sha256(uniforms[large].tobytes()).hexdigest()})
            for count in sorted(counts):
                for mode in ("static", "adaptive"):
                    prices = generate_price_scenarios(day, mode, count, loading,
                                                     scenario_seed(seed, day_index), uniforms[count])
                    solve_start = perf_counter()
                    result = optimise_schedule(prices, battery, alpha, weight)
                    elapsed = perf_counter() - solve_start
                    diagnostics = constraint_diagnostics(result.schedule, battery)
                    if diagnostics["constraint_violations"]:
                        raise RuntimeError(f"Invalid supplementary schedule: {diagnostics}")
                    strategy = f"{mode}_cvar"
                    saved = result.schedule.assign(seed=seed, n_scenarios=count, strategy=strategy, issue_day=issue_day)
                    schedules.append(saved)
                    rows.append({"seed": seed, "n_scenarios": count, "strategy": strategy, "issue_day": issue_day,
                                 "realised_profit_eur": realised_profit(day.price_eur_mwh.to_numpy(), result.schedule, battery.throughput_cost_eur_per_mwh),
                                 "in_sample_expected_profit_eur": result.expected_profit,
                                 "in_sample_cvar_loss_eur": result.scenario_cvar_loss,
                                 "objective_value": result.objective_value, "solve_seconds": elapsed, **diagnostics})
        print(f"Completed supplementary scenario seed {seed}: {forecasts.issue_day.nunique()} days, N={counts}", flush=True)
    wall = perf_counter() - start
    daily = pd.DataFrame(rows)
    all_schedules = pd.concat(schedules, ignore_index=True)
    metrics = []
    for (seed, count, strategy), group in daily.groupby(["seed", "n_scenarios", "strategy"], sort=True):
        profits = group.realised_profit_eur.to_numpy()
        metrics.append({"seed": seed, "n_scenarios": count, "strategy": strategy, "n_days": len(group),
                        "mean_daily_profit_eur": float(profits.mean()), "empirical_cvar_loss_eur": empirical_cvar_loss(profits, alpha),
                        "fifth_percentile_profit_eur": float(np.quantile(profits, .05)),
                        "total_solve_seconds": float(group.solve_seconds.sum()),
                        "constraint_violations": float(group.constraint_violations.sum())})
    metrics = pd.DataFrame(metrics)
    keys = ["seed", "strategy"]
    pairs = metrics.loc[metrics.n_scenarios == min(counts)].merge(
        metrics.loc[metrics.n_scenarios == max(counts)], on=keys, suffixes=("_small", "_large"), validate="one_to_one")
    pairs["mean_profit_change_eur"] = pairs.mean_daily_profit_eur_large - pairs.mean_daily_profit_eur_small
    pairs["cvar_loss_change_eur"] = pairs.empirical_cvar_loss_eur_large - pairs.empirical_cvar_loss_eur_small
    pairs = pairs.merge(paired_action_differences(all_schedules, counts), on=keys, validate="one_to_one")
    summary = metrics.groupby(["n_scenarios", "strategy"], sort=True).agg(
        n_seeds=("seed", "count"), mean_profit_mean=("mean_daily_profit_eur", "mean"),
        mean_profit_min=("mean_daily_profit_eur", "min"), mean_profit_max=("mean_daily_profit_eur", "max"),
        cvar_loss_mean=("empirical_cvar_loss_eur", "mean"), cvar_loss_min=("empirical_cvar_loss_eur", "min"),
        cvar_loss_max=("empirical_cvar_loss_eur", "max"), total_solve_seconds=("total_solve_seconds", "sum")).reset_index()
    idle = idle_schedule(battery)
    idle_rows = []
    for issue_day, day in forecasts.groupby("issue_day", sort=True):
        diagnostics = constraint_diagnostics(idle, battery)
        profit = realised_profit(day.sort_values("horizon").price_eur_mwh.to_numpy(), idle, battery.throughput_cost_eur_per_mwh)
        assert profit == 0.0 and diagnostics["constraint_violations"] == 0.0
        idle_rows.append({"issue_day": issue_day, "strategy": "idle", "realised_profit_eur": profit, **diagnostics})
    idle_daily = pd.DataFrame(idle_rows)
    idle_comparison = pd.DataFrame([{"strategy": "idle", "n_days": len(idle_daily), "mean_daily_profit_eur": 0.,
                                     "empirical_cvar_loss_eur": empirical_cvar_loss(idle_daily.realised_profit_eur.to_numpy(), alpha),
                                     "provenance": "fresh_verified_no_transaction_schedule"}])
    # Keep historical strategies visibly separate: these are reused references,
    # not results from this new nested-sampling experiment.
    reference = root / "corrected_v110/baseline"
    if pilot_days is None and (reference / "run_manifest.json").exists():
        old_manifest = json.loads((reference / "run_manifest.json").read_text(encoding="utf-8"))
        if (old_manifest["source_sha256"] == hashlib.sha256(source.read_bytes()).hexdigest()
                and old_manifest["battery"] == config["battery"] and old_manifest["risk"] == config["risk"]):
            old = pd.read_csv(reference / "tables/strategy_metrics.csv")
            old = old[["strategy", "n_days", "mean_daily_profit_eur", "empirical_cvar_loss_eur"]].assign(provenance="supplied_baseline_reference_not_rerun_here")
            idle_comparison = pd.concat([old, idle_comparison], ignore_index=True)
    for name, frame in {"daily_results": daily, "all_schedules": all_schedules, "strategy_metrics": metrics,
                        "paired_differences": pairs, "seed_summary": summary, "sampling_audit": pd.DataFrame(audits),
                        "idle_daily": idle_daily, "idle_comparison": idle_comparison}.items():
        frame.to_csv(output / f"{name}.csv", index=False)
    idle.to_csv(output / "idle_schedule.csv", index=False)
    manifest = {"package_version": __version__, "study_date": "2026-10-21", "execution": "fresh_run",
                "study": "paired_scenario_count_sensitivity", "pilot": pilot_days is not None,
                "scenario_counts": sorted(counts), "scenario_seeds": list(seeds), "strategies": ["static_cvar", "adaptive_cvar"],
                "test_days": int(forecasts.issue_day.nunique()), "schedules_checked": len(daily) + len(idle_daily),
                "strategy_schedules_checked": len(daily), "idle_schedules_checked": len(idle_daily),
                "periods_checked": 24 * (len(daily) + len(idle_daily)),
                "constraint_violations": float(daily.constraint_violations.sum() + idle_daily.constraint_violations.sum()),
                "scenario_sampling": "For each seed/day, draw max(N) uniforms once; smaller N is its exact prefix. Static/adaptive share identical uniforms.",
                "sampling_difference_from_reference": "The N=60 prefix of the N=200 draw is not the historical standalone N=60 draw; do not treat their outcomes as identical reruns.",
                "runtime_definition": "solve_seconds includes optimise_schedule only, not scenario generation, I/O or plotting; wall_seconds covers the main paired loop",
                "wall_seconds": wall, "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                "source_file": str(source.relative_to(root)), "config": config,
                "software": {"python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__, "scipy": scipy.__version__},
                "limits": "One simulated market, weight .55 by default, three paired Monte Carlo seeds; ranges are not confidence intervals or proof of scenario convergence/joint calibration."}
    (output / "study_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(summary.to_string(index=False), flush=True)
    print(f"{len(daily)} strategy schedules and {len(idle_daily)} idle schedules checked; wall {wall:.3f}s", flush=True)
    return {"metrics": metrics, "pairs": pairs, "summary": summary, "manifest": manifest}
