"""Recompute all physical diagnostics from every current saved daily schedule."""
from __future__ import annotations
import hashlib
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from storage_decision.battery import BatteryConfig, constraint_diagnostics, optimise_schedule


def main():
    rows = []
    for path in sorted((ROOT / "corrected_v110").rglob("run_manifest.json")):
        manifest = json.loads(path.read_text(encoding="utf-8"))
        source = ROOT / manifest["config"]["data"]["p1_forecasts"]
        assert manifest["source_sha256"] == hashlib.sha256(source.read_bytes()).hexdigest()
        assert manifest["package_version"] == "1.1.0" and manifest["formulation"] == "milp_exclusive_charge_discharge_binary_v1"
        schedules = pd.read_csv(path.parent / "tables/all_schedules.csv")
        battery = BatteryConfig(**manifest["battery"])
        diagnostics = []
        for _, schedule in schedules.groupby(["issue_day", "strategy"]):
            assert len(schedule) == 24
            diagnostics.append(constraint_diagnostics(schedule.sort_values("hour"), battery))
        frame = pd.DataFrame(diagnostics)
        assert np.isfinite(frame.to_numpy()).all() and frame.constraint_violations.eq(0).all()
        rows.append({"run": path.parent.relative_to(ROOT).as_posix(), "schedules_checked": len(frame), "periods_checked": len(schedules), "constraint_violations": float(frame.constraint_violations.sum()), "max_soc_transition_error_mwh": float(frame.max_soc_transition_error_mwh.max()), "max_soc_continuity_error_mwh": float(frame.max_soc_continuity_error_mwh.max()), "max_terminal_soc_error_mwh": float(frame.terminal_soc_error_mwh.max()), "maximum_exclusivity_violations": float(frame.exclusivity_violations.max()), "source_sha256": manifest["source_sha256"]})
    evidence = ROOT / "evidence/local_revision_20261018"
    evidence.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(evidence / "all_saved_schedule_audit.csv", index=False)
    regression = []
    battery = BatteryConfig()
    for formulation in ["lp_relaxation", "milp"]:
        result = optimise_schedule(np.array([-100.]), battery, formulation=formulation)
        regression.append({"formulation": formulation, **result.schedule.iloc[0].to_dict(), "profit_eur": result.expected_profit, **constraint_diagnostics(result.schedule, battery)})
    pd.DataFrame(regression).to_csv(evidence / "negative_price_regression.csv", index=False)
    summary = {"revision": "1.1.0", "runs_audited": len(rows), "schedules_checked": sum(row["schedules_checked"] for row in rows), "periods_checked": sum(row["periods_checked"] for row in rows), "constraint_violations": sum(row["constraint_violations"] for row in rows), "max_soc_transition_error_mwh": max(row["max_soc_transition_error_mwh"] for row in rows), "max_terminal_soc_error_mwh": max(row["max_terminal_soc_error_mwh"] for row in rows), "tolerance": 1e-7}
    (evidence / "all_saved_schedule_audit.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__": main()
