# P2: simulated forecast-to-storage scheduling — v1.1.0

A research benchmark linking corrected P1 price forecasts to 24-hour battery schedules. SciPy/HiGHS mixed-integer programming enforces exclusive charge/discharge operation. The experiments compare raw, static and adaptive uncertainty modes using common random numbers. Results show empirical risk–return tradeoffs, not a consistently best policy. All prices and profits are simulated.

See [project history](PROJECT_HISTORY.md) for the version timeline and sources.

## Active artifacts

- [Technical report](report/report_v110.md).
- `corrected_v110/baseline/`, `corrected_v110/cvar_weight_070/`, and `corrected_v110/cvar_weight_085/` contain the reference tables, figures and manifests. `outputs/` mirrors the baseline.
- `corrected_v110/multiseed/` varies scenario-draw seeds on the same simulated market and forecasts.
- `corrected_v110/market_seeds/` varies the corrected P1 simulated market seed at weight .55 with a fixed scenario seed.
- [21 October supplementary study](corrected_v110/supplementary_20261021/README.md): zero-transaction baseline and paired N=60/200 static/adaptive CVaR runs, three seeds and all 83 days. The original seven-strategy references are unchanged.
- [Verification guide](VERIFICATION.md) and [revision summary](NEW_RELEASE_SUMMARY.md).
- `historical_v102/` holds earlier inputs, numerical outputs, figures, reports and the report builder. Dated personal and CI records remain under `evidence/`.

## Model and sampling

Each period has a binary mode: `charge <= power * mode` and `discharge <= power * (1 - mode)`. The optimizer also enforces SOC transitions, capacity, and initial/terminal SOC. Schedules are not clipped or repaired afterwards. The default formulation is `"milp"`; `optimise_schedule(..., formulation="lp_relaxation")` runs the historical continuous model for comparison.

The negative-price regression explains why exclusivity matters. At -100 EUR/MWh, efficiencies 0.94, initial/terminal SOC 1 MWh and throughput cost 2 EUR/MWh, the historical LP charges 1 MW and discharges 0.8836 MW simultaneously, earning 7.8728 EUR. The MILP stays idle and earns zero.

Empirical CVaR averages exactly the worst `1-alpha` probability mass, including a fractional boundary observation. At alpha .90, this is six observations for 60 scenarios and 8.3 for 83 evaluation days. Tests compare the estimator with an independent Rockafellar–Uryasev LP, including tied losses.

Raw, static and adaptive modes share latent uniforms within each day, seed and scenario count; frontier weights reuse the same draws. The Gaussian common-factor loading .65 gives exchangeable latent cross-hour correlation .4225. Seven quantiles are interpolated and rescaled about the median using `clip(width / raw_width, .35, 4)`. Manifests record capped widths and any infinite source intervals.

## Reproduce

Use Python >=3.11 and the locked requirements. Commands run against this folder's `src/`:

```text
python -m pip install -r requirements-lock.txt
python -m unittest discover -s tests -v
python scripts/run_experiment.py --config configs/base.yaml --output-root local_runs/baseline
python scripts/run_experiment.py --config configs/cvar_weight_070.yaml --output-root local_runs/cvar_weight_070
python scripts/run_experiment.py --config configs/high_risk_aversion.yaml --output-root local_runs/cvar_weight_085
python scripts/run_experiment.py --config configs/base.yaml --seed 20260818 --output-root local_runs/scenario_seed_20260818
python scripts/run_experiment.py --config configs/base.yaml --seed 20260817 --source-forecasts data/market_seed_20260818_p1_forecasts.csv --output-root local_runs/market_seed_20260818
python scripts/run_multiseed.py --reuse-reference --output-root local_runs/reused_scenario_study
python scripts/run_market_seed_study.py --reuse-reference --output-root local_runs/reused_market_study
python scripts/run_supplementary.py --output-root local_runs/scenario_count_study
python scripts/verify_release.py
python scripts/audit_saved_schedules.py
```

Use a new `local_runs/` destination for each fresh run. Non-empty directories are rejected unless `--overwrite` is given for a recognized output directory of the same experiment type. It replaces known artifacts without deleting unrelated files; source, Git, evidence and supplied references remain protected. The seed examples above can be repeated with the documented seeds and weight configs for the full grid.

