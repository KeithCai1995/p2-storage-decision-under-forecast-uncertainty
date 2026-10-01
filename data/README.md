# Input contract

`p1_forecasts.csv` is a snapshot of Project 1's held-out forecast output. Each issue day
contains 24 hourly targets and the following fields:

- realised price and seasonal-naive point forecast;
- raw quantiles q05, q10, q25, q50, q75, q90 and q95;
- static and adaptive 80% conformal intervals;
- regime and simple out-of-distribution diagnostics.

The file is simulated and contains no employer data. To replace it with real data, rerun
Project 1 with a publication-time-safe public market dataset, then copy the resulting
`outputs/forecast_quantiles_test.csv` here. Do not construct decisions from revised values
that were unavailable at the day-ahead gate closure.
