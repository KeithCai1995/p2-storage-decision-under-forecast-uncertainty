# Project history

The supplied v1.0.2 material and earlier evidence predate this revision. Earlier project history is recorded at
[historical_v102/PROJECT_HISTORY.md](historical_v102/PROJECT_HISTORY.md).

## Version timeline

- **v1.0.2:** earlier outputs, input and documentation remain under
  `historical_v102/`; original reproduction and CI records remain under
  `evidence/` with their original dates.
- **18 October 2026:** v1.1.0 introduces exclusive battery operation, corrected
  P1 inputs, paired scenarios and expanded verification.
- **19 October 2026:** a personal rerun completed 20 tests, the default baseline,
  and 18/18 release-table comparisons with zero differences. The verifier
  checked 3,486 saved/rerun schedules. Local logs remain outside this repository
  under `Personal_Logs/20261019_080009/`. This does not record a new remote CI run
  or fresh personal execution of the full sensitivity grid.
- **20 October 2026 (local fix, not yet published):** the adaptive risk-neutral
  strategy now reports in-sample CVaR using the configured `risk.cvar_alpha`,
  while retaining a zero risk penalty. Two end-to-end regression tests cover
  alpha values .80, .90, .95 and .99 across two scheduling days. All 22 tests
  passed; all 18 default-release table comparisons had zero numerical
  difference, and 3,486 saved/rerun schedules were checked. The original dated
  reference tables and earlier test records are unchanged. These results are
  local verification of this fix, not a new GitHub Actions result.

## Sources

Initial code and reference analyses were supplied. The v1.1.0 corrections and
reference-run preparation are documented in the dated verification records. Method sources are credited in
[RELATED_WORK.md](RELATED_WORK.md); execution details remain in the dated records.
