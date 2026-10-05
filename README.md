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
pip install -r requirements-lock.txt
python -m unittest discover -s tests -v
python scripts/verify_release.py
```

The minimum Python version for the locked packages is 3.11. This v1.0.1 revision
was verified in an assisted Linux/Python 3.12.14 environment with NumPy 2.3.5,
pandas 2.2.3, SciPy 1.17.0, Matplotlib 3.10.8 and PyYAML 6.0.3. The applicant's
earlier personal reproduction used Windows/Python 3.13.15; its records remain
under `evidence/personal_run/2026-10-02/`.

The release checker reruns weights 0.55, 0.70 and 0.85 in temporary directories
without overwriting the saved baseline. It compares nine CSV tables using an
absolute numeric tolerance of 1e-10 and exact text matching. All 11 unit tests
and nine comparisons passed in the recorded assisted environment. The supplied
GitHub Actions matrix checks Linux and Windows with Python 3.11-3.13 after push;
those remote jobs have not yet been executed for this revision.

For a separate experiment and comparison:

```bash
python scripts/run_experiment.py --config configs/base.yaml --output-root evidence/runs/my_baseline
python scripts/compare_reference_outputs.py --reference experiments/baseline --current evidence/runs/my_baseline/tables
```

## CVaR reporting correction in v1.0.1

Empirical CVaR now averages exactly the worst `1 - alpha` probability mass,
including a fractional boundary observation. At alpha 0.90, sixty equally
weighted forecast scenarios contribute six observations; 83 evaluation days
contribute 8.3 observations. This agrees with empirical Rockafellar-Uryasev
CVaR even with ties. The earlier `loss >= quantile` tail mean could include
excess mass and change sharply when near-tied observations crossed a threshold.

The optimiser, forecast input, seed and three configurations are unchanged.
An audit of 3,744 paired old/new reporting solves found identical schedules,
expected profits and LP objective values. The CVaR columns, risk-frontier figure
and report were regenerated together. Current snapshots are under
`experiments/baseline`, `experiments/cvar_weight_070` and `experiments/cvar_weight_085`.
The main `outputs/` folder contains the corrected baseline. The original reference
tables remain in `experiments/legacy_threshold_tail/`; personal logs and old
output snapshots are retained. See `REFERENCE_RUNS.md`, `RELEASE_NOTES.md` and
`evidence/assisted_review/2026-10-04_cvar_fix/` for provenance and actual checks.

Project 1 forecasts are included at `data/p1_forecasts.csv`. This reporting
revision reuses those forecasts. A new forecasting model or dataset requires
regeneration of that input. These results are simulated, not trading evidence.

## Scope boundary

The model is a research benchmark, not a live bidding engine. It assumes a price-taking
battery, a single day-ahead energy market, hourly settlement, perfect execution of the
chosen schedule, no network constraint and a linear throughput cost. These assumptions
are explicit so that a supervisor can see exactly what the experiment establishes and
what remains for doctoral research.

In the supplied CSV, `issue_time` equals `target_time` for horizon 1. The CSV does
not record a separate prior-day market gate-closure timestamp. Thus the simulated
24-hour scheduling benchmark does not by itself verify operational day-ahead
forecast availability. See `data/README.md` for the input contract.

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

The two supplied configurations, the applicant's 0.70 sensitivity configuration,
and 11 unit tests provide a short verification path.
The unit tests independently recompute the SOC transition and check the
terminal-SOC rule. Other key checks are the price-taking
assumption, the CVaR sensitivity result and the role of the oracle as a diagnostic
upper bound rather than a feasible strategy.

## Report regeneration

The supplied PDF reads numbers from current CSVs and embeds the regenerated
baseline figures. To rebuild it, install `requirements-report.txt` and run
`python scripts/build_report.py`; review the resulting PDF before distributing it.
PDFs and PNGs are marked binary in `.gitattributes` to preserve their bytes.
For local update and release steps see `UPDATE_GUIDE_ZH.md`.

## Applicant's local Windows verification

- Check started: 2026-10-04T22:48:22.0591476+01:00
- Environment: Windows / Python 3.13.15
- Dependency check: no broken requirements.
- Unit tests: 11/11 passed; exit code 0.
- Release table comparisons: 9/9 passed; exit code 0.
- Configurations checked: CVaR weights 0.55, 0.70 and 0.85.
- Absolute numeric tolerance: 1e-10.
- Maximum observed absolute numeric difference: 2.27373675443e-13.
- Dated logs and installed package versions: evidence/personal_run/v101_check_20261004_224805.

The applicant executed these checks locally using the assisted code correction. The comparisons use the corrected v1.0.1 references. Earlier reproduction records are retained separately.

These checks establish numerical agreement for the three configurations within the stated tolerance. They do not claim byte-identical files across platforms. All financial results remain simulated benchmark results.

GitHub Actions verification remains pending until the pushed revision is checked.
