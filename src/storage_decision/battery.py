from __future__ import annotations

from dataclasses import dataclass
from math import fsum

import numpy as np
import pandas as pd
from scipy.optimize import linprog


@dataclass(frozen=True)
class BatteryConfig:
    energy_capacity_mwh: float = 2.0
    power_capacity_mw: float = 1.0
    charge_efficiency: float = 0.94
    discharge_efficiency: float = 0.94
    initial_soc_fraction: float = 0.50
    terminal_soc_equal_initial: bool = True
    throughput_cost_eur_per_mwh: float = 2.0

    @property
    def initial_soc_mwh(self) -> float:
        return self.energy_capacity_mwh * self.initial_soc_fraction

    def validate(self) -> None:
        if self.energy_capacity_mwh <= 0 or self.power_capacity_mw <= 0:
            raise ValueError("Battery energy and power capacities must be positive")
        if not (0 < self.charge_efficiency <= 1 and 0 < self.discharge_efficiency <= 1):
            raise ValueError("Efficiencies must be in (0, 1]")
        if not (0 <= self.initial_soc_fraction <= 1):
            raise ValueError("Initial SOC fraction must be in [0, 1]")


@dataclass
class OptimisationResult:
    schedule: pd.DataFrame
    expected_profit: float
    scenario_cvar_loss: float
    objective_value: float
    solver_message: str


def optimise_schedule(
    price_scenarios: np.ndarray,
    battery: BatteryConfig,
    cvar_alpha: float = 0.90,
    cvar_weight: float = 0.0,
) -> OptimisationResult:
    """Solve a price-taking day-ahead schedule as a linear programme.

    Decisions are common across all price scenarios. CVaR is applied to scenario loss
    using the Rockafellar-Uryasev auxiliary-variable representation.
    """

    battery.validate()
    scenarios = np.asarray(price_scenarios, dtype=float)
    if scenarios.ndim == 1:
        scenarios = scenarios[None, :]
    if scenarios.ndim != 2 or scenarios.shape[1] < 1:
        raise ValueError("price_scenarios must have shape (n_scenarios, horizon)")
    if not (0 < cvar_alpha < 1) or cvar_weight < 0:
        raise ValueError("Invalid CVaR parameters")

    n_scenarios, horizon = scenarios.shape
    n_base = 2 * horizon + (horizon + 1)
    use_cvar = cvar_weight > 0
    zeta_idx = n_base if use_cvar else None
    u_start = n_base + 1 if use_cvar else None
    n_vars = n_base + (1 + n_scenarios if use_cvar else 0)
    charge = slice(0, horizon)
    discharge = slice(horizon, 2 * horizon)
    soc = slice(2 * horizon, 2 * horizon + horizon + 1)

    mean_price = scenarios.mean(axis=0)
    throughput_cost = battery.throughput_cost_eur_per_mwh
    objective = np.zeros(n_vars)
    objective[charge] = mean_price + throughput_cost
    objective[discharge] = -mean_price + throughput_cost
    if use_cvar:
        objective[zeta_idx] = cvar_weight
        objective[u_start : u_start + n_scenarios] = cvar_weight / ((1.0 - cvar_alpha) * n_scenarios)

    equalities = []
    equality_rhs = []
    initial = np.zeros(n_vars)
    initial[2 * horizon] = 1.0
    equalities.append(initial)
    equality_rhs.append(battery.initial_soc_mwh)
    for hour in range(horizon):
        row = np.zeros(n_vars)
        row[2 * horizon + hour + 1] = 1.0
        row[2 * horizon + hour] = -1.0
        row[hour] = -battery.charge_efficiency
        row[horizon + hour] = 1.0 / battery.discharge_efficiency
        equalities.append(row)
        equality_rhs.append(0.0)
    if battery.terminal_soc_equal_initial:
        terminal = np.zeros(n_vars)
        terminal[2 * horizon + horizon] = 1.0
        equalities.append(terminal)
        equality_rhs.append(battery.initial_soc_mwh)

    inequalities = []
    inequality_rhs = []
    if use_cvar:
        for scenario_index, prices in enumerate(scenarios):
            row = np.zeros(n_vars)
            row[charge] = prices + throughput_cost
            row[discharge] = -prices + throughput_cost
            row[zeta_idx] = -1.0
            row[u_start + scenario_index] = -1.0
            inequalities.append(row)
            inequality_rhs.append(0.0)

    bounds = []
    bounds.extend([(0.0, battery.power_capacity_mw)] * horizon)
    bounds.extend([(0.0, battery.power_capacity_mw)] * horizon)
    bounds.extend([(0.0, battery.energy_capacity_mwh)] * (horizon + 1))
    if use_cvar:
        bounds.append((None, None))
        bounds.extend([(0.0, None)] * n_scenarios)

    result = linprog(
        objective,
        A_ub=np.asarray(inequalities) if inequalities else None,
        b_ub=np.asarray(inequality_rhs) if inequalities else None,
        A_eq=np.asarray(equalities),
        b_eq=np.asarray(equality_rhs),
        bounds=bounds,
        method="highs",
    )
    if not result.success:
        raise RuntimeError(f"Battery optimisation failed: {result.message}")

    x = result.x
    charge_values = x[charge]
    discharge_values = x[discharge]
    soc_values = x[soc]
    scenario_profit = profit_by_scenario(scenarios, charge_values, discharge_values, throughput_cost)
    schedule = pd.DataFrame(
        {
            "hour": np.arange(1, horizon + 1),
            "charge_mw": charge_values,
            "discharge_mw": discharge_values,
            "soc_start_mwh": soc_values[:-1],
            "soc_end_mwh": soc_values[1:],
        }
    )
    return OptimisationResult(
        schedule=schedule,
        expected_profit=float(np.mean(scenario_profit)),
        scenario_cvar_loss=empirical_cvar_loss(scenario_profit, cvar_alpha),
        objective_value=float(result.fun),
        solver_message=result.message,
    )


