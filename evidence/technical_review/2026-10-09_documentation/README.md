# P2 documentation closeout review - 9 October 2026

The supplied ZIP identifies commit
`1ed70de61059a35fe9ded074b34a7ee8ad75aefc`; its SHA256 is
`4dcf950fd1f3ed3340b73f33dcd6564350a015645cd2ce72347c49ea430f1033`.
The separate supplied PDF matches its archive counterpart.

This assisted technical review is not a new personal run by the applicant or
a GitHub Actions run. The existing audit logs record fresh execution before
documentation edits. Numerical source, tests, data, configurations and output
snapshots were then checked byte for byte against the revision candidate.
Only the package version string changes within src/.

Linux/Python 3.12.14 and locked NumPy 2.3.5, pandas 2.2.3, SciPy 1.17.0,
Matplotlib 3.10.8 and PyYAML 6.0.3 were used. All 11 tests passed; all three
weights were executed; 15 tables matched (maximum absolute difference 0 at
tolerance 1e-10), and all 18 PNGs matched RGB pixels. Forty original PDF numeric
cells matched to two decimals. Across 3,744 schedules, maximum SOC transition
residual was 4.440892098500626e-16; other recorded feasibility residuals were zero.

Four static and seven adaptive hourly rows reach the upper scale cap of 4.0;
none reaches the lower cap 0.35. The report now explains conditional width
matching and finite-scenario limits. Historical Windows/CI checks are included
with their original dates and commit scope. Figure 5 labels are repositioned
using the same frontier data. Original numerical snapshots and evidence remain intact.

candidate_validation.json records the reconstructed candidate's PDF checks and
numerical-file preservation. The archive was rebuilt after the earlier temporary
download became unavailable; no new numerical experiment is claimed for this rebuild.
These checks concern simulated data and do not establish live-market profits
or compliance with a particular university's rules.
