"""Read saved metrics after checking the configuration and input hash."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import pandas as pd
import yaml
from . import __version__


def load_study_run(destination: Path, root: Path, config_path: Path, seed: int,
                   source_override: str | None = None) -> tuple[pd.DataFrame, dict]:
    expected = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    expected["seed"] = seed
    if source_override is not None:
        expected["data"]["p1_forecasts"] = source_override
    manifest = json.loads((destination / "run_manifest.json").read_text(encoding="utf-8"))
    if manifest.get("package_version") != __version__ or manifest.get("config") != expected:
        raise ValueError(f"Cached run does not match the requested configuration: {destination}")
    source = root / expected["data"]["p1_forecasts"]
    if manifest.get("source_sha256") != hashlib.sha256(source.read_bytes()).hexdigest():
        raise ValueError(f"Cached run input hash differs: {destination}")
    if manifest.get("formulation") != "milp_exclusive_charge_discharge_binary_v1":
        raise ValueError(f"Cached run has an unexpected physical formulation: {destination}")
    return pd.read_csv(destination / "tables/strategy_metrics.csv"), manifest
