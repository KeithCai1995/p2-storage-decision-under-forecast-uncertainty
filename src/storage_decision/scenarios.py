from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import norm


QUANTILE_COLUMNS = ["q05", "q10", "q25", "q50", "q75", "q90", "q95"]
QUANTILE_LEVELS = np.asarray([0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95])


def generate_uniforms(n_scenarios: int, horizon: int, common_factor_loading: float, seed: int) -> np.ndarray:
    """Generate reproducible latent ranks shared by all compared forecast modes."""
    if isinstance(n_scenarios, bool) or not isinstance(n_scenarios, (int, np.integer)) or n_scenarios < 1:
        raise ValueError("n_scenarios must be a positive integer")
    if isinstance(horizon, bool) or not isinstance(horizon, (int, np.integer)) or horizon < 1:
        raise ValueError("horizon must be a positive integer")
    if not np.isfinite(common_factor_loading) or not 0 <= common_factor_loading < 1:
        raise ValueError("common_factor_loading must be finite and in [0, 1)")
    if isinstance(seed, bool) or not isinstance(seed, (int, np.integer)) or seed < 0:
        raise ValueError("seed must be a non-negative integer")
    rng = np.random.default_rng(seed)
    common = rng.normal(size=(n_scenarios, 1))
    idiosyncratic = rng.normal(size=(n_scenarios, horizon))
    latent = common_factor_loading * common + np.sqrt(1.0 - common_factor_loading**2) * idiosyncratic
    return np.clip(norm.cdf(latent), 0.001, 0.999)


def generate_nested_uniforms(counts: list[int] | tuple[int, ...], horizon: int,
                             common_factor_loading: float, seed: int) -> dict[int, np.ndarray]:
    """Use prefixes of one maximum-size draw for a paired scenario-count study.

    This deliberately leaves ``generate_uniforms`` and historical experiments
    unchanged. A small prefix need not equal a historical standalone small draw:
    the RNG draws all common factors before its hourly idiosyncratic factors.
    """
    if not counts:
        raise ValueError("At least one scenario count is required")
    for count in counts:
        if isinstance(count, bool) or not isinstance(count, (int, np.integer)) or count < 1:
            raise ValueError("Scenario counts must be positive integers")
    if len(set(counts)) != len(counts):
        raise ValueError("Scenario counts must be distinct")
    draws = generate_uniforms(max(counts), horizon, common_factor_loading, seed)
    return {count: draws[:count].copy() for count in counts}


def generate_price_scenarios(
    day_frame: pd.DataFrame,
    mode: str,
    n_scenarios: int,
    common_factor_loading: float,
    seed: int,
    uniforms: np.ndarray | None = None,
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
        raise ValueError("A simulated scheduling scenario set requires exactly 24 hourly rows")
    generated = generate_uniforms(n_scenarios, 24, common_factor_loading, seed)
    ranks = generated if uniforms is None else np.asarray(uniforms, dtype=float)
    if ranks.shape != (n_scenarios, 24) or not np.all(np.isfinite(ranks)) or np.any((ranks < 0) | (ranks > 1)):
        raise ValueError("uniforms must be a finite (n_scenarios, 24) array in [0, 1]")

    quantiles = day_frame[QUANTILE_COLUMNS].to_numpy(dtype=float)
    if not np.all(np.isfinite(quantiles)) or np.any(np.diff(quantiles, axis=1) < 0):
        raise ValueError("Forecast quantiles must be finite and non-decreasing")
    median = day_frame["q50"].to_numpy(dtype=float)
    if mode != "raw":
        raw_width = np.maximum(day_frame["q90"].to_numpy() - day_frame["q10"].to_numpy(), 1e-6)
        lower = day_frame[f"{mode}_lower"].to_numpy(dtype=float)
        upper = day_frame[f"{mode}_upper"].to_numpy(dtype=float)
        if np.any(np.isnan(lower)) or np.any(np.isnan(upper)) or np.any(lower > upper):
            raise ValueError("Source interval endpoints must be ordered and not NaN")
        calibrated_width = upper - lower
        if np.any(np.isnan(calibrated_width)):
            raise ValueError("Source interval widths cannot be NaN")
        # +inf is a valid finite-sample conformal interval. The scenario heuristic
        # deliberately caps its width at 4x; it does not retain that guarantee.
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
