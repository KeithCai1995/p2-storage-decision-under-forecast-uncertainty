"""Three simulated market seeds at weight .55; fixed scenario seed20260817."""
from __future__ import annotations
import json
import argparse
import hashlib
import sys
from pathlib import Path
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from storage_decision.experiment import run
from storage_decision.artifacts import prepare_output
from storage_decision.study_io import load_study_run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=ROOT / "local_runs/market_seed_study")
    parser.add_argument("--reuse-reference", action="store_true", help="Aggregate supplied runs only, explicitly recorded as reused references")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    output = prepare_output(args.output_root, ROOT, args.overwrite, kind="market_seed_study")
    frames = []
    records = []
    for market_seed in [20260817, 20260818, 20260819]:
        source = "data/p1_forecasts.csv" if market_seed == 20260817 else f"data/market_seed_{market_seed}_p1_forecasts.csv"
        if args.reuse_reference:
            destination = ROOT / "corrected_v110/baseline" if market_seed == 20260817 else ROOT / "corrected_v110/market_seeds" / f"seed_{market_seed}"
        else:
            destination = output / "runs" / f"seed_{market_seed}"
            run(ROOT / "configs/base.yaml", ROOT, destination, 20260817, source, overwrite=args.overwrite)
        frame, manifest = load_study_run(destination, ROOT, ROOT / "configs/base.yaml", 20260817, source)
        status = "reused_supplied_reference" if args.reuse_reference else "fresh_run"
        records.append({"market_seed": market_seed, "execution": status, "source_run": str(destination),
                        "manifest_sha256": hashlib.sha256((destination / "run_manifest.json").read_bytes()).hexdigest(),
                        "metrics_sha256": hashlib.sha256((destination / "tables/strategy_metrics.csv").read_bytes()).hexdigest(),
                        "input_sha256": manifest["source_sha256"]})
        frame.insert(0, "market_seed", market_seed)
        frame.insert(1, "scenario_seed", manifest["seed"])
        frames.append(frame)
        print(f"{status}: simulated market seed {market_seed}; scenario seed {manifest['seed']}", flush=True)
    combined = pd.concat(frames, ignore_index=True)
    combined.to_csv(output / "strategy_metrics_by_market_seed.csv", index=False)
    (output / "study_manifest.json").write_text(json.dumps({"execution": "reused_supplied_reference" if args.reuse_reference else "fresh_run", "runs": records}, indent=2), encoding="utf-8")
    print(combined[["market_seed", "strategy", "mean_daily_profit_eur", "empirical_cvar_loss_eur"]].to_string(index=False))


if __name__ == "__main__": main()
