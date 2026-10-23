from __future__ import annotations

from dataclasses import dataclass
from math import fsum

import numpy as np
import pandas as pd
from scipy.optimize import Bounds, LinearConstraint, linprog, milp
from scipy.sparse import csc_matrix


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
        numeric = [self.energy_capacity_mwh, self.power_capacity_mw, self.charge_efficiency,
                   self.discharge_efficiency, self.initial_soc_fraction, self.throughput_cost_eur_per_mwh]
        if not np.all(np.isfinite(numeric)):
            raise ValueError("Battery parameters must be finite")
        if self.energy_capacity_mwh <= 0 or self.power_capacity_mw <= 0:
            raise ValueError("Battery energy and power capacities must be positive")
        if not (0 < self.charge_efficiency <= 1 and 0 < self.discharge_efficiency <= 1):
            raise ValueError("Efficiencies must be in (0, 1]")
        if not (0 <= self.initial_soc_fraction <= 1):
            raise ValueError("Initial SOC fraction must be in [0, 1]")
        if self.throughput_cost_eur_per_mwh < 0:
            raise ValueError("Throughput cost must be non-negative")
        if not isinstance(self.terminal_soc_equal_initial, bool):
            raise ValueError("terminal_soc_equal_initial must be boolean")


@dataclass
class OptimisationResult:
    schedule: pd.DataFrame
    expected_profit: float
    scenario_cvar_loss: float
    objective_value: float
    solver_message: str
    formulation: str


def optimise_schedule(
    price_scenarios: np.ndarray,
    battery: BatteryConfig,
    cvar_alpha: float = 0.90,
    cvar_weight: float = 0.0,
    formulation: str = "milp",
) -> OptimisationResult:
    """Optimize one hourly schedule shared by all price scenarios.

    Binary modes enforce charge <= P*mode and discharge <= P*(1-mode).
    Scenario losses use the Rockafellar-Uryasev CVaR formulation.
    ``lp_relaxation`` runs the historical continuous model, which can charge
    and discharge simultaneously, for comparison.
    """

    battery.validate()
    scenarios = np.asarray(price_scenarios, dtype=float)
    if scenarios.ndim == 1:
        scenarios = scenarios[None, :]
    if scenarios.ndim != 2 or 0 in scenarios.shape or not np.all(np.isfinite(scenarios)):
        raise ValueError("price_scenarios must have shape (n_scenarios, horizon)")
    if not np.isfinite(cvar_alpha) or not np.isfinite(cvar_weight) or not (0 < cvar_alpha < 1) or cvar_weight < 0:
        raise ValueError("Invalid CVaR parameters")
    if formulation not in {"milp", "lp_relaxation"}:
        raise ValueError("formulation must be milp or lp_relaxation")

    n_scenarios, horizon = scenarios.shape
    mode_start = 3 * horizon + 1
    n_base = mode_start + (horizon if formulation == "milp" else 0)
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
    if formulation == "milp":
        for hour in range(horizon):
            charge_mode = np.zeros(n_vars)
            charge_mode[hour] = 1.0
            charge_mode[mode_start + hour] = -battery.power_capacity_mw
            inequalities.append(charge_mode)
            inequality_rhs.append(0.0)
            discharge_mode = np.zeros(n_vars)
            discharge_mode[horizon + hour] = 1.0
            discharge_mode[mode_start + hour] = battery.power_capacity_mw
            inequalities.append(discharge_mode)
            inequality_rhs.append(battery.power_capacity_mw)
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
    if formulation == "milp":
        bounds.extend([(0.0, 1.0)] * horizon)
    if use_cvar:
        bounds.append((None, None))
        bounds.extend([(0.0, None)] * n_scenarios)

    if formulation == "milp":
        lower = [(-np.inf if lo is None else lo) for lo, _ in bounds]
        upper = [(np.inf if hi is None else hi) for _, hi in bounds]
        integrality = np.zeros(n_vars, dtype=int)
        integrality[mode_start:mode_start + horizon] = 1
        result = milp(
            objective, integrality=integrality, bounds=Bounds(lower, upper),
            constraints=[
                LinearConstraint(csc_matrix(np.asarray(equalities)), equality_rhs, equality_rhs),
                LinearConstraint(csc_matrix(np.asarray(inequalities)), -np.inf, inequality_rhs),
            ], options={"mip_rel_gap": 1e-9},
        )
    else:
        result = linprog(
            objective,
            A_ub=np.asarray(inequalities) if inequalities else None,
            b_ub=np.asarray(inequality_rhs) if inequalities else None,
            A_eq=np.asarray(equalities), b_eq=np.asarray(equality_rhs),
            bounds=bounds, method="highs",
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
        formulation=formulation,
    )


