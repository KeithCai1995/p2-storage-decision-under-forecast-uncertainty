"""Three simulated market seeds at weight .55; fixed scenario seed20260817."""
from __future__ import annotations
import json
import sys
from pathlib import Path
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from storage_decision.experiment import run


def main():
    frames = []
    for market_seed in [20260817, 20260818, 20260819]:
        destination = ROOT / "corrected_v110/baseline" if market_seed == 20260817 else ROOT / "corrected_v110/market_seeds" / f"seed_{market_seed}"
        if not (destination / "run_manifest.json").exists():
            run(ROOT / "configs/base.yaml", ROOT, destination, 20260817, f"data/market_seed_{market_seed}_p1_forecasts.csv")
        manifest = json.loads((destination / "run_manifest.json").read_text(encoding="utf-8"))
        assert manifest["package_version"] == "1.1.0" and manifest["scenario_count"] == 60 and manifest["test_days"] == 83
        frame = pd.read_csv(destination / "tables/strategy_metrics.csv")
        frame.insert(0, "market_seed", market_seed)
        frame.insert(1, "scenario_seed", manifest["seed"])
        frames.append(frame)
        print(f"Completed simulated market seed {market_seed}; scenario seed {manifest['seed']}", flush=True)
    output = ROOT / "corrected_v110/market_seeds"
    output.mkdir(parents=True, exist_ok=True)
    combined = pd.concat(frames, ignore_index=True)
    combined.to_csv(output / "strategy_metrics_by_market_seed.csv", index=False)
    print(combined[["market_seed", "strategy", "mean_daily_profit_eur", "empirical_cvar_loss_eur"]].to_string(index=False))


if __name__ == "__main__": main()
