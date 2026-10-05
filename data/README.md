# Input contract

`p1_forecasts.csv` is a snapshot of Project 1's held-out forecast output. Each issue day
contains 24 hourly targets and the following fields:

- realised price and seasonal-naive point forecast;
- raw quantiles q05, q10, q25, q50, q75, q90 and q95;
- static and adaptive 80% conformal intervals;
- regime and simple out-of-distribution diagnostics.

`issue_time` is 00:00 UTC on the target day for each 24-hour block. For horizon 1,
`issue_time` and `target_time` are equal in all 83 days of this snapshot. The file
does not provide a separate timestamp showing when these forecasts were available
before a real day-ahead market gate closure. Consequently the simulated scheduling
results do not verify operational day-ahead information availability. A real-data
extension must check the forecast publication time against the relevant gate
closure for every target day.

The file is simulated and contains no employer data. To replace it with real data, rerun
Project 1 with a publication-time-safe public market dataset, then copy the resulting
`outputs/forecast_quantiles_test.csv` here. Do not construct decisions from revised values
that were unavailable at the day-ahead gate closure.