def profit_by_scenario(
    price_scenarios: np.ndarray,
    charge: np.ndarray,
    discharge: np.ndarray,
    throughput_cost: float,
) -> np.ndarray:
    scenarios = np.atleast_2d(np.asarray(price_scenarios, dtype=float))
    charge = np.asarray(charge, dtype=float)
    discharge = np.asarray(discharge, dtype=float)
    if scenarios.ndim != 2 or 0 in scenarios.shape or charge.shape != (scenarios.shape[1],) or discharge.shape != charge.shape:
        raise ValueError("Prices and power arrays must have matching non-empty horizons")
    if not all(np.all(np.isfinite(values)) for values in [scenarios, charge, discharge]) or not np.isfinite(throughput_cost) or throughput_cost < 0:
        raise ValueError("Profit inputs must be finite and throughput cost non-negative")
    net_export = discharge - charge
    degradation = throughput_cost * np.sum(charge + discharge)
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
    """Return loss CVaR over exactly the worst ``1 - alpha`` probability mass.

    Loss is negative profit. Equal-weight samples use a fractional boundary
    observation when needed, including when losses are tied.
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
    battery.validate()
    if len(schedule) == 0 or not np.isfinite(tolerance) or tolerance <= 0:
        raise ValueError("A non-empty schedule and positive finite tolerance are required")
    values = schedule[["charge_mw", "discharge_mw", "soc_start_mwh", "soc_end_mwh"]].to_numpy(dtype=float)
    if not np.all(np.isfinite(values)):
        raise ValueError("Schedule values must be finite")
    charge, discharge, start, end = values.T
    soc = np.r_[start, end]
    transition_error = end - start - battery.charge_efficiency * charge + discharge / battery.discharge_efficiency
    continuity_error = start[1:] - end[:-1]
    terminal_error = abs(end[-1] - battery.initial_soc_mwh)
    counts = {
        "nonnegative_violations": np.sum(charge < -tolerance) + np.sum(discharge < -tolerance),
        "power_bound_violations": np.sum(charge > battery.power_capacity_mw + tolerance) + np.sum(discharge > battery.power_capacity_mw + tolerance),
        "soc_bound_violations": np.sum(soc < -tolerance) + np.sum(soc > battery.energy_capacity_mwh + tolerance),
        "soc_transition_violations": np.sum(np.abs(transition_error) > tolerance),
        "soc_continuity_violations": np.sum(np.abs(continuity_error) > tolerance),
        "initial_soc_violations": int(abs(start[0] - battery.initial_soc_mwh) > tolerance),
        "terminal_soc_violations": int(battery.terminal_soc_equal_initial and terminal_error > tolerance),
        "exclusivity_violations": np.sum((charge > tolerance) & (discharge > tolerance)),
    }
    return {
        "constraint_violations": float(sum(counts.values())),
        **{name: float(value) for name, value in counts.items()},
        "max_soc_transition_error_mwh": float(np.max(np.abs(transition_error))),
        "max_soc_continuity_error_mwh": float(np.max(np.abs(continuity_error), initial=0.0)),
        "initial_soc_error_mwh": float(abs(start[0] - battery.initial_soc_mwh)),
        "simultaneous_throughput_mwh": float(np.minimum(charge, discharge).sum()),
        "total_throughput_mwh": float((schedule["charge_mw"] + schedule["discharge_mw"]).sum()),
        "minimum_soc_mwh": float(soc.min()),
        "maximum_soc_mwh": float(soc.max()),
        "terminal_soc_error_mwh": float(terminal_error),
    }
