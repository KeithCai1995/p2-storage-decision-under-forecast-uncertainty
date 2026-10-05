from __future__ import annotations
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from compare_reference_outputs import TABLES, compare_table
from storage_decision.experiment import run
CASES = (("base.yaml", "baseline"), ("cvar_weight_070.yaml", "cvar_weight_070"), ("high_risk_aversion.yaml", "cvar_weight_085"))

def main() -> int:
    failures = 0
    with TemporaryDirectory(prefix="p2_release_check_") as temporary:
        for config, snapshot in CASES:
            destination = Path(temporary) / snapshot
            run(ROOT / "configs" / config, ROOT, destination)
            for name in TABLES:
                matched, delta = compare_table(destination / "tables" / name, ROOT / "experiments" / snapshot / name, 1e-10)
                print(f"{'PASS' if matched else 'FAIL'} {snapshot}/{name}: max absolute difference = {delta:.12g}", flush=True)
                failures += int(not matched)
    print(f"\n{9 - failures}/9 release table comparisons passed.")
    return int(failures > 0)
if __name__ == "__main__":
    raise SystemExit(main())
