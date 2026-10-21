# Local v1.1.0 — 18 October 2026

Technical correction: exclusive-operation battery MILP, corrected P1 input, common random numbers, complete schedule diagnostics, finite validation, three-weight release verification and separate scenario-draw/market-seed sensitivity studies. See `NEW_RELEASE_SUMMARY.md` for actual results and logs. Sources and the version timeline are recorded in [project history](PROJECT_HISTORY.md).

The prior v1.0.2 release documentation and all earlier numerical artifacts are preserved under `historical_v102/`; their conclusions and checks apply only to those earlier versions. The old report-generation script also resides there. The current report source is `report/report_v110.md`.

## 21 October 2026 — local technical update

Output destinations now refuse accidental overwrites and protect frozen references/source/evidence even with explicit overwrite permission. Fresh study outputs and reused-reference summaries are separated, with checked input/configuration provenance. Matplotlib's minimum is 3.9, while the tested 3.10.8 lock remains unchanged.

The supplementary study adds verified idle=0 and paired N=60/200 evidence for two CVaR strategies, three seeds and 83 days, without changing the existing seven-strategy references. See `corrected_v110/supplementary_20261021/README.md`. The published alpha fix and the later local additions have distinct dated verification scopes in `PROJECT_HISTORY.md`; no new remote CI result is claimed for this local update.
