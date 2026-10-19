# P2 v1.0.2 documentation revision - 9 October 2026

Based on uploaded v1.0.1 archive at commit
`1ed70de61059a35fe9ded074b34a7ee8ad75aefc`.

- Explain scenario scale bounds [0.35, 4.0] and capped hourly rows.
- Describe the objective as risk-averse in the report title.
- Include historical Windows and CI checks with their original commit scope.
- Improve Figure 5 label placement using the same saved table.
- Synchronise PDF, report builder and package metadata at 1.0.2.

Numerical source, tests, data, configurations and existing snapshots are unchanged.
The fresh 9 October review passed 11 tests, 15 table comparisons and 18 figure
pixel comparisons. See `evidence/technical_review/2026-10-09_documentation/`.

Status: locally prepared candidate. Check new CI after pushing before publishing
an unused v1.0.2 tag. Preserve historical tags and records.
For current steps use `UPDATE_V102_ZH.md`.

---

# Historical v1.0.1 release notes - 4 October 2026

This revision replaces a quantile-threshold tail mean with fixed-probability-mass
empirical CVaR, including fractional boundary observations and ties. It adds
regression tests and regenerates all affected outputs and the report. The LP,
forecast data, seed and chosen schedules are unchanged.

| Adaptive CVaR weight | Earlier reported tail mean EUR | Corrected empirical CVaR EUR |
| ---: | ---: | ---: |
| 0.55 | 15.835791 | 16.226393 |
| 0.70 | 14.544325 | 15.029772 |
| 0.85 | 12.283447 | 12.585521 |

Verification in the assisted Linux/Python 3.12.14 environment: 11/11 tests,
9/9 independently rerun table comparisons, and 3,744 paired solves with identical
schedules, expected profit and LP objective. Original references and personal
runs are retained. Local Windows/Python 3.13.15 verification passed. Remote CI passed for commit c6155e7; all six matrix jobs succeeded.

Both package version declarations are 1.0.1, and Python >=3.11 matches the locked
NumPy/SciPy requirements. Independent output roots prevent overwriting runs.
PDF/PNG binary attributes preserve bytes during Git line-ending conversion.
See `UPDATE_GUIDE_ZH.md` for replacing files and publishing v1.0.1. This submission candidate combines the earlier documentation edits
with the numerical correction. The version is 1.0.1, as requested by the applicant.

## Applicant's local Windows verification

- Check started: 2026-10-04T22:48:22.0591476+01:00
- Environment: Windows / Python 3.13.15
- Dependency check: no broken requirements.
- Unit tests: 11/11 passed; exit code 0.
- Release table comparisons: 9/9 passed; exit code 0.
- Configurations checked: CVaR weights 0.55, 0.70 and 0.85.
- Absolute numeric tolerance: 1e-10.
- Maximum observed absolute numeric difference: 2.27373675443e-13.
- Dated logs and installed package versions: evidence/personal_run/v101_check_20261004_224805.

The applicant executed these checks locally using the assisted code correction. The comparisons use the corrected v1.0.1 references. Earlier reproduction records are retained separately.

These checks establish numerical agreement for the three configurations within the stated tolerance. They do not claim byte-identical files across platforms. All financial results remain simulated benchmark results.

GitHub Actions verification passed for commit c6155e7; all six matrix jobs succeeded.

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
