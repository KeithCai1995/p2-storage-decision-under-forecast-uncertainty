"""Reproduce scenario-draw sensitivity; no market-seed robustness claim."""
from __future__ import annotations
import json
import sys
from pathlib import Path
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from storage_decision.experiment import run
SEEDS = [20260817, 20260818, 20260819]
CASES = [("base.yaml", "baseline"), ("cvar_weight_070.yaml", "cvar_weight_070"), ("high_risk_aversion.yaml", "cvar_weight_085")]


def main():
    frames = []
    for config, case in CASES:
        for seed in SEEDS:
            destination = ROOT / "corrected_v110" / case if seed == SEEDS[0] else ROOT / "corrected_v110/multiseed" / f"seed_{seed}" / case
            if not (destination / "run_manifest.json").exists():
                run(ROOT / "configs" / config, ROOT, destination, seed)
            manifest = json.loads((destination / "run_manifest.json").read_text(encoding="utf-8"))
            assert manifest["seed"] == seed and manifest["package_version"] == "1.1.0"
            frame = pd.read_csv(destination / "tables/strategy_metrics.csv")
            frame.insert(0, "seed", seed)
            frame.insert(0, "cvar_weight", manifest["risk"]["cvar_weight"])
            frames.append(frame)
            print(f"Completed weight {manifest['risk']['cvar_weight']:.2f}, scenario seed {seed}, {manifest['test_days']} days, {manifest['scenario_count']} scenarios", flush=True)
    combined = pd.concat(frames, ignore_index=True)
    output = ROOT / "corrected_v110/multiseed"
    output.mkdir(parents=True, exist_ok=True)
    combined.to_csv(output / "strategy_metrics_by_seed.csv", index=False)
    summary = combined.groupby(["cvar_weight", "strategy"], sort=False).agg(n_seeds=("seed", "count"), mean_profit_mean=("mean_daily_profit_eur", "mean"), mean_profit_min=("mean_daily_profit_eur", "min"), mean_profit_max=("mean_daily_profit_eur", "max"), cvar_loss_mean=("empirical_cvar_loss_eur", "mean"), cvar_loss_min=("empirical_cvar_loss_eur", "min"), cvar_loss_max=("empirical_cvar_loss_eur", "max"), maximum_constraint_violation_rate=("constraint_violation_rate", "max"))
    summary.to_csv(output / "strategy_metrics_seed_summary.csv")
    print(summary.to_string())


if __name__ == "__main__": main()