The two study scripts default to fresh runs under `local_runs/scenario_seed_study/` and `local_runs/market_seed_study/`. With `--reuse-reference`, they check configuration and input hashes, aggregate supplied runs, and record `reused_supplied_reference` in `study_manifest.json`. Omit the flag to run a fresh grid; supplied summaries are not overwritten.

The supplementary study draws 200 uniforms per day/seed and uses the first 60 for N=60, with shared ranks across both modes. This prefix differs from the historical standalone N=60 draw. A two-day timing pilot is available with `--pilot-days 2`; it is marked incomplete.

Optional PDF rendering: install `requirements-report.txt`, then run
`python scripts/build_report.py --output report/Haorui_Cai_Storage_Report_v110.pdf`.
The active source is `report/report_v110.md`; visually review a newly rendered PDF.

The release checker reruns three weights, compares six tables per run with the v1.1.0 references at absolute tolerance 1e-8, and recalculates schedule diagnostics. See [verification](VERIFICATION.md) for checks and their evidence scope.

The 18 October reference logs are in `evidence/local_revision_20261018/`; later local checks are indexed in `NEW_RELEASE_SUMMARY.md`. Their original dates and version scope are retained.

Published updates:

- 20 October alpha-reporting fix: [PR #3](https://github.com/KeithCai1995/p2-storage-decision-under-forecast-uncertainty/pull/3), merge `5095b58`, six successful checks.
- 21 October quality update: [PR #4](https://github.com/KeithCai1995/p2-storage-decision-under-forecast-uncertainty/pull/4), merge [3fb9bd3](https://github.com/KeithCai1995/p2-storage-decision-under-forecast-uncertainty/commit/3fb9bd32473cf95b0f803d4fd11d673aca4a1d68), [Actions 39572300880](https://github.com/KeithCai1995/p2-storage-decision-under-forecast-uncertainty/actions/runs/39572300880).
- Latest presentation update: [PR #5](https://github.com/KeithCai1995/p2-storage-decision-under-forecast-uncertainty/pull/5), main merge [208675b](https://github.com/KeithCai1995/p2-storage-decision-under-forecast-uncertainty/commit/208675b342fc377afdb482d230aa8646863f48e4), [Actions 39737336488](https://github.com/KeithCai1995/p2-storage-decision-under-forecast-uncertainty/actions/runs/39737336488).

The cited post-merge runs passed all six jobs: Ubuntu and Windows with Python 3.11, 3.12 and 3.13. Each result is tied to its commit; results for other revisions are listed in Actions.

## Scope and input

Horizon 1 has `issue_time == target_time` on all 83 days. There is no separate prior-day publication or gate-closure timestamp, so the experiment does not establish operational day-ahead availability. The battery is price-taking with perfect hourly execution and linear throughput cost; network, reserve, bidding, imbalance and detailed degradation effects are omitted. The oracle uses future prices and is only an upper-bound diagnostic.

Quantile interpolation and clipped width rescaling are scenario heuristics, not calibrated marginal or joint distributions. They need not preserve interval endpoints or conformal coverage, including when an infinite interval is capped. Three scenario seeds, three simulated markets and two scenario counts do not prove convergence, generalization or future risk reduction. N=200 performing better in this study does not make the default N=60 invalid.

Battery capacity/efficiency sensitivity uses median risk-neutral scheduling on the first 28 days, not adaptive CVaR over all 83. New plots label this window; archived PNGs are unchanged.

The baseline input is `data/p1_forecasts.csv`, SHA256 `6901c84f413ba1375fd8096c3c4910c2346d479a7ff18274832c2d27aba8472b`, containing 1,992 corrected P1 forecasts. See [input contract](data/README.md) and [historical provenance](historical_v102/PROJECT_HISTORY.md).

## Published local-path redaction

Published metadata and selected logs replace the original machine-specific path prefix with `<WORKSPACE>`. Saved implementation paths are descriptive metadata, not rerun inputs. This display change leaves dates, software versions, hashes, results and execution scope intact; unredacted originals are backed up outside Git. New runs may record their own local paths. See [the presentation-update record](PRESENTATION_UPDATE_20261021.md).
