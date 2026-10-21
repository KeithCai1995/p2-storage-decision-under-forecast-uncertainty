"""Fresh, nested N=60/200 study; never changes the seven-strategy references."""
from __future__ import annotations
import argparse
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from storage_decision.supplementary import run_supplementary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "configs/base.yaml")
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--pilot-days", type=int, help="Time a small pilot; not a complete study")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    output = args.output_root or ROOT / ("local_runs/supplementary_pilot" if args.pilot_days is not None else "local_runs/scenario_count_study")
    run_supplementary(args.config, ROOT, output, pilot_days=args.pilot_days, overwrite=args.overwrite)


if __name__ == "__main__":
    main()
