# P2 CVaR weight 0.70 sensitivity results

## Run information

- Date: 2 October 2026

- Configuration: `configs/cvar_weight_070.yaml`

- Parameter changed: `risk.cvar_weight` from 0.55 to 0.70

- Check before the run: all other configuration settings were identical to `configs/base.yaml`

- Python: 3.13.15

- NumPy: 2.3.5

- pandas: 2.2.3

- SciPy: 1.17.0

- Run exit code: 0

- Data: simulated benchmark; not field, employer or live-market data

## Results

The table reports three CVaR-based strategies from the local runs. Profit and loss values are simulated.

| CVaR weight | Strategy | Mean daily profit (EUR) | Fifth-percentile profit (EUR) | Empirical CVaR loss (EUR) | Mean throughput (MWh) | Constraint violation rate |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 0.55 | raw_cvar | 9.734767 | -19.792588 | 21.261249 | 4.489953 | 0.0 |
| 0.55 | static_cvar | 8.195856 | -17.171738 | 19.679775 | 3.903444 | 0.0 |
| 0.55 | adaptive_cvar | 9.858664 | -15.237906 | 15.835791 | 4.203651 | 0.0 |
| 0.70 | raw_cvar | 9.801955 | -19.355873 | 20.683073 | 4.422010 | 0.0 |
| 0.70 | static_cvar | 8.222482 | -16.875628 | 18.592683 | 3.709531 | 0.0 |
| 0.70 | adaptive_cvar | 9.775254 | -14.874311 | 14.544325 | 3.996052 | 0.0 |
| 0.85 | raw_cvar | 9.535650 | -19.355873 | 21.143761 | 4.361372 | 0.0 |
| 0.85 | static_cvar | 8.220657 | -15.274876 | 16.833130 | 3.536103 | 0.0 |
| 0.85 | adaptive_cvar | 9.992991 | -11.092560 | 12.283447 | 3.832792 | 0.0 |

## Interpretation

For `adaptive_cvar`, the empirical CVaR loss decreased from 15.835791 at weight 0.55 to 14.544325 at 0.70 and 12.283447 at 0.85. The fifth-percentile profit also improved across these runs, while mean throughput decreased.

Mean daily profit did not change monotonically: it was 9.858664 at 0.55, 9.775254 at 0.70 and 9.992991 at 0.85. In this simulation, a higher risk weight did not automatically mean lower average profit.

At weight 0.70, the `adaptive_cvar` strategy had a lower empirical CVaR loss than at 0.55, with slightly lower mean daily profit and lower throughput. This does not establish that 0.70 is an optimal setting.

All three runs reported a constraint violation rate of zero.

## Reproduction note

The aggregate strategy metrics for the supplied 0.55 and 0.85 runs matched their reference summaries within numerical tolerance. Earlier comparisons found a small number of differences in daily `in_sample_cvar_loss_eur` values. The cause has not been established, so the daily tables are not described as exact reproductions.

## Limitations

This is a sensitivity comparison using one simulated dataset, one seed and a small number of parameter settings. It is not a real-market backtest and does not establish that any weight will perform similarly on real electricity-market data.
