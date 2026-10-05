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

## Follow-up assisted review, 4 October 2026

This section records a later diagnosis; it does not change what was known during
the applicant's 2 October Windows run. The supplied reference environment and a
3 October assisted Linux rerun used Python 3.12.14, NumPy 2.3.5, pandas 2.2.3 and
SciPy 1.17.0. The applicant used Windows/Python 3.13.15. The applicant first
installed newer available packages (NumPy 2.5.3, pandas 3.0.6, SciPy 1.18.1) and
then matched the three reference package versions; the few daily differences
remained after that package change.

In the assisted Python 3.12.14 rerun, the baseline output files, including the
figures and tables, matched the supplied baseline snapshot byte-for-byte. The
0.85 run's three selected reference tables also matched byte-for-byte. Aggregate
results from the applicant's three runs remained consistent with the report. A
comparison of the 0.70 daily table found two additional differences limited to
`in_sample_cvar_loss_eur` (maximum absolute difference 0.447155).

The code computes this diagnostic by selecting scenario losses satisfying
`loss >= np.quantile(losses, 0.90)` and averaging them. On the discrepant days,
several losses lie at the cutoff to within approximately 1e-15. Small floating-
point differences change how many of those nearly tied losses satisfy `>=`,
so the reported sample tail average can change appreciably while profit,
throughput and aggregate strategy results remain essentially the same. This
explains the observed pattern; the available runs do not isolate Python version
from operating-system and numerical-library effects. The original logs and
comparison failures remain part of the record.

## Follow-up numerical correction on 4 October 2026

The earlier numbers and failed comparisons above are preserved as historical
evidence. Version 1.0.1 uses fixed-probability-mass empirical CVaR and regenerated
risk outputs in an assisted Linux/Python 3.12.14 review. Current snapshots are
under `experiments/`; logs are under `evidence/assisted_review/2026-10-04_cvar_fix/`.
These assisted reruns were not personally performed by the applicant.
