# P2 local reproduction record

## Environment and checks

- Date: 2 October 2026
- Operating system: Windows
- Python: 3.13.15
- NumPy: 2.3.5
- pandas: 2.2.3
- SciPy: 1.17.0
- `pip check`: passed, exit code 0
- Unit tests: 2 passed, exit code 0
- Data: simulated benchmark; no field, employer or live-market data

## Baseline configuration

The run completed with exit code 0.

- `strategy_metrics.csv`: matched the reference; maximum absolute numeric difference 0.
- `risk_frontier.csv`: matched within floating-point tolerance; maximum absolute difference 3.55e-15.
- `daily_results.csv`: did not fully match; maximum absolute difference 2.059645.

The daily differences were in `in_sample_cvar_loss_eur`:

| Issue day | Strategy | Local value | Reference value | Absolute difference |
| ---: | --- | ---: | ---: | ---: |
| 341 | adaptive_cvar | 4.876441 | 5.844462 | 0.968021 |
| 354 | static_cvar | -0.935387 | -1.198660 | 0.263273 |
| 368 | static_cvar | 9.564642 | 7.504997 | 2.059645 |

## High-risk configuration

The run completed with exit code 0.

- `strategy_metrics.csv`: matched within floating-point tolerance; maximum absolute difference 3.55e-15.
- `risk_frontier.csv`: matched within floating-point tolerance; maximum absolute difference 3.55e-15.
- `daily_results.csv`: did not fully match; maximum absolute difference 0.818611.

The daily differences were in `in_sample_cvar_loss_eur`:

| Issue day | Strategy | Local value | Reference value | Absolute difference |
| ---: | --- | ---: | ---: | ---: |
| 354 | static_cvar | -1.189520 | -0.881475 | 0.308045 |
| 416 | raw_cvar | 2.039443 | 1.220832 | 0.818611 |

## Interpretation

Both configurations ran successfully, and their aggregate strategy metrics and risk-frontier results match the supplied references within numerical tolerance. The daily tables differ in a small number of scenario-based in-sample CVaR values. The cause of those differences has not been established, so I do not describe the full daily tables as exact reproductions.

All figures and financial results in this project come from simulated data. They are not evidence of real trading performance or field outcomes.
