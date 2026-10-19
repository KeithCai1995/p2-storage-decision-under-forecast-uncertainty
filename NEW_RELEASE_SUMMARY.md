# Local corrected release v1.1.0 — 18 October 2026

This note describes the reference package prepared on 18 October 2026. See [project history](PROJECT_HISTORY.md) for sources and the separate 19 October local reproduction. The checks below are local results, not a new remote CI result.

## What changed

- Default optimization is a SciPy/HiGHS MILP with one binary operating mode per hour. Charge/discharge exclusivity is enforced by constraints, with no schedule repair. The historical continuous formulation is available explicitly as `lp_relaxation`.
- The corrected P1 baseline replaces the input, while the old input and prior outputs remain historical. The fixed-probability-mass CVaR implementation and independent equivalence tests are retained.
- Every strategy comparison and frontier reuses common latent uniforms within a day/seed. Scenario-draw sensitivity spans three seeds and three weights, each with 60 scenarios and 83 days.
- A separate market-seed sensitivity uses three corrected P1 simulated market realizations at weight .55 and fixed scenario seed 20260817.
- Full physical diagnostics include power non-negativity/bounds, all SOC bounds, transitions/continuity, initial/terminal SOC and exclusivity. Input validation rejects non-finite prices, quantiles and configuration values. Valid infinite conformal intervals are counted and their heuristic width cap is explicit.
- Active documentation labels the experiment simulated 24-hour scheduling, preserves the horizon-1 issue/target timing limitation and makes no joint scenario calibration claim.

## Actual completed verification

All checks ran locally using the existing read-only Python environment. Import provenance confirms the revised `src/storage_decision/battery.py`, version 1.1.0. Environment: Windows, Python 3.13.15, NumPy 2.3.5, pandas 2.2.3, SciPy 1.17.0. Bytecode was disabled; Matplotlib cache stayed in this workspace.

| Check | Result | Evidence |
|---|---|---|
| Unit tests | 20/20 passed | `evidence/local_ai_revision_20261018/unit_tests.log` |
| Dependency consistency | No broken requirements | `evidence/local_ai_revision_20261018/dependency_check.log` |
| Import provenance | Revised local source, v1.1.0 | `evidence/local_ai_revision_20261018/environment.log` |
| Three-weight release rerun | 18/18 tables matched; max difference 0; atol 1e-8 | `evidence/local_ai_revision_20261018/release_verifier.log` |
| Release schedule checks | 3,486 saved/rerun daily schedules; 83,664 periods | Same release log |
| All corrected saved runs | 11 runs, 6,391 daily schedules, 153,384 periods; zero violations | `evidence/local_ai_revision_20261018/all_saved_schedule_audit.json` and `.csv` |
| Max SOC transition residual | 5.995204332975845e-14 MWh | Same audit JSON |
| Max terminal SOC error | 0 MWh | Same audit JSON |
| Negative-price regression | Historical LP 7.8728 EUR via simultaneous cycle; MILP idle/0 EUR | `evidence/local_ai_revision_20261018/negative_price_regression.csv` |

The first release-verifier attempt failed because the sandbox's default temporary directory could not be written. That failure is preserved in `release_verifier_initial_temp_failure.log`. The verifier now creates its temporary rerun inside this workspace; the completed rerun log above passed. This was an environment-path failure, not a failed numerical comparison. Historical CI evidence remains dated evidence for the old revisions only.

Commands completed: `python -m unittest discover -s tests -v`, `python -m pip check`, the three `scripts/run_experiment.py` configurations, `python scripts/run_multiseed.py`, `python scripts/run_market_seed_study.py`, `python scripts/verify_release.py`, and `python scripts/audit_saved_schedules.py`. The experiment scripts save complete tables, figures and manifests. The PDF was rendered separately from `report/report_v110.md`; its rendering evidence, if present, belongs to the parent review workflow.

## Numerical results

Each cell is mean simulated daily profit / empirical 90% CVaR loss in EUR, on baseline market seed 20260817 and scenario seed 20260817:

