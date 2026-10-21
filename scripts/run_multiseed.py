"""Reproduce scenario-draw sensitivity; no market-seed robustness claim."""
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
SEEDS = [20260817, 20260818, 20260819]
CASES = [("base.yaml", "baseline"), ("cvar_weight_070.yaml", "cvar_weight_070"), ("high_risk_aversion.yaml", "cvar_weight_085")]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=ROOT / "local_runs/scenario_seed_study")
    parser.add_argument("--reuse-reference", action="store_true", help="Aggregate supplied runs without rerunning; recorded as reused reference, never fresh")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    output = prepare_output(args.output_root, ROOT, args.overwrite, kind="scenario_seed_study")
    frames = []
    records = []
    for config, case in CASES:
        for seed in SEEDS:
            if args.reuse_reference:
                destination = ROOT / "corrected_v110" / case if seed == SEEDS[0] else ROOT / "corrected_v110/multiseed" / f"seed_{seed}" / case
            else:
                destination = output / "runs" / f"seed_{seed}" / case
                run(ROOT / "configs" / config, ROOT, destination, seed, overwrite=args.overwrite)
            frame, manifest = load_study_run(destination, ROOT, ROOT / "configs" / config, seed)
            status = "reused_supplied_reference" if args.reuse_reference else "fresh_run"
            records.append({"case": case, "seed": seed, "execution": status, "source_run": str(destination),
                            "manifest_sha256": hashlib.sha256((destination / "run_manifest.json").read_bytes()).hexdigest(),
                            "metrics_sha256": hashlib.sha256((destination / "tables/strategy_metrics.csv").read_bytes()).hexdigest(),
                            "input_sha256": manifest["source_sha256"]})
            frame.insert(0, "seed", seed)
            frame.insert(0, "cvar_weight", manifest["risk"]["cvar_weight"])
            frames.append(frame)
            print(f"{status}: weight {manifest['risk']['cvar_weight']:.2f}, scenario seed {seed}, {manifest['test_days']} days, {manifest['scenario_count']} scenarios", flush=True)
    combined = pd.concat(frames, ignore_index=True)
    combined.to_csv(output / "strategy_metrics_by_seed.csv", index=False)
    summary = combined.groupby(["cvar_weight", "strategy"], sort=False).agg(n_seeds=("seed", "count"), mean_profit_mean=("mean_daily_profit_eur", "mean"), mean_profit_min=("mean_daily_profit_eur", "min"), mean_profit_max=("mean_daily_profit_eur", "max"), cvar_loss_mean=("empirical_cvar_loss_eur", "mean"), cvar_loss_min=("empirical_cvar_loss_eur", "min"), cvar_loss_max=("empirical_cvar_loss_eur", "max"), maximum_constraint_violation_rate=("constraint_violation_rate", "max"))
    summary.to_csv(output / "strategy_metrics_seed_summary.csv")
    (output / "study_manifest.json").write_text(json.dumps({"execution": "reused_supplied_reference" if args.reuse_reference else "fresh_run", "runs": records}, indent=2), encoding="utf-8")
    print(summary.to_string())


if __name__ == "__main__": main()
