# Local verification — 21 October 2026

These are newly completed local checks of the 21 October technical update, not replacement logs for the original reference package and not new GitHub Actions results.

- `unit_tests.log`: all 35 tests passed, including output protection, explicit CLI overwrite forwarding, dependency/API compatibility, checked reference reuse, nested scenario draws, idle feasibility and a small fresh supplementary study.
- `release_verifier.log`: all 18 table comparisons passed with maximum difference zero at absolute tolerance 1e-8; 3,486 saved/rerun daily schedules were checked. The verifier independently reran all three risk weights, using temporary outputs under ignored `local_runs/release_checks/`.
- `supplementary_full.log`: a fresh N=60/200, three-seed, two-policy, full-83-day study; 996 strategy schedules plus 83 idle schedules, zero physical violations. Its archived tables and sampling/constraint metadata are under `../../corrected_v110/supplementary_20261021/`.
- `environment.log`: package/source import and software versions. The existing environment was read-only, current repository `src/` was forced, bytecode writes were disabled and the plotting cache stayed in the workspace.
- `fresh_market_study.log` and `fresh_market_comparison.log`: the new fresh-execution wrapper completed all three simulated market seeds into an external fresh directory; all 18 tables match their supplied references with zero numerical difference. These validate the wrapper, not new independent market evidence.

Reproduction entry points, using a new destination for the supplementary rerun:

```text
python -B -m unittest discover -s tests -v
python -B scripts/verify_release.py
python -B scripts/run_supplementary.py --output-root local_runs/scenario_count_study
```

The supplementary archive was a new, empty destination when generated. It is now protected from overwrite; reproduce it in a fresh `local_runs/` destination. Runtime is a local observation, not a portable benchmark. The earlier 18/19/20 October evidence retains its original date and scope. Published PR #3 CI covers the earlier alpha fix, not this later local update.
