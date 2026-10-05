# Reference runs and provenance

## Current v1.0.1 outputs

The empirical CVaR reporting correction and recovery verification were performed
in an assisted Linux/Python 3.12.14 environment on 4 October 2026. NumPy 2.3.5,
pandas 2.2.3, SciPy 1.17.0, Matplotlib 3.10.8 and PyYAML 6.0.3 were used. These
are assisted reviews, not new runs personally performed by the applicant.
The simulated P1 forecast input SHA256 is
`81252fba7fd9b5999ba93691aba6049867b8a09e9bb5b7f3fd3f2bbf6ac9d04e`.

Current snapshots are `experiments/baseline`, `experiments/cvar_weight_070` and
`experiments/cvar_weight_085`. Each contains five CSV tables, six figures and
one manifest with version 1.0.1 and estimator `empirical_fixed_probability_mass_v1`.
The main `outputs` folder is the corrected baseline.

| Adaptive-CVaR weight | Mean daily profit EUR | Fixed-mass empirical CVaR EUR | Mean throughput MWh/day |
| ---: | ---: | ---: | ---: |
| 0.55 | 9.858664 | 16.226393 | 4.203651 |
| 0.70 | 9.775254 | 15.029772 | 3.996052 |
| 0.85 | 9.992991 | 12.585521 | 3.832792 |

Profit, fifth-percentile profit, regret, throughput, feasibility and schedules
remain unchanged. CVaR reporting uses exactly the worst 10% probability mass,
including 0.3 of the boundary day in an 83-day evaluation. The separate frontier
sample has CVaR losses 17.643650 at weight 0.55 and 17.508437 at weight 0.85;
mean profits remain 9.516830 and 9.033616 respectively. It is a diagnostic with
its own scenario sample, not a basis for selecting a universally optimal weight.

## Verification

`python -m unittest discover -s tests -v` passed 11 tests. The independent
`python scripts/verify_release.py` rerun passed 9/9 current-reference comparisons,
with tolerance 1e-10. The old/new reporting audit compared 1,248 solves per
configuration, including evaluation, frontier and battery sensitivity: all 3,744
pairs had identical schedules, expected profits and LP objective values.
Historical non-CVaR table values agree within 1e-10. Logs and audit code are
under `evidence/assisted_review/2026-10-04_cvar_fix/`.

Corrected Windows results and the configured six-job GitHub Actions matrix have
not yet been run in this assisted review. Bitwise-identical plots on every
platform are not claimed.

## Historical records

Original reference tables and manifests remain byte-identical in
`experiments/legacy_threshold_tail/`. They use the earlier threshold-tail mean
and are not the pass/fail references for the revised estimator.

The applicant's 2 October Windows/Python 3.13.15 logs and snapshots, including
weight 0.70, remain in `evidence/personal_run/2026-10-02/`. With matched NumPy,
pandas and SciPy versions, a few daily CVaR diagnostics still differed. Near-tied
scenario losses and threshold membership explain the unstable reporting pattern;
Python version alone was not isolated as the cause. Original interpretations
remain intact with dated follow-up additions. Disclose AI or other assistance
according to the relevant application rules.

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

GitHub Actions verification remains pending until the pushed revision is checked.
