# Project 2 - Forecast-to-decision for storage bidding

> **Data status:** SIMULATED BENCHMARK - NOT A TRADING SYSTEM. All prices,
> schedules, profits, losses and regret values are generated from the simulated
> Project 1 benchmark. They are not realised revenue or employer evidence.

This portfolio connects the probabilistic forecasts produced by Project 1 to a transparent
day-ahead battery scheduling model. It tests whether calibrated uncertainty changes
decisions, realised profit, regret and tail risk - not only whether it improves a forecast
score.

## What the project demonstrates

- an auditable linear battery model with SOC, power, efficiency and terminal constraints;
- scenario generation from forecast quantiles with an explicit shared-factor dependence assumption;
- risk-neutral and mean-CVaR schedules solved with SciPy/HiGHS linear programming;
- rolling day-ahead evaluation against seasonal, median and perfect-foresight baselines;
- decision regret, empirical tail loss, feasibility and battery-parameter sensitivity;
- one-command reproduction of all reported tables and figures.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate              # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python scripts/run_experiment.py --config configs/base.yaml
python scripts/compare_reference_outputs.py --reference experiments/baseline
python scripts/run_experiment.py --config configs/high_risk_aversion.yaml
python scripts/compare_reference_outputs.py --reference experiments/cvar_weight_085
python -m unittest discover -s tests -v
```

Run the comparison command immediately after its matching configuration. It checks
the current strategy, daily-result and risk-frontier tables against the saved
snapshot, with a numeric tolerance of `1e-10` and exact text-column matching.

Project 1 forecasts are included at `data/p1_forecasts.csv` so this package runs on its
own. Regenerate that file with Project 1 before claiming a new result.

`REFERENCE_RUNS.md` describes the saved reference outputs and their provenance.
The supplied archive included a log dated 18 August 2026, but that date alone
does not establish who ran the commands. Do not present it as your personal
execution record unless you personally performed those runs. The two output
snapshots are under `experiments/`.

## Scope boundary

The model is a research benchmark, not a live bidding engine. It assumes a price-taking
battery, a single day-ahead energy market, hourly settlement, perfect execution of the
chosen schedule, no network constraint and a linear throughput cost. These assumptions
are explicit so that a supervisor can see exactly what the experiment establishes and
what remains for doctoral research.

## Relationship to existing work

The battery LP, scenario optimisation and CVaR formulation build on established
operations-research and energy-storage literature. Decision-focused learning already
shows that predictive accuracy and downstream decision quality can differ, while
stochastic storage scheduling and recent conformal decision methods already address
parts of this application. `RELATED_WORK.md` records the closest strands and the
portfolio's narrow contribution boundary.

The contribution is a compact, auditable integration of Project 1 forecasts with
battery constraints, profit, regret, tail-risk and feasibility evaluation. It is not
presented as a new CVaR formulation, a complete bid-curve model or a deployable
electricity-trading strategy.

## Scenario dependence assumption

The configuration value `common_factor_loading: 0.65` is the loading on one
Gaussian factor shared by all 24 hours. Under this construction, distinct latent
hours have pairwise Pearson correlation 0.4225; the corresponding Gaussian-copula
Spearman correlation is about 0.41 before clipping and quantile interpolation.
This is an exchangeable toy dependence assumption, not a neighbouring-hour
correlation parameter or a lag-specific time-series model. The marginal hourly
quantiles do not establish joint calibration of complete 24-hour price paths.

## Reproducibility notes

The two configurations and two unit tests provide a short verification path.
The unit tests independently recompute the SOC transition and check the
terminal-SOC rule. Other key checks are the price-taking
assumption, the CVaR sensitivity result and the role of the oracle as a diagnostic
upper bound rather than a feasible strategy.
