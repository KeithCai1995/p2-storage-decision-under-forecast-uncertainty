from __future__ import annotations
import hashlib
import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
import numpy as np
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from compare_reference_outputs import TABLES, compare_table
from storage_decision.battery import BatteryConfig, constraint_diagnostics
from storage_decision.experiment import run
CASES = (("base.yaml", "baseline"), ("cvar_weight_070.yaml", "cvar_weight_070"), ("high_risk_aversion.yaml", "cvar_weight_085"))


def verify_saved_run(destination: Path) -> int:
    manifest = json.loads((destination / "run_manifest.json").read_text(encoding="utf-8"))
    assert manifest["package_version"] == "1.1.0", "Historical manifest is not a corrected release"
    assert manifest["formulation"] == "milp_exclusive_charge_discharge_binary_v1"
    assert manifest["cvar_estimator"] == "empirical_fixed_probability_mass_v1"
    assert manifest["scenario_sampling"].startswith("common_random_numbers_v1")
    assert manifest["source_sha256"] == hashlib.sha256((ROOT / "data/p1_forecasts.csv").read_bytes()).hexdigest()
    assert manifest["source_rows"] == 1992 and manifest["test_days"] == 83
    assert manifest["horizon1_issue_equals_target_rows"] == 83
    daily = pd.read_csv(destination / "tables/daily_results.csv")
    schedules = pd.read_csv(destination / "tables/all_schedules.csv")
    assert len(daily) == 581 and len(schedules) == 13944
    assert np.isfinite(daily.select_dtypes(include="number").to_numpy()).all()
    assert daily.constraint_violations.eq(0).all()
    battery = BatteryConfig(**manifest["battery"])
    checked = 0
    for _, schedule in schedules.groupby(["issue_day", "strategy"]):
        assert len(schedule) == 24
        diagnostics = constraint_diagnostics(schedule.sort_values("hour"), battery)
        assert diagnostics["constraint_violations"] == 0, diagnostics
        checked += 1
    summary = pd.read_csv(destination / "tables/strategy_metrics.csv").set_index("strategy")
    frontier = pd.read_csv(destination / "tables/risk_frontier.csv")
    selected = frontier[np.isclose(frontier.cvar_weight, manifest["risk"]["cvar_weight"])]
    if len(selected):
        for column in ["mean_daily_profit_eur", "empirical_cvar_loss_eur"]:
            assert np.isclose(selected.iloc[0][column], summary.loc["adaptive_cvar", column], atol=1e-7, rtol=0), "Frontier must reuse the strategy's scenarios"
    return checked


def main() -> int:
    failures, comparisons, checked = 0, 0, 0
    scratch = ROOT / "local_runs/release_checks"
    scratch.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix="p2_v110_release_check_", dir=scratch) as temporary:
        for config, snapshot in CASES:
            reference = ROOT / "corrected_v110" / snapshot
            checked += verify_saved_run(reference)
            destination = Path(temporary) / snapshot
            run(ROOT / "configs" / config, ROOT, destination)
            checked += verify_saved_run(destination)
            for name in TABLES:
                matched, delta = compare_table(destination / "tables" / name, reference / "tables" / name, 1e-8)
                print(f"{'PASS' if matched else 'FAIL'} corrected_v110/{snapshot}/{name}: max absolute difference = {delta:.12g}", flush=True)
                comparisons += 1
                failures += int(not matched)
    print(f"{comparisons - failures}/{comparisons} corrected release table comparisons passed; {checked} saved/rerun schedules fully checked. Historical CI is not evidence for this local revision.")
    return int(failures > 0)


if __name__ == "__main__": raise SystemExit(main())
