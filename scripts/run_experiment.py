from __future__ import annotations
import argparse
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from storage_decision.experiment import run

def main() -> None:
    parser = argparse.ArgumentParser(description="Run the P2 storage decision experiment")
    parser.add_argument("--config", default=str(ROOT / "configs/base.yaml"))
    parser.add_argument("--output-root", type=Path)
    args = parser.parse_args()
    result = run(args.config, ROOT, args.output_root)
    print(result["summary"].to_string(index=False))
    print(f"\nArtifacts written under: {Path(result['output_root']).name}")

if __name__ == "__main__":
    main()
