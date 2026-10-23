# Checks and reproducibility

The current suite has 35 tests. It checks battery constraints, the empirical CVaR
calculation, configured risk levels, shared scenario ranks, input validation,
output paths and the distinction between fresh runs and reused results.

`scripts/verify_release.py` reruns the three reference risk weights and compares
six tables per run. The local check matched all 18 tables with zero numerical
difference and checked 3,486 saved and rerun daily schedules. Commands are in the
[README](README.md#reproduce).

## Published checks

The [22 October main run](https://github.com/KeithCai1995/p2-storage-decision-under-forecast-uncertainty/actions/runs/39737336488)
passed all six jobs for commit `208675b`: Ubuntu and Windows with Python 3.11,
3.12 and 3.13. Each job runs the tests and release verifier. That result belongs
to the linked commit; later edits have their own workflow results.

## Saved evidence

- `evidence/local_verification_20261021/` contains the 35-test and release-check
  logs, plus the fresh market and scenario-count studies.
- `evidence/local_revision_20261018/` contains the earlier reference checks.
  Its saved-schedule audit covers 11 runs and 6,391 daily schedules, with zero
  constraint violations.
- `corrected_v110/supplementary_20261021/` contains the paired N=60/200 results
  and the idle baseline: 1,079 schedules and 25,896 periods, all feasible.

[The release summary](NEW_RELEASE_SUMMARY.md) has the detailed tables and timings;
[project history](PROJECT_HISTORY.md) lists the versions. Older logs retain their
original dates and test counts. In particular, the saved-schedule audit script
writes into the dated evidence directory, so keep a copy before running it again.
