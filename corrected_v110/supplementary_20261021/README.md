# Supplementary evidence — 21 October 2026

This is a fresh, bounded sensitivity study on the same corrected simulated market, battery, risk weight .55 and alpha .90. It does not replace or modify the original seven-strategy references. The three scenario seeds are 20260817/18/19; every strategy/count/seed uses all 83 days.

## Sampling and results

For each day/seed, generate one N=200 Gaussian-common-factor uniform array, then use its exact first 60 rows for N=60. Static and adaptive scenarios use identical ranks at each N. All 249 day/seed prefixes were verified, and their full/prefix hashes are saved in `sampling_audit.csv`.

The historical generator draws all N common factors before N-by-24 idiosyncratic factors. Consequently the N=60 prefix here differs from its historical standalone N=60 draw. This is a separate paired scenario-count study, not reproduction of the earlier baseline N=60.

| N | Strategy | Mean profit average | CVaR loss average | Total solve seconds |
|---|---|---:|---:|---:|
| 60 | Static CVaR | 8.217827 | 19.697112 | 2.833 |
| 200 | Static CVaR | 9.712681 | 14.668371 | 5.605 |
| 60 | Adaptive CVaR | 8.242171 | 20.727489 | 2.290 |
| 200 | Adaptive CVaR | 9.519176 | 17.841339 | 5.014 |

Profit is mean simulated EUR/day; CVaR is empirical 90% loss in EUR over daily outcomes. Averages are over the three scenario seeds, not confidence intervals. `strategy_metrics.csv` includes all 12 seed/count/strategy results; `seed_summary.csv` includes ranges, not just selected outcomes.

| Seed | Strategy | Profit change | CVaR loss change | Mean action L1 change |
|---|---|---:|---:|---:|
| 20260817 | Static | +2.491519 | -9.562180 | 1.834897 |
| 20260818 | Static | +0.462989 | -0.874846 | 1.674168 |
| 20260819 | Static | +1.530054 | -4.649199 | 1.793132 |
| 20260817 | Adaptive | +2.523262 | -4.816999 | 1.530517 |
| 20260818 | Adaptive | +0.202391 | -2.525817 | 1.391540 |
| 20260819 | Adaptive | +1.105363 | -1.315634 | 1.624484 |

Changes are N=200 minus N=60. Action L1 is the daily sum of absolute charge and discharge changes, averaged over days, in MWh for one-hour periods. The mean number of changed hours ranges from 6.361 to 7.446 per day, using a 1e-7 MW threshold. This is action sensitivity, not an optimality gap. All six pairs improve mean profit and CVaR loss here; other metrics need not improve: adaptive seed 20260817's fifth-percentile profit falls from -18.345239 to -20.323186 EUR.

## Idle and verification

`idle_schedule.csv` charges/discharges zero and holds SOC at its initial level. Applied to all 83 actual simulated daily price paths, it has zero profit, zero CVaR loss and no physical violations. It is a feasible outside alternative, not a new optimized policy or a claim that trading beats idle on every day. `idle_comparison.csv` labels the seven original strategies as reused supplied baseline values and idle as fresh verification.

The 996 strategy-day schedules and 83 idle schedules cover 25,896 periods, with zero full-constraint violations. `all_schedules.csv` contains the 996 strategy schedules; the separately saved idle schedule and `idle_daily.csv` cover the no-transaction alternative. `study_manifest.json` records configuration, software, input hash, execution status and sampling limitations. The main paired loop took 17.194 seconds locally. Per-solve timing includes only `optimise_schedule`; it is hardware/load dependent and not a portable performance guarantee.

An initial two-day pilot took 0.346 seconds in its main loop; it was only a runtime estimate, not a substitute for the complete study. Fresh reproduction:

```text
python scripts/run_supplementary.py --output-root local_runs/scenario_count_study
```

Non-empty fresh-run destinations require explicit same-type overwrite permission; no files are deleted. Supplied reference folders, including this completed supplementary archive, are protected even with that permission. Three paired Monte Carlo seeds on one simulated market and two scenario counts do not prove convergence, statistical significance, joint calibration or real-market robustness. These remain scenarios built by capped quantile-width heuristics, under the existing issue/target timing limitation.
