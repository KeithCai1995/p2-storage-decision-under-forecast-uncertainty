from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import norm


QUANTILE_COLUMNS = ["q05", "q10", "q25", "q50", "q75", "q90", "q95"]
QUANTILE_LEVELS = np.asarray([0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95])


def generate_price_scenarios(
    day_frame: pd.DataFrame,
    mode: str,
    n_scenarios: int,
    common_factor_loading: float,
    seed: int,
) -> np.ndarray:
    """Interpolate forecast quantiles using a shared Gaussian common factor.

    ``common_factor_loading`` is the coefficient on one factor shared by all
    hours. Consequently, for different hours the latent Gaussian Pearson
    correlation is its square. This is an exchangeable dependence structure,
    not a lag-specific temporal correlation model.
    """

    if mode not in {"raw", "static", "adaptive"}:
        raise ValueError("mode must be raw, static or adaptive")
    if len(day_frame) != 24:
        raise ValueError("A day-ahead scenario set requires exactly 24 hourly rows")
    if not (0 <= common_factor_loading < 1):
        raise ValueError("common_factor_loading must be in [0, 1)")

    rng = np.random.default_rng(seed)
    common = rng.normal(size=(n_scenarios, 1))
    idiosyncratic = rng.normal(size=(n_scenarios, 24))
    latent = common_factor_loading * common + np.sqrt(1.0 - common_factor_loading**2) * idiosyncratic
    ranks = np.clip(norm.cdf(latent), 0.001, 0.999)

    quantiles = day_frame[QUANTILE_COLUMNS].to_numpy(dtype=float)
    median = day_frame["q50"].to_numpy(dtype=float)
    if mode != "raw":
        raw_width = np.maximum(day_frame["q90"].to_numpy() - day_frame["q10"].to_numpy(), 1e-6)
        calibrated_width = (
            day_frame[f"{mode}_upper"].to_numpy() - day_frame[f"{mode}_lower"].to_numpy()
        )
        scale = np.clip(calibrated_width / raw_width, 0.35, 4.0)
        quantiles = median[:, None] + (quantiles - median[:, None]) * scale[:, None]

    scenarios = np.empty((n_scenarios, 24), dtype=float)
    for hour in range(24):
        scenarios[:, hour] = np.interp(
            ranks[:, hour],
            QUANTILE_LEVELS,
            quantiles[hour],
            left=quantiles[hour, 0],
            right=quantiles[hour, -1],
        )
    return scenarios
