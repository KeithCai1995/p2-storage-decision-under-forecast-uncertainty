from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


TABLES = ("strategy_metrics.csv", "daily_results.csv", "risk_frontier.csv")


def compare_table(current_path: Path, reference_path: Path, tolerance: float) -> tuple[bool, float]:
    current = pd.read_csv(current_path)
    reference = pd.read_csv(reference_path)
    if current.shape != reference.shape or list(current.columns) != list(reference.columns):
        return False, float("inf")

    numeric_columns = [
        column for column in current.columns
        if pd.api.types.is_numeric_dtype(current[column])
        and pd.api.types.is_numeric_dtype(reference[column])
    ]
    non_numeric_columns = [column for column in current.columns if column not in numeric_columns]
    for column in non_numeric_columns:
        if not current[column].fillna("<NA>").equals(reference[column].fillna("<NA>")):
            return False, float("inf")

    max_difference = 0.0
    for column in numeric_columns:
        left = current[column].to_numpy(dtype=float)
        right = reference[column].to_numpy(dtype=float)
        difference = np.abs(left - right)
        finite = difference[np.isfinite(difference)]
        if finite.size:
            max_difference = max(max_difference, float(finite.max()))
        if not np.allclose(left, right, atol=tolerance, rtol=0.0, equal_nan=True):
            return False, max_difference
    return True, max_difference


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compare the latest P2 output tables with a supplied reference snapshot."
    )
    parser.add_argument(
        "--reference",
        required=True,
        help="Reference folder, for example experiments/baseline",
    )
    parser.add_argument(
        "--tolerance",
        type=float,
        default=1e-10,
        help="Absolute tolerance for numeric CSV columns (default: 1e-10)",
    )
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    args = parser.parse_args()

    root = args.project_root.resolve()
    current_dir = root / "outputs" / "tables"
    reference_dir = root / args.reference
    failures = 0
    for name in TABLES:
        current_path = current_dir / name
        reference_path = reference_dir / name
        if not current_path.is_file() or not reference_path.is_file():
            print(f"FAIL {name}: missing current or reference file")
            failures += 1
            continue
        matches, max_difference = compare_table(current_path, reference_path, args.tolerance)
        if matches:
            print(f"PASS {name}: values match; maximum absolute numeric difference = {max_difference:.12g}")
        else:
            print(f"FAIL {name}: table differs; maximum absolute numeric difference = {max_difference:.12g}")
            failures += 1

    if failures:
        print(f"\n{failures} table(s) did not match the reference.")
        return 1
    print("\nAll selected result tables match the reference within the stated tolerance.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