| Weight | Raw | Static | Adaptive |
|---|---:|---:|---:|
| .55 | 9.824954 / 20.671937 | 8.312606 / 18.461950 | 8.342875 / 17.903540 |
| .70 | 9.628043 / 20.116700 | 8.193503 / 18.366346 | 8.173652 / 17.948549 |
| .85 | 9.507893 / 19.671756 | 8.638098 / 16.861680 | 8.405449 / 16.623044 |

Median risk-neutral mean profit is 8.691456 EUR/day and tail loss 24.002282 EUR. Oracle mean is 56.645575 EUR/day; it uses future prices. The adaptive strategy does not maximize mean profit and is not a universal winner.

Across three scenario-draw seeds on the same baseline market, adaptive CVaR's mean-profit averages are 8.475468, 8.556264 and 8.612698 at weights .55/.70/.85, with corresponding tail-loss averages 19.594964, 18.533924 and 17.635672. Static has smaller average tail loss than adaptive at .70 and .85. Full ranges and all strategies are in `corrected_v110/multiseed/strategy_metrics_seed_summary.csv` and `strategy_metrics_by_seed.csv`. The seeds are 20260817/18/19, with 60 scenarios and 83 days throughout. Raw logs: `evidence/local_ai_revision_20261018/multiseed.log`.

For three simulated market seeds at weight .55, fixed scenario seed 20260817:

| Market seed | Raw mean / tail | Static mean / tail | Adaptive mean / tail |
|---|---:|---:|---:|
| 20260817 | 9.824954 / 20.671937 | 8.312606 / 18.461950 | 8.342875 / 17.903540 |
| 20260818 | 10.216645 / 25.894578 | 8.707315 / 19.798796 | 8.778388 / 20.531445 |
| 20260819 | 11.572049 / 21.288503 | 10.804878 / 18.235675 | 11.035034 / 17.110700 |

These are sensitivity checks on synthetic markets, not statistical significance or real-market robustness. Full results: `corrected_v110/market_seeds/strategy_metrics_by_market_seed.csv`; log: `evidence/local_ai_revision_20261018/market_seed_study.log`.

## Input provenance and active artifacts

Baseline source: corrected P1 `corrected_v110/baseline/outputs/forecast_quantiles_test.csv`, copied to `data/p1_forecasts.csv`, 1,992 rows. SHA256 `6901c84f413ba1375fd8096c3c4910c2346d479a7ff18274832c2d27aba8472b`.

Additional market-seed files and SHA256:

- `data/market_seed_20260818_p1_forecasts.csv`: `c8c8278d3a237f55c2169bedc3a857f0e3d07e7098b0c233da9f7e5bc3615d50`.
- `data/market_seed_20260819_p1_forecasts.csv`: `f2342bdf4832c3a93abbae9f7cbc7f9f8a76a2322e377ab9c984af41799e06cc`.

All three files contain 83 days × 24 periods. Corrected baseline cap counts are one static and three adaptive widths above four times the raw q90–q10 width; neither source has infinite intervals in this baseline. Each manifest records cap counts, infinite-width counts, source hash, configuration, software and implementation path.

Current runs are under `corrected_v110/`; main `outputs/` mirrors the corrected baseline. `report/report_v110.md` is the corrected report source. Historical output, experiments, input, report PDF, documentation and old report builder are under `historical_v102/`; `historical_v102/HISTORICAL_STATUS.md` explains the boundary. Original personal and CI evidence folders remain under `evidence/` unchanged.

## Limits

Horizon 1 issue and target times coincide on all 83 days. Operational day-ahead availability is unverified. Forecast quantile interpolation, width clipping and a Gaussian common-factor assumption do not yield calibrated joint paths. A valid infinite P1 interval is capped for finite scenarios, with no retained conformal guarantee. Three scenario seeds and three synthetic markets do not establish broad robustness. Execution, network, imbalance, bidding and detailed degradation effects are absent. The old/new baseline difference combines several corrections and does not isolate the effect of exclusivity.