def profit_by_scenario(
    price_scenarios: np.ndarray,
    charge: np.ndarray,
    discharge: np.ndarray,
    throughput_cost: float,
) -> np.ndarray:
    scenarios = np.atleast_2d(np.asarray(price_scenarios, dtype=float))
    net_export = np.asarray(discharge) - np.asarray(charge)
    degradation = throughput_cost * np.sum(np.asarray(charge) + np.asarray(discharge))
    return scenarios @ net_export - degradation


def realised_profit(actual_prices: np.ndarray, schedule: pd.DataFrame, throughput_cost: float) -> float:
    return float(
        profit_by_scenario(
            np.asarray(actual_prices)[None, :],
            schedule["charge_mw"].to_numpy(),
            schedule["discharge_mw"].to_numpy(),
            throughput_cost,
        )[0]
    )


def empirical_cvar_loss(profits: np.ndarray, alpha: float = 0.90) -> float:
    """Average exactly the worst ``1 - alpha`` probability mass.

    Equal-weight samples use a fractional boundary observation when required.
    This is empirical Rockafellar-Uryasev CVaR, including discrete ties.
    """
    profits = np.asarray(profits, dtype=float)
    if profits.ndim != 1 or profits.size == 0 or not np.all(np.isfinite(profits)):
        raise ValueError("profits must be a non-empty finite one-dimensional array")
    if not np.isfinite(alpha) or not 0.0 <= alpha < 1.0:
        raise ValueError("alpha must be finite and in [0, 1)")
    ordered = np.sort(-profits)[::-1]
    mass = (1.0 - alpha) * ordered.size
    whole = int(np.floor(mass))
    fraction = mass - whole
    terms = [float(value) for value in ordered[:whole]]
    if fraction > 0.0:
        terms.append(fraction * float(ordered[whole]))
    return fsum(terms) / mass


def constraint_diagnostics(schedule: pd.DataFrame, battery: BatteryConfig, tolerance: float = 1e-7) -> dict[str, float]:
    soc = np.r_[schedule["soc_start_mwh"].iloc[0], schedule["soc_end_mwh"].to_numpy()]
    violations = (
        np.sum(schedule["charge_mw"].to_numpy() > battery.power_capacity_mw + tolerance)
        + np.sum(schedule["discharge_mw"].to_numpy() > battery.power_capacity_mw + tolerance)
        + np.sum(soc < -tolerance)
        + np.sum(soc > battery.energy_capacity_mwh + tolerance)
    )
    return {
        "constraint_violations": float(violations),
        "simultaneous_throughput_mwh": float(np.minimum(schedule["charge_mw"], schedule["discharge_mw"]).sum()),
        "total_throughput_mwh": float((schedule["charge_mw"] + schedule["discharge_mw"]).sum()),
        "minimum_soc_mwh": float(soc.min()),
        "maximum_soc_mwh": float(soc.max()),
        "terminal_soc_error_mwh": float(abs(soc[-1] - battery.initial_soc_mwh)),
    }
