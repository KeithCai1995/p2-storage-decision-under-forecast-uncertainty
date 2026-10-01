# Reference runs and provenance

## What the archive establishes

The supplied archive contained baseline and sensitivity output snapshots and a
log dated 18 August 2026. File dates and saved outputs do not independently
establish who executed those commands. This record therefore treats the
18 August results as supplied reference results; it does not claim that the
applicant personally ran them on that date.

All prices, forecasts, schedules and monetary values in this project are
simulated. They are not Tarim Oilfield data, employer evidence, realised
electricity-market revenue or a live trading result.

## Technical reproduction during this revision

On 1 October 2026, the project tests and both experiment configurations were
rerun in the assisted review environment using Python 3.12.14, NumPy 2.3.5,
pandas 2.2.3 and SciPy 1.17.0. The rerun confirmed that renaming the scenario
parameter to `common_factor_loading` did not change the generated numeric
results. Each regenerated results table matched its supplied reference table
exactly in this environment. This check verifies that the code can reproduce
the snapshots; it is not evidence that the applicant personally performed the
rerun.

The two unit tests passed. One test now independently checks every hourly SOC
transition using the reported starting SOC, charge, discharge and efficiencies,
as well as the terminal-SOC condition. The second checks feasibility and finite
CVaR outputs.

## Baseline result

Run from the project root with:

```bash
python scripts/run_experiment.py --config configs/base.yaml
```

For adaptive-CVaR at weight 0.55 over 83 simulated evaluation days:

| Metric | Result |
| --- | ---: |
| Mean daily profit | 9.858664 EUR |
| Fifth-percentile daily profit | -15.237906 EUR |
| Empirical CVaR loss | 15.835791 EUR |
| Mean regret against the perfect-foresight oracle | 46.786911 EUR/day |
| Mean throughput | 4.203651 MWh/day |
| Constraint-violation rate | 0.0 |

These are outcomes on one fixed simulated benchmark. The oracle uses realised
future prices and is only an unattainable information upper bound.

## CVaR-weight sensitivity

The second configuration changes only `risk.cvar_weight` from 0.55 to 0.85:

```bash
python scripts/run_experiment.py --config configs/high_risk_aversion.yaml
```

On the main fixed scenario sample, adaptive-CVaR at weight 0.85 had mean daily
profit of 9.992991 EUR, empirical CVaR loss of 12.283447 EUR and mean throughput
of 3.832792 MWh/day. On the separate risk-frontier scenario sample, mean daily
profit was 9.033616 EUR at weight 0.85 and 9.516829 EUR at weight 0.55. The
change in ranking across scenario samples is why the 0.85 result is not called
generally better and the pre-specified base weight remains 0.55.

## Applicant's personal process record

The technical reproduction above was performed in an assisted review
environment. Before presenting the run as the applicant's own development
evidence, the applicant should follow `P2_开发过程证据补全指南.md` outside this
archive, rerun the project personally, and keep the resulting terminal log,
environment record, comparison and dated notes. Any AI or external assistance
should be disclosed according to each programme's rules.
