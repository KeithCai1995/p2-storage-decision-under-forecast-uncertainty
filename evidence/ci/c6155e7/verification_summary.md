# P2 v1.0.1 CI verification

## GitHub Actions verification

- Status checked: 5 October 2026.
- Verified commit: c6155e7.
- Workflow: P2 numerical reproducibility.
- Run: https://github.com/KeithCai1995/p2-storage-decision-under-forecast-uncertainty/actions/runs/37309344738
- Result: 6/6 matrix jobs passed.
- Platforms: Ubuntu and Windows.
- Python versions: 3.11, 3.12 and 3.13 on each platform.
- Workflow checks: dependency consistency, unit tests and release-table verification for CVaR weights 0.55, 0.70 and 0.85.
- Release-table absolute numeric tolerance: 1e-10.

This verification applies to commit c6155e7 and the corrected references. It establishes numerical agreement within the stated tolerance, not byte-identical files across platforms. All financial results remain simulated benchmark results.
