# P2 v1.0.2 GitHub Actions verification

- Recorded at: 2026-10-09T18:18:58.0791791+01:00
- Verified commit: 6a7e1c7682d03d5e272c5971ae7fb9f37f2ea82c
- Workflow: P2 numerical reproducibility
- Run: https://github.com/KeithCai1995/p2-storage-decision-under-forecast-uncertainty/actions/runs/37963803634
- Result: 6/6 matrix jobs passed.
- Platforms: Ubuntu and Windows.
- Python versions: 3.11, 3.12 and 3.13 on each platform.
- Checks: dependency consistency, unit tests and release-table verification.
- Configurations: CVaR weights 0.55, 0.70 and 0.85.
- Absolute numeric tolerance: 1e-10.
- Applicant local verification: evidence/personal_run/v102_check_20261009_175606/verification_summary.md

This record applies to the commit and workflow run named above. It establishes numerical agreement within the stated tolerance. All financial results remain simulated benchmark results.

The release page provides the workflow link for the final tagged revision.
