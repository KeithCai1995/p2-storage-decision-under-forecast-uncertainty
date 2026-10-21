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
- **20 October 2026 (published fix):** the adaptive risk-neutral
  strategy now reports in-sample CVaR using the configured `risk.cvar_alpha`,
  while retaining a zero risk penalty. Two end-to-end regression tests cover
  alpha values .80, .90, .95 and .99 across two scheduling days. All 22 tests
  passed; all 18 default-release table comparisons had zero numerical
  difference, and 3,486 saved/rerun schedules were checked. The original dated
  reference tables and earlier test records are unchanged. These results are
  local verification of this fix, not a new GitHub Actions result.
  The fix was subsequently merged as [PR #3](https://github.com/KeithCai1995/p2-storage-decision-under-forecast-uncertainty/pull/3),
  with main merge commit `5095b58` and six successful post-merge jobs in
  [Actions run 39504949986](https://github.com/KeithCai1995/p2-storage-decision-under-forecast-uncertainty/actions/runs/39504949986).
- **21 October 2026 (local technical update):** added non-empty-output refusal,
  explicit same-experiment overwrite permission without deletion, protected
  source/reference/evidence paths, and tracked ignore rules for fresh runs/cache.
  Matplotlib's declared minimum is now 3.9; the 3.10.8 lock is unchanged.
  Study scripts separate fresh execution from explicitly labelled reference reuse.
  A fresh supplementary experiment uses nested N=60/200 uniforms, three paired
  scenario seeds, static/adaptive CVaR and all 83 days. Its 996 strategy schedules
  and 83 zero-transaction schedules pass full diagnostics. New results and their
  sampling limitations are under `corrected_v110/supplementary_20261021/`.
  The seven-strategy reference tables and all earlier logs remain unchanged.
  Battery sensitivity is now explicitly labelled median risk-neutral over the
  first 28 days. This entry does not claim publication or new remote CI for the
  21 October update; current local test/release results are indexed separately
  in `NEW_RELEASE_SUMMARY.md`.

## Sources

Initial code and reference analyses were supplied. The v1.1.0 corrections and
reference-run preparation are documented in the dated verification records. Method sources are credited in
[RELATED_WORK.md](RELATED_WORK.md); execution details remain in the dated records.
