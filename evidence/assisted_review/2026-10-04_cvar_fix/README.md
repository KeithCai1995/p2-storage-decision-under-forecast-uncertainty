# Assisted correction and verification

- Date: 4 October 2026
- Environment: Linux/Python 3.12.14; package versions in environment.txt
- Role: assisted revision, not an applicant personal run
- Estimator: empirical_fixed_probability_mass_v1
- Seed: 20260817; weights: 0.55, 0.70 and 0.85

The former estimator averaged all losses at or above an interpolated quantile.
That can include excess probability mass; tiny changes in near-tied losses can
change membership sharply. Fixed tail mass removes that membership effect and
agrees with the empirical Rockafellar-Uryasev LP. Tests cover repeated values,
fractional boundaries, perturbations, invalid inputs and LP consistency.

The audit compares 3,744 old/new reporting solves without changing LP matrices
or objectives. Saved logs record actual checks. Windows results and remote CI
are pending, and exact binary reproduction across all environments is not claimed.

Reproduce the audit without changing current references:

```bash
python evidence/assisted_review/2026-10-04_cvar_fix/audit_revision.py --output-root evidence/runs/my_audit
```

Use `python scripts/verify_release.py` for the three current configurations.

The submission candidate is numbered 1.0.1 at the applicant's request. After
aligning the version declarations, all three configurations were rerun and the
nine key tables matched the earlier corrected outputs. Newly generated manifests
record package version 1.0.1. See `version_101_verification.txt` and
`unit_tests_version_101.txt`; the original numerical audit remains preserved.
