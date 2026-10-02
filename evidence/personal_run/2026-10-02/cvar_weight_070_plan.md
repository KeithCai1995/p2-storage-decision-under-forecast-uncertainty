# Planned CVaR weight sensitivity experiment

- Date planned: 2 October 2026
- Planned configuration: `configs/cvar_weight_070.yaml`
- Base CVaR weight: 0.55
- High-risk reference weight: 0.85
- Planned CVaR weight: 0.70

## Question

How does setting the CVaR weight to 0.70 affect the simulated storage decisions and performance measures, compared with the supplied 0.55 and 0.85 configurations?

## Planned change

I will copy `configs/base.yaml` and change only `risk.cvar_weight` from 0.55 to 0.70. The data, seed, battery settings, scenario count, CVaR confidence level and evaluation settings will remain the same.

## Measures to inspect

I will compare total and mean daily profit, fifth-percentile profit, empirical CVaR loss, regret, throughput and constraint violations. I will inspect the CVaR-based strategies and check whether the battery constraints remain satisfied.

## Expectation before running

A larger CVaR weight may reduce exposure to poor simulated outcomes, possibly with lower expected profit or less battery throughput. The metrics may not move monotonically, so I will report the observed result even if it does not follow this expectation.

## Limits

This is one parameter comparison on one simulated dataset and seed. It is an exploratory sensitivity check, not evidence that 0.70 is optimal, not a real-market backtest and not proof of performance under other market conditions.
