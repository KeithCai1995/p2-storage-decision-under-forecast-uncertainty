# P2: simulated forecast-to-storage scheduling — local v1.1.0

Version 1.1.0 updates the simulated storage benchmark. See [project history](PROJECT_HISTORY.md) for the version timeline and source note.

The corrected edition solves exclusive charge/discharge schedules with SciPy/HiGHS mixed-integer programming, uses the corrected P1 forecast export, and compares uncertainty modes using common random numbers. Prices and all profit figures are simulated. This is a 24-hour scheduling benchmark: horizon 1 has `issue_time == target_time` on all 83 days, so operational day-ahead availability is unverified.

## Active artifacts

- [Technical report](report/report_v110.md).
- `corrected_v110/baseline/`, `corrected_v110/cvar_weight_070/`, and `corrected_v110/cvar_weight_085/` contain current complete runs, with tables, figures and manifests. The main `outputs/` is a copy of the corrected baseline.
- `corrected_v110/multiseed/` varies **scenario-draw seeds** on the same simulated market and forecasts; this measures finite-scenario sensitivity.
- `corrected_v110/market_seeds/` varies the corrected P1 simulated market seed at weight .55 with a fixed scenario seed.
- [New revision and verification summary](NEW_RELEASE_SUMMARY.md).
- Historical numerical outputs, input files and figures remain under `historical_v102/`, together with prior reports, documentation and the report builder. Dated personal and CI records remain under `evidence/`; their numerical results, execution dates and version scope are retained.

## Corrections

For each period, `charge <= power * mode`, `discharge <= power * (1 - mode)`, and `mode` is binary. SOC transitions, capacity, initial and terminal SOC are enforced in the optimization. No clipping or cancellation of solver schedules is used. `optimise_schedule(..., formulation="lp_relaxation")` retains the historical continuous formulation as an explicit diagnostic comparison; the default is `"milp"`.

The one-period regression at price -100 EUR/MWh, charge/discharge efficiency 0.94, initial/terminal SOC 1 MWh and throughput cost 2 EUR/MWh shows the defect: the historical LP charges 1 MW and discharges 0.8836 MW simultaneously, producing 7.8728 EUR. The corrected MILP stays idle and earns zero. Negative prices can invalidate a presumed automatic exclusivity argument.

Empirical CVaR still averages exactly the worst `1-alpha` probability mass, including a fractional boundary observation. At alpha .90, 60 scenarios imply six observations, whereas 83 evaluation days imply 8.3. Tests compare this estimator to an independent Rockafellar–Uryasev LP, including ties.

Raw, static and adaptive scenario sets use the same latent uniforms for each day, seed and scenario count. Risk-frontier weights also reuse those samples. A Gaussian common-factor loading .65 implies latent cross-hour correlation .4225; it is an exchangeable assumption. Interpolating seven quantiles and rescaling around the median with `clip(width / raw_width, .35, 4)` is a heuristic. It does not establish marginal or joint scenario calibration, preserve interval endpoints, or provide conformal decision guarantees. Legitimate infinite source intervals are capped explicitly; their counts and cap counts appear in every manifest.

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
python scripts/run_multiseed.py
python scripts/run_market_seed_study.py
python scripts/verify_release.py
python scripts/audit_saved_schedules.py
```

Fresh runs write to `local_runs/`, leaving the supplied corrected reference tables intact.
The last two experiment commands illustrate scenario-seed and market-seed checks;
repeat with the documented seeds and weight configs to repeat the full grid.
The two study scripts aggregate existing supplied runs and compute a run only if
its manifest is absent. Their cached summaries are not evidence of a fresh personal
execution. Use the explicit experiment commands and new destinations for that purpose.

Optional PDF rendering: install `requirements-report.txt`, then run
`python scripts/build_report.py --output report/Haorui_Cai_Storage_Report_v110.pdf`.
The active source is `report/report_v110.md`; visually review a newly rendered PDF.

The release checker reruns all three weights and compares six tables per run to **v1.1.0** references at absolute tolerance 1e-8. It also checks manifest version, source hash and scenario method, recalculates full physical diagnostics from every saved schedule, and checks strategy/frontier consistency where weights coincide. Historical reference numbers are never accepted as the new release.

Reference verification logs for the 18 October package are in `evidence/local_revision_20261018/`; the later local rerun is recorded in [project history](PROJECT_HISTORY.md). These are local checks. Use the actual GitHub Actions result for a published commit; historical six-job CI results do not apply to v1.1.0.

## Limits and provenance

The battery is price-taking, executes hourly energy schedules perfectly, uses a linear throughput charge and omits network, reserve, bidding/gate-closure, imbalance and detailed degradation models. Oracle schedules use future simulated prices and serve only as an upper-bound diagnostic. Three scenario seeds on one market do not establish robustness across market regimes or assets. An empirically lower tail loss in this finite benchmark is not a guarantee of reduced loss in a new market.

The baseline input is `data/p1_forecasts.csv`, SHA256 `6901c84f413ba1375fd8096c3c4910c2346d479a7ff18274832c2d27aba8472b`, containing 1,992 corrected P1 forecasts. See [input contract](data/README.md) and [historical provenance](historical_v102/PROJECT_HISTORY.md).
